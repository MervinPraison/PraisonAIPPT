#!/usr/bin/env bash
# Biblerevelation sermon article SDK — thin wrapper
#
# Usage:
#   SERMON_PACK=examples/sermon_packs/bic_pack2.yaml scripts/sermon_article.sh validate
#   SERMON_PACK=examples/sermon_packs/bic_pack2.yaml scripts/sermon_article.sh validate --slug my-sermon
#
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"

PACK="${SERMON_PACK:-}"
ARGS=("$@")
if [[ -z "$PACK" && ${#ARGS[@]} -ge 2 && "${ARGS[0]}" == "--pack" ]]; then
  PACK="${ARGS[1]}"
  ARGS=("${ARGS[@]:2}")
fi
if [[ -z "$PACK" ]]; then
  echo "Set SERMON_PACK or pass --pack <examples/sermon_packs/*.yaml>" >&2
  exit 1
fi

SLUG=""
CMD_ARGS=()
i=0
while [[ $i -lt ${#ARGS[@]} ]]; do
  if [[ "${ARGS[$i]}" == "--slug" && $((i + 1)) -lt ${#ARGS[@]} ]]; then
    SLUG="${ARGS[$((i + 1))]}"
    i=$((i + 2))
  else
    CMD_ARGS+=("${ARGS[$i]}")
    i=$((i + 1))
  fi
done

PY_ARGS=(--pack "$PACK")
[[ -n "$SLUG" ]] && PY_ARGS+=(--slug "$SLUG")

zsh -c "source \$(conda info --base)/etc/profile.d/conda.sh && conda activate test && cd '$REPO' && python -m praisonaippt.sermon_article.cli ${PY_ARGS[*]} ${CMD_ARGS[*]}"
