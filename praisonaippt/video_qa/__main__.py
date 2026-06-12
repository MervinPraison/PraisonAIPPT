"""CLI for modular video QA stages."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from praisonaippt.daily_single.env import load_env
from praisonaippt.video_qa.adapters import load_project
from praisonaippt.video_qa.registry import list_stages
from praisonaippt.video_qa.runner import run_stage, run_suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="video-qa", description="Modular video QA stages")
    parser.add_argument("--project", "-p", default=".", help="Project root (manifest.json)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List registered QA stages")

    run_p = sub.add_parser("run", help="Run QA stage(s)")
    run_p.add_argument("stage", nargs="?", help="Stage id (e.g. s04-knowledge); omit with --when")
    run_p.add_argument(
        "--when",
        choices=[
            "pre_build",
            "post_vo",
            "post_bookends",
            "pre_assemble",
            "post_assemble",
            "post_captions",
            "post_build",
            "all",
        ],
        default="all",
    )
    run_p.add_argument("--phase", help="Sub-phase for s01-assets or s06-coverage")
    run_p.add_argument("--stages", nargs="*", dest="stage_list", help="Explicit stage ids for suite run")
    run_p.add_argument("--fail-fast", action="store_true", help="Stop on first stage exception")

    args = parser.parse_args(argv)
    load_env()
    project = load_project(args.project)

    if args.cmd == "list":
        for sid in list_stages():
            print(sid)
        return 0

    if args.cmd == "run":
        if args.stage:
            report = run_stage(
                project,
                args.stage,
                phase=args.phase,
                continue_on_fail=not args.fail_fast,
            )
            print(f"{'PASS' if report.ok else 'FAIL'}: {report.id}" + (" (skipped)" if report.skipped else ""))
            for check in report.checks:
                if not check.ok:
                    print(f"  [{check.severity}] {check.message}")
            return 0 if report.ok or report.skipped else 1

        suite = run_suite(
            project,
            when=args.when,
            stages=args.stage_list or None,
            continue_on_fail=not args.fail_fast,
        )
        s = suite.summary or {}
        print(
            f"{'PASS' if suite.ok else 'FAIL'}: "
            f"{s.get('stages_passed', 0)}/{s.get('stages_run', 0)} stages "
            f"(when={args.when})"
        )
        for stage in suite.stages:
            if not stage.ok and not stage.skipped:
                print(f"  FAIL {stage.id}")
                for check in stage.checks[:3]:
                    if not check.ok:
                        print(f"    {check.message}")
        return 0 if suite.ok else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
