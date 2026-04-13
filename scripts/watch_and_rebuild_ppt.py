#!/usr/bin/env python3
"""
Poll a verses YAML file; when it changes, rebuild the matching PPTX (and optional Drive upload via YAML flags).

Usage (from repo root):
  python scripts/watch_and_rebuild_ppt.py examples/how_to_come_out_of_testing_and_trials.yaml examples/how_to_come_out_of_testing_and_trials.pptx

Requires: stdlib only. Ctrl+C to stop.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time


def main() -> int:
    p = argparse.ArgumentParser(description="Rebuild PPTX when the verses file changes.")
    p.add_argument("input_yaml", help="Path to verses .yaml / .json")
    p.add_argument("output_pptx", help="Path to write .pptx")
    p.add_argument(
        "-p",
        "--poll",
        type=float,
        default=0.75,
        help="Seconds between mtime checks (default: 0.75)",
    )
    args = p.parse_args()

    yaml_path = os.path.abspath(args.input_yaml)
    out_path = os.path.abspath(args.output_pptx)
    if not os.path.isfile(yaml_path):
        print(f"Error: not found: {yaml_path}", file=sys.stderr)
        return 1

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)

    def rebuild() -> None:
        cmd = [
            sys.executable,
            "-m",
            "praisonaippt.cli",
            "-i",
            os.path.relpath(yaml_path, root),
            "-o",
            os.path.relpath(out_path, root),
        ]
        print("\n--- change detected — rebuilding ---", flush=True)
        subprocess.run(cmd, check=False)

    try:
        mtime = os.path.getmtime(yaml_path)
    except OSError as e:
        print(f"Error stat {yaml_path}: {e}", file=sys.stderr)
        return 1

    print(
        f"Watching {yaml_path}\nOutput   {out_path}\nSave the YAML file to rebuild. Ctrl+C to stop.",
        flush=True,
    )
    while True:
        time.sleep(args.poll)
        try:
            t = os.path.getmtime(yaml_path)
        except OSError:
            continue
        if t != mtime:
            mtime = t
            rebuild()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped.")
        raise SystemExit(0)
