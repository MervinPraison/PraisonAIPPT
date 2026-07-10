#!/usr/bin/env python3
"""CLI for biblerevelation sermon article SDK.

Examples:
  python -m praisonaippt.sermon_article.cli --pack examples/sermon_packs/bic_pack2.yaml build
  python -m praisonaippt.sermon_article.cli --pack examples/sermon_packs/bic_pack2.yaml images --slug my-sermon
  python -m praisonaippt.sermon_article.cli --pack examples/sermon_packs/bic_pack2.yaml pipeline run --stages gap-audit,build,validate
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from praisonaippt.sermon_article.config import DEFAULT_PACK_DIR, SERMON_PACKS_DIR
from praisonaippt.sermon_article.engine import SermonArticleEngine
from praisonaippt.sermon_article.yaml_map import audit_pack_map


def _engine(pack: str) -> SermonArticleEngine:
    path = Path(pack).expanduser()
    if not path.is_absolute():
        candidate = SERMON_PACKS_DIR / pack
        if candidate.exists():
            path = candidate
    return SermonArticleEngine(path)


def cmd_gap_audit(args: argparse.Namespace) -> int:
    engine = _engine(args.pack)
    rows = []
    for job in engine.jobs(args.slug):
        gr = engine.gap_audit(job)
        rows.append(gr.to_dict())
        status = "OK" if gr.ok else "GAP"
        print(f"{status} {job.slug}: ratio={gr.ratio:.0%} missing_yaml={len(gr.yaml_missing)} themes={gr.missing_themes}")
    if args.json:
        print(json.dumps(rows, indent=2))
    return 0 if all(r["ok"] for r in rows) else 1


def cmd_build(args: argparse.Namespace) -> int:
    engine = _engine(args.pack)
    for job in engine.jobs(args.slug):
        path = engine.build(job)
        print(f"Built {path}")
    return 0


def cmd_structure_audit(args: argparse.Namespace) -> int:
    engine = _engine(args.pack)
    ok = True
    for job in engine.jobs(args.slug):
        sr = engine.structure_audit(job)
        print(f"{job.slug}: h2={sr.h2_count} tables={sr.table_count} max_para={sr.max_paragraph_chars} ok={sr.ok}")
        for e in sr.errors:
            print(f"  FAIL: {e}")
        if not sr.ok:
            ok = False
    return 0 if ok else 1


def cmd_validate(args: argparse.Namespace) -> int:
    engine = _engine(args.pack)
    ok = True
    for job in engine.jobs(args.slug):
        vr = engine.validate_job(job)
        print(f"{job.slug}: ratio={vr.ratio:.0%} ok={vr.ok}")
        if not vr.ok:
            ok = False
            for m in vr.yaml_missing[:5]:
                print(f"  {m}")
    return 0 if ok else 1


def cmd_images(args: argparse.Namespace) -> int:
    engine = _engine(args.pack)
    for job in engine.jobs(args.slug):
        path = engine.generate_image(job, force=args.force)
        print(f"Cover {job.slug}: {path}")
    return 0


def cmd_publish_create(args: argparse.Namespace) -> int:
    engine = _engine(args.pack)
    for job in engine.jobs(args.slug):
        pr = engine.publish_create(job)
        print(f"Created {job.slug}: {pr.url} HTTP {pr.http_status} post_id={pr.post_id}")
    return 0


def cmd_publish_update(args: argparse.Namespace) -> int:
    engine = _engine(args.pack)
    upload_cover = not args.content_only
    for job in engine.jobs(args.slug):
        pr = engine.publish_update(job, upload_cover=upload_cover)
        print(f"Updated {job.slug}: {pr.url} HTTP {pr.http_status} media={pr.media_id}")
    return 0


def cmd_pipeline_run(args: argparse.Namespace) -> int:
    engine = _engine(args.pack)
    report = engine.run(args.stages, slug=args.slug)
    print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.ok else 1


def cmd_manifest(args: argparse.Namespace) -> int:
    engine = _engine(args.pack)
    print(json.dumps(engine.manifest(), indent=2))
    return 0


def cmd_yaml_audit(args: argparse.Namespace) -> int:
    map_path = Path(args.map).expanduser() if args.map else DEFAULT_PACK_DIR / "sermon_video_map.json"
    report = Path(args.report).expanduser() if args.report else map_path.parent / "yaml_validation_report.json"
    rows = audit_pack_map(map_path, report_path=report)
    bad = 0
    for r in rows:
        print(f"\n{'='*60}")
        print(f"#{r['index']} {r['video_id']} → {r['yaml_file']}")
        print(f"Verdict: {r['verdict']} | refs {r['yaml_refs_matched']}/{r['yaml_refs_total']} ({r['ref_match_pct']}%)")
        if r.get("alternate_suggestion"):
            print(f"Alternate: {r['alternate_suggestion']}")
        if r["verdict"] in ("MISMATCH", "REVIEW", "WEAK"):
            bad += 1
    print(f"\nReport: {report}")
    if args.json:
        print(json.dumps(rows, indent=2))
    return 0 if bad == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Biblerevelation sermon article SDK")
    parser.add_argument("--pack", required=True, help="Pack protocol YAML (e.g. examples/sermon_packs/bic_pack2.yaml)")
    parser.add_argument("--slug", help="Limit to one sermon slug")
    sub = parser.add_subparsers(dest="command", required=True)

    p_gap = sub.add_parser("gap-audit", help="Transcript ↔ article gap analysis")
    p_gap.add_argument("--json", action="store_true")
    p_gap.set_defaults(func=cmd_gap_audit)

    p_build = sub.add_parser("build", help="Build Gutenberg HTML drafts")
    p_build.set_defaults(func=cmd_build)

    p_val = sub.add_parser("validate", help="Validate drafts")
    p_val.set_defaults(func=cmd_validate)

    p_struct = sub.add_parser("structure-audit", help="Structural quality gate")
    p_struct.set_defaults(func=cmd_structure_audit)

    p_img = sub.add_parser("images", help="Generate unique featured covers")
    p_img.add_argument("--force", action="store_true")
    p_img.set_defaults(func=cmd_images)

    p_pub = sub.add_parser("publish-update", help="Update live WordPress posts")
    p_pub.add_argument("--content-only", action="store_true", help="Skip featured image generation/upload")
    p_pub.set_defaults(func=cmd_publish_update)

    p_create = sub.add_parser("publish-create", help="Create new WordPress posts")
    p_create.set_defaults(func=cmd_publish_create)

    p_man = sub.add_parser("manifest", help="Print pack manifest")
    p_man.set_defaults(func=cmd_manifest)

    p_yaml = sub.add_parser("yaml-audit", help="Audit transcript ↔ YAML deck mapping")
    p_yaml.add_argument("--map", help="sermon_video_map.json path")
    p_yaml.add_argument("--report", help="Output report JSON path")
    p_yaml.add_argument("--json", action="store_true")
    p_yaml.set_defaults(func=cmd_yaml_audit)

    p_pipe = sub.add_parser("pipeline")
    pipe_sub = p_pipe.add_subparsers(dest="pipe_cmd", required=True)
    p_run = pipe_sub.add_parser("run", help="Run pipeline stages")
    p_run.add_argument("--stages", default="gap-audit,validate,structure-audit,images,publish-update")
    p_run.set_defaults(func=cmd_pipeline_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
