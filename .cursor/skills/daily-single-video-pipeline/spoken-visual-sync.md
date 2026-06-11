# Spoken ↔ visual sync workflow

Use after **assemble-beats** when narration must match what is on screen at every slide change (not just cue midpoints). Required for cue-aligned beats (beat-06 safeguards) and beat-01 views timing.

**Pilot:** `examples/videos/anthropic-claude-fable-5-mythos-5/` · **178 s regression:** biology chart ends before copy-protection speech.

## Pass bar

`merge/spoken_visual_sync_report.json` → `"ok": true`:

| Check | Meaning |
|-------|---------|
| `montage_*` | Hook overview fragments inline with hero slides |
| `windows_*` | Full slide windows: worst overlapping cue must match on-screen asset |
| `charts_*` | Chart/table slides: plain-language + topic alignment |
| `coverage_*` | Spoken chart/fact lines have a matching slide |
| `plain_language_ok` | Audience-language rules |

CLI summary:

```bash
daily-single -p $PROJECT validate-spoken-visual
# PASS: montage 5/5, windows 36/36, charts 15/15, coverage 16/16, plain_language=True
```

Also run `validate-display` (per-cue midpoint ≥0.35) and pytest (below).

## Rebuild order (cue-aligned assembly)

When `final.srt` drives slide durations (beat-01 views overlay, beat-06 cue windows), **captions before assembly**:

```bash
zsh -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate test && cd /path/to/praisonaippt"
PROJECT=examples/videos/<slug>

daily-single -p $PROJECT build-captions    # merge/final.srt — must exist first
daily-single -p $PROJECT assemble-beats    # uses final.srt + timeline t0
daily-single -p $PROJECT validate-display
daily-single -p $PROJECT validate-spoken-visual
pytest tests/test_cue_slide_sync.py tests/test_spoken_visual_sync.py -q
```

Optional pixel proof:

```bash
daily-single -p $PROJECT audit-visual --interval 5 --force
```

Helper script: [scripts/run-spoken-visual-gate.sh](scripts/run-spoken-visual-gate.sh)

**First cold build** (no `final.srt` yet): `assemble-beats` → `build-captions` once, then re-run **build-captions → assemble-beats** for cue sync.

## Multi-agent validation (recommended after fixes)

Run **before** declaring done when fixing a reported A/V mismatch (e.g. chart on screen while unrelated speech).

| Agent | Task |
|-------|------|
| `explore` (readonly) | Read `merge/timeline.json`, `merge/spoken_visual_sync_report.json`, segment SRT/scripts; confirm global time (e.g. 178 s) → expected slide + cue text |
| `generalPurpose` (readonly) | Review validator/assembler changes in `cue_slide_sync.py`, `spoken_visual_sync.py`, `assemble.py`; flag false positives vs real regressions |
| Parent | Apply fixes, re-run rebuild order above, spot-check `final.mp4` at failing timestamp |

Do **not** parallelise duplicate `validate-spoken-visual` or `audit-visual` runs (API cost).

## Root-cause patterns (Fable pilot)

| Symptom | Cause | Fix |
|---------|-------|-----|
| Biology chart at ~178 s while copy-protection speech | Beat-06 equal-thirds assembly; wrong `display_sync` path | `cue_slide_sync.py` + `assemble_beat6_from_cues()` from `merge/final.srt` |
| Views speech on summary slide ~28 s | Views overlay too short | `beat01_timing.beat01_views_duration_sec(..., merged_srt=, t0=)` |
| Transition false positives | Strict topic tokens at cue boundaries | `VISUAL_META` topics/`visual_focus`; transition score ≥0.45 for non-charts |
| Chart fail from adjacent cue bleed | Cue overlaps beat boundary | Chart windows use cue **midpoint** inside window only |
| Stale report after assemble | Old `spoken_visual_sync_report.json` | Re-run validators after every `assemble-beats` |

## Key code paths

| Module | Role |
|--------|------|
| `cue_slide_sync.py` | `BEAT6_CUE_IMAGES`, `beat6_cue_windows()`, `assemble_beat6_from_cues()` |
| `beat01_timing.py` | Views overlay duration from merged SRT first cue |
| `spoken_visual_sync.py` | `validate_transition_points`, `validate_visual_windows`, `validate_chart_windows` |
| `display_sync.py` | `VISUAL_META`, `visual_windows()` with `segments_dir` for beat-06 |
| `assemble.py` | Brand bumper, beat-01 `beat_t0` + `merged_srt`, beat-06 cue assembly |
| `slide_word_map.py` | Beat-01 word map uses merged SRT + timeline t0 |

## Unit tests

```bash
pytest tests/test_cue_slide_sync.py tests/test_spoken_visual_sync.py -q
```

Includes beat-06 cue mapping, views-overlay regression, transition @178 s, chart/window gates.

## Artefacts

| Path | Purpose |
|------|---------|
| `merge/final.srt` | Locked script captions (input to cue assembly) |
| `merge/timeline.json` | Segment start/duration (beat-01 t0, beat-06 t0) |
| `merge/spoken_visual_sync_report.json` | Full spoken↔visual gate |
| `merge/display_sync_report.json` | Per-cue midpoint alignment |

## When metadata fixes are enough

If `windows_pass` but `transitions_fail`: extend `VISUAL_META` / `text_slide.py` topics for the slide file — do not weaken validators first.

If `charts_fail`: add `visual_focus` terms the narrator must say; split dual-purpose slides (e.g. `bio-aav-chart.png` vs `distillation-safeguard.png`).
