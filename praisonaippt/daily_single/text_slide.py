"""Render simple one-point-at-a-time slides for daily_single video beats."""
from __future__ import annotations

from pathlib import Path
from typing import Any

W, H = 1920, 1080
BG = (14, 16, 22)
GOLD = (212, 168, 75)
WHITE = (245, 245, 248)
MUTED = (160, 165, 175)


def _font(size: int):
    from PIL import ImageFont

    for path in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(text: str, draw, font, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for word in words:
        trial = " ".join(cur + [word])
        if draw.textlength(trial, font=font) <= max_w:
            cur.append(word)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
    return lines or [text]


def render_point_slide(
    dest: Path,
    *,
    headline: str,
    bullets: list[str] | None = None,
    step: int | None = None,
    total: int | None = None,
    accent: str = "",
    show_steps: bool = True,
) -> Path:
    from PIL import Image, ImageDraw

    dest.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 6), fill=GOLD)

    if show_steps and step and total and total > 1:
        badge = f"{step} / {total}"
        bf = _font(36)
        draw.text((W - 120, 48), badge, fill=MUTED, font=bf, anchor="ra")

    hf = _font(72 if bullets else 78)
    y = 180 if bullets else 220
    for line in _wrap(headline, draw, hf, W - 240):
        draw.text((W // 2, y), line, fill=WHITE, font=hf, anchor="ma")
        y += 88

    if accent:
        af = _font(40)
        draw.text((W // 2, y + 16), accent, fill=GOLD, font=af, anchor="ma")
        y += 72

    if bullets:
        bf = _font(48)
        y = max(y + 36, 420)
        for bullet in bullets:
            label = f"•  {bullet}"
            for line in _wrap(label, draw, bf, W - 300):
                draw.text((140, y), line, fill=WHITE, font=bf, anchor="la")
                y += 58

    img.save(dest)
    return dest


def slide_specs() -> dict[str, list[dict[str, Any]]]:
    """Slide content keyed by beat id — mirrored in display_sync."""
    return {
        "beat-01-rest": [
            {
                "file": "beat1-launch-summary.png",
                "headline": "Anthropic's June launch — why it spread",
                "accent": "Claude Fable five for everyday teams",
                "bullets": [
                    "Strong for daily work — not just research demos",
                    "Safety that answers or routes — not blank refusals",
                    "Overnight builder wave — games, sims, apps from plain English",
                ],
                "topics": (
                    "fable", "teams", "daily", "safety", "answers", "routes",
                    "builder", "demos", "games", "simulations", "apps", "instructions",
                    "social", "feeds", "festival", "software", "morning", "working", "launch",
                ),
            },
        ],
        "beat-02-extra": [
            {
                "file": "beat2-point-fable.png",
                "headline": "Fable five — for everyone",
                "bullets": ["Security checks stay on", "In Claude apps through mid-June"],
                "topics": ("fable", "security", "checks", "apps", "june", "claude"),
            },
            {
                "file": "beat2-point-mythos.png",
                "headline": "Mythos five — partners only",
                "bullets": ["No public shelf name", "Not in the programme? Pick Fable"],
                "topics": ("mythos", "partner", "programme", "pick", "fable", "research"),
            },
        ],
        "beat-07-rest": [
            {
                "file": "beat7-point-block.png",
                "headline": "Paid API connection",
                "bullets": ["Sensitive prompts blocked by default", "Expect an error — not a quiet switch"],
                "topics": ("api", "blocked", "default", "error", "billing", "sensitive", "prompts"),
            },
            {
                "file": "beat7-point-optin.png",
                "headline": "You can opt in",
                "bullets": ["Same fallback as claude.ai if you choose", "Log model name and latency"],
                "topics": ("compliance", "continuity", "silent", "story", "assumes", "opt", "fallback", "claude.ai", "hosted", "platforms", "enterprise", "log", "model", "latency"),
            },
            {
                "file": "beat7-point-test.png",
                "headline": "Before live traffic",
                "bullets": ["Test both paths in a test environment", "Audit logs matter for compliance"],
                "topics": ("test", "paths", "environment", "audit", "compliance", "enterprise"),
            },
        ],
        "beat-09-all": [
            {
                "file": "beat9-point-tokens.png",
                "headline": "Usage-based pricing",
                "bullets": ["Ten dollars per million words in", "Fifty per million words out"],
                "topics": ("pricing", "ten", "fifty", "dollars", "million", "tokens", "words"),
            },
            {
                "file": "beat9-point-subs.png",
                "headline": "Included through June",
                "bullets": ["Pro, Max, Team, Enterprise seats", "Fable through 22 June 2026"],
                "topics": ("pro", "max", "team", "enterprise", "june", "subscription", "seats"),
            },
            {
                "file": "beat9-point-budget.png",
                "headline": "Long autonomous runs",
                "bullets": ["Budget for usage billing", "If plan limits are tight"],
                "topics": ("budget", "autonomous", "runs", "usage", "billing", "limits"),
            },
        ],
        "outro-cta": [
            {
                "file": "outro-cta.png",
                "headline": "Like · Share · Subscribe",
                "bullets": ["Builder demos link in description", "Thanks for watching"],
                "topics": ("like", "share", "subscribe", "demos", "description", "thanks", "watching"),
            },
        ],
    }


def visual_meta_from_specs() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for group in slide_specs().values():
        for spec in group:
            fn = spec["file"]
            topics = tuple(spec.get("topics") or ())
            out[fn] = {
                "vision_description": " ".join(topics),
                "topics": topics,
                "visual_focus": topics[:6],
            }
    return out


def render_slide_group(specs: list[dict[str, Any]], out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    total = len(specs)
    show_steps = total > 1
    for i, spec in enumerate(specs, 1):
        dest = out_dir / spec["file"]
        render_point_slide(
            dest,
            headline=str(spec["headline"]),
            bullets=list(spec.get("bullets") or []),
            step=i if show_steps else None,
            total=total if show_steps else None,
            accent=str(spec.get("accent") or ""),
            show_steps=show_steps,
        )
        paths.append(dest)
    return paths
