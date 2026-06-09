"""Validate handoff assets cover spoken content — detect gaps before build."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..assets.canonical_crawl import (
    crawl_topic,
    enrich_handoff_descriptions,
    extract_image_urls,
    fetch_page,
    handoff_image_keys,
    ingest_urls,
    merge_review_data,
    missing_page_keys,
    persist_topic_images,
    promote_marginal_assets,
)
from ..image_selection import build_cue_plan, sentence_groups


CHART_SPEECH = re.compile(
    r"\b(throughput|benchmark|inference|five times|5x|cost|performance|accuracy|mmlu|chart|efficiency)\b",
    re.I,
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _manual_slugs(protocol: dict) -> set[str]:
    return {g.get("topic_slug") for g in protocol.get("manual_asset_gaps") or [] if g.get("topic_slug")}


def _speech_wants_chart(script: str) -> list[int]:
    """Sentence indices that mention benchmark/chart concepts."""
    return [i for i, s in enumerate(sentence_groups(script)) if CHART_SPEECH.search(s)]


def audit_topic_gaps(
    seg: dict,
    topic: dict,
    script: str,
    rules: dict,
    *,
    manual_slugs: set[str],
    fetch_canonical: bool = True,
) -> dict[str, Any]:
    slug = topic.get("topic_slug") or seg.get("slug") or ""
    sentences = sentence_groups(script)
    n_sent = len(sentences)
    images = topic.get("images") or []
    n_relevant = sum(1 for i in images if i.get("topic_relevance_label") == "relevant")
    n_charts = sum(1 for i in images if i.get("asset_type") == "benchmark_chart")

    seg_rules = {
        **rules,
        "_topic_top_picks": topic.get("top_picks") or [],
        "_allow_marginal_manual": bool(topic.get("needs_manual_asset")),
    }
    planned, _ = build_cue_plan(script, images, seg_rules)
    n_planned = len(planned)
    planned_types = {c.get("asset_type") for c in planned}
    chart_sentences = _speech_wants_chart(script)

    canonical = topic.get("canonical_url") or ""
    missing_hints: list[str] = []
    if fetch_canonical and canonical:
        html, _ = fetch_page(canonical)
        if html:
            urls = [u for u, _ in extract_image_urls(html, canonical)]
            missing_hints = missing_page_keys(urls, handoff_image_keys(topic))

    gaps: list[dict] = []
    if slug in manual_slugs or topic.get("needs_manual_asset"):
        gaps.append({"type": "manual_exempt", "detail": "listed in manual_asset_gaps"})

    if missing_hints:
        gaps.append({
            "type": "handoff_uncrawled",
            "detail": f"canonical page has uncrawled assets (e.g. {missing_hints[0][:40]})",
            "hints": missing_hints[:8],
        })

    need = min(n_sent, int(rules.get("max_cues_per_segment", 4)))
    if n_relevant < need and slug not in manual_slugs:
        gaps.append({
            "type": "insufficient_pool",
            "detail": f"{n_relevant} relevant image(s) for {n_sent} sentence(s)",
        })

    if n_planned < n_sent and n_relevant >= 2:
        gaps.append({
            "type": "cue_shortfall",
            "detail": f"{n_planned} planned cue(s) for {n_sent} sentence(s)",
        })

    if chart_sentences and "benchmark_chart" not in planned_types and n_charts > 0:
        gaps.append({
            "type": "selection_gap",
            "detail": "script mentions benchmark/throughput but no chart selected",
            "sentence_indices": chart_sentences,
        })

    if chart_sentences and n_charts == 0 and not missing_hints and slug not in manual_slugs:
        gaps.append({
            "type": "speech_asset_missing",
            "detail": "spoken benchmark content but no chart in handoff",
            "sentence_indices": chart_sentences,
        })

    critical = [g for g in gaps if g["type"] != "manual_exempt"]
    return {
        "dir": seg["dir"],
        "slug": slug,
        "sentences": n_sent,
        "planned_cues": n_planned,
        "handoff_relevant": n_relevant,
        "handoff_charts": n_charts,
        "canonical_missing_hints": missing_hints[:5],
        "gaps": gaps,
        "ok": len(critical) == 0,
        "needs_crawl": any(g["type"] == "handoff_uncrawled" for g in gaps),
        "needs_resync": any(g["type"] in ("selection_gap", "cue_shortfall", "insufficient_pool") for g in gaps),
    }


def audit_required_assets(
    project_root: Path,
    protocol: dict,
    *,
    fetch_canonical: bool = True,
) -> dict[str, Any]:
    from ..manifest import load_manifest

    manifest = load_manifest(project_root)
    review_path = Path(manifest["research_dir"]) / "review-data.json"
    topics = {t["topic_slug"]: t for t in _load_json(review_path)["topics"]}
    rules = protocol.get("image_selection") or {}
    manual = _manual_slugs(protocol)

    rows: list[dict] = []
    for seg in manifest.get("segments", []):
        if seg.get("slide_type") != "avatar_media_3":
            continue
        slug = seg.get("slug") or ""
        topic = topics.get(slug)
        if not topic:
            continue
        script_path = project_root / "segments" / seg["dir"] / "script.md"
        script = script_path.read_text(encoding="utf-8").strip() if script_path.is_file() else ""
        rows.append(audit_topic_gaps(
            seg, topic, script, rules,
            manual_slugs=manual,
            fetch_canonical=fetch_canonical,
        ))

    failed = [r for r in rows if not r["ok"]]
    crawl_targets = [r for r in rows if r.get("needs_crawl")]
    return {
        "schema_version": 1,
        "ok": len(failed) == 0,
        "topics": rows,
        "summary": {
            "total": len(rows),
            "failed": len(failed),
            "needs_crawl": len(crawl_targets),
            "needs_resync": sum(1 for r in rows if r.get("needs_resync")),
        },
    }


# Known high-value URLs when canonical HTML parse / CDN blocks fail
FALLBACK_URLS: dict[str, list[tuple[str, str]]] = {
    "anthropic-mitre-ai-cyber-threats": [
        (
            "https://cdn.sanity.io/images/4zrzovbb/website/6d4a0d28992ade92d6fa63646fd9c9d318245c6c-2400x1260.jpg",
            "MITRE ATT&CK AI threat mapping",
        ),
    ],
    "anthropic-how-we-contain-claude": [
        (
            "https://cdn.sanity.io/images/4zrzovbb/website/5fae1ecca4cd8aaefb9ac949348e96967f9a5100-1920x1080.png",
            "Claude containment workflow diagram",
        ),
        (
            "https://cdn.sanity.io/images/4zrzovbb/website/ffc97a876bdeba2031ddaeef79a954e9b1b2d52a-1920x1080.png",
            "Claude containment architecture diagram",
        ),
        (
            "https://cdn.sanity.io/images/4zrzovbb/website/a81ed723d52f6fb2e7bc5ca51471496b1307101a-1920x1080.png",
            "Claude safety containment layers diagram",
        ),
    ],
    "jetbrains-mellum2-12b-moe": [
        (
            "https://cdn-uploads.huggingface.co/production/uploads/60ef2a438432bc401cd0abbe/tFjSaWUOM_pVsgKjHrAHt.png",
            "Mellum2 JetBrains MoE benchmark chart",
        ),
    ],
    "aws-bedrock-gpt-5-5-codex-ga": [
        (
            "https://d1.awsstatic.com/onedam/marketing-channels/website/aws/en_US/homepage/theme-card-bedrock.b10cd0415583b9f36e5c49db17edee9139634b59.png",
            "Amazon Bedrock OpenAI Codex GPT deployment",
        ),
    ],
}


def fill_handoff_gaps(
    project_root: Path,
    protocol: dict,
    *,
    fetch_canonical: bool = True,
    only_slugs: list[str] | None = None,
) -> dict[str, Any]:
    """Crawl canonical URLs and patch review-data for topics with handoff_uncrawled gaps."""
    from ..manifest import load_manifest

    manifest = load_manifest(project_root)
    review_path = Path(manifest["research_dir"]) / "review-data.json"
    assets_dir = Path(manifest["review_assets_dir"])
    manual = _manual_slugs(protocol)
    audit = audit_required_assets(project_root, protocol, fetch_canonical=fetch_canonical)

    # Enrich descriptions for all topic segments
    from ..manifest import load_manifest as _lm
    m = _lm(project_root)
    rd = _load_json(review_path)
    for seg in m.get("segments", []):
        if seg.get("slide_type") == "avatar_media_3" and seg.get("slug"):
            enrich_handoff_descriptions(review_path, seg["slug"])

    logs: list[str] = []
    crawled: list[dict] = []
    for row in audit["topics"]:
        slug = row["slug"]
        if only_slugs and slug not in only_slugs:
            continue
        gap_types = {g["type"] for g in row.get("gaps") or []}
        needs_work = (
            row.get("needs_crawl")
            or row.get("needs_resync")
            or "insufficient_pool" in gap_types
            or "handoff_uncrawled" in gap_types
            or row.get("handoff_relevant", 0) < row.get("sentences", 1)
        )
        if not needs_work and row.get("ok"):
            continue

        data = _load_json(review_path)
        topic = next(t for t in data["topics"] if t["topic_slug"] == slug)
        promoted = promote_marginal_assets(review_path, slug)
        if promoted:
            logs.append(f"{slug}: promoted {promoted} marginal asset(s) to relevant")
            data = _load_json(review_path)
            topic = next(t for t in data["topics"] if t["topic_slug"] == slug)

        hints: list[str] = []
        for g in row.get("gaps") or []:
            if g.get("type") == "handoff_uncrawled":
                hints.extend(g.get("hints") or [])
        hints.extend(row.get("canonical_missing_hints") or [])

        aggressive = (
            "insufficient_pool" in gap_types
            or row.get("handoff_relevant", 0) < 2
            or slug in manual
        )
        new_images, topic_logs = crawl_topic(
            topic, assets_dir, hints=hints or None, aggressive=aggressive, max_images=10,
        )
        logs.extend(topic_logs)
        n = merge_review_data(review_path, slug, new_images)
        if n:
            crawled.append({"slug": slug, "added": n, "files": [i["filename"] for i in new_images]})
            logs.append(f"{slug}: merged {n} image(s) into review-data.json")
        enrich_handoff_descriptions(review_path, slug)

        if slug in FALLBACK_URLS:
            data = _load_json(review_path)
            topic = next(t for t in data["topics"] if t["topic_slug"] == slug)
            fb_images, fb_logs = ingest_urls(topic, assets_dir, FALLBACK_URLS[slug])
            logs.extend(fb_logs)
            if any("repaired" in line for line in fb_logs):
                persist_topic_images(review_path, slug, topic.get("images") or [])
            n2 = merge_review_data(review_path, slug, fb_images)
            if n2:
                crawled.append({"slug": slug, "added": n2, "files": [i["filename"] for i in fb_images]})
                logs.append(f"{slug}: fallback ingested {n2} image(s)")
        promoted2 = promote_marginal_assets(review_path, slug)
        if promoted2:
            logs.append(f"{slug}: promoted {promoted2} asset(s) after crawl")

    return {
        "schema_version": 1,
        "audit_before": audit,
        "crawled": crawled,
        "logs": logs,
        "added_total": sum(c["added"] for c in crawled),
    }
