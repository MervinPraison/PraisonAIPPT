"""Per-asset inventory gate — export one frame per planned asset and reject banned slides/clips."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.hook_montage import build_hook_montage_plan, load_hook_montage_plan
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.video_first_audit import PROGRAMMATIC_HOOK_MARKERS
from praisonaippt.daily_single.visual_audit import reference_frame_for_asset
from praisonaippt.vision_describe import _GENERIC_PATTERNS, describe_frame, vision_provider

HOOK_SPECTACLE_BANS = frozenset({
    "demo-scroll.mp4",
    "demo-pokemon.mp4",
    "demo-solar.mp4",
})

TRUST_AUDIT_HOOK_MP4_ALLOW = frozenset({
    "demo-launch.mp4",
    "demo-fluid.mp4",
    "demo-factorio.mp4",
    "linkedin-cintas-fable5-vs-opus.mp4",
})

SOCIAL_COMPARISON_HOOK_MP4_ALLOW = frozenset({
    "x-claudeai-launch.mp4",
    "x-claudeai-safeguards.mp4",
    "x-chrissgpt-minecraft.mp4",
    "x-chrissgpt-pokemon.mp4",
    "x-demo-deveshcodes-blackhole.mp4",
    "x-pootlepress-wp-theme.mp4",
    "x-trq212-edit-2064826394589442448.mp4",
    "x-trq212-edit-2064828193446740023.mp4",
})

TRUST_AUDIT_ATTENTION_BANS = frozenset({
    "canonical-scroll.mp4",
    "demo-scroll.mp4",
})

SKIP_FILES = frozenset({"heygen.mp4", "canonical-scroll.mp4", "brand-bumper-1080p-hevc.mp4", "none"})


def _planned_assets(project: DailySingleProject) -> list[dict[str, Any]]:
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    def add(*, source: str, file: str, path: str, beat: str, context: str = "", slot: str = "", in_sec: float = 0.0) -> None:
        if not file or file in SKIP_FILES:
            return
        key = (source, file, beat, slot)
        if key in seen:
            return
        seen.add(key)
        rows.append({
            "source": source,
            "file": file,
            "path": path,
            "beat": beat,
            "context": context,
            "in_sec": in_sec,
        })

    plan = build_hook_montage_plan(project)
    for cue in plan.get("cues") or []:
        add(
            source="hook_montage",
            file=str(cue.get("file") or ""),
            path=str(cue.get("path") or ""),
            beat="00-hook",
            context=str(cue.get("script_fragment") or ""),
            slot=str(cue.get("cue_index", "")),
            in_sec=float(cue.get("in_sec") or 0),
        )

    for beat_n, beat in (beat_map.get("beats") or {}).items():
        for pool in ("clips", "images", "generated"):
            for item in beat.get(pool) or []:
                path = str(item.get("path") or "")
                fname = Path(path).name if path else str(item.get("filename") or "")
                add(source=f"beat_map:{pool}", file=fname, path=path, beat=str(beat_n))

    return rows


def _resolve_path(project: DailySingleProject, row: dict[str, Any]) -> Path | None:
    raw = str(row.get("path") or "")
    if raw:
        p = Path(raw)
        if p.is_file():
            return p
    fname = str(row.get("file") or "")
    if not fname:
        return None
    assets = project.assets_dir
    for candidate in (
        project.root / "research" / "reference-videos" / "anthropic" / fname,
        project.root / "research" / "reference-videos" / "social" / fname,
        project.root / "research" / "reference-images" / "videos" / fname,
        project.root / "research" / "reference-images" / fname,
        assets / "generated" / fname,
        assets / "images" / fname,
        assets / "videos" / fname,
        assets / fname,
    ):
        if candidate.is_file():
            return candidate
    return None


def validate_asset_inventory(
    project: DailySingleProject,
    *,
    export_frames: bool = True,
    use_vision: bool | None = None,
) -> dict[str, Any]:
    """Enumerate every planned asset, export a reference frame, fail on banned hook/body slides."""
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    variant = str(beat_map.get("variant") or "")
    policy = str(beat_map.get("asset_policy") or "")
    trust_hook = variant == "trust-audit" and policy == "video-first-local"
    social_hook = variant == "social-comparison" and policy == "video-first-local"

    if use_vision is None:
        use_vision = vision_provider() != "off"

    issues: list[str] = []
    warnings: list[str] = []
    inventory_rows: list[dict[str, Any]] = []
    frame_dir = project.merge_dir / "qa" / "asset_frames"
    planned = _planned_assets(project)

    if trust_hook or social_hook:
        from praisonaippt.daily_single.hook_montage import attention_visual

        hook_script = project.segment_script("00-hook")
        script = hook_script.read_text(encoding="utf-8") if hook_script.is_file() else ""
        cues = [c for c in (build_hook_montage_plan(project).get("cues") or []) if c.get("ok")]
        att = attention_visual(project, cues, script=script)
        att_file = str(att.get("file") or "")
        if att_file in TRUST_AUDIT_ATTENTION_BANS:
            issues.append(
                f"Hook attention uses banned clip {att_file} — use launch or LinkedIn screen recordings"
            )

    hook_allow = TRUST_AUDIT_HOOK_MP4_ALLOW if trust_hook else (
        SOCIAL_COMPARISON_HOOK_MP4_ALLOW if social_hook else None
    )

    for row in planned:
        fname = str(row.get("file") or "")
        fn_lower = fname.lower()
        beat = str(row.get("beat") or "")
        source = str(row.get("source") or "")
        in_sec = float(row.get("in_sec") or 0)
        row_issues: list[str] = []
        row_warnings: list[str] = []

        if any(m in fn_lower for m in PROGRAMMATIC_HOOK_MARKERS):
            note = "programmatic storyboard slide — use real capture or gpt-image"
            if source == "hook_montage" or ((trust_hook or social_hook) and source.startswith("beat_map")):
                row_issues.append(note)
            else:
                row_warnings.append(note)
        if (trust_hook or social_hook) and source.startswith("beat_map") and fname in HOOK_SPECTACLE_BANS | {"fallback-notification.mp4"}:
            row_issues.append("banned spectacle or mislabelled clip in trust-audit beats")
        if source == "hook_montage":
            if fname in HOOK_SPECTACLE_BANS:
                row_issues.append("spectacle/off-topic scroll clip — not allowed in trust-audit hook")
            if fn_lower.endswith(".png") or fn_lower.endswith(".jpg"):
                row_issues.append("hook montage must use video clips only")
            if hook_allow and fn_lower.endswith(".mp4") and fname not in hook_allow:
                row_issues.append(
                    f"hook clip not on allowlist — allowed: {', '.join(sorted(hook_allow))}"
                )
            if trust_hook and fname == "demo-launch.mp4" and in_sec < 15.0:
                row_issues.append("demo-launch must skip spectacle intro (in_sec >= 15)")

        path = _resolve_path(project, row)
        frame_path: str | None = None
        generic_broll = False

        if not path:
            row_issues.append("missing file on disk")
        elif export_frames:
            at_sec = in_sec if path.suffix.lower() == ".mp4" and in_sec > 0 else None
            if at_sec is None and path.suffix.lower() == ".mp4":
                from praisonaippt.segment_video.media import ffprobe_duration

                dur = ffprobe_duration(path)
                at_sec = max(1.0, dur * 0.25)
            ref = reference_frame_for_asset(path, frame_dir, at_sec=at_sec)
            if ref and ref.is_file():
                frame_path = str(ref)
                if use_vision and source == "hook_montage":
                    spoken = str(row.get("context") or fname)
                    try:
                        vision = describe_frame(ref, spoken)
                    except Exception:
                        vision = None
                    if vision and (vision.get("generic_broll") or _GENERIC_PATTERNS.search(vision.get("description") or "")):
                        if not (social_hook and fn_lower.startswith("x-")):
                            generic_broll = True
                            row_issues.append(
                                f"frame looks like generic b-roll ({vision.get('description', '')[:80]})"
                            )

        if row_issues:
            for msg in row_issues:
                issues.append(f"{fname} [{source}, beat {beat}]: {msg}")
        if row_warnings:
            for msg in row_warnings:
                warnings.append(f"{fname} [{source}, beat {beat}]: {msg}")

        inventory_rows.append({
            **row,
            "resolved_path": str(path) if path else "",
            "frame_path": frame_path,
            "generic_broll": generic_broll,
            "ok": len(row_issues) == 0,
            "issues": row_issues,
            "warnings": row_warnings,
        })

    ok = len(issues) == 0
    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": ok,
        "assets_total": len(inventory_rows),
        "assets_pass": sum(1 for r in inventory_rows if r["ok"]),
        "assets_fail": sum(1 for r in inventory_rows if not r["ok"]),
        "frame_dir": str(frame_dir),
        "trust_audit_hook": trust_hook,
        "social_comparison_hook": social_hook,
        "vision": vision_provider() if use_vision else "off",
        "inventory": inventory_rows,
        "issues": issues,
        "warnings": warnings,
    }
    out = project.merge_dir / "asset_inventory_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
