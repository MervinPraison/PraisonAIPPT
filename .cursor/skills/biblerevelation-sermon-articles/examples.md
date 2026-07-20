# Examples — biblerevelation sermon articles

## End-to-end example (new sermon from YAML + transcript)

**Goal:** Publish `God is Good ALL the Time` from transcript + YAML.

```
Phase 1 — Transcript:
  ~/Downloads/BIC-Sermon-Deck-Pack/God is Good ALL the Time.transcript.txt

Phase 2 — YAML:
  ~/praisonaippt/examples/god_is_good_all_the_time.yaml
  (18 reference slides + 2 text-only verse markers: Colossians 2:16, Isaiah 28:21)

Phase 3 — Outline (9 h2 sections in sermon order):
  See § God Is Good section flow below

Phase 4 — Map YAML:
  Jeremiah 29:11 → "God's Plan" section
  2 Chronicles 20:22–23 → Jehoshaphat section
  Colossians 2:14 + 2:16 → "Christ ends law" section
  …

Phase 5 — Write:
  ~/praisonai-audio-editor/.agent/biblerevelation-god-is-good-all-the-time.html
  (rewrite from scratch — never append)

Phase 6 — Audit:
  validate_article.py → PASS
  audit_yaml_verses.py → fix Col 2:16 / Isa 28:21 if MISSING

Phase 7 — Images:
  featured + inline at 1536x1024 (different files)

Phase 9 — Publish:
  praisonaiwp update 240335 --server biblerevelation --no-block-conversion

Phase 10 — Verify:
  curl → HTTP 200; grep Isaiah 28:21 on live page
```

Full phased checklist → [pipeline.md](pipeline.md)

---

## ✅ Good vs ❌ bad

### Transcript fidelity

| ❌ Bad (script summary) | ✅ Good (sermon article) |
|------------------------|-------------------------|
| One paragraph per topic | Section per transcript beat with tables/lists |
| Skips OT history (Cain, Abraham, Jacob) | Full history table in sermon order |
| “God is good” stated once | Jehoshaphat story, Psalm 136 lyrics, Jericho, dot-on-screen analogy |
| 28% of transcript words | ≥85% spoken-point coverage |

### YAML verses

| ❌ Bad | ✅ Good |
|--------|---------|
| `## 📖 Scripture from the Slides` appendix at end | Each verse under the h2 that teaches it |
| 40 verses in one block | Jeremiah 29:11 under “God’s plan” section; Gal 5:4 under “fall from grace” |
| Missing verses from YAML | 36/36 or 40/40 inline count matches YAML |

### Structure

| ❌ Bad | ✅ Good |
|--------|---------|
| Append “4 Characteristics” after existing “4 Characteristics” | Single characteristic block; rewrite whole file |
| Empty `<h2>📖 </h2>` after appendix removal | Remove heading or fill with real section |
| `h3` for every verse reference | `<p><strong>Romans 5:17 (NKJV)</strong></p>` + blockquote |
| 5 consecutive 750-char transcript paragraphs | 1 short intro + bullet list + table per section |
| “Tell the person next to you, full restoration…” pasted verbatim | Ordered list: Saved → Life → Full restoration |

### Interactive digest (July 2026 reference)

| ❌ Bad | ✅ Good |
|--------|---------|
| Raw spoken run-on in `<p>` blocks | ≤450-char condensed intro + bullets |
| One giant paragraph per h2 | Table or list **before** any long prose |
| No tables in comparison sermon | Partial vs Full table, Law vs Faith table |
| Reader must parse 800 words to find 3 points | 3–5 emoji bullets surface the teaching instantly |

Reference: https://biblerevelation.org/2026/07/receive-a-hundredfold-now/

---

## Section flow example (God Is Good)

Transcript order → article h2 map:

1. Opening / miracles easy / Joshua-Caleb → **🙌 Before We Begin — Miracles Are Easy**
2. He meets all your needs / Psalm 23 → **💚 He Meets ALL Your Needs**
3. Jeremiah 29:11 / speak to sickness → **📜 Jeremiah 29:11 — God's Plan Is Prosperity**
4. Jehoshaphat / worship singers / Psalm 136 → **⚔️ Jehoshaphat: Three Enemies, One Strategy**
5. God is good / OT history table → **😇 When Is God Angry?**
6. Wilderness 50 days / Pentecost law → **📅 The 50th Day — When Everything Changed**
7. Law trap / school marks table → **⚖️ The Law Trap — 99 Marks = Zero**
8. Christ ends law / lion-snake → **🦁 The Roaring Lion — Actually a Snake**
9. Closing prayer → **🙏 Closing Prayer**

Each section: short paragraphs + at least one interactive element (table, list, or quote block).

---

## Section flow example (Full Restoration)

**Process:** read entire transcript → map 12 sections in sermon order → write HTML from scratch.

| Sermon beat (transcript order) | Article h2 |
|-------------------------------|------------|
| 100% not 50/80/90, youth, Sarah | 💯 God's Aim — 100% Full Restoration |
| Recap: wisdom, faith, desire, His righteousness | 📖 Recap — Wisdom, Faith, Desire… |
| Matthew 6 don't worry, birds, seek His kingdom | 🌸 Don't Worry — Matthew 6 |
| John 10 three steps preview | 📋 Three Steps — Saved → Life → Full |
| Step 1 saved, sózó, Ephesians 2 | 🚪 Step 1: Saved — Gate and Sōzó |
| Zero sickness math | 🔢 Simple Math — Zero Sickness |
| … | … |
| Heir of the world, Romans 4:13 | 👑 Heir of the World — Authority Through Faith |

Each section: **intro + bullets/table + inline verses** — never `"we are going to see…"` transcript paste.

Reference: https://biblerevelation.org/2026/07/full-restoration-hundred-percent-in-christ/

---

## Image orientation

Featured and inline sermon art must be **landscape** (`1536x1024` with `gpt-image`), not portrait (`1024x1536`). Use `alignwide` on inline `wp:image` blocks so concept art spans the content column on desktop.

---

## Highlight example (from Reign in Life)

```html
<!-- wp:quote -->
<blockquote class="wp-block-quote"><p><em>"…those who receive <mark style="background-color:#fde68a"><strong>abundance of grace</strong></mark> and of the <mark style="background-color:#fde68a"><strong>gift of righteousness</strong></mark> will <mark style="background-color:#bbf7d0"><strong>reign in life</strong></mark>…"</em> — <strong>Romans 5:17 (NKJV)</strong></p></blockquote>
<!-- /wp:quote -->
```

---

## Table example (world vs God — Jehoshaphat)

```html
<!-- wp:table -->
<figure class="wp-block-table"><table style="width:100%"><thead><tr><th>World's way</th><th>God's way</th></tr></thead><tbody><tr><td>Send warriors to the front</td><td>Send <strong>worship singers</strong> to the front 🎵</td></tr><tr><td>Focus on how big the enemy is</td><td>Focus on how <strong>big your God</strong> is</td></tr><tr><td>Sing whatever feels right</td><td>Sing <strong>only</strong> the lyrics Jehoshaphat wrote</td></tr></tbody></table></figure>
<!-- /wp:table -->
```

---

## Iterative workflow example

**User:** “Rebuild Love of God — missing most of the transcript.”

```
1. Read ~/Downloads/BIC-Sermon-Deck-Pack/Love of God.transcript.txt (full)
2. Read ~/praisonaippt/examples/love_of_god.yaml — note 16 verses
3. Open biblerevelation-reign-in-life.html for tone
4. Delete body of biblerevelation-love-of-god.html conceptually — rewrite from h3 title
5. Build section-by-section in transcript order (save file after each major h2)
6. Audit: 16/16 verses inline, no appendix, h2 titles unique
7. Keep wp-image-240362 block from previous version
8. praisonaiwp update 240340 --server biblerevelation --no-block-conversion
9. curl live URL → 200
```

**Result:** 1,598 → 4,020 words; ~28% → ~90% coverage.

---

## What to trim (optional)

Safe to shorten without losing doctrine:

- “How many of you are excited?” / “Are you awake?”
- Christmas programme date announcements
- Repeated “shall we read together” (keep the verse, shorten the intro)
- Tamil audience banter (keep phrases that explain a concept)

**Do not trim:** OT narratives, numbered lists the preacher counts on fingers, law/grace turning points, closing prayer declarations.

---

## Closing template (full)

```html
<!-- wp:heading -->
<h2 class="wp-block-heading">🎯 The Takeaway</h2>
<!-- /wp:heading -->

<!-- wp:list {"ordered":true} -->
<ol class="wp-block-list"><li>…</li></ol>
<!-- /wp:list -->

<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->

<!-- wp:paragraph -->
<p><em>🎧 Scripture-based study on [topic]. If it strengthened you, share it with someone who needs this truth today. 💛</em></p>
<!-- /wp:paragraph -->
```

---

## Recap section (series sermons)

Reign in Life opens with **Quick Recap: Can God Allow Sickness Like Job?** — four-row table + inline verses before new teaching. Use the same pattern when the transcript explicitly recaps a prior message.
