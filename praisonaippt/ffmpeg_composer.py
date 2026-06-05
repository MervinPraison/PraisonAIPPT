"""FFmpeg / ffprobe helpers for PPTX-to-video export (subprocess, no ffmpeg-python)."""

from __future__ import annotations

import json
import logging
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


@dataclass
class ToolCheck:
    name: str
    found: bool
    path: Optional[str] = None
    version: Optional[str] = None


def find_binary(name: str) -> Optional[str]:
    return shutil.which(name)


def _run(cmd: List[str], *, timeout: int = 600) -> subprocess.CompletedProcess:
    logger.debug("Running: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def probe_tool(name: str, version_args: Optional[List[str]] = None) -> ToolCheck:
    path = find_binary(name)
    if not path:
        return ToolCheck(name=name, found=False)
    args = [path] + (version_args or ["-version"])
    proc = _run(args, timeout=15)
    version = (proc.stdout or proc.stderr or "").splitlines()[0] if proc.returncode == 0 else None
    return ToolCheck(name=name, found=True, path=path, version=version)


def check_video_tools() -> Dict[str, ToolCheck]:
    from .pdf_converter import PDFConverter

    probe = PDFConverter.__new__(PDFConverter)
    probe.config = {}
    probe._available_backends = probe._detect_backends()
    lo_ok = "libreoffice" in probe._available_backends
    lo_path = getattr(probe, "_libreoffice_path", None) if lo_ok else None
    tools = {
        "ffmpeg": probe_tool("ffmpeg"),
        "ffprobe": probe_tool("ffprobe"),
        "pdftoppm": probe_tool("pdftoppm"),
        "libreoffice": ToolCheck(
            name="libreoffice",
            found=lo_ok,
            path=lo_path,
            version="available" if lo_ok else None,
        ),
    }
    return tools


def print_tool_check_report(tools: Optional[Dict[str, ToolCheck]] = None) -> int:
    tools = tools or check_video_tools()
    ok = True
    for key in ("ffmpeg", "ffprobe", "pdftoppm", "libreoffice"):
        t = tools[key]
        status = "OK" if t.found else "MISSING"
        line = f"  {key}: {status}"
        if t.path:
            line += f" ({t.path})"
        if t.version:
            line += f" — {t.version[:80]}"
        print(line)
        if not t.found:
            ok = False
    if not ok:
        print("\nInstall on macOS: brew install ffmpeg poppler")
        print("LibreOffice: brew install --cask libreoffice (or use existing install)")
    return 0 if ok else 1


def pick_video_encoder() -> str:
    """Prefer Apple VideoToolbox on macOS, else libx264."""
    if platform.system().lower() != "darwin":
        return "libx264"
    proc = _run(["ffmpeg", "-hide_banner", "-encoders"], timeout=15)
    text = proc.stdout or ""
    if "h264_videotoolbox" in text:
        return "h264_videotoolbox"
    return "libx264"


def ffprobe_duration(path: str) -> float:
    proc = _run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", path,
        ],
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {proc.stderr}")
    data = json.loads(proc.stdout or "{}")
    dur = float(data.get("format", {}).get("duration", 0) or 0)
    if dur <= 0:
        raise RuntimeError(f"Could not read duration for {path}")
    return dur


def ffprobe_has_audio(path: str) -> bool:
    proc = _run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "json", path,
        ],
        timeout=30,
    )
    if proc.returncode != 0:
        return False
    streams = json.loads(proc.stdout or "{}").get("streams") or []
    return len(streams) > 0


def ffprobe_video_fps(path: str) -> float:
    """Return average frame rate of the first video stream (e.g. 30.0)."""
    proc = _run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=avg_frame_rate",
            "-of", "json", path,
        ],
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe fps failed for {path}: {proc.stderr}")
    streams = json.loads(proc.stdout or "{}").get("streams") or []
    if not streams:
        raise RuntimeError(f"No video stream for {path}")
    rate = streams[0].get("avg_frame_rate") or "0/1"
    if "/" in str(rate):
        num, den = str(rate).split("/", 1)
        den_f = float(den) or 1.0
        return float(num) / den_f
    return float(rate)


def ffprobe_media_size(path: str) -> Tuple[int, int]:
    proc = _run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json", path,
        ],
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe size failed for {path}: {proc.stderr}")
    streams = json.loads(proc.stdout or "{}").get("streams") or []
    if not streams:
        raise RuntimeError(f"No video stream for {path}")
    return int(streams[0]["width"]), int(streams[0]["height"])


def is_video_path(path: str) -> bool:
    return Path(path).suffix.lower() in _VIDEO_EXTS


def is_image_path(path: str) -> bool:
    return Path(path).suffix.lower() in _IMAGE_EXTS


def contain_overlay_geometry(
    path: str, box_w: int, box_h: int, box_x: int, box_y: int,
) -> Tuple[int, int, int, int]:
    """Return scale_w, scale_h, overlay_x, overlay_y for contain-fit in a region box."""
    iw, ih = ffprobe_media_size(path)
    box_w, box_h = max(2, box_w), max(2, box_h)
    scale = min(box_w / iw, box_h / ih)
    sw = max(1, int(round(iw * scale)))
    sh = max(1, int(round(ih * scale)))
    ox = box_x + (box_w - sw) // 2
    oy = box_y + (box_h - sh) // 2
    return sw, sh, ox, oy


def pdf_to_png_pages(
    pdf_path: str,
    out_dir: Path,
    dpi: int = 192,
    *,
    first_page: Optional[int] = None,
    last_page: Optional[int] = None,
) -> List[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "slide"
    cmd = ["pdftoppm", "-png", "-r", str(dpi)]
    if first_page is not None:
        cmd.extend(["-f", str(first_page)])
    if last_page is not None:
        cmd.extend(["-l", str(last_page)])
    cmd.extend([str(pdf_path), str(prefix)])
    proc = _run(cmd, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"pdftoppm failed: {proc.stderr}")
    pages = sorted(out_dir.glob("slide-*.png"))
    if not pages:
        pages = sorted(out_dir.glob("slide*.png"))
    return [str(p) for p in pages]


def pdf_to_jpeg_pages(
    pdf_path: str,
    out_dir: Path,
    dpi: int = 192,
    *,
    jpeg_quality: int = 90,
    first_page: Optional[int] = None,
    last_page: Optional[int] = None,
) -> List[str]:
    """Rasterise each PDF page to JPEG via pdftoppm (Poppler)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    before = {p.resolve() for p in out_dir.glob("slide*.jpg")}
    prefix = out_dir / "slide"
    quality = max(1, min(int(jpeg_quality), 100))
    cmd = ["pdftoppm", "-jpeg", "-r", str(dpi), "-jpegopt", f"quality={quality}"]
    if first_page is not None:
        cmd.extend(["-f", str(first_page)])
    if last_page is not None:
        cmd.extend(["-l", str(last_page)])
    cmd.extend([str(pdf_path), str(prefix)])
    proc = _run(cmd, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"pdftoppm failed: {proc.stderr}")
    pages = sorted(
        p for p in out_dir.glob("slide*.jpg") if p.resolve() not in before
    )
    return [str(p) for p in pages]


@dataclass
class OverlaySpec:
    path: str
    x: int
    y: int
    width: int
    height: int
    is_video: bool
    fit: str = "stretch"
    video_start_sec: float = 0.0
    loop_video: bool = False
    shape: str = "rect"
    crop_x_ratio: float = 0.5
    crop_y_ratio: float = 0.12
    zoom_ratio: float = 1.35


def scaled_cover_size(
    source_w: int,
    source_h: int,
    out_w: int,
    out_h: int,
    *,
    zoom_ratio: float = 1.0,
) -> Tuple[float, float]:
    """Pixel size after ``scale:zw:zh:force_original_aspect_ratio=increase`` (ffmpeg parity)."""
    zw = max(2, int(round(out_w * zoom_ratio)))
    zh = max(2, int(round(out_h * zoom_ratio)))
    scale = max(zw / max(1, source_w), zh / max(1, source_h))
    return source_w * scale, source_h * scale


def face_x_to_crop_x_ratio(
    face_x_norm: float,
    source_w: int,
    source_h: int,
    out_w: int,
    out_h: int,
    *,
    zoom_ratio: float = 1.0,
) -> float:
    """``crop_x_ratio`` so normalised face *x* maps to horizontal centre of cropped output."""
    swp, _ = scaled_cover_size(source_w, source_h, out_w, out_h, zoom_ratio=zoom_ratio)
    ow = max(2, out_w)
    if swp <= ow + 1e-6:
        return 0.5
    crop_x = (face_x_norm * swp - 0.5 * ow) / (swp - ow)
    return max(0.2, min(0.8, float(crop_x)))


def _cover_scale_filter(
    w: int,
    h: int,
    *,
    crop_x_ratio: float = 0.5,
    crop_y_ratio: float,
    zoom_ratio: float,
) -> str:
    zw = max(2, int(round(w * zoom_ratio)))
    zh = max(2, int(round(h * zoom_ratio)))
    x_bias = max(0.2, min(float(crop_x_ratio), 0.8))
    y_bias = max(0.0, min(float(crop_y_ratio), 0.45))
    return (
        f"scale={zw}:{zh}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h}:(iw-ow)*{x_bias}:(ih-oh)*{y_bias}"
    )


def pip_face_balance(pip_rgba) -> float:
    """Signed horizontal balance in upper face band: 0 centred, + face right, − face left."""
    import numpy as np
    from PIL import Image

    if isinstance(pip_rgba, (str, Path)):
        img = np.array(Image.open(pip_rgba).convert("RGBA"))
    else:
        img = np.asarray(pip_rgba.convert("RGBA"))
    h, w = img.shape[:2]
    alpha = img[:, :, 3] > 128
    lum = np.mean(img[:, :, :3], axis=2)
    band = np.zeros((h, w), dtype=bool)
    band[: int(h * 0.55), int(w * 0.1) : int(w * 0.9)] = True
    mask = alpha & band & (lum < 210)
    left = float(mask[:, : w // 2].sum())
    right = float(mask[:, w // 2 :].sum())
    total = left + right
    return (right - left) / total if total else 0.0


def _circle_alpha_filter(*, border_px: int = 0) -> str:
    """
    Circular alpha mask for PiP overlays.

    ``border_px`` draws a white ring on the compositor (avoids PPTX stroke leaking
    past a smaller video mask as a visible 'lid' behind the circle).
    """
    dist = "pow(X-W/2,2)+pow(Y-H/2,2)"
    outer = "pow(W/2,2)"
    if border_px <= 0:
        return (
            "format=rgba,"
            "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
            f"a='if(lte({dist},{outer}),255,0)'"
        )
    inner = f"pow(W/2-{border_px},2)"
    ring = f"if(lte({dist},{inner}),0,if(lte({dist},{outer}),255,0))"
    return (
        "format=rgba,"
        f"geq=r='if(eq({ring},255),255,r(X,Y))':"
        f"g='if(eq({ring},255),255,g(X,Y))':"
        f"b='if(eq({ring},255),255,b(X,Y))':"
        f"a='if(lte({dist},{outer}),255,0)'"
    )


def render_slide_segment(
    base_png: str,
    duration: float,
    output: str,
    *,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    encoder: Optional[str] = None,
    overlays: Optional[List[OverlaySpec]] = None,
    audio_path: Optional[str] = None,
    audio_start_sec: float = 0.0,
    fade_sec: float = 0.0,
    video_crf: int = 23,
) -> None:
    """Render one slide segment MP4 from PNG base + optional overlays + audio."""
    overlays = overlays or []
    encoder = encoder or pick_video_encoder()
    dur = max(duration, 0.1)

    cmd: List[str] = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", base_png]

    overlay_inputs = []
    for ov in overlays:
        if ov.is_video:
            if ov.loop_video:
                cmd += ["-stream_loop", "-1"]
            cmd += ["-i", ov.path]
        else:
            cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", ov.path]
        overlay_inputs.append(ov)

    if audio_path:
        if audio_start_sec > 0:
            cmd += ["-ss", f"{audio_start_sec:.3f}"]
        cmd += ["-i", audio_path]
    else:
        cmd += [
            "-f", "lavfi", "-t", f"{dur:.3f}",
            "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        ]

    filters: List[str] = []
    base = "[0:v]"
    filters.append(
        f"{base}scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}[v0]"
    )
    prev = "v0"
    for idx, ov in enumerate(overlay_inputs, start=1):
        w, h = max(2, ov.width), max(2, ov.height)
        ox, oy = ov.x, ov.y
        if ov.fit == "cover":
            scale = _cover_scale_filter(
                w,
                h,
                crop_x_ratio=ov.crop_x_ratio,
                crop_y_ratio=ov.crop_y_ratio,
                zoom_ratio=ov.zoom_ratio,
            )
        elif ov.fit == "contain":
            sw, sh, ox, oy = contain_overlay_geometry(ov.path, w, h, ov.x, ov.y)
            scale = f"scale={sw}:{sh}"
        else:
            scale = f"scale={w}:{h}"
        tag = f"ov{idx}"
        out = f"v{idx}"
        chain = scale
        if ov.is_video:
            start = max(0.0, float(ov.video_start_sec))
            chain = f"trim=start={start:.3f}:duration={dur:.3f},setpts=PTS-STARTPTS,{scale}"
        if str(ov.shape).lower() in ("circle", "round", "rounded"):
            chain = f"{chain},{_circle_alpha_filter(border_px=2)}"
        filters.append(f"[{idx}:v]{chain},setsar=1[{tag}]")
        fmt = "auto" if str(ov.shape).lower() in ("circle", "round", "rounded") else "auto"
        filters.append(f"[{prev}][{tag}]overlay={ox}:{oy}:format={fmt}[{out}]")
        prev = out

    fade = max(0.0, float(fade_sec))
    if fade > 0 and dur > fade * 2.5:
        fade = min(fade, dur / 4.0)
        fade_out = f"[{prev}]fade=t=in:st=0:d={fade:.3f},fade=t=out:st={max(0.0, dur - fade):.3f}:d={fade:.3f}[vfade]"
        filters.append(fade_out)
        prev = "vfade"

    filters.append(f"[{prev}]format=yuv420p[vout]")
    cmd += ["-filter_complex", ";".join(filters), "-map", "[vout]"]

    audio_idx = 1 + len(overlay_inputs)
    cmd += ["-map", f"{audio_idx}:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]

    if encoder == "h264_videotoolbox":
        cmd += ["-c:v", "h264_videotoolbox", "-b:v", "8M"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(int(video_crf)), "-pix_fmt", "yuv420p"]

    cmd += ["-t", f"{dur:.3f}", output]
    proc = _run(cmd, timeout=max(int(dur * 20) + 120, 180))
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg segment failed: {proc.stderr}")


def _concat_list_path(path: str) -> str:
    """Escape path for ffmpeg concat demuxer."""
    return Path(path).resolve().as_posix().replace("'", "'\\''")


def concat_segments(segment_paths: List[str], output: str) -> None:
    if not segment_paths:
        raise RuntimeError("No segments to concat")
    if len(segment_paths) == 1:
        shutil.copyfile(segment_paths[0], output)
        return
    list_file = Path(output).with_suffix(".concat.txt")
    lines = [f"file '{_concat_list_path(p)}'" for p in segment_paths]
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    proc = _run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", output,
        ],
        timeout=600,
    )
    if proc.returncode != 0:
        enc = pick_video_encoder()
        venc = enc if enc != "h264_videotoolbox" else "libx264"
        proc = _run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", str(list_file),
                "-c:v", venc, "-c:a", "aac", "-b:a", "192k", output,
            ],
            timeout=900,
        )
    list_file.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg concat failed: {proc.stderr}")


def build_xfade_filter_chain(
    durations: List[float],
    edges: List[Any],
    *,
    fps: int = 30,
) -> Tuple[str, str]:
    """Build filter_complex for chained xfade. Returns (filter_string, final_video_label)."""
    n = len(durations)
    if n <= 1:
        return "", "0:v"
    if n - 1 != len(edges):
        raise ValueError(f"Expected {n - 1} edges for {n} segments")

    from .transition_backends import ffmpeg_xfade_transition

    pre: List[str] = []
    norm: List[str] = []
    for i in range(n):
        tag = f"vn{i}"
        pre.append(f"[{i}:v]fps={fps},settb=AVTB,format=yuv420p[{tag}]")
        norm.append(tag)

    filters: List[str] = list(pre)
    running = float(durations[0])
    prev_label = norm[0]
    out_idx = 0
    for i in range(n - 1):
        edge = edges[i]
        edge_type = getattr(edge, "type", edge.get("type") if isinstance(edge, dict) else "none")
        dur = float(getattr(edge, "duration_sec", 0) if not isinstance(edge, dict) else edge.get("duration_sec", 0))
        is_blend = edge_type in (
            "crossfade", "wipeleft", "wiperight", "slideleft", "slideright",
        )
        next_in = norm[i + 1]
        out_label = f"vx{out_idx}"
        if is_blend and dur > 0:
            xf = ffmpeg_xfade_transition(str(edge_type))
            offset = max(0.0, running - dur)
            filters.append(
                f"[{prev_label}][{next_in}]xfade=transition={xf}:duration={dur:.3f}:"
                f"offset={offset:.3f},format=yuv420p[{out_label}]"
            )
            running = running + float(durations[i + 1]) - dur
        else:
            filters.append(f"[{prev_label}][{next_in}]concat=n=2:v=1:a=0,format=yuv420p[{out_label}]")
            running += float(durations[i + 1])
        prev_label = out_label
        out_idx += 1
    return ";".join(filters), prev_label


def build_acrossfade_filter_chain(
    durations: List[float],
    edges: List[Any],
) -> Tuple[str, str]:
    """Build audio acrossfade chain mirroring video edges."""
    n = len(durations)
    if n <= 1:
        return "", "0:a"
    pre: List[str] = []
    norm: List[str] = []
    for i in range(n):
        tag = f"an{i}"
        pre.append(f"[{i}:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo[{tag}]")
        norm.append(tag)

    filters: List[str] = list(pre)
    running = float(durations[0])
    prev_label = norm[0]
    out_idx = 0
    for i in range(n - 1):
        edge = edges[i]
        edge_type = getattr(edge, "type", edge.get("type") if isinstance(edge, dict) else "none")
        dur = float(getattr(edge, "duration_sec", 0) if not isinstance(edge, dict) else edge.get("duration_sec", 0))
        is_blend = edge_type in (
            "crossfade", "wipeleft", "wiperight", "slideleft", "slideright",
        )
        next_in = norm[i + 1]
        out_label = f"ax{out_idx}"
        if is_blend and dur > 0:
            filters.append(
                f"[{prev_label}][{next_in}]acrossfade=d={dur:.3f}[{out_label}]"
            )
            running = running + float(durations[i + 1]) - dur
        else:
            filters.append(f"[{prev_label}][{next_in}]concat=n=2:v=0:a=1[{out_label}]")
            running += float(durations[i + 1])
        prev_label = out_label
        out_idx += 1
    return ";".join(filters), prev_label


def concat_segments_with_transitions(
    segment_paths: List[str],
    durations: List[float],
    edges: List[Any],
    output: str,
    *,
    video_crf: int = 23,
    encoder: Optional[str] = None,
) -> None:
    """Concat segments with xfade/acrossfade on blend edges; hard join on none/segment_fade."""
    if not segment_paths:
        raise RuntimeError("No segments to concat")
    if len(segment_paths) == 1:
        shutil.copyfile(segment_paths[0], output)
        return
    if len(durations) != len(segment_paths):
        durations = [max(0.1, ffprobe_duration(p)) for p in segment_paths]

    encoder = encoder or pick_video_encoder()
    cmd: List[str] = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for p in segment_paths:
        cmd += ["-i", p]

    v_filter, v_out = build_xfade_filter_chain(durations, edges)
    a_filter, a_out = build_acrossfade_filter_chain(durations, edges)
    filters = v_filter
    if a_filter:
        filters = f"{v_filter};{a_filter}" if v_filter else a_filter

    cmd += ["-filter_complex", filters, "-map", f"[{v_out}]", "-map", f"[{a_out}]"]
    if encoder == "h264_videotoolbox":
        cmd += ["-c:v", "h264_videotoolbox", "-b:v", "8M"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(int(video_crf)), "-pix_fmt", "yuv420p"]
    cmd += ["-c:a", "aac", "-b:a", "192k", output]

    proc = _run(cmd, timeout=900)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg transition concat failed: {proc.stderr}")
