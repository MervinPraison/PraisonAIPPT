"""Audio waveform alignment: silence detection, RMS emphasis, word-level SRT."""

from __future__ import annotations

import logging
import math
import re
import struct
import subprocess
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from .transcript_loader import TranscriptData, WhisperWord, normalise_text

logger = logging.getLogger(__name__)

_SILENCE_RE = re.compile(
    r"silence_(start|end):\s*([0-9.]+)",
    re.IGNORECASE,
)


def _run_ffmpeg(args: List[str], *, timeout: int = 120) -> str:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "info", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.stderr + proc.stdout


def detect_silences(
    audio_path: str | Path,
    *,
    noise_db: float = -30.0,
    min_duration: float = 0.25,
) -> List[Tuple[float, float]]:
    """Return list of (start, end) silence intervals via ffmpeg silencedetect."""
    path = str(audio_path)
    log = _run_ffmpeg([
        "-i", path,
        "-af", f"silencedetect=noise={noise_db}dB:d={min_duration}",
        "-f", "null", "-",
    ])
    starts: List[float] = []
    ends: List[float] = []
    for kind, val in _SILENCE_RE.findall(log):
        t = float(val)
        if kind.lower() == "start":
            starts.append(t)
        else:
            ends.append(t)
    gaps: List[Tuple[float, float]] = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else s
        gaps.append((s, e))
    return gaps


def merge_boundaries(
    segment_gaps: Sequence[Tuple[float, float]],
    silence_gaps: Sequence[Tuple[float, float]],
    tolerance: float = 0.15,
) -> List[Tuple[float, float]]:
    """Align Whisper segment gaps with detected silences within tolerance."""
    merged = list(segment_gaps)
    for sg_start, sg_end in segment_gaps:
        mid = (sg_start + sg_end) / 2
        for sl_start, sl_end in silence_gaps:
            sl_mid = (sl_start + sl_end) / 2
            if abs(mid - sl_mid) <= tolerance:
                merged.append((sl_start, sl_end))
                break
    return merged


def segment_gaps_from_data(data: TranscriptData) -> List[Tuple[float, float]]:
    gaps: List[Tuple[float, float]] = []
    segs = data.segments
    for i in range(len(segs) - 1):
        gaps.append((segs[i].end, segs[i + 1].start))
    return gaps


def refine_verses(
    verses: List[dict],
    data: TranscriptData,
    silence_gaps: Sequence[Tuple[float, float]],
    *,
    tolerance: float = 0.15,
) -> int:
    """Adjust slide boundaries where silence aligns with segment gaps. Returns change count."""
    seg_gaps = segment_gaps_from_data(data)
    changes = 0
    sm = {s.id: s for s in data.segments}
    for v in verses:
        start = float(v.get("audio_start_sec", 0))
        dur = float(v.get("duration_sec", 0))
        end = start + dur
        for gap_start, gap_end in seg_gaps:
            if abs(gap_start - start) < 0.05 or abs(gap_end - end) < 0.05:
                for sl_start, sl_end in silence_gaps:
                    if abs(gap_start - sl_start) <= tolerance:
                        new_end = sl_end if sl_end > gap_start else gap_end
                        if abs(new_end - end) > 0.01:
                            v["duration_sec"] = round(new_end - start, 3)
                            changes += 1
                            logger.info(
                                "Silence refine: slide start=%.2f duration %.2f -> %.2f",
                                start, dur, v["duration_sec"],
                            )
                        break
    return changes


def decode_mono_pcm(
    audio_path: str | Path,
    *,
    sample_rate: int = 16000,
) -> Tuple[List[float], int]:
    """Decode audio to normalised mono float samples via ffmpeg."""
    path = str(audio_path)
    proc = subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", path,
            "-ac", "1", "-ar", str(sample_rate),
            "-f", "f32le", "-",
        ],
        capture_output=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"PCM decode failed: {proc.stderr.decode()}")
    raw = proc.stdout
    count = len(raw) // 4
    samples = list(struct.unpack(f"<{count}f", raw)) if count else []
    return samples, sample_rate


def _rms(samples: Sequence[float]) -> float:
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def word_rms_scores(
    words: Sequence[WhisperWord],
    samples: Sequence[float],
    sample_rate: int,
) -> List[float]:
    scores: List[float] = []
    for w in words:
        i0 = max(0, int(w.start * sample_rate))
        i1 = min(len(samples), max(i0 + 1, int(w.end * sample_rate)))
        scores.append(_rms(samples[i0:i1]))
    return scores


def emphasis_score(word_rms: float, local_median: float) -> float:
    if local_median <= 0:
        return 1.0
    return word_rms / local_median


def _local_median(scores: Sequence[float], index: int, window: int = 15) -> float:
    lo = max(0, index - window)
    hi = min(len(scores), index + window + 1)
    chunk = sorted(scores[lo:hi])
    if not chunk:
        return 1.0
    mid = len(chunk) // 2
    return chunk[mid] if len(chunk) % 2 else (chunk[mid - 1] + chunk[mid]) / 2


def apply_emphasis_layout(
    verses: List[dict],
    data: TranscriptData,
    samples: Sequence[float],
    sample_rate: int,
    *,
    only_body_slides: bool = True,
) -> None:
    """Reassign slide_type/headline on verses using RMS emphasis (thematic decks)."""
    if not data.words or not verses:
        return
    rms_list = word_rms_scores(data.words, samples, sample_rate)
    for v in verses:
        if only_body_slides and v.get("slide_type") not in (None, "avatar_only"):
            continue
        start = float(v.get("audio_start_sec", 0))
        end = start + float(v.get("duration_sec", 0))
        window_words = [
            (i, w) for i, w in enumerate(data.words)
            if w.start >= start - 0.05 and w.end <= end + 0.05
        ]
        if not window_words:
            continue
        best_i, best_w = max(
            window_words,
            key=lambda iw: emphasis_score(rms_list[iw[0]], _local_median(rms_list, iw[0])),
        )
        score = emphasis_score(rms_list[best_i], _local_median(rms_list, best_i))
        phrase_words = [data.words[j].word for j in range(best_i, min(best_i + 6, len(data.words)))]
        phrase = normalise_text(" ".join(phrase_words))
        if score >= 1.4 and len(phrase.split()) <= 6:
            v["slide_type"] = "avatar_headline"
            v["headline"] = phrase.rstrip(".")
        elif score >= 1.2 and 7 <= len(phrase.split()) <= 20:
            v["slide_type"] = "avatar_quote"
            v["text"] = phrase
        elif v.get("slide_type") not in ("title_only",):
            if not v.get("headline") and score < 1.2:
                v["slide_type"] = "avatar_only"


def _srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def refine_word_onset(
    word: WhisperWord,
    samples: Sequence[float],
    sample_rate: int,
    window_sec: float = 0.2,
) -> float:
    """Nudge word start to first RMS rise above local threshold."""
    i0 = max(0, int((word.start - window_sec) * sample_rate))
    i1 = min(len(samples), int((word.start + window_sec) * sample_rate))
    if i1 <= i0:
        return word.start
    baseline = _rms(samples[i0:i0 + max(1, (i1 - i0) // 4)])
    threshold = max(baseline * 2, 0.01)
    for i in range(i0, i1):
        if abs(samples[i]) > threshold:
            return i / sample_rate
    return word.start


def write_word_srt(
    words: Sequence[WhisperWord],
    path: str | Path,
    *,
    samples: Optional[Sequence[float]] = None,
    sample_rate: int = 16000,
    refine_onset: bool = True,
) -> None:
    lines: List[str] = []
    for idx, w in enumerate(words, start=1):
        start = w.start
        if refine_onset and samples:
            start = refine_word_onset(w, samples, sample_rate)
        end = max(start + 0.05, w.end)
        lines.append(str(idx))
        lines.append(f"{_srt_time(start)} --> {_srt_time(end)}")
        lines.append(w.word.strip())
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def align_deck(
    deck: dict,
    data: TranscriptData,
    audio_path: str | Path,
    align: Sequence[str],
) -> dict:
    """Apply silence/emphasis alignment to deck verses in place."""
    verses = deck.get("sections", [{}])[0].get("verses", [])
    content = [v for v in verses if v.get("slide_type") != "title_only"]

    if "silence" in align:
        silences = detect_silences(audio_path)
        n = refine_verses(content, data, silences)
        logger.info("Silence alignment: %d boundary adjustment(s)", n)

    samples: Optional[List[float]] = None
    sr = 16000
    if "emphasis" in align or "karaoke" in align:
        try:
            samples, sr = decode_mono_pcm(audio_path)
        except Exception as exc:
            logger.warning("PCM decode skipped: %s", exc)

    if "emphasis" in align and samples:
        apply_emphasis_layout(content, data, samples, sr)

    return deck
