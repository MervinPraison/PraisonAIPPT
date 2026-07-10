#!/usr/bin/env bash
# Upload Pack-2 featured covers and set _thumbnail_id
set -eo pipefail

RESULTS="/tmp/pack2_cover_uploads.tsv"
echo -e "slug\tpost_id\tmedia_id" > "$RESULTS"

upload_cover() {
  local slug="$1" post_id="$2"
  local cover="/tmp/pack2-covers/${slug}-cover.png"
  local marker="/tmp/pack2-covers/.uploaded-${slug}"
  [[ -f "$cover" ]] || return 0
  [[ -f "$marker" ]] && return 0

  echo "=== Upload $slug ==="
  local UPLOAD_OUT MEDIA_ID
  UPLOAD_OUT=$(bash -lc "praisonaiwp media upload '$cover' --server biblerevelation \
    --post-id $post_id --title '${slug} cover' --alt 'Featured image for ${slug}'" 2>&1)
  MEDIA_ID=$(echo "$UPLOAD_OUT" | grep -oE 'ID: [0-9]+' | tail -1 | grep -oE '[0-9]+' || true)
  if [[ -z "$MEDIA_ID" ]]; then
    MEDIA_ID=$(echo "$UPLOAD_OUT" | grep -oE 'Media ID: [0-9]+' | tail -1 | grep -oE '[0-9]+' || true)
  fi
  if [[ -n "$MEDIA_ID" ]]; then
    bash -lc "praisonaiwp update $post_id --server biblerevelation --meta '{\"_thumbnail_id\":\"$MEDIA_ID\"}'"
    touch "$marker"
    echo -e "${slug}\t${post_id}\t${MEDIA_ID}" >> "$RESULTS"
    echo "OK|$slug|$MEDIA_ID"
  else
    echo "FAIL|$slug|no media id" >&2
  fi
}

upload_cover "gospel-of-christ-hear-right-covenant" 240543
upload_cover "first-adam-vs-last-adam-identity-in-christ" 240545
upload_cover "miracles-are-easy-stand-still" 240547
upload_cover "freedom-from-troubles-righteousness-apart-from-works" 240549
upload_cover "full-restoration-hundred-percent-in-christ" 240551
upload_cover "be-fruitful-and-multiply-every-area" 240553
upload_cover "why-delay-abraham-instant-blessing" 240555
upload_cover "freedom-in-the-spirit-son-and-father" 240557
upload_cover "why-listen-to-the-word-of-god" 240559
upload_cover "heir-of-the-world-through-faith-not-law" 240561
upload_cover "holy-communion-one-reason-for-sickness" 240563
upload_cover "miracles-are-easy-next-level-faith" 240565

cat "$RESULTS"
