"""Protocol types for biblerevelation sermon article pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

StageKind = Literal["audit", "build", "validate", "image", "publish", "pack"]

BuilderKind = Literal["generic", "named", "existing_html", "manual"]


@dataclass(frozen=True)
class PipelineStep:
    id: str
    kind: StageKind
    label: str
    cli: str = ""
    optional: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "cli": self.cli or self.id,
            "optional": self.optional,
        }


@dataclass
class SermonJob:
    """One sermon → article → WordPress post."""

    slug: str
    title: str
    video_id: str
    pack_name: str
    transcript_file: str
    yaml_file: str
    topic: str
    excerpt: str = ""
    categories: str = "Gospel,Wisdom"
    post_id: int | None = None
    builder: BuilderKind = "generic"
    builder_name: str = ""
    existing_html: str = ""
    takeaway: list[str] = field(default_factory=list)
    reference_slug: str = ""
    reference_html: str = ""
    yaml_deck: str = ""
    skip: bool = False
    skip_reason: str = ""

    def agent_html_path(self, agent_dir: Path) -> Path:
        return agent_dir / f"biblerevelation-{self.slug}.html"

    def transcript_path(self, pack_dir: Path) -> Path:
        return pack_dir / self.transcript_file

    def yaml_path(self, pack_dir: Path) -> Path:
        return pack_dir / self.yaml_file

    def draft_html_path(self, draft_dir: Path) -> Path:
        return draft_dir / f"{self.slug}-gutenberg.html"

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "video_id": self.video_id,
            "pack_name": self.pack_name,
            "transcript_file": self.transcript_file,
            "yaml_file": self.yaml_file,
            "topic": self.topic,
            "excerpt": self.excerpt,
            "categories": self.categories,
            "post_id": self.post_id,
            "builder": self.builder,
            "builder_name": self.builder_name,
            "existing_html": self.existing_html,
            "takeaway": self.takeaway,
            "reference_slug": self.reference_slug,
            "reference_html": self.reference_html,
            "yaml_deck": self.yaml_deck,
            "skip": self.skip,
            "skip_reason": self.skip_reason,
        }


@dataclass
class SermonPack:
    pack_id: str
    pack_dir: Path
    yaml_examples_dir: Path
    draft_dir: Path
    cover_dir: Path
    visual_briefs_path: Path | None
    jobs: list[SermonJob]

    def active_jobs(self) -> list[SermonJob]:
        return [j for j in self.jobs if not j.skip]


@dataclass
class GapReport:
    slug: str
    transcript_words: int
    article_words: int
    ratio: float
    yaml_missing: list[str] = field(default_factory=list)
    raw_transcript_paste: bool = False
    generic_takeaway: bool = False
    missing_themes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.ratio >= 0.55 and not self.raw_transcript_paste and not self.yaml_missing

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "transcript_words": self.transcript_words,
            "article_words": self.article_words,
            "ratio": round(self.ratio, 3),
            "yaml_missing": self.yaml_missing,
            "raw_transcript_paste": self.raw_transcript_paste,
            "generic_takeaway": self.generic_takeaway,
            "missing_themes": self.missing_themes,
            "ok": self.ok,
        }


@dataclass
class ValidationReport:
    slug: str
    ok: bool
    ratio: float
    yaml_missing: list[str]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class PublishResult:
    slug: str
    post_id: int
    url: str
    http_status: int
    media_id: int | None = None
    ratio: float = 0.0
