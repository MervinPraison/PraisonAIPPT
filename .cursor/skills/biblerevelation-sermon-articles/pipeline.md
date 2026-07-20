# End-to-end pipeline — transcript + YAML → biblerevelation.org

**One input → one output.**

| Input | Output |
|-------|--------|
| `.transcript.txt` + PPT YAML deck | Live WordPress article |

Complete workflow from sermon audio to live post. Read this file when building or rebuilding any biblerevelation sermon article.

**Related skills**

| Skill | When |
|-------|------|
| [SKILL.md](SKILL.md) | Content quality standards only |
| [create-post/reference.md](../biblerevelation-create-post/reference.md) | praisonaiwp, SSH, publish commands |
| [youtube-clip-transcribe](../youtube-clip-transcribe/SKILL.md) | Phase 1 — transcribe audio |

---

## Phase 0 — Prerequisites

```bash
bash -lc 'praisonaiwp doctor --server biblerevelation'
ffmpeg -version
bash -lc 'test -n "$OPENAI_API_KEY" && echo ok'
```

| Path | Purpose |
|------|---------|
| `~/Downloads/BIC-Sermon-Deck-Pack/` | Pack transcripts (`.transcript.txt`) |
| `~/praisonaippt/examples/*.yaml` | PPT YAML decks |
| `~/praisonai-audio-editor/.agent/biblerevelation-{slug}.html` | Local draft HTML |
| `~/praisonai-audio-editor/` | Transcribe workspace |

**Stop and ask the user** if transcript or YAML is missing. Do not publish from memory.

---

## Phase 1 — Acquire transcript

Follow [youtube-clip-transcribe/SKILL.md](../youtube-clip-transcribe/SKILL.md):

1. Download full audio (`yt-dlp` via conda — not homebrew for long clips)
2. Crop with ffmpeg (`-ss` / `-to`; `-to` is absolute on timeline)
3. **Always normalise volume** (Step 2b in that skill)
4. Transcribe → `{stem}.transcript.json` + `{stem}.transcript.txt`
5. Save transcript as `~/Downloads/BIC-Sermon-Deck-Pack/{Sermon Title}.transcript.txt` (or path user provides)

---

## Phase 2 — Match YAML deck

1. Open `~/praisonaippt/examples/` and find YAML by `presentation_title` or sermon topic
2. Confirm mapping in [reference.md](reference.md) § sermon mapping
3. Read entire YAML — count slides, note `reference`, `text`, `highlights`, `large_text`, empty-ref teaching lines

**YAML location:** `~/praisonaippt/examples/{snake_case}.yaml`

Deep schema + gap rules → [yaml-and-transcript.md](yaml-and-transcript.md)

---

## Phase 3 — Outline from transcript

1. Read **full** `.transcript.txt` top-to-bottom once (single-line files are normal)
2. List every **h2-worthy** block in sermon order:
   - Stories (Jehoshaphat, Job, Abraham…)
   - Numbered lists preacher counts on fingers
   - Objections / Q&A beats
   - Law vs grace turning points
   - Tables (world vs God, before/after law, exam analogy)
   - Closing prayer / declarations
3. Draft emoji `h2` titles — one per major block
4. **Rewrite SEO title + kebab-case slug** — never copy YouTube or deck title verbatim

Example outline → [examples.md](examples.md) § God Is Good section flow.

---

## Phase 4 — Map YAML to transcript sections

For each YAML slide entry:

| YAML field | Article use |
|------------|-------------|
| `reference` | Citation line + blockquote attribution |
| `text` | Verse body (NKJV unless YAML says NIV) |
| `highlights` | `#bbf7d0` / `#fde68a` on those words in blockquote |
| `large_text` | Hebrew/Greek word study — centred blockquote |
| `leading_title` | Optional h3 subheading before verse |
| Empty `reference` + text like `Colossians 2:16` | **Still required** — treat text as verse ref; add blockquote |
| Empty `reference` + label (`God is Love`, `True Faith`) | Weave into prose or list — not a standalone appendix |

**Placement rule:** verse blockquote goes **under the h2/h3** where the transcript teaches that topic — never in a `📖 Scripture from the Slides` appendix.

**Range refs:** YAML `1 Kings 5:3–4` → one blockquote with full range text, not v4 only.

---

## Phase 5 — Write HTML from scratch

**Golden rule:** Read the **entire transcript once** and map every teaching block in **sermon order** before writing. REWRITE entire body in that order. **NEVER append** to old HTML.

### File

`~/praisonai-audio-editor/.agent/biblerevelation-{slug}.html`

### Structure (in order)

1. `h3` hook + emoji — article title (may echo rewritten WP title)
2. Anchor verse blockquote
3. Highlight-key blockquote (green/gold legend)
4. `<!-- wp:separator -->`
5. Optional inline `wp:image` **alignwide** (after first separator)
6. `h2` sections in transcript order — **each section: 1 short intro paragraph (≤450 chars) + list/table + inline verses**
7. `🎯 The Takeaway` — ordered list (4–7 bullets)
8. Footer: `🎧 Scripture-based study on …` (not “Based on a Sunday message”)

Block templates → [reference.md](reference.md) § block templates.

### Content standards

| Metric | Target |
|--------|--------|
| Spoken-point coverage | ≥85% of major teaching blocks |
| Word ratio vs transcript | ≥55% (summary-only drafts sit ~28–50%) |
| YAML verses | 100% inline at correct section |
| Language | British English |
| Attribution | No preacher/ministry names in body |

### Interactive elements (required)

**Per section pattern (mandatory):**

1. Emoji `h2` heading
2. **One** short intro paragraph (≤450 chars) — condensed teaching, **not** verbatim transcript
3. **At least one** of: bullet list · ordered list · comparison table
4. **Never** add auto-generated transcript bullets when a curated override exists for that section
5. Inline verse blockquotes where YAML maps them
6. Separator before next section

**Article minimums:** ≥6 `wp-block-list` blocks · ≥1 `wp-block-table` · max paragraph ≤450 chars · no spoken filler (“tell the person next to you”, “shall we all read”).

Use at least one per major section where transcript supports it:

- Comparison tables (`World's way` / `God's way`, `Partial` / `Full`, `Law path` / `Faith path`)
- Bullet or numbered lists (3–5 digest points per section)
- Blockquotes for verses and teaching quotes
- Emoji `h2` / `h3` headings
- `<strong>`, `<em>`, `<mark>` highlights — green for grace, gold for gift terms

**Phase 6b — structure self-check:**

Before publish, confirm: ≥8 h2 sections · ≥6 lists · ≥1 table · paragraphs ≤450 chars · highlight key · takeaway · no spoken filler · no `Scripture from the Slides` appendix.

---

## Phase 6 — YAML verse audit (before publish)

Run **both** validators:

```bash
# Standard article checks
python ~/.cursor/skills/biblerevelation-sermon-articles/scripts/validate_article.py \
  --html ~/praisonai-audio-editor/.agent/biblerevelation-{slug}.html \
  --transcript ~/Downloads/BIC-Sermon-Deck-Pack/SERMON.transcript.txt \
  --yaml ~/praisonaippt/examples/deck.yaml

# Deep YAML gap check (empty refs, text-only verse markers, partial ranges)
python ~/.cursor/skills/biblerevelation-sermon-articles/scripts/audit_yaml_verses.py \
  --html ~/praisonai-audio-editor/.agent/biblerevelation-{slug}.html \
  --yaml ~/praisonaippt/examples/deck.yaml
```

Fix all `FAIL` / `MISSING` lines. Common gaps:

- Text-only slide lines (`reference: ''`, `text: Colossians 2:16`)
- Partial ranges (YAML `5:3–4`, article cites `5:4` only)
- Merged citations OK if content present (e.g. `John 21:15–17` covers 16 & 17)

Gap-fix pattern: **minimal inline inserts only** — do not rewrite whole article.

---

## Phase 7 — Images

| Asset | Size | WordPress |
|-------|------|-----------|
| Featured banner | **`1536x1024`** landscape | `_thumbnail_id` / og:image |
| Inline concept | **`1536x1024`** or `1536x864` | `alignwide` in body |

**Never `1024x1536`** — portrait looks tiny on wide screens; WP creates `-683x1024` derivatives.

Generate featured + inline art (1536×1024 landscape):

```bash
cd ~/praisonaippt
uv run .cursor/skills/gpt-image/scripts/generate.py \
  --prompt "Wide horizontal faith article banner, … landscape composition, no text" \
  --size 1536x1024 --quality high --output /tmp/{slug}-featured.png

uv run .cursor/skills/gpt-image/scripts/generate.py \
  --prompt "Wide horizontal sermon concept illustration, … landscape composition, no text" \
  --size 1536x1024 --quality high --output /tmp/{slug}-inline.png
```

Upload:

```bash
bash -lc 'praisonaiwp media upload /tmp/{slug}-featured.png --server biblerevelation'
bash -lc 'praisonaiwp media upload /tmp/{slug}-inline.png --server biblerevelation'
```

Featured and inline **must be different files**. When rewriting text-only, preserve existing `wp:image` blocks from live post.

Portrait scan on live post:

```bash
curl -sL "https://biblerevelation.org/?p=POST_ID" | grep -oE '683x1024|768x1152|1024x1536' | sort -u
```

Full image workflow → [reference.md](reference.md) § images.

---

## Phase 8 — Self-audit checklist

| Check | Pass |
|-------|------|
| Title / slug rewritten for SEO | ✓ |
| Transcript order preserved | ✓ |
| ≥85% spoken-point blocks | ✓ |
| All YAML refs + text-only verse markers inline | ✓ |
| No `Scripture from the Slides` appendix | ✓ |
| No duplicate h2/h3 titles | ✓ |
| Highlights on key terms | ✓ |
| Landscape images only | ✓ |
| `validate_article.py` PASS | ✓ |
| `audit_yaml_verses.py` no MISSING | ✓ |

---

## Phase 9 — Publish

Full commands (create, update, featured image, categories) → [create-post/reference.md](../biblerevelation-create-post/reference.md).

**Update existing sermon post:**

```bash
bash -lc 'praisonaiwp update POST_ID \
  --server biblerevelation \
  --no-block-conversion \
  --post-content "$(cat ~/praisonai-audio-editor/.agent/biblerevelation-{slug}.html)"'
```

Always `--server biblerevelation` and `--no-block-conversion`. Never `--append` for sermon body.

---

## Phase 10 — Live verification

```bash
curl -sL -o /dev/null -w "%{http_code}\n" "https://biblerevelation.org/2026/07/{slug}/"
curl -sL "URL" | grep -c "critical error"          # expect 0
curl -sL "URL" | grep -c "Scripture from the Slides"  # expect 0
```

Resolve canonical URL: `curl -sI "https://biblerevelation.org/?p=POST_ID" | grep -i location`

---

## Phase 11 — Report to user

| Field | Example |
|-------|---------|
| Post ID | 240335 |
| Title | God Is Good ALL the Time |
| Live URL | https://biblerevelation.org/2026/07/god-is-good-all-the-time/ |
| Word ratio | 58% |
| YAML verses | 18/18 inline (audit clean) |
| Transcript | `~/Downloads/BIC-Sermon-Deck-Pack/God is Good ALL the Time.transcript.txt` |
| YAML | `~/praisonaippt/examples/god_is_good_all_the_time.yaml` |
| Draft HTML | `~/praisonai-audio-editor/.agent/biblerevelation-god-is-good-all-the-time.html` |
| Images | featured ID, inline ID |

---

## Scope rules (production)

| Rule | Reason |
|------|--------|
| Do not modify posts user did not ask to change | Prior reverts on pre-July posts |
| Revert via WP revision before session edits | July revision can cause HTTP 500 — use June if needed |
| Text-only YAML gap fixes = minimal inserts | Keep article body intact |
| Omit event logistics / pure audience banter | Optional trim |
| Keep Tamil phrases when doctrinally meaningful | |

---

## Quick command cheat sheet

```bash
# Full validate + YAML audit
SLUG=god-is-good-all-the-time
SERMON="God is Good ALL the Time"
YAML=god_is_good_all_the_time.yaml

python ~/.cursor/skills/biblerevelation-sermon-articles/scripts/validate_article.py \
  --html ~/praisonai-audio-editor/.agent/biblerevelation-${SLUG}.html \
  --transcript ~/Downloads/BIC-Sermon-Deck-Pack/${SERMON}.transcript.txt \
  --yaml ~/praisonaippt/examples/${YAML}.yaml

python ~/.cursor/skills/biblerevelation-sermon-articles/scripts/audit_yaml_verses.py \
  --html ~/praisonai-audio-editor/.agent/biblerevelation-${SLUG}.html \
  --yaml ~/praisonaippt/examples/${YAML}.yaml

# Publish
bash -lc "praisonaiwp update POST_ID --server biblerevelation --no-block-conversion \
  --post-content \"\$(cat ~/praisonai-audio-editor/.agent/biblerevelation-${SLUG}.html)\""
```
