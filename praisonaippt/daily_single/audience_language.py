"""Plain-language checks for general YouTube audience (non-developer)."""
from __future__ import annotations

import re

from praisonaippt.daily_single.captions import split_caption_cues
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER

# Hard ban — always fail (also in youtube_quality.JARGON_PATTERNS).
BANNED_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bmessages api\b", "Say 'developer connection' instead of Messages API"),
    (r"\bmer\.vin\b", "Do not mention mer.vin in spoken script"),
    (r"\bclassifier stack\b", "Say 'safety checks' instead"),
    (r"\bmetered api\b", "Say 'pay-as-you-go billing' instead"),
)

# Allowed only after beat 02 (mythos-tier) introduces the tiers.
MYTHOS_BEFORE_TIER_BEAT = re.compile(r"\bmythos\b", re.I)

# Terms that need a plain gloss in the same sentence.
GLOSS_REQUIRED: tuple[tuple[str, str, str], ...] = (
    (
        r"\bbackup model\b",
        r"(simpler model|routes?|switches?|another model|different model)",
        "Explain backup model: e.g. 'routes to a simpler model'",
    ),
    (
        r"\bjailbreak\b",
        r"(bypass|trick|break|safety rule)",
        "Say 'tricks to bypass safety rules' not 'jailbreak'",
    ),
    (
        r"\bproject glasswing\b",
        r"(partner|research|trusted|defence|defense)",
        "Explain Glasswing: e.g. 'trusted partner programme'",
    ),
    (
        r"\bhard no\b",
        r"(refusal|shut|block|blank)",
        "Say 'blank refusal' or 'shuts you down' not 'hard no'",
    ),
    (
        r"\bmythos[- ]level\b",
        r"(research|partner|everyday|standard|version)",
        "Explain Mythos: e.g. 'research-only version' — or remove until beat 02",
    ),
)


def _segment_text(project: DailySingleProject, seg_dir: str) -> str:
    path = project.segment_script(seg_dir)
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def validate_audience_language(project: DailySingleProject) -> tuple[bool, list[str]]:
    """Flag jargon and unexplained product terms before tier beat."""
    issues: list[str] = []
    seen_tier_beat = False

    for label, seg_dir, beat_n in SEGMENT_ORDER:
        if label == "99-outro":
            continue
        text = _segment_text(project, seg_dir)
        if not text.strip():
            continue
        if beat_n == 2 or seg_dir == "02-mythos-tier":
            seen_tier_beat = True

        lower = text.lower()
        for pat, hint in BANNED_PATTERNS:
            if re.search(pat, lower, re.I):
                issues.append(f"{seg_dir}: {hint}")

        if not seen_tier_beat and MYTHOS_BEFORE_TIER_BEAT.search(text):
            issues.append(
                f"{seg_dir}: 'Mythos' before tiers are explained — use 'everyday version' "
                "or 'partner version' until 02-mythos-tier"
            )

        for sentence in split_caption_cues(text):
            sent_lower = sentence.lower()
            for term_pat, gloss_pat, hint in GLOSS_REQUIRED:
                if re.search(term_pat, sent_lower, re.I) and not re.search(gloss_pat, sent_lower, re.I):
                    issues.append(f"{seg_dir}: {hint} — in: {sentence[:80]}…")

    return len(issues) == 0, issues
