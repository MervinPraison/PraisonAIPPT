"""Wrap biblerevelation-sermon-articles validators."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from .config import MIN_WORD_RATIO, VALIDATE_SKILL_DIR
from .faithful import DIGEST_OVERRIDES
from .transcript_flow import FLOW_BY_SLUG
from .protocol import SermonJob, SermonPack, ValidationReport
from .transcript import word_count


def _run(script: str, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATE_SKILL_DIR / script)] + args,
        capture_output=True,
        text=True,
    )


def validate(job: SermonJob, pack: SermonPack, html_path: Path) -> ValidationReport:
    tpath = job.transcript_path(pack.pack_dir)
    ypath = job.yaml_path(pack.pack_dir)
    base_args = ["--html", str(html_path), "--yaml", str(ypath)]

    min_ratio = 0.30 if job.slug in DIGEST_OVERRIDES or job.slug in FLOW_BY_SLUG else MIN_WORD_RATIO
    r1 = _run("validate_article.py", base_args + ["--transcript", str(tpath), "--min-ratio", str(min_ratio)])
    r2 = _run("audit_yaml_verses.py", base_args)

    out = r1.stdout + r1.stderr + r2.stdout + r2.stderr
    ratio_m = re.search(r"ratio[:\s=]+(\d+\.?\d*)%?", out, re.I)
    ratio = float(ratio_m.group(1)) / 100 if ratio_m else 0.0

    missing = [ln.strip() for ln in out.splitlines() if "MISSING" in ln or "YAML reference not found" in ln]
    errors = [ln.strip() for ln in out.splitlines() if ln.startswith("FAIL:")]
    warnings = [ln.strip() for ln in out.splitlines() if ln.startswith("WARN:")]
    if html_path.exists() and "Scripture-based study" in html_path.read_text(encoding="utf-8"):
        warnings = [w for w in warnings if "No closing footer" not in w]
    if "Result: FAIL" in out:
        errors.append("validate_article.py returned FAIL")

    if not ratio and html_path.exists():
        tw = word_count(tpath.read_text(encoding="utf-8"))
        hw = word_count(re.sub(r"<[^>]+>", " ", html_path.read_text(encoding="utf-8")))
        ratio = hw / tw if tw else 0.0

    ok = not errors and ratio >= min_ratio and not missing and not warnings
    return ValidationReport(slug=job.slug, ok=ok, ratio=ratio, yaml_missing=missing, warnings=warnings, errors=errors)
