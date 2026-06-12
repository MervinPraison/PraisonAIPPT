"""Robust spoken↔caption↔visual validation for daily_single."""
from __future__ import annotations

import json
from typing import Any

from praisonaippt.daily_single.captions import split_caption_cues
from praisonaippt.daily_single.display_sync import MIN_ALIGNMENT, parse_srt, validate_display_sync
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.daily_single.hook_validation import validate_hook_montage
from praisonaippt.daily_single.visual_audit import validate_visual_audit
from praisonaippt.daily_single.spoken_visual_sync import validate_spoken_visual_sync
from praisonaippt.daily_single.viral_readiness import validate_viral_readiness
from praisonaippt.daily_single.youtube_quality import validate_youtube_quality

BORDERLINE_MAX = 0.45
HOOK_BRIDGE = "let's get started"


def expected_script_cues(project: DailySingleProject) -> list[str]:
    """Locked script sentences in merge order — one per SRT cue."""
    cues: list[str] = []
    for _label, seg_dir, _beat in SEGMENT_ORDER:
        script = project.segment_script(seg_dir)
        if script.is_file():
            cues.extend(split_caption_cues(script.read_text(encoding="utf-8")))
    return cues


def validate_caption_script_lock(project: DailySingleProject) -> tuple[bool, list[str]]:
    """SRT cue text must match segment scripts exactly (not Whisper)."""
    srt_path = project.merge_dir / "final.srt"
    if not srt_path.is_file():
        return False, [f"missing {srt_path} — run build-captions"]
    srt_cues = parse_srt(srt_path)
    expected = expected_script_cues(project)
    spoken = [c["text"] for c in srt_cues]
    issues: list[str] = []
    if len(spoken) != len(expected):
        issues.append(f"cue count srt={len(spoken)} script={len(expected)}")
    for i, (got, want) in enumerate(zip(spoken, expected), 1):
        if got != want:
            issues.append(f"cue {i} text mismatch")
    if len(spoken) > len(expected):
        for i in range(len(expected) + 1, len(spoken) + 1):
            issues.append(f"cue {i} extra in srt")
    return len(issues) == 0, issues


def validate_hook_structure(cue_map: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    """YouTube hook: attention → overview → Let's get started."""
    issues: list[str] = []
    if len(cue_map) < 3:
        return False, ["fewer than 3 cues for hook structure"]
    bridge = cue_map[2]["spoken"].strip().lower()
    if not bridge.startswith(HOOK_BRIDGE):
        issues.append(f"cue 3 must start with 'Let's get started' (got: {cue_map[2]['spoken'][:50]})")
    if HOOK_BRIDGE in cue_map[0]["spoken"].lower():
        issues.append("cue 1 must not contain 'Let's get started'")
    if len(cue_map[0]["spoken"].split()) < 5:
        issues.append("cue 1 hook too short (<5 words)")
    if len(cue_map[1]["spoken"].split()) < 8:
        issues.append("cue 2 overview too short (<8 words)")
    return len(issues) == 0, issues


def borderline_cues(cue_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cues that pass threshold but sit in the warn band."""
    return [
        row for row in cue_map
        if row.get("ok") and MIN_ALIGNMENT <= float(row.get("alignment", 0)) <= BORDERLINE_MAX
    ]


def _cue_map_signature(cue_map: list[dict[str, Any]]) -> list[tuple]:
    return [
        (r["cue"], r["spoken"], r["file"], r["alignment"], r["ok"])
        for r in cue_map
    ]


def run_sync_suite(project: DailySingleProject, *, runs: int = 3) -> dict[str, Any]:
    """Run spoken↔image mapping + script lock + hook checks `runs` times; assert idempotency."""
    run_rows: list[dict[str, Any]] = []
    signatures: list[list[tuple]] = []
    last_yt_checks: dict[str, Any] = {}

    last_montage_report: dict[str, Any] = {}
    last_spoken_visual: dict[str, Any] = {}
    visual_ok, visual_report = validate_visual_audit(project)
    spoken_visual = validate_spoken_visual_sync(project)
    last_spoken_visual = spoken_visual
    viral_report = validate_viral_readiness(project)

    for n in range(1, runs + 1):
        display = validate_display_sync(project)
        lock_ok, lock_issues = validate_caption_script_lock(project)
        hook_ok, hook_issues = validate_hook_structure(display["cue_map"])
        yt_ok, yt_checks = validate_youtube_quality(project, display["cue_map"])
        last_yt_checks = yt_checks
        borderline = borderline_cues(display["cue_map"])
        image_ok = display.get("ok", False)
        yt_issues = [
            f"{name}: {msg}"
            for name, block in yt_checks.items()
            for msg in block.get("issues", [])
        ]
        montage_ok, montage_report = validate_hook_montage(project)
        last_montage_report = montage_report
        montage_issues = montage_report.get("issues") or []
        visual_issues = visual_report.get("issues") or []
        spoken_ok = spoken_visual.get("ok", False)
        spoken_issues = spoken_visual.get("issues") or []
        ok = lock_ok and hook_ok and image_ok and yt_ok and montage_ok and visual_ok and spoken_ok

        sig = _cue_map_signature(display["cue_map"])
        signatures.append(sig)
        run_rows.append({
            "run": n,
            "ok": ok,
            "cues_total": display["cues_total"],
            "cues_pass": display["cues_pass"],
            "cues_fail": display["cues_fail"],
            "borderline_count": len(borderline),
            "caption_script_lock": lock_ok,
            "hook_structure": hook_ok,
            "image_mapping": image_ok,
            "youtube_quality": yt_ok,
            "hook_montage": montage_ok,
            "visual_audit": visual_ok,
            "spoken_visual": spoken_ok,
            "issues": lock_issues + hook_issues + yt_issues + montage_issues + visual_issues + spoken_issues + (
                [] if image_ok else [f"{display['cues_fail']} cues below {MIN_ALIGNMENT}"]
            ),
        })

    idempotent = all(s == signatures[0] for s in signatures[1:]) if signatures else True
    final = run_rows[-1] if run_rows else {}
    last_cue_map = validate_display_sync(project)["cue_map"] if run_rows else []
    report: dict[str, Any] = {
        "schema_version": 1,
        "runs": runs,
        "idempotent": idempotent,
        "ok": idempotent and all(r["ok"] for r in run_rows),
        "min_alignment": MIN_ALIGNMENT,
        "borderline_max": BORDERLINE_MAX,
        "youtube_quality": last_yt_checks,
        "hook_montage": last_montage_report,
        "spoken_visual_sync": {
            "ok": spoken_visual.get("ok"),
            "montage_pass": spoken_visual.get("montage_fragments_pass"),
            "montage_total": spoken_visual.get("montage_fragments_total"),
            "windows_pass": spoken_visual.get("windows_pass"),
            "windows_total": spoken_visual.get("windows_total"),
            "issues": (spoken_visual.get("issues") or [])[:10],
        },
        "viral_readiness": {
            "ok": viral_report.get("ok"),
            "proof_cue_count": viral_report.get("proof_cue_count"),
            "comparison_beats": viral_report.get("comparison_beats"),
            "issues": (viral_report.get("issues") or [])[:10],
        },
        "visual_audit": {
            "ok": visual_ok,
            "samples_total": visual_report.get("samples_total"),
            "samples_pass": visual_report.get("samples_pass"),
            "generic_broll_count": visual_report.get("generic_broll_count"),
            "issues": visual_issues[:10],
        },
        "run_results": run_rows,
        "borderline_cues": [
            {"cue": r["cue"], "alignment": r["alignment"], "spoken": r["spoken"][:80], "file": r["file"]}
            for r in borderline_cues(last_cue_map)
        ],
        "summary": {
            "cues_total": final.get("cues_total"),
            "pass_rate": round(final.get("cues_pass", 0) / max(1, final.get("cues_total", 1)), 3),
            "borderline_count": final.get("borderline_count"),
            "caption_script_lock": final.get("caption_script_lock"),
            "hook_structure": final.get("hook_structure"),
            "image_mapping": final.get("image_mapping"),
            "youtube_quality": final.get("youtube_quality"),
            "hook_montage": final.get("hook_montage"),
            "visual_audit": final.get("visual_audit"),
            "spoken_visual": final.get("spoken_visual"),
        },
    }
    out = project.merge_dir / "sync_validation_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
