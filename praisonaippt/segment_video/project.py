from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .manifest import load_manifest
from .media import ffprobe_duration


@dataclass
class SegmentVideoProject:
    root: Path

    @classmethod
    def from_path(cls, path: str | Path) -> SegmentVideoProject:
        root = Path(path).resolve()
        if not (root / "manifest.json").is_file():
            raise FileNotFoundError(f"manifest.json not found in {root}")
        return cls(root=root)

    @property
    def scripts_dir(self) -> Path:
        return self.root / "scripts"

    @property
    def protocol_path(self) -> Path:
        return self.scripts_dir / "config" / "protocol.json"

    @property
    def state_dir(self) -> Path:
        d = self.root / ".segment-video"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def repo_root(self) -> Path:
        return self.root.parents[1]

    def load_protocol(self) -> dict:
        return json.loads(self.protocol_path.read_text(encoding="utf-8"))

    def save_protocol(self, protocol: dict) -> None:
        self.protocol_path.write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")

    def load_manifest(self) -> dict:
        return load_manifest(self.root)

    def segment_dirs(self) -> list[str]:
        return [s["dir"] for s in self.load_manifest().get("segments", [])]

    def segment_status(self, seg_dir: str) -> dict:
        base = self.root / "segments" / seg_dir
        checks = {
            "script": (base / "script.md").is_file(),
            "narration": (base / "narration.mp3").is_file(),
            "heygen": (base / "heygen.mp4").is_file(),
            "yaml": (base / "segment.yaml").is_file(),
            "mp4": (base / "segment.mp4").is_file(),
        }
        dur = None
        if checks["mp4"]:
            dur = round(ffprobe_duration(base / "segment.mp4"), 2)
        return {"dir": seg_dir, "checks": checks, "duration_sec": dur, "ok": all(checks.values())}
