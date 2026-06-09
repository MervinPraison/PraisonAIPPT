"""Pipeline stage — crawl missing canonical assets into handoff."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from ..project import SegmentVideoProject
from ..validation.required_assets import fill_handoff_gaps


def run_crawl_missing_assets(
    project: SegmentVideoProject,
    *,
    segments: list[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    protocol = project.load_protocol()
    cfg = (protocol.get("validation_suite") or {}).get("required_assets") or {}
    fetch = bool(cfg.get("fetch_canonical", True))

    only_slugs = None
    if segments:
        manifest = project.load_manifest()
        only_slugs = []
        for seg in manifest.get("segments", []):
            if seg["dir"] in segments and seg.get("slug"):
                only_slugs.append(seg["slug"])

    emit("crawl-missing-assets: fetching canonical images for handoff gaps…")
    report = fill_handoff_gaps(
        project.root,
        protocol,
        fetch_canonical=fetch,
        only_slugs=only_slugs,
    )

    from ..assets.canonical_crawl import enrich_handoff_descriptions
    from ..manifest import load_manifest
    review_path = Path(project.load_manifest()["research_dir"]) / "review-data.json"
    for seg in project.load_manifest().get("segments", []):
        if seg.get("slide_type") == "avatar_media_3" and seg.get("slug"):
            n = enrich_handoff_descriptions(review_path, seg["slug"])
            if n:
                emit(f"  enriched {n} description(s) for {seg['slug']}")
    out = project.root / "asset_crawl_report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for line in report.get("logs") or []:
        emit(f"  {line}")

    added = report.get("added_total", 0)
    emit(f"crawl-missing-assets → {out} (+{added} image(s))")
    return 0
