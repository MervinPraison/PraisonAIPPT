#!/usr/bin/env zsh
# Cue-aligned rebuild + spoken/visual validation gate.
# Usage: ./scripts/run-spoken-visual-gate.sh /path/to/daily_single/project [--assemble]

set -euo pipefail

PROJECT="${1:?project root (contains manifest.json)}"
DO_ASSEMBLE=false
[[ "${2:-}" == "--assemble" ]] && DO_ASSEMBLE=true

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate test 2>/dev/null || true

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO_ROOT"

daily-single -p "$PROJECT" build-captions
if $DO_ASSEMBLE; then
  daily-single -p "$PROJECT" assemble-beats
fi
daily-single -p "$PROJECT" validate-display
daily-single -p "$PROJECT" validate-spoken-visual
pytest tests/test_cue_slide_sync.py tests/test_spoken_visual_sync.py -q

echo "Reports:"
echo "  $PROJECT/merge/spoken_visual_sync_report.json"
echo "  $PROJECT/merge/display_sync_report.json"
