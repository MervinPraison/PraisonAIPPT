# YAML deck + transcript — mapping reference

How PPT YAML decks relate to sermon transcripts and article HTML.

---

## YAML schema (praisonaippt/examples)

```yaml
presentation_title: God is Good ALL the Time
presentation_subtitle: ''
slide_size: standard
slide_style:
  background_image: assets/background_alt.jpg
sections:
- section: ''
  verses:
  - reference: Jeremiah 29:11
    text: '"For I know the plans…"'
    highlights:
    - plans to prosper you
  - reference: ''
    text: Colossians 2:16          # text-only verse marker — still required inline
  - reference: True Faith
    text: |-
      Don't fight for Victory, fight from Victory
    highlights:
    - fight from Victory
```

### Fields per slide

| Field | Required | Article use |
|-------|----------|-------------|
| `reference` | Often | Book chapter:verse for citation; may be empty, emoji-prefixed, or a teaching label |
| `text` | Usually | Verse body, slide title, or teaching bullet |
| `highlights` | Optional | Words/phrases → `#bbf7d0` or `#fde68a` in blockquote |
| `leading_title` | Optional | h3 subheading before verse |
| `large_text` | Optional | Big display text (Hebrew/Greek) — centred blockquote |
| `font_size` | Optional | Ignore for article (deck rendering only) |

---

## Entry types and how to handle them

### 1. Standard scripture (`reference` + `text`)

```yaml
- reference: Romans 5:17 (NKJV)
  text: '"For if by the one man\'s offense death reigned…"'
  highlights:
  - reign in life
```

**Article:**

```html
<!-- wp:paragraph -->
<p><strong>Romans 5:17 (NKJV)</strong></p>
<!-- /wp:paragraph -->

<!-- wp:quote -->
<blockquote class="wp-block-quote"><p><em>"…<mark style="background-color:#bbf7d0"><strong>reign in life</strong></mark>…"</em> — <strong>Romans 5:17 (NKJV)</strong></p></blockquote>
<!-- /wp:quote -->
```

### 2. Chapter or range refs

| YAML | Article |
|------|---------|
| `2 Chronicles 20` (two slides, v22 + v23 text) | Two blockquotes: `2 Chronicles 20:22`, `:23` |
| `1 Kings 5:3–4 (NIV)` | **One** blockquote with full v3 + v4 text |
| `Matthew 13:5–6, 13:20–21` | Combined blockquote or adjacent quotes |
| `Psalms 136` | At minimum `Psalm 136:1`; chapter teaching in prose OK |

### 3. Empty reference + verse in text field

```yaml
- reference: ''
  text: Colossians 2:16
- reference: ''
  text: Isaiah 28:21
```

`validate_article.py` **skips** these (only checks non-empty `reference`). Use `audit_yaml_verses.py` — it detects `Book chapter:verse` patterns in `text` when `reference` is empty.

**Fix:** Add NKJV blockquote at the transcript section that teaches that topic. Pull text from YAML sibling entries, transcript, or standard NKJV if deck has ref only.

### 4. Teaching labels (not scripture)

```yaml
- reference: True Faith
  text: Don't fight for Victory, fight from Victory
- reference: 'a) God Won't Test With Evil'
  text: …
- reference: Identity
  text: …
```

Weave into **prose, bullet list, or blockquote** where transcript teaches it — not a separate appendix.

### 5. Emoji / noise in reference

```yaml
- reference: '🍎 Romans 1:29'
```

Strip emoji for citation; verse text must still appear inline. Content match matters more than exact ref string.

### 6. Duplicate refs in YAML

`love_of_god.yaml` lists `John 21:16` and `John 21:17` twice (agape/phileo sections). One combined `John 21:15–17` blockquote is **OK** if all three exchanges are present.

---

## Transcript → section mapping workflow

```
1. Read transcript once → numbered outline of teaching blocks
2. Read YAML → list all entries (reference + text-only markers + labels)
3. For each YAML entry, find transcript anchor:
   - Same verse quoted or paraphrased
   - Same story (Jehoshaphat, Solomon, wilderness 50 days)
   - Same keyword (law, Pentecost, agape, hundredfold)
4. Assign to h2 section from step 1
5. Write section HTML with verse inline (not collected at end)
6. Run audit_yaml_verses.py — fix MISSING before publish
```

### Transcript file notes

- Often **one long line** — use grep or Python search, not line-by-line reading
- Filename matches sermon title: `God is Good ALL the Time.transcript.txt`
- JSON fallback: `~/praisonai-audio-editor/{stem}.transcript.json` → `text` field

---

## Highlight colour rules

| Colour | Hex | Use |
|--------|-----|-----|
| Green | `#bbf7d0` | Grace / apart-from-works / identity truth |
| Gold | `#fde68a` | Precious gift / key promise / covenant terms |

Apply to words in YAML `highlights:` list plus obvious key terms in the same blockquote.

```html
<mark style="background-color:#bbf7d0"><strong>term</strong></mark>
<mark style="background-color:#fde68a"><strong>term</strong></mark>
```

Include highlight-key legend blockquote near top of every article.

---

## Sermon pack file mapping

| Transcript (`~/Downloads/BIC-Sermon-Deck-Pack/`) | YAML (`~/praisonaippt/examples/`) | Slug |
|--------------------------------------------------|-----------------------------------|------|
| `Authority over Death through Jesus Christ.transcript.txt` | `authority_over_death.yaml` | `authority-over-death-through-jesus-christ` |
| `Reign in Life.transcript.txt` | `reign_in_life.yaml` | `reign-in-life` |
| `Great Faith.transcript.txt` | `great_faith.yaml` | `great-faith` |
| `100 Fold Blessing.transcript.txt` | `100_fold_blessing.yaml` | `100-fold-blessings` |
| `Can God allow sickness in our lives, like Job?.transcript.txt` | `job_sickness.yaml` | `can-god-allow-sickness-like-job` |
| `How to Come Out of Testing and Trials.transcript.txt` | `how_to_come_out_of_testing_and_trials.yaml` | `how-to-come-out-of-testing-and-trials` |
| `God is Good ALL the Time.transcript.txt` | `god_is_good_all_the_time.yaml` | `god-is-good-all-the-time` |
| `Freedom.transcript.txt` | `freedom_in_spirit.yaml` | `freedom` |
| `Love of God.transcript.txt` | `love_of_god.yaml` | `love-of-god` |
| `receive a hundredfold now.transcript.txt` | `receive_a_hundredfold_now.yaml` | `receive-a-hundredfold-now` |
| `Freedom from ALL your troubles.transcript.txt` | `freedom_from_all_your_troubles.yaml` | `freedom-from-all-your-troubles` |

If YAML missing for a new sermon: locate closest deck by `presentation_title` or create new YAML under `examples/` before writing article.

---

## Gap audit examples (from production)

| Post | Gap | Fix |
|------|-----|-----|
| 240335 God Is Good | `Colossians 2:16`, `Isaiah 28:21` text-only in YAML | Add blockquotes after Col 2:14 / Isaiah anger section |
| 240064 Testing | `1 Kings 5:3–4` — only v4 cited | Extend quote to full YAML range |
| 240340 Love of God | John 21:16/17 as separate YAML refs | OK — combined `21:15–17` has all content |

**Gap-fix rule:** minimal inline inserts; no full article rewrite unless user requests rebuild.

---

## audit_yaml_verses.py

Detects gaps `validate_article.py` misses:

```bash
python ~/.cursor/skills/biblerevelation-sermon-articles/scripts/audit_yaml_verses.py \
  --html ~/praisonai-audio-editor/.agent/biblerevelation-{slug}.html \
  --yaml ~/praisonaippt/examples/deck.yaml
```

Output statuses:

| Status | Meaning |
|--------|---------|
| `OK` | Ref or text found in HTML |
| `CONTENT PRESENT` | Verse words in HTML but citation split/merged |
| `MISSING` | Ref and content absent — must fix before publish |

Optional teaching-label check:

```bash
python .../audit_yaml_verses.py --html ... --yaml ... --check-labels
```

---

## Legacy — do not use for new articles

`~/praisonai-audio-editor/.agent/apply_highlights.py` appended a `📖 Scripture from the Slides` block. If present in old HTML:

1. Delete appendix section entirely
2. Move each verse inline to correct h2
3. Remove empty `📖` headings
