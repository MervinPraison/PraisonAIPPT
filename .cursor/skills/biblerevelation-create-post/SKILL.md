---
name: biblerevelation-create-post
description: Publish ready-made content to biblerevelation.org via post_publish SDK or praisonaiwp — interactive HTML, markdown, Gutenberg drafts in /tmp. Use when HTML is already written and there is NO transcript+YAML sermon workflow. Do NOT use when user provides sermon transcript + YAML deck — use biblerevelation-sermon-articles instead.
---

# biblerevelation.org create post

## Which skill?

| You have | Use |
|----------|-----|
| Transcript + YAML deck | [biblerevelation-sermon-articles](../biblerevelation-sermon-articles/pipeline.md) — **not this skill** |
| Ready HTML/markdown, post_publish job | **This skill** |
| YouTube → transcript first | [youtube-clip-transcribe](../youtube-clip-transcribe/SKILL.md) |

**Do not read both skills for the same task.**

## Config

| Item | Value |
|------|--------|
| Server | `biblerevelation` → https://biblerevelation.org |
| CLI config | `~/.praisonaiwp/config.yaml` |
| Publish SDK | `python3 ~/create-post/scripts/post_publish_cli.py` |
| SDK docs | [`~/create-post/docs/post-publish-sdk.md`](~/create-post/docs/post-publish-sdk.md) |
| Connectivity | `praisonaiwp doctor --server biblerevelation` |
| Style reference | https://biblerevelation.org/2026/05/the-gospel-in-the-stars/ |

**Always pass `--server biblerevelation`** — default server is `mer.vin`.

**Never commit per-post scripts to `.agent/`.** Drafts and sources live in `/tmp`.

## Content style (post_publish / interactive only)

Scannable faith teaching — emoji headings, tables/lists before paragraphs, landscape images.  
**Transcript + YAML sermon articles:** content rules live in [sermon-articles/SKILL.md](../biblerevelation-sermon-articles/SKILL.md) — do not duplicate here.

## Source attribution (mandatory)

Articles are **Scripture-based study**, not preacher profiles. When content comes from a YouTube sermon or similar source:

- **Never** name the preacher, prophet, ministry, or channel (e.g. no "Uebert Angel", "Prophet Angel", or equivalent).
- **Never** attribute teaching to a sermon or speaker — avoid phrases like "from the sermon", "Full sermon notes", "What the Sermon Teaches", "Sermon Teaching", "Prayer cry from the sermon", or "This sermon breaks down".
- **Use instead:** "Study notes", "What Scripture Teaches", "Teaching", "Answer", "Scripture breaks down", "Theme in This Study".
- Historical revival names used only as examples (e.g. Finney) — prefer generic wording: "revival prayer pattern".
- Comparison sections: **Surface Preaching vs Deep Teaching** — not "Preacher vs Teacher".
- Excerpts follow the same rules — no preacher names or sermon attribution.

## Title and slug (mandatory)

Every post needs a **rewritten SEO title** and a **deliberate slug** — never copy the source headline.

| Rule | Detail |
|------|--------|
| Rewrite title | Clear keywords + reader intent; add a Scripture anchor when natural |
| Never verbatim | Do **not** reuse YouTube titles, sermon titles, or source article headlines |
| No source hooks | Drop marketing phrases from the original (e.g. "Stop Guessing—Get Divine Direction!") |
| Slug from rewrite | Short kebab-case from **your** title concepts — not auto-derived from the source |
| Draft `slug` ≠ URL | `slug` in `.post.yaml` / `--slug` names `/tmp` drafts only; WordPress `post_name` is set separately |

**Before publish:** pick `{slug}` and `--title` / `title:` from the rewritten headline (e.g. `god-breathed-wisdom-proverbs-30-christ`).

**Set WordPress slug at create** (preferred — avoids a wrong URL briefly going live):

```bash
ssh -i ~/.ssh/id_ed25519 root@185.249.73.167 \
  "cd /home/hestiaadmin/web/biblerevelation.org/public_html/wordpress && \
   wp post create --post_type=post --post_status=publish \
   --post_title='God-Breathed Wisdom for Every Need: Proverbs 30'\''s Hidden Picture of Christ' \
   --post_name='god-breathed-wisdom-proverbs-30-christ' \
   --post_content='…' --porcelain --allow-root"
```

When using `post_publish` or `praisonaiwp create`, set `post_name` immediately after create if the CLI did not accept a slug flag:

```bash
ssh -i ~/.ssh/id_ed25519 root@185.249.73.167 \
  "cd /home/hestiaadmin/web/biblerevelation.org/public_html/wordpress && \
   wp post update POST_ID --post_name='god-breathed-wisdom-proverbs-30-christ' --allow-root"
```

**Post-publish fix** (title + slug):

```bash
praisonaiwp update POST_ID --server biblerevelation \
  --post-title "God-Breathed Wisdom for Every Need: Proverbs 30's Hidden Picture of Christ"

ssh -i ~/.ssh/id_ed25519 root@185.249.73.167 \
  "cd /home/hestiaadmin/web/biblerevelation.org/public_html/wordpress && \
   wp post update POST_ID --post_name='god-breathed-wisdom-proverbs-30-christ' --allow-root"
```

WordPress issues a **301** from the old slug to the new one. Confirm with `wp post get POST_ID --field=url`.

| Source hook | ❌ Bad (copies source) | ✅ Good (rewritten) |
|-------------|------------------------|---------------------|
| "Stop Guessing—Get Divine Direction!" | Title: `Stop Guessing, Get Divine Direction: …`<br>Slug: `stop-guessing-get-divine-direction-…` | Title: `God-Breathed Wisdom for Every Need: Proverbs 30's Hidden Picture of Christ`<br>Slug: `god-breathed-wisdom-proverbs-30-christ` |
| YouTube: `DO THIS EVERY MORNING AND CHANGE YOUR LIFE` | Title: `Do This Every Morning and Change Your Life`<br>Slug: `do-this-every-morning-change-your-life` | Title: `Command the Morning Before Sunrise: Job 38 Heavenly Ordinances Explained`<br>Slug: `command-morning-job-38-heavenly-ordinances` |

**YouTube sources:** before publish, fetch the original title (oEmbed or `yt-dlp --print title`) and confirm your WordPress title shares **no verbatim phrase** from the source hook — not even re-cased or emoji-stripped. Scripture anchors (e.g. Job 38, Proverbs 30) are fine; clickbait lines from the video are not.

## Workflow (protocol-driven)

```
Task Progress:
- [ ] Route content type (sermon Gutenberg vs interactive HTML)
- [ ] Rewrite SEO title + deliberate kebab-case slug (not source headline)
- [ ] Save source to /tmp/{slug}-source.html or /tmp/{slug}-gutenberg.html
- [ ] Build draft via post_publish (transform → draft → validate)
- [ ] Review draft in /tmp before publish
- [ ] praisonaiwp doctor --server biblerevelation
- [ ] Publish via post_publish --publish (or praisonaiwp directly)
- [ ] Set WordPress post_name if create did not use your slug
- [ ] Plan image visual brief — image must teach the concept without reading the article
- [ ] Upload featured image + set _thumbnail_id (no duplicate inline copy)
- [ ] Pick 1–2 categories from main list (never create new)
- [ ] Verify HTTP 200 + return Post ID and URL
```

### Content type router

| Input | Adapter | Source path | Draft path |
|-------|---------|-------------|------------|
| Markdown / sermon article | `gutenberg` | `/tmp/{slug}-gutenberg.html` | same |
| Full HTML page (CSS + JS reader) | `html_interactive` | `/tmp/{slug}-source.html` | `/tmp/{slug}-gutenberg.html` |

Block patterns and sermon templates: [reference.md](reference.md).

### 1. Build draft (no publish)

**Sermon (hand-built Gutenberg):**

```bash
# Write Gutenberg to /tmp/{slug}-gutenberg.html first, then validate:
python3 ~/create-post/scripts/post_publish_cli.py /tmp/my-sermon-gutenberg.html \
  --adapter gutenberg \
  --slug my-sermon \
  --stages transform,draft,validate
```

**Interactive HTML reader (e.g. Galatians):**

```bash
# Save full HTML page to /tmp/{slug}-source.html first
python3 ~/create-post/scripts/post_publish_cli.py /tmp/galatians1-source.html \
  --adapter html_interactive \
  --slug galatians1 \
  --adapter-options '{"container_id":"gal1-reader"}'
```

Or use a job file — copy and edit:

- Sermon: `~/create-post/examples/post-publish/biblerevelation-sermon.post.yaml`
- Interactive: `~/create-post/examples/post-publish/biblerevelation-interactive.post.yaml`

```bash
python3 ~/create-post/scripts/post_publish_cli.py \
  --job ~/create-post/examples/post-publish/biblerevelation-sermon.post.yaml
```

Set `publish: false` in the job to build only; set `publish: true` when ready.

### 2. Publish (create + featured image)

**Preferred — full pipeline via job file:**

```bash
python3 ~/create-post/scripts/post_publish_cli.py \
  --job /tmp/my-sermon.post.yaml \
  --publish
```

**CLI flags (sermon):**

```bash
python3 ~/create-post/scripts/post_publish_cli.py /tmp/my-sermon-gutenberg.html \
  --adapter gutenberg \
  --server biblerevelation \
  --title "Article Title" \
  --category "Gospel,Wisdom" \
  --excerpt "One-line summary." \
  --featured ~/Downloads/cover.png \
  --featured-title "Article Title" \
  --featured-alt "Featured image for Article Title" \
  --publish
```

**CLI flags (interactive HTML):**

```bash
python3 ~/create-post/scripts/post_publish_cli.py /tmp/galatians1-source.html \
  --adapter html_interactive \
  --server biblerevelation \
  --title "Galatians 1: No Other Gospel" \
  --category "Bible Study" \
  --featured ~/Downloads/cover.png \
  --publish
```

Stages run: `transform` → `draft` → `validate` → `create` → `media_upload` → `set_featured` → `verify`.

### 3. Update existing post

```bash
python3 ~/create-post/scripts/post_publish_cli.py /tmp/my-sermon-gutenberg.html \
  --adapter gutenberg \
  --server biblerevelation \
  --post-id POST_ID \
  --featured ~/Downloads/new-cover.png \
  --publish
```

Or direct praisonaiwp for content-only patches:

```bash
praisonaiwp update POST_ID --server biblerevelation \
  --no-block-conversion \
  --post-content "$(cat /tmp/my-sermon-gutenberg.html)"
```

### 4. Images — landscape + must teach the concept

Every generated image (featured banner **or** inline) must be an **explanatory mental model** — a reader should grasp the article's core idea **from the image alone**, without reading the title or body.

**Plan before pixels** — write in `/tmp/{slug}-visual-brief.md`:

```text
After seeing this image, the reader understands [X] without reading [Y].
Concept to show: [e.g. believer praying before sunrise while sun is still below horizon = commanding the morning]
Must NOT show: generic sunset wallpaper, decorative clouds, unrelated scenery
```

| Asset | Role | Size | Meaning test |
|-------|------|------|--------------|
| **Featured** | Full-width banner → `_thumbnail_id` | `1536x1024` landscape | Passes visual-brief sentence — not mood-only art |
| **Inline** | One teaching concept → `wp:image alignwide` | `1536x1024` landscape | Different concept from featured; same brief test |

**Good image prompts** name the **teaching metaphor** — e.g. "believer kneeling in darkness before golden horizon, sun still below line, visual metaphor for commanding the morning before sunrise, chain of stars and constellations faint above".

**Bad image prompts** — "peaceful sunrise over hills", "faith banner", "beautiful morning sky" — decorative only; **regenerate**.

Reference: [`~/create-post/docs/create-post-images.md`](~/create-post/docs/create-post-images.md) § mental-model figures (adapt for faith teaching, not dev pipelines).

Generate with `gpt-image`:

```bash
cd ~/create-post/gpt-image && uv run scripts/generate.py \
  --prompt "Wide horizontal faith teaching illustration, [specific concept metaphor from visual brief], landscape banner composition, no text, no logos, no watermarks" \
  --size 1536x1024 --quality high --output /tmp/{slug}-cover.png
```

**Publish-gate:** if you cannot complete the visual-brief sentence honestly, do not generate or upload yet.

Rename local file to a SEO-friendly name first, then upload:

```bash
praisonaiwp media upload /path/to/my-sermon-cover.png \
  --server biblerevelation --post-id POST_ID \
  --title "Article Title" --alt "Featured image alt text"

# Set featured (media ID from upload output):
praisonaiwp update POST_ID --server biblerevelation \
  --meta '{"_thumbnail_id":"MEDIA_ID"}'
```

**Rule:** never embed the same asset as both featured image and inline content image.

### 5. Validate

```bash
# Post URL
ssh -i ~/.ssh/id_ed25519 root@185.249.73.167 \
  "cd /home/hestiaadmin/web/biblerevelation.org/public_html/wordpress && \
   wp post get POST_ID --field=url --allow-root"

# HTTP check
curl -sI "https://biblerevelation.org/…" | head -1

# Categories on post
praisonaiwp category list POST_ID --server biblerevelation

# Featured image set
ssh -i ~/.ssh/id_ed25519 root@185.249.73.167 \
  "cd /home/hestiaadmin/web/biblerevelation.org/public_html/wordpress && \
   wp post meta get POST_ID _thumbnail_id --allow-root"
```

## Job file template (`.post.yaml`)

Save to `/tmp/{slug}.post.yaml` — do not commit to the repo.

```yaml
schema_version: 1
slug: god-breathed-wisdom-proverbs-30-christ   # draft filename only — also set WP post_name
server: biblerevelation
title: "God-Breathed Wisdom for Every Need: Proverbs 30's Hidden Picture of Christ"
status: publish
category: "Gospel,Wisdom"
excerpt: "One-line summary."
publish: true

content:
  adapter: gutenberg          # or html_interactive
  source: /tmp/my-sermon-gutenberg.html
  options:                    # html_interactive only
    container_id: gal1-reader

draft:
  path: /tmp/my-sermon-gutenberg.html

featured:
  path: /Users/praison/Downloads/my-sermon-cover.png
  title: "Article Title"
  alt: "Featured image for Article Title"
```

## Category picker (existing only)

**Never** run `praisonaiwp category create`. Pick 1–2 from:

| Name | ID | Typical fit |
|------|-----|-------------|
| Wisdom | 3 | Teaching, practical faith |
| Revelation | 69 | Prophetic / revelation themes |
| Blessings | 21 | Hundredfold, favour |
| Redemption | 26 | Abraham, salvation, righteousness |
| Gospel | 70 | Good news, faith, new covenant |
| Bible Study | — | Chapter studies, interactive readers |

Refresh: `praisonaiwp category list --server biblerevelation`

## Checklist before finishing

- [ ] Title rewritten for SEO — verified against YouTube/sermon source title (no shared hook phrases)
- [ ] Slug is deliberate kebab-case from rewritten concepts — `post_name` set on WordPress
- [ ] Image visual brief written — featured/inline teach the concept without reading the article
- [ ] Source and draft in `/tmp` (not `.agent/`)
- [ ] `post_publish` build stages passed (`transform,draft,validate`)
- [ ] `--server biblerevelation` on every praisonaiwp call
- [ ] Categories from main list only (not newly created)
- [ ] Featured image is **horizontal** (`1536x1024`) and passes the visual-brief meaning test
- [ ] Featured image uploaded and `_thumbnail_id` set
- [ ] Featured image not duplicated inline in post body
- [ ] User given **Post ID**, live URL, and categories
- [ ] HTTP 200 confirmed on live URL
- [ ] No preacher/author names or "from the sermon" attribution in body or excerpt

## Related skills

- Transcript + YAML → article: [biblerevelation-sermon-articles/pipeline.md](../biblerevelation-sermon-articles/pipeline.md)
- Publish SDK stages: [`~/create-post/docs/post-publish-sdk.md`](~/create-post/docs/post-publish-sdk.md)
- YouTube → transcript: [youtube-clip-transcribe](../youtube-clip-transcribe/SKILL.md)
- mer.vin posts: `mer-vin-create-post`

## Additional resources

- Gutenberg blocks, categories, CLI commands, examples: [reference.md](reference.md)
- Example job files: `~/create-post/examples/post-publish/biblerevelation-*.post.yaml`
