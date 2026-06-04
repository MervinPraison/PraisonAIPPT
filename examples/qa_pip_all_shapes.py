#!/usr/bin/env python3
"""Probe PiP head centring for circle, square, rect, and h_rect; write validation PNGs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from praisonaippt.avatar_calibrate import (
    maybe_auto_calibrate_deck,
    pip_probe_dims_for_shape,
)
from praisonaippt.pip_face_measure import (
    centring_advice,
    measure_pip_video,
    save_pip_validation_diagram,
)

VIDEO = ROOT / "examples" / "heygen-article-50590.mp4"
DECK = ROOT / "examples" / "heygen-50590-video-audio-heygen.yaml"
OUT = ROOT / "examples" / "qa"
SHAPES = ("circle", "square", "rect", "rounded", "h_rect")


def main() -> int:
    import yaml

    if not VIDEO.is_file() or not DECK.is_file():
        print("Missing HeyGen video or deck YAML")
        return 1

    data = yaml.safe_load(DECK.read_text(encoding="utf-8"))
    data["_source_file"] = str(DECK.resolve())
    ac = dict(data.get("avatar_calibration") or {})
    ac["force"] = True
    data["avatar_calibration"] = ac
    data = maybe_auto_calibrate_deck(data, source_file=data["_source_file"])
    pip = data["slide_style"]["layouts"]["pip"]
    crop_x = float(pip["crop_x_ratio"])
    crop_y = float(pip["crop_y_ratio"])
    zoom = float(pip.get("zoom_ratio", 1.45))
    seek = 6.0

    OUT.mkdir(parents=True, exist_ok=True)
    failed = 0
    for shape in SHAPES:
        pw, ph = pip_probe_dims_for_shape(data["slide_style"], shape)
        metrics, probe = measure_pip_video(
            str(VIDEO),
            seek_sec=seek,
            crop_x=crop_x,
            crop_y=crop_y,
            zoom=zoom,
            width=pw,
            height=ph,
            shape=shape,
        )
        advice = centring_advice(metrics)
        out = OUT / f"pip-validation-{shape}.png"
        save_pip_validation_diagram(probe, metrics, out, frame_shape=shape)
        mark = "✓" if advice.is_centred or abs(metrics.centre_offset_x) <= 0.05 else "✗"
        print(
            f"{mark} {shape} {pw}×{ph} centred={advice.is_centred} "
            f"offset_x={metrics.centre_offset_x:+.3f} offset_y={metrics.centre_offset_y:+.3f} → {out.name}",
        )
        if not advice.is_centred and abs(metrics.centre_offset_x) > 0.05:
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
