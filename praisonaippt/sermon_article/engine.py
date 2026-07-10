"""Sermon article SDK engine — programmatic pipeline runner."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import builders, gap, images, publish, validate
from .config import DEFAULT_AGENT_DIR
from .pack import job_by_slug, load_pack
from .pipeline import parse_stages
from .protocol import GapReport, PublishResult, SermonJob, SermonPack, ValidationReport
from .structure_audit import audit_structure


@dataclass
class StepResult:
    step_id: str
    ok: bool
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineReport:
    ok: bool
    steps: list[StepResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "steps": [{"step_id": s.step_id, "ok": s.ok, "message": s.message, "details": s.details} for s in self.steps]}


class SermonArticleEngine:
    """SDK entry point for biblerevelation sermon article workflows."""

    def __init__(self, pack_yaml: Path, agent_dir: Path = DEFAULT_AGENT_DIR):
        self.pack_yaml = Path(pack_yaml).expanduser()
        self.pack = load_pack(self.pack_yaml)
        self.agent_dir = agent_dir
        self.agent_dir.mkdir(parents=True, exist_ok=True)

    def jobs(self, slug: str | None = None) -> list[SermonJob]:
        if slug:
            return [job_by_slug(self.pack, slug)]
        return self.pack.active_jobs()

    def _html_path(self, job: SermonJob) -> Path:
        agent = job.agent_html_path(self.agent_dir)
        if agent.exists():
            return agent
        draft = job.draft_html_path(self.pack.draft_dir)
        if draft.exists():
            return draft
        return agent

    def gap_audit(self, job: SermonJob) -> GapReport:
        html_path = self._html_path(job)
        return gap.gap_report(job, self.pack, html_path if html_path.exists() else None)

    def build(self, job: SermonJob) -> Path:
        agent = job.agent_html_path(self.agent_dir)
        out = job.draft_html_path(self.pack.draft_dir)

        if job.builder == "manual":
            if not agent.exists():
                raise FileNotFoundError(
                    f"Manual build requires {agent} — rewrite from transcript + YAML first"
                )
            shutil.copy(agent, out)
            return out

        html = builders.build_article(job, self.pack)
        out.write_text(html, encoding="utf-8")
        shutil.copy(out, agent)
        return out

    def validate_job(self, job: SermonJob, html_path: Path | None = None) -> ValidationReport:
        path = html_path or self._html_path(job)
        return validate.validate(job, self.pack, path)

    def structure_audit(self, job: SermonJob, html_path: Path | None = None):
        path = html_path or self._html_path(job)
        return audit_structure(job, self.pack, path, agent_dir=self.agent_dir)

    def generate_image(self, job: SermonJob, force: bool = False) -> Path:
        return images.generate_cover(job, self.pack, force=force)

    def publish_update(self, job: SermonJob, html_path: Path | None = None, *, upload_cover: bool = True) -> PublishResult:
        path = html_path or self._html_path(job)
        vr = self.validate_job(job, path)
        sr = self.structure_audit(job, path)
        if not vr.ok:
            raise RuntimeError(f"Validate failed for {job.slug}: {vr.errors or vr.yaml_missing}")
        if not sr.ok:
            raise RuntimeError(f"Structure audit failed for {job.slug}: {sr.errors}")
        return publish.update_post(job, self.pack, path, upload_cover=upload_cover)

    def publish_create(self, job: SermonJob, html_path: Path | None = None) -> PublishResult:
        path = html_path or self._html_path(job)
        vr = self.validate_job(job, path)
        sr = self.structure_audit(job, path)
        if not vr.ok:
            raise RuntimeError(f"Validate failed for {job.slug}: {vr.errors or vr.yaml_missing}")
        if not sr.ok:
            raise RuntimeError(f"Structure audit failed for {job.slug}: {sr.errors}")
        return publish.create_post(job, self.pack, path)

    def run(self, stages: str, slug: str | None = None) -> EngineReport:
        steps = parse_stages(stages)
        report = EngineReport(ok=True)
        for job in self.jobs(slug):
            for step in steps:
                try:
                    result = self._run_step(step.id, job)
                    report.steps.append(result)
                    if not result.ok:
                        report.ok = False
                except Exception as exc:
                    report.ok = False
                    report.steps.append(StepResult(step.id, False, str(exc), {"slug": job.slug}))
        return report

    def _run_step(self, step_id: str, job: SermonJob) -> StepResult:
        if step_id == "gap-audit":
            gr = self.gap_audit(job)
            return StepResult(step_id, gr.ok, f"ratio={gr.ratio:.0%}", gr.to_dict())
        if step_id == "build":
            path = self.build(job)
            return StepResult(step_id, True, str(path))
        if step_id == "validate":
            vr = self.validate_job(job)
            return StepResult(step_id, vr.ok, f"ratio={vr.ratio:.0%}", {"missing": vr.yaml_missing})
        if step_id == "structure-audit":
            sr = self.structure_audit(job)
            return StepResult(step_id, sr.ok, f"h2={sr.h2_count} tables={sr.table_count}", sr.to_dict())
        if step_id == "images":
            path = self.generate_image(job)
            return StepResult(step_id, True, str(path))
        if step_id == "publish-update":
            pr = self.publish_update(job)
            ok = pr.http_status == 200
            return StepResult(step_id, ok, pr.url, pr.__dict__)
        if step_id == "publish-create":
            pr = self.publish_create(job)
            ok = pr.http_status == 200
            return StepResult(step_id, ok, pr.url, pr.__dict__)
        raise ValueError(f"Unknown step: {step_id}")

    def manifest(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack.pack_id,
            "pack_dir": str(self.pack.pack_dir),
            "jobs": [j.to_dict() for j in self.pack.jobs],
        }
