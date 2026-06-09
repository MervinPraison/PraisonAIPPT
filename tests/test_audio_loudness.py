"""Tests for audio loudness measurement parsing."""
from __future__ import annotations

from praisonaippt.segment_video.audio_loudness import (
    parse_loudnorm_summary,
    parse_volumedetect,
    validate_loudness_audit,
)


LOUDNORM_SAMPLE = """
[Parsed_loudnorm_0 @ 0x600003abc000] 
Input Integrated:    -23.0 LUFS
Input True Peak:      -4.5 dBTP
Input LRA:             7.0 LU
Input Threshold:     -33.2 LUFS
Target Offset:        +0.5 dB
"""


VOLUMEDETECT_SAMPLE = """
[Parsed_volumedetect_0 @ 0x600003abc000] mean_volume: -18.3 dB
[Parsed_volumedetect_0 @ 0x600003abc000] max_volume: -2.1 dB
"""


def test_parse_loudnorm_summary():
    m = parse_loudnorm_summary(LOUDNORM_SAMPLE)
    assert m.integrated_lufs == -23.0
    assert m.true_peak_dbtp == -4.5
    assert m.lra == 7.0
    assert m.threshold_lufs == -33.2
    assert m.offset == 0.5


def test_parse_volumedetect():
    m = parse_volumedetect(VOLUMEDETECT_SAMPLE)
    assert m.mean_volume_db == -18.3
    assert m.max_volume_db == -2.1


def test_validate_loudness_audit_spread():
    audit = {
        "segments": [
            {"dir": "01-a", "ok": True, "metrics": {"integrated_lufs": -16.2, "true_peak_dbtp": -2.0}},
            {"dir": "02-b", "ok": True, "metrics": {"integrated_lufs": -15.8, "true_peak_dbtp": -2.5}},
        ],
        "summary": {"spread_lufs": 0.4},
    }
    cfg = {"target_lufs": -16.0, "tolerance_lufs": 1.0, "max_spread_lufs": 2.0, "warn_true_peak_dbtp": -1.0}
    ok, issues = validate_loudness_audit(audit, cfg)
    assert ok
    assert not issues


def test_validate_loudness_audit_fails_spread():
    audit = {
        "segments": [
            {"dir": "01-a", "ok": True, "metrics": {"integrated_lufs": -20.0}},
            {"dir": "02-b", "ok": True, "metrics": {"integrated_lufs": -14.0}},
        ],
        "summary": {"spread_lufs": 6.0},
    }
    cfg = {"target_lufs": -16.0, "tolerance_lufs": 1.0, "max_spread_lufs": 2.0}
    ok, issues = validate_loudness_audit(audit, cfg)
    assert not ok
    assert any("spread" in i for i in issues)
