"""Slide JPEG / MP4 frame QA helpers for deck validation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .text_panel_anchors import HERO_PANEL_ANCHORS
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


def _hero_coverage_ratio(
    jpeg: Path, *, bg_rgb: Tuple[int, int, int] = (18, 18, 18), tol: int = 40,
) -> Optional[float]:
    try:
        from PIL import Image
    except ImportError:
        return None
    im = Image.open(jpeg).convert("RGB")
    w, h = im.size
    step = 8
    non_bg = 0
    total = 0
    px = im.load()
    for y in range(0, h, step):
        for x in range(0, w, step):
            total += 1
            r, g, b = px[x, y]
            if abs(r - bg_rgb[0]) + abs(g - bg_rgb[1]) + abs(b - bg_rgb[2]) > tol:
                non_bg += 1
    return non_bg / total if total else 0.0


def _content_width_ratio(
    jpeg: Path, *, bg_rgb: Tuple[int, int, int] = (18, 18, 18), tol: int = 40,
) -> Optional[float]:
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
    """Validate per-slide ``qa`` rules against exported JPEGs."""
    from .deck_pipeline import StepResult
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

        min_cover = qa.get("min_hero_coverage_ratio")
        if min_cover is not None and slide_type in _MEDIA_SLIDE_TYPES:
            if str(verse.get("media_fit") or "").lower() == "contain":
                pass
            else:
                cover = _hero_coverage_ratio(jpg)
                if cover is None:
                    issues.append(f"slide {idx}: Pillow required for min_hero_coverage_ratio")
                elif cover < float(min_cover):
                    issues.append(
                        f"slide {idx}: hero coverage {cover:.2f} < {float(min_cover):.2f}",
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


def check_hero_text_placement(
    data: dict,
    *,
    source_file: Optional[str] = None,
):
    """Validate auto hero panel anchors meet minimum confidence."""
    from .deck_pipeline import StepResult
    from .hero_panel_calibrate import HeroTextConfig, maybe_auto_place_hero_text_deck

    cfg_raw = data.get("hero_text_placement") or {}
    if not cfg_raw.get("auto"):
        return StepResult("hero_text", True, "hero_text_placement.auto disabled (skipped)")

    merged = maybe_auto_place_hero_text_deck(dict(data), source_file=source_file)
    results = merged.get("_hero_text_placement") or {}
    cfg = HeroTextConfig.from_dict(cfg_raw, style=merged.get("slide_style") or {})
    issues: List[str] = []
    for path, raw in results.items():
        conf = float(raw.get("confidence") or 0)
        anchor = raw.get("anchor")
        if conf < cfg.min_confidence:
            issues.append(f"{Path(path).name}: confidence {conf:.2f} < {cfg.min_confidence}")
        if anchor not in HERO_PANEL_ANCHORS:
            issues.append(f"{Path(path).name}: invalid anchor {anchor!r}")

    if issues:
        return StepResult("hero_text", False, "; ".join(issues), {"issues": issues})
    return StepResult(
        "hero_text",
        True,
        f"hero text placement OK ({len(results)} slide(s))",
        {"count": len(results)},
    )


def check_slide_transitions(
    data: dict,
    *,
    source_file: Optional[str] = None,
    strict: bool = False,
):
    """Validate resolved slide transition plan."""
    from .deck_pipeline import StepResult
    from .slide_transition import maybe_apply_slide_transitions_deck
    from .transition_backends import known_transition_types
    from .video_exporter import iter_slide_plan

    st_raw = data.get("slide_transitions")
    if isinstance(st_raw, dict) and st_raw.get("enabled") is False:
        return StepResult("slide_transitions", True, "slide_transitions disabled (skipped)")

    plan = list(iter_slide_plan(data))
    merged = maybe_apply_slide_transitions_deck(dict(data), plan, source_file=source_file)
    sidecar = merged.get("_slide_transitions") or {}
    edges = sidecar.get("edges") or []
    allowed = known_transition_types()
    issues: List[str] = []
    for edge in edges:
        t = edge.get("type", "none")
        if t not in allowed:
            issues.append(f"after_slide {edge.get('after_slide')}: unknown type {t!r}")
        if strict and t != "none" and float(edge.get("duration_sec") or 0) <= 0:
            issues.append(f"after_slide {edge.get('after_slide')}: zero duration")

    ts = data.get("slide_timestamps")
    if ts and any(e.get("type") in ("crossfade", "wipeleft", "wiperight", "slideleft", "slideright") for e in edges):
        issues.append("slide_timestamps with blend transitions may drift (warning)")

    if issues and strict:
        return StepResult("slide_transitions", False, "; ".join(issues), {"issues": issues})
    if issues:
        return StepResult(
            "slide_transitions",
            True,
            f"slide transitions OK with warnings: {'; '.join(issues)}",
            {"edges": edges, "warnings": issues},
        )
    return StepResult(
        "slide_transitions",
        True,
        f"slide transitions OK ({len(edges)} edge(s))",
        {"edges": edges},
    )


def resolve_mp4_output(data: dict, deck_yaml: str | Path) -> Path:
    """Default MP4 path next to deck stem."""
    deck = Path(deck_yaml).resolve()
    return deck.parent / f"{deck.stem}.mp4"
