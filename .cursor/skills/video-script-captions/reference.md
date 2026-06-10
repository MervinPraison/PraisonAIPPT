# Caption alignment reference

## June roundup pattern

**SRT body** = `verse.notes` or `cue.script_fragment` from locked `script.md`.  
**SRT timing** = Whisper via `align-cues` → `audio_start_sec` / `duration_sec`.

Functions in `praisonaippt/segment_video/timeline.py`:

- `write_verses_srt(seg_dir, verses)` — hook lead-in + montage
- `write_cue_timings_srt(seg_dir, cues)` — one row per aligned fragment

Merge offsets: `praisonaippt/segment_video/stages/merge.py` (`parse_srt` + segment duration offsets).

## daily_single pattern

**SRT body** = sentences from `segments/*/script.md` after `narration_text_for_tts()`.  
**SRT timing** = per-segment `timestamps.json` from `praisonaippt transcribe` on `narration.mp3`, aligned with `match_fragment_to_words`.

Never use merged `merge/narration.json` for caption text — it is one long Whisper blob with ASR errors.

## Script → cue split

One cue per sentence ending `.` `!` `?`. Beat 7 integration table is prose in script, not markdown rows.

## Anti-patterns

| Bad | Good |
|-----|------|
| `"Hook, Anthropic shipped Mythos class..."` | `"Anthropic put Mythos-class weights..."` |
| Whisper-only SRT | Script + Whisper timing |
| Caption after script change without rebuild | `build-captions` in same turn |
