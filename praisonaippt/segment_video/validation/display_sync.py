"""Deep validation: captions ↔ slides ↔ speech ↔ handoff catalogue."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..assets.canonical_crawl import (
    extract_image_urls,
    fetch_page,
    handoff_image_keys,
    missing_page_keys,
)
from ..image_selection import sentence_groups
from ..manifest import load_manifest
from ..timeline import build_segment_timeline, parse_srt, resolve_at_time
from ..validate_sync import overlap_ratio


def _load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_handoff_catalogue(
    project_root: Path,
    manifest: dict,
    topics: dict[str, dict],
    *,
    fetch_canonical: bool = True,
    allow_synced_cue_fill: bool = True,
    manual_slugs: set[str] | None = None,
) -> dict[str, Any]:
    """Per topic: relevant pool size, cues used, canonical URL gaps."""
    assets = (_load_json(project_root / "media_assets.json") if (project_root / "media_assets.json").is_file() else {}).get("segments", {})
    rows: list[dict] = []
    for seg in manifest.get("segments", []):
        if seg.get("slide_type") != "avatar_media_3":
            continue
        slug = seg.get("slug") or ""
        topic = topics.get(slug) or {}
        seg_dir = project_root / "segments" / seg["dir"]
        script = (seg_dir / "script.md").read_text(encoding="utf-8").strip() if (seg_dir / "script.md").is_file() else ""
        n_sentences = len(sentence_groups(script))
        images = topic.get("images") or []
        n_relevant = sum(1 for i in images if i.get("topic_relevance_label") == "relevant")
        n_marginal = sum(1 for i in images if i.get("topic_relevance_label") == "marginal")
        n_charts = sum(1 for i in images if i.get("asset_type") == "benchmark_chart")
        cues = (assets.get(seg["dir"]) or {}).get("cues") or []
        n_cues = len(cues)

        canonical = topic.get("canonical_url") or ""
        missing_on_page: list[str] = []
        if fetch_canonical and canonical:
            html, _ = fetch_page(canonical)
            if html:
                page_urls = [u for u, _ in extract_image_urls(html, canonical)]
                handoff_keys = handoff_image_keys(topic)
                missing_on_page = missing_page_keys(page_urls, handoff_keys)

        need = min(n_sentences, 4)
        pool_ok = n_relevant >= need or (n_relevant + n_marginal >= need and n_cues >= 1)
        issues: list[str] = []
        if n_cues < n_sentences:
            issues.append(f"{n_cues} cue(s) for {n_sentences} sentence(s)")
        thin_pool = n_relevant < 2 and n_sentences >= 2
        synced_ok = allow_synced_cue_fill and n_cues >= n_sentences and n_relevant >= 1
        manual_ok = slug in (manual_slugs or set())
        if thin_pool and not synced_ok and not manual_ok:
            issues.append(f"only {n_relevant} relevant image(s) in handoff")
        if missing_on_page[:3]:
            issues.append(f"canonical page may have uncrawled assets (e.g. {missing_on_page[0][:40]})")

        rows.append({
            "dir": seg["dir"],
            "slug": slug,
            "sentences": n_sentences,
            "handoff_relevant": n_relevant,
            "handoff_marginal": n_marginal,
            "handoff_charts": n_charts,
            "media_cues": n_cues,
            "canonical_url": canonical,
            "canonical_missing_hints": missing_on_page[:5],
            "pool_ok": pool_ok,
            "ok": len(issues) == 0,
            "issues": issues,
        })
    failed = [r for r in rows if not r["ok"]]
    return {
        "schema_version": 1,
        "ok": len(failed) == 0,
        "topics": rows,
        "summary": {"total": len(rows), "failed": len(failed)},
    }


def validate_segment_caption_slides(
    seg_dir: Path,
    project_root: Path,
    *,
    time_tol: float = 0.06,
) -> dict[str, Any]:
    """Validate SRT ↔ timeline cues ↔ slide JPEGs for one segment."""
    tl_path = seg_dir / "timeline.json"
    if not tl_path.is_file():
        build_segment_timeline(seg_dir, project_root)
    timeline = _load_json(tl_path)
    cues = timeline.get("cues") or []
    srt_cues = timeline.get("srt_cues") or []

    if not srt_cues and (seg_dir / "segment.srt").is_file():
        srt_cues = parse_srt((seg_dir / "segment.srt").read_text(encoding="utf-8"))

    issues: list[str] = []
    rows: list[dict] = []
    for i, cue in enumerate(cues):
        notes = (cue.get("notes") or "").strip()
        start = float(cue.get("start_sec") or 0)
        end = float(cue.get("end_sec") or 0)
        media = Path(cue.get("media_path") or "").name
        jpeg = seg_dir / "slide_jpegs" / f"slide-{i + 1:03d}.jpg"
        mp4_frame = seg_dir / "slide_jpegs" / "mp4-frames" / f"mp4-slide-{i + 1:03d}.jpg"

        srt = srt_cues[i] if i < len(srt_cues) else {}
        cap = (srt.get("text") or "").strip()
        cap_start = float(srt["start_sec"]) if srt.get("start_sec") is not None else -1.0
        cap_end = float(srt["end_sec"]) if srt.get("end_sec") is not None else -1.0

        caption_text_ok = notes.lower() == cap.lower() if cap else bool(notes)
        caption_time_ok = (
            cap_start >= 0
            and abs(start - cap_start) <= time_tol
            and abs(end - cap_end) <= time_tol
        )
        jpeg_ok = jpeg.is_file()
        mp4_ok = mp4_frame.is_file()

        mid = start + (end - start) / 2
        resolved = resolve_at_time(timeline, mid)
        resolver_ok = (
            resolved.get("slide_index") == i
            and (resolved.get("caption") or {}).get("text", "").strip().lower() == notes.lower()
        )

        row_ok = caption_text_ok and caption_time_ok and jpeg_ok and resolver_ok
        if not caption_text_ok:
            issues.append(f"cue {i}: caption text mismatch ({cap!r} vs {notes!r})")
        if not caption_time_ok and cap:
            issues.append(f"cue {i}: caption timing drift >{time_tol}s")
        if not jpeg_ok:
            issues.append(f"cue {i}: missing {jpeg.name}")
        if not resolver_ok and notes:
            issues.append(f"cue {i}: resolve_at_time mismatch at t={mid:.2f}s")

        rows.append({
            "cue_index": i,
            "notes": notes,
            "caption": cap,
            "image": media,
            "start_sec": round(start, 2),
            "end_sec": round(end, 2),
            "jpeg_exists": jpeg_ok,
            "mp4_frame_exists": mp4_ok,
            "checks": {
                "caption_text": caption_text_ok,
                "caption_timing": caption_time_ok,
                "slide_jpeg": jpeg_ok,
                "resolver_mid": resolver_ok,
            },
            "ok": row_ok,
        })

    # SRT count vs cue count
    if srt_cues and len(srt_cues) != len(cues):
        issues.append(f"srt cues {len(srt_cues)} != timeline cues {len(cues)}")

    return {
        "dir": seg_dir.name,
        "ok": len(issues) == 0,
        "cue_count": len(cues),
        "issues": issues,
        "cues": rows,
    }


def validate_segment_speech_overlap(seg_dir: Path, *, min_overlap: float = 0.35) -> dict[str, Any]:
    """Check spoken fragment (notes) overlaps transcript window for each cue."""
    from praisonaippt.transcript_loader import load_whisper_json

    yaml_cues: list[dict] = []
    ts_path = seg_dir / "timestamps.json"
    ct_path = seg_dir / "cue_timings.json"
    if ct_path.is_file():
        yaml_cues = _load_json(ct_path).get("cues") or []
    if not yaml_cues:
        return {"dir": seg_dir.name, "ok": True, "skipped": True, "issues": [], "cues": []}

    if not ts_path.is_file():
        return {"dir": seg_dir.name, "ok": False, "issues": ["missing timestamps.json"], "cues": []}

    td = load_whisper_json(ts_path)
    issues: list[str] = []
    rows: list[dict] = []
    for i, cue in enumerate(yaml_cues):
        fragment = str(cue.get("script_fragment") or "")
        start = float(cue.get("audio_start_sec") or 0)
        dur = float(cue.get("duration_sec") or 0)
        window = ""
        if td.words:
            window = " ".join(w.word for w in td.words if start <= w.start < start + dur)
        else:
            for s in td.segments:
                if s.end > start and s.start < start + dur:
                    window += " " + s.text
        ov = overlap_ratio(fragment, window) if fragment else 1.0
        ok = ov >= min_overlap
        if not ok:
            issues.append(f"cue {i}: speech overlap {ov:.2f} < {min_overlap} ({fragment[:40]}…)")
        rows.append({
            "cue_index": i,
            "fragment": fragment,
            "overlap": round(ov, 3),
            "match_method": cue.get("match_method"),
            "ok": ok,
        })

    return {"dir": seg_dir.name, "ok": len(issues) == 0, "issues": issues, "cues": rows}


def validate_project_display(
    project_root: Path,
    protocol: dict,
    *,
    fetch_canonical: bool = True,
) -> dict[str, Any]:
    """Full in-depth display validation report."""
    manifest = load_manifest(project_root)
    review_path = Path(manifest["research_dir"]) / "review-data.json"
    topics = {t["topic_slug"]: t for t in _load_json(review_path)["topics"]}

    manual_slugs = {
        g.get("topic_slug") for g in protocol.get("manual_asset_gaps") or [] if g.get("topic_slug")
    }
    cfg = (protocol.get("validation_suite") or {}).get("display_sync") or {}
    catalogue = audit_handoff_catalogue(
        project_root,
        manifest,
        topics,
        fetch_canonical=fetch_canonical,
        allow_synced_cue_fill=bool(cfg.get("allow_synced_cue_fill", True)),
        manual_slugs=manual_slugs,
    )

    min_overlap = float(cfg.get("min_speech_overlap", 0.35))
    time_tol = float(cfg.get("caption_time_tol_sec", 0.06))

    segments_out: list[dict] = []
    for seg in manifest.get("segments", []):
        seg_dir = project_root / "segments" / seg["dir"]
        if seg.get("slide_type") not in ("avatar_media_3", "big_number"):
            continue
        if not seg_dir.is_dir():
            continue
        cap = validate_segment_caption_slides(seg_dir, project_root, time_tol=time_tol)
        speech = validate_segment_speech_overlap(seg_dir, min_overlap=min_overlap)
        segments_out.append({
            "dir": seg["dir"],
            "slide_type": seg.get("slide_type"),
            "caption_slides": cap,
            "speech_overlap": speech,
            "ok": cap.get("ok") and speech.get("ok"),
        })

    # Hook deep report
    hook_path = project_root / "hook_validation_report.json"
    hook_extra = _load_json(hook_path) if hook_path.is_file() else None

    failed = [s for s in segments_out if not s.get("ok")]
    return {
        "schema_version": 1,
        "ok": catalogue.get("ok") and len(failed) == 0,
        "catalogue": catalogue,
        "segments": segments_out,
        "hook": hook_extra,
        "summary": {
            "segments_checked": len(segments_out),
            "segments_failed": len(failed),
            "catalogue_failed": catalogue.get("summary", {}).get("failed", 0),
        },
    }
