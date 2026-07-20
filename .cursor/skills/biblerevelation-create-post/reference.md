# biblerevelation.org post reference

**Canonical for:** praisonaiwp, SSH, title/slug, image policy, post_publish SDK, categories.  
**Not here:** transcript workflow → [sermon-articles/pipeline.md](../biblerevelation-sermon-articles/pipeline.md).

## Site & config

| Item | Value |
|------|--------|
| CLI | `praisonaiwp` |
| Config | `~/.praisonaiwp/config.yaml` |
| Server flag | `--server biblerevelation` |
| Public URL | https://biblerevelation.org |
| WP root | `/home/hestiaadmin/web/biblerevelation.org/public_html/wordpress` |
| SSH | `root@185.249.73.167:22`, key `~/.ssh/id_ed25519` |
| Author | `praison` |

## Source attribution

Do not name source preachers or use sermon attribution in published copy. Present as Scripture-based study — see **Source attribution** in `SKILL.md`.

## Title and slug

Rewrite every title for SEO. Never reuse YouTube, sermon, or source article headlines verbatim. Choose a short kebab-case slug from the **rewritten** concepts — not from the original hook.

```bash
# Title (praisonaiwp)
praisonaiwp update POST_ID --server biblerevelation \
  --post-title "God-Breathed Wisdom for Every Need: Proverbs 30's Hidden Picture of Christ"

# Slug / post_name (WP-CLI over SSH — praisonaiwp has no --post-name)
ssh -i ~/.ssh/id_ed25519 root@185.249.73.167 \
  "cd /home/hestiaadmin/web/biblerevelation.org/public_html/wordpress && \
   wp post update POST_ID --post_name='god-breathed-wisdom-proverbs-30-christ' --allow-root"

# Confirm URL (old slug 301s to new)
ssh -i ~/.ssh/id_ed25519 root@185.249.73.167 \
  "cd /home/hestiaadmin/web/biblerevelation.org/public_html/wordpress && \
   wp post get POST_ID --field=url --allow-root"
```

| ❌ Avoid | ✅ Prefer |
|----------|-----------|
| `stop-guessing-get-divine-direction-proverbs-30s-four-mysteries-of-christ` | `god-breathed-wisdom-proverbs-30-christ` |
| Copying YouTube title punctuation and hooks | Scripture-anchored SEO title in your own words |

`slug` in `.post.yaml` / `--slug` only names `/tmp` draft files. Set WordPress `post_name` at or right after create.

**YouTube check:** `curl -s 'https://www.youtube.com/oembed?url=VIDEO_URL&format=json' | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])"` — confirm zero overlap with your rewritten title.

## Images — teach meaning, not decoration

Every image must pass: *After seeing this image, the reader understands [X] without reading [Y].*

Write `/tmp/{slug}-visual-brief.md` before generating. Featured and inline assets are both **explanatory mental models** — landscape `1536x1024`, no text/logos.

| ❌ Decorative | ✅ Explanatory |
|---------------|----------------|
| "peaceful sunrise over hills" | believer praying before dawn, sun below horizon = commanding the morning |
| "faith banner, golden light" | chain of stars/constellations linked to one kneeling figure = heavenly ordinances |
| generic clouds or cross wallpaper | before/after: chaotic day vs ordered day after morning prayer |

Full policy: `~/create-post/docs/create-post-images.md` (adapt for Scripture teaching).

## Gutenberg blocks (sermon articles)

Full sermon block templates → [sermon-articles/reference.md](../biblerevelation-sermon-articles/reference.md) § Block templates.  
Use [Markdown → Gutenberg](#markdown--gutenberg-conversion-rules) below for post_publish jobs.

## Markdown → Gutenberg conversion rules

| Markdown | Gutenberg |
|----------|-----------|
| `# Title` | `wp:heading level:3` hook with emoji |
| `## Section` | `wp:heading` h2 with emoji |
| `### Sub` | `wp:heading level:3` (sub-themes only) |
| `> quote` | `wp:quote` blockquote |
| `\| table \|` | `wp:table` with `style="width:100%"` |
| `- bullet` | `wp:list` ul |
| `1. numbered` | `wp:list {"ordered":true}` ol |
| `---` | `wp:separator` |
| `**bold**` | `<strong>` |
| `*italic*` | `<em>` |
| `> **Key text:**` | verse ref paragraph + `wp:quote` |

## post_publish SDK (preferred)

Drafts and sources live in **`/tmp`**, not `.agent/`. Full docs: `~/create-post/docs/post-publish-sdk.md`.

```bash
# Build + publish sermon
python3 ~/create-post/scripts/post_publish_cli.py /tmp/great-faith-gutenberg.html \
  --adapter gutenberg \
  --server biblerevelation \
  --title "Great Faith: How to Pray in One Second, Not One Hour" \
  --category "Gospel,Wisdom" \
  --excerpt "Four marks of great faith from Romans 1:16–17." \
  --featured ~/Downloads/great-faith-cover.png \
  --publish

# Interactive HTML reader
python3 ~/create-post/scripts/post_publish_cli.py /tmp/galatians1-source.html \
  --adapter html_interactive \
  --server biblerevelation \
  --title "Galatians 1: No Other Gospel" \
  --category "Bible Study" \
  --publish

# Job file
python3 ~/create-post/scripts/post_publish_cli.py \
  --job ~/create-post/examples/post-publish/biblerevelation-sermon.post.yaml \
  --publish
```

Example jobs: `~/create-post/examples/post-publish/biblerevelation-sermon.post.yaml`, `biblerevelation-interactive.post.yaml`.

## `create` command (direct praisonaiwp fallback)

```bash
bash -lc 'praisonaiwp create "Great Faith: How to Pray in One Second, Not One Hour" \
  --server biblerevelation \
  --status publish \
  --category "Gospel,Wisdom" \
  --excerpt "Four marks of great faith from Romans 1:16–17." \
  --no-block-conversion \
  --content "$(cat /tmp/great-faith-gutenberg.html)"'
```

| Option | Values |
|--------|--------|
| `--status` | `publish`, `draft`, `private` |
| `--type` | `post` (default) or `page` |
| `--category` | Comma-separated names |
| `--category-id` | Comma-separated IDs |
| `--tags` | Comma-separated tag names |
| `--author` | `praison` |
| `--meta` | JSON, e.g. `'{"key":"value"}'` |

JSON scripting: `praisonaiwp --json create …`

## `update` command

```bash
# Replace entire content
praisonaiwp update POST_ID --server biblerevelation \
  --no-block-conversion \
  --post-content "$(cat …html)"

# Title, status, excerpt, tags
praisonaiwp update POST_ID --server biblerevelation --post-title "New Title"
praisonaiwp update POST_ID --server biblerevelation --post-status publish
praisonaiwp update POST_ID --server biblerevelation --category "Blessings,Gospel"

# Slug (post_name) — WP-CLI only; see Title and slug section above
ssh -i ~/.ssh/id_ed25519 root@185.249.73.167 \
  "cd /home/hestiaadmin/web/biblerevelation.org/public_html/wordpress && \
   wp post update POST_ID --post_name='new-seo-slug' --allow-root"

# Find-and-replace in content
praisonaiwp update POST_ID --server biblerevelation "old phrase" "new phrase"

# Append section
praisonaiwp update POST_ID --server biblerevelation \
  --append "<!-- wp:paragraph --><p>Added</p><!-- /wp:paragraph -->"
```

## Categories

Main categories (parent = 0, > 30 posts):

| ID | Name | Slug | Posts | Typical sermon fit |
|----|------|------|-------|-------------------|
| 3 | Wisdom | wisdom | 231 | teaching, practical faith |
| 69 | Revelation | revelation | 182 | prophetic themes |
| 21 | Blessings | blessings | 74 | hundredfold, favour |
| 26 | Redemption | redemption | 56 | Abraham, salvation |
| 70 | Gospel | gospel | 39 | good news, faith |

```bash
praisonaiwp category list --server biblerevelation
praisonaiwp category list POST_ID --server biblerevelation
praisonaiwp category search "Bless" --server biblerevelation
praisonaiwp category set POST_ID --server biblerevelation --category "Gospel,Wisdom"
praisonaiwp category add POST_ID --server biblerevelation --category "Wisdom"
```

**Do not use:** `praisonaiwp category create`

## `list` and search

Use **single-word** search only:

```bash
praisonaiwp list --server biblerevelation --search "Faith" --limit 5
praisonaiwp list --server biblerevelation --status draft
```

## Post URL

```bash
ssh -i ~/.ssh/id_ed25519 root@185.249.73.167 \
  "cd /home/hestiaadmin/web/biblerevelation.org/public_html/wordpress && \
   wp post get POST_ID --field=url --allow-root"
```

URL pattern: `https://biblerevelation.org/YYYY/MM/{slug}/`

## Published examples

| Post ID | Title | URL |
|---------|-------|-----|
| 240535 | God-Breathed Wisdom for Every Need: Proverbs 30's Hidden Picture of Christ | https://biblerevelation.org/2026/07/god-breathed-wisdom-proverbs-30-christ/ |
| 240230 | Reigning in Life: The Two Keys to Living Victorious | https://biblerevelation.org/2026/06/reigning-in-life-the-two-keys-to-living-victorious/ |
| 240228 | Great Faith: The Secret to Instant Miracles | https://biblerevelation.org/2026/06/great-faith-the-secret-to-instant-miracles/ |
| 240225 | Great Faith: How to Pray in One Second, Not One Hour | https://biblerevelation.org/2026/06/great-faith-how-to-pray-in-one-second-not-one-hour/ |
| 240197 | 100 Fold Blessings | https://biblerevelation.org/2026/05/100-fold-blessings/ |
| 240198 | How to Prevent Delay | https://biblerevelation.org/2026/05/how-to-prevent-delay/ |

## Featured image

**Orientation:** horizontal landscape only (`1536x1024`). **Meaning:** must teach the article concept visually — plan in `/tmp/{slug}-visual-brief.md` before `gpt-image`. Decorative mood art fails the publish gate.

```bash
# Visual brief first, then generate with concept-specific metaphor in prompt
cd ~/create-post/gpt-image && uv run scripts/generate.py \
  --prompt "Wide horizontal faith teaching illustration, [concept from visual brief], landscape composition, no text, no logos" \
  --size 1536x1024 --quality high --output /tmp/{slug}-cover.png

# Rename local file first, then upload
praisonaiwp media upload /path/to/my-sermon-cover.png \
  --server biblerevelation --post-id POST_ID \
  --title "Article Title" --alt "Featured image alt"

praisonaiwp update POST_ID --server biblerevelation \
  --meta '{"_thumbnail_id":"MEDIA_ID"}'
```

Or include `featured:` block in a `.post.yaml` job and run `post_publish_cli.py --publish`.

## Publish workflow checklist

```
1. praisonaiwp doctor --server biblerevelation
2. Rewrite SEO title + deliberate slug — verify against YouTube oEmbed title (no shared hook)
3. Write `/tmp/{slug}-visual-brief.md` — image must teach concept without reading article
4. Write source to /tmp/{slug}-gutenberg.html (or /tmp/{slug}-source.html for interactive)
4. post_publish: transform → draft → validate (review /tmp draft)
5. post_publish --publish (or praisonaiwp create as fallback)
6. Set WordPress post_name if create left the default slug
7. Featured image: landscape + passes visual-brief meaning test; uploaded; _thumbnail_id set; not duplicated inline
8. Note Post ID
9. praisonaiwp category list POST_ID --server biblerevelation
10. wp post get POST_ID --field=url
11. curl -sI URL → HTTP 200
12. Report: Post ID, URL, categories, featured media ID
```
