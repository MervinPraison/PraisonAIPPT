"""HeyGen bookend media (hook/outro) — skips existing when requested."""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

from praisonaippt.daily_single.env import load_env, require_keys
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.tts import synthesise
from praisonaippt.segment_video.media import ffprobe_duration

HEYGEN_UPLOAD = "https://upload.heygen.com/v1/asset"
HEYGEN_API = "https://api.heygen.com"
POLL_SEC = 30
MAX_POLLS = 100


def _api_json(method: str, url: str, headers: dict, body: bytes | None = None) -> dict:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def _heygen_pipeline(mp3: Path, heygen: Path, avatar: str, key_hg: str) -> None:
    body = mp3.read_bytes()
    headers = {"X-Api-Key": key_hg, "Content-Type": "audio/mpeg", "Accept": "application/json"}
    data = _api_json("POST", HEYGEN_UPLOAD, headers, body)
    asset_id = data.get("data", {}).get("id") or ""
    if not asset_id:
        raise RuntimeError(f"HeyGen upload failed: {data}")
    gen_body = {
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": avatar, "avatar_style": "normal"},
            "voice": {"type": "audio", "audio_asset_id": asset_id},
            "background": {"type": "color", "value": "#008000"},
        }],
        "dimension": {"width": 1280, "height": 720},
    }
    headers = {"X-Api-Key": key_hg, "Content-Type": "application/json", "Accept": "application/json"}
    data = _api_json("POST", f"{HEYGEN_API}/v2/video/generate", headers, json.dumps(gen_body).encode())
    vid = data.get("data", {}).get("video_id") or ""
    if not vid:
        raise RuntimeError(f"HeyGen generate failed: {data}")
    for _ in range(MAX_POLLS):
        q = urllib.parse.urlencode({"video_id": vid})
        data = _api_json("GET", f"{HEYGEN_API}/v1/video_status.get?{q}", headers)
        payload = data.get("data", {})
        status = (payload.get("status") or "").lower()
        if status == "completed":
            vurl = payload.get("video_url") or ""
            if not vurl:
                raise RuntimeError("HeyGen completed but no video_url")
            req = urllib.request.Request(vurl)
            with urllib.request.urlopen(req, timeout=600) as resp:
                heygen.write_bytes(resp.read())
            return
        if status == "failed":
            raise RuntimeError(f"HeyGen failed: {payload}")
        time.sleep(POLL_SEC)
    raise RuntimeError("HeyGen poll timeout")


def run_bookend(
    project: DailySingleProject,
    seg_dir: str,
    *,
    skip_existing: bool = False,
    heygen_only: bool = False,
) -> None:
    require_keys("ELEVEN_API_KEY", "HEYGEN_API_KEY")
    load_env()
    avatar = os.environ.get("AVATAR_ID")
    key_hg = os.environ["HEYGEN_API_KEY"]
    seg_path = project.segments_dir / seg_dir
    script = (seg_path / "script.md").read_text(encoding="utf-8").strip()
    mp3 = seg_path / "narration.mp3"
    heygen = seg_path / "heygen.mp4"

    if skip_existing and mp3.is_file() and heygen.is_file():
        print(f"skip {seg_dir}")
        return

    if not (skip_existing and mp3.is_file()) and not heygen_only:
        print(f"TTS {seg_dir}...")
        synthesise(script, mp3)
        print(f"  mp3 {ffprobe_duration(mp3):.1f}s")

    if not (skip_existing and heygen.is_file()):
        print(f"HeyGen {seg_dir}...")
        _heygen_pipeline(mp3, heygen, avatar, key_hg)
        print(f"  heygen {ffprobe_duration(heygen):.1f}s")

    ts = seg_path / "timestamps.json"
    if not skip_existing or not ts.is_file():
        try:
            subprocess.run(
                ["praisonaippt", "transcribe", "-i", str(mp3), "-o", str(ts)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            dur = ffprobe_duration(mp3)
            ts.write_text(
                json.dumps({"segments": [{"start": 0.0, "end": dur, "text": script}]}, indent=2),
                encoding="utf-8",
            )


def run_bookends(
    project: DailySingleProject,
    segments: list[str] | None = None,
    *,
    skip_existing: bool = False,
    heygen_only: bool = False,
) -> None:
    for seg in segments or ["00-hook", "99-outro"]:
        run_bookend(project, seg, skip_existing=skip_existing, heygen_only=heygen_only)
