#!/usr/bin/env zsh
# Downstream gap audit for segment-video roundup projects.
# Usage: gap-audit.sh [project_root]
# Example: gap-audit.sh examples/videos/june-2026-ai-roundup
set -euo pipefail

ROOT="${1:-examples/videos/june-2026-ai-roundup}"
SCRIPTS="$ROOT/scripts"

if [[ ! -f "$ROOT/manifest.json" ]]; then
  echo "error: no manifest.json in $ROOT" >&2
  exit 1
fi

cd "$SCRIPTS"

echo "=== validate-all ==="
python3 pipeline.py validate-all 2>&1 | tail -40 || true

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

echo ""
echo "=== HD resolution (expect 1920x1080 on all segment.mp4 + final) ==="
python3 << PY
import subprocess
from pathlib import Path
root = Path("$ROOT")

def wh(p):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(p)],
        capture_output=True, text=True,
    )
    return r.stdout.strip()

bad = []
for d in sorted((root / "segments").iterdir()):
    mp4 = d / "segment.mp4"
    if not mp4.is_file():
        continue
    spec = wh(mp4)
    ok = spec.startswith("1920,1080")
    if not ok:
        bad.append(f"  NOT HD {d.name}: {spec}")
final = root / "merge/final-roundup.mp4"
if final.is_file():
    spec = wh(final)
    ok = spec.startswith("1920,1080")
    print(f"  final-roundup.mp4: {spec} {'OK' if ok else 'NOT HD'}")
    if not ok:
        bad.append(f"  NOT HD final: {spec}")
else:
    print("  (missing merge/final-roundup.mp4)")
    bad.append("  missing final-roundup.mp4")
if bad:
    for line in bad:
        print(line)
else:
    print("  all checked files 1920x1080")
PY

echo ""
echo "=== loudness audit (segment.mp4 LUFS) ==="
python3 << PY
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path("$SCRIPTS").resolve().parents[1]))
from praisonaippt.segment_video.audio_loudness import audit_segments, loudness_config, validate_loudness_audit

root = Path("$ROOT")
manifest = json.loads((root / "manifest.json").read_text())
protocol = json.loads((root / "scripts/config/protocol.json").read_text())
cfg = loudness_config(protocol)
audit = audit_segments(root, manifest)
s = audit.get("summary") or {}
print(f"  measured: {s.get('measured', 0)}/{s.get('count', 0)}")
if s.get("median_lufs") is not None:
    print(f"  median: {s['median_lufs']} LUFS  spread: {s.get('spread_lufs')} LUFS  range: {s.get('min_lufs')} .. {s.get('max_lufs')}")
ok, issues = validate_loudness_audit(audit, cfg)
for row in audit.get("segments") or []:
    if not row.get("ok"):
        continue
    lufs = (row.get("metrics") or {}).get("integrated_lufs")
    if lufs is not None:
        flag = "OK" if abs(lufs - cfg["target_lufs"]) <= cfg.get("tolerance_lufs", 1.0) else "OUT"
        print(f"  [{flag}] {row['dir']}: {lufs:.1f} LUFS")
if issues:
    print("  issues:")
    for i in issues[:8]:
        print(f"    - {i}")
PY
