"""Audit slide images against transcript and handoff review-data."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .align import load_cue_timings
from .image_selection import (
    build_cue_plan,
    is_relevant_image,
    rank_images,
    script_alignment,
    sentence_groups,
    validate_cue,
)
from .validate_sync import overlap_ratio


def hook_clauses(script: str) -> list[str]:
    """Split hook roll-call into per-topic clauses."""
    m = re.search(r"moves:\s*(.+?)\.\s*Here is what changed", script, re.I | re.S)
    if m:
        return [p.strip() for p in m.group(1).split(",") if p.strip()]
    return sentence_groups(script)


def hook_topic_phrase(seg: dict) -> str:
    """One spoken name per topic segment — must match montage order."""
    phrases = {
        "nvidia-nemotron-3-ultra": "Nemotron 3 Ultra",
        "google-gemma-4-12b": "Gemma 4 twelve billion",
        "microsoft-mai-family-build-2026": "seven Microsoft MAI models",
        "minimax-m3-1m-context": "MiniMax M3 with million-token context",
        "aws-bedrock-gpt-5-5-codex-ga": "GPT-five point five and Codex on Bedrock",
        "openai-codex-role-plugins-sites": "Codex role plugins",
        "huggingface-hf-cli-agents": "the hf CLI for agents",
        "huggingface-holo-3-1-local-agents": "Holo three point one for local desktop control",
        "jetbrains-mellum2-12b-moe": "Mellum2 from JetBrains",
        "anthropic-defending-code-harness": "Anthropic defending-code",
        "anthropic-how-we-contain-claude": "Claude containment",
        "huggingface-eva-bench-2": "EVA-Bench two point oh",
        "openai-gpt-rosalind-life-sciences": "GPT-Rosalind",
        "anthropic-mitre-ai-cyber-threats": "MITRE AI threat mapping",
        "meta-muse-spark-api-june": "Meta Muse Spark on watch",
    }
    slug = seg.get("slug") or ""
    return phrases.get(slug) or seg.get("headline") or seg.get("title") or slug


def build_hook_montage_plan(
    hook_script: str,
    topic_segments: list[dict],
    topics: dict[str, dict],
    *,
    hero_resolver: Any,
    rules: dict,
) -> tuple[list[dict], list[dict]]:
    """Map hook clauses → one hero per topic segment (cross-topic montage)."""
    cues: list[dict] = []
    rejected: list[dict] = []
    max_cues = int(rules.get("hook_montage_max_cues", 15))

    for i, seg in enumerate(topic_segments[:max_cues]):
        slug = seg.get("slug")
        if not slug:
            continue
        topic = topics.get(slug) or {}
        clause = hook_topic_phrase(seg)
        hero = hero_resolver(seg, topic)
        if not hero:
            rejected.append({
                "segment_dir": seg.get("dir"),
                "topic_slug": slug,
                "reject_reason": "no_hero_image",
                "script_fragment": clause,
            })
            continue
        score = script_alignment(clause, hero)
        cues.append({
            **hero,
            "file": hero.get("dest_file") or hero.get("file"),
            "source_filename": hero.get("filename") or hero.get("source_filename"),
            "script_fragment": clause,
            "script_alignment": score,
            "sentence_index": i,
            "narrative_order": len(cues) + 1,
            "topic_slug": slug,
            "topic_headline": seg.get("headline") or topic.get("title"),
            "alignment_method": "hook_montage",
        })
    return cues, rejected


def suggest_alternatives(
    fragment: str,
    images: list[dict],
    current_filename: str,
    rules: dict,
    *,
    limit: int = 3,
) -> list[dict]:
    """Rank handoff images that may fit the spoken fragment better."""
    out: list[dict] = []
    for score, img in rank_images(images, fragment, rules):
        fn = img.get("filename") or ""
        if fn == current_filename:
            continue
        if not is_relevant_image(img, rules):
            continue
        out.append({
            "filename": fn,
            "script_alignment": score,
            "topic_relevance_score": img.get("topic_relevance_score"),
            "asset_type": img.get("asset_type"),
            "vision_description": (img.get("vision_description") or "")[:120],
        })
        if len(out) >= limit:
            break
    return out


def audit_segment_images(
    seg: dict,
    *,
    script: str,
    media_entry: dict | None,
    topic: dict | None,
    rules: dict,
    seg_dir: Path | None = None,
    slide_dir: Path | None = None,
) -> dict:
    """Audit one segment's cues vs script and review-data pool."""
    issues: list[str] = []
    cues_report: list[dict] = []
    images = (topic or {}).get("images") or []
    sentences = sentence_groups(script)
    entry_cues = (media_entry or {}).get("cues") or []
    timings = load_cue_timings(seg_dir) if seg_dir else None

    if not entry_cues and seg.get("slide_type") == "avatar_media_3":
        issues.append("no media cues synced")
        planned, _ = build_cue_plan(script, images, rules)
        if not planned and not rules.get("allow_text_only_if_no_relevant"):
            issues.append("handoff has no relevant images for script")

    for i, cue in enumerate(entry_cues):
        fragment = str(cue.get("script_fragment") or "")
        src = cue.get("source_filename") or cue.get("file") or ""
        exists = bool(slide_dir and (slide_dir / str(cue.get("file") or "")).is_file())
        ok, cue_issues = validate_cue(cue, rules, exists=exists)
        alts = suggest_alternatives(fragment, images, src, rules) if images else []
        best_alt = alts[0] if alts else None
        cur_align = float(cue.get("script_alignment") or 0)
        better = (
            best_alt
            and best_alt["filename"] != src
            and float(best_alt["script_alignment"]) > cur_align + 0.08
        )

        row = {
            "cue_index": i,
            "file": cue.get("file"),
            "source_filename": src,
            "script_fragment": fragment[:160],
            "script_alignment": cue.get("script_alignment"),
            "topic_relevance_score": cue.get("topic_relevance_score"),
            "topic_relevance_label": cue.get("topic_relevance_label"),
            "asset_type": cue.get("asset_type"),
            "validated": ok,
            "issues": cue_issues,
            "alternatives": alts,
            "recommend_swap": best_alt["filename"] if better else None,
        }
        if timings and i < len(timings):
            row["audio_start_sec"] = timings[i].get("audio_start_sec")
            row["duration_sec"] = timings[i].get("duration_sec")
        cues_report.append(row)
        if not ok:
            issues.extend(f"cue {i}: {x}" for x in cue_issues)
        if better:
            issues.append(
                f"cue {i}: better handoff image {best_alt['filename']} "
                f"(align {best_alt['script_alignment']:.2f} vs {cue.get('script_alignment')})"
            )

    uncovered = max(0, len(sentences) - len(entry_cues))
    if uncovered and len(images) >= 2 and seg.get("slide_type") == "avatar_media_3":
        issues.append(f"{uncovered} script sentence(s) without a dedicated image cue")

    return {
        "dir": seg["dir"],
        "slug": seg.get("slug"),
        "slide_type": seg.get("slide_type"),
        "sentence_count": len(sentences),
        "cue_count": len(entry_cues),
        "handoff_relevant_count": sum(1 for img in images if is_relevant_image(img, rules)),
        "handoff_image_count": len(images),
        "cues": cues_report,
        "ok": len(issues) == 0,
        "issues": issues,
    }


def audit_project_images(project_root: Path, manifest: dict, protocol: dict) -> dict:
    """Full-project image ↔ transcript audit report."""
    rules = protocol.get("image_selection") or {}
    review_path = Path(manifest["research_dir"]) / "review-data.json"
    topics = {t["topic_slug"]: t for t in json.loads(review_path.read_text())["topics"]}
    assets_path = project_root / "media_assets.json"
    assets = json.loads(assets_path.read_text()) if assets_path.is_file() else {"segments": {}}
    slide_dir = project_root / "slide_images"

    segments_out: list[dict] = []
    hook_cfg = protocol.get("hook_montage") or {}
    topic_segs = [s for s in manifest["segments"] if s.get("slide_type") == "avatar_media_3"]

    for seg in manifest["segments"]:
        seg_dir = project_root / "segments" / seg["dir"]
        script_path = seg_dir / "script.md"
        script = script_path.read_text(encoding="utf-8").strip() if script_path.is_file() else ""
        slug = seg.get("slug")
        topic_slug = slug if slug != "hook" else None
        topic = topics.get(topic_slug) if topic_slug else None
        media_entry = assets.get("segments", {}).get(seg["dir"])

        if seg.get("slug") == "hook" and hook_cfg.get("enabled"):
            hook_entry = assets.get("segments", {}).get("00-hook")
            hook_rules = {**rules, "min_topic_relevance": 0.0, "require_topic_relevance_label": ""}
            report = audit_segment_images(
                seg,
                script=script,
                media_entry=hook_entry,
                topic=None,
                rules=hook_rules,
                seg_dir=seg_dir,
                slide_dir=slide_dir,
            )
            if not hook_entry or not hook_entry.get("cues"):
                report["issues"].append(
                    f"hook montage enabled but no cues — expected {len(topic_segs)} topic heroes"
                )
                report["ok"] = False
            segments_out.append(report)
            continue

        if seg.get("slide_type") != "avatar_media_3":
            segments_out.append({
                "dir": seg["dir"],
                "slide_type": seg.get("slide_type"),
                "skipped": True,
                "note": "non-media segment",
                "ok": True,
                "issues": [],
            })
            continue

        segments_out.append(
            audit_segment_images(
                seg,
                script=script,
                media_entry=media_entry,
                topic=topic,
                rules=rules,
                seg_dir=seg_dir,
                slide_dir=slide_dir,
            )
        )

    failed = [s for s in segments_out if not s.get("ok")]
    return {
        "schema_version": 1,
        "ok": len(failed) == 0,
        "failed_count": len(failed),
        "segments": segments_out,
        "summary": {
            "total": len(segments_out),
            "passed": len(segments_out) - len(failed),
            "failed": len(failed),
        },
    }
