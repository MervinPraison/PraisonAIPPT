"""Default paths and constants for sermon article SDK."""
from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
SERMON_PACKS_DIR = EXAMPLES_DIR / "sermon_packs"

DEFAULT_PACK_DIR = Path.home() / "Downloads" / "BIC-Sermon-Deck-Pack-2"
DEFAULT_DRAFT_DIR = Path("/tmp")
DEFAULT_COVER_DIR = Path("/tmp") / "sermon-covers"
DEFAULT_AGENT_DIR = Path.home() / "praisonai-audio-editor" / ".agent"

WP_SERVER = "biblerevelation"
WP_SSH = "root@185.249.73.167"
WP_ROOT = "/home/hestiaadmin/web/biblerevelation.org/public_html/wordpress"
SSH_KEY = Path.home() / ".ssh" / "id_ed25519"

GPT_IMAGE_DIR = Path.home() / "create-post" / "gpt-image"
VALIDATE_SKILL_DIR = Path.home() / ".cursor/skills/biblerevelation-sermon-articles/scripts"

IMAGE_SIZE = "1536x1024"
MIN_WORD_RATIO = 0.55

GREEN = "#bbf7d0"
GOLD = "#fde68a"
