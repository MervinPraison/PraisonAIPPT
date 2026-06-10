"""ElevenLabs TTS with optional chunking."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from praisonaippt.daily_single.env import load_env, require_keys
from praisonaippt.segment_video.script_text import narration_text_for_tts

ELEVEN_MODEL = "eleven_multilingual_v2"
CHUNK_SIZE = 3500


def _tts_chunk(text: str, out_mp3: Path, voice: str, key: str) -> None:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{urllib.parse.quote(voice)}"
    payload = json.dumps({"text": text, "model_id": ELEVEN_MODEL}).encode()
    headers = {
        "xi-api-key": key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json; charset=utf-8",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        out_mp3.write_bytes(resp.read())


def _concat_mp3(parts: list[Path], dest: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in parts:
            f.write(f"file '{p.resolve()}'\n")
        lst = f.name
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", str(dest)],
        check=True,
        capture_output=True,
    )


def synthesise(text: str, dest: Path, *, strip_labels: bool = True) -> Path:
    """Generate narration MP3; strip Hook:/Beat N: editor labels by default."""
    require_keys("ELEVEN_API_KEY")
    load_env()
    voice = os.environ.get("ELEVEN_VOICE_ID", "lJwraGf9dHERkgZPWTyE")
    key = os.environ["ELEVEN_API_KEY"]
    raw = text.strip()
    if strip_labels:
        raw = narration_text_for_tts(raw)
    if not raw:
        raise RuntimeError("Empty narration text after label stripping")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if len(raw) <= CHUNK_SIZE:
        _tts_chunk(raw, dest, voice, key)
        return dest
    chunks: list[str] = []
    buf = ""
    for para in raw.split("\n\n"):
        if len(buf) + len(para) + 2 <= CHUNK_SIZE:
            buf = f"{buf}\n\n{para}".strip() if buf else para
        else:
            if buf:
                chunks.append(buf)
            buf = para
    if buf:
        chunks.append(buf)
    tmp: list[Path] = []
    for i, ch in enumerate(chunks):
        part = dest.parent / f"{dest.stem}-part{i:02d}.mp3"
        _tts_chunk(ch, part, voice, key)
        tmp.append(part)
    _concat_mp3(tmp, dest)
    return dest
