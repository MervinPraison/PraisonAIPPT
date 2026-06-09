"""Run project-local script stages via subprocess."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

from ..manifest import load_manifest, save_manifest
from ..project import SegmentVideoProject
from ..protocol import resolve_stage_id
from .align_cues import run_align_cues
from .audit_images import run_audit_images
from .build_timeline import run_build_timeline
from .catalogue_media import run_catalogue_media
from .merge import run_merge
from .validate_visual_stage import run_validate_sync, run_validate_visual
from .validate_all import run_validate_all
from .validate_display import run_validate_display
from .validate_hook import run_validate_hook
from .crawl_missing_assets import run_crawl_missing_assets
from .validate_assets import run_validate_assets
from .normalize_audio import run_normalize_audio

SCRIPT_STAGES: dict[str, str] = {
    "sync-media": "sync_media_assets.py",
    "validate-media": "validate_media.py",
    "media": "run_segment_media.py",
    "yaml": "build_segment_yaml.py",
    "scripts": "write_scripts.py",
}

SHELL_STAGES: dict[str, str] = {
    "build": "build_segment_mp4.sh",
    "fix-jpegs": "fix_slide_jpeg_paths.sh",
    "seed-golden": "seed_golden_slides.sh",
}


def _run_cmd(cmd: list[str], cwd: Path, log: Callable[[str], None]) -> tuple[int, list[str]]:
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert proc.stdout is not None
    lines: list[str] = []
    for line in proc.stdout:
        stripped = line.rstrip()
        lines.append(stripped)
        log(stripped)
    return proc.wait(), lines


def run_stage(
    project: SegmentVideoProject,
    stage_id: str,
    *,
    segments: list[str] | None = None,
    force: bool = False,
    no_transitions: bool = False,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    stage_id = resolve_stage_id(stage_id)
    scripts = project.scripts_dir

    SDK_STAGES = {
        "catalogue-media": run_catalogue_media,
        "align-cues": run_align_cues,
        "audit-images": run_audit_images,
        "validate-sync": run_validate_sync,
        "validate-visual": run_validate_visual,
        "validate-all": run_validate_all,
        "validate-hook": run_validate_hook,
        "validate-display": run_validate_display,
        "validate-assets": run_validate_assets,
        "crawl-missing-assets": run_crawl_missing_assets,
        "build-timeline": run_build_timeline,
        "normalize-audio": run_normalize_audio,
    }
    if stage_id in SDK_STAGES:
        fn = SDK_STAGES[stage_id]
        if stage_id == "normalize-audio":
            return fn(project, segments=segments, force=force, log=emit)
        if stage_id in ("align-cues", "validate-sync", "validate-visual", "build-timeline", "validate-all", "validate-hook", "validate-display", "crawl-missing-assets"):
            return fn(project, segments=segments, log=emit)
        if stage_id == "validate-assets":
            return fn(project, log=emit)
        return fn(project, log=emit)

    if stage_id == "merge":
        rc = run_merge(project, no_transitions=no_transitions, log=emit)
        if rc == 0:
            run_build_timeline(project, log=emit)
        return rc

    if stage_id == "publish":
        return _run_publish(project, log=emit)

    if stage_id in SCRIPT_STAGES:
        cmd = [sys.executable, str(scripts / SCRIPT_STAGES[stage_id])]
        protocol = project.load_protocol()
        st = next((s for s in protocol.get("stages", []) if s.get("id") == stage_id), {})
        if st.get("skip_existing") and not force and stage_id == "media":
            cmd.append("--skip-existing")
        if stage_id == "validate-media":
            cmd.append("--strict")
        if segments:
            cmd.extend(segments)
        return _run_cmd(cmd, scripts, emit)[0]

    if stage_id in SHELL_STAGES:
        cmd = ["zsh", str(scripts / SHELL_STAGES[stage_id])]
        if force and stage_id == "build":
            cmd.append("--force")
        if segments and stage_id == "build":
            cmd.extend(segments)
        cwd = project.root if stage_id == "build" else scripts
        return _run_cmd(cmd, cwd, emit)[0]

    emit(f"unknown stage: {stage_id}")
    return 1


def _run_publish(project: SegmentVideoProject, *, log: Callable[[str], None]) -> int:
    manifest = load_manifest(project.root)
    post_id = manifest.get("post_id")
    mp4 = project.root / "merge" / "final-roundup.mp4"
    if not post_id:
        log("publish: post_id missing in manifest")
        return 1
    if not mp4.is_file():
        log(f"publish: missing {mp4}")
        return 1

    cmd = [
        "praisonaiwp", "media", "upload", str(mp4),
        f"--post-id={post_id}", "--server", "default",
    ]
    log("publish: " + " ".join(cmd))
    rc, lines = _run_cmd(cmd, project.root, log)
    if rc != 0:
        return rc

    att_id = None
    for line in lines:
        m = re.search(r"Imported media with ID:\s*(\d+)", line)
        if m:
            att_id = m.group(1)
            break
    if not att_id:
        log("publish: could not parse attachment ID from upload output")
        return 1

    url_proc = subprocess.run(
        ["praisonaiwp", "media", "url", att_id, "--server", "default"],
        capture_output=True,
        text=True,
        cwd=str(project.root),
    )
    att_url = ""
    for line in (url_proc.stdout or "").splitlines():
        if line.startswith("http"):
            att_url = line.strip()
            break
    if not att_url:
        log("publish: could not resolve attachment URL")
        return 1

    prev = (manifest.get("final_video") or {})
    old_id = str(prev.get("wordpress_attachment_id") or "")
    old_url = prev.get("wordpress_url") or ""

    if old_id and old_id != att_id:
        subprocess.run(
            ["bash", "-c", f"yes | praisonaiwp update {post_id} '{old_id}' '{att_id}' --server default"],
            cwd=str(project.root),
        )
    if old_url and old_url != att_url:
        subprocess.run(
            ["bash", "-c", f"yes | praisonaiwp update {post_id} '{old_url}' '{att_url}' --server default"],
            cwd=str(project.root),
        )
    elif not old_url:
        subprocess.run(
            ["bash", "-c", f"yes | praisonaiwp update {post_id} 'final-roundup' '{att_url.split('/')[-1]}' --server default"],
            cwd=str(project.root),
        )

    manifest.setdefault("final_video", {})
    manifest["final_video"]["wordpress_attachment_id"] = int(att_id)
    manifest["final_video"]["wordpress_url"] = att_url
    save_manifest(project.root, manifest)
    log(f"publish: attachment {att_id} → {att_url}")
    return 0
