"""Golden JPEG path resolution for slide_jpegs gate."""

from pathlib import Path

from praisonaippt.deck_pipeline import check_slide_jpegs


def test_golden_dir_resolves_relative_to_deck(tmp_path):
    img_dir = tmp_path / "slides"
    gold_dir = tmp_path / "slides" / "golden"
    img_dir.mkdir()
    gold_dir.mkdir()
    jpg = img_dir / "slide-001.jpg"
    jpg.write_bytes(b"x" * 6000)
    (gold_dir / "slide-001.jpg").write_bytes(b"x" * 6000)

    deck = tmp_path / "deck.yaml"
    deck.write_text("presentation_title: t\n")
    data = {
        "slide_images_dir": "slides",
        "pipeline": {"golden_slide_dir": "slides/golden"},
    }
    step = check_slide_jpegs(data, source_file=str(deck), golden_dir="slides/golden")
    assert step.ok, step.detail
