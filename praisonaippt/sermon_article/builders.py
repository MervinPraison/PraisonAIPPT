"""Article builders — registry of generic and named transcript-faithful builders."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from . import blocks as b
from .deck import deck_verses, load_deck
from .faithful import build_faithful
from .protocol import SermonJob, SermonPack
from .transcript import filter_sentences


def _section_title(name: str, idx: int) -> str:
    name = name.strip()
    if not name:
        return f"📖 Teaching Block {idx}"
    emojis = {
        "separated": "⛓️", "fallen": "📉", "cursed": "☠️", "death": "☠️",
        "apart": "⚖️", "witnessed": "📜", "mix": "⚠️", "victorious": "🏆",
        "grace": "📈", "healing": "🩺", "hear": "👂", "fruitful": "🌳",
        "delay": "⏱️", "abraham": "👴", "restoration": "💯", "gospel": "✝️",
    }
    low = name.lower()
    for key, emoji in emojis.items():
        if key in low:
            return f"{emoji} {name}"
    return f"📖 {name}" if name[0] not in "📖🌿✝️⚡🎯1️⃣2️⃣3️⃣" else name


def build_generic(job: SermonJob, pack: SermonPack) -> str:
    """Weave YAML sections with filtered transcript sentences in sermon order."""
    ypath = job.yaml_path(pack.pack_dir)
    tpath = job.transcript_path(pack.pack_dir)
    deck = load_deck(ypath)
    sentences = filter_sentences(tpath.read_text(encoding="utf-8"))
    sections = deck.get("sections", [])
    n_sec = max(len(sections), 1)
    per_sec = max(3, len(sentences) // n_sec)

    verses_all = deck_verses(ypath)
    anchor = verses_all[0]
    anchor_body = b.apply_highlights(anchor["text"].strip().strip('"'), anchor["highlights"])
    anchor_ref = anchor["ref"] or "Scripture"

    parts = [
        b.h3(f"✝️ {job.title}"),
        b.quote(f'<em>"{anchor_body}"</em>' + (f" — <strong>{anchor_ref}</strong>" if anchor["ref"] else "")),
        b.highlight_key(),
        b.separator(),
    ]

    si = 0
    for idx, section in enumerate(sections, 1):
        sec_name = (section.get("section") or "").strip()
        parts.append(b.h2(_section_title(sec_name, idx)))
        chunk = sentences[si: si + per_sec]
        si += per_sec
        if chunk:
            parts.append(b.paragraph(" ".join(chunk[:3])))
        if len(chunk) > 3:
            parts.append(b.paragraph(" ".join(chunk[3:6])))
        for v in section.get("verses", []):
            ref = (v.get("reference") or "").strip()
            text = (v.get("text") or "").strip()
            if not text:
                continue
            lt = (v.get("leading_title") or "").strip()
            if lt:
                parts.append(b.paragraph(f"<strong>{lt}</strong>"))
            if not ref and not re.search(r"\d+:\d+", text) and "\n" in text:
                parts.append(b.quote(f"<em>{b.apply_highlights(text, v.get('highlights') or [])}</em>"))
                continue
            parts.append(b.verse_block(ref, text, v.get("highlights")))
        parts.append(b.separator())

    while si < len(sentences):
        parts.append(b.h2("📖 Further Teaching"))
        parts.append(b.paragraph(" ".join(sentences[si:si + 5])))
        si += 5
        parts.append(b.separator())

    parts.extend([
        b.h2("🎯 The Takeaway"),
        b.ordered_list(job.takeaway or ["💚 <strong>Stand in grace</strong> — righteousness is a gift in Christ."]),
        b.separator(),
        b.footer(job.topic),
    ])
    return "\n\n".join(parts)


def _build_first_adam(job: SermonJob, pack: SermonPack) -> str:
    y = job.yaml_path(pack.pack_dir)
    vmap = {v["ref"]: v for v in deck_verses(y) if v["ref"]}

    parts = [
        b.h3("👤 First Adam vs Last Adam: Your True Identity in Christ"),
        b.quote(
            f'<em>"The <mark style="background-color:#bbf7d0"><strong>eyes</strong></mark> of the Lord are on the righteous, '
            f'and his <mark style="background-color:#bbf7d0"><strong>ears</strong></mark> are attentive to their cry;"</em> '
            f"— <strong>Psalm 34:15 (NKJV)</strong>"
        ),
        b.highlight_key(), b.separator(),
        b.h2("👁️ God Sees, Hears, and Feels — For the Righteous"),
        b.table(["#", "What God does", "What it means for you"], [
            ("1️⃣", "<strong>Sees</strong> you", "Friends may not see your situation — God does"),
            ("2️⃣", "<strong>Hears</strong> your cry", "You can share anything with Him"),
            ("3️⃣", "<strong>Feels</strong> your pain", "Close to the <em>brokenhearted</em>"),
            ("4️⃣", "<strong>Delivers</strong> from <em>all</em> troubles", "Every lack — sickness, peacelessness, opposition"),
        ]),
        b.paragraph("Call unto Him with <strong>faith</strong>, not namesake prayer. The difference is <strong>confidence that you are righteous.</strong>"),
    ]
    for ref in ("Psalm 34:17 (NKJV)", "Psalm 34:18 (NKJV)", "Exodus 2:24 (NKJV)", "Proverbs 12:21 (NKJV)",
                "Psalm 103:3 (NKJV)", "Psalm 103:4 (NKJV)", "Psalm 103:5 (NKJV)", "Romans 5:19 (NKJV)",
                "Psalm 51:5 (NKJV)", "Genesis 5:1 (NKJV)", "Genesis 3:4–5 (NKJV)", "Romans 5:14 (NKJV)",
                "Romans 5:17 (NKJV)", "1 Corinthians 15:45 (NKJV)", "Ephesians 2:8–9 (NKJV)",
                "Genesis 2:15 (NKJV)", "John 20:15 (NKJV)", "John 3:3 (NKJV)", "Romans 2:4 (NKJV)"):
        if ref in vmap:
            parts.append(b.verse_block(ref, vmap[ref]["text"], vmap[ref]["highlights"]))
    parts += [
        b.separator(), b.h2("🎯 The Takeaway"),
        b.ordered_list(job.takeaway or []),
        b.separator(), b.footer(job.topic),
    ]
    return "\n\n".join(parts)


def _build_miracles(job: SermonJob, pack: SermonPack) -> str:
    y = job.yaml_path(pack.pack_dir)
    verses = deck_verses(y)
    anchor = next((v for v in verses if "Seek" in v["text"] or "1 Chronicles" in v["ref"]), verses[0])
    parts = [
        b.h3(f"⚡ {job.title}"),
        b.verse_block(anchor["ref"] or "1 Chronicles 16:11", anchor["text"], anchor["highlights"]),
        b.highlight_key(), b.separator(),
        b.h2("🙌 Miracles Are Easy — Seek His Face"),
        b.paragraph("Do not settle for the same level. God's power flows when you <strong>stand still</strong> and seek His face."),
        b.table(["World's way", "God's way"], [
            ("Prepare harder, upskill, strive", "<strong>Stand still</strong> — see the salvation of the Lord"),
            ("Fear the enemy's size", "The Lord will <strong>fight for you</strong>"),
            ("Earn the miracle by works", "Miracles are <strong>free</strong> — by grace through faith"),
        ]),
        b.separator(), b.h2("🏔️ Caleb: We Are Well Able"),
    ]
    for v in verses:
        if v["text"].strip():
            parts.append(b.verse_block(v["ref"] or "Scripture", v["text"], v["highlights"]))
    parts += [
        b.takeaway_section(job.takeaway or []),
        b.footer(job.topic),
    ]
    return "\n\n".join(parts)


def _build_holy_communion(job: SermonJob, pack: SermonPack) -> str:
    y = job.yaml_path(pack.pack_dir)
    verses = deck_verses(y)
    parts = [
        b.h3("🍷 Holy Communion: The One Reason for Sickness and Four Remedies"),
        b.verse_block("1 Corinthians 11:30 (NKJV)", verses[0]["text"], verses[0]["highlights"]),
        b.highlight_key(), b.separator(),
        b.h2("⚠️ One Reason — Not Many"),
        b.paragraph("Scripture says <strong>one reason</strong> many are weak, sick, and sleep before their time."),
        b.table(["Remedy #", "Purpose", "What you remember"], [
            ("1️⃣", "<strong>Remember it is free</strong>", "Prevent falling — God gives freely"),
            ("2️⃣", "<strong>Open your eyes</strong>", "See provision near you — like Hagar's well"),
            ("3️⃣", "<strong>Redeem from bondage</strong>", "Passover lamb — blood and body"),
            ("4️⃣", "<strong>The one reason</strong>", "Not discerning the Lord's body"),
        ]),
    ]
    for v in verses[1:]:
        parts.append(b.verse_block(v["ref"] or "Scripture", v["text"], v["highlights"]))
    parts += [b.takeaway_section(job.takeaway or []), b.footer(job.topic)]
    return "\n\n".join(parts)


def _build_heir(job: SermonJob, pack: SermonPack) -> str:
    y = job.yaml_path(pack.pack_dir)
    verses = deck_verses(y)
    heir_text = next(v["text"] for v in verses if "heir of the world" in v["text"].lower())
    parts = [
        b.h3("👑 Heir of the World: How Faith—not Law—Makes You an Inheritor"),
        b.verse_block("Romans 4:13 (NKJV)", heir_text, ["heir of the world", "not", "through the law"]),
        b.highlight_key(), b.separator(),
        b.h2("🌍 Zero Troubles — Heir of the World"),
        b.table(["Law path", "Faith path"], [
            ("Blessed because you obey", "Blessed because Christ obeyed"),
            ("Heir through works", "<strong>Heir of the world</strong> through faith"),
            ("Mix Moses, Elijah, and Jesus", "Father's voice: <strong>Hear Him</strong>"),
        ]),
    ]
    for v in verses:
        if v["text"].strip():
            parts.append(b.verse_block(v["ref"] or "Scripture", v["text"], v["highlights"]))
    parts += [b.takeaway_section(job.takeaway or []), b.footer(job.topic)]
    return "\n\n".join(parts)


def _build_full_restoration(job: SermonJob, pack: SermonPack) -> str:
    y = job.yaml_path(pack.pack_dir)
    verses = deck_verses(y)
    parts = [
        b.h3("💯 Full Restoration: 100% Healing and Provision in Christ"),
        b.highlight_key(), b.separator(),
        b.h2("🔄 100% Restoration — Not 50% or 80%"),
        b.table(["Stage", "What God restores"], [
            ("1️⃣ <strong>Saved</strong>", "Rescued, preserved — John 10:9"),
            ("2️⃣ <strong>Life</strong> (<em>zōē</em>)", "Abundant life — zero sickness, pain, sorrow"),
            ("3️⃣ <strong>Full</strong>", "More than Adam lost — exceedingly abundantly"),
        ]),
        b.paragraph("Adam lost <em>zōē</em> at the fall. Ezekiel 37 — dry bones live when breath enters."),
    ]
    for v in verses:
        if v["text"].strip():
            parts.append(b.verse_block(v["ref"] or "Scripture", v["text"], v["highlights"]))
    parts += [b.takeaway_section(job.takeaway or []), b.footer(job.topic)]
    return "\n\n".join(parts)


NAMED_BUILDERS: dict[str, Callable[[SermonJob, SermonPack], str]] = {
    "first_adam": _build_first_adam,
    "miracles": _build_miracles,
    "miracles_next": _build_miracles,
    "holy_communion": _build_holy_communion,
    "heir": _build_heir,
    "full_restoration": _build_full_restoration,
}


def build_article(job: SermonJob, pack: SermonPack) -> str:
    if job.builder == "existing_html" and job.existing_html:
        src = Path(job.existing_html).expanduser()
        if src.exists():
            html = src.read_text(encoding="utf-8")
            return re.sub(
                r"🎧 Based on a Sunday message[^<]*",
                f"🎧 Scripture-based study on {job.topic}. "
                "If it strengthened you, share it with someone who needs this truth today. 💛",
                html,
            )

    if job.builder == "named" and job.builder_name in NAMED_BUILDERS:
        html = NAMED_BUILDERS[job.builder_name](job, pack)
        from .transcript import word_count
        tpath = job.transcript_path(pack.pack_dir)
        tw = word_count(tpath.read_text(encoding="utf-8"))
        hw = word_count(re.sub(r"<[^>]+>", " ", html))
        if hw / max(tw, 1) >= 0.55 and html.count("wp-block-table") > 0:
            return html
        return build_faithful(job, pack)

    return build_faithful(job, pack)


def _enrich_with_transcript(html: str, job: SermonJob, pack: SermonPack) -> str:
    from .transcript import word_count

    tpath = job.transcript_path(pack.pack_dir)
    tw = word_count(tpath.read_text(encoding="utf-8"))
    hw = word_count(re.sub(r"<[^>]+>", " ", html))
    if hw / max(tw, 1) >= 0.55:
        return html

    sentences = filter_sentences(tpath.read_text(encoding="utf-8"))
    extra_blocks = [b.paragraph(" ".join(sentences[i:i + 4])) for i in range(0, min(len(sentences), 20), 4)]
    injection = "\n\n".join(extra_blocks[:6])
    marker = "<!-- wp:separator -->"
    first = html.find(marker)
    if first > 0:
        html = html[:first] + injection + "\n\n" + html[first:]
    return html
