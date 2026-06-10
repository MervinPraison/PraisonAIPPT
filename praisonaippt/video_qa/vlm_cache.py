"""Per-frame VLM result cache for idempotent QA runs."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def cache_dir(project_qa_dir: Path) -> Path:
    path = project_qa_dir / "vlm_cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def frame_key(frame_bytes: bytes, model: str, prompt: str) -> str:
    blob = hashlib.sha256(frame_bytes).hexdigest()[:16]
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
    return f"{blob}_{model}_{prompt_hash}"


def cache_path(qa_dir: Path, key: str) -> Path:
    return cache_dir(qa_dir) / f"{key}.json"


def load_cached(qa_dir: Path, key: str) -> dict[str, Any] | None:
    path = cache_path(qa_dir, key)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_cached(qa_dir: Path, key: str, payload: dict[str, Any]) -> None:
    path = cache_path(qa_dir, key)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def describe_frame_cached(
    qa_dir: Path,
    frame_path: Path,
    spoken: str,
    *,
    model: str | None = None,
) -> dict[str, Any]:
    """Wrap vision_describe.describe_frame with disk cache."""
    from praisonaippt.vision_describe import describe_frame, vision_model

    model = model or vision_model()
    prompt = spoken[:500]
    frame_bytes = frame_path.read_bytes()
    key = frame_key(frame_bytes, model, prompt)
    cached = load_cached(qa_dir, key)
    if cached is not None:
        cached["cache_hit"] = True
        return cached

    if os.environ.get("PRAISONAIPPT_QA_OFFLINE", "").lower() in ("1", "true", "yes"):
        return {"description": "", "topics": [], "generic_broll": False, "offline": True}

    try:
        result = describe_frame(frame_path, spoken) or {
            "description": "",
            "topics": [],
            "generic_broll": False,
        }
    except Exception as exc:
        result = {"description": "", "topics": [], "generic_broll": False, "error": str(exc)[:120]}
    result["cache_hit"] = False
    save_cached(qa_dir, key, result)
    return result
