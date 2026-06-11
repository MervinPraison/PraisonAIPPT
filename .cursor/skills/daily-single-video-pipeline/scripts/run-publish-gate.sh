#!/usr/bin/env zsh
# Full publish gate matrix (V1–V13): sync + professional + viral quality.
# Usage: ./scripts/run-publish-gate.sh /path/to/daily_single/project [--assemble]

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

echo "=== V1 unit tests ==="
pytest tests/test_cue_slide_sync.py tests/test_spoken_visual_sync.py tests/test_slide_design_audit.py tests/test_engagement_audit.py tests/test_viral_readiness.py tests/test_video_qa.py -q

echo "=== V3 validate-display ==="
daily-single -p "$PROJECT" validate-display

echo "=== V4 validate-spoken-visual ==="
daily-single -p "$PROJECT" validate-spoken-visual

echo "=== V5 validate-slide-quality ==="
daily-single -p "$PROJECT" validate-slide-quality

echo "=== V6 validate-engagement-assets ==="
daily-single -p "$PROJECT" validate-engagement-assets

echo "=== V7 validate-viral-readiness ==="
daily-single -p "$PROJECT" validate-viral-readiness

echo "=== V8 audit-visual ==="
daily-single -p "$PROJECT" audit-visual || true

echo "=== V9 validate-hook-attention ==="
daily-single -p "$PROJECT" validate-hook-attention

echo "=== V10 validate-canonical-scroll ==="
daily-single -p "$PROJECT" validate-canonical-scroll || true

echo "=== V11 validate-sync (3 runs) ==="
daily-single -p "$PROJECT" validate-sync --runs 3

echo "=== V12 validate-all ==="
daily-single -p "$PROJECT" validate-all

echo "=== V13 validate-qa post_build ==="
daily-single -p "$PROJECT" validate-qa --when post_build

echo "PASS: publish gate matrix complete"
echo "Reports under $PROJECT/merge/"
