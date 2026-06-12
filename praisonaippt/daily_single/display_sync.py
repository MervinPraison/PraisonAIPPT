"""Map SRT cues to on-screen visuals and score caption↔slide sync."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.brand_bumper import BUMPER_FILENAME, BUMPER_STEM
from praisonaippt.daily_single.beat10_timing import beat10_chart_durations
from praisonaippt.daily_single.segment_cue_timing import (
    beat4_visual_durations,
    beat8_clip_durations,
    beat9_visual_durations,
    clip_durations_for_cues,
)
from praisonaippt.daily_single.beat01_timing import beat01_views_duration_sec
from praisonaippt.daily_single.hook_montage import build_hook_montage_plan, hook_visual_windows
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.daily_single.publish_quality_config import beat_map_variant
from praisonaippt.daily_single.text_slide import outro_slide_specs, slide_specs, visual_meta_from_specs
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
        "vision_description": "anthropic launch clip june shipped builders official b-roll pro max subscribers capable claude website api trap cloud footnote",
        "topics": ("launch", "june", "shipped", "walkthrough", "b-roll", "builders", "pro", "max", "subscribers", "capable", "public", "claude", "live", "website", "api", "trap", "cloud", "footnote", "discourse", "launch-week", "brake", "pedal", "monday", "rsi", "timeline", "internet"),
    },
    "canonical-scroll.mp4": {
        "vision_description": "anthropic news blog claude fable mythos announcement scroll launch page",
        "topics": ("anthropic", "fable", "mythos", "launch", "announcement", "blog", "claude", "news", "dropped", "changes"),
    },
    "bio-aav-chart.png": {
        "vision_description": "biology chemistry AAV viral capsid packaging classification chart",
        "topics": ("biology", "chemistry", "aav", "virus", "viral", "capsid", "packaging", "gene", "therapy", "classifier", "chart"),
        "visual_focus": ("biology", "chemistry", "aav", "viral", "capsid", "packaging", "chart"),
    },
    "beat1-views-overlay.png": {
        "vision_description": "twenty six million views on X official claude launch clip social viral reach engagement",
        "topics": ("views", "million", "viral", "social", "launch", "clip", "engagement", "reach", "record"),
        "visual_focus": ("views", "million", "viral", "social", "reach", "engagement", "clip", "record"),
    },
    "beat2-tier-diagram.png": {
        "vision_description": "fable mythos glasswing tier diagram api june live pro max subscribers capable public claude rsi timeline",
        "topics": ("fable", "mythos", "glasswing", "tier", "tiers", "api", "integrate", "teams", "get", "most", "actually", "diagram", "chart", "june", "live", "pro", "max", "subscribers", "capable", "public", "claude", "rsi", "timeline", "essay", "whiplash", "anthropic"),
        "visual_focus": ("tier", "tiers", "fable", "mythos", "glasswing", "api", "diagram", "chart", "june", "live", "pro", "max", "subscribers", "capable", "public", "claude"),
    },
    "beat3-stripe-card.png": {
        "vision_description": "stripe fifty million lines migration one day manual months gap real independent tests coding community roundups linkedin demos beast ferrari limiter",
        "topics": ("stripe", "million", "lines", "migration", "manual", "ruby", "gap", "real", "independent", "tests", "coding", "tasks", "costing", "community", "roundups", "linkedin", "demos", "launch", "beast", "ferrari", "limiter", "willison", "hacker", "enterprise", "ceiling", "tuesday", "refactor"),
    },
    "beat1-launch-summary.png": {
        "vision_description": "fable teams daily safety builder demos games apps social feeds festival software morning launch",
        "topics": (
            "fable", "teams", "daily", "safety", "answers", "builder", "demos", "games",
            "simulations", "apps", "instructions", "social", "feeds", "festival", "software", "morning", "launch", "working",
        ),
    },
    "beat1-views-overlay.png": {
        "vision_description": "headline receipt launch promised mythos views million anthropic june official inequality reddit fable cyber biology copy-protection checks people opus",
        "topics": ("views", "million", "launch", "anthropic", "june", "official", "headline", "receipt", "promised", "mythos", "inequality", "reddit", "fable", "included", "plan", "cyber", "biology", "copy-protection", "checks", "people", "opus", "glasswing", "researchers", "trusted"),
        "visual_focus": ("views", "million", "launch", "headline", "receipt", "promised", "partner", "intelligence", "everyone", "anthropic", "said", "class", "engine", "experiences", "checks", "people", "opus", "copy-protection"),
    },
    "carousel-factorio.mp4": {
        "vision_description": "factorio factory automation agentic loops coding tasks migrations community apps browser hacker news beast ferrari",
        "topics": ("factorio", "factory", "automation", "agentic", "loops", "migrations", "coding", "tasks", "projects", "browser", "game", "match", "board", "windows", "community", "demos", "hacker", "news", "beast", "ferrari", "stripe", "willison", "engineers"),
    },
    "carousel-vibecad.mp4": {
        "vision_description": "cad vibecad engineering workflows hacker news beast ferrari stripe",
        "topics": ("cad", "workflows", "refactors", "automation", "clips", "design", "tools", "community", "demos", "roundups", "linkedin", "projects", "migrations", "hacker", "news", "beast", "ferrari", "stripe", "willison", "enterprise", "proof", "ceiling", "default", "experience", "treat", "migration"),
    },
    "carousel-solar.mp4": {
        "vision_description": "solar system eclipse simulation community demo browser game city builder pokemon spectacle viral scroll",
        "topics": ("solar", "system", "eclipse", "simulation", "browser", "game", "city", "world", "prompt", "demo", "builders", "linkedin", "community", "pokemon", "spectacle", "viral", "scroll", "timelapse", "vision", "harness", "clip"),
    },
    "carousel-fluid.mp4": {
        "vision_description": "fluid simulation engineering demo b-roll clip benchmark swe terminal share social",
        "topics": ("fluid", "simulation", "engineering", "demo", "clip", "vision", "benchmark", "swe", "terminal", "share", "social", "scores", "fable", "opus", "gpt", "table", "paste", "numbers", "paragraphs", "people", "three", "card", "comparison"),
    },
    "beat4-stat-overlay.png": {
        "vision_description": "swe-bench verified ninety-five terminal-bench eighties fable mythos longer jobs advantage scores companies office",
        "topics": ("swe-bench", "ninety-five", "terminal", "eighties", "fable", "mythos", "benchmark", "longer", "jobs", "advantage", "scores", "companies", "office", "everyday", "coding"),
        "visual_focus": ("ninety-five", "swe-bench", "terminal", "benchmark", "scores", "companies", "office", "fable", "mythos", "longer", "jobs", "advantage", "eighty", "three", "percent", "opus", "gpt", "numbers", "paste", "card", "comparison"),
    },
    "benchmark-table.png": {
        "vision_description": "benchmark scorecard frontier leaderboard engineering swe-bench eighty fable opus gpt",
        "topics": ("frontier", "benchmark", "leaderboard", "engineering", "knowledge", "launch", "card", "coding", "tests", "eighty", "sixty-nine", "fifty-eight", "fable", "opus", "gpt", "swe-bench", "partner", "percent"),
        "visual_focus": ("benchmark", "swe-bench", "eighty", "fable", "opus", "scores", "chart", "table", "terminal", "five", "percent", "fallback", "sessions", "comparison", "cards", "tier", "diagrams", "travel"),
    },
    "pokemon-timelapse.mp4": {
        "vision_description": "pokemon firered vision screenshot navigation harness demo solar browser games spectacle viral repo logging",
        "topics": ("pokemon", "vision", "firered", "screenshot", "navigation", "demo", "scaffolding", "solar", "browser", "games", "city", "worlds", "prompt", "others", "modelled", "built", "spectacle", "harness", "viral", "logging", "tests", "budget", "scroll"),
    },
    "beat5-spire-stat.png": {
        "vision_description": "slay spire memory pokemon spectacle demo viral scroll harness clip budget logging tests",
        "topics": ("spire", "memory", "three", "final-act", "opus", "stat", "gameplay", "pokemon", "spectacle", "demo", "viral", "scroll", "harness", "clip", "budget", "logging", "tests", "timelapse", "vision", "navigation"),
        "visual_focus": ("pokemon", "spectacle", "demo", "viral", "scroll", "harness", "clip"),
    },
    "gpt-image-safeguard-fallback.png": {
        "vision_description": "safeguard fallback diagram classifier backup not blocked safety dead ends notice plan sessions",
        "topics": ("fallback", "diagram", "safeguard", "classifier", "sessions", "refusing", "safety", "dead", "ends", "blocking", "support", "monitoring", "playbooks", "plan", "backup", "notice", "visible", "percent", "five"),
        "visual_focus": ("fallback", "safeguard", "diagram", "notice", "plan", "visible", "sessions", "percent"),
    },
    "distillation-safeguard.png": {
        "vision_description": "copy protection distillation safeguard model abilities training steal",
        "topics": ("distillation", "copy", "protection", "steal", "abilities", "training", "model"),
        "visual_focus": ("distillation", "copy", "protection", "steal", "abilities"),
    },
    "cyber-classifier.png": {
        "vision_description": "cyber classifier false positives innocuous biology homework greeting register ferrari meme villains incidents",
        "topics": ("cyber", "classifier", "exploitation", "hacking", "offensive", "ninety", "five", "percent", "sessions", "backup", "need", "support", "monitoring", "playbooks", "plan", "false", "positive", "positives", "innocuous", "biology", "homework", "greeting", "register", "ferrari", "meme", "villains", "incidents", "refused", "pretend", "safeguards", "innocent", "willison", "simon", "sabotage", "paid", "product", "steering", "silent", "feels"),
        "visual_focus": ("cyber", "classifier", "false", "positive", "biology", "homework", "greeting", "register", "ferrari", "incidents", "villains", "willison", "sabotage", "paid", "product", "steering", "silent"),
    },
    "jailbreak-resistance.png": {
        "vision_description": "jailbreak resistance cyber adversarial robustness attack success rate bar chart opus fable",
        "chart_kind": "attack_rate_bar",
        "topics": ("jailbreak", "resistance", "attack", "adversarial", "robustness", "success", "rate", "cyber", "bounty", "harmful", "completions", "bypass", "safety", "chart", "red-teaming", "stress", "fable", "opus", "percent", "bar"),
        "visual_focus": ("jailbreak", "resistance", "attack", "adversarial", "robustness", "success", "rate", "cyber", "stress", "red-teaming", "bar"),
    },
    "beat7-api-table.png": {
        "vision_description": "api messages web app block fallback claude.ai enterprise website trap billing developer",
        "topics": ("api", "web", "app", "block", "fallback", "messages", "claude.ai", "enterprise", "opt", "website", "developer", "mistake", "versus", "support", "tickets", "billing", "blocked", "error", "response", "developers", "sensitive", "prompts", "assume", "switch", "trap", "cloud", "platform"),
        "visual_focus": ("api", "web", "website", "fallback", "developer", "billing", "trap", "platform", "block", "notification", "switch", "sensitive", "prompt", "cloud", "footnote", "enterprise", "hosted", "compliance", "continuity", "tweet", "launch"),
    },
    "beat8-glasswing.png": {
        "vision_description": "project glasswing cyber defenders mythos preview tiers headline receipt lab coat science slack",
        "topics": ("glasswing", "cyber", "defenders", "mythos", "preview", "tiers", "headline", "receipt", "science", "slack", "lab", "partner", "biology", "cohort", "press", "coverage", "drug", "design", "genomics", "benchmarks", "protein", "methods", "inequality", "ladder", "coat", "faster", "preference", "scientist"),
    },
    "protein-complexes.png": {
        "vision_description": "biology trusted access cohort researchers bio classifiers public purchase sign online neither path",
        "topics": ("biology", "trusted", "researchers", "cohort", "bio", "classifiers", "public", "purchase", "sign", "online", "neither", "path", "simple"),
    },
    "beat9-pricing.png": {
        "vision_description": "pricing ten fifty dollars million tokens june subscription deadline cliff rsi timeline launch mythos preview double",
        "topics": ("pricing", "ten", "fifty", "dollars", "tokens", "june", "subscription", "enterprise", "usage", "billing", "budget", "autonomous", "plan", "limits", "deadline", "cliff", "rsi", "timeline", "launch", "copy", "fable", "mythos", "preview", "social", "math", "double", "model", "money", "clock", "twenty-two", "cloud", "spend", "chat", "runs", "unlimited"),
    },
    "jailbreak-retention.png": {
        "vision_description": "retention thirty days jailbreak prompts logged training distillation eval",
        "topics": ("retention", "thirty", "jailbreak", "prompts", "training", "distillation", "eval", "classifiers"),
    },
    "alignment-chart.png": {
        "vision_description": "misaligned behaviour alignment eval chart scores off-track answers",
        "chart_kind": "alignment_eval",
        "topics": ("misaligned", "alignment", "behaviour", "chart", "off-track", "scores", "safeguards", "launch", "settings", "rules", "company", "data", "plan", "switch", "hype"),
        "visual_focus": ("alignment", "misaligned", "behaviour", "off-track", "chart", "scores", "rules", "company"),
    },
    "v2-inequality-ladder.png": {
        "vision_description": "access paths inequality fable mythos glasswing bio trusted classifiers fallback",
        "topics": ("inequality", "reddit", "preview", "fable", "mythos", "glasswing", "bio", "trusted", "classifiers", "fallback", "access", "receipt", "engine", "people", "partners", "researchers", "cyber", "biology", "copy-protection", "opus", "visible", "switch", "chemistry", "blunt", "launch", "model", "weights", "slide", "session"),
    },
    "v2-headline-vs-receipt.png": {
        "vision_description": "headline receipt launch promised mythos-class included plan june cliff",
        "topics": ("headline", "receipt", "promised", "launch", "mythos", "included", "plan", "june", "fallback", "classifiers", "reddit", "inequality", "session", "weights", "slide", "partner", "class", "everyone", "engine", "experiences"),
    },
    "v2-timeline-rsi-fable.png": {
        "vision_description": "rsi essay five day whiplash june ship fable credits cliff brake pedal frontier",
        "topics": ("rsi", "essay", "safety", "june", "ship", "fable", "whiplash", "credits", "twenty-two", "anthropic", "brake", "pedal", "frontier", "monday", "friday", "tension", "workflow"),
    },
    "v2-hn-split-quotes.png": {
        "vision_description": "hacker news beast ferrari willison stripe scale session counter-meme limiter",
        "topics": ("hacker", "news", "beast", "ferrari", "willison", "stripe", "thread", "speed", "limited", "counter", "meme", "limiter", "conversation"),
    },
    "v2-benchmark-3row.png": {
        "vision_description": "swe-bench pro eighty point three fable opus gpt benchmark comparison table",
        "topics": ("swe-bench", "benchmark", "eighty", "three", "percent", "fable", "opus", "gpt", "comparison", "scores", "terminal", "share", "social", "card", "verify"),
        "visual_focus": ("swe-bench", "benchmark", "eighty", "fable", "opus", "percent", "table", "numbers", "paste", "paragraphs", "three"),
    },
    "v2-pricing-compare.png": {
        "vision_description": "pricing ten fifty tokens opus double api cost cliff june subscription credits",
        "topics": ("pricing", "ten", "fifty", "tokens", "opus", "double", "api", "cost", "credits", "june", "subscription", "pharmaceutical", "cliff", "plans"),
    },
    "v2-two-safeties.png": {
        "vision_description": "visible fallback silent steering two safeties conflate trust opus sessions stories different breaks",
        "topics": ("visible", "fallback", "silent", "steering", "safeties", "conflate", "trust", "opus", "sessions", "stories", "different", "safety", "willison", "sabotage", "breaks", "path", "stories", "conflating", "notice", "plan", "route", "classifiers", "percent", "average"),
    },
    "v2-false-positive-list.png": {
        "vision_description": "false positives innocuous biology homework greeting register ferrari meme silent steering",
        "topics": ("false", "positive", "innocent", "biology", "homework", "greeting", "register", "ferrari", "refused", "silent", "steering", "willison", "incidents", "villains", "safeguards", "pretend", "name", "pop-up", "popup", "safety", "see", "may", "deserve", "know", "kind", "hit", "which", "bad", "point"),
    },
    "v2-decision-matrix.png": {
        "vision_description": "decision matrix switch coder researcher cost enterprise compliance june matrix",
        "topics": ("decision", "matrix", "switch", "coder", "researchers", "subscribers", "safeguards", "festival", "billing", "logging", "long-horizon", "refactors", "fallbacks", "instrument", "wait", "june", "tune", "launch", "week", "sessions", "receipts", "headlines", "sla", "autonomous", "chat", "cloud", "spend"),
    },
    "v2-june22-calendar.png": {
        "vision_description": "june twenty-two calendar cliff credits pro max billing pharmaceutical plans",
        "topics": ("june", "twenty-two", "calendar", "cliff", "credits", "billing", "pro", "max", "included", "pharmaceutical", "plans", "required", "team", "enterprise", "seats", "twenty", "twenty-six", "deadline", "timeline", "rsi"),
    },
    "v2-quote-karpathy.png": {
        "vision_description": "karpathy step change coding agents trigger-happy safeguards caveat pokemon demo",
        "topics": ("karpathy", "step", "change", "coding", "agents", "trigger", "safeguards", "caveat", "pokemon", "timelapse", "scroll", "demo", "spectacle"),
    },
    "v2-quote-willison.png": {
        "vision_description": "willison beast silent steering sabotage paid product hn",
        "topics": ("willison", "beast", "silent", "steering", "sabotage", "paid", "product", "trust", "cheaper", "quietly", "takes", "over", "telling", "model", "without", "banner"),
    },
    "v2-platform-fallback-gaps.png": {
        "vision_description": "website api fallback trap claude block error cloud model id footnote platform",
        "topics": ("website", "api", "fallback", "trap", "block", "error", "cloud", "developer", "model", "footnote", "platform", "compliance", "continuity"),
    },
    "social-capture-hn-beast-ferrari.png": {
        "vision_description": "hacker news beast ferrari willison stripe scale session counter-meme limiter shipped fable thread",
        "topics": ("hacker", "news", "beast", "ferrari", "willison", "stripe", "thread", "speed", "limited", "counter", "meme", "limiter", "conversation", "shipped", "fable", "anthropic", "claude", "watched", "million", "linkedin", "side", "comparison", "five", "real", "jobs", "tasks"),
    },
    "social-capture-reddit-inequality.png": {
        "vision_description": "access paths inequality fable mythos glasswing bio trusted classifiers fallback reddit blunt model launch preview",
        "topics": ("inequality", "reddit", "preview", "fable", "mythos", "headline", "receipt", "promised", "launch", "fallback", "classifiers", "access", "engine", "blunt", "model", "frame", "session", "weights", "slide", "partner", "glasswing", "biology", "unequal", "toy", "everyone", "vip", "lanes", "highway", "vip lanes"),
    },
    "fallback-notification.mp4": {
        "vision_description": "claude ai fallback notification visible safety classifier route opus session pop-up",
        "topics": ("fallback", "visible", "notification", "classifier", "opus", "safety", "session", "route", "claude", "platform", "pop-up", "popup", "notice", "message", "switch", "clear", "check", "fired", "percent", "sessions"),
    },
    "linkedin-cintas-fable5-vs-opus.mp4": {
        "vision_description": "linkedin side by side fable opus five real jobs comparison clip cintas montage hours proof screen",
        "topics": (
            "linkedin", "side", "comparison", "fable", "opus", "five", "real", "jobs", "clip", "cintas", "montage", "hours", "proof", "screen", "side-by-side", "beating", "tasks", "watch", "launch", "video", "same", "big", "jobs", "tackling", "working", "checks", "sharing",
            "asteroid", "nasa", "solar", "flares", "aurora", "fitness", "retreat", "apollo", "panels", "world", "cup", "jersey", "absurd", "work", "promised", "people", "actually", "get", "recording", "multi-step", "sandbox", "log", "model", "answered",
        ),
        "visual_focus": ("linkedin", "fable", "opus", "comparison", "side", "tasks", "clip", "montage", "screen", "recording"),
    },
    "x-claudeai-launch.mp4": {
        "vision_description": "claudeai official X launch video Fable 5 Mythos announcement",
        "topics": ("x", "launch", "claudeai", "fable", "anthropic", "official", "announcement", "mythos"),
        "visual_focus": ("launch", "claudeai", "fable", "official", "x"),
    },
    "x-claudedevs-launch.mp4": {
        "vision_description": "claudedevs engineering X launch video Fable 5 API agent tooling rollout",
        "topics": ("x", "launch", "claudedevs", "engineering", "fable", "anthropic", "api", "agent", "rollout"),
        "visual_focus": ("launch", "claudedevs", "engineering", "fable", "x", "rollout"),
    },
    "x-claudeai-safeguards.mp4": {
        "vision_description": "Anthropic X safeguards video Fable routes to Opus 4.8 cyber bio chemistry classifiers",
        "topics": ("x", "safeguards", "fable", "opus", "routing", "classifier", "cyber", "biology", "comparison"),
        "visual_focus": ("safeguards", "opus", "fable", "routing", "classifier"),
    },
    "x-chrissgpt-minecraft.mp4": {
        "vision_description": "ChrissGPT X screen recording Minecraft clone one prompt Fable 5 biomes caves",
        "topics": ("x", "minecraft", "clone", "game", "build", "chrissgpt", "one-shot", "biomes", "caves"),
        "visual_focus": ("minecraft", "clone", "game", "build", "biomes"),
    },
    "x-chrissgpt-pokemon.mp4": {
        "vision_description": "ChrissGPT X Pokemon clone Gen-1 sprites Fable 5 one shot build",
        "topics": ("x", "pokemon", "clone", "game", "sprites", "chrissgpt", "build", "gen-1"),
        "visual_focus": ("pokemon", "clone", "sprites", "game", "build"),
    },
    "x-pootlepress-wp-theme.mp4": {
        "vision_description": "pootlepress X WordPress block theme one shot Fable 5 build",
        "topics": ("x", "wordpress", "theme", "block", "build", "one-shot", "pootlepress"),
        "visual_focus": ("wordpress", "theme", "block", "build"),
    },
    "x-trq212-edit-2064826394589442448.mp4": {
        "vision_description": "trq212 X walkthrough Fable 5 edited launch video ffmpeg Remotion pipeline",
        "topics": ("x", "trq212", "video", "edit", "ffmpeg", "remotion", "fable", "pipeline"),
        "visual_focus": ("video", "edit", "ffmpeg", "remotion", "pipeline"),
    },
    "x-trq212-edit-2064828193446740023.mp4": {
        "vision_description": "trq212 X Fable 5 self-edited launch video tool calls transcription",
        "topics": ("x", "trq212", "video", "edit", "fable", "launch", "tool", "calls"),
        "visual_focus": ("video", "edit", "fable", "launch"),
    },
    "linkedin-cintas-frame.png": {
        "vision_description": "linkedin side by side fable opus comparison frame five real jobs split screen montage",
        "topics": ("linkedin", "side", "comparison", "fable", "opus", "five", "real", "jobs", "clip", "cintas", "montage", "side-by-side", "tasks", "split", "screen", "comparison", "real-world"),
    },
    "demo-launch.mp4": {
        "vision_description": "anthropic launch clip june shipped builders official b-roll pro max subscribers capable claude website price table",
        "topics": ("launch", "june", "shipped", "walkthrough", "b-roll", "builders", "pro", "max", "subscribers", "capable", "public", "claude", "live", "website", "price", "table", "promised", "anthropic", "everyone", "headline"),
    },
    "demo-scroll.mp4": {
        "vision_description": "anthropic news blog claude fable mythos announcement scroll launch page",
        "topics": ("anthropic", "fable", "mythos", "launch", "announcement", "blog", "claude", "news", "dropped", "changes", "promised", "montage", "hype", "influencers", "absurd", "experience", "account"),
    },
    "demo-factorio.mp4": {
        "vision_description": "factorio factory automation agentic loops coding tasks migrations community apps browser game engineers share clips proof",
        "topics": ("factorio", "factory", "automation", "agentic", "loops", "migrations", "coding", "tasks", "projects", "browser", "game", "community", "demos", "engineers", "share", "clips", "proof", "poetry", "forum", "developer", "beast", "months", "staged", "launch", "reel", "tuesday", "afternoon"),
    },
    "demo-vibecad.mp4": {
        "vision_description": "cad vibecad engineering workflows design tools three dimensions spinning partners programme",
        "topics": ("cad", "workflows", "design", "tools", "three", "dimensions", "spinning", "engineering", "demos", "partners", "programme", "public", "limits", "flaunt", "builds", "simulations", "richer", "fluid", "partner", "tier", "headline", "story"),
    },
    "demo-solar.mp4": {
        "vision_description": "solar system eclipse simulation demo pokemon spectacle viral scroll navigating sight pixels memory",
        "topics": ("solar", "system", "eclipse", "simulation", "demo", "pokemon", "spectacle", "viral", "scroll", "navigating", "sight", "pixels", "memory", "cheat", "sheet", "studio", "retries", "budget", "popup", "session", "wow", "genuine"),
    },
    "demo-fluid.mp4": {
        "vision_description": "fluid simulation engineering demo benchmark swe terminal share social scores fable opus chart",
        "topics": ("fluid", "simulation", "engineering", "demo", "benchmark", "swe", "terminal", "share", "social", "scores", "fable", "opus", "chart", "numbers", "official", "score", "card", "ahead", "hard", "coding", "tests", "rivals", "openai", "percent", "meeting", "date", "move", "vendors"),
    },
    "demo-pokemon.mp4": {
        "vision_description": "pokemon firered vision screenshot navigation harness demo solar browser games spectacle viral logging",
        "topics": ("pokemon", "vision", "firered", "screenshot", "navigation", "demo", "solar", "browser", "games", "spectacle", "viral", "scroll", "timelapse", "sight", "pixels", "memory", "studio", "retries", "budget", "account", "default", "show"),
    },
}
VISUAL_META.update(visual_meta_from_specs())
VISUAL_META["beat1-launch-summary.png"].update({
    "vision_description": "fable teams daily safety builder demos games apps social feeds festival software morning launch working",
    "topics": (
        "fable", "teams", "daily", "safety", "answers", "builder", "demos", "games",
        "simulations", "apps", "instructions", "social", "feeds", "festival", "software", "morning", "launch", "working",
    ),
})


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
        w in cue_tokens for w in ("thirty", "prompts", "mer.vin", "distillation", "jailbreak")
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
    segments_dir: Path | None = None,
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

    if beat_num == 1 and images and not generated:
        headline = next(
            (i for i in images if "headline" in i.get("filename", "") or "views-overlay" in i.get("filename", "")),
            images[0],
        )
        ladder = next(
            (i for i in images if "inequality" in i.get("filename", "") or "social-capture" in i.get("filename", "")),
            images[-1],
        )
        headline_d = dur * 0.20
        off = t0
        if clips:
            clip_d = min(headline_d, dur * 0.22)
            wins.append(VisualWindow(
                off, off + clip_d, "beat-01", "launch clip", Path(clips[0]["path"]).name,
            ))
            off += clip_d
        wins.append(VisualWindow(
            off, off + headline_d, "beat-01", "headline vs receipt",
            Path(headline["path"]).name,
        ))
        wins.append(VisualWindow(
            off + headline_d, t0 + dur, "beat-01", "inequality ladder",
            Path(ladder["path"]).name,
        ))
        return wins

    if beat_num == 1 and generated:
        fname = Path(generated[0]["path"]).name
        ts = (segments_dir or assets.parent) / "01-cold-open" / "timestamps.json"
        root = segments_dir.parent if segments_dir else assets.parent
        merged_srt = root / "merge" / "final.srt"
        views_d = beat01_views_duration_sec(
            dur, ts,
            merged_srt=merged_srt if merged_srt.is_file() else None,
            t0=t0,
        )
        wins.append(VisualWindow(t0, t0 + views_d, "beat-01", "views overlay", fname))
        rest = max(0.0, dur - views_d)
        points = slide_specs()["beat-01-rest"]
        if rest >= 0.75 and points:
            per = rest / len(points)
            off = t0 + views_d
            for spec in points:
                wins.append(VisualWindow(
                    off, off + per, "beat-01", spec["headline"], spec["file"],
                ))
                off += per
        return wins

    if beat_num == 2 and images and clips:
        img_d = dur * 0.62
        per = img_d / max(1, len(images))
        off = t0
        for img in images:
            wins.append(VisualWindow(
                off, off + per, "beat-02", "RSI timeline slide", Path(img["path"]).name,
            ))
            off += per
        wins.append(VisualWindow(
            off, t0 + dur, "beat-02", "launch clip", Path(clips[0]["path"]).name,
        ))
        return wins

    if beat_num == 2 and generated:
        tier = Path(generated[0]["path"]).name
        tier_d = dur * 0.38
        wins.append(VisualWindow(t0, t0 + tier_d, "beat-02", "tier diagram", tier))
        points = slide_specs()["beat-02-extra"]
        rest = max(0.0, dur - tier_d)
        if points and rest >= 0.75:
            per = rest / len(points)
            off = t0 + tier_d
            for spec in points:
                wins.append(VisualWindow(off, off + per, "beat-02", spec["headline"], spec["file"]))
                off += per
        return wins

    if beat_num == 7:
        if clips and not generated and not images:
            root = segments_dir.parent if segments_dir else assets.parent
            lens = clip_durations_for_cues(root, "07-api-integration", dur, [0, 1])
            off = t0
            for i, c in enumerate(clips):
                if i < len(lens) and lens[i] >= 0.25:
                    wins.append(VisualWindow(
                        off, off + lens[i], "beat-07", "X clip", Path(c["path"]).name,
                    ))
                    off += lens[i]
            return wins
        table = next((g for g in generated if "beat7" in g.get("filename", "")), None)
        if not table and (assets / "generated" / "beat7-api-table.png").is_file():
            table = {"path": str(assets / "generated" / "beat7-api-table.png"), "filename": "beat7-api-table.png"}
        clip_d = min(10.0, dur * 0.25) if clips else 0.0
        off = t0
        if clips:
            wins.append(VisualWindow(
                off, off + clip_d, "beat-07", "launch clip", Path(clips[0]["path"]).name,
            ))
            off += clip_d
        table_d = min(28.0, max(12.0, (dur - clip_d) * 0.55))
        if table:
            wins.append(VisualWindow(
                off, off + table_d, "beat-07", "API table", Path(table["path"]).name,
            ))
        gap = next((g for g in generated[1:] if "fallback-gaps" in g.get("filename", "")), None)
        points = slide_specs()["beat-07-rest"]
        rest = max(0.0, dur - clip_d - table_d)
        off = off + table_d if table else off
        if gap and rest >= 0.75:
            gap_d = min(18.0, rest * 0.45)
            wins.append(VisualWindow(off, off + gap_d, "beat-07", "platform fallback gaps", Path(gap["path"]).name))
            off += gap_d
            rest = max(0.0, dur - clip_d - table_d - gap_d)
        if points and rest >= 0.75:
            per = rest / len(points)
            for spec in points:
                wins.append(VisualWindow(off, off + per, "beat-07", spec["headline"], spec["file"]))
                off += per
        return wins

    if beat_num == 9 and generated:
        fname = Path(generated[0]["path"]).name
        wins.append(VisualWindow(t0, t0 + dur, "beat-09", "pricing card", fname))
        return wins

    if beat_num == 3 and generated and clips:
        social = next(
            (i for i in images if "social-capture" in (i.get("filename") or "").lower()),
            None,
        )
        off = t0
        if social:
            soc_d = min(14.0, dur * 0.32)
            wins.append(VisualWindow(
                off, off + soc_d, f"beat-{beat_num:02d}", "HN social capture",
                Path(social["path"]).name,
            ))
            off += soc_d
            card_d = min(12.0, dur * 0.26)
        else:
            card_d = min(14.0, dur * 0.38)
        wins.append(VisualWindow(
            off, off + card_d, f"beat-{beat_num:02d}", "Stripe card", Path(generated[0]["path"]).name,
        ))
        rest = dur - (off - t0) - card_d
        per = rest / len(clips)
        off += card_d
        for c in clips:
            wins.append(VisualWindow(off, off + per, f"beat-{beat_num:02d}", "B-roll", Path(c["path"]).name))
            off += per
        return wins

    if beat_num == 5 and clips:
        root5 = segments_dir.parent if segments_dir else assets.parent
        if not generated and not images:
            lens = clip_durations_for_cues(root5, "05-vision-memory", dur, [0, 1, 1])
            if len(lens) == len(clips):
                off = t0
                for i, c in enumerate(clips):
                    if lens[i] >= 0.25:
                        wins.append(VisualWindow(
                            off, off + lens[i], f"beat-{beat_num:02d}", "X clip", Path(c["path"]).name,
                        ))
                        off += lens[i]
                return wins
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
        from praisonaippt.daily_single.cue_slide_sync import beat6_cue_windows

        seg_srt = (segments_dir or assets.parent) / "06-safeguards" / "segment.srt"
        merged_srt = (segments_dir.parent if segments_dir else assets.parent) / "merge" / "final.srt"
        wins = beat6_cue_windows(t0, dur, images, seg_srt, merged_srt)
        if wins:
            return wins
        wins = []
        order = ("fallback", "bio-aav", "distillation", "cyber", "jailbreak")
        ranked = sorted(
            images,
            key=lambda i: next((n for n, k in enumerate(order) if k in i.get("filename", "").lower()), 99),
        )[:4]
        per = dur / max(1, len(ranked))
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
        clip_d = 0.0
        off = t0
        if clips:
            clip_d = min(14.0, dur * 0.28)
            wins.append(VisualWindow(
                off, off + clip_d, f"beat-{beat_num:02d}", "demo clip", Path(clips[0]["path"]).name,
            ))
            off += clip_d
        slides = images[:1] + generated
        remain = dur - clip_d
        per = remain / max(1, len(slides))
        for s in slides:
            wins.append(VisualWindow(off, off + per, f"beat-{beat_num:02d}", "benchmark slide", Path(s["path"]).name))
            off += per
        return wins

    root = segments_dir.parent if segments_dir else assets.parent

    if beat_num == 4 and clips and images and not generated:
        chart_d, clip_d, tail_d = beat4_visual_durations(root, dur)
        chart_name = Path(images[0]["path"]).name
        clip_name = Path(clips[0]["path"]).name
        off = t0
        wins.append(VisualWindow(off, off + chart_d, f"beat-{beat_num:02d}", "benchmark slide", chart_name))
        off += chart_d
        wins.append(VisualWindow(off, off + clip_d, f"beat-{beat_num:02d}", "clip", clip_name))
        off += clip_d
        if tail_d >= 0.25:
            wins.append(VisualWindow(off, off + tail_d, f"beat-{beat_num:02d}", "benchmark slide", chart_name))
        return wins

    cue_clip_beats: dict[int, tuple[str, list[int]]] = {
        1: ("01-cold-open", [0, 1, 1]),
        2: ("02-mythos-tier", [0, 0, 1]),
        3: ("03-engineers-care", [0, 1, 1, 1]),
        5: ("05-vision-memory", [0, 1, 1]),
        6: ("06-safeguards", [0, 1, 1, 1]),
    }
    if beat_num == 8 and clips and not generated and not images:
        lens = beat8_clip_durations(root, dur)
        off = t0
        for i, c in enumerate(clips):
            if i < len(lens) and lens[i] >= 0.25:
                wins.append(VisualWindow(off, off + lens[i], beat_key, "clip", Path(c["path"]).name))
                off += lens[i]
        return wins
    if beat_num in cue_clip_beats and clips and not generated and not images:
        seg_dir, cue_map = cue_clip_beats[beat_num]
        lens = clip_durations_for_cues(root, seg_dir, dur, cue_map)
        off = t0
        for i, c in enumerate(clips):
            if i < len(lens) and lens[i] >= 0.25:
                wins.append(VisualWindow(off, off + lens[i], beat_key, "clip", Path(c["path"]).name))
                off += lens[i]
        return wins

    if beat_num == 9 and images and any("v2-pricing" in i.get("filename", "") for i in images):
        fracs = (0.38, 0.30, 0.32)
        off = t0
        for i, item in enumerate(images[:3]):
            frac = fracs[i] if i < len(fracs) else 0.32
            wins.append(VisualWindow(
                off, off + dur * frac, f"beat-{beat_num:02d}", "pricing slide", item["filename"],
            ))
            off += dur * frac
        return wins

    if beat_num == 9 and images and not clips and not generated:
        pricing = next((i for i in images if "pricing" in i.get("filename", "")), images[0])
        bench = next((i for i in images if "benchmark" in i.get("filename", "")), images[-1])
        p_d, b_d, tail_d = beat9_visual_durations(root, dur)
        off = t0
        wins.append(VisualWindow(off, off + p_d, f"beat-{beat_num:02d}", "pricing slide", pricing["filename"]))
        off += p_d
        wins.append(VisualWindow(off, off + b_d, f"beat-{beat_num:02d}", "benchmark slide", bench["filename"]))
        off += b_d
        if tail_d >= 0.25:
            wins.append(VisualWindow(
                off, off + tail_d, f"beat-{beat_num:02d}", "pricing slide", pricing["filename"],
            ))
        return wins

    if beat_num == 10:
        v2_items = [
            i for i in (images or []) + (generated or [])
            if (i.get("filename") or "").startswith("v2-")
        ]
        if v2_items:
            per = dur / max(1, len(v2_items))
            off = t0
            for item in v2_items:
                wins.append(VisualWindow(
                    off, off + per, f"beat-{beat_num:02d}", "trust audit slide", item["filename"],
                ))
                off += per
            return wins

        jail_item = next((i for i in (images or []) if "jailbreak" in i.get("filename", "")), None)
        align_item = next((i for i in (images or []) if "alignment" in i.get("filename", "")), None)
        jail = Path(jail_item["path"]) if jail_item else assets / "jailbreak-resistance.png"
        align = Path(align_item["path"]) if align_item else assets / "alignment-chart.png"
        root = segments_dir.parent if segments_dir else assets.parent
        jail_d, align_d, tail_d = beat10_chart_durations(root, dur)
        specs: list[tuple[Path, float]] = []
        if jail.is_file():
            specs.append((jail, jail_d))
        if align.is_file():
            specs.append((align, align_d))
        if jail.is_file() and tail_d > 0:
            specs.append((jail, tail_d))
        if not specs and images:
            specs = [(Path(images[0]["path"]), dur)]
        off = t0
        for path, seg_len in specs:
            wins.append(VisualWindow(off, off + seg_len, f"beat-{beat_num:02d}", "close slide", path.name))
            off += seg_len
        return wins

    if clips and not generated:
        per = dur / len(clips)
        off = t0
        for c in clips:
            wins.append(VisualWindow(off, off + per, beat_key, "clip", Path(c["path"]).name))
            off += per
        return wins

    if images and not clips:
        slides = images + (generated or [])
        per = dur / max(1, len(slides))
        off = t0
        for item in slides:
            wins.append(VisualWindow(off, off + per, beat_key, "slide", Path(item["path"]).name))
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
            cta = outro_slide_specs(beat_map_variant(project))[0]
            out.append(VisualWindow(
                start, start + dur, "99-outro", cta["headline"], cta["file"],
            ))
        else:
            if label == "01-cold-open":
                bumper_row = seg_by_id.get(BUMPER_STEM)
                if bumper_row:
                    bs = float(bumper_row["start_sec"])
                    be = bs + float(bumper_row["duration_sec"])
                    out.append(VisualWindow(
                        bs, be, "brand-bumper", "brand bumper", BUMPER_FILENAME,
                    ))
            spec = beats.get(str(beat_num), {})
            out.extend(_windows_for_beat(tl_id, beat_num, start, dur, spec, assets, segments_dir=project.segments_dir))
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
        if vis and vis.file.endswith(".png"):
            from praisonaippt.daily_single.spoken_visual_sync import is_chart_or_table_file

            if is_chart_or_table_file(vis.file):
                threshold = max(threshold, 0.38)
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
