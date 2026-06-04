#!/usr/bin/env python3
"""Rebuild avatar, deck, and HeyGen 50590 showcase PPTX + MP4 outputs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
CLI = [sys.executable, "-m", "praisonaippt.cli"]

HEYGEN_VARIANTS = [
    ("heygen-50590-video-audio-heygen.yaml", "heygen-50590-video-audio-heygen"),
    ("heygen-50590-video-visual-mp3.yaml", "heygen-50590-video-visual-mp3"),
    ("heygen-50590-audio-only.yaml", "heygen-50590-audio-only"),
    ("heygen-50590-video-only-silent.yaml", "heygen-50590-video-only-silent"),
    ("heygen-50590-slides-silent.yaml", "heygen-50590-slides-silent"),
]

SHOWCASES = [
    ("avatar_layouts.yaml", "avatar_layouts_built"),
    ("deck_template_gallery.yaml", "deck_template_gallery"),
    *HEYGEN_VARIANTS,
]


def sync_variants() -> None:
    script = ROOT / "sync_heygen_variants.py"
    print("Syncing HeyGen variant YAMLs from heygen-50590-content.yaml …")
    subprocess.run([sys.executable, str(script)], cwd=str(REPO), check=True)


def calibrate_content_master() -> None:
    master = ROOT / "heygen-50590-content.yaml"
    print("Calibrating PiP crop (hybrid) and writing into content master …")
    subprocess.run(
        [
            *CLI,
            "calibrate-avatar",
            str(master),
            "--force",
            "--write",
            "--validation-image",
            str(ROOT / "qa" / "pip-validation-circle-master.png"),
        ],
        cwd=str(REPO),
        check=True,
    )


def build(yaml_name: str, stem: str) -> None:
    yaml_path = ROOT / yaml_name
    pptx = ROOT / f"{stem}.pptx"
    mp4 = ROOT / f"{stem}.mp4"
    if not yaml_path.is_file():
        raise FileNotFoundError(yaml_path)
    cmd = [
        *CLI,
        "-i",
        str(yaml_path),
        "-o",
        str(pptx),
        "--convert-video",
        "--video-output",
        str(mp4),
        "--no-list-slides",
    ]
    print(f"\n=== Building {yaml_name} → {pptx.name}, {mp4.name} ===")
    subprocess.run(cmd, cwd=str(REPO), check=True)


def build_heygen_only() -> None:
    sync_variants()
    calibrate_content_master()
    sync_variants()
    qa = REPO / "examples" / "qa_pip_all_shapes.py"
    if qa.is_file():
        print("\n=== PiP centring QA (circle, square, rect, …) ===")
        subprocess.run([sys.executable, str(qa)], cwd=str(REPO), check=False)
    for yaml_name, stem in HEYGEN_VARIANTS:
        build(yaml_name, stem)


def main() -> None:
    import sys as _sys

    if len(_sys.argv) > 1 and _sys.argv[1] == "--heygen-only":
        build_heygen_only()
        print("\n✓ HeyGen 50590 variants rebuilt.")
        return

    sync_variants()
    calibrate_content_master()
    sync_variants()
    qa = REPO / "examples" / "qa_pip_all_shapes.py"
    if qa.is_file():
        print("\n=== PiP centring QA (circle, square, rect, …) ===")
        subprocess.run([sys.executable, str(qa)], cwd=str(REPO), check=False)
    for yaml_name, stem in SHOWCASES:
        build(yaml_name, stem)
    print("\n✓ All showcase examples built.")


if __name__ == "__main__":
    main()
