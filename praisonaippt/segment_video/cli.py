"""segment-video CLI — thin wrapper over PipelineEngine."""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from .engine import PipelineEngine
from .project import SegmentVideoProject


def _project(path: str | None) -> SegmentVideoProject:
    root = Path(path or ".").resolve()
    return SegmentVideoProject.from_path(root)


def cmd_status(args: argparse.Namespace) -> int:
    data = PipelineEngine(_project(args.project)).status()
    if args.json:
        print(json.dumps(data, indent=2))
        return 0
    print(f"project: {data.get('slug')} post_id={data.get('post_id')}")
    for seg in data.get("segments", []):
        c = seg["checks"]
        mark = "OK" if seg["ok"] else "PARTIAL"
        print(
            f"  [{mark}] {seg['dir']}: "
            + ", ".join(f"{k}={'Y' if v else 'n'}" for k, v in c.items())
        )
    if data.get("final_video"):
        fv = data["final_video"]
        print(f"  merge: {fv['path']} {fv['duration_sec']}s")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    return PipelineEngine(_project(args.project)).validate(strict=getattr(args, "strict", False))


def cmd_run(args: argparse.Namespace) -> int:
    engine = PipelineEngine(_project(args.project))
    if args.job:
        job = engine.run_job(
            args.stage,
            segments=args.segments,
            force=args.force,
            no_transitions=args.no_transitions,
        )
        if args.json:
            print(json.dumps(job, indent=2))
        return job.get("exit_code", 1)
    return engine.run(
        args.stage,
        segments=args.segments,
        force=args.force,
        no_transitions=args.no_transitions,
    )


def cmd_regenerate(args: argparse.Namespace) -> int:
    engine = PipelineEngine(_project(args.project))
    jobs = engine.regenerate_from(
        args.change,
        args.segment,
        force=not args.no_force,
        no_transitions=args.no_transitions,
    )
    if args.json:
        print(json.dumps(jobs, indent=2))
    return 0 if jobs and jobs[-1].get("exit_code") == 0 else 1


def cmd_validate_all(args: argparse.Namespace) -> int:
    from .stages.validate_all import run_validate_all

    project = _project(args.project)
    rc = run_validate_all(project, strict=args.strict)
    if args.json:
        report_path = project.root / "validation_report.json"
        if report_path.is_file():
            print(report_path.read_text(encoding="utf-8"))
    return rc


def cmd_studio(args: argparse.Namespace) -> int:
    from .studio.server import run_studio

    project = _project(args.project)
    protocol = project.load_protocol()
    studio_cfg = protocol.get("studio") or {}
    host = "127.0.0.1"
    if args.host and args.host != host:
        print(f"Studio only binds to {host} (ignoring --host {args.host})")
    port = args.port or int(studio_cfg.get("port", 8765))
    url = f"http://{host}:{port}"
    if not args.no_open:
        webbrowser.open(url)
    print(f"Segment Video Studio: {url}")
    run_studio(project, host=host, port=port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="segment-video")
    parser.add_argument("--project", "-p", default=".", help="project root (manifest.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status")
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_val = sub.add_parser("validate")
    p_val.add_argument("--strict", action="store_true", help="fail on any validator warning")
    p_val.set_defaults(func=cmd_validate)

    p_val_all = sub.add_parser("validate-all")
    p_val_all.add_argument("--strict", action="store_true")
    p_val_all.add_argument("--json", action="store_true")
    p_val_all.set_defaults(func=cmd_validate_all)

    p_run = sub.add_parser("run")
    p_run.add_argument("stage")
    p_run.add_argument("segments", nargs="*")
    p_run.add_argument("--force", action="store_true")
    p_run.add_argument("--no-transitions", action="store_true")
    p_run.add_argument("--job", action="store_true", help="track job in state.json")
    p_run.add_argument("--json", action="store_true")
    p_run.set_defaults(func=cmd_run)

    p_regen = sub.add_parser("regenerate")
    p_regen.add_argument("--change", required=True)
    p_regen.add_argument("--segment")
    p_regen.add_argument("--no-force", action="store_true")
    p_regen.add_argument("--no-transitions", action="store_true")
    p_regen.add_argument("--json", action="store_true")
    p_regen.set_defaults(func=cmd_regenerate)

    p_studio = sub.add_parser("studio")
    p_studio.add_argument("--host")
    p_studio.add_argument("--port", type=int)
    p_studio.add_argument("--no-open", action="store_true")
    p_studio.set_defaults(func=cmd_studio)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
