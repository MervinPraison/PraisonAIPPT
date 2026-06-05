# mer.vin article video upload — reference

## Example: article 50590

**URL:** https://mer.vin/2026/05/dreaming-outcomes-and-webhooks-claude-managed-agents-update-may-2026/  
**Post ID:** 50590  
**Local video (Mac):** `/Users/praison/praisonaippt/examples/heygen-50590-video-audio-heygen-images.mp4`

Existing content already has `Clip from the live announcement` with attachment 50594. The composite walkthrough is added under **Short video walkthrough** (separate section).

### One-shot (after scp)

```bash
ssh hestia 'cd /home/hestiaadmin/web/mer.vin/public_html && \
  bash .cursor/skills/mer-vin-article-video-upload/scripts/upload-video-to-article.sh \
  /tmp/heygen-50590-video-audio-heygen-images.mp4 50590 "Short video walkthrough"'
```

### Manual WP-CLI

```bash
cd /home/hestiaadmin/web/mer.vin/public_html

ATT_ID=$(wp media import /tmp/heygen-50590-video-audio-heygen-images.mp4 \
  --post_id=50590 \
  --title="Dreaming outcomes webhooks — short walkthrough" \
  --porcelain --allow-root)

ATT_URL=$(wp post get "$ATT_ID" --field=guid --allow-root)

# Then merge block into post_content (prefer the upload script).
```

## praisonaiwp media upload (Mac)

Exact flags depend on installed praisonaiwp version; typical flow:

```bash
praisonaiwp media upload examples/heygen-50590-video-audio-heygen-images.mp4 \
  --post-id 50590 --server default

praisonaiwp update 50590 --no-block-conversion \
  --post-content-file /tmp/50590-with-video.html
```

Configure server alias `default` in praisonaiwp config (Application Password or equivalent for mer.vin).

## REST alternative

Authenticated `POST /wp/v2/media` with `Content-Disposition` filename header, then `PUT /wp/v2/posts/{id}` with updated `content`. Prefer WP-CLI on hestia when the agent already has shell access.

## Related docs

| File | Topic |
|------|-------|
| `docs/create-post-workflow-simple.md` | Create flow + praisonaiwp media |
| `docs/external-create-post-meta.md` | `_mer_*` meta (not video) |
| `migration-markdown/.../2025-12-20-praisonaiwp-post-creation-guide.md` | Gutenberg block tags |
