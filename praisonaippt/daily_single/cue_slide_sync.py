"""Align slide changes to SRT cues — one image per spoken beat."""
from __future__ import annotations

import re
from pathlib import Path

from praisonaippt.daily_single.display_sync import VisualWindow


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


def _srt_ts(ts: str) -> float:
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def find_image(images: list[dict], *needles: str) -> dict | None:
    for needle in needles:
        for img in images:
            fn = (img.get("filename") or img.get("path") or "").lower()
            if needle in fn:
                return img
    return None


def find_clip(clips: list[dict], *needles: str) -> dict | None:
    for needle in needles:
        for clip in clips:
            fn = (clip.get("filename") or clip.get("path") or "").lower()
            if needle in fn:
                return clip
    return None


# Beat 06: cue order → image (filename needles)
BEAT6_CUE_IMAGES: list[tuple[str, ...]] = [
    ("fallback", "safeguard-fallback"),
    ("bio-aav",),
    ("distillation",),
    ("cyber-classifier", "cyber"),
    ("jailbreak",),
    ("cyber-classifier", "cyber"),
]

BEAT6_COMBINED_CLIP_CUES: list[tuple[str, ...]] = [
    ("jono-flight", "flight", "simulator"),
    ("bridgemind", "app", "build"),
    ("cintas", "fable5-opus", "linkedin"),
]

BEAT6_COMBINED_IMAGE_CUES: list[tuple[str, ...]] = [
    ("fallback", "safeguard-fallback"),
    ("jailbreak",),
    ("cyber-classifier", "cyber"),
    ("fallback", "safeguard-fallback"),
    ("fallback",),
]

BEAT6_TRUST_CUE_IMAGES: list[tuple[str, ...]] = [
    ("fallback-notification", "stories", "safety", "trust", "mixed", "two"),
    ("fallback-notification", "fallback", "visible", "switched", "older", "message", "clear"),
    ("fallback-notification", "notice", "plan", "percent", "sessions", "five", "anthropic"),
    ("fallback-notification", "notice", "plan", "percent", "sessions"),
    ("v2-quote-willison", "willison", "banner", "steering", "silent", "announcing"),
    ("v2-quote-willison", "willison", "steer", "steering", "silent", "swap", "announcing"),
    ("v2-quote-willison", "willison", "sabotage", "paid", "product", "simon"),
    ("v2-false-positive", "false", "positive", "homework", "hello", "everyday", "architecture"),
    ("v2-false-positive", "false", "positive", "safety", "bad", "point"),
    ("v2-false-positive", "deserve", "kind", "hit", "know", "which"),
]


def beat6_cue_image_map(images: list[dict]) -> list[tuple[str, ...]]:
    if find_image(images, "v2-false-positive") or find_image(images, "v2-quote-willison"):
        return BEAT6_TRUST_CUE_IMAGES
    return BEAT6_CUE_IMAGES


def beat6_absolute_cues(
    t0: float,
    seg_dur: float,
    seg_srt: Path,
    merged_srt: Path | None = None,
) -> list[tuple[float, float, str]]:
    """Cue spans in global timeline seconds — prefer merged final.srt when present."""
    if merged_srt and merged_srt.is_file():
        from praisonaippt.daily_single.display_sync import parse_srt

        rows = [
            (float(c["start_sec"]), float(c["end_sec"]), c.get("text") or "")
            for c in parse_srt(merged_srt)
            if float(c["start_sec"]) < t0 + seg_dur - 0.05
            and float(c["end_sec"]) > t0 + 0.05
        ]
        if rows:
            return rows
    local = _parse_segment_srt(seg_srt)
    return [(t0 + s, t0 + min(e, seg_dur), text) for s, e, text in local]


def beat6_cue_windows(
    t0: float,
    seg_dur: float,
    images: list[dict],
    seg_srt: Path,
    merged_srt: Path | None = None,
) -> list[VisualWindow]:
    """Visual windows — slide changes when narration topic changes."""
    cues = beat6_absolute_cues(t0, seg_dur, seg_srt, merged_srt)
    if not cues:
        return []
    cue_map = beat6_cue_image_map(images)
    wins: list[VisualWindow] = []
    for i, (start, end, text) in enumerate(cues):
        needles = cue_map[i] if i < len(cue_map) else cue_map[-1]
        img = find_image(images, *needles)
        if not img:
            continue
        wins.append(VisualWindow(
            start,
            min(end, t0 + seg_dur),
            "beat-06",
            text[:48],
            Path(img["path"]).name,
        ))
    return wins


def beat6_combined_cue_windows(
    t0: float,
    seg_dur: float,
    clips: list[dict],
    images: list[dict],
    seg_srt: Path,
    merged_srt: Path | None = None,
) -> list[VisualWindow]:
    """Combined beat-06: comparison clips then safeguard charts."""
    cues = beat6_absolute_cues(t0, seg_dur, seg_srt, merged_srt)
    if not cues:
        return []
    wins: list[VisualWindow] = []
    for i, (start, end, text) in enumerate(cues):
        needles = (
            BEAT6_COMBINED_CLIP_CUES[i]
            if i < len(BEAT6_COMBINED_CLIP_CUES)
            else BEAT6_COMBINED_IMAGE_CUES[i - len(BEAT6_COMBINED_CLIP_CUES)]
            if i - len(BEAT6_COMBINED_CLIP_CUES) < len(BEAT6_COMBINED_IMAGE_CUES)
            else BEAT6_COMBINED_IMAGE_CUES[-1]
        )
        asset = find_clip(clips, *needles) if i < len(BEAT6_COMBINED_CLIP_CUES) else find_image(images, *needles)
        if not asset:
            continue
        wins.append(VisualWindow(
            start,
            min(end, t0 + seg_dur),
            "beat-06",
            text[:48],
            Path(asset["path"]).name,
        ))
    return wins


def assemble_beat6_combined_from_cues(
    parts_dir: Path,
    seg_srt: Path,
    clips: list[dict],
    images: list[dict],
    out: Path,
    dur: float,
    *,
    t0: float = 0.0,
    merged_srt: Path | None = None,
) -> Path | None:
    """Build combined beat-06 — clip per comparison cue, then safeguard slides."""
    cues = beat6_absolute_cues(t0, dur, seg_srt, merged_srt)
    if not cues:
        return None
    parts: list[Path] = []
    for i, (start, end, _text) in enumerate(cues):
        needles = (
            BEAT6_COMBINED_CLIP_CUES[i]
            if i < len(BEAT6_COMBINED_CLIP_CUES)
            else BEAT6_COMBINED_IMAGE_CUES[i - len(BEAT6_COMBINED_CLIP_CUES)]
            if i - len(BEAT6_COMBINED_CLIP_CUES) < len(BEAT6_COMBINED_IMAGE_CUES)
            else BEAT6_COMBINED_IMAGE_CUES[-1]
        )
        asset = find_clip(clips, *needles) if i < len(BEAT6_COMBINED_CLIP_CUES) else find_image(images, *needles)
        if not asset:
            continue
        clip_d = max(0.5, min(end, t0 + dur) - start)
        part = parts_dir / f"cue-{i:02d}.mp4"
        from praisonaippt.daily_single.assemble import _trim_clip, _video_from_image, _extend_or_trim

        src = Path(asset["path"])
        if src.suffix.lower() == ".mp4":
            in_sec = float(asset.get("in_sec") or 0)
            _trim_clip(src, part, in_sec, in_sec + clip_d)
            _extend_or_trim(part, part, clip_d)
        else:
            _video_from_image(src, part, clip_d)
        parts.append(part)
    if not parts:
        return None
    from praisonaippt.daily_single.assemble import _concat_videos, _extend_or_trim

    merged = parts_dir / "merged.mp4"
    _concat_videos(parts, merged)
    _extend_or_trim(merged, out, dur)
    return out


def assemble_beat6_from_cues(
    parts_dir: Path,
    seg_srt: Path,
    images: list[dict],
    out: Path,
    dur: float,
    *,
    t0: float = 0.0,
    merged_srt: Path | None = None,
) -> Path | None:
    """Build beat-06 video — slide duration from merged final.srt or segment.srt."""
    cues = beat6_absolute_cues(t0, dur, seg_srt, merged_srt)
    if not cues:
        return None
    cue_map = beat6_cue_image_map(images)
    parts: list[Path] = []
    for i, (start, end, _text) in enumerate(cues):
        needles = cue_map[i] if i < len(cue_map) else cue_map[-1]
        img = find_image(images, *needles)
        if not img:
            continue
        clip_d = max(0.5, min(end, t0 + dur) - start)
        part = parts_dir / f"cue-{i:02d}.mp4"
        from praisonaippt.daily_single.assemble import _trim_clip, _video_from_image

        src = Path(img["path"])
        if src.suffix.lower() == ".mp4":
            _trim_clip(src, part, 0.0, clip_d)
            from praisonaippt.daily_single.assemble import _extend_or_trim
            _extend_or_trim(part, part, clip_d)
        else:
            _video_from_image(src, part, clip_d)
        parts.append(part)
    if not parts:
        return None
    from praisonaippt.daily_single.assemble import _concat_videos, _extend_or_trim

    merged = parts_dir / "merged.mp4"
    _concat_videos(parts, merged)
    _extend_or_trim(merged, out, dur)
    return out
