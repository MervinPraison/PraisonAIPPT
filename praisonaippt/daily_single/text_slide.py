"""Render simple one-point-at-a-time slides for daily_single video beats."""
from __future__ import annotations

from pathlib import Path
from typing import Any

W, H = 1920, 1080
BG = (14, 16, 22)
BG_TOP = (11, 14, 24)
BG_BOT = (22, 28, 42)
GOLD = (212, 168, 75)
GOLD_SOFT = (160, 125, 55)
WHITE = (245, 245, 248)
MUTED = (160, 165, 175)
CARD_BG = (26, 32, 48)
CARD_EDGE = (48, 56, 72)


def _font(size: int, *, bold: bool = True):
    from PIL import ImageFont

    paths = (
        (
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        )
        if bold
        else (
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        )
    )
    for path in (
        *paths,
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient_bg() -> "Image.Image":
    from PIL import Image

    img = Image.new("RGB", (W, H), BG_TOP)
    px = img.load()
    for y in range(H):
        t = y / max(1, H - 1)
        row = tuple(int(BG_TOP[i] * (1 - t) + BG_BOT[i] * t) for i in range(3))
        for x in range(W):
            px[x, y] = row
    return img


def _rounded_rect(
    draw: "ImageDraw.ImageDraw",
    box: tuple[int, int, int, int],
    radius: int,
    *,
    fill: tuple[int, ...],
    outline: tuple[int, ...] | None = None,
    width: int = 2,
) -> None:
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    else:
        draw.rectangle(box, fill=fill, outline=outline, width=width)


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


def _draw_accent_pill(draw: "ImageDraw.ImageDraw", text: str, y: int) -> int:
    af = _font(34, bold=False)
    pad_x, pad_y = 28, 14
    tw = draw.textlength(text, font=af)
    box = (
        int(W // 2 - tw / 2 - pad_x),
        y,
        int(W // 2 + tw / 2 + pad_x),
        y + af.size + pad_y * 2,
    )
    _rounded_rect(draw, box, 28, fill=(36, 42, 58), outline=GOLD_SOFT, width=2)
    draw.text((W // 2, y + pad_y + af.size // 2), text, fill=GOLD, font=af, anchor="mm")
    return box[3] + 28


def _draw_bullet_cards(draw: "ImageDraw.ImageDraw", bullets: list[str]) -> None:
    n = len(bullets)
    if n == 0:
        return
    body = _font(30, bold=False)
    label_f = _font(22, bold=True)
    if n == 3:
        card_w, card_h, gap = 520, 220, 36
        total_w = n * card_w + (n - 1) * gap
        x0 = (W - total_w) // 2
        y0 = 700
        icons = ("✦", "◆", "▲")
        for i, bullet in enumerate(bullets):
            x1 = x0 + i * (card_w + gap)
            x2, y2 = x1 + card_w, y0 + card_h
            _rounded_rect(draw, (x1, y0, x2, y2), 18, fill=CARD_BG, outline=CARD_EDGE, width=2)
            draw.rectangle((x1, y0, x2, y0 + 5), fill=GOLD)
            badge_cx, badge_cy = x1 + 52, y0 + 52
            draw.ellipse((badge_cx - 28, badge_cy - 28, badge_cx + 28, badge_cy + 28), fill=GOLD_SOFT)
            draw.text((badge_cx, badge_cy), icons[i % len(icons)], fill=WHITE, font=_font(26), anchor="mm")
            ty = y0 + 100
            for line in _wrap(bullet, draw, body, card_w - 56):
                draw.text((x1 + 28, ty), line, fill=WHITE, font=body, anchor="la")
                ty += 38
            draw.text((x1 + 28, y2 - 34), f"0{i + 1}", fill=MUTED, font=label_f, anchor="la")
        return

    bf = _font(42)
    y = max(520, H // 2)
    for i, bullet in enumerate(bullets):
        x1, y1 = 120, y
        x2 = W - 120
        lines = _wrap(bullet, draw, bf, x2 - x1 - 80)
        box_h = max(96, len(lines) * 50 + 36)
        _rounded_rect(draw, (x1, y1, x2, y1 + box_h), 16, fill=CARD_BG, outline=CARD_EDGE, width=2)
        draw.ellipse((x1 + 24, y1 + 24, x1 + 56, y1 + 56), fill=GOLD_SOFT)
        draw.text((x1 + 40, y1 + 40), str(i + 1), fill=WHITE, font=_font(20), anchor="mm")
        ty = y1 + 22
        for line in lines:
            draw.text((x1 + 72, ty), line, fill=WHITE, font=bf, anchor="la")
            ty += 50
        y = y1 + box_h + 24


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
    img = _gradient_bg()
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 5), fill=GOLD)
    draw.rectangle((0, 5, W, 7), fill=GOLD_SOFT)
    draw.line((96, 120, 96, H - 120), fill=GOLD_SOFT, width=2)

    if show_steps and step and total and total > 1:
        badge = f"{step} / {total}"
        draw.text((W - 96, 52), badge, fill=MUTED, font=_font(32), anchor="ra")

    hf = _font(64 if bullets else 78)
    y = 150 if bullets else 220
    for line in _wrap(headline, draw, hf, W - 280):
        draw.text((W // 2, y), line, fill=WHITE, font=hf, anchor="ma")
        y += 78

    if accent:
        y = _draw_accent_pill(draw, accent, y + 20)

    if bullets:
        _draw_bullet_cards(draw, bullets)
    else:
        draw.line((W // 2 - 120, y + 40, W // 2 + 120, y + 40), fill=GOLD, width=3)

    img.save(dest)
    return dest


_DEFAULT_OUTRO_CTA: list[dict[str, Any]] = [
    {
        "file": "outro-cta.png",
        "headline": "Like · Share · Subscribe",
        "bullets": ["Builder demos link in description", "Thanks for watching"],
        "topics": ("like", "share", "subscribe", "demos", "description", "thanks", "watching"),
    },
]

_SOCIAL_COMPARISON_OUTRO: list[dict[str, Any]] = [
    {
        "file": "outro-cta.png",
        "headline": "Every comparison clip is sourced",
        "accent": "Benchmark tables and clip links in the description",
        "bullets": [
            "Subscribe for launch-week breakdowns",
            "Thanks for watching",
        ],
        "topics": (
            "source", "links", "comparison", "clip", "benchmark", "tables",
            "description", "subscribe", "launch-week", "breakdowns", "thanks", "watching",
        ),
    },
]

_TRUST_AUDIT_OUTRO: list[dict[str, Any]] = [
    {
        "file": "outro-cta.png",
        "headline": "Full comparison tables",
        "accent": "Source links in the video description",
        "bullets": [
            "Subscribe for launch-week breakdowns",
            "Thanks for watching",
        ],
        "topics": (
            "comparison", "tables", "source", "links", "description",
            "subscribe", "launch-week", "breakdowns", "thanks", "watching",
        ),
    },
]


def outro_slide_specs(variant: str = "") -> list[dict[str, Any]]:
    """Variant-aware outro CTA slide — matches segments/99-outro/script.md tone."""
    if variant == "social-comparison":
        return _SOCIAL_COMPARISON_OUTRO
    if variant == "trust-audit":
        return _TRUST_AUDIT_OUTRO
    return _DEFAULT_OUTRO_CTA


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
        "outro-cta": _DEFAULT_OUTRO_CTA,
    }


def visual_meta_from_specs() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    groups = list(slide_specs().values()) + [
        _DEFAULT_OUTRO_CTA,
        _SOCIAL_COMPARISON_OUTRO,
        _TRUST_AUDIT_OUTRO,
    ]
    for group in groups:
        for spec in group:
            fn = spec["file"]
            topics = tuple(spec.get("topics") or ())
            prev = out.get(fn, {}).get("topics") or ()
            merged = tuple(dict.fromkeys(prev + topics))
            out[fn] = {
                "vision_description": " ".join(merged),
                "topics": merged,
                "visual_focus": merged[:6],
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
