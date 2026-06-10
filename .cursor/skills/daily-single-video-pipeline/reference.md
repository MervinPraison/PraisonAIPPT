# daily_single pipeline — QA reference

## validate-qa stage map

| Stage | When | Phase | Required | Checks |
|-------|------|-------|----------|--------|
| s04-knowledge | pre_build | — | yes | manifest, video-script, handoff, beat-map, segment scripts |
| s06-coverage | pre_build | post_scripts | yes | script→asset coverage, hook montage plan |
| s01-assets | pre_build | pre_sync | yes | handoff + beat-map present |
| s01-assets | pre_build | post_sync | yes | media inventory on disk |
| s02-source-vlm | pre_build | — | no | 5s VLM samples on source clips (needs API key) |
| s06-coverage | pre_build | post_sync | no | post-sync coverage gaps (warn) |
| s00-bookends | pre_assemble | — | yes | hook/outro script, narration, heygen.mp4 |
| s05-transcript | post_vo | post_vo | yes | narration.mp3 + script per segment |
| s05-transcript | post_build | post_captions | yes | caption lock, Whisper/proportional overlap |
| s03-image-speech | post_build | post_render | yes | display sync (cue → visual) |
| s08-av-sync | post_build | — | yes | hook structure, word match, section boundaries |
| s07-framing | post_build | — | no | HeyGen dimensions |
| s09-on-screen-text | post_build | — | no | weak on-screen cue alignment |
| s10-final-composite | post_build | — | yes | visual audit + sync×3 + validate-all |

List stages: `python -m praisonaippt.video_qa --project $P list`

## Re-run matrix (after edits)

| Changed | Re-run from | QA to re-run |
|---------|-------------|--------------|
| `video-script.md` / beat-map | write-scripts | pre_build |
| Handoff / assets | sync-assets | pre_build |
| Segment script | synthesise-vo (segment) | post_vo → … |
| Hook/outro script | synthesise-vo + bookend-media | pre_assemble → assemble → captions → post_build |
| Beat script only | synthesise-vo (beat dir) | post_vo → assemble-beats → build-captions → post_build |
| B-roll / assembly | assemble-beats | build-captions → post_build |
| Captions only | build-captions | post_build (s05 post_captions+) |

## Degradation flags (`merge/qa/summary.json`)

| Flag | Meaning | Acceptable? |
|------|---------|-------------|
| `whisper: missing_timestamps` | Beat segments use proportional captions | Warn — hook/outro should still have timestamps |
| `vlm: offline` | No OPENAI_API_KEY; s02 skipped | OK for CI |
| `final_mp4: missing` | post_build stages skipped | Must fix before publish |

## Legacy vs modular QA

`s10-final-composite` runs `audit-visual`, `validate-sync --runs 3`, and `validate-all`. Running step 10 (`validate-qa --when post_build`) covers the same bar as steps 11–12 unless you need standalone legacy reports refreshed.

Standalone legacy (faster re-check after cached s10):

```bash
daily-single -p $PROJECT validate-display
daily-single -p $PROJECT validate-sync --runs 3
daily-single -p $PROJECT validate-all
```

## Output artefacts

| Path | Purpose |
|------|---------|
| `merge/final.mp4` | Loudnorm final video |
| `merge/final.srt` | Script-locked captions |
| `merge/timeline.json` | Segment start/duration (from `beats/*.mp4`) |
| `merge/qa/summary.json` | Latest suite rollup |
| `merge/display_sync_report.json` | Cue → asset mapping |
| `merge/sync_validation_report.json` | 3-run robust gate |
| `merge/visual_audit_report.json` | 5s frame audit |

## Protocol

Project protocol: `scripts/config/protocol.json`. Missing `video_qa` block is merged from defaults at runtime. Emit template:

```bash
daily-single -p $PROJECT emit-protocol
```
