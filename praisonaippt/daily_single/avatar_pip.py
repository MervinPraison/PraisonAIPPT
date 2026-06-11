"""Circle avatar PiP (bottom-right) — same geometry as June roundup compositor."""
from __future__ import annotations

import subprocess
from pathlib import Path

from praisonaippt.ffmpeg_composer import _circle_alpha_filter, _cover_scale_filter

W, H = 1920, 1080
PIP_WIDTH_RATIO = 0.2
PIP_MARGIN_PX = 60
PIP_ZOOM = 1.3
PIP_CROP_Y = 0.1


def pip_width_px(*, frame_w: int = W) -> int:
    return max(160, int(round(frame_w * PIP_WIDTH_RATIO)))


def circle_pip_filter_complex(*, frame_w: int = W, frame_h: int = H) -> str:
    """ffmpeg filter_complex tail: [0:v] bg, [1:v] heygen → [v]."""
    pw = pip_width_px(frame_w=frame_w)
    scale_pad = (
        f"scale={frame_w}:{frame_h}:force_original_aspect_ratio=decrease,"
        f"pad={frame_w}:{frame_h}:(ow-iw)/2:(oh-ih)/2"
    )
    pip_chain = f"{_cover_scale_filter(pw, pw, crop_y_ratio=PIP_CROP_Y, zoom_ratio=PIP_ZOOM)}"
    pip_chain = f"{pip_chain},{_circle_alpha_filter(border_px=2)}"
    ox = f"W-w-{PIP_MARGIN_PX}"
    oy = f"H-h-{PIP_MARGIN_PX}"
    return (
        f"[1:v]{pip_chain}[pip];"
        f"[0:v]{scale_pad}[bg];"
        f"[bg][pip]overlay={ox}:{oy}:format=auto[v]"
    )


def overlay_circle_pip(bg: Path, heygen: Path, dest: Path, dur: float) -> None:
    """Composite HeyGen avatar as circle PiP over a full-frame background clip."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(bg),
        "-i", str(heygen),
        "-filter_complex", circle_pip_filter_complex(),
        "-map", "[v]",
        "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
        str(dest),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
