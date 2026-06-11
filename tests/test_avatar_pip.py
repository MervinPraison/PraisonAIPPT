"""Circle avatar PiP — June roundup geometry."""
from praisonaippt.daily_single.avatar_pip import (
    PIP_WIDTH_RATIO,
    circle_pip_filter_complex,
    pip_width_px,
)


def test_pip_width_matches_june_roundup_ratio():
    assert pip_width_px(frame_w=1920) == 384
    assert PIP_WIDTH_RATIO == 0.2


def test_circle_filter_in_pip_chain():
    fc = circle_pip_filter_complex()
    assert "overlay=W-w-60:H-h-60" in fc
    assert "geq=" in fc
    assert "[pip]" in fc and "[bg][pip]overlay" in fc
