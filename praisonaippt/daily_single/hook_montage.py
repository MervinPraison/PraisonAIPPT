"""Hook montage plan — June-style phrase → hero mapping for daily_single."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.captions import split_caption_cues
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.segment_video.align import _hook_roll_window

# Order matches comma clauses in overview cue (June roll-call pattern).
DEFAULT_MONTAGE_SPECS: list[dict[str, Any]] = [
    {
        "fragment": "Fable versus Mythos",
        "filename": "beat2-tier-diagram.png",
        "beat": 2,
        "visual": "tier diagram",
    },
    {
        "fragment": "Stripe's fifty-million-line proof",
        "filename": "beat3-stripe-card.png",
        "beat": 3,
        "visual": "Stripe card",
    },
    {
        "fragment": "benchmark scores that matter",
        "filename": "benchmark-table.png",
        "beat": 4,
        "visual": "benchmark slide",
    },
    {
        "fragment": "safety without dead ends",
        "filename": "cyber-classifier.png",
        "beat": 6,
        "visual": "safeguard slide",
        "fallback": "gpt-image-safeguard-fallback.png",
    },
    {
        "fragment": "app-versus-API mistake",
        "filename": "beat7-api-table.png",
        "beat": 7,
        "visual": "API table",
    },
]


def _word_weights(parts: list[str]) -> list[float]:
    return [max(1.0, len(p.split())) for p in parts]


def _resolve_asset(
    project: DailySingleProject,
    beat_map: dict,
    spec: dict[str, Any],
) -> Path | None:
    assets = project.assets_dir
    fname = spec["filename"]
    for candidate in (
        assets / "generated" / fname,
        assets / "images" / fname,
        assets / fname,
    ):
        if candidate.is_file():
            return candidate
    beat = beat_map.get("beats", {}).get(str(spec.get("beat", "")))
    if beat:
        for key in ("generated", "images", "clips"):
            for item in beat.get(key) or []:
                if fname in str(item.get("filename", "")) or fname in str(item.get("path", "")):
                    path = Path(item["path"])
                    if path.is_file():
                        return path
    fb = spec.get("fallback")
    if fb:
        p = assets / "generated" / fb
        if p.is_file():
            return p
    return None


def parse_overview_clauses(overview_sentence: str) -> list[str]:
    """Split overview roll-call after colon into montage phrases."""
    text = overview_sentence.strip()
    if ":" in text:
        text = text.split(":", 1)[1].strip()
    parts = [p.strip() for p in re.split(r",\s*(?:and\s+)?", text) if p.strip()]
    return parts


def build_hook_montage_plan(project: DailySingleProject) -> dict[str, Any]:
    script_path = project.segment_script("00-hook")
    script = script_path.read_text(encoding="utf-8") if script_path.is_file() else ""
    sentences = split_caption_cues(script)
    overview = sentences[1] if len(sentences) >= 2 else ""
    clauses = parse_overview_clauses(overview)
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))

    cues: list[dict[str, Any]] = []
    for i, spec in enumerate(DEFAULT_MONTAGE_SPECS):
        path = _resolve_asset(project, beat_map, spec)
        fragment = clauses[i] if i < len(clauses) else spec["fragment"]
        cues.append({
            "cue_index": i,
            "script_fragment": fragment,
            "file": path.name if path else spec["filename"],
            "path": str(path) if path else "",
            "visual": spec["visual"],
            "beat": spec.get("beat"),
            "ok": path is not None and path.is_file(),
        })

    plan = {
        "schema_version": 1,
        "overview_sentence": overview,
        "clauses": clauses,
        "cues": cues,
        "min_cues": len(DEFAULT_MONTAGE_SPECS),
    }
    out = project.segments_dir / "00-hook" / "hook_montage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan


def load_hook_montage_plan(project: DailySingleProject) -> dict[str, Any]:
    path = project.segments_dir / "00-hook" / "hook_montage.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return build_hook_montage_plan(project)


def hook_sentence_durations(hook_dur: float, script: str) -> tuple[float, float, float]:
    """Return (attention_sec, overview_sec, bridge_sec) from three hook sentences."""
    sentences = split_caption_cues(script)
    if len(sentences) < 3:
        third = hook_dur / 3
        return third, third, hook_dur - 2 * third
    weights = _word_weights(sentences)
    total_w = sum(weights)
    durs = [max(0.8, hook_dur * (w / total_w)) for w in weights]
    drift = hook_dur - sum(durs)
    durs[-1] += drift
    return durs[0], durs[1], durs[2]


def montage_cue_durations(overview_dur: float, montage_cues: list[dict]) -> list[float]:
    """Word-weight duration per montage hero within overview window."""
    weights = _word_weights([c.get("script_fragment", "") for c in montage_cues])
    total_w = sum(weights) or len(montage_cues)
    durs = [max(0.5, overview_dur * (w / total_w)) for w in weights]
    drift = overview_dur - sum(durs)
    if durs:
        durs[-1] += drift
    return durs


def attention_hero(montage_cues: list[dict]) -> dict[str, Any]:
    """First resolved montage hero — used for hook attention instead of launch B-roll."""
    return montage_cues[0] if montage_cues else {}


def hook_visual_windows(
    hook_start: float,
    hook_dur: float,
    script: str,
    montage_cues: list[dict],
    *,
    launch_file: str = "claudeai-launch.mp4",
    bridge_file: str = "heygen.mp4",
) -> list[dict[str, Any]]:
    """Timeline windows for display_sync: attention → N heroes → bridge."""
    att, overview, bridge = hook_sentence_durations(hook_dur, script)
    windows: list[dict[str, Any]] = []
    t = hook_start
    hero = attention_hero(montage_cues)
    windows.append({
        "start": t,
        "end": t + att,
        "beat": "00-hook",
        "visual": hero.get("visual", "hero slide"),
        "file": hero.get("file", launch_file),
        "section": "attention",
        "script_fragment": hero.get("script_fragment", ""),
    })
    t += att
    per = montage_cue_durations(overview, montage_cues)
    for cue, dur in zip(montage_cues, per):
        windows.append({
            "start": t,
            "end": t + dur,
            "beat": "00-hook",
            "visual": cue.get("visual", "montage slide"),
            "file": cue.get("file", ""),
            "section": "overview",
            "script_fragment": cue.get("script_fragment", ""),
        })
        t += dur
    windows.append({
        "start": t,
        "end": hook_start + hook_dur,
        "beat": "00-hook",
        "visual": "HeyGen avatar",
        "file": bridge_file,
        "section": "bridge",
    })
    return windows


def roll_window_from_script(script: str, hook_dur: float) -> tuple[float, float]:
    """Reuse segment_video roll-call window helper."""
    full = " ".join(split_caption_cues(script))
    return _hook_roll_window(full, hook_dur)
