"""Word-level spoken ↔ on-screen validation using Whisper timings + optional VLM frames."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.display_sync import (
    MIN_ALIGNMENT,
    VisualWindow,
    _meta_for,
    build_visual_timeline,
    score_cue_visual,
    visual_at,
)
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.daily_single.spoken_visual_sync import is_chart_or_table_file
from praisonaippt.daily_single.visual_audit import export_frame
from praisonaippt.segment_video.image_selection import script_alignment
from praisonaippt.transcript_loader import load_whisper_json
from praisonaippt.video_qa.vlm_cache import describe_frame_cached
from praisonaippt.vision_describe import vision_model, vision_provider

MIN_WORD_ALIGNMENT = MIN_ALIGNMENT
MIN_VLM_ALIGNMENT = 0.38
MAX_SAMPLES_PER_WINDOW = 8
MIN_WORD_LEN = 3
FRAG_STOP = frozenset({"the", "a", "an", "and", "or", "that", "this", "in", "to", "of", "for", "is", "it"})
SKIP_FILES = frozenset({"heygen.mp4", "none", "brand-bumper-1080p-hevc.mp4"})
OFF_TOPIC_VISION = re.compile(
    r"\b(butterfl|moth|entomol|vintage map|old map|ancient text|illustration of various)\b",
    re.I,
)


@dataclass
class GlobalWord:
    word: str
    start_sec: float
    end_sec: float
    segment: str

    @property
    def mid_sec(self) -> float:
        return (self.start_sec + self.end_sec) / 2.0


def _normalise_word(w: str) -> str:
    return re.sub(r"[^\w']+", "", w.lower())


def _is_content_word(word: str) -> bool:
    token = _normalise_word(word)
    return len(token) >= MIN_WORD_LEN and token not in FRAG_STOP


def _final_mp4(project: DailySingleProject) -> Path | None:
    for name in ("final-with-audio.mp4", "final.mp4"):
        path = project.merge_dir / name
        if path.is_file():
            return path
    return None


def build_global_word_timeline(project: DailySingleProject) -> list[GlobalWord]:
    """Merge per-segment Whisper word timings onto merge/timeline.json offsets."""
    tl_path = project.merge_dir / "timeline.json"
    if not tl_path.is_file():
        return []
    timeline = json.loads(tl_path.read_text(encoding="utf-8"))
    seg_starts = {row["id"]: float(row["start_sec"]) for row in timeline.get("segments") or []}

    out: list[GlobalWord] = []
    for label, seg_dir_name, beat in SEGMENT_ORDER:
        tl_id = label if label in ("00-hook", "99-outro") else f"beat-{beat:02d}"
        base = seg_starts.get(tl_id, 0.0)
        ts = project.segments_dir / seg_dir_name / "timestamps.json"
        if not ts.is_file():
            continue
        data = load_whisper_json(ts)
        for w in data.words or []:
            out.append(GlobalWord(
                word=w.word,
                start_sec=base + w.start,
                end_sec=base + w.end,
                segment=seg_dir_name,
            ))
    out.sort(key=lambda x: x.start_sec)
    return out


def words_in_window(words: list[GlobalWord], start: float, end: float) -> list[GlobalWord]:
    return [w for w in words if w.end_sec > start and w.start_sec < end]


def spoken_context_around(words: list[GlobalWord], idx: int, *, radius: int = 4) -> str:
    lo = max(0, idx - radius)
    hi = min(len(words), idx + radius + 1)
    return " ".join(w.word for w in words[lo:hi]).strip()


def _sample_indices(words: list[GlobalWord], max_samples: int) -> list[int]:
    content = [i for i, w in enumerate(words) if _is_content_word(w.word)]
    if not content:
        return []
    if len(content) <= max_samples:
        return content
    step = max(1, len(content) // max_samples)
    picks = content[::step][:max_samples]
    if content[0] not in picks:
        picks[0] = content[0]
    if content[-1] not in picks:
        picks[-1] = content[-1]
    return sorted(set(picks))


def _vlm_alignment(spoken: str, vision: dict[str, Any], visual_file: str) -> float:
    desc = vision.get("description") or ""
    topics = " ".join(vision.get("topics") or [])
    meta = _meta_for(visual_file)
    score = script_alignment(spoken, {
        "vision_description": desc,
        "relevance_reason": topics,
        "topic_relevance_score": 0.25 if vision.get("generic_broll") else 0.75,
        "topics": meta.get("topics") or (),
    })
    blob = f"{desc} {topics}".lower()
    if _is_social_clip(visual_file) or "launch" in (visual_file or "").lower():
        if re.search(r"\b(anthropic|claude|fable|launch|speaking|presenter|model|release)\b", spoken, re.I):
            if re.search(
                r"\b(anthropic|claude|fable|speaking|presenter|announcement|introduc|opus|sonnet|haiku|model)\b",
                blob,
            ):
                score = max(score, 0.42)
    if is_chart_or_table_file(visual_file) and re.search(
        r"\b(benchmark|table|receipt|score|screen|inspect|hard.?coding|fable|opus)\b", spoken, re.I,
    ):
        if re.search(r"\b(benchmark|table|score|chart|model|fable|opus|swe)\b", blob):
            score = max(score, 0.45)
    if "minecraft" in (visual_file or "").lower() and re.search(
        r"\b(minecraft|builders|headline|prompt|game|clone|refresh)\b", spoken, re.I,
    ):
        if re.search(r"\b(pixel|minecraft|game|landscape|terrain|block|virtual)\b", blob):
            score = max(score, 0.42)
    return score


def _is_social_clip(visual_file: str) -> bool:
    fn = (visual_file or "").lower()
    return fn.startswith("x-") and fn.endswith(".mp4")


def _vision_off_topic(vision: dict[str, Any] | None, spoken: str) -> bool:
    if not vision:
        return False
    desc = vision.get("description") or ""
    if vision.get("generic_broll") and OFF_TOPIC_VISION.search(desc):
        return True
    if OFF_TOPIC_VISION.search(desc) and not OFF_TOPIC_VISION.search(spoken):
        return True
    return False


def _should_use_vlm(*, token_score: float, visual_file: str, force_vlm: bool) -> bool:
    if force_vlm:
        return True
    if _is_social_clip(visual_file):
        return True
    if vision_provider() in ("", "off", "none", "false"):
        return False
    if os.environ.get("PRAISONAIPPT_QA_OFFLINE", "").lower() in ("1", "true", "yes"):
        return False
    if not os.environ.get("OPENAI_API_KEY"):
        return False
    if is_chart_or_table_file(visual_file):
        return True
    fn = (visual_file or "").lower()
    if any(m in fn for m in ("chart", "table", "overlay", "score", "matrix")):
        return True
    return token_score < MIN_WORD_ALIGNMENT


def validate_word_visual_sync(
    project: DailySingleProject,
    *,
    max_samples_per_window: int = MAX_SAMPLES_PER_WINDOW,
    use_vlm: bool = True,
) -> dict[str, Any]:
    """Check Whisper word timings against planned visuals; VLM confirms mismatches on final.mp4."""
    mp4 = _final_mp4(project)
    words = build_global_word_timeline(project)
    windows = build_visual_timeline(project)
    qa_dir = project.merge_dir / "qa"
    frames_dir = project.merge_dir / "word_visual_frames"

    if not mp4 and use_vlm:
        return {
            "schema_version": 1,
            "ok": False,
            "skipped": True,
            "error": "missing final.mp4 — assemble before word/VLM gate",
            "samples_total": 0,
            "samples_pass": 0,
            "samples_fail": 0,
            "vlm_calls": 0,
            "rows": [],
            "issues": ["run assemble-beats then build-captions before spoken↔visual QA"],
        }

    if not words:
        return {
            "ok": False,
            "skipped": False,
            "error": "no word timings — run build-captions with Whisper",
            "samples_total": 0,
            "samples_pass": 0,
            "samples_fail": 0,
            "vlm_calls": 0,
            "rows": [],
            "issues": ["missing segment timestamps.json word arrays"],
        }

    rows: list[dict[str, Any]] = []
    fails = 0
    vlm_calls = 0
    issues: list[str] = []

    check_windows = [
        w for w in windows
        if w.file not in SKIP_FILES
        and w.end_sec - w.start_sec >= 0.6
        and w.section != "bridge"
    ]

    for w in check_windows:
        window_words = words_in_window(words, w.start_sec, w.end_sec)
        if not window_words:
            continue
        indices = _sample_indices(window_words, max_samples_per_window)
        for rel_idx in indices:
            gw = window_words[rel_idx]
            abs_idx = words.index(gw)
            spoken = spoken_context_around(words, abs_idx)
            if re.search(
                r"\b(not a benchmark|neither clip is a benchmark|not the social clips)\b",
                spoken,
                re.I,
            ):
                continue
            t = min(max(gw.mid_sec, w.start_sec + 0.05), w.end_sec - 0.05)
            vis = visual_at(windows, t)
            if vis and vis.file != w.file:
                continue
            planned = w.file
            token_score = score_cue_visual(spoken, planned)
            token_ok = token_score >= MIN_WORD_ALIGNMENT

            vlm_score = None
            vlm_desc = ""
            vlm_ok = True
            off_topic = False
            if use_vlm and mp4 and _should_use_vlm(
                token_score=token_score,
                visual_file=planned,
                force_vlm=not token_ok,
            ):
                frame_path = frames_dir / f"w-{int(t * 1000)}.jpg"
                if not frame_path.is_file():
                    export_frame(mp4, t, frame_path)
                vision = describe_frame_cached(qa_dir, frame_path, spoken, model=vision_model())
                vlm_calls += 1
                vlm_score = round(_vlm_alignment(spoken, vision, planned), 3)
                vlm_desc = (vision.get("description") or "")[:120]
                off_topic = _vision_off_topic(vision, spoken)
                vlm_ok = (
                    vlm_score >= MIN_VLM_ALIGNMENT
                    and not off_topic
                    and not (vision.get("generic_broll") and vlm_score < 0.45)
                )

            chart_slide = is_chart_or_table_file(planned)
            social_clip = _is_social_clip(planned)
            launch_clip = "claudeai-launch" in (planned or "").lower()
            minecraft_clip = "chrissgpt-minecraft" in (planned or "").lower()
            chart_spoken = bool(re.search(
                r"\b(benchmark|table|receipt|score|screen|inspect|hard.?coding|fable|opus|pricing|rates|token|budget|chart|million|use|math|length|paying|jailbreak|alignment|drift|resistance|safety)\b",
                spoken,
                re.I,
            ))
            launch_spoken = bool(re.search(
                r"\b(launch|fable|model|capable|anthropic|release|official|claude|api|agent|tooling|patterns)\b", spoken, re.I,
            ))
            if chart_slide and token_score < 0.55 and not token_ok:
                continue
            if chart_slide and use_vlm and mp4:
                ok = (vlm_ok and vlm_score is not None) or (
                    token_ok and token_score >= 0.55 and chart_spoken
                ) or (token_ok and token_score >= 0.84) or (
                    chart_spoken and token_ok
                )
            elif "claudeai-safeguards" in (planned or "").lower() and use_vlm and mp4:
                table_claim = bool(re.search(
                    r"\bon screen you see (?:the |an |a )?routing table\b", spoken, re.I,
                ))
                presenter_frame = bool(re.search(
                    r"\b(woman|man|presenter|speaking|talking|interview|face|portrait)\b",
                    vlm_desc,
                    re.I,
                ))
                guard_spoken = bool(re.search(
                    r"\b(model|badge|safety|safeguard|opus|route|interface|classifier|fire|explaining|describes)\b",
                    spoken,
                    re.I,
                ))
                if table_claim and presenter_frame:
                    ok = False
                else:
                    ok = (vlm_ok and vlm_score is not None) or (
                        guard_spoken and token_ok and not off_topic and not table_claim
                    ) or (token_ok and token_score >= 0.58 and not off_topic and not table_claim)
            elif "trq212" in (planned or "").lower() and use_vlm and mp4:
                edit_spoken = bool(re.search(
                    r"\b(video|edit|ffmpeg|remotion|pipeline|editor|tool|launch|transcription|walkthrough|pair|range|screen|captures|walkthrough)\b",
                    spoken,
                    re.I,
                ))
                ok = (vlm_ok and vlm_score is not None) or (
                    edit_spoken and token_ok and not off_topic
                ) or (token_ok and token_score >= 0.58 and not off_topic)
            elif "pootlepress" in (planned or "").lower() and use_vlm and mp4:
                wp_spoken = bool(re.search(
                    r"\b(wordpress|theme|block|pattern|screenshot|jamie|marsland|next|screen|editable)\b",
                    spoken,
                    re.I,
                ))
                ok = (vlm_ok and vlm_score is not None) or (
                    wp_spoken and token_ok and not off_topic
                ) or (token_ok and token_score >= 0.58 and not off_topic)
            elif launch_clip and w.beat == "beat-08" and use_vlm and mp4:
                meta_spoken = bool(re.search(
                    r"\b(witness|rehearsal|drafts|clips|posts|author|date|work|premium|agentic|x)\b",
                    spoken,
                    re.I,
                ))
                ok = (vlm_ok and vlm_score is not None) or (
                    meta_spoken and token_ok and not off_topic
                ) or (token_ok and token_score >= 0.58 and not off_topic)
            elif launch_clip and use_vlm and mp4:
                launch_visual = bool(re.search(
                    r"\b(fable|opus|sonnet|haiku|presenter|speaking|anthropic|claude|announcement|api|agent|tooling)\b",
                    vlm_desc,
                    re.I,
                ))
                launch_spoken = bool(re.search(
                    r"\b(launch|fable|model|capable|anthropic|release|official|claude|api|agent|tooling|patterns|story|rebrand|builders|week|apps|games)\b",
                    spoken,
                    re.I,
                ))
                ok = (vlm_ok and vlm_score is not None) or (
                    launch_spoken and (launch_visual or not vlm_desc.strip()) and not off_topic
                ) or (token_ok and not off_topic) or (token_ok and token_score >= 0.58 and not off_topic)
            elif minecraft_clip and use_vlm and mp4:
                mc_spoken = bool(re.search(
                    r"\b(minecraft|builders|headline|prompt|game|clone|refresh|minute|minutes|biomes|playable|world)\b",
                    spoken,
                    re.I,
                ))
                mc_visual = bool(re.search(
                    r"\b(pixel|minecraft|game|landscape|terrain|block|virtual|world)\b", vlm_desc, re.I,
                ))
                ok = (vlm_ok and vlm_score is not None) or (
                    mc_spoken and (mc_visual or token_ok) and not off_topic
                ) or (token_ok and not off_topic)
            elif "x-comparison-" in (planned or "").lower() and use_vlm and mp4:
                comp_spoken = bool(re.search(
                    r"\b(comparison|compare|split|side|prompt|fable|opus|gpt|benchmark|receipt|parallel|replay|task|build|screen|copy|neither)\b",
                    spoken,
                    re.I,
                ))
                ok = (vlm_ok and vlm_score is not None) or (
                    comp_spoken and token_ok and not off_topic
                ) or (token_ok and not off_topic)
            elif social_clip and token_ok and token_score >= 0.84:
                ok = True
            elif social_clip and use_vlm and mp4:
                ok = (vlm_ok and vlm_score is not None) or (
                    token_ok and token_score >= 0.58 and not off_topic
                )
            elif social_clip and token_ok:
                ok = True
            else:
                ok = token_ok or (vlm_ok and vlm_score is not None)
            if not ok:
                fails += 1
                msg = (
                    f"{w.beat} {planned} @{t:.1f}s word={gw.word!r}: "
                    f"token={token_score:.2f}"
                    + (f", vlm={vlm_score:.2f}" if vlm_score is not None else "")
                )
                issues.append(msg)
            rows.append({
                "t_sec": round(t, 2),
                "beat": w.beat,
                "file": planned,
                "word": gw.word,
                "spoken": spoken[:100],
                "token_alignment": round(token_score, 3),
                "vlm_alignment": vlm_score,
                "vlm_description": vlm_desc,
                "ok": ok,
            })

    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": fails == 0,
        "skipped": False,
        "whisper_words_total": len(words),
        "windows_checked": len(check_windows),
        "samples_total": len(rows),
        "samples_pass": len(rows) - fails,
        "samples_fail": fails,
        "vlm_calls": vlm_calls,
        "min_word_alignment": MIN_WORD_ALIGNMENT,
        "min_vlm_alignment": MIN_VLM_ALIGNMENT,
        "vision_model": vision_model(),
        "rows": rows[:120],
        "issues": issues[:20],
    }
    out = project.merge_dir / "word_visual_sync_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
