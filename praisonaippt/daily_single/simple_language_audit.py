"""Dedicated plain-language gate — scripts and captions must stay non-developer friendly."""
from __future__ import annotations

import json
from typing import Any

from praisonaippt.daily_single.audience_language import (
    BANNED_PATTERNS,
    GLOSS_REQUIRED,
    INSIDER_PHRASES,
    validate_audience_language,
)
from praisonaippt.daily_single.display_sync import parse_srt
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.daily_single.youtube_quality import validate_plain_language

import re


def _check_text(text: str, *, source: str) -> list[str]:
    issues: list[str] = []
    lower = text.lower()
    for pat, hint in BANNED_PATTERNS + INSIDER_PHRASES:
        if re.search(pat, lower, re.I):
            issues.append(f"{source}: {hint}")
    for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
        if not sentence.strip():
            continue
        sent_lower = sentence.lower()
        for term_pat, gloss_pat, hint in GLOSS_REQUIRED:
            if re.search(term_pat, sent_lower, re.I) and not re.search(gloss_pat, sent_lower, re.I):
                issues.append(f"{source}: {hint} — in: {sentence[:80]}…")
    return issues


def validate_simple_language(project: DailySingleProject) -> dict[str, Any]:
    """Fail when scripts or final captions use jargon or insider newsroom phrasing."""
    issues: list[str] = []
    rows: list[dict[str, Any]] = []

    for label, seg_dir, _beat in SEGMENT_ORDER:
        path = project.segment_script(seg_dir)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        seg_issues = _check_text(text, source=seg_dir)
        issues.extend(seg_issues)
        rows.append({
            "source": seg_dir,
            "kind": "script",
            "ok": not seg_issues,
            "issues": seg_issues,
        })

    plain_ok, plain_issues = validate_plain_language(project)
    for msg in plain_issues:
        if msg not in issues:
            issues.append(msg)

    srt_path = project.merge_dir / "final.srt"
    if srt_path.is_file():
        for cue in parse_srt(srt_path):
            text = cue.get("text") or ""
            cue_issues = _check_text(text, source=f"final.srt@{cue.get('start_sec', 0):.1f}s")
            issues.extend(cue_issues)
            if cue_issues:
                rows.append({
                    "source": "final.srt",
                    "kind": "caption",
                    "start_sec": cue.get("start_sec"),
                    "ok": False,
                    "issues": cue_issues,
                })

    audience_ok, _ = validate_audience_language(project)
    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": len(issues) == 0 and plain_ok and audience_ok,
        "segments_checked": len(rows),
        "issues": issues[:30],
        "rows": rows[:40],
        "plain_language_ok": plain_ok,
        "audience_language_ok": audience_ok,
    }
    out = project.merge_dir / "simple_language_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
