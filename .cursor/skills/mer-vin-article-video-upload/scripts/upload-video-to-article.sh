#!/usr/bin/env bash
# Upload MP4 to mer.vin Media Library and embed wp:video in article post_content.
# Usage: upload-video-to-article.sh VIDEO_FILE ARTICLE_ID_OR_SLUG [SECTION_HEADING]
set -euo pipefail

VIDEO="${1:?video file path required}"
ARTICLE="${2:?article ID, slug, or URL path required}"
HEADING="${3:-Short video walkthrough}"

WP_ROOT="/home/hestiaadmin/web/mer.vin/public_html"
cd "$WP_ROOT"

if [[ ! -f "$VIDEO" ]]; then
  echo "ERROR: Video not found: $VIDEO" >&2
  echo "On Mac, copy first: scp /path/to/video.mp4 hestia:/tmp/" >&2
  exit 1
fi

if [[ "$ARTICLE" =~ ^[0-9]+$ ]]; then
  POST_ID="$ARTICLE"
else
  SLUG="$ARTICLE"
  SLUG="${SLUG##*/}"
  SLUG="${SLUG%/}"
  POST_ID=$(wp post list --name="$SLUG" --field=ID --allow-root 2>/dev/null | head -1)
fi

if [[ -z "${POST_ID:-}" || "$POST_ID" == "0" ]]; then
  echo "ERROR: Could not resolve article: $ARTICLE" >&2
  exit 1
fi

TITLE=$(wp post get "$POST_ID" --field=post_title --allow-root)
echo "Article $POST_ID: $TITLE"

ATT_ID=$(wp media import "$VIDEO" \
  --post_id="$POST_ID" \
  --title="${HEADING} — post ${POST_ID}" \
  --porcelain --allow-root)

ATT_URL=$(wp post get "$ATT_ID" --field=guid --allow-root)
echo "Imported attachment $ATT_ID → $ATT_URL"

CONTENT=$(wp post get "$POST_ID" --field=post_content --allow-root)

if echo "$CONTENT" | grep -qF "$ATT_URL"; then
  echo "Video already embedded; nothing to do."
  exit 0
fi

BLOCK=$(cat <<EOF

<!-- wp:heading -->
<h2 class="wp-block-heading">${HEADING}</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If you prefer motion to static diagrams, this walkthrough covers the same story as the article in under a minute.</p>
<!-- /wp:paragraph -->

<!-- wp:video {"id":${ATT_ID}} -->
<figure class="wp-block-video"><video controls src="${ATT_URL}"></video></figure>
<!-- /wp:video -->

EOF
)

MARKER='<!-- wp:heading -->
<h2 class="wp-block-heading">At a glance</h2>'

NEW_CONTENT=$(CONTENT="$CONTENT" BLOCK="$BLOCK" MARKER="$MARKER" python3 <<'PY'
import os
content = os.environ["CONTENT"]
block = os.environ["BLOCK"]
marker = os.environ["MARKER"]
if marker in content:
    print(content.replace(marker, block + marker, 1))
else:
    print(content + block)
PY
)

TMP_CONTENT=$(mktemp)
trap 'rm -f "$TMP_CONTENT"' EXIT
printf '%s' "$NEW_CONTENT" > "$TMP_CONTENT"
wp post update "$POST_ID" --post_content="$(cat "$TMP_CONTENT")" --allow-root >/dev/null

echo "Updated post $POST_ID with wp:video block (attachment $ATT_ID)."
echo "Live: $(wp post get "$POST_ID" --field=url --allow-root)"
