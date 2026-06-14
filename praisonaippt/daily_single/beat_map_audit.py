"""Beat-map policy — banned assets, LinkedIn placement, body clip diversity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.hook_montage import build_hook_montage_plan
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.video_first_audit import (
    BODY_SPECTACLE_BANS,
    MISLABELLED_CLIPS,
    PROGRAMMATIC_HOOK_MARKERS,
)

LINKEDIN_MARKER = "linkedin-cintas"
TRUST_AUDIT_LINKEDIN_BODY_BEATS = frozenset({"1", "2"})
SOCIAL_COMPARISON_LINKEDIN_BEATS = frozenset({"1", "2", "3", "4"})
SOCIAL_CLIP_MARKERS = ("x-", "social-capture")
COMPARISON_CLIP_PREFIX = "x-comparison-"
YOUTUBE_CLIP_MARKER = "youtube-"
MIN_DISTINCT_SOCIAL_CLIPS = 3
BODY_BEATS = tuple(str(n) for n in range(3, 11))
MAX_BODY_CLIP_SHARE = 0.38
MAX_SOCIAL_CLIP_SHARE = 0.46
MAX_BODY_LINKEDIN_SEC = 32.0
DEFAULT_CLIP_SEC = 10.0


def _clip_seconds(item: dict[str, Any]) -> float:
    try:
        out_s = float(item.get("out_sec") or 0)
        in_s = float(item.get("in_sec") or 0)
        if out_s > in_s:
            return out_s - in_s
    except (TypeError, ValueError):
        pass
    return DEFAULT_CLIP_SEC


def _fname(item: dict[str, Any]) -> str:
    path = str(item.get("path") or "")
    if path:
        return Path(path).name
    return str(item.get("filename") or "")


def _is_banned_asset(name: str) -> str | None:
    lower = name.lower()
    if any(m in lower for m in MISLABELLED_CLIPS):
        return "mislabelled clip (vintage B-roll, not a safety pop-up)"
    if any(m in lower for m in BODY_SPECTACLE_BANS):
        return "spectacle scroll clip — use screen recordings with in_sec offsets"
    if lower.startswith("v2-"):
        return "programmatic v2 slide — use video clips or chart PNGs only"
    return None


def _file_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_beat_map_policy(project: DailySingleProject) -> dict[str, Any]:
    """Fail early on beat-map choices that caused trust-audit regressions."""
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    variant = str(beat_map.get("variant") or "")
    policy = str(beat_map.get("asset_policy") or "")
    trust = variant == "trust-audit" and policy == "video-first-local"
    social = variant == "social-comparison" and policy == "video-first-local"
    video_first = trust or social

    issues: list[str] = []
    warnings: list[str] = []
    body_clip_sec: dict[str, float] = {}
    social_clip_sec: dict[str, float] = {}
    body_linkedin_sec = 0.0
    distinct_social: set[str] = set()
    content_hashes: dict[str, set[str]] = {}

    for beat_n, beat in (beat_map.get("beats") or {}).items():
        for pool in ("clips", "images", "generated"):
            for item in beat.get(pool) or []:
                name = _fname(item)
                if not name:
                    continue
                ban = _is_banned_asset(name)
                if ban:
                    issues.append(f"Beat {beat_n}: {name} — {ban}")
                lower = name.lower()
                if any(m in lower for m in SOCIAL_CLIP_MARKERS) and pool == "clips":
                    distinct_social.add(name)
                if trust and beat_n in BODY_BEATS and pool == "clips":
                    sec = _clip_seconds(item)
                    body_clip_sec[name] = body_clip_sec.get(name, 0.0) + sec
                    if LINKEDIN_MARKER in lower:
                        issues.append(
                            f"Beat {beat_n}: LinkedIn clip only allowed in beats 1–2 "
                            "(headline vs receipt, side-by-side work)"
                        )
                        body_linkedin_sec += sec
                if social and pool == "clips" and YOUTUBE_CLIP_MARKER in lower:
                    issues.append(
                        f"Beat {beat_n}: {name} — social-comparison is X-only; remove YouTube clips"
                    )
                if social and pool == "clips" and "linkedin-cintas" in lower and COMPARISON_CLIP_PREFIX not in lower:
                    issues.append(
                        f"Beat {beat_n}: {name} — use x-comparison-* trims in research/reference-videos/x/"
                    )
                if social and pool == "clips":
                    sec = _clip_seconds(item)
                    if any(m in lower for m in SOCIAL_CLIP_MARKERS):
                        social_clip_sec[name] = social_clip_sec.get(name, 0.0) + sec
                if video_first and pool == "clips":
                    path = Path(str(item.get("path") or ""))
                    digest = _file_digest(path)
                    if digest:
                        content_hashes.setdefault(digest, set()).add(name)
                        if social and any(m in lower for m in SOCIAL_CLIP_MARKERS):
                            distinct_social.add(digest)

    if video_first:
        for digest, names in content_hashes.items():
            unique = sorted(names)
            if len(unique) > 1:
                issues.append(
                    "Duplicate clip bytes under different filenames: "
                    + ", ".join(unique)
                    + " — use one name or a distinct source file"
                )

    if trust:
        for beat_n in TRUST_AUDIT_LINKEDIN_BODY_BEATS:
            beat = (beat_map.get("beats") or {}).get(beat_n) or {}
            clips = beat.get("clips") or []
            if not any(LINKEDIN_MARKER in _fname(c).lower() for c in clips):
                warnings.append(
                    f"Beat {beat_n}: trust-audit usually includes LinkedIn comparison clip"
                )

        total_body = sum(body_clip_sec.values())
        if total_body > 0:
            for fname, sec in sorted(body_clip_sec.items(), key=lambda x: -x[1]):
                share = sec / total_body
                if share > MAX_BODY_CLIP_SHARE:
                    issues.append(
                        f"Body clip mix: {fname} is {share:.0%} of beats 3–10 MP4 time "
                        f"({sec:.0f}s) — diversify (target ≤{MAX_BODY_CLIP_SHARE:.0%} per clip)"
                    )
        if body_linkedin_sec > MAX_BODY_LINKEDIN_SEC:
            issues.append(
                f"LinkedIn appears {body_linkedin_sec:.0f}s in body beats 3+ — "
                f"keep LinkedIn to beats 1–2 only (~{MAX_BODY_LINKEDIN_SEC:.0f}s max elsewhere)"
            )

    if social:
        if len(distinct_social) < MIN_DISTINCT_SOCIAL_CLIPS:
            issues.append(
                f"social-comparison needs ≥{MIN_DISTINCT_SOCIAL_CLIPS} distinct comparison clips "
                f"in beat-map — found {len(distinct_social)}"
            )
        total_social = sum(social_clip_sec.values())
        if total_social > 0:
            for fname, sec in sorted(social_clip_sec.items(), key=lambda x: -x[1]):
                share = sec / total_social
                if share > MAX_SOCIAL_CLIP_SHARE:
                    issues.append(
                        f"Social clip mix: {fname} is {share:.0%} of comparison MP4 time "
                        f"({sec:.0f}s) — add more X sources (target ≤{MAX_SOCIAL_CLIP_SHARE:.0%})"
                    )
        x_dir = project.root / "research" / "reference-videos" / "x"
        for clip_id in (
            "x-claudeai-launch.mp4",
            "x-claudeai-safeguards.mp4",
            "x-chrissgpt-minecraft.mp4",
        ):
            if not (x_dir / clip_id).is_file():
                warnings.append(f"Missing X clip — run scripts/download_x_clips.sh ({clip_id})")

    plan = build_hook_montage_plan(project)
    for cue in plan.get("cues") or []:
        fname = str(cue.get("file") or "")
        if not fname:
            continue
        ban = _is_banned_asset(fname)
        if ban:
            issues.append(f"Hook montage: {fname} — {ban}")
        if any(m in fname.lower() for m in PROGRAMMATIC_HOOK_MARKERS):
            issues.append(
                f"Hook montage: programmatic text slide {fname} — use screen recordings"
            )

    ok = len(issues) == 0
    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": ok,
        "trust_audit": trust,
        "social_comparison": social,
        "asset_policy": policy,
        "body_clip_seconds": {k: round(v, 1) for k, v in sorted(body_clip_sec.items())},
        "social_clip_seconds": {k: round(v, 1) for k, v in sorted(social_clip_sec.items())},
        "distinct_social_clips": sorted(distinct_social),
        "body_linkedin_seconds": round(body_linkedin_sec, 1),
        "issues": issues,
        "warnings": warnings,
    }
    out = project.merge_dir / "beat_map_policy_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
