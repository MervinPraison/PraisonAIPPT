"""Daily-single pipeline SDK — programmatic build and publish gate."""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.assemble import assemble
from praisonaippt.daily_single.bookends import run_bookends
from praisonaippt.daily_single.captions import build_all_captions
from praisonaippt.daily_single.display_sync import validate_display_sync
from praisonaippt.daily_single.env import load_env
from praisonaippt.daily_single.media_sync import run_sync_assets
from praisonaippt.daily_single.pipeline import (
    BUILD_PIPELINE,
    PUBLISH_GATE,
    PYTEST_MODULES,
    PipelineStep,
    pipeline_manifest,
)
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.scripts import write_beat_scripts
from praisonaippt.daily_single.sync_validation import run_sync_suite
from praisonaippt.daily_single.timeline import build_timeline
from praisonaippt.daily_single.validation import validate_all
from praisonaippt.daily_single.vo import synthesise_segments
from praisonaippt.segment_video.media import ffprobe_duration
from praisonaippt.video_qa.runner import run_suite


@dataclass
class StepResult:
    step_id: str
    ok: bool
    exit_code: int = 0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineReport:
    ok: bool
    steps: list[StepResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "steps": [
                {
                    "step_id": s.step_id,
                    "ok": s.ok,
                    "exit_code": s.exit_code,
                    "message": s.message,
                    "details": s.details,
                }
                for s in self.steps
            ],
        }


class DailySinglePipelineEngine:
    """SDK entry point for daily_single — mirrors ``segment_video.PipelineEngine``."""

    def __init__(self, project: DailySingleProject | str | Path):
        if not isinstance(project, DailySingleProject):
            project = DailySingleProject.from_root(project)
        self.project = project

    @staticmethod
    def manifest() -> dict[str, Any]:
        return pipeline_manifest()

    @staticmethod
    def build_steps() -> tuple[PipelineStep, ...]:
        return BUILD_PIPELINE

    @staticmethod
    def publish_gate_steps() -> tuple[PipelineStep, ...]:
        return PUBLISH_GATE

    def status(self) -> dict[str, Any]:
        p = self.project
        final = p.merge_dir / "final.mp4"
        with_audio = p.merge_dir / "final-with-audio.mp4"
        srt = p.merge_dir / "final.srt"
        out: dict[str, Any] = {
            "slug": p.slug,
            "root": str(p.root),
            "protocol_path": str(p.protocol_path),
            "pipeline_manifest": pipeline_manifest(),
            "outputs": {},
        }
        if final.is_file():
            out["outputs"]["final_mp4"] = {
                "path": str(final),
                "duration_sec": round(ffprobe_duration(final), 2),
            }
        if with_audio.is_file():
            out["outputs"]["final_with_audio"] = {
                "path": str(with_audio),
                "duration_sec": round(ffprobe_duration(with_audio), 2),
            }
        if srt.is_file():
            out["outputs"]["final_srt"] = str(srt)
        return out

    def run_qa(self, when: str, *, continue_on_fail: bool = False) -> PipelineReport:
        load_env()
        suite = run_suite(self.project, when=when, continue_on_fail=continue_on_fail)
        ok = bool(suite.ok)
        return PipelineReport(
            ok=ok,
            steps=[
                StepResult(
                    step_id=f"validate-qa-{when}",
                    ok=ok,
                    exit_code=0 if ok else 1,
                    message=f"{suite.summary.get('stages_passed', 0)}/{suite.summary.get('stages_run', 0)} stages",
                    details=suite.to_dict(),
                )
            ],
        )

    def _run_build_cmd(self, cmd: str, **kwargs: Any) -> StepResult:
        handlers = {
            "sync-assets": lambda: self._sync_assets(**kwargs),
            "write-scripts": lambda: self._write_scripts(),
            "synthesise-vo": lambda: self._synthesise_vo(**kwargs),
            "bookend-media": lambda: self._bookend_media(**kwargs),
            "record-canonical-scroll": lambda: self._record_scroll(**kwargs),
            "build-captions": lambda: self._build_captions(),
            "assemble-beats": lambda: self._assemble_beats(),
        }
        fn = handlers.get(cmd)
        if fn is None:
            return StepResult(cmd, False, 1, f"unknown build command: {cmd}")
        try:
            fn()
            return StepResult(cmd, True, 0, "OK")
        except Exception as exc:
            return StepResult(cmd, False, 1, str(exc))

    def _sync_assets(self, *, skip_hd: bool = False, crawl: bool = True) -> None:
        report = run_sync_assets(self.project, force_hd=not skip_hd, crawl=crawl)
        if not report["ok"]:
            raise RuntimeError("; ".join((report.get("inventory") or {}).get("issues") or ["sync failed"]))

    def _write_scripts(self) -> None:
        write_beat_scripts(self.project)

    def _synthesise_vo(self, *, segments: list[str] | None = None, skip_existing: bool = False) -> None:
        synthesise_segments(self.project, only=segments, skip_existing=skip_existing)
        from praisonaippt.daily_single.spoken_visual_gates import ensure_whisper_after_vo

        ensure_whisper_after_vo(self.project, force=not skip_existing)

    def _bookend_media(self, *, segments: list[str] | None = None, skip_existing: bool = False) -> None:
        from praisonaippt.daily_single.publish_quality_config import requires_heygen_bookends

        if not requires_heygen_bookends(self.project):
            return
        run_bookends(self.project, segments, skip_existing=skip_existing)

    def _record_scroll(self, **kwargs: Any) -> None:
        from praisonaippt.daily_single.canonical_scroll import record_canonical_scroll

        record_canonical_scroll(self.project, **kwargs)

    def _build_captions(self) -> None:
        build_all_captions(self.project)

    def _assemble_beats(self) -> None:
        assemble(self.project)
        build_timeline(self.project)

    def _run_gate(self, cmd: str, **kwargs: Any) -> StepResult:
        p = self.project
        if cmd == "validate-display":
            report = validate_display_sync(p)
            ok = bool(report["ok"])
            return StepResult(cmd, ok, 0 if ok else 1, f"{report['cues_pass']}/{report['cues_total']} cues")
        if cmd == "validate-spoken-visual":
            from praisonaippt.daily_single.spoken_visual_gates import run_spoken_visual_map

            ok, report = run_spoken_visual_map(p, use_vlm=True)
            return StepResult(cmd, ok, 0 if ok else 1, "spoken-visual sync")
        if cmd == "validate-sync":
            report = run_sync_suite(p, runs=int(kwargs.get("runs", 3)))
            ok = bool(report["ok"])
            return StepResult(cmd, ok, 0 if ok else 1, f"idempotent={report.get('idempotent')}")
        if cmd == "validate-all":
            ok, report = validate_all(p, refresh=True)
            return StepResult(cmd, ok, 0 if ok else 1, "validate-all")
        if cmd == "audit-visual":
            load_env()
            from praisonaippt.daily_single.visual_audit import run_visual_audit

            report = run_visual_audit(p, interval=5.0, use_vision=True, force=False)
            ok = bool(report["ok"])
            return StepResult(cmd, ok, 0 if ok else 1, f"{report['samples_pass']}/{report['samples_total']}")
        if cmd == "validate-hook-attention":
            from praisonaippt.daily_single.hook_attention_audit import run_hook_attention_audit

            report = run_hook_attention_audit(p, seconds=5)
            ok = bool(report.get("ok"))
            return StepResult(cmd, ok, 0 if ok else 1, "hook attention")
        if cmd == "validate-canonical-scroll":
            from praisonaippt.daily_single.canonical_scroll import scroll_video_path
            from praisonaippt.daily_single.page_capture_quality import validate_scroll_asset
            from praisonaippt.daily_single.publish_quality_config import beat_map_variant

            if beat_map_variant(p) in ("trust-audit", "social-comparison"):
                return StepResult(cmd, True, 0, "skipped — video-first variant")
            scroll = scroll_video_path(p)
            if not scroll:
                return StepResult(cmd, False, 1, "missing canonical-scroll.mp4")
            ok, _ = validate_scroll_asset(p, scroll)
            return StepResult(cmd, ok, 0 if ok else 1, scroll.name)
        if cmd == "validate-slide-quality":
            from praisonaippt.daily_single.slide_design_audit import validate_slide_design

            report = validate_slide_design(p)
            return StepResult(cmd, bool(report["ok"]), 0 if report["ok"] else 1, "slide quality")
        if cmd == "validate-asset-inventory":
            from praisonaippt.daily_single.asset_inventory_audit import validate_asset_inventory

            report = validate_asset_inventory(p, export_frames=True)
            ok = bool(report["ok"])
            msg = f"{report.get('assets_pass')}/{report.get('assets_total')} assets"
            return StepResult(cmd, ok, 0 if ok else 1, msg)
        if cmd == "validate-beat-map":
            from praisonaippt.daily_single.beat_map_audit import validate_beat_map_policy

            report = validate_beat_map_policy(p)
            ok = bool(report["ok"])
            msg = "; ".join((report.get("issues") or [])[:2]) or "beat-map policy OK"
            return StepResult(cmd, ok, 0 if ok else 1, msg)
        if cmd == "validate-engagement-assets":
            from praisonaippt.daily_single.engagement_audit import validate_engagement_assets

            report = validate_engagement_assets(p)
            return StepResult(cmd, bool(report["ok"]), 0 if report["ok"] else 1, "engagement")
        if cmd == "validate-viral-readiness":
            from praisonaippt.daily_single.viral_readiness import validate_viral_readiness

            report = validate_viral_readiness(p)
            return StepResult(cmd, bool(report["ok"]), 0 if report["ok"] else 1, "viral readiness")
        return StepResult(cmd, False, 1, f"unknown gate: {cmd}")

    def _run_pytest(self) -> StepResult:
        repo = Path(__file__).resolve().parents[2]
        cmd = [sys.executable, "-m", "pytest", *PYTEST_MODULES, "-q"]
        proc = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True)
        ok = proc.returncode == 0
        return StepResult(
            "pytest",
            ok,
            proc.returncode,
            (proc.stdout or proc.stderr or "").strip().splitlines()[-1] if ok else proc.stderr[:200],
        )

    def run_build(
        self,
        *,
        skip_optional: bool = True,
        stop_on_fail: bool = True,
        **kwargs: Any,
    ) -> PipelineReport:
        steps: list[StepResult] = []
        ok = True
        for step in BUILD_PIPELINE:
            if step.optional and skip_optional:
                continue
            if step.kind == "qa" and step.when:
                result = self.run_qa(step.when).steps[0]
                result.step_id = step.id
            elif step.kind == "build":
                cmd = step.cli.split()[0]
                result = self._run_build_cmd(cmd, **kwargs)
                result.step_id = step.id
            elif step.kind == "gate":
                cmd = step.cli.split()[0]
                result = self._run_gate(cmd, **kwargs)
                result.step_id = step.id
            else:
                continue
            steps.append(result)
            if not result.ok:
                ok = False
                if stop_on_fail:
                    break
        return PipelineReport(ok=ok, steps=steps)

    def run_publish_gate(
        self,
        *,
        assemble: bool = False,
        stop_on_fail: bool = True,
    ) -> PipelineReport:
        """Run V2–V19 publish matrix (Python port of run-publish-gate.sh)."""
        steps: list[StepResult] = []
        ok = True
        for step in PUBLISH_GATE:
            if step.id == "assemble-beats" and not assemble:
                continue
            if step.kind == "qa" and step.when:
                result = self.run_qa(step.when).steps[0]
                result.step_id = step.id
            elif step.kind == "build":
                cmd = step.cli.split()[0]
                result = self._run_build_cmd(cmd)
                result.step_id = step.id
            elif step.kind == "test":
                result = self._run_pytest()
                result.step_id = step.id
            elif step.kind == "gate":
                cmd = step.cli.split()[0]
                extra = {}
                if "runs" in step.cli:
                    extra["runs"] = 3
                result = self._run_gate(cmd, **extra)
                result.step_id = step.id
            else:
                continue
            steps.append(result)
            if not result.ok:
                ok = False
                if stop_on_fail:
                    break
        report_path = self.project.merge_dir / "pipeline_report.json"
        report = PipelineReport(ok=ok, steps=steps)
        report_path.write_text(
            __import__("json").dumps(report.to_dict(), indent=2),
            encoding="utf-8",
        )
        return report
