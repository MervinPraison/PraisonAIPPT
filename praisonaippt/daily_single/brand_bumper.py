"""Brand bumper clip inserted after the hook bridge ('Let's get started')."""
from __future__ import annotations

import subprocess
from pathlib import Path

from praisonaippt.segment_video.media import ffprobe_duration

W, H = 1920, 1080
FPS = 30
BUMPER_FILENAME = "brand-bumper-1080p-hevc.mp4"
BUMPER_STEM = "brand-bumper"


def repo_brand_bumper_path() -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / "brand" / BUMPER_FILENAME


def bumper_available() -> bool:
    return repo_brand_bumper_path().is_file()


def prepare_brand_bumper(out_dir: Path) -> tuple[Path, Path] | None:
    """Transcode bumper to h264 + extract audio for concat. Returns (video, audio) or None."""
    src = repo_brand_bumper_path()
    if not src.is_file():
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    video = out_dir / f"{BUMPER_STEM}.mp4"
    audio = out_dir / f"{BUMPER_STEM}-a.mp3"
    scale = (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps={FPS}"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", scale, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(video),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src), "-vn",
            "-c:a", "libmp3lame", "-b:a", "192k", str(audio),
        ],
        check=True,
        capture_output=True,
    )
    return video, audio


def bumper_duration_sec() -> float:
    src = repo_brand_bumper_path()
    if not src.is_file():
        return 0.0
    return ffprobe_duration(src)
