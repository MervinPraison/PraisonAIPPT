"""Segment sync validation — yaml / cue_timings / media_assets drift."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from praisonaippt.segment_video.validate_sync import validate_segment_sync


def test_validate_segment_sync_detects_yaml_cue_count_drift(tmp_path: Path):
    seg = tmp_path / "seg"
    seg.mkdir()
    (seg / "timestamps.json").write_text(json.dumps({
        "segments": [{"start": 0.0, "end": 5.0, "text": "Hello world test phrase."}],
        "words": [{"word": "Hello", "start": 0.0, "end": 0.5}],
    }))
    (seg / "cue_timings.json").write_text(json.dumps({
        "cues": [
            {"cue_index": 0, "audio_start_sec": 0.0, "duration_sec": 2.5, "script_fragment": "Hello"},
            {"cue_index": 1, "audio_start_sec": 2.5, "duration_sec": 2.5, "script_fragment": "world"},
        ],
    }))
    yaml_data = {
        "sections": [{"verses": [
            {"notes": "Hello", "audio_start_sec": 0.0, "duration_sec": 5.0},
        ]}],
    }
    (seg / "segment.yaml").write_text(yaml.dump(yaml_data))
    ok, issues = validate_segment_sync(seg)
    assert not ok
    assert any("yaml verses" in i for i in issues)
