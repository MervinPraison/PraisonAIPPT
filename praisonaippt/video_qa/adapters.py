"""Project adapters for video QA."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.video_qa.config import DEFAULT_VIDEO_QA_PROTOCOL
from praisonaippt.video_qa.degradation import resolve_final_mp4


def load_project(root: Path | str) -> DailySingleProject:
    return DailySingleProject.from_root(root)


def load_protocol(project: DailySingleProject) -> dict[str, Any]:
    from praisonaippt.daily_single.protocol import DEFAULT_PROTOCOL

    path = project.protocol_path
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = dict(DEFAULT_PROTOCOL)
    if "video_qa" not in data:
        data["video_qa"] = dict(DEFAULT_VIDEO_QA_PROTOCOL)
    return data


def qa_dir(project: DailySingleProject) -> Path:
    path = project.merge_dir / "qa"
    path.mkdir(parents=True, exist_ok=True)
    return path


def stage_report_path(project: DailySingleProject, stage_id: str, *, phase: str | None = None) -> Path:
    safe = stage_id.replace("-", "_")
    if phase:
        safe = f"{safe}_{phase}"
    return qa_dir(project) / f"{safe}_report.json"


def write_stage_report(
    project: DailySingleProject,
    stage_id: str,
    report: dict[str, Any],
    *,
    phase: str | None = None,
) -> Path:
    out = stage_report_path(project, stage_id, phase=phase)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out


def write_summary(project: DailySingleProject, suite: dict[str, Any]) -> Path:
    out = qa_dir(project) / "summary.json"
    out.write_text(json.dumps(suite, indent=2), encoding="utf-8")
    return out


def mirror_legacy_report(
    project: DailySingleProject,
    stage_id: str,
    legacy_path: Path,
) -> None:
    """Record legacy report path in merge/qa/legacy_links.json (keyed by filename)."""
    if not legacy_path.is_file():
        return
    links_path = qa_dir(project) / "legacy_links.json"
    links: dict[str, str] = {}
    if links_path.is_file():
        try:
            links = json.loads(links_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            links = {}
    rel = str(legacy_path.relative_to(project.root))
    links[legacy_path.name] = rel
    links[f"{stage_id}:{legacy_path.name}"] = rel
    links_path.write_text(json.dumps(links, indent=2), encoding="utf-8")


def export_vlm_timeline(project: DailySingleProject) -> Path:
    """Merge s02 source timeline + visual audit into merge/qa/vlm_timeline.json."""
    qa = qa_dir(project)
    out = qa / "vlm_timeline.json"
    payload: dict[str, Any] = {"schema_version": 1, "sources": []}

    s02 = qa / "s02_source_vlm_timeline.json"
    if s02.is_file():
        try:
            payload["sources"].append({"kind": "source_clips", "path": str(s02.relative_to(project.root))})
        except ValueError:
            payload["sources"].append({"kind": "source_clips", "path": str(s02)})

    va = project.merge_dir / "visual_audit_report.json"
    if va.is_file():
        try:
            va_data = json.loads(va.read_text(encoding="utf-8"))
            payload["final_composite"] = {
                "samples_total": va_data.get("samples_total"),
                "samples_pass": va_data.get("samples_pass"),
                "interval_sec": va_data.get("interval_sec"),
            }
        except (OSError, json.JSONDecodeError):
            pass

    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out
