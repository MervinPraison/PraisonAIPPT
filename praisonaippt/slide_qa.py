"""Slide JPEG / MP4 frame QA helpers for deck validation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .utils import resolve_asset_path

_PIP_SLIDE_TYPES = frozenset({
    "big_number",
    "avatar_quote",
    "avatar_media_3",
    "avatar_media_border_3",
    "deck_thank_you",
    "avatar_headline",
    "avatar_headline_full",
})

_MEDIA_SLIDE_TYPES = frozenset({
    "avatar_media_3",
    "avatar_media_border_3",
    "avatar_media_1",
    "avatar_media_2",
})


def _deck_base(source_file: Optional[str]) -> Path:
    return Path(source_file).resolve().parent if source_file else Path.cwd()


def _merged_qa(data: dict, verse: dict) -> dict:
    out = dict(data.get("slide_qa") or {})
    out.update(verse.get("qa") or {})
    return out


def _jpeg_paths(img_dir: Path) -> List[Path]:
    return sorted(img_dir.glob("slide-*.jpg")) + sorted(img_dir.glob("slide-*.jpeg"))


def _content_width_ratio(jpeg: Path, *, bg_rgb: Tuple[int, int, int] = (18, 18, 18), tol: int = 40) -> Optional[float]:
    try:
        from PIL import Image
    except ImportError:
        return None
    im = Image.open(jpeg).convert("RGB")
    w, h = im.size
    y0 = int(h * 0.12)
    band = im.crop((0, y0, int(w * 0.82), h))
    px = band.load()
    bw, bh = band.size
    cols_with_content = 0
    for x in range(bw):
        for y in range(bh):
            r, g, b = px[x, y]
            if abs(r - bg_rgb[0]) + abs(g - bg_rgb[1]) + abs(b - bg_rgb[2]) > tol:
                cols_with_content = x + 1
                break
    if cols_with_content < 2:
        return 0.0
    return min(1.0, cols_with_content / max(w, 1))


def export_mp4_plan_frames(
    mp4_path: str | Path,
    data: dict,
    out_dir: str | Path,
    *,
    source_file: Optional[str] = None,
    offset_sec: float = 0.35,
) -> List[str]:
    """Grab one JPEG per plan slide at ``audio_start_sec + offset`` (live PiP visible)."""
    from .video_exporter import iter_slide_plan

    mp4 = Path(mp4_path)
    if not mp4.is_file():
        raise FileNotFoundError(f"MP4 not found: {mp4}")
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    exported: List[str] = []
    for i, item in enumerate(iter_slide_plan(data), start=1):
        verse = item.get("verse") or {}
        start = verse.get("audio_start_sec")
        if start is None:
            continue
        t = max(0.0, float(start) + offset_sec)
        dest = target / f"mp4-slide-{i:03d}.jpg"
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{t:.3f}",
            "-i",
            str(mp4.resolve()),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(dest),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        exported.append(str(dest))
    return exported


def check_slide_qa_manifest(
    data: dict,
    *,
    source_file: Optional[str] = None,
    jpeg_dir: Optional[str | Path] = None,
):
    from .deck_pipeline import StepResult
    """Validate per-slide ``qa`` rules against exported JPEGs."""
    from .video_exporter import iter_slide_plan

    plan = list(iter_slide_plan(data))
    if not plan:
        return StepResult("slide_qa", True, "empty plan (skipped)")

    base = _deck_base(source_file)
    if jpeg_dir is None:
        rel = data.get("slide_images_dir")
        if not rel:
            return StepResult("slide_qa", True, "no slide_images_dir (skipped)")
        img_dir = (base / rel).resolve()
    else:
        img_dir = Path(jpeg_dir).resolve()

    jpgs = _jpeg_paths(img_dir)
    if len(jpgs) != len(plan):
        return StepResult(
            "slide_qa",
            False,
            f"JPEG count {len(jpgs)} != plan slides {len(plan)} in {img_dir}",
        )

    issues: List[str] = []
    for idx, (item, jpg) in enumerate(zip(plan, jpgs), start=1):
        verse = item.get("verse") or {}
        slide_type = item.get("slide_type") or verse.get("slide_type") or ""
        qa = _merged_qa(data, verse)
        if not qa:
            continue

        if qa.get("expect_media"):
            if not verse.get("media_path"):
                issues.append(f"slide {idx}: expect_media but no media_path")
            elif not Path(
                resolve_asset_path(verse["media_path"], source_file=source_file)
                or base / verse["media_path"]
            ).is_file():
                issues.append(f"slide {idx}: media file missing")

        if qa.get("expect_pip"):
            has_avatar = bool(verse.get("avatar_video_path"))
            in_pip_kind = slide_type in _PIP_SLIDE_TYPES
            preview = bool(data.get("jpeg_show_pip_preview")) or verse.get("jpeg_show_pip_preview")
            if slide_type == "avatar_quote" and not preview:
                pass
            elif not (has_avatar and in_pip_kind):
                issues.append(f"slide {idx}: expect_pip but type={slide_type!r}")

        min_ratio = qa.get("min_media_width_ratio")
        if min_ratio is not None and slide_type in _MEDIA_SLIDE_TYPES:
            ratio = _content_width_ratio(jpg)
            if ratio is None:
                issues.append(f"slide {idx}: Pillow required for min_media_width_ratio")
            elif ratio < float(min_ratio):
                issues.append(
                    f"slide {idx}: media width ratio {ratio:.2f} < {float(min_ratio):.2f}",
                )

    if issues:
        return StepResult("slide_qa", False, "; ".join(issues), {"issues": issues})
    checked = sum(1 for item in plan if _merged_qa(data, item.get("verse") or {}))
    return StepResult(
        "slide_qa",
        True,
        f"QA manifest OK ({checked} slide(s) with rules, {len(plan)} JPEG(s))",
        {"dir": str(img_dir), "count": len(plan)},
    )


def check_mp4_plan_frames(
    data: dict,
    mp4_path: str | Path,
    *,
    source_file: Optional[str] = None,
    frames_dir: Optional[str | Path] = None,
    min_bytes: int = 8000,
):
    from .deck_pipeline import StepResult
    """Ensure MP4 seek frames exist for each verse ``audio_start_sec``."""
    from .video_exporter import iter_slide_plan

    mp4 = Path(mp4_path)
    if not mp4.is_file():
        return StepResult("mp4_frames", False, f"MP4 not found: {mp4}")

    base = _deck_base(source_file)
    rel = (data.get("pipeline") or {}).get("mp4_frames_dir") or "mp4-frames"
    out = Path(frames_dir) if frames_dir else (base / rel)
    if not out.is_absolute() and source_file:
        out = (base / rel).resolve()

    plan = list(iter_slide_plan(data))
    expected = sum(1 for item in plan if (item.get("verse") or {}).get("audio_start_sec") is not None)
    try:
        export_mp4_plan_frames(mp4, data, out, source_file=source_file)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        return StepResult("mp4_frames", False, str(e))

    frames = sorted(out.glob("mp4-slide-*.jpg"))
    small = [f.name for f in frames if f.stat().st_size < min_bytes]
    if len(frames) != expected:
        return StepResult(
            "mp4_frames",
            False,
            f"exported {len(frames)} frame(s), expected {expected}",
        )
    if small:
        return StepResult("mp4_frames", False, f"small MP4 frames: {', '.join(small)}")
    return StepResult(
        "mp4_frames",
        True,
        f"{len(frames)} MP4 frame(s) in {out}",
        {"dir": str(out), "count": len(frames)},
    )


def resolve_mp4_output(data: dict, deck_yaml: str | Path) -> Path:
    """Default MP4 path next to deck stem."""
    deck = Path(deck_yaml).resolve()
    return deck.parent / f"{deck.stem}.mp4"
