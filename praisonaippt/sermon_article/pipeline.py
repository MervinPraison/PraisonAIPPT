"""Pipeline stage definitions — single source of truth."""
from __future__ import annotations

from .protocol import PipelineStep

GAP_AUDIT = PipelineStep("gap-audit", "audit", "Transcript ↔ article gap analysis", cli="gap-audit")
BUILD = PipelineStep("build", "build", "Build Gutenberg HTML from transcript + YAML", cli="build")
VALIDATE = PipelineStep("validate", "validate", "Run validate_article + audit_yaml_verses", cli="validate")
STRUCTURE_AUDIT = PipelineStep("structure-audit", "audit", "Block raw-paste / Teaching Block articles", cli="structure-audit")
IMAGES = PipelineStep("images", "image", "Generate unique sermon-specific featured covers", cli="images")
PUBLISH_UPDATE = PipelineStep("publish-update", "publish", "Update live WordPress posts", cli="publish-update")
PUBLISH_CREATE = PipelineStep("publish-create", "publish", "Create new WordPress posts", cli="publish-create")

ARTICLE_PIPELINE: tuple[PipelineStep, ...] = (
    GAP_AUDIT,
    BUILD,
    VALIDATE,
    STRUCTURE_AUDIT,
    IMAGES,
    PUBLISH_UPDATE,
)

FULL_PUBLISH_PIPELINE: tuple[PipelineStep, ...] = (
    GAP_AUDIT,
    BUILD,
    VALIDATE,
    IMAGES,
    PUBLISH_CREATE,
)


def parse_stages(spec: str) -> list[PipelineStep]:
    """Parse comma-separated stage ids."""
    by_id = {s.id: s for s in (*ARTICLE_PIPELINE, PUBLISH_CREATE, STRUCTURE_AUDIT)}
    ids = [s.strip() for s in spec.split(",") if s.strip()]
    out: list[PipelineStep] = []
    for sid in ids:
        if sid not in by_id:
            raise ValueError(f"Unknown stage: {sid}. Choose from: {', '.join(by_id)}")
        out.append(by_id[sid])
    return out
