"""Map SRT cues to on-screen visuals and score caption↔slide sync."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.hook_montage import build_hook_montage_plan, hook_visual_windows
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.segment_video.image_selection import script_alignment, tokenise
from praisonaippt.segment_video.media import ffprobe_duration

MIN_ALIGNMENT = 0.35
HOOK_MONTAGE_MIN_ALIGNMENT = 0.45

# Keywords / metadata for scoring when handoff vision_description is absent.
VISUAL_META: dict[str, dict[str, Any]] = {
    "heygen.mp4": {
        "vision_description": "presenter avatar hook overview walkthrough subscribe fable mythos stripe pricing started",
        "topics": ("walkthrough", "cover", "fable", "mythos", "overview", "started", "subscribe", "minutes", "stripe", "pricing", "safety"),
    },
    "claudeai-launch.mp4": {
        "vision_description": "anthropic launch clip june shipped builders official b-roll",
        "topics": ("launch", "june", "shipped", "walkthrough", "b-roll", "builders"),
    },
    "canonical-scroll.mp4": {
        "vision_description": "anthropic news blog claude fable mythos announcement scroll launch page",
        "topics": ("anthropic", "fable", "mythos", "launch", "announcement", "blog", "claude", "news", "dropped", "changes"),
    },
    "bio-aav-chart.png": {
        "vision_description": "biology chemistry AAV viral shell assembly evaluation chart",
        "topics": ("biology", "chemistry", "aav", "virus", "gene", "therapy", "classifier"),
    },
    "beat1-views-overlay.png": {
        "vision_description": "anthropic june launch views everyone claude fable five strongest models",
        "topics": ("anthropic", "june", "launch", "everyone", "fable", "five", "strongest", "models", "teams", "claude"),
    },
    "beat2-tier-diagram.png": {
        "vision_description": "fable mythos glasswing tier api claude-fable-5 messages enterprise what teams get",
        "topics": ("fable", "mythos", "glasswing", "engine", "surfaces", "api", "integrate", "teams", "get", "most", "actually"),
    },
    "beat3-stripe-card.png": {
        "vision_description": "stripe fifty million lines migration one day manual months",
        "topics": ("stripe", "million", "lines", "migration", "manual", "ruby"),
    },
    "carousel-factorio.mp4": {
        "vision_description": "factorio factory automation agentic loops coding tasks migrations community apps browser",
        "topics": ("factorio", "factory", "automation", "agentic", "loops", "migrations", "coding", "tasks", "projects", "browser", "game", "match", "board", "windows", "community", "demos"),
    },
    "carousel-vibecad.mp4": {
        "vision_description": "cad vibecad engineering workflows",
        "topics": ("cad", "workflows", "refactors", "automation", "clips", "design", "tools"),
    },
    "carousel-solar.mp4": {
        "vision_description": "solar system eclipse simulation community demo browser game city builder",
        "topics": ("solar", "system", "eclipse", "simulation", "browser", "game", "city", "world", "prompt", "demo", "builders", "linkedin", "community"),
    },
    "carousel-fluid.mp4": {
        "vision_description": "fluid simulation engineering demo b-roll clip",
        "topics": ("fluid", "simulation", "engineering", "demo", "clip", "vision"),
    },
    "beat4-stat-overlay.png": {
        "vision_description": "swe-bench verified ninety-five terminal-bench eighties fable mythos longer jobs advantage",
        "topics": ("swe-bench", "ninety-five", "terminal", "eighties", "fable", "mythos", "benchmark", "longer", "jobs", "advantage"),
    },
    "benchmark-table.png": {
        "vision_description": "benchmark scorecard frontier leaderboard engineering knowledge vision",
        "topics": ("frontier", "benchmark", "leaderboard", "engineering", "knowledge", "launch", "card"),
    },
    "pokemon-timelapse.mp4": {
        "vision_description": "pokemon firered vision screenshot navigation harness demo",
        "topics": ("pokemon", "vision", "firered", "screenshot", "navigation", "demo", "scaffolding"),
    },
    "beat5-spire-stat.png": {
        "vision_description": "slay spire memory three times final-act opus completion stat",
        "topics": ("spire", "memory", "three", "final-act", "opus", "stat", "gameplay"),
    },
    "gpt-image-safeguard-fallback.png": {
        "vision_description": "safeguard fallback diagram classifier backup not blocked safety dead ends",
        "topics": ("fallback", "diagram", "safeguard", "classifier", "sessions", "refusing", "safety", "dead", "ends", "blocking"),
    },
    "distillation-safeguard.png": {
        "vision_description": "copy protection distillation safeguard biology chemistry checks training partner cyber testing",
        "topics": ("distillation", "copy", "protection", "safeguard", "biology", "chemistry", "training", "steal", "abilities", "partner", "testing", "cyber", "harmful", "tricks", "bypass"),
    },
    "cyber-classifier.png": {
        "vision_description": "cyber classifier exploitation offensive agentic hacking sessions backup ninety-five percent",
        "topics": ("cyber", "classifier", "exploitation", "hacking", "offensive", "ninety", "five", "percent", "sessions", "backup", "need"),
    },
    "jailbreak-resistance.png": {
        "vision_description": "jailbreak resistance bounty harmful cyber completions thirty days bypass safety",
        "topics": ("jailbreak", "bounty", "harmful", "cyber", "completions", "techniques", "thirty", "days", "bypass", "safety", "training", "stored"),
    },
    "beat7-api-table.png": {
        "vision_description": "api messages web app block fallback claude.ai enterprise consumption website developer mistake",
        "topics": ("api", "web", "app", "block", "fallback", "messages", "claude.ai", "enterprise", "opt", "website", "developer", "mistake", "versus"),
    },
    "beat8-glasswing.png": {
        "vision_description": "project glasswing cyber defenders mythos preview tiers",
        "topics": ("glasswing", "cyber", "defenders", "mythos", "preview", "tiers"),
    },
    "protein-complexes.png": {
        "vision_description": "biology trusted access cohort researchers bio classifiers",
        "topics": ("biology", "trusted", "researchers", "cohort", "bio", "classifiers"),
    },
    "beat9-pricing.png": {
        "vision_description": "pricing ten fifty dollars million tokens june subscription",
        "topics": ("pricing", "ten", "fifty", "dollars", "tokens", "june", "subscription", "enterprise"),
    },
    "jailbreak-retention.png": {
        "vision_description": "retention thirty days jailbreak prompts logged training distillation eval",
        "topics": ("retention", "thirty", "jailbreak", "prompts", "training", "distillation", "eval", "classifiers"),
    },
    "alignment-chart.png": {
        "vision_description": "misaligned behaviour alignment eval chart mythos opus scores safeguards tighten launch",
        "topics": ("misaligned", "alignment", "behaviour", "chart", "safeguards", "tighten", "launch", "settings", "copying", "model", "production"),
    },
}


def _srt_ts(ts: str) -> float:
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_srt(path: Path) -> list[dict[str, Any]]:
    blocks = re.split(r"\n\n+", path.read_text(encoding="utf-8").strip())
    cues: list[dict[str, Any]] = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        a, b = [x.strip() for x in lines[1].split("-->")]
        cues.append({
            "start_sec": _srt_ts(a),
            "end_sec": _srt_ts(b),
            "text": " ".join(lines[2:]).strip(),
        })
    return cues


def _meta_for(filename: str) -> dict[str, Any]:
    base = Path(filename).name
    if base in VISUAL_META:
        return VISUAL_META[base]
    stem = base.lower()
    for key, meta in VISUAL_META.items():
        if key.replace(".png", "").replace(".mp4", "") in stem:
            return meta
    return {"vision_description": stem, "topics": ()}


def score_cue_visual(cue_text: str, visual_file: str) -> float:
    meta = _meta_for(visual_file)
    img = {
        "vision_description": meta.get("vision_description", ""),
        "relevance_reason": " ".join(meta.get("topics") or ()),
        "topic_relevance_score": 0.8,
    }
    score = script_alignment(cue_text, img)
    topics = meta.get("topics") or ()
    cue_tokens = tokenise(cue_text)
    if topics:
        hit = len(cue_tokens & set(topics)) / max(1, len(cue_tokens))
        score = max(score, min(1.0, hit * 2.5))
    # Hard penalties for known mismatches
    if "alignment-chart" in visual_file and any(
        w in cue_tokens for w in ("retention", "thirty", "prompts", "mer.vin", "distillation")
    ):
        score = min(score, 0.15)
    if "beat4-stat-overlay" in visual_file and "leaderboard" in cue_text.lower() and "swe" not in cue_text.lower():
        score = min(score, 0.25)
    if "benchmark-table" in visual_file and any(w in cue_tokens for w in ("swe-bench", "ninety-five", "terminal")):
        score = max(score, 0.5)
    return round(score, 3)


@dataclass
class VisualWindow:
    start_sec: float
    end_sec: float
    beat: str
    visual: str
    file: str
    section: str = ""
    script_fragment: str = ""


def _windows_for_beat(
    beat_key: str,
    beat_num: int | None,
    seg_start: float,
    seg_dur: float,
    spec: dict,
    assets: Path,
    *,
    hook_launch: bool = False,
    outro_table: bool = False,
) -> list[VisualWindow]:
    dur = seg_dur
    t0 = seg_start

    if hook_launch:
        return [VisualWindow(t0, t0 + dur, "00-hook", "launch B-roll", "claudeai-launch.mp4")]

    if outro_table:
        return [VisualWindow(t0, t0 + dur, "99-outro", "API table recap", "beat7-api-table.png")]

    clips = spec.get("clips") or []
    generated = spec.get("generated") or []
    images = spec.get("images") or []

    def _dedupe(items: list[dict]) -> list[dict]:
        seen: set[str] = set()
        out: list[dict] = []
        for it in items:
            k = it.get("filename") or it.get("path", "")
            if k in seen:
                continue
            seen.add(k)
            out.append(it)
        return out

    generated = _dedupe(generated)
    images = _dedupe(images)
    wins: list[VisualWindow] = []

    if beat_num == 7:
        table = next((g for g in generated if "beat7" in g.get("filename", "")), None)
        table_dur = min(28.0, max(12.0, dur * 0.5))
        if table:
            wins.append(VisualWindow(t0, t0 + table_dur, f"beat-{beat_num:02d}", "API table", Path(table["path"]).name))
        flow = assets / "gpt-image-safeguard-fallback.png"
        if flow.is_file() and table_dur < dur:
            wins.append(VisualWindow(t0 + table_dur, t0 + dur, f"beat-{beat_num:02d}", "fallback diagram", flow.name))
        return wins

    if beat_num == 1 and generated:
        wins.append(VisualWindow(
            t0, t0 + dur, "beat-01", "views overlay", Path(generated[0]["path"]).name,
        ))
        return wins

    if beat_num == 3 and generated and clips:
        card_d = min(14.0, dur * 0.38)
        wins.append(VisualWindow(t0, t0 + card_d, f"beat-{beat_num:02d}", "Stripe card", Path(generated[0]["path"]).name))
        rest = dur - card_d
        per = rest / len(clips)
        off = t0 + card_d
        for c in clips:
            wins.append(VisualWindow(off, off + per, f"beat-{beat_num:02d}", "B-roll", Path(c["path"]).name))
            off += per
        return wins

    if beat_num == 5 and clips:
        stat = generated[0] if generated else None
        poke = next((c for c in clips if "pokemon" in c.get("filename", "")), None)
        solar = next((c for c in clips if "solar" in c.get("filename", "")), None)
        if stat and poke and solar:
            poke_dur = dur * 0.36
            solar_dur = dur * 0.30
            wins.append(VisualWindow(
                t0, t0 + poke_dur, f"beat-{beat_num:02d}", "Pokémon clip", Path(poke["path"]).name,
            ))
            wins.append(VisualWindow(
                t0 + poke_dur, t0 + poke_dur + solar_dur, f"beat-{beat_num:02d}",
                "community demo clip", Path(solar["path"]).name,
            ))
            wins.append(VisualWindow(
                t0 + poke_dur + solar_dur, t0 + dur, f"beat-{beat_num:02d}",
                "Spire stat", Path(stat["path"]).name,
            ))
            return wins
        if stat and poke:
            poke_dur = dur * 0.48
            wins.append(VisualWindow(
                t0, t0 + poke_dur, f"beat-{beat_num:02d}", "Pokémon clip", Path(poke["path"]).name,
            ))
            wins.append(VisualWindow(
                t0 + poke_dur, t0 + dur, f"beat-{beat_num:02d}", "Spire stat", Path(stat["path"]).name,
            ))
            return wins
        stat_share = 0.32 if stat else 0.0
        clip_total = max(1.0, dur * (1.0 - stat_share))
        poke = next((c for c in clips if "pokemon" in c.get("filename", "")), None)
        others = sorted(
            [c for c in clips if c is not poke],
            key=lambda c: {"carousel-solar.mp4": 0, "carousel-fluid.mp4": 1}.get(Path(c["path"]).name, 99),
        )
        off = t0
        if poke:
            poke_dur = clip_total * 0.55
            wins.append(VisualWindow(
                off, off + poke_dur, f"beat-{beat_num:02d}", "Pokémon clip", Path(poke["path"]).name,
            ))
            off += poke_dur
            rest = clip_total - poke_dur
        else:
            rest = clip_total
        if others and rest > 0:
            per = rest / len(others)
            for c in others:
                wins.append(VisualWindow(
                    off, off + per, f"beat-{beat_num:02d}", "vision clip", Path(c["path"]).name,
                ))
                off += per
        if stat:
            wins.append(VisualWindow(
                off, t0 + dur, f"beat-{beat_num:02d}", "Spire stat", Path(stat["path"]).name,
            ))
        return wins

    if beat_num == 6 and images:
        order = ("safeguard", "fallback", "cyber", "jailbreak")
        ranked = sorted(
            images,
            key=lambda i: next((n for n, k in enumerate(order) if k in i.get("filename", "").lower()), 99),
        )[:3]
        per = dur / len(ranked)
        off = t0
        for img in ranked:
            wins.append(VisualWindow(off, off + per, f"beat-{beat_num:02d}", "safeguard slide", Path(img["path"]).name))
            off += per
        return wins

    if beat_num == 8 and generated:
        slides = generated + [i for i in images if "protein" in i.get("filename", "")]
        per = dur / max(1, len(slides[:2]))
        off = t0
        for s in slides[:2]:
            wins.append(VisualWindow(off, off + per, f"beat-{beat_num:02d}", "access slide", Path(s["path"]).name))
            off += per
        return wins

    if beat_num == 4 and generated and images:
        slides = images[:1] + generated  # table first, stat second
        per = dur / 2
        off = t0
        for s in slides:
            wins.append(VisualWindow(off, off + per, f"beat-{beat_num:02d}", "benchmark slide", Path(s["path"]).name))
            off += per
        return wins

    if beat_num == 10:
        jail = assets / "jailbreak-resistance.png"
        align = assets / "alignment-chart.png"
        specs: list[tuple[Path, float]] = []
        if jail.is_file():
            specs.append((jail, 0.65))
        if align.is_file():
            specs.append((align, 0.35))
        if not specs and images:
            specs = [(Path(images[0]["path"]), 1.0)]
        off = t0
        for path, frac in specs:
            seg_dur = dur * frac
            wins.append(VisualWindow(off, off + seg_dur, f"beat-{beat_num:02d}", "close slide", path.name))
            off += seg_dur
        return wins

    if clips and not generated:
        per = dur / len(clips)
        off = t0
        for c in clips:
            wins.append(VisualWindow(off, off + per, beat_key, "clip", Path(c["path"]).name))
            off += per
        return wins

    if generated and not clips:
        g = generated[0]
        wins.append(VisualWindow(t0, t0 + dur, beat_key, "card", Path(g["path"]).name))
        return wins

    if clips:
        wins.append(VisualWindow(t0, t0 + dur, beat_key, "clip", Path(clips[0]["path"]).name))
        return wins

    return [VisualWindow(t0, t0 + dur, beat_key, "unknown", "none")]


def build_visual_timeline(project: DailySingleProject) -> list[VisualWindow]:
    timeline = json.loads((project.merge_dir / "timeline.json").read_text(encoding="utf-8"))
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    beats = beat_map.get("beats") or {}
    seg_by_id = {row["id"]: row for row in timeline.get("segments", [])}
    assets = project.assets_dir
    out: list[VisualWindow] = []

    for label, seg_dir, beat_num in SEGMENT_ORDER:
        tl_id = label if label in ("00-hook", "99-outro") else f"beat-{beat_num:02d}"
        row = seg_by_id.get(tl_id)
        if not row:
            continue
        start = float(row["start_sec"])
        dur = float(row["duration_sec"])
        if label == "00-hook":
            script_path = project.segment_script("00-hook")
            script = script_path.read_text(encoding="utf-8") if script_path.is_file() else ""
            plan = build_hook_montage_plan(project)
            montage_cues = [c for c in plan.get("cues") or [] if c.get("ok")]
            if montage_cues and script:
                for w in hook_visual_windows(start, dur, script, montage_cues, project=project):
                    out.append(VisualWindow(
                        w["start"], w["end"], w["beat"], w["visual"], w["file"],
                        w.get("section", ""), w.get("script_fragment", ""),
                    ))
            elif (project.segments_dir / "00-hook" / "heygen.mp4").is_file():
                launch = assets / "videos" / "claudeai-launch.mp4"
                split = dur * 0.72
                out.append(VisualWindow(start, start + split, "00-hook", "launch B-roll", "claudeai-launch.mp4", "attention"))
                out.append(VisualWindow(start + split, start + dur, "00-hook", "HeyGen avatar", "heygen.mp4", "bridge"))
            else:
                out.extend(_windows_for_beat("00-hook", None, start, dur, {}, assets, hook_launch=True))
        elif label == "99-outro":
            heygen = project.segments_dir / "99-outro" / "heygen.mp4"
            if heygen.is_file():
                out.append(VisualWindow(start, start + dur, "99-outro", "HeyGen avatar", "heygen.mp4"))
            else:
                out.extend(_windows_for_beat("99-outro", None, start, dur, {}, assets, outro_table=True))
        else:
            spec = beats.get(str(beat_num), {})
            out.extend(_windows_for_beat(tl_id, beat_num, start, dur, spec, assets))
    return out


def visual_at(windows: list[VisualWindow], t: float) -> VisualWindow | None:
    for w in windows:
        if w.start_sec <= t < w.end_sec:
            return w
    return windows[-1] if windows else None


def _windows_overlap_cue(w: VisualWindow, cue: dict[str, Any]) -> bool:
    return w.start_sec < cue["end_sec"] and w.end_sec > cue["start_sec"]


def _score_cue_against_windows(cue: dict[str, Any], windows: list[VisualWindow], *, hook_overview: bool = False) -> tuple[float, VisualWindow | None]:
    mid = (cue["start_sec"] + cue["end_sec"]) / 2
    if hook_overview:
        overview = [w for w in windows if w.beat == "00-hook" and w.section == "overview"]
        if overview:
            best_score = 0.0
            best_win: VisualWindow | None = None
            for w in overview:
                if not _windows_overlap_cue(w, cue):
                    continue
                frag = w.script_fragment or cue["text"]
                s = score_cue_visual(frag, w.file)
                if s > best_score:
                    best_score = s
                    best_win = w
            if best_win:
                return best_score, best_win
    vis = visual_at(windows, mid)
    if not vis:
        return 0.0, None
    text = cue["text"]
    if vis.script_fragment:
        text = vis.script_fragment
    return score_cue_visual(text, vis.file), vis


def validate_display_sync(project: DailySingleProject) -> dict[str, Any]:
    srt_path = project.merge_dir / "final.srt"
    if not srt_path.is_file():
        raise FileNotFoundError(f"Missing {srt_path} — run build-captions first")

    cues = parse_srt(srt_path)
    windows = build_visual_timeline(project)
    rows: list[dict[str, Any]] = []
    fails = 0

    for i, cue in enumerate(cues, 1):
        hook_overview = i == 2 and any(w.section == "overview" for w in windows)
        score, vis = _score_cue_against_windows(cue, windows, hook_overview=hook_overview)
        file = vis.file if vis else "none"
        threshold = HOOK_MONTAGE_MIN_ALIGNMENT if hook_overview else MIN_ALIGNMENT
        ok = score >= threshold
        if not ok:
            fails += 1
        rows.append({
            "cue": i,
            "start_sec": round(cue["start_sec"], 2),
            "end_sec": round(cue["end_sec"], 2),
            "spoken": cue["text"],
            "visual": vis.visual if vis else "?",
            "file": file,
            "beat": vis.beat if vis else "?",
            "alignment": score,
            "ok": ok,
            "hook_montage": hook_overview,
        })

    report = {
        "schema_version": 1,
        "min_alignment": MIN_ALIGNMENT,
        "cues_total": len(rows),
        "cues_pass": len(rows) - fails,
        "cues_fail": fails,
        "pass_rate": round((len(rows) - fails) / max(1, len(rows)), 3),
        "ok": fails == 0,
        "visual_windows": [
            {
                "start": w.start_sec,
                "end": w.end_sec,
                "beat": w.beat,
                "visual": w.visual,
                "file": w.file,
                "section": w.section,
                "script_fragment": w.script_fragment,
            }
            for w in windows
        ],
        "cue_map": rows,
    }
    out = project.merge_dir / "display_sync_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
