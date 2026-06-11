"""Brand bumper and slide word-map tests."""
from pathlib import Path

import pytest

from praisonaippt.daily_single.brand_bumper import bumper_available, prepare_brand_bumper, repo_brand_bumper_path
from praisonaippt.daily_single.slide_word_map import validate_beat01_slide_word_map, words_in_range
from praisonaippt.daily_single.text_slide import slide_specs
from praisonaippt.transcript_loader import load_whisper_json


def test_repo_brand_bumper_exists():
    assert repo_brand_bumper_path().is_file()


@pytest.mark.skipif(not bumper_available(), reason="brand bumper asset missing")
def test_prepare_brand_bumper(tmp_path: Path):
    out = prepare_brand_bumper(tmp_path)
    assert out is not None
    video, audio = out
    assert video.is_file() and audio.is_file()


def test_beat01_single_summary_slide():
    specs = slide_specs()["beat-01-rest"]
    assert len(specs) == 1
    assert specs[0]["file"] == "beat1-launch-summary.png"
    assert len(specs[0]["bullets"]) == 3


def test_beat01_slide_word_map_on_project():
    from praisonaippt.daily_single.project import DailySingleProject

    root = Path("examples/videos/anthropic-claude-fable-5-mythos-5")
    if not root.is_dir():
        pytest.skip("Fable pilot not present")
    project = DailySingleProject.from_root(root)
    ts = project.segments_dir / "01-cold-open" / "timestamps.json"
    if not ts.is_file():
        pytest.skip("run build-captions on pilot first")
    ok, report = validate_beat01_slide_word_map(project)
    assert ok, report
