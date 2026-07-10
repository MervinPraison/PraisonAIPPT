"""Tests for sermon article SDK."""
from pathlib import Path

import pytest

from praisonaippt.sermon_article.engine import SermonArticleEngine
from praisonaippt.sermon_article.pack import load_pack
from praisonaippt.sermon_article.pipeline import parse_stages
from praisonaippt.sermon_article.yaml_map import load_yaml_refs, sermon_signals

PACK_YAML = Path(__file__).resolve().parents[1] / "examples" / "sermon_packs" / "bic_pack2.yaml"


def test_load_pack_has_jobs():
    pack = load_pack(PACK_YAML)
    assert pack.pack_id == "bic-pack-2"
    assert len(pack.jobs) >= 12
    active = pack.active_jobs()
    assert all(not j.skip for j in active)
    assert any(j.slug == "great-faith-centurion-canaanite-woman" and j.skip for j in pack.jobs)


def test_engine_manifest():
    engine = SermonArticleEngine(PACK_YAML)
    m = engine.manifest()
    assert m["pack_id"] == "bic-pack-2"
    assert len(m["jobs"]) >= 12


def test_parse_stages():
    steps = parse_stages("gap-audit,build,validate")
    assert [s.id for s in steps] == ["gap-audit", "build", "validate"]


def test_yaml_map_helpers():
    sig = sermon_signals("The first Adam and last Adam in Psalm 34")
    assert any("First Adam" in s for s in sig)


def test_visual_briefs_path():
    pack = load_pack(PACK_YAML)
    assert pack.visual_briefs_path is not None
    assert pack.visual_briefs_path.exists()
