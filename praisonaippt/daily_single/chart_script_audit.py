"""Chart script contract — when a chart appears, the script names it in plain words."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.display_sync import _meta_for
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import BEAT_SEGMENT_DIRS
from praisonaippt.daily_single.spoken_visual_sync import (
    CHART_SPEECH,
    is_chart_or_table_file,
    validate_chart_kind_parity,
)

MIN_FOCUS_HITS = 2


def _script_chunk_for_chart(script: str, fname: str) -> str:
    """Use only the script lines that belong to each beat-10 chart."""
    lower = script.lower()
    align_at = lower.find("alignment chart")
    if "alignment" in fname.lower() and align_at >= 0:
        return script[align_at:]
    if "jailbreak" in fname.lower() and align_at >= 0:
        return script[:align_at]
    return script


def _script_for_beat(project: DailySingleProject, beat_n: int) -> str:
    seg = BEAT_SEGMENT_DIRS.get(beat_n, "")
    if not seg:
        return ""
    path = project.segment_script(seg)
    return path.read_text(encoding="utf-8").lower() if path.is_file() else ""


def _check_chart_in_script(
    beat_label: str,
    fname: str,
    script: str,
    issues: list[str],
) -> None:
    if not script.strip():
        issues.append(f"{beat_label}: missing script for chart {fname}")
        return
    meta = _meta_for(fname)
    focus = tuple(meta.get("visual_focus") or meta.get("topics") or ())[:12]
    hits = [t for t in focus if re.search(rf"\b{re.escape(t)}\b", script)]
    if len(hits) < MIN_FOCUS_HITS:
        sample = ", ".join(list(focus)[:4])
        issues.append(
            f"{beat_label}: script must describe {fname} in plain words "
            f"(use terms like: {sample})"
        )
    if not CHART_SPEECH.search(script):
        issues.append(
            f"{beat_label}: add plain chart words (chart, table, matrix, score…) "
            f"when {fname} is on screen"
        )


def validate_chart_script_contract(project: DailySingleProject) -> tuple[bool, list[str], dict[str, Any]]:
    issues: list[str] = []
    checked: set[str] = set()
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))

    for beat_n, beat in (beat_map.get("beats") or {}).items():
        script = _script_for_beat(project, int(beat_n))
        for pool in ("images", "generated"):
            for item in beat.get(pool) or []:
                fname = Path(str(item.get("path") or item.get("filename") or "")).name
                if not fname or fname in checked:
                    continue
                if not is_chart_or_table_file(fname):
                    continue
                checked.add(fname)
                _check_chart_in_script(f"Beat {beat_n}", fname, script, issues)

    assets = project.root / "research/reference-images"
    script10 = _script_for_beat(project, 10)
    for fname in ("jailbreak-resistance.png", "alignment-chart.png"):
        if not (assets / fname).is_file() or fname in checked:
            continue
        checked.add(fname)
        _check_chart_in_script("Beat 10", fname, script10, issues)
        chunk = _script_chunk_for_chart(script10, fname)
        kind_ok, kind_issues = validate_chart_kind_parity(chunk, fname)
        if not kind_ok:
            issues.extend(f"Beat 10: {msg}" for msg in kind_issues)

    gen = assets / "generated" / "beat7-api-table.png"
    if gen.is_file() and "beat7-api-table.png" not in checked:
        _check_chart_in_script("Beat 7", "beat7-api-table.png", _script_for_beat(project, 7), issues)

    return len(issues) == 0, issues, {"charts_checked": len(checked)}
