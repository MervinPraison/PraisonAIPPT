#!/usr/bin/env zsh
# Downstream gap audit for segment-video roundup projects.
# Usage: gap-audit.sh [project_root]
# Example: gap-audit.sh examples/june-2026-ai-roundup
set -euo pipefail

ROOT="${1:-examples/june-2026-ai-roundup}"
SCRIPTS="$ROOT/scripts"

if [[ ! -f "$ROOT/manifest.json" ]]; then
  echo "error: no manifest.json in $ROOT" >&2
  exit 1
fi

cd "$SCRIPTS"

echo "=== validate-all ==="
python3 pipeline.py validate-all 2>&1 | tail -40

echo ""
echo "=== segment duration drift (heygen vs segment.mp4 >0.5s) ==="
python3 << PY
import json, subprocess
from pathlib import Path
root = Path("$ROOT")
for d in sorted((root / "segments").iterdir()):
    if not d.is_dir():
        continue
    hg, mp4 = d / "heygen.mp4", d / "segment.mp4"
    if not hg.is_file() or not mp4.is_file():
        continue
    def dur(p):
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
            capture_output=True, text=True,
        )
        return float(r.stdout.strip() or 0)
    drift = abs(dur(hg) - dur(mp4))
    if drift > 0.5:
        print(f"  DRIFT {d.name}: heygen={dur(hg):.2f}s segment={dur(mp4):.2f}s drift={drift:.2f}s")
PY

echo ""
echo "=== cue count mismatches ==="
python3 << PY
import json, yaml
from pathlib import Path
root = Path("$ROOT")
ma = json.loads((root / "media_assets.json").read_text()) if (root / "media_assets.json").is_file() else {}
for d in sorted((root / "segments").iterdir()):
    if not d.is_dir():
        continue
    yp, cp = d / "segment.yaml", d / "cue_timings.json"
    if not yp.is_file() or not cp.is_file():
        continue
    mc = len((ma.get("segments", {}).get(d.name) or {}).get("cues") or [])
    ct = len(json.loads(cp.read_text()).get("cues") or [])
    yv = len(yaml.safe_load(yp.read_text())["sections"][0]["verses"])
    if mc and (mc != ct or ct != yv):
        print(f"  MISMATCH {d.name}: media={mc} timings={ct} verses={yv}")
PY

echo ""
echo "=== final video ==="
ls -lh "$ROOT/merge/final-roundup.mp4" 2>/dev/null || echo "  (missing merge/final-roundup.mp4)"
