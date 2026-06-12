"""Protocol validators for daily_single output."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.media_sync import validate_media_inventory


def _ffprobe_dur(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True,
    )
    return float(out.strip())


def validate_all(project: DailySingleProject, *, refresh: bool = False) -> tuple[bool, dict]:
    issues: list[str] = []
    report: dict = {"validators": {}, "passed": True}
    final = project.merge_dir / "final.mp4"
    if not final.is_file():
        final = project.merge_dir / "final-with-audio.mp4"
    narr = project.merge_dir / "narration.mp3"
    srt = project.merge_dir / "final.srt"

    if refresh and final.is_file() and srt.is_file():
        from praisonaippt.daily_single.spoken_visual_gates import refresh_publish_validators

        fresh_ok, fresh = refresh_publish_validators(project)
        report["refresh"] = fresh
        if not fresh_ok:
            for key, block in fresh.items():
                if isinstance(block, dict) and not block.get("ok", True):
                    issues.append(f"refresh/{key}: failed live re-check")

    for tool in ("ffprobe", "ffmpeg", "praisonaippt"):
        if not shutil.which(tool):
            issues.append(f"tools: missing {tool}")
    report["validators"]["tools"] = not any("tools:" in i for i in issues)

    if not final.is_file():
        issues.append("final_output: missing merge/final.mp4")
    else:
        dur = _ffprobe_dur(final)
        if dur < 280 or dur > 540:
            issues.append(f"final_output: duration {dur:.0f}s outside 280-540s")
        res = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", str(final)],
            text=True,
        ).strip()
        if res != "1920,1080":
            issues.append(f"final_output: resolution {res}")
        audio = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", str(final)],
            text=True,
        ).strip()
        if not audio:
            issues.append("final_output: no audio track")
    report["validators"]["final_output"] = not any("final_output" in i for i in issues)

    bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    for b in range(1, 11):
        if str(b) not in bm.get("beats", {}):
            issues.append(f"beat_coverage: missing beat {b}")
    b7 = bm.get("beats", {}).get("7", {})
    has_b7_visual = any(
        Path(item.get("path", "")).is_file()
        for key in ("generated", "images", "clips")
        for item in (b7.get(key) or [])
    )
    if not has_b7_visual:
        issues.append("beat_coverage: Beat 7 missing clips/images")
    report["validators"]["beat_coverage"] = not any("beat_coverage" in i for i in issues)

    if not narr.is_file():
        issues.append("audio_loudness: missing merge/narration.mp3")
    else:
        sr = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=sample_rate", "-of", "default=noprint_wrappers=1:nokey=1", str(narr)],
            text=True,
        ).strip()
        if sr != "44100":
            issues.append(f"audio_loudness: narration sample_rate {sr} != 44100")
    hook_hg = project.segments_dir / "00-hook" / "heygen.mp4"
    outro_hg = project.segments_dir / "99-outro" / "heygen.mp4"
    from praisonaippt.daily_single.publish_quality_config import beat_map_variant, requires_heygen_bookends

    variant = beat_map_variant(project)
    video_first = False
    try:
        bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
        video_first = str(bm.get("asset_policy") or "") == "video-first-local"
    except (OSError, json.JSONDecodeError):
        pass
    skip_heygen = not requires_heygen_bookends(project)
    if not skip_heygen:
        if not hook_hg.is_file():
            issues.append("heygen: missing hook heygen.mp4")
        outro_hg = project.segments_dir / "99-outro" / "heygen.mp4"
        if not outro_hg.is_file():
            issues.append("heygen: missing outro heygen.mp4")
    if not srt.is_file():
        issues.append("captions: missing merge/final.srt")

    media_ok, media_report = validate_media_inventory(project)
    report["validators"]["media_inventory"] = media_ok
    report["media_inventory"] = media_report
    if not media_ok:
        for issue in media_report.get("issues") or []:
            issues.append(f"media: {issue}")

    report["validators"]["sync_validation"] = False
    report["validators"]["display_sync"] = False
    report["validators"]["visual_audit"] = False
    report["validators"]["spoken_visual"] = False
    report["validators"]["canonical_capture"] = False
    report["validators"]["hook_attention"] = False
    report["validators"]["hook_framing"] = False
    report["validators"]["slide_design"] = False
    report["validators"]["engagement"] = False
    report["validators"]["viral_readiness"] = False
    sv_path = project.merge_dir / "sync_validation_report.json"
    va_path = project.merge_dir / "visual_audit_report.json"
    if sv_path.is_file():
        sv = json.loads(sv_path.read_text(encoding="utf-8"))
        report["validators"]["sync_validation"] = sv.get("ok", False)
        if not sv.get("ok"):
            issues.append("sync_validation: failed — run validate-sync")
    else:
        issues.append("sync_validation: missing merge/sync_validation_report.json — run validate-sync")
    ds_path = project.merge_dir / "display_sync_report.json"
    if ds_path.is_file():
        ds = json.loads(ds_path.read_text(encoding="utf-8"))
        report["validators"]["display_sync"] = ds.get("ok", False)
        if not ds.get("ok"):
            issues.append(f"display_sync: {ds.get('cues_fail', '?')} cues below alignment threshold")
    else:
        issues.append("display_sync: missing merge/display_sync_report.json — run validate-display")
    if va_path.is_file():
        va = json.loads(va_path.read_text(encoding="utf-8"))
        report["validators"]["visual_audit"] = va.get("ok", False)
        if not va.get("ok"):
            issues.append(
                f"visual_audit: {va.get('samples_fail', '?')} samples failed — run audit-visual"
            )
    else:
        issues.append("visual_audit: missing merge/visual_audit_report.json — run audit-visual")
    sv_path = project.merge_dir / "spoken_visual_sync_report.json"
    wv_path = project.merge_dir / "word_visual_sync_report.json"
    if sv_path.is_file():
        sv = json.loads(sv_path.read_text(encoding="utf-8"))
        report["validators"]["spoken_visual"] = sv.get("ok", False)
        if not sv.get("ok"):
            issues.append(
                f"spoken_visual: {sv.get('windows_fail', '?')} window(s), "
                f"{sv.get('montage_fragments_fail', '?')} montage fragment(s) — run validate-spoken-visual"
            )
        if sv.get("word_visual_ok") is False:
            wv = sv.get("word_visual") or {}
            if not wv.get("deferred") and not wv.get("skipped"):
                report["validators"]["word_visual"] = False
                issues.append(
                    f"word_visual: {wv.get('samples_fail', '?')} sample(s) — Whisper/VLM mismatch"
                )
        elif wv_path.is_file():
            wv = json.loads(wv_path.read_text(encoding="utf-8"))
            report["validators"]["word_visual"] = wv.get("ok", False)
            if not wv.get("ok"):
                issues.append(
                    f"word_visual: {wv.get('samples_fail', '?')} sample(s) — run validate-spoken-visual"
                )
    else:
        issues.append(
            "spoken_visual: missing merge/spoken_visual_sync_report.json — run validate-spoken-visual"
        )
    from praisonaippt.daily_single.canonical_scroll import scroll_video_path
    from praisonaippt.daily_single.page_capture_quality import validate_scroll_asset

    scroll = scroll_video_path(project)
    skip_scroll = video_first and variant in ("social-comparison", "trust-audit")
    if scroll and not skip_scroll:
        cap_ok, cap_details = validate_scroll_asset(project, scroll)
        report["validators"]["canonical_capture"] = cap_ok
        if not cap_ok:
            issues.append(
                "canonical_capture: scroll clip shows error page — run record-canonical-scroll"
            )
    cap_path = project.merge_dir / "qa" / "canonical_capture" / "capture_report.json"
    framing_path = project.merge_dir / "qa" / "canonical_capture" / "framing_report.json"
    if framing_path.is_file():
        fr = json.loads(framing_path.read_text(encoding="utf-8"))
        report["validators"]["hook_framing"] = fr.get("ok", False)
        if not fr.get("ok"):
            issues.append("hook_framing: failed — inspect merge/qa/canonical_capture/framing-diagram.png")
    elif cap_path.is_file():
        cap = json.loads(cap_path.read_text(encoding="utf-8"))
        framing = cap.get("framing") or {}
        if framing:
            report["validators"]["hook_framing"] = cap.get("ok", False)
    if cap_path.is_file():
        cap = json.loads(cap_path.read_text(encoding="utf-8"))
        if not cap.get("ok"):
            report["validators"]["canonical_capture"] = False
            issues.append("canonical_capture: capture_report ok=false")
    ha_path = project.merge_dir / "qa" / "hook_attention_audit.json"
    if ha_path.is_file():
        ha = json.loads(ha_path.read_text(encoding="utf-8"))
        report["validators"]["hook_attention"] = ha.get("ok", False)
        if not ha.get("ok"):
            issues.append("hook_attention: failed — run validate-hook-attention after assemble")
    elif scroll and not skip_scroll:
        issues.append("hook_attention: missing hook_attention_audit.json — run validate-hook-attention")
    if skip_scroll:
        report["validators"]["canonical_capture"] = True
        report["validators"]["hook_framing"] = True
    for key, path_name, label in (
        ("slide_design", "slide_design_report.json", "validate-slide-quality"),
        ("asset_inventory", "asset_inventory_report.json", "validate-asset-inventory"),
        ("beat_map_policy", "beat_map_policy_report.json", "validate-beat-map"),
        ("engagement", "engagement_report.json", "validate-engagement-assets"),
        ("viral_readiness", "viral_readiness_report.json", "validate-viral-readiness"),
    ):
        p = project.merge_dir / path_name
        if p.is_file():
            data = json.loads(p.read_text(encoding="utf-8"))
            report["validators"][key] = data.get("ok", False)
            if not data.get("ok"):
                issues.append(f"{key}: failed — run {label}")
        else:
            issues.append(f"{key}: missing merge/{path_name} — run {label}")
    report["passed"] = len(issues) == 0
    report["issues"] = issues
    (project.root / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report["passed"], report
