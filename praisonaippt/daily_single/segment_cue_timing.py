"""Map segment.srt cue boundaries to clip/chart durations (scaled to narration)."""
from __future__ import annotations

import re
from pathlib import Path


def _srt_ts(ts: str) -> float:
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_segment_srt(path: Path) -> list[tuple[float, float, str]]:
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


def cue_span_durations(project_root: Path, seg_dir: str, seg_dur: float) -> list[float]:
    """Per-cue durations scaled to actual segment narration length."""
    rows = parse_segment_srt(project_root / "segments" / seg_dir / "segment.srt")
    if not rows:
        return [seg_dur]
    total = rows[-1][1]
    if total <= 0:
        return [seg_dur]
    scale = seg_dur / total
    durs = [(end - start) * scale for start, end, _ in rows]
    drift = seg_dur - sum(durs)
    if durs:
        durs[-1] += drift
    return durs


def clip_durations_for_cues(
    project_root: Path,
    seg_dir: str,
    seg_dur: float,
    cue_to_clip: list[int],
) -> list[float]:
    """Sum cue durations per clip index."""
    cue_durs = cue_span_durations(project_root, seg_dir, seg_dur)
    if not cue_to_clip:
        return [seg_dur]
    n_clips = max(cue_to_clip) + 1
    clip_durs = [0.0] * n_clips
    for i, clip_idx in enumerate(cue_to_clip):
        if i < len(cue_durs):
            clip_durs[clip_idx] += cue_durs[i]
    clip_durs = [max(0.5, d) for d in clip_durs]
    total = sum(clip_durs)
    if total > 0 and abs(total - seg_dur) > 0.05:
        scale = seg_dur / total
        clip_durs = [d * scale for d in clip_durs]
    return clip_durs


def beat4_visual_durations(project_root: Path, seg_dur: float) -> tuple[float, float, float]:
    """Chart → clip → chart tail (matches segments/04-benchmarks/script.md)."""
    durs = cue_span_durations(project_root, "04-benchmarks", seg_dur)
    if len(durs) >= 3:
        chart_d, clip_d, tail_d = durs[0], durs[1], durs[2]
        nudge = min(0.85, clip_d * 0.1)
        return chart_d, clip_d + nudge, max(0.5, tail_d - nudge)
    if len(durs) == 2:
        return durs[0], durs[1], 0.5
    return seg_dur * 0.45, seg_dur * 0.45, seg_dur * 0.1


def beat8_clip_durations(project_root: Path, seg_dur: float) -> list[float]:
    """Comparison splits then voxel Minecraft demos; closing lines stay on last clip."""
    rows = parse_segment_srt(project_root / "segments" / "08-glasswing" / "segment.srt")
    n = max(5, len(rows))
    cue_map = [0, 1, 2, 3] + [1] * (n - 4)
    return clip_durations_for_cues(project_root, "08-glasswing", seg_dur, cue_map)


def beat5_x_clip_durations(project_root: Path, seg_dur: float) -> tuple[list[float], float]:
    """Three curated X clips from first three cues; spire stat from fourth."""
    durs = cue_span_durations(project_root, "05-vision-memory", seg_dur)
    if len(durs) >= 4:
        return [max(0.5, d) for d in durs[:3]], max(0.5, durs[3])
    if len(durs) == 3:
        return [max(0.5, d) for d in durs], 0.0
    per = seg_dur / 3.0
    return [per, per, per], 0.0


def beat9_visual_durations(project_root: Path, seg_dur: float) -> tuple[float, float, float]:
    """Pricing chart → benchmark table for remaining cues."""
    durs = cue_span_durations(project_root, "09-pricing", seg_dur)
    if len(durs) >= 2:
        return durs[0], sum(durs[1:]), 0.0
    if len(durs) == 1:
        return durs[0], 0.5, 0.0
    return seg_dur * 0.42, seg_dur * 0.58, 0.0
