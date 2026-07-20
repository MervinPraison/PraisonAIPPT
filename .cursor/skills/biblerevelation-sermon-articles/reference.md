# Reference — biblerevelation.org sermon articles

**Publish, SSH, title/slug, image policy:** [create-post/reference.md](../biblerevelation-create-post/reference.md) — do not duplicate those sections here.

This file: sermon file mapping, Gutenberg block templates, validate scripts only.

---

## Sermon mapping (BIC deck)

| Transcript file | YAML | Local HTML slug | Notes |
|-----------------|------|-----------------|-------|
| `Authority over Death through Jesus Christ.transcript.txt` | `authority_over_death.yaml` | `authority-over-death-through-jesus-christ` | Reference quality |
| `Reign in Life.transcript.txt` | `reign_in_life.yaml` | `reign-in-life` | **Primary style reference** |
| `Great Faith.transcript.txt` | `great_faith.yaml` | `great-faith` | Exam / biriyani analogies |
| `100 Fold Blessing.transcript.txt` | `100_fold_blessing.yaml` | `100-fold-blessings` | Four levels of faith |
| `Can God allow sickness in our lives, like Job?.transcript.txt` | `job_sickness.yaml` | `can-god-allow-sickness-like-job` | |
| `How to Come Out of Testing and Trials.transcript.txt` | `how_to_come_out_of_testing_and_trials.yaml` | `how-to-come-out-of-testing-and-trials` | |
| `God is Good ALL the Time.transcript.txt` | `god_is_good_all_the_time.yaml` | `god-is-good-all-the-time` | Jehoshaphat, 50th day |
| `Freedom.transcript.txt` | `freedom_in_spirit.yaml` | `freedom` | Two trees, Gal 5:4 |
| `Love of God.transcript.txt` | `love_of_god.yaml` | `love-of-god` | agape vs phileo |
| `receive a hundredfold now.transcript.txt` | `receive_a_hundredfold_now.yaml` | `receive-a-hundredfold-now` | Tithing, 40 YAML verses |
| `Freedom from ALL your troubles.transcript.txt` | `freedom_from_all_your_troubles.yaml` | `freedom-from-all-your-troubles` | Abraham, Romans 4 |

Paths:

- Transcripts: `~/Downloads/BIC-Sermon-Deck-Pack/{Sermon Title}.transcript.txt`
- YAML: `~/praisonaippt/examples/{snake_case}.yaml`
- Drafts: `~/praisonai-audio-editor/.agent/biblerevelation-{slug}.html`

## Block templates

### Opening (h3 title + anchor verse + highlight key)

```html
<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">🌾 Sermon Title — Subtitle Hook</h3>
<!-- /wp:heading -->

<!-- wp:quote -->
<blockquote class="wp-block-quote"><p><em>"Verse text with <mark style="background-color:#fde68a"><strong>key term</strong></mark>…"</em> — <strong>Book 0:0 (NKJV)</strong></p></blockquote>
<!-- /wp:quote -->

<!-- wp:quote -->
<blockquote class="wp-block-quote"><p>🎨 <strong>Highlight key:</strong> 🟩 = grace / <em>apart-from-works</em> truth · 🟨 = the precious gift · <strong>bold</strong> = key terms</p></blockquote>
<!-- /wp:quote -->

<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->
```

### Section heading (h2)

```html
<!-- wp:heading -->
<h2 class="wp-block-heading">📖 Section Title in Transcript Order</h2>
<!-- /wp:heading -->
```

### Verse inline (paragraph ref + blockquote — not h3)

```html
<!-- wp:paragraph -->
<p><strong>Romans 5:17 (NKJV)</strong></p>
<!-- /wp:paragraph -->

<!-- wp:quote -->
<blockquote class="wp-block-quote"><p><em>"…<mark style="background-color:#bbf7d0"><strong>reign in life</strong></mark>…"</em> — <strong>Romans 5:17 (NKJV)</strong></p></blockquote>
<!-- /wp:quote -->
```

### Comparison table

```html
<!-- wp:table -->
<figure class="wp-block-table"><table style="width:100%"><thead><tr><th>World's way</th><th>God's way</th></tr></thead><tbody><tr><td>…</td><td>…</td></tr></tbody></table></figure>
<!-- /wp:table -->
```

### Inline image (preserve when rewriting)

```html
<!-- wp:image {"id":MEDIA_ID,"sizeSlug":"large","linkDestination":"none","align":"wide"} -->
<figure class="wp-block-image alignwide size-large"><img src="https://biblerevelation.org/wordpress/wp-content/uploads/…" alt="Concept illustration" class="wp-image-MEDIA_ID"/></figure>
<!-- /wp:image -->
```

Insert after the **first** `<!-- /wp:separator -->` unless the live post places it elsewhere — **match existing placement** when updating.

### Closing (Takeaway + footer)

```html
<!-- wp:heading -->
<h2 class="wp-block-heading">🎯 The Takeaway</h2>
<!-- /wp:heading -->

<!-- wp:list {"ordered":true} -->
<ol class="wp-block-list"><li>💚 <strong>Key truth one</strong> — short explanation</li><li>✝️ <strong>Key truth two</strong> — short explanation</li></ol>
<!-- /wp:list -->

<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->

<!-- wp:paragraph -->
<p><em>🎧 Scripture-based study on [topic]. If it strengthened you, share it with someone who needs this truth today. 💛</em></p>
<!-- /wp:paragraph -->
```

### Recap section (multi-sermon series)

When the transcript references a prior week’s teaching:

```html
<!-- wp:heading -->
<h2 class="wp-block-heading">📚 Quick Recap: [Prior Sermon Title]</h2>
<!-- /wp:heading -->
```

Use a comparison table summarising the prior message before new content (see Reign in Life → Job recap).

---

## Images

Generate and upload steps → [pipeline.md](pipeline.md) Phase 7.  
Image policy (visual brief, landscape sizes) → [create-post/reference.md](../biblerevelation-create-post/reference.md) § Images.

---

## Published sermon articles (live URLs)

| Post ID | Title | URL |
|---------|-------|-----|
| 240230 | Reign in Life | https://biblerevelation.org/2026/06/reigning-in-life-the-two-keys-to-living-victorious/ |
| 240088 | Authority over Death | https://biblerevelation.org/2025/12/authority-over-death-through-jesus-christ/ |
| 240082 | Can God Allow Sickness Like Job? | https://biblerevelation.org/2025/12/can-god-allow-sickness-in-our-lives-like-job/ |
| 240064 | Testing and Trials | https://biblerevelation.org/2026/04/how-to-come-out-of-testing-and-trials/ |
| 240197 | 100 Fold Blessings | https://biblerevelation.org/2026/05/100-fold-blessings/ |
| 240228 | Great Faith | https://biblerevelation.org/2026/06/great-faith-christs-obedience/ |
| 240335 | God Is Good ALL the Time | https://biblerevelation.org/2026/07/god-is-good-all-the-time/ |
| 240337 | Freedom | https://biblerevelation.org/2026/07/freedom/ |
| 240340 | Love of God | https://biblerevelation.org/2026/07/love-of-god-2/ |
| 240342 | Receive a Hundredfold Now | https://biblerevelation.org/2026/07/receive-a-hundredfold-now/ |
| 240346 | Freedom from ALL Your Troubles | https://biblerevelation.org/2026/07/freedom-from-all-your-troubles/ |

Resolve any URL: `curl -sI "https://biblerevelation.org/?p=POST_ID" | grep -i location`

---

## Published posts detail (July 2026 batch)

| Post ID | Title | URL path | Inline media |
|---------|-------|----------|--------------|
| 240335 | God is Good ALL the Time | `/2026/07/god-is-good-all-the-time/` | 240359 |
| 240337 | Freedom | `/2026/07/freedom/` | 240360 |
| 240340 | Love of God | `/2026/07/love-of-god-2/` | 240362 |
| 240342 | receive a hundredfold now | `/2026/07/receive-a-hundredfold-now/` | none |
| 240346 | Freedom from ALL your troubles | `/2026/07/freedom-from-all-your-troubles/` | 240366 |

Pre-July reference posts (do not rewrite without user permission): 240088, 240082, 240064, 240197, 240228, 240230.

---

## YAML verse workflow

1. Parse YAML slides — extract reference + verse text + any `highlights` / `large_text`
2. While reading transcript, note when each reference is taught
3. Place verse blockquote **under the h2/h3** that covers that teaching
4. Apply `#bbf7d0` / `#fde68a` to highlighted words from YAML `highlights:` list where present
5. YAML `large_text:` fields (Hebrew word studies) → centred paragraph or blockquote; 80pt styling optional
6. Final pass: count YAML references vs inline blockquotes — must match

**Legacy helper** (appendix mode — do **not** use for new articles):

```bash
cd ~/praisonai-audio-editor/.agent
python apply_highlights.py --yaml ~/praisonaippt/examples/example.yaml \
  --heading "…" --html biblerevelation-example.html
```

If used historically, **remove the appendix** and move verses inline manually.

---

## Audit commands

### Word count ratio (transcript vs draft)

```bash
python3 <<'PY'
import re
from pathlib import Path
t = Path("~/Downloads/BIC-Sermon-Deck-Pack/SERMON.transcript.txt").expanduser().read_text()
h = Path("~/praisonai-audio-editor/.agent/biblerevelation-SLUG.html").expanduser().read_text()
tw = len(re.findall(r"\w+", t))
hw = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", h)))
print(f"transcript={tw} html_text≈{hw} ratio={hw/tw:.0%}")
PY
```

Target: **≥55% word ratio** usually correlates with ≥85% spoken-point coverage. Love of God at 28% ratio was critically under-built.

### Duplicate heading scan

```bash
python3 <<'PY'
import re
from pathlib import Path
from collections import Counter
c = Path("FILE.html").read_text()
h2 = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<h2[^>]*>(.*?)</h2>", c, re.S)]
for title, n in Counter(h2).items():
    if n > 1: print(f"DUPLICATE x{n}: {title[:70]}")
print("appendix:", "Scripture from the Slides" in c)
PY
```

### Live post check

```bash
curl -sL -o /dev/null -w "%{http_code}\n" "https://biblerevelation.org/…/"
curl -sL "URL" | grep -c "Scripture from the Slides"
curl -sL "URL" | grep -c "critical error"
```

### Automated validate scripts

```bash
python ~/.cursor/skills/biblerevelation-sermon-articles/scripts/validate_article.py \
  --html ~/praisonai-audio-editor/.agent/biblerevelation-god-is-good-all-the-time.html \
  --transcript ~/Downloads/BIC-Sermon-Deck-Pack/God\ is\ Good\ ALL\ the\ Time.transcript.txt \
  --yaml ~/praisonaippt/examples/god_is_good_all_the_time.yaml

python ~/.cursor/skills/biblerevelation-sermon-articles/scripts/audit_yaml_verses.py \
  --html ~/praisonai-audio-editor/.agent/biblerevelation-god-is-good-all-the-time.html \
  --yaml ~/praisonaippt/examples/god_is_good_all_the_time.yaml
```

Requires `pyyaml` for YAML checks (`pip install pyyaml` if missing).

### Interactive digest checklist (mandatory)

Before publish, every article must pass:

| Check | Rule |
|-------|------|
| h2 sections | ≥8 sermon-specific titles |
| Paragraph length | ≤450 chars per `<p>` — no transcript walls |
| Lists | ≥6 `wp-block-list` blocks across article |
| Tables | ≥1 comparison or summary table |
| Highlight key | Blockquote near top |
| Takeaway | `🎯 The Takeaway` ordered list |
| Footer | `Scripture-based study on …` |
| Appendix | No `Scripture from the Slides` dump |
| Section pattern | h2 → 1 short intro → list/table → verses |
| Filler | No “tell the person next to you”, “shall we all read”, “again tell” |
| Word ratio | ≥55% when coverage is good (summary drafts sit ~28–50%) |
| Formatting | `<strong>`, `<em>`, `<mark>` on key grace/gift terms |

Run `validate_article.py` then `audit_yaml_verses.py` before publish.

Reference digests: receive-a-hundredfold-now, freedom, love-of-god-2, freedom-from-all-your-troubles.

### Spoken-point audit (manual)

1. Read transcript once; note every **h2-worthy** block (story, table, numbered list, key objection)
2. After drafting, tick each block against the HTML outline
3. Target **≥85%** of blocks present in order
4. Word ratio ≥55% is a sanity check — not a substitute for block coverage

---

## Publish & server

All `praisonaiwp`, SSH, categories, and revert commands → [create-post/reference.md](../biblerevelation-create-post/reference.md).

Publish steps for sermon articles → [pipeline.md](pipeline.md) Phase 9.

---

## Coverage targets (July 2026 rebuild benchmarks)

| Article | Before ratio | After | Spoken-point audit |
|---------|--------------|-------|-------------------|
| God Is Good | 48% | 59% words | ~90%+ |
| Freedom | 57% | ~2× words | ~92% |
| Love of God | **28%** | ~2.5× words | ~90% |
| Hundredfold now | 50% | ~2× words | ~93% |
| Freedom from troubles | 57% | ~1.5× words | ~90% |

**Lesson:** sub-50% word ratio almost always means a script summary, not a sermon article.
