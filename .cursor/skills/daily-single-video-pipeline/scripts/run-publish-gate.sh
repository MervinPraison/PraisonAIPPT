#!/usr/bin/env zsh
# Thin wrapper — publish gate order lives in praisonaippt.daily_single.pipeline (SDK).
# Usage: ./scripts/run-publish-gate.sh /path/to/daily_single/project [--assemble]

set -euo pipefail

PROJECT="${1:?project root (contains manifest.json)}"
EXTRA=()
[[ "${2:-}" == "--assemble" ]] && EXTRA=(--assemble)

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate test 2>/dev/null || true

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO_ROOT"

daily-single -p "$PROJECT" pipeline publish-gate "${EXTRA[@]}"

echo "Reports under $PROJECT/merge/"
