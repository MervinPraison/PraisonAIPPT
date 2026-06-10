"""CLI for daily_single pipeline stages."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from praisonaippt.daily_single.assemble import assemble
from praisonaippt.daily_single.env import load_env
from praisonaippt.daily_single.bookends import run_bookends
from praisonaippt.daily_single.captions import build_all_captions
from praisonaippt.daily_single.display_sync import validate_display_sync
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import DEFAULT_PROTOCOL
from praisonaippt.daily_single.scripts import write_beat_scripts
from praisonaippt.daily_single.timeline import build_timeline
from praisonaippt.daily_single.sync_validation import run_sync_suite
from praisonaippt.daily_single.media_sync import run_sync_assets, validate_media_inventory
from praisonaippt.daily_single.validation import validate_all
from praisonaippt.daily_single.visual_audit import run_visual_audit, validate_visual_audit
from praisonaippt.daily_single.vo import synthesise_segments


def _project(path: str) -> DailySingleProject:
    return DailySingleProject.from_root(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="daily-single", description="Daily single news video pipeline")
    parser.add_argument("--project", "-p", default=".", help="Project root (manifest.json)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("write-scripts", help="Write beat segment scripts from video-script.md")
    vo_p = sub.add_parser("synthesise-vo", help="ElevenLabs TTS for all segments + merge")
    vo_p.add_argument("--segments", nargs="*", help="Only these segment dirs (e.g. 00-hook)")
    vo_p.add_argument("--skip-existing", action="store_true")
    bk_p = sub.add_parser("bookend-media", help="ElevenLabs + HeyGen for hook/outro")
    bk_p.add_argument("segments", nargs="*", help="Segment dirs (default 00-hook 99-outro)")
    bk_p.add_argument("--skip-existing", action="store_true")
    bk_p.add_argument("--heygen-only", action="store_true", help="Skip TTS; only HeyGen if missing")
    sub.add_parser("assemble-beats", help="VO-driven ffmpeg assembly → merge/final.mp4")
    sub.add_parser("build-captions", help="Script-aligned SRT (not raw Whisper text)")
    sub.add_parser("build-timeline", help="Write merge/timeline.json")
    scroll_p = sub.add_parser(
        "record-canonical-scroll",
        help="Record scrolling capture of canonical news page for hook attention",
    )
    scroll_p.add_argument("--url", help="Override canonical URL from handoff")
    scroll_p.add_argument("--duration", type=float, default=5.0, help="Clip length (seconds)")
    scroll_p.add_argument(
        "--mode",
        choices=("auto", "scroll", "zoom"),
        default="auto",
        help="Scroll down tall pages; zoom in when short (default auto)",
    )
    sub.add_parser("validate-display", help="Map SRT cues to visuals; write display_sync_report.json")
    sub.add_parser(
        "validate-spoken-visual",
        help="Check narration matches slides/images on screen → spoken_visual_sync_report.json",
    )
    sync_p = sub.add_parser(
        "validate-sync",
        help="Robust sync test: script lock + hook + image mapping (default 3 idempotent runs)",
    )
    sync_p.add_argument("--runs", type=int, default=3, help="Repeat validation N times (default 3)")
    audit_p = sub.add_parser(
        "audit-visual",
        help="Sample final.mp4 every N seconds; pixel + topic audit → visual_audit_report.json",
    )
    audit_p.add_argument("--interval", type=float, default=5.0, help="Seconds between samples (default 5)")
    audit_p.add_argument("--force", action="store_true", help="Re-export frames even if report exists")
    audit_p.add_argument("--no-vision", action="store_true", help="Skip optional vision LLM descriptions")
    sub.add_parser("validate-visual-audit", help="Gate on merge/visual_audit_report.json")
    hook_att_p = sub.add_parser(
        "validate-hook-attention",
        help="Per-second frames for hook attention (first 5s vs canonical-scroll)",
    )
    hook_att_p.add_argument("--seconds", type=int, default=5)
    sub.add_parser(
        "validate-canonical-scroll",
        help="Gate canonical-scroll.mp4 — reject browser error pages before assemble",
    )
    sub.add_parser("validate-all", help="Full validation gate (tools, output, sync, display, visual audit)")
    sync_assets_p = sub.add_parser(
        "sync-assets",
        help="Crawl canonical page images + download HD motion clips from handoff",
    )
    sync_assets_p.add_argument("--skip-hd", action="store_true", help="Do not upgrade low-resolution videos")
    sync_assets_p.add_argument("--no-crawl", action="store_true", help="Skip canonical image crawl")
    qa_p = sub.add_parser("validate-qa", help="Run modular video QA stages (merge/qa/)")
    qa_p.add_argument("stage", nargs="?", help="Single stage id (e.g. s04-knowledge)")
    qa_p.add_argument("--when", choices=["pre_build", "pre_assemble", "post_vo", "post_build", "all"], default="all")
    qa_p.add_argument("--phase", help="Sub-phase for s01-assets or s06-coverage")
    sub.add_parser("emit-protocol", help="Write default protocol.json template")

    args = parser.parse_args(argv)
    project = _project(args.project)

    if args.cmd == "write-scripts":
        write_beat_scripts(project)
        return 0
    if args.cmd == "synthesise-vo":
        synthesise_segments(project, only=args.segments, skip_existing=args.skip_existing)
        return 0
    if args.cmd == "bookend-media":
        run_bookends(
            project,
            list(args.segments) or None,
            skip_existing=args.skip_existing,
            heygen_only=args.heygen_only,
        )
        return 0
    if args.cmd == "assemble-beats":
        assemble(project)
        build_timeline(project)
        return 0
    if args.cmd == "build-captions":
        build_all_captions(project)
        return 0
    if args.cmd == "build-timeline":
        build_timeline(project)
        return 0
    if args.cmd == "record-canonical-scroll":
        from praisonaippt.daily_single.canonical_scroll import record_canonical_scroll

        record_canonical_scroll(
            project,
            url=getattr(args, "url", None),
            duration=float(getattr(args, "duration", 5.0)),
            mode=str(getattr(args, "mode", "auto")),
        )
        return 0
    if args.cmd == "validate-display":
        report = validate_display_sync(project)
        if report["ok"]:
            print(f"PASS: {report['cues_pass']}/{report['cues_total']} cues aligned")
            return 0
        print(f"FAIL: {report['cues_fail']}/{report['cues_total']} cues below {report['min_alignment']}")
        for row in report["cue_map"]:
            if not row["ok"]:
                print(f"  cue {row['cue']} [{row['start_sec']:.1f}s] score={row['alignment']}: {row['spoken'][:60]}… → {row['file']}")
        return 1
    if args.cmd == "validate-spoken-visual":
        from praisonaippt.daily_single.spoken_visual_sync import validate_spoken_visual_sync

        report = validate_spoken_visual_sync(project)
        print(
            f"{'PASS' if report['ok'] else 'FAIL'}: "
            f"montage {report['montage_fragments_pass']}/{report['montage_fragments_total']}, "
            f"windows {report['windows_pass']}/{report['windows_total']}"
        )
        if not report["ok"]:
            for issue in report.get("issues") or []:
                print(f"  {issue}")
        return 0 if report["ok"] else 1
    if args.cmd == "validate-sync":
        report = run_sync_suite(project, runs=max(1, args.runs))
        s = report.get("summary") or {}
        print(
            f"Runs {report['runs']}: idempotent={report['idempotent']} "
            f"lock={s.get('caption_script_lock')} hook={s.get('hook_structure')} "
            f"image={s.get('image_mapping')} youtube={s.get('youtube_quality')} "
            f"montage={s.get('hook_montage')} visual={s.get('visual_audit')} "
            f"spoken={s.get('spoken_visual')} borderline={s.get('borderline_count')}"
        )
        if report["ok"]:
            print(f"PASS: {s.get('cues_total')} cues, {report['runs']} identical runs")
            return 0
        for row in report["run_results"]:
            if not row["ok"]:
                print(f"  run {row['run']}: {', '.join(row['issues'][:5])}")
        return 1
    if args.cmd == "audit-visual":
        load_env()
        report = run_visual_audit(
            project,
            interval=max(1.0, args.interval),
            use_vision=not args.no_vision,
            force=args.force,
        )
        print(
            f"{'PASS' if report['ok'] else 'FAIL'}: "
            f"{report['samples_pass']}/{report['samples_total']} samples "
            f"(generic_broll={report.get('generic_broll_count', 0)}, "
            f"vision={report.get('vision_model', 'off')} "
            f"n={report.get('vision_samples', 0)})"
        )
        if not report["ok"]:
            for f in (report.get("failures") or [])[:8]:
                print(f"  t={f['t_sec']:.1f}s {f['planned_file']}: {', '.join(f['issues'])}")
        return 0 if report["ok"] else 1
    if args.cmd == "validate-visual-audit":
        ok, report = validate_visual_audit(project)
        if ok:
            print(f"PASS: {report['samples_pass']}/{report['samples_total']} visual samples")
            return 0
        print(f"FAIL: {report.get('samples_fail', '?')} samples")
        for issue in (report.get("issues") or [])[:10]:
            print(f"  {issue}")
        return 1
    if args.cmd == "validate-hook-attention":
        from praisonaippt.daily_single.hook_attention_audit import run_hook_attention_audit

        report = run_hook_attention_audit(project, seconds=int(getattr(args, "seconds", 5)))
        ok = bool(report.get("ok"))
        print(
            f"{'PASS' if ok else 'FAIL'}: {report.get('samples_pass', 0)}/"
            f"{report.get('samples_total', 0)} second-frames, motion={report.get('motion_ok')} → "
            f"{report.get('frames_dir')}"
        )
        if not ok:
            for s in report.get("samples") or []:
                if not s.get("ok"):
                    print(f"  t={s['t_sec']:.0f}s pixel={s.get('pixel_sim')} {s.get('issues')}")
        return 0 if ok else 1
    if args.cmd == "validate-canonical-scroll":
        from praisonaippt.daily_single.canonical_scroll import scroll_video_path
        from praisonaippt.daily_single.page_capture_quality import validate_scroll_asset

        scroll = scroll_video_path(project)
        if not scroll:
            print(f"FAIL: missing assets/videos/canonical-scroll.mp4 — run record-canonical-scroll")
            return 1
        ok, details = validate_scroll_asset(project, scroll)
        print(f"{'PASS' if ok else 'FAIL'}: {scroll.name} ({details.get('duration_sec')}s)")
        if not ok:
            for issue in details.get("issues") or []:
                print(f"  {issue}")
        return 0 if ok else 1
    if args.cmd == "sync-assets":
        report = run_sync_assets(project, force_hd=not args.skip_hd, crawl=not args.no_crawl)
        inv = report.get("inventory") or {}
        for line in (report.get("videos") or {}).get("logs") or []:
            print(line)
        if report["ok"]:
            print(f"PASS: {len(inv.get('images') or [])} images, {len(inv.get('videos') or [])} videos HD")
            return 0
        for issue in inv.get("issues") or []:
            print(f"  {issue}")
        return 1
    if args.cmd == "validate-all":
        ok, report = validate_all(project)
        if ok:
            print("PASS")
            return 0
        print("FAIL:", "; ".join(report.get("issues", [])))
        return 1
    if args.cmd == "validate-qa":
        from praisonaippt.video_qa.runner import run_stage, run_suite

        load_env()
        if args.stage:
            report = run_stage(project, args.stage, phase=getattr(args, "phase", None))
            print(f"{'PASS' if report.ok else 'FAIL'}: {report.id}")
            for check in report.checks:
                if not check.ok:
                    print(f"  [{check.severity}] {check.message}")
            return 0 if report.ok or report.skipped else 1
        suite = run_suite(project, when=args.when)
        s = suite.summary or {}
        print(
            f"{'PASS' if suite.ok else 'FAIL'}: "
            f"{s.get('stages_passed', 0)}/{s.get('stages_run', 0)} stages"
        )
        return 0 if suite.ok else 1
    if args.cmd == "emit-protocol":
        out = project.root / "scripts" / "config" / "protocol.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(DEFAULT_PROTOCOL, indent=2), encoding="utf-8")
        print(f"Wrote {out}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
