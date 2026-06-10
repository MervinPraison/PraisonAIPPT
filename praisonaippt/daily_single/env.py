"""Environment loading for daily_single media stages."""
from __future__ import annotations

import os
from pathlib import Path

DEFAULT_VOICE_ID = "lJwraGf9dHERkgZPWTyE"
DEFAULT_AVATAR_ID = "78b7d68884634fbdb84c965e4a9d7dee"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_env(extra_env: Path | None = None) -> None:
    paths = [repo_root() / ".env"]
    if extra_env:
        paths.append(extra_env)
    home_eleven = Path.home() / "elevenlabsAutomation" / ".env"
    if home_eleven.is_file():
        paths.append(home_eleven)
    for path in paths:
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip("\"'"))
    key = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVEN_API_KEY")
    if key:
        os.environ["ELEVENLABS_API_KEY"] = key
        os.environ["ELEVEN_API_KEY"] = key
    os.environ.setdefault("ELEVEN_VOICE_ID", DEFAULT_VOICE_ID)
    os.environ.setdefault("AVATAR_ID", DEFAULT_AVATAR_ID)
    os.environ.setdefault("PRAISONAIPPT_VISION_MODEL", "gpt-4o-mini")
    if os.environ.get("OPENAI_API_KEY") and not os.environ.get("PRAISONAIPPT_VISION_PROVIDER"):
        os.environ.setdefault("PRAISONAIPPT_VISION_PROVIDER", "openai")


def require_keys(*names: str) -> None:
    load_env()
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise RuntimeError(f"Missing required env: {', '.join(missing)}")
