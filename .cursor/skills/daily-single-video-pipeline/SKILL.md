---
name: daily-single-video-pipeline
description: Step-by-step daily_single video build with modular QA gates, spoken↔visual sync, social comparison clips, pytest, and validate-sync. Use for Fable-style pilots, social-comparison videos, A/V sync fixes, or end-to-end daily-single orchestration.
---

# daily_single video pipeline (step by step)

**Agent contract:** read repo root [`AGENTS.md`](../../AGENTS.md) first — full BUILD_PIPELINE, PUBLISH_GATE, and QA-between-steps matrix.

Orchestrate **build commands** and **QA gates** in order. Do not skip gates after a step fails — fix, re-run that step, then re-gate.

**Script/ hook contract:** `.cursor/skills/daily-single-video/SKILL.md`  
**Spoken↔visual sync (cue assembly, 178 s regression):** [spoken-visual-sync.md](spoken-visual-sync.md)  
**Social / viral research (X, Reddit, last30days):** [social-research-last30days.md](social-research-last30days.md)  
**Reference pilot:** `examples/videos/anthropic-claude-fable-5-mythos-5/`  
**Trust audit:** `examples/videos/anthropic-claude-fable-5-trust-audit/`  
**Social comparison (same-prompt clips):** `examples/videos/anthropic-claude-fable-5-social-comparison/` — download clips first: `bash scripts/download_social_videos.sh`  
**Stage details:** [reference.md](reference.md)

## Environment

```bash
zsh -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate test && cd /path/to/praisonaippt"
PROJECT=examples/videos/<slug>
```

Requires `OPENAI_API_KEY` for s02 VLM and s10 visual audit (unless offline). Set `PRAISONAIPPT_QA_OFFLINE=1` to skip VLM-only stages in CI.

## Master checklist

Copy and tick as you go:

```text
- [ ] 0. Project has manifest.json + create-news handoff + beat-map
- [ ] 1. write-scripts (if segments missing)
- [ ] 2. QA pre_build  → validate-qa --when pre_build
- [ ] 3. sync-assets
- [ ] 4. synthesise-vo
- [ ] 5. QA post_vo    → validate-qa --when post_vo
- [ ] 6. bookend-media (00-hook, 99-outro)
- [ ] 7. record-canonical-scroll --duration 5  (inspect merge/qa/canonical_capture/framing-diagram.png — no wide gutters)
- [ ] 8. validate-canonical-scroll  → must PASS (margins ≤12%, fill ≥55%, scroll ≤100 px/s)
- [ ] 9. QA pre_assemble → validate-qa --when pre_assemble  (includes s11-canonical-capture)
- [ ]10. build-captions  (merge/final.srt — before assemble when cue-aligned beats)
- [ ]11. assemble-beats  (writes merge/timeline.json; beat-06/beat-01 use final.srt)
- [ ]12. validate-display  (per-cue midpoint → visual)
- [ ]12b. validate-spoken-visual  (montage/windows/charts/coverage/transitions + plain language)
- [ ]12c. validate-slide-quality → validate-engagement-assets → validate-viral-readiness
- [ ]12d. pytest tests/test_cue_slide_sync.py tests/test_spoken_visual_sync.py tests/test_slide_design_audit.py -q
- [ ]13. validate-hook-attention  (1s frames ×5, then 2s until hook end)
- [ ]14. QA post_build  → validate-qa --when post_build  (includes s12-hook-attention, s03 charts/plain)
- [ ]15. Legacy confirm → validate-all && validate-sync --runs 3
- [ ]16. Publish gate   → mer-vin upload skill (optional)
```

**Cue-aligned rebuild** (after script or safeguard-slide fixes): steps 10 → 11 → 12 → 12b → 12c only, or:

```bash
.cursor/skills/daily-single-video-pipeline/scripts/run-spoken-visual-gate.sh $PROJECT --assemble
.cursor/skills/daily-single-video-pipeline/scripts/run-publish-gate.sh $PROJECT
```

## Step-by-step commands

Replace `$PROJECT` with the video project root (directory containing `manifest.json`).

| # | Step | Command | Pass criterion |
|---|------|---------|----------------|
| 1 | Scripts | `daily-single -p $PROJECT write-scripts` | All `segments/*/script.md` exist |
| 2 | Pre-build QA | `daily-single -p $PROJECT validate-qa --when pre_build` | **PASS** N/N — see [reference.md](reference.md) |
| 3 | Sync assets | `daily-single -p $PROJECT sync-assets` | HD clips + canonical images on disk |
| 4 | Voice-over | `daily-single -p $PROJECT synthesise-vo --skip-existing` | All `segments/*/narration.mp3` |
| 5 | Post-VO QA | `daily-single -p $PROJECT validate-qa --when post_vo` | s05: script + narration per segment |
| 6 | Bookends | `daily-single -p $PROJECT bookend-media --skip-existing` | `heygen.mp4` hook + outro |
| 7 | Pre-assemble QA | `daily-single -p $PROJECT validate-qa --when pre_assemble` | s00: hook/outro script, VO, HeyGen |
| 8 | Captions | `daily-single -p $PROJECT build-captions` | `merge/final.srt` |
| 9 | Assemble | `daily-single -p $PROJECT assemble-beats` | `merge/final.mp4`, `merge/timeline.json` |
| 10 | Display sync | `daily-single -p $PROJECT validate-display` | cues_pass == cues_total |
| 11 | Spoken↔visual | `daily-single -p $PROJECT validate-spoken-visual` | **PASS** — `merge/spoken_visual_sync_report.json` ok:true |
| 12 | Post-build QA | `daily-single -p $PROJECT validate-qa --when post_build` | **PASS** 6/6 — display, AV sync, visual audit |
| 13 | Legacy gates | `daily-single -p $PROJECT validate-all` | Prints **PASS** |
| 14 | Idempotent sync | `daily-single -p $PROJECT validate-sync --runs 3` | 3 identical runs, spoken_visual=True |

Single stage debug:

```bash
daily-single -p $PROJECT validate-qa s08-av-sync
daily-single -p $PROJECT validate-spoken-visual
python -m praisonaippt.video_qa --project $PROJECT run s10-final-composite
```

Reports: `$PROJECT/merge/qa/summary.json` and `$PROJECT/merge/qa/s*_report.json`.

## Automated tests (run before declaring done)

```bash
pytest tests/test_video_qa.py \
       tests/test_page_capture_quality.py \
       tests/test_canonical_scroll.py \
       tests/test_content_framing.py \
       tests/test_daily_single_sync_validation.py \
       tests/test_daily_single_display_sync_unit.py \
       tests/test_daily_single_hook_montage.py \
       tests/test_daily_single_visual_audit.py \
       tests/test_cue_slide_sync.py \
       tests/test_spoken_visual_sync.py -q
```

Tier-0 only (no API keys): `pytest tests/test_video_qa.py tests/test_cue_slide_sync.py tests/test_spoken_visual_sync.py -q`

## When a gate fails

1. Read `merge/qa/summary.json` → `failed_required` and per-stage `checks`.
2. For A/V mismatch at a timestamp: read [spoken-visual-sync.md](spoken-visual-sync.md) → multi-agent validation table.
3. Fix the **root cause** (script, asset, assembly, `VISUAL_META`), not the validator.
4. Re-run from the **lowest affected build step** (see table in [reference.md](reference.md)).
5. Re-run only the QA `--when` phases that cover changed artefacts.

Common fixes:

| Failure | Fix |
|---------|-----|
| s06 sparse_assets | Add beat-map images/clips or shorten script |
| s02 generic B-roll | Swap handoff clip or disable in protocol |
| build-captions crash | Proportional captions OK — s05 marks `degraded: whisper` |
| s08 section_boundaries | Re-run `assemble-beats` or `build-timeline`; compare `beats/*.mp4` to timeline |
| s10 visual audit | Fix beat B-roll; re-run `assemble-beats` → post_build QA |
| s11 / validate-canonical-scroll | Browser error or wide gutters in hook — re-run `record-canonical-scroll`; open `framing-diagram.png` |
| s12 / validate-hook-attention | Error page, margins, or static first 5s — fix scroll capture then `assemble-beats` |
| validate-spoken-visual FAIL @~178s | Beat-06 cue assembly — see [spoken-visual-sync.md](spoken-visual-sync.md) |
| transitions_fail, windows_pass | Extend slide `VISUAL_META` topics or fix equal-thirds assembly |
| charts_fail on stat overlay | Add `visual_focus`; ensure cue midpoint inside chart window |

## Multi-agent orchestration

Use subagents **only where parallel or deep investigation helps**. The parent agent keeps the checklist and runs gates sequentially.

| Situation | Agent | Task |
|-----------|-------|------|
| Unknown project state, missing files | `explore` | Map `$PROJECT/segments`, `merge/`, handoff paths; return gap list |
| Reported A/V mismatch at timestamp T | `explore` | `timeline.json` + `spoken_visual_sync_report.json` + segment script; PASS/FAIL at T with evidence |
| Validator/assembler code review | `generalPurpose` | Review `cue_slide_sync`, `spoken_visual_sync`, `assemble`; flag false positives |
| One stage fails with opaque error | `explore` | Read `merge/qa/*_report.json` + relevant source; return fix steps |
| After code changes to validators | `software-tester` | Run pytest + `$PROJECT validate-spoken-visual` |
| Full pilot rebuild (Fable-scale) | Parent + optional `software-tester` | Parent runs steps 8–14; tester runs pytest in parallel after assemble |

Do **not** launch multiple agents to run the same `validate-qa --when post_build` (s10 runs visual audit once; duplicate runs waste API spend).

## Publish-quality bar

All must be true before upload:

- `validate-qa --when post_build` → **PASS** 6/6
- `validate-spoken-visual` → **PASS** (`merge/spoken_visual_sync_report.json` → `ok: true`)
- `validate-all` → **PASS**
- `validate-sync --runs 3` → idempotent, `hook_montage=True`, `visual_audit=True`, `spoken_visual=True`
- `merge/visual_audit_report.json` → samples_pass == samples_total
- `merge/display_sync_report.json` → cues_pass == cues_total

## Related docs

- Spoken↔visual workflow: [spoken-visual-sync.md](spoken-visual-sync.md)
- Modular QA stages: `docs/video-qa.md`
- Full daily_single guide: `docs/daily-single-video.md`
- Testing: `docs/daily-single-testing.md`
