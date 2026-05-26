#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Validate gpt-image skill scripts without calling the API (optional --generate smoke test)."""

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parents[2]  # ppt-package repo root
GENERATE = SKILL_ROOT / "scripts" / "generate.py"
EDIT = SKILL_ROOT / "scripts" / "edit.py"
OUT_TEST = REPO_ROOT / "assets" / "generated" / "skill_test.png"


def _load_validate_size():
    spec = importlib.util.spec_from_file_location("gen", GENERATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.validate_size


def main():
    parser = argparse.ArgumentParser(description="Validate gpt-image skill setup")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Run a small live gpt-image-2 generation (uses API credits)",
    )
    args = parser.parse_args()
    errors = []

    for path in (GENERATE, EDIT, SKILL_ROOT / "SKILL.md", SKILL_ROOT / "references" / "prompting-guide.md"):
        if not path.is_file():
            errors.append(f"Missing: {path}")

    validate_size = _load_validate_size()
    for size in ("1536x864", "1024x1024", "auto"):
        try:
            validate_size(size)
        except ValueError as e:
            errors.append(f"validate_size({size}): {e}")

    try:
        validate_size("100x100")
        errors.append("validate_size should reject 100x100")
    except ValueError:
        pass

    if not shutil_which("uv"):
        errors.append("uv not found on PATH (needed for generate.py / edit.py)")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)

    print("✓ Skill files present")
    print("✓ Size validation OK")
    print("✓ uv available")

    if not args.generate:
        key = os.environ.get("OPENAI_API_KEY")
        if key:
            print("✓ OPENAI_API_KEY set (ready for generate)")
        else:
            print("○ OPENAI_API_KEY not set (add .env or export for live generation)")
        print("\nRun with --generate to create assets/generated/skill_test.png")
        return

    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY required for --generate", file=sys.stderr)
        sys.exit(1)

    OUT_TEST.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "uv", "run", str(GENERATE),
        "--prompt",
        "Minimal test card: dark blue background, single gold star in the centre, "
        "text \"PPT skill test\" below the star, flat design, no watermark, no logo.",
        "--size", "1536x864",
        "--quality", "low",
        "--output", str(OUT_TEST),
    ]
    print("Running live generation smoke test...")
    try:
        subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        out = (exc.stdout or "") + (exc.stderr or "")
        if "billing" in out.lower() or "insufficient" in out.lower():
            print("○ Live generation skipped: OpenAI billing/quota limit (scripts and API key OK)")
            print("  Fix billing at https://platform.openai.com/account/billing then re-run with --generate")
            return
        print(out, file=sys.stderr)
        raise

    if not OUT_TEST.is_file() or OUT_TEST.stat().st_size < 1000:
        print(f"FAIL: output missing or too small: {OUT_TEST}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ Live generation OK: {OUT_TEST} ({OUT_TEST.stat().st_size} bytes)")


def shutil_which(cmd):
    from shutil import which
    return which(cmd)


if __name__ == "__main__":
    main()
