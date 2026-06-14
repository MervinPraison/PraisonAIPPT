"""Validate spoken narration matches slides/images on screen (talk-through check)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.audience_language import BANNED_PATTERNS, INSIDER_PHRASES
from praisonaippt.daily_single.display_sync import (
    HOOK_MONTAGE_MIN_ALIGNMENT,
    MIN_ALIGNMENT,
    VisualWindow,
    _meta_for,
    build_visual_timeline,
    parse_srt,
    score_cue_visual,
    visual_at,
)
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.youtube_quality import validate_audience_language, validate_plain_language
from praisonaippt.segment_video.image_selection import tokenise

MIN_WINDOW_ALIGNMENT = MIN_ALIGNMENT
FRAGMENT_MIN_HIT = 0.28
MIN_WINDOW_SEC = 0.75
MIN_CHART_ALIGNMENT = 0.38
SKIP_FILES = frozenset({"heygen.mp4", "none", "claudeai-launch.mp4", "brand-bumper-1080p-hevc.mp4"})
TRANSITION_SKIP = SKIP_FILES | frozenset({"canonical-scroll.mp4"})
GENERIC_FILES = frozenset({"claudeai-launch.mp4"})
FRAG_STOP = frozenset({"the", "a", "an", "and", "or", "that", "this", "in", "to", "of", "for"})

CHART_SPEECH = re.compile(
    r"\b("
    r"benchmark|chart|score|scores|percent|table|stat|leaderboard|views|viral|"
    r"swe-bench|terminal-bench|stripe|million|lines|biology|aav|"
    r"jailbreak|alignment|throughput|ninety|eighty|frontier|tier|tiers|"
    r"pricing|safeguard|classifier|api|glasswing|pok[eé]mon|spire|"
    r"resistance|attack|matrix|decision|red.?team|bars|success.?rate"
    r")\b",
    re.I,
)

CHART_FILE_MARKERS = ("chart", "table", "bench", "stat", "overlay", "classifier", "diagram", "scorecard")
NON_CHART_SLIDES = frozenset({
    "social-capture-hn-beast-ferrari.png",
    "social-capture-reddit-inequality.png",
})

DECISION_TABLE_SPEECH = re.compile(
    r"\b(decision table|decision matrix|different rows|chart rows|table says|table splits)\b",
    re.I,
)

CHART_KIND_RULES: dict[str, dict[str, Any]] = {
    "attack_rate_bar": {
        "must_mention": re.compile(
            r"\b(jailbreak|attack|resistance|adversarial|robustness|red.?team|success rate|cyber stress)\b",
            re.I,
        ),
        "must_not_say": DECISION_TABLE_SPEECH,
    },
    "alignment_eval": {
        "must_mention": re.compile(
            r"\b(alignment|misaligned|off.?track|behaviour|behavior)\b",
            re.I,
        ),
        "must_not_say": re.compile(
            r"\b(decision table|attack success|jailbreak resistance|adversarial robustness)\b",
            re.I,
        ),
    },
    "decision_table": {
        "must_mention": DECISION_TABLE_SPEECH,
        "must_not_say": re.compile(
            r"\b(attack success rate|adversarial robustness|jailbreak resistance bar)\b",
            re.I,
        ),
    },
}


def chart_kind_for(visual_file: str) -> str:
    meta = _meta_for(visual_file)
    kind = str(meta.get("chart_kind") or "")
    if kind:
        return kind
    fn = (visual_file or "").lower()
    if "decision-matrix" in fn or "decision_matrix" in fn:
        return "decision_table"
    if "jailbreak" in fn and "resistance" in fn:
        return "attack_rate_bar"
    if "alignment" in fn and "chart" in fn:
        return "alignment_eval"
    return ""


def validate_chart_kind_parity(spoken: str, visual_file: str) -> tuple[bool, list[str]]:
    """Ensure narration describes the chart type actually on screen — not just shared keywords."""
    kind = chart_kind_for(visual_file)
    rules = CHART_KIND_RULES.get(kind)
    if not rules or not spoken.strip():
        return True, []
    issues: list[str] = []
    must_mention = rules.get("must_mention")
    must_not_say = rules.get("must_not_say")
    if must_not_say and must_not_say.search(spoken):
        issues.append(
            f"spoken describes a different chart type than {Path(visual_file).name} ({kind})"
        )
    if must_mention and not must_mention.search(spoken):
        issues.append(
            f"chart on screen is {kind} — name jailbreak/attack or alignment terms in plain words"
        )
    return len(issues) == 0, issues


def is_chart_or_table_file(filename: str) -> bool:
    """Slides that show numbers, tables, or benchmark charts."""
    fn = (filename or "").lower()
    if not fn or fn in SKIP_FILES:
        return False
    if fn.endswith(".mp4"):
        return False
    if "-point-" in fn or fn in ("beat1-launch-summary.png", "outro-cta.png"):
        return False
    if fn in NON_CHART_SLIDES:
        return False
    if visual_focus_terms(filename):
        return True
    return any(m in fn for m in CHART_FILE_MARKERS)


def visual_focus_terms(visual_file: str) -> tuple[str, ...]:
    meta = _meta_for(visual_file)
    focus = meta.get("visual_focus") or meta.get("required_speech") or ()
    return tuple(str(t) for t in focus)


def spoken_hits_visual_focus(spoken: str, visual_file: str) -> bool:
    """Stat/chart slides must be described in plain terms that match what is on screen."""
    focus = visual_focus_terms(visual_file)
    if not focus:
        return True
    tokens = tokenise(spoken)
    lower = spoken.lower()
    return any(t in tokens or t in lower for t in focus)


def validate_chart_inline(spoken: str, visual_file: str) -> tuple[bool, float, list[str]]:
    """Chart/table on screen must match what is being said (and vice versa)."""
    if not is_chart_or_table_file(visual_file):
        return True, 1.0, []
    if not spoken.strip():
        return False, 0.0, ["chart visible but no spoken narration"]
    score = score_cue_visual(spoken, visual_file)
    topics_ok = spoken_topic_overlap(spoken, visual_file)
    focus_ok = spoken_hits_visual_focus(spoken, visual_file)
    kind_ok, kind_issues = validate_chart_kind_parity(spoken, visual_file)
    mentions_chart = bool(CHART_SPEECH.search(spoken))
    issues: list[str] = []
    if score < MIN_CHART_ALIGNMENT:
        issues.append(f"chart alignment {score:.2f} < {MIN_CHART_ALIGNMENT}")
    if not topics_ok:
        issues.append("spoken words do not match chart topics")
    if not focus_ok:
        issues.append("narration does not describe what is on screen — name the stat or chart in plain words")
    issues.extend(kind_issues)
    ok = score >= MIN_CHART_ALIGNMENT and topics_ok and focus_ok and kind_ok
    if not ok and focus_ok and kind_ok and score >= MIN_WINDOW_ALIGNMENT:
        ok = True
    if ok and not mentions_chart and score < 0.55:
        ok = False
        issues.append("narration loosely related — name what the chart shows in plain words")
    elif not ok and not mentions_chart and topics_ok and not kind_ok:
        issues.append("narration does not describe what the chart shows — add plain terms")
    return ok, score, issues


def validate_srt_plain_language(cues: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    """Spoken captions must stay non-developer friendly."""
    issues: list[str] = []
    for cue in cues:
        text = cue.get("text") or ""
        lower = text.lower()
        for pat, hint in BANNED_PATTERNS + INSIDER_PHRASES:
            if re.search(pat, lower, re.I):
                issues.append(f"@{cue.get('start_sec', 0):.1f}s: {hint}")
    return len(issues) == 0, issues


def validate_speech_needs_visual(
    windows: list[VisualWindow],
    cues: list[dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    """Flag factual/chart speech with no slide on screen — needs image or slide."""
    rows: list[dict[str, Any]] = []
    fails = 0

    for cue in cues:
        dur = float(cue["end_sec"]) - float(cue["start_sec"])
        if dur < MIN_WINDOW_SEC:
            continue
        spoken = cue.get("text") or ""
        if not CHART_SPEECH.search(spoken):
            continue
        mid = (float(cue["start_sec"]) + float(cue["end_sec"])) / 2
        vis = visual_at(windows, mid)
        skip_file = vis.file in SKIP_FILES if vis else False
        if vis and vis.file == "claudeai-launch.mp4" and vis.beat != "00-hook":
            skip_file = False
        has_slide = (
            vis is not None
            and not skip_file
            and vis.file not in GENERIC_FILES
            and vis.section != "bridge"
        )
        if vis and vis.file == "claudeai-launch.mp4" and vis.beat != "00-hook":
            has_slide = spoken_topic_overlap(spoken, vis.file)
        ok = has_slide
        if not ok:
            fails += 1
        rows.append({
            "start_sec": round(float(cue["start_sec"]), 2),
            "end_sec": round(float(cue["end_sec"]), 2),
            "spoken": spoken[:100],
            "on_screen": vis.file if vis else "none",
            "ok": ok,
            "issue": "" if ok else "spoken chart/fact content — add matching slide or image",
        })

    return fails == 0, rows


def validate_chart_windows(
    windows: list[VisualWindow],
    cues: list[dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    """While a chart/table is visible, narration must describe it in plain language."""
    rows: list[dict[str, Any]] = []
    fails = 0

    for w in windows:
        if w.file in SKIP_FILES or not is_chart_or_table_file(w.file):
            continue
        if w.section == "overview":
            continue
        if w.end_sec - w.start_sec < MIN_WINDOW_SEC:
            continue
        overlapping = [
            c for c in cues
            if w.start_sec <= (float(c["start_sec"]) + float(c["end_sec"])) / 2 < w.end_sec
        ]
        if not overlapping:
            fails += 1
            rows.append({
                "start_sec": round(w.start_sec, 2),
                "end_sec": round(w.end_sec, 2),
                "beat": w.beat,
                "file": w.file,
                "spoken": "",
                "chart_alignment": 0.0,
                "ok": False,
                "issues": ["no spoken cue while chart visible"],
            })
            continue
        worst_ok = True
        worst_score = 1.0
        worst_spoken = ""
        worst_issues: list[str] = []
        for cue in overlapping:
            spoken = cue.get("text") or ""
            ok, score, issues = validate_chart_inline(spoken, w.file)
            if not ok:
                worst_ok = False
                worst_spoken = spoken
                worst_score = min(worst_score, score)
                worst_issues = issues
        if not worst_ok:
            fails += 1
        rows.append({
            "start_sec": round(w.start_sec, 2),
            "end_sec": round(w.end_sec, 2),
            "beat": w.beat,
            "file": w.file,
            "spoken": worst_spoken[:120],
            "chart_alignment": worst_score,
            "ok": worst_ok,
            "issues": worst_issues,
        })

    return fails == 0, rows


def _content_tokens(text: str) -> set[str]:
    return tokenise(text) - FRAG_STOP


def fragment_token_hit(fragment: str, spoken: str) -> float:
    frag = _content_tokens(fragment)
    if not frag:
        return 1.0
    spoken_tokens = _content_tokens(spoken)
    return len(frag & spoken_tokens) / len(frag)


def _overlaps(w: VisualWindow, cue: dict[str, Any]) -> bool:
    return w.start_sec < cue["end_sec"] and w.end_sec > cue["start_sec"]


def best_spoken_for_window(w: VisualWindow, cues: list[dict[str, Any]]) -> str:
    """Pick narration that best describes what is on screen for the full window."""
    overlapping = [c for c in cues if _overlaps(w, c)]
    if overlapping:
        if visual_focus_terms(w.file) or is_chart_or_table_file(w.file):
            return max(
                overlapping,
                key=lambda c: (
                    int(spoken_hits_visual_focus(c["text"], w.file)),
                    score_cue_visual(c["text"], w.file),
                ),
            )["text"]
        return max(overlapping, key=lambda c: score_cue_visual(c["text"], w.file))["text"]
    mid = (w.start_sec + w.end_sec) / 2
    primary = _cue_at_mid(cues, mid)
    return primary["text"] if primary else ""


def _cue_for_transition(
    cues: list[dict[str, Any]],
    t: float,
    *,
    vis_start: float | None = None,
) -> dict[str, Any] | None:
    """Pick SRT cue aligned to a visual boundary (not a stale overlapping cue)."""
    if vis_start is not None:
        near = [
            c for c in cues
            if abs(float(c["start_sec"]) - vis_start) < 0.9
        ]
        if near:
            return min(near, key=lambda c: abs(float(c["start_sec"]) - t))
    return _cue_at_mid(cues, t)


def _cue_at_mid(cues: list[dict[str, Any]], t: float) -> dict[str, Any] | None:
    for cue in cues:
        if cue["start_sec"] <= t < cue["end_sec"]:
            return cue
    return None


def spoken_topic_overlap(spoken: str, visual_file: str) -> bool:
    meta = _meta_for(visual_file)
    topics = set(meta.get("topics") or ())
    topics |= set(meta.get("visual_focus") or ())
    blob = tokenise(str(meta.get("vision_description") or ""))
    spoken_tokens = tokenise(spoken)
    if spoken_tokens & (topics | blob):
        return True
    focus = visual_focus_terms(visual_file)
    if focus:
        return (
            spoken_hits_visual_focus(spoken, visual_file)
            and score_cue_visual(spoken, visual_file) >= MIN_WINDOW_ALIGNMENT
        )
    return False


def _transition_inline_ok(spoken: str, vis: VisualWindow) -> tuple[bool, float, list[str]]:
    """Per-cue check at slide boundaries — stricter for charts, lighter for point slides."""
    fn = (vis.file or "").lower()
    if fn in TRANSITION_SKIP:
        return True, 1.0, []
    score = score_cue_visual(spoken, vis.file)
    if "-point-" in fn:
        ok = score >= MIN_WINDOW_ALIGNMENT
        issues = [] if ok else [f"alignment {score:.2f} < {MIN_WINDOW_ALIGNMENT}"]
        return ok, score, issues
    if is_chart_or_table_file(vis.file):
        return validate_hook_sample_inline(spoken, vis)
    if fn.endswith(".mp4") and score >= MIN_WINDOW_ALIGNMENT:
        return True, score, []
    if score >= 0.45:
        return True, score, []
    return validate_hook_sample_inline(spoken, vis)


def validate_transition_points(
    windows: list[VisualWindow],
    cues: list[dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    """At every image change and every cue start, speech must match what is on screen."""
    from praisonaippt.daily_single.display_sync import visual_at

    rows: list[dict[str, Any]] = []
    fails = 0
    sample_times: set[float] = set()

    for w in windows:
        if w.file in SKIP_FILES or w.section == "bridge":
            continue
        if w.end_sec - w.start_sec < MIN_WINDOW_SEC:
            continue
        sample_times.add(round(w.start_sec + 0.15, 3))

    for cue in cues:
        t = float(cue["start_sec"])
        vis = visual_at(windows, t + 0.1)
        if vis is None or vis.file in TRANSITION_SKIP or vis.section == "bridge":
            continue
        if vis.end_sec - vis.start_sec < MIN_WINDOW_SEC:
            continue
        sample_times.add(round(t + 0.1, 3))

    for t in sorted(sample_times):
        vis = visual_at(windows, t)
        if vis is None or vis.file in TRANSITION_SKIP or vis.section == "bridge":
            continue
        cue = _cue_for_transition(cues, t, vis_start=vis.start_sec)
        if cue is None:
            continue
        spoken = cue.get("text") or ""
        ok, score, issues = _transition_inline_ok(spoken, vis)
        if not ok:
            fails += 1
        rows.append({
            "start_sec": round(t, 2),
            "window_start": round(vis.start_sec, 2),
            "window_end": round(vis.end_sec, 2),
            "beat": vis.beat,
            "file": vis.file,
            "spoken": spoken[:100],
            "alignment": score,
            "ok": ok,
            "issues": issues,
        })

    return fails == 0, rows


def _all_overlapping_cues_pass(w: VisualWindow, cues: list[dict[str, Any]]) -> tuple[bool, str, float]:
    """Every cue heard while a slide is visible must match that slide (worst-cue-wins)."""
    overlapping = [c for c in cues if _overlaps(w, c)]
    if not overlapping:
        return False, "", 0.0
    worst_ok = True
    worst_score = 1.0
    worst_spoken = ""
    for cue in overlapping:
        spoken = cue.get("text") or ""
        if w.section == "overview" and w.script_fragment:
            ok, score, _ = validate_hook_sample_inline(spoken, w)
        elif is_chart_or_table_file(w.file):
            ok, score, _ = validate_chart_inline(spoken, w.file)
        else:
            score = score_cue_visual(spoken, w.file)
            ok = score >= MIN_WINDOW_ALIGNMENT and spoken_topic_overlap(spoken, w.file)
        if not ok:
            worst_ok = False
            worst_spoken = spoken
            worst_score = min(worst_score, score)
        elif score < worst_score:
            worst_score = score
            worst_spoken = spoken
    if worst_ok and overlapping:
        best = max(overlapping, key=lambda c: score_cue_visual(c["text"], w.file))
        return True, best["text"], score_cue_visual(best["text"], w.file)
    return worst_ok, worst_spoken, worst_score


def validate_hook_sample_inline(
    spoken: str,
    window: VisualWindow | None,
) -> tuple[bool, float, list[str]]:
    """Check spoken words at sample time match the slide/image on screen."""
    if window is None or window.file in SKIP_FILES:
        return True, 1.0, []
    if not spoken.strip():
        return False, 0.0, ["no spoken cue at sample time"]

    issues: list[str] = []
    if window.section == "bridge" and (
        window.file == "heygen.mp4"
        or re.search(r"\b(clips|started|unpack|watch|mean)\b", spoken, re.I)
    ):
        return True, 1.0, []

    if window.section == "overview" and window.script_fragment:
        hit = fragment_token_hit(window.script_fragment, spoken)
        topic = score_cue_visual(window.script_fragment, window.file)
        ok = (
            hit >= FRAGMENT_MIN_HIT
            and topic >= HOOK_MONTAGE_MIN_ALIGNMENT
            and spoken_topic_overlap(window.script_fragment or spoken, window.file)
        )
        if hit < FRAGMENT_MIN_HIT:
            issues.append(f"montage fragment not inline (hit={hit:.2f})")
        if topic < HOOK_MONTAGE_MIN_ALIGNMENT:
            issues.append(f"topic alignment {topic:.2f} < {HOOK_MONTAGE_MIN_ALIGNMENT}")
        if not spoken_topic_overlap(window.script_fragment or spoken, window.file):
            issues.append("spoken topic does not match slide")
        return ok, max(hit, topic), issues

    score = score_cue_visual(spoken, window.file)
    ok = score >= MIN_WINDOW_ALIGNMENT and spoken_topic_overlap(spoken, window.file)
    if score < MIN_WINDOW_ALIGNMENT:
        issues.append(f"alignment {score:.2f} < {MIN_WINDOW_ALIGNMENT}")
    if not spoken_topic_overlap(spoken, window.file):
        issues.append("spoken topic does not match on-screen visual")
    if window.section != "overview":
        chart_ok, chart_score, chart_issues = validate_chart_inline(spoken, window.file)
        if not chart_ok:
            ok = False
            issues.extend(chart_issues)
        return ok, max(score, chart_score), issues
    return ok, score, issues


def validate_montage_fragments(
    windows: list[VisualWindow],
    cues: list[dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    """Each hook overview flash must map a script fragment → spoken overview cue → slide."""
    overview_spoken = cues[1]["text"] if len(cues) >= 2 else ""
    rows: list[dict[str, Any]] = []
    fails = 0

    for w in [x for x in windows if x.beat == "00-hook" and x.section == "overview"]:
        frag = (w.script_fragment or "").strip()
        hit = fragment_token_hit(frag, overview_spoken)
        topic = score_cue_visual(frag or overview_spoken, w.file)
        frag_ok = hit >= FRAGMENT_MIN_HIT
        topic_ok = topic >= HOOK_MONTAGE_MIN_ALIGNMENT and spoken_topic_overlap(frag or overview_spoken, w.file)
        ok = frag_ok and topic_ok
        if not ok:
            fails += 1
        rows.append({
            "start_sec": round(w.start_sec, 2),
            "end_sec": round(w.end_sec, 2),
            "file": w.file,
            "script_fragment": frag,
            "fragment_in_overview": round(hit, 3),
            "topic_alignment": topic,
            "ok": ok,
        })

    return fails == 0, rows


def validate_visual_windows(
    windows: list[VisualWindow],
    cues: list[dict[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    """While each slide/image is on screen, overlapping speech must describe it."""
    rows: list[dict[str, Any]] = []
    fails = 0

    for w in windows:
        if w.file in SKIP_FILES:
            continue
        if w.section == "bridge":
            continue
        dur = w.end_sec - w.start_sec
        if dur < MIN_WINDOW_SEC:
            continue

        mid = (w.start_sec + w.end_sec) / 2
        overlapping = [c for c in cues if _overlaps(w, c)]

        if w.section == "overview" and w.script_fragment:
            spoken = w.script_fragment
            threshold = HOOK_MONTAGE_MIN_ALIGNMENT
        else:
            overlapping = [c for c in cues if _overlaps(w, c)]
            if not overlapping:
                fails += 1
                rows.append({
                    "start_sec": round(w.start_sec, 2),
                    "end_sec": round(w.end_sec, 2),
                    "beat": w.beat,
                    "file": w.file,
                    "spoken": "",
                    "alignment": 0.0,
                    "ok": False,
                    "issue": "no spoken cue while slide visible",
                })
                continue
            spoken = best_spoken_for_window(w, cues)
            threshold = MIN_WINDOW_ALIGNMENT

        score = score_cue_visual(spoken, w.file)
        focus_ok = spoken_hits_visual_focus(spoken, w.file) if w.section != "overview" else True
        ok = score >= threshold and spoken_topic_overlap(spoken, w.file) and focus_ok
        if not ok:
            fails += 1
        issue = ""
        if not focus_ok:
            issue = "narration does not describe what is on screen — name the stat or chart in plain words"
        rows.append({
            "start_sec": round(w.start_sec, 2),
            "end_sec": round(w.end_sec, 2),
            "beat": w.beat,
            "section": w.section,
            "file": w.file,
            "spoken": spoken[:120],
            "alignment": score,
            "threshold": threshold,
            "ok": ok,
            "issue": issue,
        })

    return fails == 0, rows


def validate_spoken_visual_sync(project: DailySingleProject) -> dict[str, Any]:
    srt_path = project.merge_dir / "final.srt"
    if not srt_path.is_file():
        raise FileNotFoundError(f"Missing {srt_path} — run build-captions first")

    cues = parse_srt(srt_path)
    windows = build_visual_timeline(project)
    transitions_ok, transition_rows = validate_transition_points(windows, cues)
    montage_ok, montage_rows = validate_montage_fragments(windows, cues)
    windows_ok, window_rows = validate_visual_windows(windows, cues)
    chart_ok, chart_rows = validate_chart_windows(windows, cues)
    coverage_ok, coverage_rows = validate_speech_needs_visual(windows, cues)
    srt_plain_ok, srt_plain_issues = validate_srt_plain_language(cues)
    script_plain_ok, script_plain_issues = validate_plain_language(project)
    audience_ok, audience_issues = validate_audience_language(project)
    plain_ok = srt_plain_ok and script_plain_ok and audience_ok

    slide_words_ok = True
    slide_words: dict[str, Any] = {}
    try:
        from praisonaippt.daily_single.slide_word_map import validate_beat01_slide_word_map

        slide_words_ok, slide_words = validate_beat01_slide_word_map(project)
    except FileNotFoundError:
        pass

    word_visual_ok = True
    word_visual: dict[str, Any] = {}
    mp4 = project.merge_dir / "final-with-audio.mp4"
    if not mp4.is_file():
        mp4 = project.merge_dir / "final.mp4"
    if mp4.is_file():
        from praisonaippt.daily_single.word_visual_sync import validate_word_visual_sync

        word_visual = validate_word_visual_sync(project)
        word_visual_ok = bool(word_visual.get("ok"))
    else:
        word_visual_ok = True
        word_visual = {
            "ok": True,
            "skipped": True,
            "deferred": True,
            "note": "word/VLM gate runs after assemble-beats (s22 + post_build phase gates)",
        }

    transition_fails = sum(1 for r in transition_rows if not r["ok"])
    montage_fails = sum(1 for r in montage_rows if not r["ok"])
    window_fails = sum(1 for r in window_rows if not r["ok"])
    chart_fails = sum(1 for r in chart_rows if not r["ok"])
    coverage_fails = sum(1 for r in coverage_rows if not r["ok"])

    issues: list[str] = []
    for row in transition_rows:
        if not row["ok"]:
            issues.append(
                f"transition {row['beat']} {row['file']} @{row['start_sec']:.1f}s: "
                + "; ".join(row.get("issues") or ["speech does not match slide"])
            )
    for row in montage_rows:
        if not row["ok"]:
            issues.append(
                f"hook montage {row['file']}: fragment not inline "
                f"(hit={row['fragment_in_overview']}, topic={row['topic_alignment']})"
            )
    for row in window_rows:
        if not row["ok"]:
            msg = row.get("issue") or (
                f"alignment {row['alignment']} < {row.get('threshold', MIN_WINDOW_ALIGNMENT)}"
            )
            issues.append(
                f"{row['beat']} {row['file']} @{row['start_sec']:.1f}s: {msg} — "
                f"\"{row.get('spoken', '')[:50]}\""
            )
    for row in chart_rows:
        if not row["ok"]:
            issues.append(
                f"chart {row['file']} @{row['start_sec']:.1f}s: "
                + "; ".join(row.get("issues") or [])
            )
    for row in coverage_rows:
        if not row["ok"]:
            issues.append(
                f"@{row['start_sec']:.1f}s: {row.get('issue')} — \"{row.get('spoken', '')[:50]}\""
            )
    if not slide_words_ok and slide_words:
        for block in (slide_words.get("views_window"), slide_words.get("summary_window")):
            if not block:
                continue
            for row in block.get("slides") or []:
                if not row.get("ok"):
                    issues.append(
                        f"word-map {row['file']}: {row.get('hit_count', 0)} topic hits "
                        f"(need {row.get('min_hits')})"
                    )
    if not word_visual_ok and word_visual.get("issues"):
        issues.extend(word_visual["issues"][:8])

    visual_claim_ok = True
    visual_claim: dict[str, Any] = {}
    if mp4.is_file():
        from praisonaippt.daily_single.visual_claim_audit import validate_visual_claims

        visual_claim = validate_visual_claims(project, use_vlm=bool(word_visual.get("vlm_calls")))
        visual_claim_ok = bool(visual_claim.get("ok"))
        if not visual_claim_ok:
            issues.extend((visual_claim.get("issues") or [])[:6])

    issues.extend(srt_plain_issues[:5])
    issues.extend(script_plain_issues[:5])
    issues.extend(audience_issues[:5])

    report: dict[str, Any] = {
        "schema_version": 3,
        "ok": (
            montage_ok and windows_ok and chart_ok and coverage_ok
            and plain_ok and slide_words_ok and transitions_ok and word_visual_ok
            and visual_claim_ok
        ),
        "transitions_total": len(transition_rows),
        "transitions_pass": len(transition_rows) - transition_fails,
        "transitions_fail": transition_fails,
        "montage_fragments_total": len(montage_rows),
        "montage_fragments_pass": len(montage_rows) - montage_fails,
        "montage_fragments_fail": montage_fails,
        "windows_total": len(window_rows),
        "windows_pass": len(window_rows) - window_fails,
        "windows_fail": window_fails,
        "charts_total": len(chart_rows),
        "charts_pass": len(chart_rows) - chart_fails,
        "charts_fail": chart_fails,
        "coverage_total": len(coverage_rows),
        "coverage_pass": len(coverage_rows) - coverage_fails,
        "coverage_fail": coverage_fails,
        "slide_word_map_ok": slide_words_ok,
        "slide_word_map": slide_words,
        "word_visual_ok": word_visual_ok,
        "word_visual": word_visual,
        "visual_claim_ok": visual_claim_ok,
        "visual_claim": visual_claim,
        "plain_language_ok": plain_ok,
        "plain_language": {
            "srt_ok": srt_plain_ok,
            "script_ok": script_plain_ok,
            "audience_ok": audience_ok,
            "issues": (srt_plain_issues + script_plain_issues + audience_issues)[:15],
        },
        "min_window_alignment": MIN_WINDOW_ALIGNMENT,
        "min_chart_alignment": MIN_CHART_ALIGNMENT,
        "hook_montage_min_alignment": HOOK_MONTAGE_MIN_ALIGNMENT,
        "montage": montage_rows,
        "transitions": transition_rows,
        "windows": window_rows,
        "charts": chart_rows,
        "coverage_gaps": coverage_rows,
        "issues": issues[:25],
    }
    out = project.merge_dir / "spoken_visual_sync_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
