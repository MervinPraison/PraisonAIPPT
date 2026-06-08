from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any


def _state_path(state_dir: Path) -> Path:
    return state_dir / "state.json"


def load_state(state_dir: Path) -> dict:
    path = _state_path(state_dir)
    if not path.is_file():
        return {"jobs": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state_dir: Path, state: dict) -> None:
    _state_path(state_dir).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def create_job(state_dir: Path, *, stage: str, segments: list[str] | None = None) -> dict:
    state = load_state(state_dir)
    job = {
        "id": uuid.uuid4().hex[:12],
        "stage": stage,
        "segments": segments or [],
        "status": "pending",
        "log": [],
        "created_at": time.time(),
        "finished_at": None,
    }
    state.setdefault("jobs", []).insert(0, job)
    state["jobs"] = state["jobs"][:50]
    save_state(state_dir, state)
    return job


def update_job(state_dir: Path, job_id: str, **fields: Any) -> dict | None:
    state = load_state(state_dir)
    for job in state.get("jobs", []):
        if job.get("id") == job_id:
            job.update(fields)
            save_state(state_dir, state)
            return job
    return None


def append_job_log(state_dir: Path, job_id: str, line: str) -> None:
    state = load_state(state_dir)
    for job in state.get("jobs", []):
        if job.get("id") == job_id:
            job.setdefault("log", []).append(line.rstrip())
            save_state(state_dir, state)
            return


def get_job(state_dir: Path, job_id: str) -> dict | None:
    for job in load_state(state_dir).get("jobs", []):
        if job.get("id") == job_id:
            return job
    return None
