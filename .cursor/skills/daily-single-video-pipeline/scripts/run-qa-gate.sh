#!/usr/bin/env zsh
# Run one validate-qa gate for a daily_single project.
# Usage: ./scripts/run-qa-gate.sh /path/to/project pre_build|pre_assemble|post_vo|post_build|all

set -euo pipefail

PROJECT="${1:?project root}"
WHEN="${2:-all}"

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate test

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO_ROOT"

daily-single -p "$PROJECT" validate-qa --when "$WHEN"
echo "Summary: $PROJECT/merge/qa/summary.json"
