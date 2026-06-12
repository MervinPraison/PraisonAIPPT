"""Video-first policy — local screen recordings, not mythos slide decks."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.audience_language import validate_audience_language
from praisonaippt.daily_single.project import DailySingleProject

MYTHOS_SLIDE_MARKERS = (
    "beat1-views-overlay",
    "beat2-tier-diagram",
    "beat3-stripe-card",
    "beat4-stat-overlay",
    "beat5-spire-stat",
    "gpt-image-safeguard-fallback",
)
HOOK_SPECTACLE_BANS = (
    "demo-scroll",
    "demo-pokemon",
    "demo-solar",
)
BODY_SPECTACLE_BANS = HOOK_SPECTACLE_BANS
MISLABELLED_CLIPS = ("fallback-notification",)
BANNED_CLIP_MD5 = frozenset({
    "589121a8f556e058172cbeda024eed5b",  # vintage B-roll mislabelled as x-claudeai-launch
})

PROGRAMMATIC_HOOK_MARKERS = (
    "v2-headline-vs-receipt",
    "v2-false-positive",
    "v2-quote-willison",
    "v2-two-safeties",
    "v2-inequality-ladder",
    "beat1-launch-summary",
    "social-capture-reddit",
    "inequality-ladder",
    "social-capture-hn",
)
VIDEO_FIRST_BEATS = (1, 2, 4, 5)


def validate_video_first_policy(project: DailySingleProject) -> tuple[bool, list[str], dict[str, Any]]:
    issues: list[str] = []
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    policy = str(beat_map.get("asset_policy") or "")

    if policy not in ("video-first-local",):
        return True, [], {"asset_policy": policy, "skipped": True}

    is_social = beat_map.get("variant") == "social-comparison"

    for beat_n, beat in (beat_map.get("beats") or {}).items():
        for pool in ("clips", "images", "generated"):
            for item in beat.get(pool) or []:
                path = str(item.get("path") or "")
                name = Path(path).name.lower()
                if any(m in name for m in MYTHOS_SLIDE_MARKERS):
                    issues.append(
                        f"Beat {beat_n}: still uses old mythos slide {name} — use local video instead"
                    )
                if any(m in name for m in MISLABELLED_CLIPS):
                    issues.append(
                        f"Beat {beat_n}: mislabelled clip {name} — vintage scroll B-roll, not a safety pop-up"
                    )
                if any(m in name for m in BODY_SPECTACLE_BANS):
                    issues.append(
                        f"Beat {beat_n}: spectacle scroll clip {name} — use screen recordings with in_sec offsets"
                    )
                if name.startswith("v2-") and beat_map.get("variant") in ("trust-audit", "social-comparison"):
                    issues.append(
                        f"Beat {beat_n}: programmatic v2 slide {name} — use video clips or chart PNGs only"
                    )
                if path and not Path(path).is_file():
                    issues.append(f"Beat {beat_n}: missing file {name}")

    if is_social:
        import hashlib

        x_dir = project.root / "research/reference-videos/x"
        for fname in (
            "x-claudeai-launch.mp4",
            "x-claudeai-safeguards.mp4",
            "x-chrissgpt-minecraft.mp4",
            "x-chrissgpt-pokemon.mp4",
        ):
            clip = x_dir / fname
            if not clip.is_file():
                issues.append(
                    f"Missing X clip {fname} — run scripts/download_x_clips.sh"
                )
                continue
            digest = hashlib.md5(clip.read_bytes()).hexdigest()
            if digest in BANNED_CLIP_MD5:
                issues.append(
                    f"Corrupt X clip {fname} (MD5 {digest[:8]}) — re-run scripts/download_x_clips.sh"
                )
        sources = project.root / "research/social-sources.json"
        if not sources.is_file():
            issues.append("Missing research/social-sources.json — catalog X URLs before build")
    elif not is_social:
        linkedin = project.root / "research/reference-videos/social/linkedin-cintas-fable5-vs-opus.mp4"
        if not linkedin.is_file():
            issues.append(
                "Missing LinkedIn comparison clip — download with scripts/download_social_videos.sh"
            )

    for bn in VIDEO_FIRST_BEATS:
        beat = (beat_map.get("beats") or {}).get(str(bn)) or {}
        clips = beat.get("clips") or []
        if not clips:
            issues.append(f"Beat {bn}: video-first build needs at least one screen-recording clip")

    from praisonaippt.daily_single.hook_montage import load_hook_montage_plan

    plan = load_hook_montage_plan(project)
    motion_montage = 0
    for cue in plan.get("cues") or []:
        fn = (cue.get("file") or "").lower()
        if any(m in fn for m in PROGRAMMATIC_HOOK_MARKERS):
            issues.append(
                f"Hook montage uses programmatic text slide {cue.get('file')} — "
                "replace with a screen-recording clip for a professional look"
            )
        if any(m in fn for m in HOOK_SPECTACLE_BANS):
            issues.append(
                f"Hook montage uses spectacle scroll clip {cue.get('file')} — "
                "replace with launch, LinkedIn, or safety clips only"
            )
        if fn.endswith(".mp4"):
            motion_montage += 1
        elif fn.endswith(".png") or fn.endswith(".jpg"):
            issues.append(
                f"Hook montage must use video clips only — not still slide {cue.get('file')}"
            )
    if motion_montage < 3:
        issues.append(
            f"Hook montage needs at least three video clips — only {motion_montage} motion heroes"
        )

    lang_ok, lang_issues = validate_audience_language(project)
    if not lang_ok:
        for msg in lang_issues[:8]:
            issues.append(f"Plain language: {msg}")

    x_launch = project.root / "research/reference-videos/x/x-claudeai-launch.mp4"
    return len(issues) == 0, issues, {
        "asset_policy": policy,
        "x_launch_clip": x_launch.is_file(),
        "language_ok": lang_ok,
    }
