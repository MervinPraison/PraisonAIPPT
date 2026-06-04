"""Load Whisper transcript JSON and build HeyGen article deck YAML."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import yaml

# Thematic slide groups: list of segment ids per content slide (after title).
THEMATIC_GROUPS: List[List[int]] = [
    [0],
    [1, 2, 3, 4],
    [5, 6],
    [7, 8, 9],
    [10, 11],
    [12, 13],
    [14],
]

THEMATIC_LAYOUTS = [
    "avatar_headline",
    "avatar_headline",
    "avatar_headline",
    "avatar_headline",
    "avatar_quote",
    "avatar_headline",
    "avatar_headline",
]

THEMATIC_HEADLINES = [
    "Claude Managed Agents — a serious upgrade",
    "First: Dreaming",
    "Second: Outcomes",
    None,
    "How do you actually run AI agents in the real world?",
    "What changed — 6 May 2026",
    "Foundation, not a demo",
]

THEMATIC_SUBHEADERS = [
    "Dreaming · Outcomes · Webhooks — three pillars for production agent stacks",
    "Async memory curation · up to 100 transcripts · read-only until you adopt output",
    "Rubric-backed grader · satisfied / needs_revision · define success not steps",
    "Signed HTTPS callbacks · session & thread events · no polling",
    None,
    "Dreaming preview · outcomes & webhooks public beta · multi-agent orchestration",
    "Read the full article · Managed Agents docs · request dreaming access",
]

PILLAR_SEGMENT_IDS = {1, 4, 6}


@dataclass
class WhisperSegment:
    id: int
    start: float
    end: float
    text: str


@dataclass
class WhisperWord:
    word: str
    start: float
    end: float


@dataclass
class TranscriptData:
    duration: float
    text: str
    segments: List[WhisperSegment] = field(default_factory=list)
    words: List[WhisperWord] = field(default_factory=list)


def normalise_text(text: str) -> str:
    """Fix common Whisper mis-hearings."""
    return re.sub(r"\bClawed\b", "Claude", text, flags=re.IGNORECASE).strip()


def wall_clock_duration(first: WhisperSegment, last: WhisperSegment) -> float:
    return round(last.end - first.start, 3)


def load_whisper_json(path: str | Path) -> TranscriptData:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    segments = [
        WhisperSegment(
            id=int(s.get("id", i)),
            start=float(s["start"]),
            end=float(s["end"]),
            text=normalise_text(str(s.get("text", ""))),
        )
        for i, s in enumerate(raw.get("segments") or [])
    ]
    words = [
        WhisperWord(
            word=normalise_text(str(w.get("word", ""))),
            start=float(w["start"]),
            end=float(w["end"]),
        )
        for w in raw.get("words") or []
    ]
    return TranscriptData(
        duration=float(raw.get("duration") or (segments[-1].end if segments else 0)),
        text=normalise_text(str(raw.get("text", ""))),
        segments=segments,
        words=words,
    )


def _seg_map(data: TranscriptData) -> Dict[int, WhisperSegment]:
    return {s.id: s for s in data.segments}


def _join_notes(segs: Sequence[WhisperSegment]) -> str:
    return normalise_text(" ".join(s.text for s in segs))


def _verse_base(
    *,
    duration_sec: float,
    audio_start_sec: float,
    notes: str,
    slide_type: str,
    avatar_video_path: Optional[str] = None,
    audio_path: Optional[str] = None,
    headline: Optional[str] = None,
    text: Optional[str] = None,
    reference: Optional[str] = None,
) -> dict:
    v: dict = {
        "slide_type": slide_type,
        "duration_sec": duration_sec,
        "audio_start_sec": audio_start_sec,
        "notes": notes,
    }
    if avatar_video_path:
        v["avatar_video_path"] = avatar_video_path
    if audio_path:
        v["audio_path"] = audio_path
    if headline:
        v["headline"] = headline
    if text:
        v["text"] = text
    if reference:
        v["reference"] = reference
    return v


def _layout_for_segment(seg: WhisperSegment, seg_id: int) -> Tuple[str, Optional[str], Optional[str]]:
    t = seg.text.strip()
    if seg_id in PILLAR_SEGMENT_IDS or len(t.split()) <= 6:
        return "avatar_headline", t.rstrip("."), None
    if seg_id in (10, 11, 12):
        return "avatar_quote", None, t
    if seg_id == 14:
        return "avatar_headline", "Read the full piece online", None
    return "avatar_only", None, None


def segments_to_verses(
    data: TranscriptData,
    *,
    mode: str = "thematic",
    avatar_video_path: Optional[str] = None,
    audio_path: Optional[str] = None,
    title_duration_sec: float = 3.0,
    post_roll_sec: float = 0.31,
) -> Tuple[List[dict], List[float]]:
    """Return content verses (no title) and cumulative slide_timestamps."""
    sm = _seg_map(data)
    verses: List[dict] = []

    if mode == "full":
        for seg in data.segments:
            if seg.id == 1:
                continue
            if seg.id == 2:
                group_segs = [sm[i] for i in (1, 2) if i in sm]
            else:
                group_segs = [seg]
            first, last = group_segs[0], group_segs[-1]
            dur = wall_clock_duration(first, last)
            notes = _join_notes(group_segs)
            st, headline, quote_text = _layout_for_segment(first, first.id)
            if seg.id == 2:
                st = "avatar_only"
                headline = None
            elif first.id in PILLAR_SEGMENT_IDS:
                st = "avatar_headline"
                headline = first.text.strip().rstrip(".")
            v = _verse_base(
                duration_sec=dur,
                audio_start_sec=first.start,
                notes=notes,
                slide_type=st,
                avatar_video_path=avatar_video_path,
                audio_path=audio_path,
                headline=headline,
                text=quote_text,
            )
            verses.append(v)
    else:
        for i, group_ids in enumerate(THEMATIC_GROUPS):
            group_segs = [sm[j] for j in group_ids if j in sm]
            if not group_segs:
                continue
            first, last = group_segs[0], group_segs[-1]
            dur = wall_clock_duration(first, last)
            notes = _join_notes(group_segs)
            st = THEMATIC_LAYOUTS[i] if i < len(THEMATIC_LAYOUTS) else "avatar_only"
            headline = THEMATIC_HEADLINES[i] if i < len(THEMATIC_HEADLINES) else None
            subheader = THEMATIC_SUBHEADERS[i] if i < len(THEMATIC_SUBHEADERS) else None
            quote_text = notes if st == "avatar_quote" else None
            if st == "avatar_headline" and not headline:
                headline = group_segs[0].text.strip().rstrip(".")
            v = _verse_base(
                duration_sec=dur,
                audio_start_sec=first.start,
                notes=notes,
                slide_type=st,
                avatar_video_path=avatar_video_path,
                audio_path=audio_path,
                headline=headline,
                text=quote_text,
            )
            if subheader and st == "avatar_headline":
                v["subheader"] = subheader
            if st == "avatar_quote" and headline:
                v["reference"] = subheader or ""
            verses.append(v)

    if verses and post_roll_sec > 0:
        verses[-1]["duration_sec"] = round(
            float(verses[-1]["duration_sec"]) + post_roll_sec, 3
        )

    timestamps = [0.0, title_duration_sec]
    t = title_duration_sec
    for v in verses:
        t += float(v["duration_sec"])
        timestamps.append(round(t, 3))

    return verses, timestamps


def build_title_verse(
    title: str,
    subtitle: str = "",
    duration_sec: float = 3.0,
) -> dict:
    v: dict = {
        "slide_type": "title_only",
        "text": title,
        "duration_sec": duration_sec,
    }
    if subtitle:
        v["reference"] = subtitle
    return v


def build_deck_yaml(
    data: TranscriptData,
    *,
    mode: str = "thematic",
    presentation_title: str = "Dreaming, outcomes, and webhooks",
    presentation_subtitle: str = "Claude Managed Agents update · May 2026",
    avatar_video_path: str = "examples/heygen-article-50590.mp4",
    audio_path: str = "examples/short-script-50590.mp3",
    narration_mode: str = "avatar",
    title_duration_sec: float = 3.0,
    verses: Optional[List[dict]] = None,
    slide_timestamps: Optional[List[float]] = None,
) -> dict:
    if verses is None:
        verses, slide_timestamps = segments_to_verses(
            data,
            mode=mode,
            avatar_video_path=avatar_video_path,
            audio_path=audio_path,
        )
    title = build_title_verse(presentation_title, presentation_subtitle)
    if mode == "thematic":
        all_verses = verses
    else:
        all_verses = [title] + verses
    deck = {
        "presentation_title": presentation_title,
        "presentation_subtitle": presentation_subtitle,
        "slide_size": "widescreen",
        "sections": [{"verses": all_verses}],
        "slide_timestamps": slide_timestamps,
        "video_export": {
            "backend": "compositor",
            "preset": "standard",
            "narration_mode": narration_mode,
            "avatar_timeline": "continuous",
            "slide_duration_sec": title_duration_sec,
            "avatar": {"fit": "cover"},
            "captions": {"enabled": True},
        },
    }
    return deck


def write_deck_yaml(deck: dict, path: str | Path) -> None:
    Path(path).write_text(
        yaml.dump(deck, default_flow_style=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


# Media combination presets for HeyGen article examples.
MEDIA_VARIANTS: Dict[str, Dict[str, Any]] = {
    "video-audio-heygen": {
        "label": "HeyGen video + embedded audio",
        "include_avatar": True,
        "include_audio_path": False,
        "narration_mode": "avatar",
    },
    "video-visual-mp3": {
        "label": "HeyGen video (muted PiP) + MP3 narration",
        "include_avatar": True,
        "include_audio_path": True,
        "narration_mode": "audio_file",
    },
    "audio-only": {
        "label": "Slides + MP3 only (no headshot video)",
        "include_avatar": False,
        "include_audio_path": True,
        "narration_mode": "audio_file",
    },
    "video-only-silent": {
        "label": "HeyGen video PiP only, silent slides",
        "include_avatar": True,
        "include_audio_path": False,
        "narration_mode": "fixed",
    },
    "slides-silent": {
        "label": "Slides only, no media (fixed timing)",
        "include_avatar": False,
        "include_audio_path": False,
        "narration_mode": "fixed",
    },
}


def apply_media_variant(
    deck: dict,
    variant: str,
    *,
    avatar_video_path: str = "examples/heygen-article-50590.mp4",
    audio_path: str = "examples/short-script-50590.mp3",
) -> dict:
    """Return a copy of deck with avatar/audio paths and narration_mode for a variant."""
    spec = MEDIA_VARIANTS.get(variant)
    if not spec:
        raise ValueError(f"Unknown variant {variant!r}. Choose from: {list(MEDIA_VARIANTS)}")

    import copy
    out = copy.deepcopy(deck)
    for v in out.get("sections", [{}])[0].get("verses", []):
        v.pop("avatar_video_path", None)
        v.pop("audio_path", None)
        if spec["include_avatar"]:
            v["avatar_video_path"] = avatar_video_path
        if spec["include_audio_path"]:
            v["audio_path"] = audio_path

    vex = out.setdefault("video_export", {})
    vex["narration_mode"] = spec["narration_mode"]
    if spec["narration_mode"] == "fixed":
        vex["captions"] = {"enabled": False}
    else:
        vex.setdefault("captions", {})["enabled"] = True
    return out


def generate_media_variants(
    transcript_path: str | Path,
    output_dir: str | Path,
    *,
    mode: str = "thematic",
    avatar_video_path: str = "examples/heygen-article-50590.mp4",
    audio_path: str = "examples/short-script-50590.mp3",
    presentation_title: str = "AI Agents: A Serious Upgrade",
    presentation_subtitle: str = "Three pillars for production AI agents",
    variants: Optional[Sequence[str]] = None,
) -> List[Path]:
    """Write one YAML per media combination under output_dir."""
    data = load_whisper_json(transcript_path)
    base = build_deck_yaml(
        data,
        mode=mode,
        presentation_title=presentation_title,
        presentation_subtitle=presentation_subtitle,
        avatar_video_path=avatar_video_path,
        audio_path=audio_path,
    )
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = list(variants or MEDIA_VARIANTS.keys())
    written: List[Path] = []
    for name in names:
        deck = apply_media_variant(
            base, name,
            avatar_video_path=avatar_video_path,
            audio_path=audio_path,
        )
        path = out_dir / f"heygen-50590-{name}.yaml"
        write_deck_yaml(deck, path)
        written.append(path)
    return written


def generate_decks(
    transcript_path: str | Path,
    output_prefix: str | Path,
    *,
    mode: str = "both",
    avatar_video_path: str = "examples/heygen-article-50590.mp4",
    audio_path: str = "examples/short-script-50590.mp3",
    presentation_title: str = "AI Agents: A Serious Upgrade",
) -> List[Path]:
    data = load_whisper_json(transcript_path)
    prefix = Path(output_prefix)
    written: List[Path] = []
    modes = ["full", "thematic"] if mode == "both" else [mode]
    for m in modes:
        deck = build_deck_yaml(
            data,
            mode=m,
            presentation_title=presentation_title,
            avatar_video_path=avatar_video_path,
            audio_path=audio_path,
        )
        suffix = "full" if m == "full" else "short"
        out = prefix.parent / f"{prefix.name}-{suffix}.yaml"
        write_deck_yaml(deck, out)
        written.append(out)
    return written
