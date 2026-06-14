"""Resource usefulness QA — score related clips for topical, informational value."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.publish_quality_config import beat_map_variant
from praisonaippt.segment_video.image_selection import script_alignment

MIN_USEFULNESS = 0.34
MIN_USEFUL_CATALOG = 6
MIN_USED_CLIP_SCORE = 0.30
INFORMATIONAL_BONUS = re.compile(
    r"\b(comparison|compare|split|same.?prompt|side.?by.?side|benchmark|walkthrough|"
    r"build|demo|test|opus|fable|gpt|performance|working|ship)\b",
    re.I,
)
LOW_VALUE_PENALTY = re.compile(r"\b(teaser|trailer|reaction only|logo|hype montage)\b", re.I)


def _social_sources_path(project: DailySingleProject) -> Path:
    return project.root / "research" / "social-sources.json"


def _topic_text(project: DailySingleProject) -> str:
    parts: list[str] = []
    src = _social_sources_path(project)
    if src.is_file():
        data = json.loads(src.read_text(encoding="utf-8"))
        parts.append(str(data.get("focus") or ""))
    if project.video_script_path.is_file():
        parts.append(project.video_script_path.read_text(encoding="utf-8")[:2000])
    if project.beat_map_path.is_file():
        bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
        parts.append(str(bm.get("variant") or ""))
        parts.append(str(bm.get("asset_policy") or ""))
    return " ".join(parts).strip() or project.slug.replace("-", " ")


def _beat_map_used_files(project: DailySingleProject) -> set[str]:
    if not project.beat_map_path.is_file():
        return set()
    bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    used: set[str] = set()
    for spec in (bm.get("beats") or {}).values():
        for clip in spec.get("clips") or []:
            path = str(clip.get("path") or clip.get("filename") or "")
            if path:
                used.add(Path(path).name.lower())
                used.add(Path(path).stem.lower())
    return used


def _catalog_in_use(entry: dict[str, Any], used_files: set[str]) -> bool:
    local = Path(str(entry.get("local_file") or "")).name.lower()
    if not local:
        return False
    stem = local.replace(".mp4", "").replace("youtube-", "").replace("linkedin-", "")
    tokens = [t for t in re.split(r"[-_]", stem) if len(t) > 3]
    for used in used_files:
        if local == used or local in used or used in local:
            return True
        if sum(1 for t in tokens if t in used) >= 2:
            return True
    return False


def score_resource(
    entry: dict[str, Any],
    topic: str,
    *,
    variant: str = "",
) -> tuple[float, list[str]]:
    """Return usefulness score 0–1 and short rationale tags."""
    blob = " ".join(
        str(entry.get(k) or "")
        for k in ("title", "notes", "id", "author", "angle", "platform")
    )
    img = {
        "vision_description": blob,
        "relevance_reason": blob,
        "topic_relevance_score": 0.75 if INFORMATIONAL_BONUS.search(blob) else 0.45,
    }
    score = script_alignment(topic, img)
    tags: list[str] = []
    if INFORMATIONAL_BONUS.search(blob):
        score = min(1.0, score + 0.08)
        tags.append("informational_keywords")
    if variant == "social-comparison" and re.search(r"\b(opus|split|same.?prompt|comparison)\b", blob, re.I):
        score = min(1.0, score + 0.06)
        tags.append("comparison_fit")
    if LOW_VALUE_PENALTY.search(blob):
        score = max(0.0, score - 0.15)
        tags.append("low_value_signal")
    return round(score, 3), tags


def validate_resource_usefulness(project: DailySingleProject) -> dict[str, Any]:
    """Score catalog clips against main topic; flag weak picks and suggest better resources."""
    src_path = _social_sources_path(project)
    if not src_path.is_file():
        report = {
            "schema_version": 1,
            "ok": False,
            "issues": ["missing research/social-sources.json — catalog related videos first"],
            "rows": [],
        }
        out = project.merge_dir / "resource_usefulness_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    catalog = json.loads(src_path.read_text(encoding="utf-8"))
    topic = _topic_text(project)
    variant = beat_map_variant(project)
    used_files = _beat_map_used_files(project)
    issues: list[str] = []
    rows: list[dict[str, Any]] = []
    useful_count = 0
    fails = 0

    for entry in catalog.get("clips") or []:
        local = str(entry.get("local_file") or "")
        local_path = project.root / local if local else None
        exists = local_path.is_file() if local_path else False
        score, tags = score_resource(entry, topic, variant=variant)
        in_beat_map = _catalog_in_use(entry, used_files)
        useful = score >= MIN_USEFULNESS and exists
        if useful:
            useful_count += 1
        row_issues: list[str] = []
        if in_beat_map and score < MIN_USED_CLIP_SCORE:
            row_issues.append(f"usefulness {score:.2f} below {MIN_USED_CLIP_SCORE} for on-screen clip")
        if not exists and local:
            row_issues.append("local_file missing — download before build")
        if score < MIN_USEFULNESS:
            row_issues.append(f"low topical usefulness {score:.2f} for main topic")

        ok = not (in_beat_map and score < MIN_USED_CLIP_SCORE) and (exists or not local)
        if in_beat_map and score < MIN_USED_CLIP_SCORE:
            ok = False
            fails += 1
            issues.append(f"{entry.get('id')}: {row_issues[0]}")

        rows.append({
            "id": entry.get("id"),
            "title": entry.get("title"),
            "local_file": local,
            "file_exists": exists,
            "usefulness_score": score,
            "tags": tags,
            "in_beat_map": in_beat_map,
            "ok": ok,
            "issues": row_issues,
            "recommended": useful and not in_beat_map,
        })

    if useful_count < MIN_USEFUL_CATALOG:
        issues.append(
            f"only {useful_count} catalog clips score ≥{MIN_USEFULNESS} with local files — "
            f"add more informational comparison sources (need {MIN_USEFUL_CATALOG})"
        )

    recommendations = [
        r for r in rows
        if r.get("recommended") and r.get("usefulness_score", 0) >= MIN_USEFULNESS + 0.05
    ]
    recommendations.sort(key=lambda r: r["usefulness_score"], reverse=True)

    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": fails == 0 and useful_count >= MIN_USEFUL_CATALOG,
        "topic_excerpt": topic[:200],
        "variant": variant,
        "useful_catalog_count": useful_count,
        "min_useful_catalog": MIN_USEFUL_CATALOG,
        "resources_fail": fails,
        "issues": issues[:25],
        "rows": rows,
        "recommendations": recommendations[:8],
    }
    out = project.merge_dir / "resource_usefulness_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
