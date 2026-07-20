---
name: biblerevelation-sermon-articles
description: Transcript + PPT YAML deck → biblerevelation.org sermon article. Use ONLY when the user provides (or you transcribe) a sermon transcript AND a YAML deck. Do NOT use for generic posts, post_publish SDK jobs, or posts without a transcript — use biblerevelation-create-post instead.
disable-model-invocation: true
---

# biblerevelation.org Sermon Articles

**Router:** repo root [`AGENTS-SERMON-ARTICLES.md`](../../AGENTS-SERMON-ARTICLES.md)

**One input → one output:** transcript + YAML → live article.

## Which skill?

| You have | Use |
|----------|-----|
| Transcript + YAML deck | **This skill** → [pipeline.md](pipeline.md) |
| HTML/markdown ready, no transcript workflow | [biblerevelation-create-post](../biblerevelation-create-post/SKILL.md) |
| YouTube URL, need audio/transcript first | [youtube-clip-transcribe](../youtube-clip-transcribe/SKILL.md) |
| praisonaiwp / SSH / categories | [create-post/reference.md](../biblerevelation-create-post/reference.md) |

**Do not read both sermon-articles and create-post for the same task** — pick one row above.

**Workflow:** [pipeline.md](pipeline.md) Phases 0–11 only.  
**YAML mapping:** [yaml-and-transcript.md](yaml-and-transcript.md).  
**Block templates & audit scripts:** [reference.md](reference.md).

If transcript or YAML is missing → **stop and ask the user**.

---

## Golden rule

**REWRITE from scratch in transcript order. NEVER append.**

Appending caused duplicate sections (e.g. Great Faith had the “4 Characteristics” block twice). Each rebuild replaces the entire `.html` file body.

---

## Reference articles (read before writing)

Match **structure and density**, not word-for-word copying:

| Live URL | Why |
|----------|-----|
| https://biblerevelation.org/2026/06/reigning-in-life-the-two-keys-to-living-victorious/ | Primary pattern — inline verses, tables, recap sections |
| https://biblerevelation.org/2025/12/authority-over-death-through-jesus-christ/ | Transcript-faithful flow, OT history tables |
| https://biblerevelation.org/2026/06/great-faith-christs-obedience/ | Exam analogy, characteristic lists |
| https://biblerevelation.org/2026/07/the-three-raptures-explained-church-tribulation-saints-and-old-testament-resurrection/ | Long-form interactive teaching |
| https://biblerevelation.org/2026/07/freedom-from-all-your-troubles/ | Scannable tables + short paragraphs |
| https://biblerevelation.org/2026/07/receive-a-hundredfold-now/ | Gold standard — lists/tables before prose |
| https://biblerevelation.org/2026/07/love-of-god-2/ | Emoji h2 + comparison tables |
| https://biblerevelation.org/2026/07/freedom/ | Interactive digest, not transcript walls |

Local copies: `~/praisonai-audio-editor/.agent/biblerevelation-*.html`

---

## Source files

| Input | Typical path |
|-------|----------------|
| Transcript (plain text) | `~/Downloads/BIC-Sermon-Deck-Pack/{Sermon Title}.transcript.txt` |
| Transcript (JSON, optional) | `~/praisonai-audio-editor/{id}.transcript.json` — use `text` field if no `.txt` |
| PPT YAML deck | `~/praisonaippt/examples/{snake_case}.yaml` |
| Draft HTML (output) | `~/praisonai-audio-editor/.agent/biblerevelation-{slug}.html` |

**Before writing:** read the **entire** transcript top-to-bottom once. Build a mental section outline in sermon order.

**If either transcript or YAML is missing → stop and ask the user.** Do not publish from memory or partial notes.

Known transcript ↔ YAML mapping → [reference.md](reference.md) § sermon mapping.

---

## Title and slug

Rewrite SEO title and kebab-case slug — never copy YouTube or sermon deck names. Full rules and WP-CLI commands → [create-post/reference.md](../biblerevelation-create-post/reference.md) § Title and slug.

---

## What “good” looks like

### Content

- **≥85% spoken-point coverage** — every major teaching block, illustration, table-worthy comparison, and story beat from the transcript appears **in sermon order**
- **Interactive, not prose walls** — emoji `h2`/`h3`, bullet lists, comparison tables, blockquotes, numbered steps
- **Interactive digest (mandatory)** — each `h2` section uses **one short intro paragraph (≤450 chars)** then **bullets, ordered list, or table** — never paste spoken transcript run-ons
- **≥6 list blocks + ≥1 table** per article — structure-audit enforces this
- **Condense repetition** — call-and-response (“tell the person next to you”) → shorten to blockquote or drop; **doctrine and stories must stay**
- **British English** — no preacher attribution in body

### YAML verses

- **Every verse in the YAML deck** appears **inline** where the transcript discusses that topic
- **No appendix** — never end with `📖 Scripture from the Slides` or a verse dump block
- Verse reference line: `<strong>Book chapter:verse (NKJV)</strong>` in a **paragraph** — **not** an `h3` per verse

### Highlights

| Colour | Hex | Use |
|--------|-----|-----|
| Green | `#bbf7d0` | Grace / apart-from-works truth |
| Gold | `#fde68a` | Precious gift / key promise terms |

```html
<mark style="background-color:#bbf7d0"><strong>term</strong></mark>
<mark style="background-color:#fde68a"><strong>term</strong></mark>
```

Include a highlight-key blockquote near the top (see Reign in Life example).

### Gutenberg blocks

Use native block comments — content is pre-Gutenberg; publish with `--no-block-conversion`:

- `<!-- wp:heading -->` / `h2` sections, `h3` subsections
- `<!-- wp:paragraph -->`, `<!-- wp:list -->`, `<!-- wp:table -->`
- `<!-- wp:quote -->` for verses and teaching quotes
- `<!-- wp:separator -->` between major sections
- `<!-- wp:image -->` for inline concept art (see Images)

### Closing (every article)

End with standard pattern — see [reference.md](reference.md) § closing template:

1. `🎯 The Takeaway` — ordered list of 4–7 bullet truths from the sermon
2. Separator
3. Footer: `🎧 Scripture-based study on {topic}. If it strengthened you, share it with someone who needs this truth today. 💛`

Templates → [reference.md](reference.md) § block templates.

---

## Workflow

Follow [pipeline.md](pipeline.md) only. Checklist:

```
- [ ] 1. Confirm transcript + YAML exist (else STOP — ask user)
- [ ] 2. Rewrite SEO title + deliberate kebab-case slug (not source headline)
- [ ] 3. Read full transcript; list sections in sermon order
- [ ] 4. Read YAML; map each verse to transcript section (see yaml-and-transcript.md)
- [ ] 5. Read one reference .html for tone
- [ ] 6. Write HTML from scratch — interactive digest, sermon order
- [ ] 7. validate_article.py + audit_yaml_verses.py — fix all FAIL/MISSING
- [ ] 8. Self-audit (≥85% spoken points, 100% YAML verses inline, no filler phrases)
- [ ] 9. Generate landscape featured cover (1536x1024)
- [ ] 10. praisonaiwp create or update — verify HTTP 200
- [ ] 11. Validate live (no duplicate headings, no appendix dump)
```

**Do not publish the full article in one blind pass.** Update the local file section-by-section if needed; publish when ready.

---

## Self-audit checklist

Before `praisonaiwp update`:

| Check | Pass criterion |
|-------|----------------|
| Title / slug | Rewritten for SEO; verified vs YouTube oEmbed — no shared hook phrases |
| Transcript order | Sections follow sermon flow top-to-bottom |
| Spoken-point coverage | ≥85% of major teaching blocks present |
| YAML verses | 100% inline; count matches YAML slide count |
| No appendix | `Scripture from the Slides` absent |
| No duplicates | Each `h2`/`h3` title appears once |
| Highlights | Green/gold on key terms in quotes |
| Images | Landscape `1536x1024`; visual-brief meaning test passed; featured ≠ inline |
| Word ratio | Body typically **≥55%** of transcript word count when coverage is good (summary-only drafts sit ~28–50%) |

Audit helpers → [reference.md](reference.md) § audit commands.

---

## Scope rules (learned from production)

| Rule | Reason |
|------|--------|
| **Do not modify posts the user did not ask to change** | User reverted pre-July posts; only images were re-applied |
| **July-created posts** | Full transcript rebuilds OK when user requests |
| **Revert broken content** | Use WordPress revision before session edits; June revision if July snapshot causes HTTP 500 |
| **Omit non-doctrinal asides** | Event dates, “tell person next to you” logistics — optional trim |
| **Keep Tamil phrases** when they carry meaning; skip pure audience banter |

---

## Anti-patterns

| ❌ Don't | ✅ Do |
|---------|------|
| Copy YouTube/sermon title to WordPress title or slug | Rewrite SEO title; verify vs oEmbed — zero shared hook phrases |
| Decorative image ("sunrise over hills") | Visual-brief mental model — image teaches concept alone |
| Let WordPress auto-slug from a source hook | Set `post_name` via WP-CLI after create |
| Append new sections to old HTML | Rewrite entire body in transcript order |
| Summarise transcript to ~30–50% | Target ≥85% spoken-point coverage |
| Dump YAML verses in appendix | Weave each verse inline at the right heading |
| One `h3` per verse reference | Paragraph ref + blockquote for text |
| Publish without reading transcript | Read full `.transcript.txt` first |
| Use `praisonaiwp` without `--no-block-conversion` | Always pass flag for Gutenberg HTML |
| `--post_content=-` over SSH without testing | SCP file to server or use praisonaiwp locally |
| `praisonaiwp update --append` for sermon body | Full `--post-content "$(cat file.html)"` replace |
| Empty `<h2>📖 </h2>` left after appendix removal | Delete heading or replace with real section title |

---

## Additional resources

| File | Contents |
|------|----------|
| [pipeline.md](pipeline.md) | **Only workflow** — transcribe → publish |
| [yaml-and-transcript.md](yaml-and-transcript.md) | YAML schema, verse mapping |
| [reference.md](reference.md) | Block templates, sermon mapping, validators |
| [examples.md](examples.md) | Good/bad patterns |
| [create-post/reference.md](../biblerevelation-create-post/reference.md) | praisonaiwp, SSH, title/slug, images policy |
