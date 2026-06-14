"""Assembled-video duplicate clip gate — reject hook teasers and body beats reusing the same MP4."""
from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from praisonaippt.daily_single.display_sync import VisualWindow, build_visual_timeline
from praisonaippt.daily_single.hook_montage import build_hook_montage_plan
from praisonaippt.daily_single.project import DailySingleProject

SKIP_FILES = frozenset({"heygen.mp4", "none", "brand-bumper-1080p-hevc.mp4"})
MAX_MP4_TOTAL_SEC = 38.0
MAX_BODY_BEAT_GROUPS = 1
def _hook_allowed_body_beats(plan: dict[str, Any], filename: str) -> set[str]:
    """Hook teaser may repeat only in the beat it previews (from montage spec)."""
    allowed: set[str] = set()
    for cue in plan.get("cues") or []:
        if str(cue.get("file") or "") != filename or not cue.get("ok"):
            continue
        beat_n = cue.get("beat")
        if beat_n is not None:
            allowed.add(f"beat-{int(beat_n):02d}")
    return allowed


def _is_mp4(filename: str) -> bool:
    return (filename or "").lower().endswith(".mp4")


def _body_beat_groups(windows: list[VisualWindow]) -> list[str]:
    """Distinct beat ids in timeline order (body only, excluding hook/outro)."""
    groups: list[str] = []
    for w in sorted(windows, key=lambda x: x.start_sec):
        if w.beat in ("00-hook", "99-outro"):
            continue
        if not groups or groups[-1] != w.beat:
            groups.append(w.beat)
    return groups


def validate_visual_duplicates(project: DailySingleProject) -> dict[str, Any]:
    """Fail when the same social clip keeps reappearing across hook and body beats."""
    windows = build_visual_timeline(project)
    plan = build_hook_montage_plan(project)
    hook_files = {
        str(c.get("file") or "")
        for c in (plan.get("cues") or [])
        if c.get("ok") and c.get("file")
    }

    by_file: dict[str, list[VisualWindow]] = defaultdict(list)
    for w in windows:
        if w.file in SKIP_FILES or not _is_mp4(w.file):
            continue
        by_file[w.file].append(w)

    issues: list[str] = []
    rows: list[dict[str, Any]] = []

    for fname in sorted(by_file):
        wins = sorted(by_file[fname], key=lambda x: x.start_sec)
        total_sec = sum(w.end_sec - w.start_sec for w in wins)
        beats = sorted({w.beat for w in wins})
        body_groups = _body_beat_groups(wins)
        row_issues: list[str] = []

        if total_sec > MAX_MP4_TOTAL_SEC:
            row_issues.append(
                f"{total_sec:.0f}s on screen (max {MAX_MP4_TOTAL_SEC:.0f}s) — trim or diversify"
            )

        if len(body_groups) > MAX_BODY_BEAT_GROUPS:
            row_issues.append(
                f"body reuse across {len(body_groups)} beat groups "
                f"({', '.join(body_groups)}) — max {MAX_BODY_BEAT_GROUPS}"
            )

        if fname in hook_files:
            allowed = _hook_allowed_body_beats(plan, fname)
            extra_body = [b for b in body_groups if b not in allowed]
            if extra_body:
                row_issues.append(
                    f"hook montage clip reappears in {', '.join(extra_body)} "
                    f"(allowed body beats: {', '.join(sorted(allowed)) or 'none'})"
                )

        if row_issues:
            for msg in row_issues:
                issues.append(f"{fname}: {msg}")

        rows.append({
            "file": fname,
            "beats": beats,
            "body_beat_groups": body_groups,
            "windows": len(wins),
            "total_sec": round(total_sec, 1),
            "hook_teaser": fname in hook_files,
            "ok": len(row_issues) == 0,
            "issues": row_issues,
        })

    ok = len(issues) == 0
    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": ok,
        "files_checked": len(rows),
        "files_fail": sum(1 for r in rows if not r["ok"]),
        "hook_teaser_files": sorted(hook_files),
        "max_mp4_total_sec": MAX_MP4_TOTAL_SEC,
        "max_body_beat_groups": MAX_BODY_BEAT_GROUPS,
        "rows": rows,
        "issues": issues,
    }
    out = project.merge_dir / "visual_duplicate_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
