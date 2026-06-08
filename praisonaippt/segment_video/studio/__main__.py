"""Launch Studio: python -m praisonaippt.segment_video.studio"""
import sys

from ..cli import main

if __name__ == "__main__":
    args = sys.argv[1:]
    if "studio" not in args:
        args = ["studio"] + args
    if "-p" not in args and "--project" not in args:
        args = ["--project", "."] + args
    raise SystemExit(main(args))
