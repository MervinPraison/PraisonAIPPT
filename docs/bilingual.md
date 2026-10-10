# English + Tamil slides

Show each scripture verse in English and Tamil (TAOVBSI / Tamil O.V.) on the same slide.

## Where the Tamil text comes from

The SDK supports two sources. **If the YAML gives the Tamil, that is used; anything missing is looked up in the Tamil Bible:**

| Source | When to use it | How |
|---|---|---|
| **Tamil Bible lookup** (default) | Almost always. Nothing is copied by hand, verse ranges work, and the text is verbatim O.V. | Add a `bilingual:` block, or pass `--bilingual ta`. Each verse's English `reference` is looked up, e.g. `Romans 10:6–12 (NKJV)` → `ரோமர் 10:6-12 (TAOVBSI)` with the text of verses 6–12. |
| **YAML** | A different verse range, edited wording, or a machine without the Bible file | Set `text_ta` (and optionally `reference_ta`) on the verse. Or set only `reference_ta` (for example `எபேசியர் 1:18-19 (TAOVBSI)`) to look up a different range. |

The Bible file is the JSON written by `praisonai-lyrical-video bible-import`. The SDK looks for it in this order:

1. `bilingual.bible_path` in the deck
2. `$PRAISONAI_TAMIL_BIBLE`
3. `~/.praisonai/lyrical-video/tamil-ov.json`
4. `~/.praisonaippt/tamil-ov.json`

Tamil **highlights are never guessed**, because Tamil word order differs from English. Write them as `highlights_ta`. Every build prints a report:

```
Bilingual: 36 scripture slides — 36 from the Tamil Bible, 0 from YAML, 0 without Tamil
  ✗ Romans 10:18: no verse Romans 10:18 in the Tamil Bible
  ✗ Hebrews 4:2: highlights_ta 'xyz' is not in the Tamil text
  · English highlights but no highlights_ta: Malachi 3:8, …
```

With `strict: true`, any ✗ line fails the build instead of producing a slide with Tamil missing.

## Deck keys

```yaml
bilingual:
  language: ta          # only Tamil has a bundled lookup
  version: TAOVBSI      # label after the Tamil reference
  source: auto          # auto = look up missing verses; yaml = use only text_ta
  strict: true          # fail when a verse has no Tamil or a highlights_ta phrase is not found

slide_style:
  font_name: Noto Serif
  tamil_font_name: Noto Serif Tamil   # set on the Latin, East Asian and complex-script font slots, plus lang="ta-IN"
  bilingual_layout: cards             # cards | paired | below
  bilingual_primary: tamil            # tamil | english — which language comes first
  bilingual_overflow: split           # split | paired — what to do when a verse cannot fit
  typography:
    bilingual_en_size_pt: 28
    bilingual_ta_size_pt: 26
    bilingual_min_size_pt: 24
  layouts:
    bilingual_cards: {card_opacity_top: 0.70, card_opacity_bottom: 0.82, max_parts: 6}

sections:
- section: 1. Sent
  section_ta: 1. அனுப்பப்படுதல்
  section_subtitle: How shall they preach unless they are sent
  section_subtitle_ta: அனுப்பப்படாவிட்டால் எப்படிப் பிரசங்கிப்பார்கள்
  verses:
  - reference: Malachi 3:8 (NKJV)
    leading_title: Tithes and Offerings
    leading_title_ta: தசமபாகமும் காணிக்கைகளும்
    text: ...
    highlights: [tithes and offerings]
    highlights_ta: [தசமபாகத்திலும் காணிக்கைகளிலுந்தானே]
  - reference: John 3:16
    bilingual: false      # this verse stays English-only
```

`section_ta`, `section_subtitle_ta`, `leading_title_ta` and `highlights_ta` have no effect when an English-only deck is built. They can live in the English deck, and a bilingual variant reuses its sections:

```yaml
# he_will_not_put_to_shame_ta.yaml
presentation_title: He will not put to shame / அவன் வெட்கப்படுவதில்லை
bilingual: {language: ta, strict: true}
slide_style: {bilingual_layout: cards, bilingual_primary: tamil, tamil_font_name: Noto Serif Tamil}
sections_from: he_will_not_put_to_shame.yaml
```

## Layouts

- **`cards`** (default): two rounded translucent cards, one per language, over the background. The text is measured with the real font files when they are installed, and with calibrated per-script widths otherwise. A verse is first shrunk (28/26 pt down to 24 pt). If it still doesn't fit, both languages are split at clause breaks into `(1/2)`, `(2/2)` slides, never inside a highlighted phrase.
- **`paired`**: one full-size slide per language, back to back.
- **`below`**: the original layout, with the Tamil under the English. Kept for older decks.

## Commands

```bash
praisonaippt -i examples/he_will_not_put_to_shame_ta.yaml -o out.pptx
praisonaippt -i any_english_deck.yaml --bilingual ta -o out.pptx      # turn any deck bilingual
praisonaippt -i deck.yaml --no-upload                                  # ignore auto_upload_gdrive
praisonaippt bilingual-fill deck.yaml -o deck_filled.yaml              # write the looked-up Tamil into a portable YAML
```

## Fonts

Use fonts that exist wherever the deck is shown. **Noto Serif + Noto Serif Tamil**, or Noto Sans + Noto Sans Tamil, are built into Google Slides and free to install on Mac and Windows. Avoid Apple-only faces such as Tamil MN and Palatino. Google Slides doesn't have them, so it substitutes other fonts and the line breaks change.

## Python

```python
from praisonaippt import create_presentation, load_verses_from_file
from praisonaippt.bilingual import tamil_text, tamil_reference, load_tamil_bible

tamil_text("Romans 10:6–12", load_tamil_bible())
tamil_reference("Romans 10:17 (NKJV)")      # 'ரோமர் 10:17 (TAOVBSI)'
create_presentation(load_verses_from_file("deck_ta.yaml"), output_file="deck_ta.pptx")
```
