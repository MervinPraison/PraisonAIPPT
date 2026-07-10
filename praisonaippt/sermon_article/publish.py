"""Publish and update biblerevelation.org posts via praisonaiwp."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .config import SSH_KEY, WP_ROOT, WP_SERVER, WP_SSH
from .images import cover_path, generate_cover
from .protocol import PublishResult, SermonJob, SermonPack
from .validate import validate


def _bash(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True)


def update_post(job: SermonJob, pack: SermonPack, html_path: Path, *, upload_cover: bool = True) -> PublishResult:
    if not job.post_id:
        raise ValueError(f"post_id required for update: {job.slug}")

    val = validate(job, pack, html_path)
    html_esc = html_path.read_text(encoding="utf-8").replace("'", "'\\''")

    _bash(
        f"praisonaiwp update {job.post_id} --server {WP_SERVER} "
        f"--no-block-conversion --post-content \"$(cat '{html_path}')\""
    )
    if job.excerpt:
        exc = job.excerpt.replace("'", "'\\''")
        _bash(f"praisonaiwp update {job.post_id} --server {WP_SERVER} --post-excerpt '{exc}'")
    if job.categories:
        _bash(f"praisonaiwp category set {job.post_id} --server {WP_SERVER} --category '{job.categories}'")

    media_id = None
    if upload_cover:
        cover = cover_path(pack, job.slug)
        if cover.exists():
            pass
        else:
            try:
                cover = generate_cover(job, pack)
            except (subprocess.CalledProcessError, OSError):
                cover = None
        if cover and cover.exists():
            up = _bash(
                f"praisonaiwp media upload '{cover}' --server {WP_SERVER} "
                f"--post-id {job.post_id} --title '{job.slug} cover' "
                f"--alt '{job.excerpt or job.title}'"
            )
            out = up.stdout + up.stderr
            m = (
                re.search(r"(?:Media ID:|Imported media with ID:)\s*(\d+)", out)
                or re.search(r"id[=: ](\d+)", out)
            )
            if m:
                media_id = int(m.group(1))
                _bash(f"praisonaiwp update {job.post_id} --server {WP_SERVER} "
                      f"--meta '{{\"_thumbnail_id\":\"{media_id}\"}}'")

    url_proc = subprocess.run(
        ["curl", "-sI", f"https://biblerevelation.org/?p={job.post_id}"],
        capture_output=True, text=True,
    )
    loc = [ln for ln in url_proc.stdout.splitlines() if ln.lower().startswith("location:")]
    url = loc[-1].split(":", 1)[1].strip() if loc else f"https://biblerevelation.org/?p={job.post_id}"
    http_proc = subprocess.run(["curl", "-sL", "-o", "/dev/null", "-w", "%{http_code}", url], capture_output=True, text=True)

    return PublishResult(
        slug=job.slug,
        post_id=job.post_id,
        url=url,
        http_status=int(http_proc.stdout or 0),
        media_id=media_id,
        ratio=val.ratio,
    )


def create_post(job: SermonJob, pack: SermonPack, html_path: Path) -> PublishResult:
    val = validate(job, pack, html_path)
    title_esc = job.title.replace("'", "'\\''")
    out = _bash(
        f"praisonaiwp create '{title_esc}' --server {WP_SERVER} --status publish "
        f"--category '{job.categories}' --no-block-conversion "
        f"--content \"$(cat '{html_path}')\""
    )
    text = out.stdout + out.stderr
    m = re.search(r"Created post ID: (\d+)", text)
    if not m:
        raise RuntimeError(f"Could not parse post ID: {text}")
    job.post_id = int(m.group(1))

    subprocess.run(
        ["ssh", "-i", str(SSH_KEY), WP_SSH,
         f"cd {WP_ROOT} && wp post update {job.post_id} --post_name='{job.slug}' --allow-root"],
        check=True,
    )
    return update_post(job, pack, html_path)
