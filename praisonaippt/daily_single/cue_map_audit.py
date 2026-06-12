"""Cue-to-picture map — every spoken beat must line up with the right image."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from praisonaippt.daily_single.cue_slide_sync import beat6_absolute_cues, beat6_cue_image_map, find_image
from praisonaippt.daily_single.display_sync import MIN_ALIGNMENT, score_cue_visual
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import BEAT_SEGMENT_DIRS
from praisonaippt.segment_video.media import ffprobe_duration

MIN_CUE_SCORE = MIN_ALIGNMENT

BEAT6_SOCIAL_CUE_CLIPS: list[tuple[str, ...]] = [
    ("claudeai-safeguards", "safeguard"),
    ("pootlepress", "wp-theme", "wordpress", "marsland"),
    ("claudeai-safeguards", "pootlepress", "wordpress", "benchmark"),
    ("claudeai-safeguards", "pootlepress", "fable", "output", "concrete"),
]

BEAT7_SOCIAL_CUE_CLIPS: list[tuple[str, ...]] = [
    ("trq212", "pipeline", "whisper", "ffmpeg", "remotion"),
    ("claudeai", "launch", "rollout", "engineering", "demo"),
]

BEAT8_SOCIAL_CUE_CLIPS: list[tuple[str, ...]] = [
    ("pokemon", "chrissgpt"),
    ("trq212", "walkthrough", "ffmpeg", "remotion"),
    ("claudeai", "launch", "engineering", "api"),
    ("witness", "author", "theme", "clone", "edit", "pokemon", "trq212", "claudeai"),
    ("drafts", "premium", "long", "builds", "pokemon", "trq212", "claudeai"),
    ("agentic", "overnight", "dress", "rehearsal", "pokemon", "trq212", "claudeai"),
]

_SOCIAL_BEATS: dict[int, tuple[str, list[tuple[str, ...]]]] = {
    6: ("06-safeguards", BEAT6_SOCIAL_CUE_CLIPS),
    7: ("07-api-integration", BEAT7_SOCIAL_CUE_CLIPS),
    8: ("08-glasswing", BEAT8_SOCIAL_CUE_CLIPS),
}


def _clip_cue_needles(clips: list[dict]) -> list[tuple[str, ...]]:
    """Filename needles for clip-only beats without a hand-tuned cue map."""
    needles: list[tuple[str, ...]] = []
    for clip in clips:
        fn = Path(str(clip.get("path") or clip.get("filename") or "")).stem.lower()
        parts = [
            p for p in re.split(r"[-_\.]+", fn)
            if len(p) >= 3 and p not in ("mp4", "social", "capture", "clip")
        ]
        needles.append(tuple(parts[:4]) if parts else (fn[:10],))
    return needles or [("clip",)]


def _cue_map_for_clip_beat(beat_n: int, clips: list[dict]) -> list[tuple[str, ...]]:
    if beat_n in _SOCIAL_BEATS:
        return _SOCIAL_BEATS[beat_n][1]
    if beat_n == 6:
        return BEAT6_SOCIAL_CUE_CLIPS
    return _clip_cue_needles(clips)


def find_clip(clips: list[dict], *needles: str) -> dict | None:
    for needle in needles:
        for clip in clips:
            fn = Path(str(clip.get("path") or "")).name.lower()
            if needle in fn:
                return clip
    return None


def _beat_timeline_start(project: DailySingleProject, tl_id: str) -> float:
    tl = project.merge_dir / "timeline.json"
    if not tl.is_file():
        return 0.0
    for row in json.loads(tl.read_text(encoding="utf-8")).get("segments") or []:
        if row.get("id") == tl_id:
            return float(row.get("start_sec") or 0)
    return 0.0


def _validate_social_beat_cues(
    project: DailySingleProject,
    *,
    beat_n: int,
    seg_dir: str,
    tl_id: str,
    clips: list[dict],
    cue_map: list[tuple[str, ...]],
) -> tuple[list[str], dict[str, Any]]:
    issues: list[str] = []
    mp3 = project.segment_narration(seg_dir)
    if not mp3.is_file():
        return [f"Beat {beat_n}: record voice-over before checking picture map"], {}

    seg_dur = ffprobe_duration(mp3)
    t0 = _beat_timeline_start(project, tl_id)
    merged_srt = project.merge_dir / "final.srt"
    seg_srt = project.segments_dir / seg_dir / "segment.srt"
    cues = beat6_absolute_cues(
        t0, seg_dur, seg_srt,
        merged_srt=merged_srt if merged_srt.is_file() else None,
    )

    for i, (_start, _end, text) in enumerate(cues):
        needles = cue_map[i] if i < len(cue_map) else cue_map[-1]
        clip = find_clip(clips, *needles)
        if not clip:
            issues.append(f"Beat {beat_n} cue {i + 1}: no clip matched — speech: {text[:60]}…")
            continue
        score = score_cue_visual(text, Path(clip["path"]).name)
        if score < MIN_CUE_SCORE:
            issues.append(
                f"Beat {beat_n} cue {i + 1}: words do not match {Path(clip['path']).name} "
                f"(score {score:.2f}) — {text[:50]}…"
            )

    return issues, {"beat": beat_n, "cues": len(cues), "clips": len(clips), "mode": "clips"}


def _validate_beat6_image_cues(
    project: DailySingleProject,
    *,
    images: list[dict],
) -> tuple[list[str], dict[str, Any]]:
    issues: list[str] = []
    mp3 = project.segment_narration("06-safeguards")
    if not mp3.is_file():
        return ["Beat 6: record voice-over before checking picture map"], {}

    seg_dur = ffprobe_duration(mp3)
    t0 = _beat_timeline_start(project, "beat-06")
    merged_srt = project.merge_dir / "final.srt"
    seg_srt = project.segments_dir / "06-safeguards" / "segment.srt"
    cues = beat6_absolute_cues(
        t0, seg_dur, seg_srt,
        merged_srt=merged_srt if merged_srt.is_file() else None,
    )
    cue_map = beat6_cue_image_map(images)

    for i, (_start, _end, text) in enumerate(cues):
        needles = cue_map[i] if i < len(cue_map) else cue_map[-1]
        img = find_image(images, *needles)
        if not img:
            issues.append(f"Beat 6 cue {i + 1}: no picture matched — speech: {text[:60]}…")
            continue
        score = score_cue_visual(text, Path(img["path"]).name)
        if score < MIN_CUE_SCORE:
            issues.append(
                f"Beat 6 cue {i + 1}: words do not match {Path(img['path']).name} "
                f"(score {score:.2f}) — {text[:50]}…"
            )

    return issues, {
        "beat": 6,
        "cues": len(cues),
        "images": len(images),
        "mode": "images",
    }


def validate_cue_picture_map(project: DailySingleProject) -> tuple[bool, list[str], dict[str, Any]]:
    issues: list[str] = []
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    details: dict[str, Any] = {"beats": []}

    for beat_n_str, beat in sorted((beat_map.get("beats") or {}).items(), key=lambda x: int(x[0])):
        try:
            beat_n = int(beat_n_str)
        except ValueError:
            continue
        seg_dir = BEAT_SEGMENT_DIRS.get(beat_n)
        if not seg_dir:
            continue

        images = list(beat.get("images") or [])
        clips = list(beat.get("clips") or [])

        if images and beat_n == 6:
            beat_issues, beat_detail = _validate_beat6_image_cues(project, images=images)
            issues.extend(beat_issues)
            details["beats"].append(beat_detail)
            continue

        if not clips or images:
            continue

        beat_issues, beat_detail = _validate_social_beat_cues(
            project,
            beat_n=beat_n,
            seg_dir=seg_dir,
            tl_id=f"beat-{beat_n:02d}",
            clips=clips,
            cue_map=_cue_map_for_clip_beat(beat_n, clips),
        )
        issues.extend(beat_issues)
        details["beats"].append(beat_detail)

    return len(issues) == 0, issues, details
