"""Hook montage plan — June-style phrase → hero mapping for daily_single."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.captions import split_caption_cues
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.segment_video.align import _hook_roll_window

SCROLL_ATTENTION_FILE = "canonical-scroll.mp4"
ATTENTION_MOTION_SEC = 5.0

DEFAULT_MONTAGE_SPECS: list[dict[str, Any]] = [
    {
        "fragment": "what most teams actually get",
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
        "filename": "gpt-image-safeguard-fallback.png",
        "beat": 6,
        "visual": "safeguard slide",
        "fallback": "cyber-classifier.png",
    },
    {
        "fragment": "website-versus-developer mistake",
        "filename": "beat7-api-table.png",
        "beat": 7,
        "visual": "API table",
    },
]

TRUST_AUDIT_MONTAGE_SPECS: list[dict[str, Any]] = [
    {
        "fragment": "what the launch promised",
        "filename": "demo-launch.mp4",
        "in_sec": 18.0,
        "beat": 1,
        "visual": "launch clip",
    },
    {
        "fragment": "what the real task demos actually look like",
        "filename": "demo-fluid.mp4",
        "in_sec": 2.0,
        "beat": 4,
        "visual": "engineering demo clip",
    },
    {
        "fragment": "the LinkedIn comparison on five real jobs",
        "filename": "linkedin-cintas-fable5-vs-opus.mp4",
        "in_sec": 0.0,
        "beat": 1,
        "visual": "LinkedIn comparison clip",
    },
    {
        "fragment": "the safety pop-up you may see",
        "filename": "demo-factorio.mp4",
        "in_sec": 0.0,
        "beat": 3,
        "visual": "agent task demo clip",
    },
    {
        "fragment": "when the cheaper model quietly takes over without telling you",
        "filename": "linkedin-cintas-fable5-vs-opus.mp4",
        "in_sec": 8.0,
        "beat": 2,
        "visual": "side-by-side agent clip",
    },
]


COMBINED_MONTAGE_SPECS: list[dict[str, Any]] = [
    {
        "fragment": "what most teams actually get",
        "filename": "claudeai-launch.mp4",
        "in_sec": 0.0,
        "beat": 1,
        "visual": "launch clip",
    },
    {
        "fragment": "benchmark scores that matter",
        "filename": "carousel-factorio.mp4",
        "in_sec": 0.0,
        "beat": 3,
        "visual": "engineering demo",
    },
    {
        "fragment": "the X demo wave builders are sharing",
        "filename": "x-demo-deveshcodes-blackhole.mp4",
        "in_sec": 0.0,
        "beat": 5,
        "visual": "black hole demo",
    },
    {
        "fragment": "same-prompt comparisons on screen",
        "filename": "x-comparison-jono-flight.mp4",
        "in_sec": 0.0,
        "beat": 6,
        "visual": "flight comparison",
    },
    {
        "fragment": "safety without dead ends",
        "filename": "x-comparison-cintas-fable5-opus.mp4",
        "in_sec": 0.0,
        "beat": 6,
        "visual": "fable vs opus split",
    },
]


SPACEX_CURSOR_MONTAGE_SPECS: list[dict[str, Any]] = [
    {
        "fragment": "the headline numbers on screen",
        "filename": "beat1-deal-headline.png",
        "beat": 1,
        "visual": "deal headline card",
    },
    {
        "fragment": "what Cursor and Anysphere actually are",
        "filename": "beat2-cursor-stats.png",
        "beat": 2,
        "visual": "cursor stats card",
    },
    {
        "fragment": "how the all-stock merger works",
        "filename": "beat3-deal-structure.png",
        "beat": 3,
        "visual": "deal structure card",
    },
    {
        "fragment": "why a rocket company wants an IDE",
        "filename": "beat5-why-spacex.png",
        "beat": 5,
        "visual": "strategy card",
    },
    {
        "fragment": "five things to watch before Q3 close",
        "filename": "beat6-dev-watchlist.png",
        "beat": 6,
        "visual": "watchlist card",
    },
]


DISABLED_MONTAGE_SPECS: list[dict[str, Any]] = [
    {
        "fragment": "the launch hype that aged in 72 hours",
        "filename": "demo-launch.mp4",
        "in_sec": 18.0,
        "beat": 1,
        "visual": "launch clip",
    },
    {
        "fragment": "Anthropic's shutdown letter on screen",
        "filename": "demo-fluid.mp4",
        "in_sec": 2.0,
        "beat": 3,
        "visual": "engineering demo clip",
    },
    {
        "fragment": "why a jailbreak story killed access",
        "filename": "demo-factorio.mp4",
        "in_sec": 0.0,
        "beat": 5,
        "visual": "agent task demo clip",
    },
    {
        "fragment": "demos you cannot reproduce anymore",
        "filename": "demo-pokemon.mp4",
        "in_sec": 0.0,
        "beat": 5,
        "visual": "vision demo clip",
    },
    {
        "fragment": "five fixes for your stack tonight",
        "filename": "linkedin-cintas-fable5-vs-opus.mp4",
        "in_sec": 0.0,
        "beat": 1,
        "visual": "comparison clip",
    },
]


SOCIAL_COMPARISON_MONTAGE_SPECS: list[dict[str, Any]] = [
    {
        "fragment": "the official launch clip on X",
        "filename": "x-claudeai-launch.mp4",
        "in_sec": 0.0,
        "beat": 1,
        "visual": "@claudeai launch on X",
    },
    {
        "fragment": "a black-hole gravity sim posted on X the same week",
        "filename": "x-demo-deveshcodes-blackhole.mp4",
        "in_sec": 0.0,
        "beat": 1,
        "visual": "deveshcodes black hole sim on X",
    },
    {
        "fragment": "the Minecraft build from one prompt",
        "filename": "x-chrissgpt-minecraft.mp4",
        "in_sec": 0.0,
        "beat": 1,
        "visual": "ChrissGPT Minecraft clone on X",
    },
    {
        "fragment": "the Pokémon clone on screen that builders shared alongside it.",
        "filename": "x-chrissgpt-pokemon.mp4",
        "in_sec": 0.0,
        "beat": 4,
        "visual": "ChrissGPT Pokémon build on X",
    },
]


def montage_specs_for(beat_map: dict[str, Any]) -> list[dict[str, Any]]:
    variant = beat_map.get("variant")
    if beat_map.get("story_angle") == "m_and_a_developer_impact":
        return SPACEX_CURSOR_MONTAGE_SPECS
    if beat_map.get("story_angle") == "policy_shutdown_playbook":
        return DISABLED_MONTAGE_SPECS
    if variant == "trust-audit":
        return TRUST_AUDIT_MONTAGE_SPECS
    if variant == "social-comparison":
        return SOCIAL_COMPARISON_MONTAGE_SPECS
    if variant == "combined":
        return COMBINED_MONTAGE_SPECS
    return DEFAULT_MONTAGE_SPECS


def _word_weights(parts: list[str]) -> list[float]:
    return [max(1.0, len(p.split())) for p in parts]


def _resolve_asset(
    project: DailySingleProject,
    beat_map: dict,
    spec: dict[str, Any],
) -> Path | None:
    assets = project.assets_dir
    fname = spec["filename"]
    local_ref = project.root / "research" / "reference-images"
    local_vid = project.root / "research" / "reference-videos"
    for candidate in (
        local_ref / "generated" / fname,
        local_ref / "videos" / fname,
        local_ref / fname,
        local_vid / "anthropic" / fname,
        local_vid / "x" / fname,
        local_vid / "social" / fname,
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
    specs = montage_specs_for(beat_map)

    cues: list[dict[str, Any]] = []
    for i, spec in enumerate(specs):
        path = _resolve_asset(project, beat_map, spec)
        fragment = clauses[i] if i < len(clauses) else spec["fragment"]
        cues.append({
            "cue_index": i,
            "script_fragment": fragment,
            "file": path.name if path else spec["filename"],
            "path": str(path) if path else "",
            "visual": spec["visual"],
            "beat": spec.get("beat"),
            "in_sec": float(spec.get("in_sec") or 0),
            "ok": path is not None and path.is_file(),
        })

    plan = {
        "schema_version": 1,
        "overview_sentence": overview,
        "clauses": clauses,
        "cues": cues,
        "min_cues": len(specs),
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


def hook_attention_durations(
    hook_dur: float,
    script: str,
    *,
    motion_clip: bool = False,
) -> tuple[float, float, float]:
    """When a scroll clip is used, show scroll through hook line 1, then montage."""
    s1, s2, s3 = hook_sentence_durations(hook_dur, script)
    if not motion_clip:
        return s1, s2, s3
    scroll_att = min(ATTENTION_MOTION_SEC, max(2.0, hook_dur - 4.0))
    att = max(scroll_att, s1)
    rest = max(1.0, hook_dur - att)
    share = s2 / max(0.1, s2 + s3)
    overview = rest * share
    bridge = rest - overview
    return att, overview, bridge


def montage_cue_durations_from_whisper(
    project_root: Path,
    overview_dur: float,
    montage_cues: list[dict],
) -> list[float] | None:
    """Split overview montage using Whisper word spans from hook timestamps.json."""
    ts_path = project_root / "segments" / "00-hook" / "timestamps.json"
    if not ts_path.is_file() or not montage_cues:
        return None
    try:
        data = json.loads(ts_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    segs = data.get("segments") or []
    if len(segs) < 2:
        return None
    words = segs[1].get("words") or []
    if len(words) < 8:
        return None
    ov_start = float(segs[1].get("start") or 0)
    preamble_end = ov_start
    for w in words:
        if "minutes" in (w.get("word") or ""):
            preamble_end = float(w["end"])
            break
    ends: list[float] = []
    for w in words:
        tok = (w.get("word") or "").rstrip(",.:;")
        if tok in ("X", "fire", "prompt", "week"):
            ends.append(float(w["end"]))
    if len(ends) < len(montage_cues):
        return None
    ends = ends[: len(montage_cues)]
    starts = [preamble_end, *ends[:-1]]
    durs = [max(0.5, e - s) for s, e in zip(starts, ends)]
    total = sum(durs)
    if total <= 0:
        return None
    scale = overview_dur / total
    durs = [d * scale for d in durs]
    durs[-1] += overview_dur - sum(durs)
    return durs


def overview_montage_start_sec(project_root: Path) -> float | None:
    """Segment time when the first montage clause is spoken (after overview preamble)."""
    ts_path = project_root / "segments" / "00-hook" / "timestamps.json"
    if not ts_path.is_file():
        return None
    try:
        data = json.loads(ts_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    words = (data.get("segments") or [{}, {}])[1].get("words") or []
    for w in words:
        if "minutes" in (w.get("word") or ""):
            return float(w["end"])
    return None


def montage_cue_durations(
    overview_dur: float,
    montage_cues: list[dict],
    *,
    project_root: Path | None = None,
) -> list[float]:
    """Duration per montage hero within overview window."""
    if project_root is not None:
        whisper = montage_cue_durations_from_whisper(project_root, overview_dur, montage_cues)
        if whisper:
            return whisper
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


def attention_visual(
    project: DailySingleProject,
    montage_cues: list[dict],
    *,
    script: str = "",
) -> dict[str, Any]:
    """Prefer canonical page scroll video for hook attention when present."""
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    if beat_map.get("variant") == "trust-audit":
        for prefer in (
            "linkedin-cintas-fable5-vs-opus.mp4",
            "demo-fluid.mp4",
            "demo-launch.mp4",
            "demo-factorio.mp4",
        ):
            for cue in montage_cues:
                if cue.get("file") == prefer and cue.get("path"):
                    return cue
        return attention_hero(montage_cues)

    if beat_map.get("variant") == "social-comparison":
        for prefer in (
            "x-claudeai-launch.mp4",
            "x-chrissgpt-minecraft.mp4",
            "x-claudeai-safeguards.mp4",
            "x-pootlepress-wp-theme.mp4",
        ):
            for cue in montage_cues:
                if cue.get("file") == prefer and cue.get("path"):
                    return cue
        return attention_hero(montage_cues)

    if beat_map.get("variant") == "combined":
        for prefer in (
            "claudeai-launch.mp4",
            "x-demo-deveshcodes-blackhole.mp4",
            "x-comparison-jono-flight.mp4",
        ):
            for cue in montage_cues:
                if cue.get("file") == prefer and cue.get("path"):
                    return cue
        return attention_hero(montage_cues)

    scroll = project.assets_dir / "videos" / SCROLL_ATTENTION_FILE
    if scroll.is_file():
        sentences = split_caption_cues(script) if script else []
        return {
            "file": SCROLL_ATTENTION_FILE,
            "path": str(scroll),
            "visual": "canonical blog scroll",
            "script_fragment": sentences[0] if sentences else "",
            "ok": True,
        }
    return attention_hero(montage_cues)


def hook_visual_windows(
    hook_start: float,
    hook_dur: float,
    script: str,
    montage_cues: list[dict],
    *,
    project: DailySingleProject | None = None,
    launch_file: str = "claudeai-launch.mp4",
    bridge_file: str = "heygen.mp4",
) -> list[dict[str, Any]]:
    """Timeline windows for display_sync: attention → N heroes → bridge."""
    motion = False
    if project:
        from praisonaippt.daily_single.canonical_scroll import scroll_video_path

        try:
            beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            beat_map = {}
        skip_scroll = beat_map.get("variant") in ("trust-audit", "social-comparison", "combined")
        motion = bool(scroll_video_path(project)) and not skip_scroll
    att, overview, bridge = hook_attention_durations(hook_dur, script, motion_clip=motion)
    if project:
        from praisonaippt.daily_single.cue_slide_sync import _parse_segment_srt

        seg_srt = project.segments_dir / "00-hook" / "segment.srt"
        if seg_srt.is_file():
            rows = _parse_segment_srt(seg_srt)
            if len(rows) >= 3:
                att = max(att, rows[0][1])
                overview = max(0.5, rows[1][1] - att)
                bridge = max(0.5, rows[2][1] - rows[1][1])
                drift = hook_dur - att - overview - bridge
                if abs(drift) > 0.05:
                    bridge = max(0.5, bridge + drift)
        montage_t0 = overview_montage_start_sec(project.root)
        if montage_t0 is not None and montage_t0 > hook_start + att:
            att = montage_t0 - hook_start
            overview = max(0.5, rows[1][1] - att)
            bridge = max(0.5, rows[2][1] - rows[1][1])
            drift = hook_dur - att - overview - bridge
            if abs(drift) > 0.05:
                bridge = max(0.5, bridge + drift)
    windows: list[dict[str, Any]] = []
    t = hook_start
    hero = attention_visual(project, montage_cues, script=script) if project else attention_hero(montage_cues)
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
    per = montage_cue_durations(overview, montage_cues, project_root=project.root if project else None)
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
    bridge_file = launch_file
    bridge_visual = "bridge B-roll"
    if project:
        from praisonaippt.daily_single.canonical_scroll import scroll_video_path

        beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
        skip_scroll = beat_map.get("variant") in ("trust-audit", "social-comparison", "combined")
        scroll = scroll_video_path(project) if not skip_scroll else None
        if scroll:
            bridge_file = SCROLL_ATTENTION_FILE
            bridge_visual = "canonical blog scroll"
        elif beat_map.get("variant") in ("social-comparison", "combined"):
            bridge_file = "heygen.mp4"
            bridge_visual = "hook avatar bridge"
        elif montage_cues:
            bridge_file = str(montage_cues[0].get("file") or launch_file)
            bridge_visual = str(montage_cues[0].get("visual") or "montage hero")
    windows.append({
        "start": t,
        "end": hook_start + hook_dur,
        "beat": "00-hook",
        "visual": bridge_visual,
        "file": bridge_file,
        "section": "bridge",
    })
    return windows


def roll_window_from_script(script: str, hook_dur: float) -> tuple[float, float]:
    """Reuse segment_video roll-call window helper."""
    full = " ".join(split_caption_cues(script))
    return _hook_roll_window(full, hook_dur)
