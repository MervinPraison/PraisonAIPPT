"""Load daily_single project paths from manifest.json."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DailySingleProject:
    root: Path
    slug: str
    research_dir: Path
    beat_map_path: Path
    assets_dir: Path
    segments_dir: Path
    beats_dir: Path
    merge_dir: Path

    @classmethod
    def from_root(cls, root: Path | str) -> DailySingleProject:
        root = Path(root).resolve()
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        research = Path(manifest["create_news_research"]).resolve()
        slug = manifest.get("slug") or research.name
        topic = slug
        assets = research / "review-assets" / topic
        beat_map = Path(manifest.get("beat_map") or research / "video-understanding" / "beat-map.json")
        return cls(
            root=root,
            slug=slug,
            research_dir=research,
            beat_map_path=beat_map.resolve(),
            assets_dir=assets,
            segments_dir=root / "segments",
            beats_dir=root / "beats",
            merge_dir=root / "merge",
        )

    @property
    def video_script_path(self) -> Path:
        return self.research_dir / "video-script.md"

    @property
    def protocol_path(self) -> Path:
        return self.root / "scripts" / "config" / "protocol.json"

    def segment_script(self, seg_dir: str) -> Path:
        return self.segments_dir / seg_dir / "script.md"

    def segment_narration(self, seg_dir: str) -> Path:
        return self.segments_dir / seg_dir / "narration.mp3"
