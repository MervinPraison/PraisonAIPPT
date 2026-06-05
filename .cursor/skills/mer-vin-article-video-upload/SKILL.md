---
name: mer-vin-article-video-upload
description: Upload an MP4 to mer.vin WordPress and embed it in a published article with a Gutenberg wp:video block. Use when the user provides a local video path, asks to add video to an article, praisonaiwp media upload, wp media import, or wp:video on mer.vin.
disable-model-invocation: true
---

# mer.vin — upload video to article

## How mer.vin handles article media

| Layer | Tool | When |
|-------|------|------|
| **Docs workflow** | `praisonaiwp media upload` → `praisonaiwp update` | Mac with praisonaiwp configured for mer.vin |
| **Server (agent on hestia)** | `wp media import` → `wp post update` | Video file already on server (e.g. after `scp`) |
| **Article create** | `praisonaiwp create --meta '{…}' --content '…'` | New posts; see `docs/create-post-workflow-simple.md` |
| **Meta only** | `_mer_content_source_url`, `_mer_references` | Not used for video embeds — video goes in `post_content` |

WordPress root: `/home/hestiaadmin/web/mer.vin/public_html`

Always run WP-CLI with `--allow-root` on hestia.

## Gutenberg block (required shape)

Match existing mer.vin articles (e.g. post 50671, 50442):

```html
<!-- wp:heading -->
<h2 class="wp-block-heading">Short video walkthrough</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Optional one-line intro before the player.</p>
<!-- /wp:paragraph -->

<!-- wp:video {"id":ATTACHMENT_ID} -->
<figure class="wp-block-video"><video controls src="ATTACHMENT_URL"></video></figure>
<!-- /wp:video -->
```

Use `--no-block-conversion` semantics: raw block markup in `post_content`, not bare HTML.

## Path A — Mac + praisonaiwp (preferred)

When the video is on the Mac and praisonaiwp is installed:

```bash
# 1. Upload to Media Library (parent = article)
praisonaiwp media upload /path/to/video.mp4 --post-id=ARTICLE_ID --server default

# 2. Note attachment ID + URL from output, then update content
praisonaiwp update ARTICLE_ID --no-block-conversion --post-content "$(cat article-with-video.html)"
```

See `docs/create-post-workflow-simple.md` and `migration-markdown/mer.vin/posts/2025/2025-12-20-praisonaiwp-post-creation-guide.md`.

## Path B — Server WP-CLI (agent on hestia)

Local Mac paths (`/Users/…`) are **not** visible on hestia. Copy the file first:

```bash
# Mac
scp /Users/praison/praisonaippt/examples/heygen-50590-video-audio-heygen-images.mp4 \
  hestia:/tmp/heygen-50590-video-audio-heygen-images.mp4
```

Then on server:

```bash
cd /home/hestiaadmin/web/mer.vin/public_html
bash .cursor/skills/mer-vin-article-video-upload/scripts/upload-video-to-article.sh \
  /tmp/heygen-50590-video-audio-heygen-images.mp4 \
  50590 \
  "Short video walkthrough"
```

Script behaviour:

1. Resolve article by numeric ID or slug/URL.
2. `wp media import` with `--post_id` set to the article.
3. Insert heading + optional paragraph + `wp:video` block **before** `## At a glance` if present, else append before closing content.
4. Skip if the same attachment URL is already in content.

## Resolve article ID from URL

```bash
wp post list --name=dreaming-outcomes-and-webhooks-claude-managed-agents-update-may-2026 \
  --field=ID --allow-root
# → 50590
```

## Section placement conventions

| Section heading | Use when |
|-----------------|----------|
| **Short video walkthrough** | PraisonAIPPT / HeyGen deck summary (avatar + slides) |
| **Clip from the live announcement** | Source event MP4 only (already used on some posts) |
| Near top after intro | Product demo / HyperFrames-style source video (post 50442) |

Do not replace an existing announcement clip unless the user asks. Add a separate section for composite walkthrough videos.

## HeyGen article videos (related, not the same)

- `_mer_heygen_video_attachment_id` — HeyGen talking-head MP4 sideloaded by mu-plugin; used on **Shorts** CPT, not auto-embedded in article body.
- PraisonAIPPT composite (`heygen-50590-video-audio-heygen-images.mp4`) is a **separate** deck export — upload via this skill into `post_content`.

## Verify

```bash
wp post get ARTICLE_ID --field=url --allow-root
wp post get ARTICLE_ID --field=post_content --allow-root | grep -A2 'wp:video'
curl -sI "ATTACHMENT_URL" | head -1   # expect HTTP/2 200
```

Open the live URL in a browser; confirm the player loads and `controls` work.

## Common failures

| Symptom | Fix |
|---------|-----|
| `No such file` on hestia | `scp` from Mac first (Path B) |
| Video block missing on front end | Use full Gutenberg `wp:video {"id":…}` block, not raw `<video>` alone |
| Duplicate block | Script checks attachment URL; remove old block manually if replacing |
| `praisonaiwp: command not found` on server | Use Path B (`wp media import`) |

## Additional detail

See [reference.md](reference.md) for full example (article 50590) and REST alternative.
