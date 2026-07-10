"""Load sermon pack protocol YAML."""
from __future__ import annotations

from pathlib import Path

import yaml

from .config import DEFAULT_COVER_DIR, DEFAULT_DRAFT_DIR, DEFAULT_PACK_DIR, SERMON_PACKS_DIR
from .protocol import SermonJob, SermonPack


def _expand(path: str | Path) -> Path:
    return Path(path).expanduser()


def load_pack(pack_yaml: Path) -> SermonPack:
    data = yaml.safe_load(pack_yaml.read_text(encoding="utf-8"))
    pack_dir = _expand(data.get("pack_dir", DEFAULT_PACK_DIR))
    draft_dir = _expand(data.get("draft_dir", DEFAULT_DRAFT_DIR))
    cover_dir = _expand(data.get("cover_dir", DEFAULT_COVER_DIR))
    yaml_examples = _expand(data.get("yaml_examples_dir", SERMON_PACKS_DIR.parent))

    briefs = data.get("visual_briefs")
    briefs_path = _expand(briefs) if briefs else None

    jobs: list[SermonJob] = []
    for row in data.get("jobs", []):
        jobs.append(SermonJob(
            slug=row["slug"],
            title=row["title"],
            video_id=row.get("video_id", ""),
            pack_name=row.get("pack_name", row["title"]),
            transcript_file=row["transcript_file"],
            yaml_file=row["yaml_file"],
            topic=row.get("topic", row["title"].lower()),
            excerpt=row.get("excerpt", ""),
            categories=row.get("categories", "Gospel,Wisdom"),
            post_id=row.get("post_id"),
            builder=row.get("builder", "generic"),
            builder_name=row.get("builder_name", ""),
            existing_html=row.get("existing_html", ""),
            takeaway=row.get("takeaway", []) or [],
            reference_slug=row.get("reference_slug", ""),
            reference_html=row.get("reference_html", ""),
            yaml_deck=row.get("yaml_deck", ""),
            skip=bool(row.get("skip", False)),
            skip_reason=row.get("skip_reason", ""),
        ))
    return SermonPack(
        pack_id=data.get("pack_id", pack_yaml.stem),
        pack_dir=pack_dir,
        yaml_examples_dir=yaml_examples,
        draft_dir=draft_dir,
        cover_dir=cover_dir,
        visual_briefs_path=briefs_path,
        jobs=jobs,
    )


def job_by_slug(pack: SermonPack, slug: str) -> SermonJob:
    for job in pack.jobs:
        if job.slug == slug:
            return job
    raise KeyError(f"Unknown slug: {slug}")
