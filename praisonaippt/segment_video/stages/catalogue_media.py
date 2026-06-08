"""catalogue-media stage — audit all review assets; enrich rejection metadata."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from ..image_selection import is_relevant_image
from ..manifest import load_manifest
from ..project import SegmentVideoProject


def run_catalogue_media(
    project: SegmentVideoProject,
    *,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    root = project.root
    protocol = project.load_protocol()
    rules = protocol.get("image_selection") or {}
    manifest = load_manifest(root)
    review_data_path = Path(manifest["research_dir"]) / "review-data.json"
    topics = {t["topic_slug"]: t for t in json.loads(review_data_path.read_text())["topics"]}

    catalog: dict = {"schema_version": 1, "topics": {}}
    for seg in manifest.get("segments", []):
        slug = seg.get("slug")
        if seg.get("slide_type") != "avatar_media_3" or not slug:
            continue
        topic = topics.get(slug)
        if not topic:
            continue
        images = topic.get("images") or []
        accepted = []
        rejected = []
        for img in images:
            row = {
                "filename": img.get("filename"),
                "topic_relevance_score": img.get("topic_relevance_score"),
                "topic_relevance_label": img.get("topic_relevance_label"),
                "editorial_rank": img.get("editorial_rank"),
                "vision_description": img.get("vision_description"),
                "asset_type": img.get("asset_type"),
            }
            if is_relevant_image(img, rules):
                accepted.append(row)
            else:
                row["reject_reason"] = "below_relevance_threshold"
                rejected.append(row)
        catalog["topics"][slug] = {
            "segment_dir": seg["dir"],
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "accepted": accepted,
            "rejected": rejected,
        }
        emit(f"catalogue {slug}: {len(accepted)} relevant, {len(rejected)} rejected")

    out = root / "asset_catalog.json"
    out.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    emit(f"catalogue-media → {out}")
    return 0
