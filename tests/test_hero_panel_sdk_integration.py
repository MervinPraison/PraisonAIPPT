"""Integration: hero text SDK → merged YAML → measured panel clearance."""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from praisonaippt.hero_panel_calibrate import (
    calibrate_deck_hero_panels,
    maybe_auto_place_hero_text_deck,
)
from praisonaippt.hero_panel_measure import (
    measure_hero_panel_image,
    placement_advice,
    save_hero_panel_validation_diagram,
)
from praisonaippt.utils import resolve_asset_path
from praisonaippt.video_exporter import iter_slide_plan

PKG = Path(__file__).resolve().parent.parent
HEYGEN_IMAGES = PKG / "examples" / "heygen-50590-video-audio-heygen-images.yaml"
MIN_CALIB_CONFIDENCE = 0.35


def _hero_verses(data: dict):
    for entry in iter_slide_plan(data):
        if (entry.get("slide_type") or "") != "avatar_media_3":
            continue
        verse = entry.get("verse") if isinstance(entry.get("verse"), dict) else entry
        if verse.get("media_path"):
            yield verse


@pytest.mark.skipif(not HEYGEN_IMAGES.is_file(), reason="HeyGen images YAML missing")
def test_sdk_pipeline_calibrates_and_measures_hero_panels(tmp_path):
    """SDK sweep + auto-merge must yield measurable panel clearances on hero screenshots."""
    data = yaml.safe_load(HEYGEN_IMAGES.read_text(encoding="utf-8"))
    sf = str(HEYGEN_IMAGES.resolve())
    data["_source_file"] = sf
    style = data.get("slide_style") or {}

    results = calibrate_deck_hero_panels(data, force=True, source_file=sf)
    assert len(results) >= 3, "expected hero slides with anchor:auto"

    merged = maybe_auto_place_hero_text_deck(data, source_file=sf)
    measured = 0
    for verse in _hero_verses(merged):
        media = verse.get("media_path")
        resolved = resolve_asset_path(str(media), source_file=sf)
        assert resolved and Path(resolved).is_file(), f"missing hero image: {media}"

        metrics, result = measure_hero_panel_image(
            resolved, style=style, data=merged, verse=verse,
        )
        assert result.anchor in {
            "top_left", "top_right", "top", "bottom_left", "bottom_right", "bottom",
        }
        assert result.confidence >= MIN_CALIB_CONFIDENCE, result.summary_line()
        assert metrics.panel_width > 0 and metrics.panel_height > 0
        assert metrics.min_clearance_px >= 0

        advice = placement_advice(metrics)
        assert advice.summary

        out = tmp_path / f"{Path(resolved).stem}_validation.png"
        saved = save_hero_panel_validation_diagram(
            resolved, metrics, out, style=style, data=merged, verse=verse, result=result,
        )
        assert saved.is_file() and saved.stat().st_size > 800
        measured += 1

    assert measured >= 3
    anchors = {
        v.get("_hero_panel_anchor")
        for v in _hero_verses(merged)
        if v.get("_hero_panel_anchor")
    }
    assert len(anchors) >= 3


@pytest.mark.skipif(not HEYGEN_IMAGES.is_file(), reason="HeyGen images YAML missing")
def test_hero_panel_centre_cli_deck_slide(tmp_path):
    """CLI hero-panel-centre -i deck --slide N resolves media and writes diagram."""
    out = tmp_path / "cli_hero_val.png"
    proc = subprocess.run(
        [
            sys.executable, "-m", "praisonaippt.cli",
            "hero-panel-centre",
            "-i", str(HEYGEN_IMAGES),
            "--slide", "2",
            "--validation-image", str(out),
        ],
        cwd=str(PKG),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "Hero text panel measurement" in proc.stdout
    assert out.is_file() and out.stat().st_size > 800
