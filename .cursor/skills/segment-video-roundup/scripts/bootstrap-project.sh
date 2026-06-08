#!/usr/bin/env zsh
# Bootstrap a new segment-video roundup project from the June 2026 template.
# Usage: bootstrap-project.sh SLUG RESEARCH_DIR POST_ID
# Example: bootstrap-project.sh august-2026-ai-roundup /Users/praison/create-news/research/august-2026-ai-roundup 52000
set -euo pipefail

SLUG="${1:?slug required, e.g. august-2026-ai-roundup}"
RESEARCH="${2:?research dir required}"
POST_ID="${3:?wordpress post id required}"

REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
TEMPLATE="$REPO/examples/june-2026-ai-roundup"
DEST="$REPO/examples/${SLUG}"

if [[ -d "$DEST" ]]; then
  echo "ERROR: $DEST already exists" >&2
  exit 1
fi
if [[ ! -d "$RESEARCH" ]]; then
  echo "ERROR: research dir not found: $RESEARCH" >&2
  exit 1
fi

mkdir -p "$DEST"
# Copy pipeline infrastructure only
cp -R "$TEMPLATE/scripts" "$DEST/"
cp "$TEMPLATE/PROTOCOL.md" "$DEST/" 2>/dev/null || true
mkdir -p "$DEST/slide_images" "$DEST/merge" "$DEST/segments"

python3 <<PY
import json
from pathlib import Path

dest = Path("$DEST")
research = Path("$RESEARCH")
assets = research / "review-assets"
handoff = research / "video-handoff.json"
topics = []
if (research / "review-data.json").is_file():
    topics = json.loads((research / "review-data.json").read_text()).get("topics", [])

manifest = {
    "schema_version": 1,
    "megapost_slug": "$SLUG",
    "post_id": int("$POST_ID"),
    "post_url": f"https://mer.vin/?p=$POST_ID",
    "research_dir": str(research),
    "review_assets_dir": str(assets),
    "target_duration_sec": 600,
    "pipeline_status": "pending",
    "final_video": {
        "path": "merge/final-roundup.mp4",
        "duration_sec": None,
        "captions": "merge/final-roundup.srt",
        "wordpress_attachment_id": None,
        "wordpress_url": None,
    },
    "segments": [],
}
# Minimal segment stubs from topics — edit manifest after bootstrap
manifest["segments"].append({
    "index": 0, "dir": "00-hook", "slug": "hook", "title": "Hook",
    "slide_type": "big_number", "headline": str(len(topics)), "subheader": "$SLUG",
    "target_words": 60, "target_sec": 22, "hero_image": None, "status": "pending",
})
for i, t in enumerate(topics, 1):
    slug = t.get("topic_slug", f"topic-{i}")
    manifest["segments"].append({
        "index": i,
        "dir": f"{i:02d}-{slug}",
        "slug": slug,
        "title": t.get("title", slug),
        "slide_type": "avatar_media_3",
        "headline": t.get("title", slug)[:40],
        "subheader": "",
        "target_words": 85,
        "target_sec": 36,
        "hero_image": (t.get("top_picks") or [None])[0],
        "status": "pending",
    })
outro_i = len(topics) + 1
manifest["segments"].append({
    "index": outro_i, "dir": f"{outro_i:02d}-outro", "slug": "outro", "title": "Outro",
    "slide_type": "deck_thank_you", "headline": "Full roundup", "subheader": "Read online",
    "target_words": 45, "target_sec": 18, "hero_image": None, "status": "pending",
})
(dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"manifest: {len(manifest['segments'])} segments")
PY

for seg in $(python3 -c "import json; m=json.load(open('$DEST/manifest.json')); print(' '.join(s['dir'] for s in m['segments']))"); do
  mkdir -p "$DEST/segments/$seg"
done

echo "Bootstrapped: $DEST"
echo "Next: edit manifest.json headlines/subheaders, write scripts (Phase 2), then pipeline.py sync-media"
