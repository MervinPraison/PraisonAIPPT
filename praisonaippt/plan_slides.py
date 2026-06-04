"""Draft slide verses and layout hints from a Whisper transcript."""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

PLAN_STATUS_PENDING = "pending"
PLAN_STATUS_APPROVED = "approved"

from .transcript_loader import (
    THEMATIC_GROUPS,
    THEMATIC_HEADLINES,
    THEMATIC_LAYOUTS,
    THEMATIC_SUBHEADERS,
    TranscriptData,
    _join_notes,
    _seg_map,
    _verse_base,
    load_whisper_json,
    wall_clock_duration,
    write_deck_yaml,
)

_DECK_KEYWORDS = re.compile(
    r"\b(\d+%|\d+\s*(million|billion|users|agents)|table|compare|versus|vs\.)\b",
    re.I,
)
_QUOTE_MIN_WORDS = 12


def _suggest_slide_type(seg_text: str, group_notes: str, thematic_layout: str) -> str:
    """Pick a richer layout when transcript cues suggest it."""
    blob = f"{seg_text} {group_notes}"
    if thematic_layout == "avatar_quote" or len(group_notes.split()) >= _QUOTE_MIN_WORDS:
        return "avatar_quote"
    if _DECK_KEYWORDS.search(blob):
        return "deck_exec_summary"
    if len(seg_text.split()) <= 8:
        return "avatar_headline"
    return thematic_layout if thematic_layout.startswith("deck_") else "avatar_headline"


def draft_verses_from_transcript(
    data: TranscriptData,
    *,
    mode: str = "thematic",
    avatar_video_path: Optional[str] = None,
    audio_path: Optional[str] = None,
    title_duration_sec: float = 3.0,
) -> List[dict]:
    """Build verse dicts with suggested slide_type (for plan-slides / seeding)."""
    sm = _seg_map(data)
    verses: List[dict] = []

    if mode == "full":
        from .transcript_loader import segments_to_verses

        verses, _ = segments_to_verses(
            data,
            mode="full",
            avatar_video_path=avatar_video_path,
            audio_path=audio_path,
            title_duration_sec=title_duration_sec,
        )
        return verses

    for i, group_ids in enumerate(THEMATIC_GROUPS):
        group_segs = [sm[j] for j in group_ids if j in sm]
        if not group_segs:
            continue
        first, last = group_segs[0], group_segs[-1]
        notes = _join_notes(group_segs)
        base_layout = THEMATIC_LAYOUTS[i] if i < len(THEMATIC_LAYOUTS) else "avatar_only"
        st = _suggest_slide_type(first.text, notes, base_layout)
        headline = THEMATIC_HEADLINES[i] if i < len(THEMATIC_HEADLINES) else None
        subheader = THEMATIC_SUBHEADERS[i] if i < len(THEMATIC_SUBHEADERS) else None
        quote_text = notes if st == "avatar_quote" else None
        if st == "avatar_headline" and not headline:
            headline = group_segs[0].text.strip().rstrip(".")
        v = _verse_base(
            duration_sec=wall_clock_duration(first, last),
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
    return verses


def build_plan_deck(
    transcript_path: str | Path,
    *,
    presentation_title: str = "AI Agents: A Serious Upgrade",
    presentation_subtitle: str = "Three pillars for production AI agents",
    avatar_video_path: str = "examples/heygen-article-50590.mp4",
    audio_path: str = "examples/short-script-50590.mp3",
    merge_master: Optional[str | Path] = None,
) -> dict:
    """Return a deck dict with planned verses; optionally merge slide_style from master."""
    data = load_whisper_json(transcript_path)
    verses = draft_verses_from_transcript(
        data,
        avatar_video_path=avatar_video_path,
        audio_path=audio_path,
    )
    deck: Dict[str, Any] = {
        "presentation_title": presentation_title,
        "presentation_subtitle": presentation_subtitle,
        "slide_size": "widescreen",
        "avatar_calibration": {"auto": True, "method": "hybrid"},
        "pipeline": {
            "transcript_path": str(transcript_path),
            "content_master": str(merge_master) if merge_master else None,
        },
        "sections": [{"verses": verses}],
        "video_export": {
            "preset": "standard",
            "narration_mode": "avatar",
            "audio_source": "heygen_video",
            "avatar_timeline": "continuous",
            "captions": {"enabled": True},
        },
    }
    if merge_master and Path(merge_master).is_file():
        master = yaml.safe_load(Path(merge_master).read_text(encoding="utf-8")) or {}
        for key in ("slide_style", "slide_images_dir", "avatar_calibration", "pipeline"):
            if key in master:
                deck[key] = copy.deepcopy(master[key])
        if master.get("presentation_title"):
            deck["presentation_title"] = master["presentation_title"]
        if master.get("presentation_subtitle"):
            deck["presentation_subtitle"] = master["presentation_subtitle"]
    return deck


def plan_meta_path(draft_yaml: str | Path) -> Path:
    p = Path(draft_yaml)
    return p.with_name(f"{p.stem}.plan-meta.json")


def write_plan_meta(draft_yaml: str | Path, *, transcript_path: str) -> Path:
    """Write approval checkpoint metadata (status=pending until approve-plan)."""
    meta_path = plan_meta_path(draft_yaml)
    meta = {
        "status": PLAN_STATUS_PENDING,
        "draft_yaml": str(Path(draft_yaml).resolve()),
        "transcript_path": transcript_path,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None,
        "instruction": "Edit the draft YAML, then run: praisonaippt approve-plan <draft.yaml>",
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta_path


def approve_plan(draft_yaml: str | Path) -> Path:
    """Mark a plan draft approved (required before pipeline sync when plan_draft is set)."""
    meta_path = plan_meta_path(draft_yaml)
    if not meta_path.is_file():
        raise FileNotFoundError(
            f"Plan metadata not found: {meta_path}. Run plan-slides first.",
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["status"] = PLAN_STATUS_APPROVED
    meta["approved_at"] = datetime.now(timezone.utc).isoformat()
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta_path


def is_plan_approved(draft_yaml: str | Path) -> bool:
    meta_path = plan_meta_path(draft_yaml)
    if not meta_path.is_file():
        return False
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return meta.get("status") == PLAN_STATUS_APPROVED


def check_plan_approval_gate(
    pipe: Optional[dict],
    *,
    base_dir: Optional[Path] = None,
) -> Tuple[bool, str]:
    """Return (ok, detail) for plan approval before sync/build."""
    pipe = pipe or {}
    if pipe.get("content_approved") or pipe.get("plan_approved"):
        return True, "Content/plan explicitly approved in pipeline config"
    draft = pipe.get("plan_draft")
    if not draft:
        return True, "No plan_draft required (skipped)"
    draft_path = Path(draft)
    if base_dir and not draft_path.is_file():
        draft_path = base_dir / draft
    if not draft_path.is_file():
        return False, f"plan_draft not found: {draft}"
    if is_plan_approved(draft_path):
        return True, f"Plan approved: {draft_path.name}"
    return (
        False,
        f"Plan not approved. Edit {draft_path.name} then: praisonaippt approve-plan {draft_path}",
    )


def write_plan_yaml(
    transcript_path: str | Path,
    output_path: str | Path,
    **kwargs: Any,
) -> Path:
    deck = build_plan_deck(transcript_path, **kwargs)
    out = Path(output_path)
    write_deck_yaml(deck, out)
    write_plan_meta(out, transcript_path=str(transcript_path))
    return out


def seed_timing_from_transcript(
    deck: dict,
    transcript_path: str | Path,
    *,
    mode: str = "thematic",
) -> dict:
    """Update duration_sec, audio_start_sec, and notes on existing verses from Whisper."""
    data = load_whisper_json(transcript_path)
    draft = draft_verses_from_transcript(data, mode=mode)
    out = copy.deepcopy(deck)
    verses = (out.get("sections") or [{}])[0].get("verses") or []
    for i, src in enumerate(draft):
        if i >= len(verses):
            break
        verses[i]["duration_sec"] = src["duration_sec"]
        verses[i]["audio_start_sec"] = src["audio_start_sec"]
        verses[i]["notes"] = src["notes"]
    return out
