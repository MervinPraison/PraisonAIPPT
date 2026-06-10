---
name: daily-single-video-pipeline
description: Step-by-step daily_single video build with modular QA gates (validate-qa pre_build/pre_assemble/post_vo/post_build), pytest suite, and legacy validate-sync. Use when the user asks to create a video step by step, run the pipeline robustly, validate each stage, rebuild a pilot like Fable, or orchestrate daily-single + video-qa end to end.
---

# daily_single video pipeline (step by step)

Orchestrate **build commands** and **QA gates** in order. Do not skip gates after a step fails — fix, re-run that step, then re-gate.

**Script/ hook contract:** `.cursor/skills/daily-single-video/SKILL.md`  
**Reference pilot:** `examples/videos/anthropic-claude-fable-5-mythos-5/`  
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
- [ ] 7. record-canonical-scroll --duration 5  (inspect merge/qa/canonical_capture/page.png)
- [ ] 8. validate-canonical-scroll  → must PASS before assemble
- [ ] 9. QA pre_assemble → validate-qa --when pre_assemble  (includes s11-canonical-capture)
- [ ]10. assemble-beats  (writes merge/timeline.json)
- [ ]11. build-captions  (merge/final.srt)
- [ ]12. validate-hook-attention --seconds 5  (reject error pages in first 5s)
- [ ]13. QA post_build  → validate-qa --when post_build  (includes s12-hook-attention)
- [ ]14. Legacy confirm → validate-all && validate-sync --runs 3
- [ ]15. Publish gate   → mer-vin upload skill (optional)
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
| 8 | Assemble | `daily-single -p $PROJECT assemble-beats` | `merge/final.mp4`, `merge/timeline.json` |
| 9 | Captions | `daily-single -p $PROJECT build-captions` | `merge/final.srt` (52 cues typical) |
| 10 | Post-build QA | `daily-single -p $PROJECT validate-qa --when post_build` | **PASS** 6/6 — display, AV sync, visual audit |
| 11 | Legacy gates | `daily-single -p $PROJECT validate-all` | Prints **PASS** |
| 12 | Idempotent sync | `daily-single -p $PROJECT validate-sync --runs 3` | 3 identical runs, hook_montage + visual |

Single stage debug:

```bash
daily-single -p $PROJECT validate-qa s08-av-sync
python -m praisonaippt.video_qa --project $PROJECT run s10-final-composite
```

Reports: `$PROJECT/merge/qa/summary.json` and `$PROJECT/merge/qa/s*_report.json`.

## Automated tests (run before declaring done)

```bash
pytest tests/test_video_qa.py \
       tests/test_page_capture_quality.py \
       tests/test_canonical_scroll.py \
       tests/test_daily_single_sync_validation.py \
       tests/test_daily_single_display_sync_unit.py \
       tests/test_daily_single_hook_montage.py \
       tests/test_daily_single_visual_audit.py -q
```

Tier-0 only (no API keys): `pytest tests/test_video_qa.py -q`

## When a gate fails

1. Read `merge/qa/summary.json` → `failed_required` and per-stage `checks`.
2. Fix the **root cause** (script, asset, assembly), not the validator.
3. Re-run from the **lowest affected build step** (see table in [reference.md](reference.md)).
4. Re-run only the QA `--when` phases that cover changed artefacts.

Common fixes:

| Failure | Fix |
|---------|-----|
| s06 sparse_assets | Add beat-map images/clips or shorten script |
| s02 generic B-roll | Swap handoff clip or disable in protocol |
| build-captions crash | Proportional captions OK — s05 marks `degraded: whisper` |
| s08 section_boundaries | Re-run `assemble-beats` or `build-timeline`; compare `beats/*.mp4` to timeline |
| s10 visual audit | Fix beat B-roll; re-run `assemble-beats` → post_build QA |
| s11 / validate-canonical-scroll | Browser error in hook — re-run `record-canonical-scroll`; open `merge/qa/canonical_capture/page.png` |
| s12 / validate-hook-attention | Error page in first 5s of final — fix scroll capture then `assemble-beats` |

## Multi-agent orchestration

Use subagents **only where parallel or deep investigation helps**. The parent agent keeps the checklist and runs gates sequentially.

| Situation | Agent | Task |
|-----------|-------|------|
| Unknown project state, missing files | `explore` | Map `$PROJECT/segments`, `merge/`, handoff paths; return gap list |
| One stage fails with opaque error | `explore` | Read `merge/qa/*_report.json` + relevant source; return fix steps |
| After code changes to `video_qa/` or validators | `software-tester` | Run pytest + `$PROJECT validate-qa --when all` |
| Full pilot rebuild (Fable-scale) | Parent + optional `software-tester` | Parent runs steps 1–12; tester runs pytest in parallel after step 10 |

Do **not** launch multiple agents to run the same `validate-qa --when post_build` (s10 runs visual audit once; duplicate runs waste API spend).

## Publish-quality bar

All must be true before upload:

- `validate-qa --when post_build` → **PASS** 6/6
- `validate-all` → **PASS**
- `validate-sync --runs 3` → idempotent, `hook_montage=True`, `visual_audit=True`
- `merge/visual_audit_report.json` → samples_pass == samples_total
- `merge/display_sync_report.json` → cues_pass == cues_total

## Related docs

- Modular QA stages: `docs/video-qa.md`
- Full daily_single guide: `docs/daily-single-video.md` (if present) or `.cursor/skills/daily-single-video/SKILL.md`
