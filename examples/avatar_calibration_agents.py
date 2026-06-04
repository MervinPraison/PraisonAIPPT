#!/usr/bin/env python3
"""
Three-phase avatar calibration (deterministic + optional Cursor SDK review).

Phase 1 — Sample: collect seek times from deck YAML (audio_start_sec).
Phase 2 — Tune: sweep crop_x via praisonaippt.avatar_calibrate (ffmpeg probes).
Phase 3 — Validate (optional): Cursor SDK agent reviews probe PNGs if CURSOR_API_KEY is set.

Usage:
  python examples/avatar_calibration_agents.py examples/heygen-50590-content.yaml
  python examples/avatar_calibration_agents.py examples/heygen-50590-content.yaml --sdk-review
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from praisonaippt.avatar_calibrate import (
    calibrate_deck_avatars,
    collect_avatar_seek_samples,
    format_calibration_report,
    merge_framing_into_slide_style,
)


def phase_sample(deck_path: Path) -> dict:
    data = yaml.safe_load(deck_path.read_text(encoding="utf-8")) or {}
    data["_source_file"] = str(deck_path.resolve())
    samples = collect_avatar_seek_samples(data)
    print("Phase 1 — Sample seeks per avatar:")
    for path, seeks in samples.items():
        print(f"  {path}: {seeks}")
    return data


def phase_tune(data: dict, *, force: bool) -> dict:
    print("\nPhase 2 — Tune crop_x (hybrid face detect + anchored balance refine):")
    results = calibrate_deck_avatars(data, force=force, source_file=data.get("_source_file"))
    print(format_calibration_report(results))
    return results


def phase_sdk_review(results: dict, *, model: str) -> None:
    api_key = os.environ.get("CURSOR_API_KEY")
    if not api_key:
        print("\nPhase 3 — Skipped (set CURSOR_API_KEY for SDK visual review)")
        return
    try:
        from cursor_sdk import Agent, AgentOptions, LocalAgentOptions
    except ImportError:
        print("\nPhase 3 — Skipped (pip install cursor-sdk for agent review)")
        return

    summary = format_calibration_report(results)
    prompt = (
        "Review this avatar PiP calibration summary for a talking-head deck. "
        "Confirm crop_x_ratio centres the face in the circle PiP. "
        "Reply with OK or suggest one adjusted crop_x between 0.40 and 0.56.\n\n"
        f"{summary}"
    )
    print("\nPhase 3 — SDK validation agent:")
    result = Agent.prompt(
        prompt,
        AgentOptions(
            api_key=api_key,
            model=model,
            local=LocalAgentOptions(cwd=str(ROOT)),
        ),
    )
    print(result.result or result.status)


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-phase avatar framing calibration")
    parser.add_argument("deck", type=Path, help="Deck YAML with avatar_video_path entries")
    parser.add_argument("--force", action="store_true", help="Ignore calibration cache")
    parser.add_argument("--write", action="store_true", help="Write crop_x into deck YAML")
    parser.add_argument("--sdk-review", action="store_true", help="Optional Cursor SDK review")
    parser.add_argument("--model", default="composer-2.5", help="SDK model id")
    args = parser.parse_args()

    if not args.deck.is_file():
        print(f"Deck not found: {args.deck}")
        return 1

    data = phase_sample(args.deck)
    results = phase_tune(data, force=args.force)
    if args.sdk_review:
        phase_sdk_review(results, model=args.model)

    if args.write and results:
        primary = next(iter(results.values()))
        data["slide_style"] = merge_framing_into_slide_style(
            data.get("slide_style") or {}, primary,
        )
        data.setdefault("avatar_calibration", {})["auto"] = True
        args.deck.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        print(f"\n✓ Wrote calibrated pip framing to {args.deck}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
