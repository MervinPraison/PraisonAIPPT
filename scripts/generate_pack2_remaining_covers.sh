#!/usr/bin/env bash
# Generate remaining Pack-2 covers (skip existing files)
set -eo pipefail

BRIEFS="/Users/praison/praisonaippt/scripts/pack2_sermon_visual_briefs.yaml"
OUT_DIR="/tmp/pack2-covers"
mkdir -p "$OUT_DIR"

zsh -c "source \$(conda info --base)/etc/profile.d/conda.sh && conda activate test && python3 <<'PY'
import yaml
from pathlib import Path
briefs = yaml.safe_load(Path('$BRIEFS').read_text())['briefs']
out_dir = Path('$OUT_DIR')
for slug, b in briefs.items():
    out = out_dir / f'{slug}-cover.png'
    if out.exists():
        print(f'SKIP|{slug}|exists')
        continue
    prompt = (
        b['concept']
        + '. Photorealistic biblical faith illustration, soft cinematic lighting, '
        'wide horizontal banner composition 1536x1024, rich colour, '
        'absolutely no text, no letters, no numbers, no logos, no watermarks.'
    )
    (out_dir / f'{slug}-prompt.txt').write_text(prompt, encoding='utf-8')
    print(f'NEED|{slug}|{out}')
PY" | while IFS='|' read -r kind slug path; do
  if [[ "$kind" == "NEED" ]]; then
    PROMPT=$(cat "/tmp/pack2-covers/${slug}-prompt.txt")
    echo "=== Generating $slug ==="
    cd ~/create-post/gpt-image && uv run scripts/generate.py \
      --prompt "$PROMPT" --size 1536x1024 --quality high --output "$path" \
      || echo "FAIL|$slug" >&2
    echo "DONE|$slug|$path"
  fi
done
