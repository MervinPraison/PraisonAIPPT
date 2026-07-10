"""Sermon-specific featured image generation via ~/create-post/gpt-image."""
from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from .config import GPT_IMAGE_DIR, IMAGE_SIZE
from .protocol import SermonJob, SermonPack


def load_visual_brief(pack: SermonPack, slug: str) -> dict:
    if not pack.visual_briefs_path or not pack.visual_briefs_path.exists():
        raise FileNotFoundError(f"Visual briefs not found: {pack.visual_briefs_path}")
    data = yaml.safe_load(pack.visual_briefs_path.read_text(encoding="utf-8"))
    briefs = data.get("briefs", {})
    if slug not in briefs:
        raise KeyError(f"No visual brief for slug: {slug}")
    return briefs[slug]


def sermon_image_prompt(concept: str) -> str:
    return (
        f"{concept}. Photorealistic biblical faith illustration, soft cinematic lighting, "
        f"wide horizontal banner composition {IMAGE_SIZE}, rich colour, "
        "absolutely no text, no letters, no numbers, no logos, no watermarks."
    )


def cover_path(pack: SermonPack, slug: str) -> Path:
    pack.cover_dir.mkdir(parents=True, exist_ok=True)
    return pack.cover_dir / f"{slug}-cover.png"


def prompt_path(pack: SermonPack, slug: str) -> Path:
    pack.cover_dir.mkdir(parents=True, exist_ok=True)
    return pack.cover_dir / f"{slug}-prompt.txt"


def generate_cover(job: SermonJob, pack: SermonPack, force: bool = False) -> Path:
    out = cover_path(pack, job.slug)
    if out.exists() and not force:
        return out

    brief = load_visual_brief(pack, job.slug)
    prompt = sermon_image_prompt(brief["concept"])
    prompt_file = prompt_path(pack, job.slug)
    prompt_file.write_text(prompt, encoding="utf-8")

    result = subprocess.run(
        [
            "uv", "run", "scripts/generate.py",
            "--prompt", prompt,
            "--size", IMAGE_SIZE,
            "--quality", "high",
            "--output", str(out),
        ],
        cwd=str(GPT_IMAGE_DIR),
        check=False,
    )
    if result.returncode != 0 and out.exists():
        return out
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args)
    return out
