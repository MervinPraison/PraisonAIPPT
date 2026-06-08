from __future__ import annotations

import shutil
import subprocess
import sys
import threading
import time
from typing import Callable

from .manifest import load_manifest
from .media import ffprobe_duration
from .project import SegmentVideoProject
from .protocol import REGENERATE_CHAINS, resolve_stage_id, validate_deps
from .state import append_job_log, create_job, update_job
from .stages.runner import run_stage


class PipelineEngine:
    def __init__(self, project: SegmentVideoProject):
        self.project = project

    def status(self) -> dict:
        manifest = self.project.load_manifest()
        segments = [self.project.segment_status(d) for d in self.project.segment_dirs()]
        final = self.project.root / "merge" / "final-roundup.mp4"
        out = {
            "slug": manifest.get("megapost_slug"),
            "post_id": manifest.get("post_id"),
            "pipeline_status": manifest.get("pipeline_status"),
            "segments": segments,
            "final_video": None,
        }
        if final.is_file():
            out["final_video"] = {
                "path": str(final.relative_to(self.project.root)),
                "duration_sec": round(ffprobe_duration(final), 2),
            }
        return out

    def validate(self, *, strict: bool = False) -> int:
        from .validation.suite import run_validation_suite, write_validation_report

        suite = run_validation_suite(self.project, strict=strict)
        out = write_validation_report(self.project, suite)
        summary = suite.to_dict()["summary"]
        print(
            f"validation {'OK' if suite.ok else 'FAILED'} → {out.name} "
            f"({summary.get('validators_passed')}/{summary.get('validators_run')} validators)"
        )
        if not suite.ok:
            for vid in summary.get("failed_required") or []:
                print(f"  required failed: {vid}")
        return 0 if suite.ok else 1

    def run(
        self,
        stage_id: str,
        *,
        segments: list[str] | None = None,
        force: bool = False,
        no_transitions: bool = False,
        job_id: str | None = None,
    ) -> int:
        stage_id = resolve_stage_id(stage_id)
        protocol = self.project.load_protocol()
        for err in validate_deps(protocol, stage_id):
            raise ValueError(err)

        def log(line: str) -> None:
            if job_id:
                append_job_log(self.project.state_dir, job_id, line)
            print(line)

        return run_stage(
            self.project,
            stage_id,
            segments=segments,
            force=force,
            no_transitions=no_transitions,
            log=log,
        )

    def run_job(
        self,
        stage_id: str,
        *,
        segments: list[str] | None = None,
        force: bool = False,
        no_transitions: bool = False,
    ) -> dict:
        job = create_job(self.project.state_dir, stage=stage_id, segments=segments or [])
        update_job(self.project.state_dir, job["id"], status="running")
        try:
            rc = self.run(
                stage_id,
                segments=segments,
                force=force,
                no_transitions=no_transitions,
                job_id=job["id"],
            )
            status = "done" if rc == 0 else "error"
        except Exception as exc:
            append_job_log(self.project.state_dir, job["id"], str(exc))
            rc = 1
            status = "error"
        update_job(
            self.project.state_dir,
            job["id"],
            status=status,
            exit_code=rc,
            finished_at=time.time(),
        )
        return update_job(self.project.state_dir, job["id"]) or job

    def run_job_async(
        self,
        stage_id: str,
        *,
        segments: list[str] | None = None,
        force: bool = False,
        no_transitions: bool = False,
    ) -> dict:
        job = create_job(
            self.project.state_dir,
            stage=resolve_stage_id(stage_id),
            segments=segments or [],
        )
        update_job(self.project.state_dir, job["id"], status="running")

        def worker() -> None:
            try:
                rc = self.run(
                    stage_id,
                    segments=segments,
                    force=force,
                    no_transitions=no_transitions,
                    job_id=job["id"],
                )
                status = "done" if rc == 0 else "error"
            except Exception as exc:
                append_job_log(self.project.state_dir, job["id"], str(exc))
                rc = 1
                status = "error"
            update_job(
                self.project.state_dir,
                job["id"],
                status=status,
                exit_code=rc,
                finished_at=time.time(),
            )

        threading.Thread(target=worker, daemon=True).start()
        return job

    def regenerate_from_async(
        self,
        change_type: str,
        segment_dir: str | None = None,
        *,
        force: bool = True,
        no_transitions: bool = False,
    ) -> dict:
        chain = REGENERATE_CHAINS.get(change_type)
        if not chain:
            raise ValueError(f"unknown change_type: {change_type}")
        job = create_job(
            self.project.state_dir,
            stage=f"regenerate:{change_type}",
            segments=[segment_dir] if segment_dir else [],
        )
        update_job(self.project.state_dir, job["id"], status="running")

        def worker() -> None:
            segs = [segment_dir] if segment_dir else None
            rc = 0
            try:
                for stage_id in chain:
                    append_job_log(self.project.state_dir, job["id"], f"--- {stage_id} ---")
                    scope = segs if stage_id not in (
                        "merge", "sync-media", "validate-media", "publish",
                        "fix-jpegs", "seed-golden", "catalogue-media",
                        "build-timeline",
                    ) else None
                    rc = self.run(
                        stage_id,
                        segments=scope,
                        force=force,
                        no_transitions=no_transitions,
                        job_id=job["id"],
                    )
                    if rc != 0:
                        break
            except Exception as exc:
                append_job_log(self.project.state_dir, job["id"], str(exc))
                rc = 1
            update_job(
                self.project.state_dir,
                job["id"],
                status="done" if rc == 0 else "error",
                exit_code=rc,
                finished_at=time.time(),
            )

        threading.Thread(target=worker, daemon=True).start()
        return job

    def regenerate_from(
        self,
        change_type: str,
        segment_dir: str | None = None,
        *,
        force: bool = True,
        no_transitions: bool = False,
    ) -> list[dict]:
        chain = REGENERATE_CHAINS.get(change_type)
        if not chain:
            raise ValueError(f"unknown change_type: {change_type}")
        jobs = []
        segs = [segment_dir] if segment_dir else None
        for stage_id in chain:
            scope_segments = segs if stage_id not in (
                "merge", "sync-media", "validate-media", "publish",
                "catalogue-media", "fix-jpegs", "seed-golden", "build-timeline",
            ) else None
            jobs.append(
                self.run_job(
                    stage_id,
                    segments=scope_segments,
                    force=force,
                    no_transitions=no_transitions,
                )
            )
            if jobs[-1].get("exit_code", 1) != 0:
                break
        return jobs
