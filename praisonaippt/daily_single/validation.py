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


def validate_all(project: DailySingleProject) -> tuple[bool, dict]:
    issues: list[str] = []
    report: dict = {"validators": {}, "passed": True}
    final = project.merge_dir / "final.mp4"
    narr = project.merge_dir / "narration.mp3"
    srt = project.merge_dir / "final.srt"

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
    table = next((g for g in b7.get("generated", []) if "beat7" in g.get("filename", "")), None)
    if not table or not Path(table["path"]).is_file():
        issues.append("beat_coverage: Beat 7 table PNG missing")
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
    report["passed"] = len(issues) == 0
    report["issues"] = issues
    (project.root / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report["passed"], report
