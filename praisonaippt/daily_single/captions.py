"""Build on-point SRT from segment scripts + Whisper timing (not raw transcription)."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.segment_video.align import match_fragment_to_words
from praisonaippt.segment_video.media import ffprobe_duration
from praisonaippt.segment_video.timeline import write_cue_timings_srt
from praisonaippt.transcript_loader import load_whisper_json
from praisonaippt.segment_video.script_text import narration_text_for_tts

_whisper_model = None


def split_caption_cues(text: str) -> list[str]:
    """One SRT cue per sentence — same density as June roundup verses."""
    clean = narration_text_for_tts(text)
    parts = re.split(r"(?<=[.!?])\s+", clean.strip())
    return [p.strip() for p in parts if p.strip()]


def _load_whisper():
    global _whisper_model
    if _whisper_model is None:
        os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
        import whisper
        _whisper_model = whisper.load_model("base")
    return _whisper_model


def _transcribe_with_module(mp3: Path, ts: Path) -> None:
    model = _load_whisper()
    result = model.transcribe(str(mp3), word_timestamps=True)
    words: list[dict] = []
    for seg in result.get("segments") or []:
        for w in seg.get("words") or []:
            words.append({"word": w.get("word", ""), "start": w["start"], "end": w["end"]})
    payload = {
        "text": result.get("text", ""),
        "segments": [
            {"id": i, "start": s["start"], "end": s["end"], "text": s.get("text", ""), "words": s.get("words")}
            for i, s in enumerate(result.get("segments") or [])
        ],
        "words": words,
        "source": "local-whisper",
    }
    ts.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _proportional_word_timestamps(mp3: Path, script_path: Path, ts: Path) -> None:
    """When Whisper fails, map script words to audio duration (TTS matches script)."""
    text = narration_text_for_tts(script_path.read_text(encoding="utf-8"))
    raw_words = re.findall(r"\S+", text)
    if not raw_words:
        return
    total = ffprobe_duration(mp3)
    weights = [max(1, len(re.sub(r"[^\w']+", "", w.lower())) or 1) for w in raw_words]
    total_w = sum(weights)
    t = 0.0
    words: list[dict] = []
    segments: list[dict] = []
    seg_words: list[dict] = []
    seg_text: list[str] = []
    seg_start = 0.0
    for word_raw, weight in zip(raw_words, weights):
        dur = total * (weight / total_w)
        entry = {"word": word_raw, "start": round(t, 3), "end": round(t + dur, 3)}
        words.append(entry)
        seg_words.append(entry)
        seg_text.append(word_raw)
        t += dur
        if word_raw.rstrip().endswith((".", "!", "?")):
            segments.append({
                "id": len(segments),
                "start": seg_start,
                "end": round(t, 3),
                "text": " ".join(seg_text),
                "words": seg_words,
            })
            seg_start = t
            seg_words = []
            seg_text = []
    if seg_words:
        segments.append({
            "id": len(segments),
            "start": seg_start,
            "end": round(t, 3),
            "text": " ".join(seg_text),
            "words": seg_words,
        })
    ts.write_text(
        json.dumps({
            "text": text,
            "duration": total,
            "segments": segments,
            "words": words,
            "source": "proportional",
        }, indent=2),
        encoding="utf-8",
    )


def _ensure_transcript(mp3: Path, ts: Path, *, force: bool = False) -> None:
    if ts.is_file() and not force and ts.stat().st_mtime >= mp3.stat().st_mtime:
        try:
            from praisonaippt.transcript_loader import load_whisper_json

            raw = json.loads(ts.read_text(encoding="utf-8"))
            data = load_whisper_json(ts)
            if len(data.words or []) >= 8 and str(raw.get("source") or "") != "proportional":
                return
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    from praisonaippt.daily_single.openai_whisper import transcribe_mp3_openai, whisper_provider

    provider = whisper_provider()
    if provider in ("openai", "auto"):
        try:
            if transcribe_mp3_openai(mp3, ts):
                return
        except Exception:
            pass
    if provider == "openai":
        script = mp3.parent / "script.md"
        if script.is_file():
            _proportional_word_timestamps(mp3, script, ts)
        return
    env = os.environ.copy()
    env.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    try:
        subprocess.run(
            ["praisonaippt", "transcribe", "-i", str(mp3), "-o", str(ts)],
            check=True,
            capture_output=True,
            env=env,
            timeout=600,
        )
        if ts.is_file():
            return
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, subprocess.TimeoutExpired):
        pass
    try:
        _transcribe_with_module(mp3, ts)
        if ts.is_file():
            return
    except Exception:
        pass
    script = mp3.parent / "script.md"
    if script.is_file():
        _proportional_word_timestamps(mp3, script, ts)


def _proportional_cues(sentences: list[str], total_dur: float) -> list[dict]:
    weights = [max(1, len(s.split())) for s in sentences]
    total_w = sum(weights)
    t = 0.0
    cues: list[dict] = []
    for sent, w in zip(sentences, weights):
        dur = max(0.8, total_dur * (w / total_w))
        cues.append({
            "audio_start_sec": round(t, 3),
            "duration_sec": round(dur, 3),
            "script_fragment": sent,
        })
        t += dur
    if cues and t > total_dur:
        cues[-1]["duration_sec"] = round(max(0.8, cues[-1]["duration_sec"] - (t - total_dur)), 3)
    return cues


def _align_sentences(sentences: list[str], ts_path: Path | None, total_dur: float) -> list[dict]:
    if ts_path and ts_path.is_file():
        try:
            data = load_whisper_json(ts_path)
            cues: list[dict] = []
            min_start = 0.0
            for sent in sentences:
                span = match_fragment_to_words(sent, data, min_start=min_start)
                if not span:
                    break
                start, end = span
                start = max(min_start, start)
                end = max(end, start + 0.4)
                min_start = end
                cues.append({
                    "audio_start_sec": round(start, 3),
                    "duration_sec": round(end - start, 3),
                    "script_fragment": sent,
                })
            if len(cues) == len(sentences):
                last = cues[-1]
                last_end = last["audio_start_sec"] + last["duration_sec"]
                if last_end < total_dur - 0.2:
                    last["duration_sec"] = round(total_dur - last["audio_start_sec"], 3)
                return cues
        except Exception:
            pass
    return _proportional_cues(sentences, total_dur)


def build_segment_captions(seg_dir: Path) -> Path:
    script = seg_dir / "script.md"
    mp3 = seg_dir / "narration.mp3"
    if not script.is_file() or not mp3.is_file():
        raise FileNotFoundError(f"Need script.md + narration.mp3 in {seg_dir}")
    ts = seg_dir / "timestamps.json"
    _ensure_transcript(mp3, ts)
    sentences = split_caption_cues(script.read_text(encoding="utf-8"))
    if not sentences:
        raise RuntimeError(f"No caption cues in {script}")
    total = ffprobe_duration(mp3)
    ts_use = ts if ts.is_file() else None
    cues = _align_sentences(sentences, ts_use, total)
    return write_cue_timings_srt(seg_dir, cues)


def _parse_srt(text: str) -> list[tuple[float, float, str]]:
    import re as _re
    blocks = _re.split(r"\n\n+", text.strip())
    rows: list[tuple[float, float, str]] = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        a, b = [x.strip() for x in lines[1].split("-->")]
        body = " ".join(lines[2:]).strip()
        rows.append((_srt_ts(a), _srt_ts(b), body))
    return rows


def _srt_ts(ts: str) -> float:
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def _fmt_ts(sec: float) -> str:
    ms = int(round((sec % 1) * 1000))
    s = int(sec) % 60
    m = (int(sec) // 60) % 60
    h = int(sec) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def merge_final_srt(project: DailySingleProject) -> Path:
    timeline_path = project.merge_dir / "timeline.json"
    if not timeline_path.is_file():
        raise FileNotFoundError(f"Missing {timeline_path} — run assemble-beats first")
    import json
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    seg_starts = {row["id"]: float(row["start_sec"]) for row in timeline.get("segments", [])}

    id_map = {"00-hook": "00-hook", "99-outro": "99-outro"}
    for i in range(1, 11):
        id_map[f"beat-{i:02d}"] = f"beat-{i:02d}"

    merged: list[tuple[float, float, str]] = []
    for label, seg_dir_name, _beat in SEGMENT_ORDER:
        tl_id = label if label in ("00-hook", "99-outro") else f"beat-{_beat:02d}"
        base = seg_starts.get(tl_id, 0.0)
        srt = project.segments_dir / seg_dir_name / "segment.srt"
        if not srt.is_file():
            build_segment_captions(project.segments_dir / seg_dir_name)
        for start, end, body in _parse_srt(srt.read_text(encoding="utf-8")):
            merged.append((base + start, base + end, body))

    out = project.merge_dir / "final.srt"
    lines = [
        f"{i}\n{_fmt_ts(s)} --> {_fmt_ts(e)}\n{body}\n"
        for i, (s, e, body) in enumerate(merged, 1)
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(merged)} cues)")
    return out


def build_all_captions(project: DailySingleProject) -> Path:
    for _label, seg_dir_name, _beat in SEGMENT_ORDER:
        build_segment_captions(project.segments_dir / seg_dir_name)
        print(f"Captions {seg_dir_name}")
    return merge_final_srt(project)
