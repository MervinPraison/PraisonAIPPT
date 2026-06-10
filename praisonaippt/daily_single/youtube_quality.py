"""YouTube-ready quality gates: compelling hook, plain language, professional pacing."""
from __future__ import annotations

import json
import re
from typing import Any

from praisonaippt.daily_single.captions import split_caption_cues
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER

# Unexplained dev jargon — fail if present in spoken scripts.
JARGON_PATTERNS = (
    r"\bmessages api\b",
    r"\bhttp\b",
    r"\brunbooks?\b",
    r"\bclassifier stack\b",
    r"\bdistillation classifiers?\b",
    r"\bmer\.vin\b",
    r"\bmetered api\b",
)

HOOK_STAKES = re.compile(
    r"\b(released|dropped|shipped|launch|miss|changes?|cannot afford|need to know|part of your job)\b",
    re.I,
)
OVERVIEW_TOPICS = re.compile(
    r"\b(fable|mythos|stripe|benchmark|safety|pricing|api|glasswing|pok[eé]mon)\b",
    re.I,
)
OUTRO_SUBSCRIBE = re.compile(r"\bsubscribe\b", re.I)

MAX_BORDERLINE_RATIO = 0.58
MIN_HOOK_SEC = 12.0
MIN_BEAT_ALIGNMENT = 0.42
MIN_TOTAL_SEC = 240.0
MAX_TOTAL_SEC = 540.0


def _all_script_text(project: DailySingleProject) -> str:
    chunks: list[str] = []
    for _label, seg_dir, _beat in SEGMENT_ORDER:
        p = project.segment_script(seg_dir)
        if p.is_file():
            chunks.append(p.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def validate_plain_language(project: DailySingleProject) -> tuple[bool, list[str]]:
    text = _all_script_text(project).lower()
    issues: list[str] = []
    for pat in JARGON_PATTERNS:
        if re.search(pat, text, re.I):
            issues.append(f"jargon: matched /{pat}/")
    return len(issues) == 0, issues


def validate_compelling_hook(cue_map: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if len(cue_map) < 2:
        return False, ["hook cues missing"]
    hook1 = cue_map[0]["spoken"]
    hook2 = cue_map[1]["spoken"]
    if not re.search(r"\b(claude|fable|anthropic|mythos)\b", hook1, re.I):
        issues.append("hook cue 1: missing product name")
    if not HOOK_STAKES.search(hook1):
        issues.append("hook cue 1: missing stakes verb (released/dropped/miss/change…)")
    topic_hits = len(OVERVIEW_TOPICS.findall(hook2))
    if topic_hits < 3:
        issues.append(f"hook cue 2: overview needs ≥3 named topics (got {topic_hits})")
    if "minute" not in hook2.lower() and "cover" not in hook2.lower() and "next" not in hook2.lower():
        issues.append("hook cue 2: add time promise or 'cover' framing")
    return len(issues) == 0, issues


def validate_outro_cta(project: DailySingleProject) -> tuple[bool, list[str]]:
    outro = project.segment_script("99-outro")
    if not outro.is_file():
        return False, ["missing 99-outro/script.md"]
    text = outro.read_text(encoding="utf-8")
    issues: list[str] = []
    if not OUTRO_SUBSCRIBE.search(text):
        issues.append("outro: missing subscribe CTA")
    if "mer.vin" in text.lower():
        issues.append("outro: must not mention mer.vin")
    if "thanks for watching" not in text.lower():
        issues.append("outro: missing 'Thanks for watching'")
    return len(issues) == 0, issues


def validate_pacing(project: DailySingleProject) -> tuple[bool, list[str], dict[str, float]]:
    tl_path = project.merge_dir / "timeline.json"
    if not tl_path.is_file():
        return False, ["missing timeline.json"], {}
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    segs = {s["id"]: s for s in tl.get("segments", [])}
    issues: list[str] = []
    total = float(tl.get("duration_sec") or 0)
    metrics = {"total_sec": total}
    if total < MIN_TOTAL_SEC or total > MAX_TOTAL_SEC:
        issues.append(f"duration {total:.0f}s outside {MIN_TOTAL_SEC:.0f}-{MAX_TOTAL_SEC:.0f}s")
    hook = segs.get("00-hook", {})
    hook_d = float(hook.get("duration_sec") or 0)
    metrics["hook_sec"] = hook_d
    if hook_d < MIN_HOOK_SEC:
        issues.append(f"hook {hook_d:.1f}s too short (<{MIN_HOOK_SEC}s)")
    for i in range(1, 11):
        sid = f"beat-{i:02d}"
        d = float(segs.get(sid, {}).get("duration_sec") or 0)
        if d < 12.0:
            issues.append(f"{sid} {d:.1f}s too short for a chapter (<12s)")
    return len(issues) == 0, issues, metrics


def validate_alignment_quality(cue_map: list[dict[str, Any]]) -> tuple[bool, list[str], dict[str, Any]]:
    borderline = [
        r for r in cue_map
        if r.get("ok") and 0.35 <= float(r.get("alignment", 0)) <= 0.45
    ]
    ratio = len(borderline) / max(1, len(cue_map))
    beat_rows = [r for r in cue_map if str(r.get("beat", "")).startswith("beat-")]
    mean_beat = (
        sum(float(r.get("alignment", 0)) for r in beat_rows) / max(1, len(beat_rows))
    )
    issues: list[str] = []
    if ratio > MAX_BORDERLINE_RATIO:
        issues.append(f"borderline ratio {ratio:.2f} > {MAX_BORDERLINE_RATIO}")
    if mean_beat < MIN_BEAT_ALIGNMENT:
        issues.append(f"mean beat alignment {mean_beat:.2f} < {MIN_BEAT_ALIGNMENT}")
    return len(issues) == 0, issues, {
        "borderline_ratio": round(ratio, 3),
        "mean_beat_alignment": round(mean_beat, 3),
        "borderline_count": len(borderline),
    }


def validate_youtube_quality(
    project: DailySingleProject,
    cue_map: list[dict[str, Any]],
) -> tuple[bool, dict[str, Any]]:
    plain_ok, plain_issues = validate_plain_language(project)
    hook_ok, hook_issues = validate_compelling_hook(cue_map)
    outro_ok, outro_issues = validate_outro_cta(project)
    pace_ok, pace_issues, pace_metrics = validate_pacing(project)
    align_ok, align_issues, align_metrics = validate_alignment_quality(cue_map)

    checks = {
        "plain_language": {"ok": plain_ok, "issues": plain_issues},
        "compelling_hook": {"ok": hook_ok, "issues": hook_issues},
        "outro_cta": {"ok": outro_ok, "issues": outro_issues},
        "pacing": {"ok": pace_ok, "issues": pace_issues, "metrics": pace_metrics},
        "alignment_quality": {"ok": align_ok, "issues": align_issues, "metrics": align_metrics},
    }
    ok = all(c["ok"] for c in checks.values())
    return ok, checks
