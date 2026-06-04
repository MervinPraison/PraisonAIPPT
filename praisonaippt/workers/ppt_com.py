"""Windows PowerPoint CreateVideo worker — Phase 3 (on-prem only, not implemented in v1)."""

from __future__ import annotations


def create_video_via_powerpoint(pptx_path: str, output_path: str) -> str:
    raise NotImplementedError(
        "PowerPoint CreateVideo worker is not implemented. "
        "Use backend=compositor on Mac/Linux."
    )
