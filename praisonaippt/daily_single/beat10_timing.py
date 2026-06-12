"""Beat 10 chart timing — align jailbreak vs alignment slides to segment VO."""
from __future__ import annotations

import re
from pathlib import Path


def _srt_ts(ts: str) -> float:
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def _parse_segment_srt(path: Path) -> list[tuple[float, float, str]]:
    if not path.is_file():
        return []
    rows: list[tuple[float, float, str]] = []
    for block in re.split(r"\n\n+", path.read_text(encoding="utf-8").strip()):
        lines = block.strip().splitlines()
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        a, b = [x.strip() for x in lines[1].split("-->")]
        body = " ".join(lines[2:]).strip()
        rows.append((_srt_ts(a), _srt_ts(b), body))
    return rows


def beat10_chart_durations(project_root: Path, seg_dur: float) -> tuple[float, float, float]:
    """Return (jailbreak_sec, alignment_sec, summary_sec) from segment.srt cue spans."""
    from praisonaippt.daily_single.segment_cue_timing import cue_span_durations

    durs = cue_span_durations(project_root, "10-alignment", seg_dur)
    if len(durs) >= 3:
        jail_d, align_d, tail_d = durs[0], durs[1], durs[2]
        pad = min(0.3, jail_d * 0.05)
        return max(0.5, jail_d - pad), align_d + pad, tail_d
    if len(durs) == 2:
        return durs[0], durs[1], max(0.5, seg_dur - durs[0] - durs[1])
    return seg_dur * 0.45, seg_dur * 0.35, seg_dur * 0.2
