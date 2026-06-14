"""Fail when narration claims a chart/table on screen but the planned visual is a talking-head clip."""
from __future__ import annotations

import json
import re
from typing import Any

from praisonaippt.daily_single.display_sync import VisualWindow, build_visual_timeline, parse_srt
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.visual_audit import export_frame
from praisonaippt.video_qa.vlm_cache import describe_frame_cached
from praisonaippt.vision_describe import vision_model

ON_SCREEN_TABLE = re.compile(
    r"\bon screen you see (?:the |an |a )?(?:routing table|benchmark table|score card|pricing chart)\b",
    re.I,
)
ON_SCREEN_CHART = re.compile(r"\bon screen you see\b", re.I)
CHART_FILE = re.compile(r"(chart|table|benchmark|pricing|classifier|scorecard)", re.I)
TALKING_HEAD = re.compile(
    r"\b(woman|man|person|presenter|speaking|talking|interview|portrait|face|headshot)\b",
    re.I,
)
ABSTRACT_BROLL = re.compile(r"\b(binary|red circle|abstract|b-?roll|vintage)\b", re.I)


def _is_chart_file(filename: str) -> bool:
    return bool(CHART_FILE.search(filename or ""))


def validate_visual_claims(
    project: DailySingleProject,
    *,
    use_vlm: bool = True,
) -> dict[str, Any]:
    """Check script-locked cues that claim on-screen tables against assembled visuals."""
    srt = project.merge_dir / "final.srt"
    mp4 = project.merge_dir / "final-with-audio.mp4"
    if not mp4.is_file():
        mp4 = project.merge_dir / "final.mp4"
    issues: list[str] = []
    rows: list[dict[str, Any]] = []
    windows = build_visual_timeline(project)
    cues = parse_srt(srt) if srt.is_file() else []
    qa_dir = project.merge_dir / "qa"
    frames_dir = qa_dir / "visual_claim_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    for cue in cues:
        text = cue.get("text") or ""
        if not ON_SCREEN_CHART.search(text):
            continue
        if not ON_SCREEN_TABLE.search(text) and "routing table" not in text.lower():
            continue
        mid = (float(cue["start_sec"]) + float(cue["end_sec"])) / 2
        vis = next(
            (w for w in windows if w.start_sec <= mid < w.end_sec),
            None,
        )
        if not vis:
            issues.append(f"@{mid:.1f}s: claims on-screen table but no visual window")
            rows.append({"t_sec": mid, "spoken": text[:80], "ok": False, "issue": "no window"})
            continue
        if _is_chart_file(vis.file):
            rows.append({"t_sec": mid, "file": vis.file, "spoken": text[:80], "ok": True})
            continue
        row_issue = ""
        ok = True
        if "safeguards" in vis.file.lower() or "launch" in vis.file.lower():
            row_issue = (
                f"speech claims table on screen but visual is {vis.file} "
                "(launch/safeguards livestream — talking head, not a routing table UI)"
            )
            ok = False
        vlm_desc = ""
        if use_vlm and mp4.is_file():
            frame = frames_dir / f"claim-{int(mid * 1000)}.jpg"
            if not frame.is_file():
                export_frame(mp4, mid, frame)
            vision = describe_frame_cached(qa_dir, frame, text, model=vision_model())
            vlm_desc = (vision.get("description") or "")[:160]
            if TALKING_HEAD.search(vlm_desc) or ABSTRACT_BROLL.search(vlm_desc):
                if ON_SCREEN_TABLE.search(text):
                    ok = False
                    row_issue = (
                        f"@{mid:.1f}s: claims routing/benchmark table but frame shows "
                        f"presenter/B-roll — {vlm_desc[:80]}"
                    )
        if not ok:
            issues.append(row_issue or f"@{mid:.1f}s: on-screen table claim mismatches {vis.file}")
        rows.append({
            "t_sec": round(mid, 2),
            "beat": vis.beat,
            "file": vis.file,
            "spoken": text[:100],
            "vlm_description": vlm_desc,
            "ok": ok,
            "issue": row_issue,
        })

    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": len(issues) == 0,
        "claims_checked": len(rows),
        "issues": issues,
        "rows": rows,
    }
    out = project.merge_dir / "visual_claim_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
