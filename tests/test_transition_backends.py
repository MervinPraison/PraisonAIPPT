"""Tests for transition backend registry."""

from praisonaippt.transition_backends import (
    get_transition_backend,
    list_transition_backends,
    register_transition_backend,
)


def test_builtin_backends_registered():
    names = list_transition_backends()
    assert "segment_fade" in names
    assert "crossfade" in names
    assert "wipeleft" in names


def test_register_custom_backend():
    class CustomBackend:
        name = "custom_test"
        requires_reencode = True

        def ffmpeg_xfade_name(self):
            return "fade"

    register_transition_backend(CustomBackend())
    assert get_transition_backend("custom_test") is not None
