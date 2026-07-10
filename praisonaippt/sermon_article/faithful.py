"""Transcript-faithful article builder — structured rewrites, not raw paste."""
from __future__ import annotations

import re
from pathlib import Path

from . import blocks as b
from .deck import deck_verses, load_deck
from .digest import digest_section
from .protocol import SermonJob, SermonPack
from .transcript import filter_sentences, word_count
from .transcript_flow import FLOW_BY_SLUG, build_transcript_flow

# Per-slug section plans: (emoji title, keyword needles for transcript sentences)
SECTION_PLANS: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "gospel-of-christ-hear-right-covenant": [
        ("✝️ Hear the Gospel of Christ — Faith Comes by Hearing", ("gospel", "hear", "faith", "word of christ", "romans 10")),
        ("🍞 Eating Is Fighting — Lechem and Lacham", ("eating", "fighting", "lechem", "lacham", "bread", "living bread")),
        ("📜 First Covenant Had Fault — New Covenant Syllabus", ("first covenant", "fault", "new covenant", "second covenant", "faultless")),
        ("☠️ Law Written on Stones — Ministry of Death", ("law", "stones", "letter kills", "ministry of death")),
        ("💪 Gospel = Power — Teaching, Preaching, and Healing", ("power", "teaching", "preaching", "healing", "gospel of god")),
        ("🎁 Hundredfold Now — Mark 10:30", ("hundred", "hundredfold", "mark 10", "now", "receive")),
        ("💧 2 Kings 3:17 — Valley Filled Without Rain", ("2 kings", "valley", "water", "rain", "wind")),
        ("👑 Noble Like Bereans — Search the Scriptures", ("berean", "noble", "search", "scripture", "daily")),
        ("📖 Right Covenant — Hear Him, Not Moses Alone", ("covenant", "hear him", "right covenant", "syllabus")),
    ],
    "freedom-in-the-spirit-son-and-father": [
        ("🕊️ In His Presence — Deliverance and Miracles", ("presence", "deliverance", "miracle", "solution", "light")),
        ("🌳 Tree of Life vs Tree of Knowledge", ("tree of life", "tree of knowledge", "good and evil", "choose")),
        ("👂 Four Benefits of Hearing the Word", ("four", "hear", "victorious", "noble", "grace", "healing")),
        ("✝️ Christ Has Set Us Free — Do Not Return", ("set us free", "slavery", "galatians", "free", "yoke")),
        ("🕊️ Freedom Through the Spirit", ("spirit", "holy spirit", "freedom through the spirit")),
        ("👶 Freedom Through the Son", ("son", "jesus", "freedom through the son", "christ")),
        ("👨 Freedom Through the Father", ("father", "freedom through the father", "beloved son")),
        ("🔊 Hear About Jesus ONLY — Not Law Mixed In", ("hear about jesus", "only", "mix", "law", "gospel")),
        ("🍞 Eat Freely — Gift of God, Not Reward System", ("eat freely", "gift", "reward", "wages", "tree of life")),
    ],
    "first-adam-vs-last-adam-identity-in-christ": [
        ("👁️ God Sees, Hears, and Feels the Righteous", ("righteous", "eyes", "ears", "cry", "brokenhearted")),
        ("🛡️ Zero Harm and Healing for the Righteous", ("no harm", "heals", "diseases", "troubles", "deliver")),
        ("🍎 First Adam — Many Made Sinners", ("first adam", "disobedience", "sinners", "sinful at birth", "genesis 3")),
        ("✝️ Last Adam — Gift Righteousness in Christ", ("last adam", "obedience", "made righteous", "ephesians 2", "gift")),
        ("👤 Your True Identity — Whose You Are", ("identity", "born again", "john 3", "romans 5", "reign")),
        ("💚 Goodness of God Leads to Repentance", ("goodness", "repentance", "romans 2", "kindness")),
        ("📖 Psalm 103 — Forgiveness, Healing, Renewal", ("psalm 103", "iniquities", "youth", "eagle")),
        ("🌿 Garden Calling — Dress and Keep", ("garden", "genesis 2", "dress", "keep", "work")),
        ("🎯 From Sinner to Righteous by One Man", ("one man", "many", "righteousness", "christ")),
    ],
    "miracles-are-easy-stand-still": [
        ("🔍 Seek the Lord and His Strength", ("seek", "face", "chronicles", "strength")),
        ("🏔️ Caleb — We Are Well Able", ("caleb", "well able", "giants", "anakim")),
        ("🛑 Stand Still — See the Salvation of the Lord", ("stand still", "fight for you", "exodus 14", "red sea")),
        ("🙏 Humble Faith — The Tax Collector", ("tax collector", "pharisee", "justified", "humble")),
        ("🎁 Miracles Are Free — Not Wages", ("free", "gift", "wages", "grace", "earn")),
        ("📖 Faith Comes by Hearing", ("hearing", "faith", "word", "paul")),
        ("✨ Go to the Next Level", ("next level", "same situation", "remain")),
        ("🕊️ In His Presence — Miracles Flow", ("presence", "deliverance", "miracle")),
        ("💪 Believe It Is Easy", ("easy", "believe", "well able")),
    ],
    "miracles-are-easy-next-level-faith": [
        ("🚀 Go to the Next Level Today", ("next level", "same situation", "remain", "stuck")),
        ("🔍 Seek His Face Evermore", ("seek", "face", "chronicles", "evermore")),
        ("🛑 Stand Still — The Lord Fights for You", ("stand still", "fight", "salvation")),
        ("🏔️ Caleb's Confession of Faith", ("caleb", "well able", "giants")),
        ("🙏 Humble Yourself — Justified by Grace", ("humble", "tax collector", "justified")),
        ("🎁 Miracles Are Free Gifts", ("free", "gift", "wages", "grace")),
        ("📢 Do Not Settle for the Same Level", ("level", "upgrade", "higher")),
        ("✝️ Hearing With Faith Brings Power", ("hearing", "faith", "spirit")),
        ("🌟 Miracles Are Easy for the Righteous", ("easy", "righteous", "believe")),
    ],
    "freedom-from-troubles-righteousness-apart-from-works": [
        ("🌅 New Grace Every Morning", ("grace", "morning", "new month", "new beginning")),
        ("🐑 The Lord Is My Shepherd — Zero Lack", ("shepherd", "lack", "psalm 23", "green pasture")),
        ("👴 Abraham — Against All Hope He Believed", ("abraham", "isaac", "ninety", "stars", "romans 4")),
        ("📖 Righteousness Apart From the Law", ("apart from the law", "romans 3", "righteousness of god")),
        ("⛓️ Separated From Christ", ("separated from christ", "galatians 5", "justified by law")),
        ("📉 Fallen From Grace", ("fallen from grace", "grace", "law")),
        ("☠️ Ministry of Death on Stones", ("ministry of death", "letter kills", "stones", "law")),
        ("👂 Hear Him — Not Moses and Elijah", ("hear him", "matthew 17", "beloved son")),
        ("🕊️ Holy Spirit Falls While Peter Speaks", ("holy spirit", "peter", "still speaking", "acts 10")),
        ("⚖️ Law Path vs Faith Path", ("law", "faith", "curse", "blessed")),
        ("📜 What Is Written in Your Hearts?", ("hearts", "written", "spirit", "letter")),
        ("🎯 Zero Troubles Through the Gospel", ("troubles", "deliver", "righteous", "all")),
    ],
    "full-restoration-hundred-percent-in-christ": [
        ("💯 100% Restoration — Not 50%, Not 80%", ("100", "full", "restoration", "partial", "fifty", "desire")),
        ("📋 Three Steps: Saved → Life → Full Restoration", ("saved", "life", "three", "step", "full")),
        ("🌸 Don't Worry — God Cares for Birds and Flowers", ("worry", "birds", "flowers", "youth", "protect")),
        ("🚪 John 10:9–10 — The Gate and Abundant Life", ("john 10", "gate", "abundant", "life", "full")),
        ("🌱 Three Levels of Life — Plant, Animal, and Zōē", ("zoe", "bios", "psyche", "plant", "animal", "life")),
        ("🌬️ Pentecost — God's Breath Restored in You", ("pentecost", "breath", "wind", "spirit", "adam")),
        ("🦴 Ezekiel 37 — Dry Bones Live Again", ("ezekiel", "dry bones", "live", "lord")),
        ("👑 Daughters of Sarah — Desire the Blessing", ("sarah", "ruth", "daughters", "desire", "blessing")),
        ("🌳 Tree of Life — What Adam Lost and Christ Restores", ("tree of life", "adam", "fruit", "jesus", "desires")),
    ],
    "be-fruitful-and-multiply-every-area": [
        ("🌳 Shalom — Completeness in Every Area", ("shalom", "complete", "every area", "fruitful")),
        ("🌬️ Zōē Restored — Adam's Breath-Life", ("zoe", "breath", "adam", "pentecost")),
        ("🩸 Touch Jesus by Faith", ("touch", "issue of blood", "woman", "hem")),
        ("📈 Fruitful in Health, Riches, and Calling", ("fruitful", "multiply", "health", "riches")),
        ("🆕 Former Things Passed Away", ("former", "passed", "old", "sorrow", "pain")),
        ("🌾 Sowing and Reaping in Christ", ("sow", "reap", "seed", "harvest")),
        ("👑 Dominion and Blessing", ("dominion", "bless", "multiply", "genesis")),
        ("💚 God's Blessing in Every Area", ("area", "blessing", "life", "family")),
        ("✝️ In Christ — Complete Restoration", ("christ", "complete", "full", "restore")),
    ],
    "why-delay-abraham-instant-blessing": [
        ("⏱️ Why Delay? — Instant Blessing Through Faith", ("delay", "instant", "quickly", "wait")),
        ("👴 At Ninety-Nine — El Shaddai Appears", ("ninety", "abraham", "abram", "el shaddai")),
        ("⚖️ Righteousness Apart From Works", ("apart from", "works", "romans 4", "believed")),
        ("💯 100% His Power — Not 50/50 Mix", ("100", "fifty", "mix", "effort", "power")),
        ("📉 Fallen From Grace — Mixing Law and Gospel", ("fallen", "grace", "law", "mix")),
        ("🌟 Abraham Called Things That Are Not", ("called", "father", "sarah", "princess")),
        ("📖 Romans 4 — Fully Convinced God Performs", ("convinced", "romans 4", "perform", "promise")),
        ("🎁 Blessing Comes by Hearing Christ", ("hearing", "christ", "faith", "gospel")),
        ("✨ No More Delay at 99", ("99", "ninety-nine", "instant", "now")),
    ],
    "why-listen-to-the-word-of-god": [
        ("💧 2 Kings 3:17 — Valley Filled Without Rain", ("2 kings", "valley", "water", "rain")),
        ("🏆 To Be Victorious — Hear and Overcome", ("victorious", "overcome", "victory")),
        ("👑 To Become Noble Like the Bereans", ("berean", "noble", "search", "scripture")),
        ("📈 Grace Multiplied — 2 Peter 1:2", ("grace", "multiplied", "peter", "knowledge")),
        ("🩺 Healing by Hearing — Lystra Cripple", ("healing", "lystra", "crippled", "leaped", "paul")),
        ("🍞 Eating Is Fighting — Lechem and Lacham", ("eating", "fighting", "lechem", "bread")),
        ("📢 Israelites — Heard Once, Stalled 40 Years", ("israel", "40", "wilderness", "heard")),
        ("👂 What to Hear — Christ, Not the Law", ("what to hear", "christ", "law", "covenant")),
        ("✝️ Four Blessings of Hearing Summarised", ("four", "blessing", "hear", "listen")),
    ],
    "heir-of-the-world-through-faith-not-law": [
        ("👑 Heir of the World — Romans 4:13", ("heir", "world", "romans 4")),
        ("🔊 Hear Him — Matthew 17:5", ("hear him", "beloved son", "matthew 17")),
        ("⚖️ Justified Apart From Works", ("justified", "works", "galatians 2")),
        ("☠️ Under the Curse of the Law", ("curse", "law", "works")),
        ("⛓️ Separated From Christ by Law", ("separated", "christ", "galatians 5")),
        ("📉 Fallen From Grace", ("fallen", "grace")),
        ("🕊️ Sons Are Free — Heirs Walk in Exaltation", ("sons", "free", "heir", "exaltation")),
        ("🌍 Zero Troubles as an Heir", ("troubles", "zero", "inherit")),
        ("✝️ Faith Not Law Makes You an Inheritor", ("faith", "law", "inherit", "promise")),
    ],
    "holy-communion-one-reason-for-sickness": [
        ("☝️ One Reason — Not Discerning the Lord's Body", ("one reason", "discerning", "body", "1 corinthians 11")),
        ("🎁 Remember It Is Free", ("free", "falling", "adam", "gift")),
        ("👁️ Open Your Eyes — Provision Is Near", ("open", "eyes", "hagar", "well")),
        ("⛓️ Redeemed From Bondage — Passover Lamb", ("bondage", "passover", "lamb", "blood")),
        ("🌳 Eat the Tree of Life", ("tree of life", "adam", "curse")),
        ("🍷 Four Remedies Through Communion", ("communion", "remedy", "remember")),
        ("💊 Weak, Sick, and Sleep Before Time", ("weak", "sick", "sleep")),
        ("✝️ Discern Christ's Body by Faith", ("discern", "christ", "body")),
        ("🛡️ Prevent Sickness Through Right Hearing", ("prevent", "sickness", "hear")),
    ],
}

TABLE_SPECS: dict[str, tuple[list[str], list[tuple]]] = {
    "gospel-of-christ-hear-right-covenant": (
        ["Old covenant", "Gospel of Christ"],
        [
            ("Law on stones — letter kills", "<strong>Hear the word of Christ</strong> — faith comes"),
            ("First covenant had <strong>fault</strong>", "New covenant — <strong>right syllabus</strong>"),
            ("Works and wages", "Gospel = <strong>power</strong> — teaching, preaching, healing"),
        ],
    ),
    "freedom-in-the-spirit-son-and-father": (
        ["Tree of Knowledge", "Tree of Life"],
        [
            ("Mix law and gospel", "<strong>Spirit, Son, Father</strong> — freedom"),
            ("Earn by reward system", "<strong>Eat freely</strong> — gift of God"),
            ("Hear Moses + Elijah + Jesus", "Father's voice: <strong>Hear Him</strong>"),
        ],
    ),
    "first-adam-vs-last-adam-identity-in-christ": (
        ["First Adam", "Last Adam"],
        [
            ("Disobedience → <strong>many sinners</strong>", "Obedience → <strong>many righteous</strong>"),
            ("Sin, death, and curse", "Gift righteousness in Christ"),
            ("Identity in the flesh", "Identity in the Last Adam"),
        ],
    ),
    "miracles-are-easy-stand-still": (
        ["World's way", "God's way"],
        [
            ("Prepare harder and strive", "<strong>Stand still</strong> — see salvation"),
            ("Fear the enemy's size", "The Lord <strong>fights for you</strong>"),
            ("Earn miracles by works", "Miracles are <strong>free</strong> by grace"),
        ],
    ),
    "miracles-are-easy-next-level-faith": (
        ["Staying put", "Next level"],
        [
            ("Same situation year after year", "<strong>Go higher</strong> by faith"),
            ("Self-effort and striving", "<strong>Stand still</strong> and seek His face"),
            ("Earned breakthrough", "<strong>Free</strong> miracles by grace"),
        ],
    ),
    "freedom-from-troubles-righteousness-apart-from-works": (
        ["Law path", "Faith path"],
        [
            ("Blessed because you obey", "Blessed because <strong>Christ obeyed</strong>"),
            ("Ministry of death on stones", "Gospel of <strong>righteousness apart from law</strong>"),
            ("Separated from Christ", "<strong>Hear Him</strong> — Spirit falls"),
        ],
    ),
    "full-restoration-hundred-percent-in-christ": (
        ["Partial mindset", "Full restoration"],
        [
            ("50% or 80% healing", "<strong>100%</strong> — zero sickness, pain, sorrow"),
            ("Adam lost <em>zōē</em>", "Pentecost <strong>restores breath-life</strong>"),
            ("Dry bones hopeless", "Ezekiel 37 — <strong>live again</strong>"),
        ],
    ),
    "be-fruitful-and-multiply-every-area": (
        ["Old creation", "In Christ"],
        [
            ("Former sorrow and pain", "<strong>Former things passed away</strong>"),
            ("Partial blessing", "<strong>Shalom</strong> in every area"),
            ("Touch by law-works", "<strong>Touch Jesus</strong> by faith"),
        ],
    ),
    "why-delay-abraham-instant-blessing": (
        ["Delay mindset", "Instant blessing"],
        [
            ("50/50 mix of effort and grace", "<strong>100% His power</strong> through faith"),
            ("Waiting on your performance", "<strong>El Shaddai</strong> at ninety-nine"),
            ("Law-justification", "<strong>Righteousness apart from works</strong>"),
        ],
    ),
    "why-listen-to-the-word-of-god": (
        ["Hear once", "Keep hearing"],
        [
            ("Israel stalled 40 years", "Abraham rehearsed the gospel"),
            ("Worldly addition — slow", "<strong>Multiplication</strong> of grace"),
            ("Random messages", "<strong>Word of Christ</strong> with faith"),
        ],
    ),
    "heir-of-the-world-through-faith-not-law": (
        ["Law path", "Faith path"],
        [
            ("Heir through works", "<strong>Heir of the world</strong> through faith"),
            ("Under the curse", "<strong>Justified apart from works</strong>"),
            ("Mix Moses, Elijah, and Jesus", "Father's voice: <strong>Hear Him</strong>"),
        ],
    ),
    "holy-communion-one-reason-for-sickness": (
        ["Remedy", "What you remember"],
        [
            ("1️⃣ <strong>It is free</strong>", "Prevent falling like Adam"),
            ("2️⃣ <strong>Open your eyes</strong>", "See provision near — Hagar's well"),
            ("3️⃣ <strong>Redeemed from bondage</strong>", "Passover lamb — blood and body"),
            ("4️⃣ <strong>One reason</strong>", "Not discerning the Lord's body"),
        ],
    ),
}

# Curated interactive digest — short intro + lists/tables, never raw transcript paste.
DIGEST_OVERRIDES: dict[str, dict[str, dict]] = {
    "full-restoration-hundred-percent-in-christ": {
        "💯 100% Restoration — Not 50%, Not 80%": {
            "intro": (
                "God's aim is <strong>full restoration</strong> — not partial healing, "
                "not 80% peace. <em>Only when you desire 100% restoration</em> can it come to you."
            ),
            "bullets": [
                "📖 <strong>Know</strong> from Scripture that <strong>100% restoration is possible</strong>",
                "💛 <strong>Desire</strong> full restoration — don't settle for partial",
                "🙏 <strong>Trust</strong> Him to restore you completely — friendship, family, every lack",
            ],
            "table": (
                ["Level", "What it means", "Full?"],
                [
                    ("50–80%", "Partial relief", "❌ Not full"),
                    ("90%", "Almost there — one sickness left", "❌ Still not full"),
                    ("100%", "Zero sickness · complete shalom", "✅ Full restoration"),
                ],
            ),
        },
        "📋 Three Steps: Saved → Life → Full Restoration": {
            "intro": "Pastor teaches a clear <strong>three-step path</strong> — saved, then life, then full restoration.",
            "ordered": [
                "<strong>Saved</strong> — Christ rescues you first",
                "<strong>Life</strong> — <em>zōē</em> (God's own life) enters you",
                "<strong>Full restoration</strong> — 100% peace, zero sickness, complete wholeness",
            ],
        },
        "🌸 Don't Worry — God Cares for Birds and Flowers": {
            "intro": (
                "When worry rises, remember: <em>God feeds the birds and clothes the flowers</em> — "
                "He protects, heals, saves, and rescues you in your youth and now."
            ),
            "bullets": [
                "🌸 Youth memories — God was protecting you even then",
                "🕊️ If He cares for birds, He cares for <strong>you</strong> far more",
                "💚 Don't let worry block the <strong>blessing chasing you</strong>",
            ],
        },
        "🚪 John 10:9–10 — The Gate and Abundant Life": {
            "intro": (
                "Jesus is the <strong>gate</strong> toward restoration — "
                "<em>I have come that they may have life, and have it to the full.</em>"
            ),
            "bullets": [
                "🚪 <strong>I am the gate</strong> — Jesus is the only way in",
                "💾 <strong>Saved (sōzó)</strong> — heal · preserve · rescue · deliver",
                "🐺 Thief steals, kills, destroys — Christ gives <strong>abundant life</strong>",
                "💯 <strong>Have it to the full</strong> — 100%, not one sickness left",
            ],
            "table": (
                ["Jesus says", "What you receive"],
                [
                    ("I am the gate", "Entry into restoration"),
                    ("Life (<em>zōē</em>)", "God's own breath inside you"),
                    ("Have it to the full", "100% — not one sickness remaining"),
                ],
            ),
        },
        "🌱 Three Levels of Life — Plant, Animal, and Zōē": {
            "intro": "Not all 'life' in Scripture is the same. Pastor contrasts <strong>three levels</strong>:",
            "bullets": [
                "🌿 <strong>Bios</strong> — lowest form: plants, grass, flowers",
                "🐾 <strong>Psyche</strong> — animal/soul life, mere creature breath",
                "✨ <strong>Zōē</strong> — God's own life: <em>zero sickness, zero pain, zero sorrow</em>",
            ],
            "table": (
                ["Greek", "Level", "Example"],
                [
                    ("Bios", "Plant life", "Grass, flowers"),
                    ("Psyche", "Animal / soul life", "Breath of creatures"),
                    ("<strong>Zōē</strong>", "God's own life", "What Adam had · what Jesus restores"),
                ],
            ),
        },
        "🌬️ Pentecost — God's Breath Restored in You": {
            "intro": (
                "At Pentecost the <strong>Holy Spirit</strong> brought God's breath back — "
                "the same <em>zōē</em> Adam knew. <strong>Believe His breath is in you</strong> "
                "and you can believe for full restoration."
            ),
            "bullets": [
                "🌬️ God's breath (<em>zōē</em>) — not mere human life",
                "✅ Same life Adam had — <strong>complete restoration</strong> is the goal",
                "🎯 Zero sickness = fullness; even one sickness is <em>not</em> fullness",
            ],
            "verse_refs": ["Acts 2:1-4", "Genesis 2:7", "Revelation 21:4"],
        },
        "🦴 Ezekiel 37 — Dry Bones Live Again": {
            "intro": (
                "Dry bones rising pictures <strong>full restoration</strong> — "
                "then you will know that <em>I am the Lord</em>."
            ),
            "bullets": [
                "💀 Dry bones → living army — God does not stop halfway",
                "📖 He reads Scripture over you so you know He is the Lord",
                "🌳 The fruit is nothing other than <strong>Jesus</strong>",
            ],
            "verse_refs": ["Proverbs 22:3", "Psalm 71:15"],
        },
        "👑 Daughters of Sarah — Desire the Blessing": {
            "intro": "The Bible calls women <strong>daughters of Sarah</strong> — not daughters of Ruth. <em>Desire the blessing.</em>",
            "bullets": [
                "👑 Sarah's line — heir mindset, not striving like Ruth",
                "💛 One man's disobedience made many sinners — grace reverses the curse",
                "🎁 God will <strong>fulfil the desires of your heart</strong> when you desire His fullness",
            ],
            "verse_refs": ["Deuteronomy 28:1", "Deuteronomy 28:15", "Psalm 109:17"],
        },
        "🌳 Tree of Life — What Adam Lost and Christ Restores": {
            "intro": (
                "Eden had <strong>two trees</strong>. Adam lost the tree of life — "
                "but in Christ, <em>that fruit is nothing other than Jesus</em>."
            ),
            "bullets": [
                "🌳 <strong>Tree of knowledge</strong> vs <strong>tree of life</strong> — Adam could not eat life after the fall",
                "✝️ <strong>In Christ</strong> we eat the fruit of life again — the fruit is Jesus",
                "🩸 <strong>Woman bleeding 12 years</strong> — healed instantly through faith",
                "⚖️ By <strong>one Man's obedience</strong> — many made righteous",
                "👑 <strong>Sons of Abraham</strong> — heirs who receive full restoration",
            ],
            "table": (
                ["What Christ took", "What you receive"],
                [
                    ("All your sickness", "<strong>100% healing</strong>"),
                    ("All pain and sorrow", "Complete <strong>shalom</strong>"),
                    ("Adam's lost tree of life", "<strong>Full restoration</strong> in Christ"),
                ],
            ),
        },
    },
}


def _britishise(text: str) -> str:
    repl = {
        "honor": "honour", "Honor": "Honour", "recognized": "recognised",
        "behavior": "behaviour", "center": "centre", "favor": "favour",
    }
    for a, z in repl.items():
        text = text.replace(a, z)
    return re.sub(r"\s+", " ", text).strip()


def _score_sentence(s: str, needles: tuple[str, ...]) -> int:
    low = s.lower()
    return sum(1 for n in needles if n in low)


def _assign_sentences(sentences: list[str], plan: list[tuple[str, tuple[str, ...]]]) -> dict[str, list[str]]:
    buckets = {title: [] for title, _ in plan}
    unassigned: list[str] = []
    for s in sentences:
        best_title, best_score = "", 0
        for title, needles in plan:
            sc = _score_sentence(s, needles)
            if sc > best_score:
                best_score, best_title = sc, title
        if best_score:
            buckets[best_title].append(s)
        else:
            unassigned.append(s)
    # Distribute unassigned round-robin
    keys = list(buckets.keys())
    for i, s in enumerate(unassigned):
        buckets[keys[i % len(keys)]].append(s)
    return buckets


def _section_emoji_title(raw: str) -> str:
    if raw[0] in "📖🌿✝️⚡🎯👁️🛡️🍎💯🌬️🦴👑⏱️👴💧🏆🍞☝️🎁🔍🛑🙏🚀":
        return raw
    return raw


def _is_real_verse(v: dict) -> bool:
    ref = (v.get("ref") or "").strip()
    text = (v.get("text") or "").strip()
    if not text:
        return False
    if re.search(r"\d+:\d+", ref):
        return True
    return len(text) > 120


def _verses_for_section(section_name: str, verses: list[dict], used: set[int]) -> list[dict]:
    out: list[dict] = []
    sec_low = section_name.lower()
    for i, v in enumerate(verses):
        if i in used or not _is_real_verse(v):
            continue
        ref = (v.get("ref") or "").lower()
        text = (v.get("text") or "").lower()
        yaml_sec = (v.get("section") or "").lower()
        if yaml_sec and yaml_sec in sec_low:
            out.append(v)
            used.add(i)
        elif any(tok in sec_low for tok in ref.split()[:2] if tok):
            out.append(v)
            used.add(i)
        elif any(word in text[:40] for word in ("heir", "stand still", "discerning") if word in sec_low):
            out.append(v)
            used.add(i)
    return out


def build_faithful(job: SermonJob, pack: SermonPack) -> str:
    """Build a structured transcript-faithful article for pack-2 sermons."""
    if job.slug in FLOW_BY_SLUG:
        return build_transcript_flow(job, pack, FLOW_BY_SLUG[job.slug])

    ypath = job.yaml_path(pack.pack_dir)
    tpath = job.transcript_path(pack.pack_dir)
    deck = load_deck(ypath)
    verses = deck_verses(ypath)
    sentences = filter_sentences(tpath.read_text(encoding="utf-8"))

    plan = SECTION_PLANS.get(job.slug)
    if not plan:
        # Derive from YAML section names
        plan = []
        for sec in deck.get("sections", []):
            name = (sec.get("section") or "").strip()
            if name and "teaching block" not in name.lower():
                needles = tuple(w.lower() for w in re.findall(r"[A-Za-z]{4,}", name))
                plan.append((_section_emoji_title(f"📖 {name}"), needles or (name.lower(),)))
        if len(plan) < MIN_SECTIONS:
            chunk = max(1, len(sentences) // MIN_SECTIONS)
            plan = [
                (f"📖 Teaching Part {i + 1}", ())
                for i in range(MIN_SECTIONS)
            ]

    anchor = verses[0] if verses else {"ref": "", "text": job.title, "highlights": []}
    anchor_body = b.apply_highlights(anchor["text"].strip().strip('"'), anchor["highlights"])
    anchor_ref = anchor["ref"] or ""

    emoji = {"first_adam": "👤", "miracles": "⚡", "miracles_next": "⚡", "holy_communion": "🍷",
             "heir": "👑", "full_restoration": "💯"}.get(job.builder_name, "✝️")
    parts = [
        b.h3(f"{emoji} {job.title}"),
        b.quote(
            f'<em>"{anchor_body}"</em>'
            + (f" — <strong>{anchor_ref}</strong>" if anchor_ref else "")
        ),
        b.highlight_key(),
        b.separator(),
    ]

    buckets = _assign_sentences(sentences, plan)
    used_verse_idx: set[int] = set()
    seen_refs: set[str] = set()

    for idx, (title, _) in enumerate(plan):
        parts.append(b.h2(title))
        sents = [_britishise(s) for s in buckets.get(title, [])]
        override = DIGEST_OVERRIDES.get(job.slug, {}).get(title, {})
        curated = bool(override)
        if override.get("intro"):
            parts.append(b.paragraph(override["intro"]))
        elif sents and not curated:
            intro, _ = digest_section(sents)
            if intro:
                parts.append(b.paragraph(intro))
        if override.get("ordered"):
            parts.append(b.ordered_list(override["ordered"]))
        elif override.get("bullets"):
            parts.append(b.bullet_list(override["bullets"]))
        elif sents and not curated:
            _, bullets = digest_section(sents)
            if bullets:
                parts.append(b.bullet_list(bullets))
        if override.get("table"):
            hdrs, rows = override["table"]
            parts.append(b.table(hdrs, rows))
        elif idx == 1 and job.slug in TABLE_SPECS and not override.get("table"):
            hdrs, rows = TABLE_SPECS[job.slug]
            parts.append(b.table(hdrs, rows))
        # Attach YAML verses — dedupe by ref, honour override verse_refs
        sec_verses = _verses_for_section(title, verses, used_verse_idx)
        for wanted in override.get("verse_refs", []):
            for i, v in enumerate(verses):
                if i in used_verse_idx or not _is_real_verse(v):
                    continue
                if wanted.lower() in (v.get("ref") or "").lower():
                    sec_verses.append(v)
                    used_verse_idx.add(i)
                    break
        if not sec_verses and idx < len(verses):
            per = max(1, len(verses) // len(plan))
            start = idx * per
            for i, v in enumerate(verses[start:start + per]):
                if i + start not in used_verse_idx:
                    sec_verses.append(v)
                    used_verse_idx.add(i + start)
        added = 0
        for v in sec_verses:
            if not _is_real_verse(v):
                continue
            ref_key = re.sub(r"\s+", " ", (v.get("ref") or "").lower().strip())
            if ref_key and ref_key in seen_refs:
                continue
            if ref_key:
                seen_refs.add(ref_key)
            parts.append(b.verse_block(v["ref"], v["text"], v["highlights"]))
            added += 1
            if added >= 4:
                break
        parts.append(b.separator())

    # Any remaining verses (deduped)
    for i, v in enumerate(verses):
        if i in used_verse_idx or not v["text"].strip() or not _is_real_verse(v):
            continue
        ref_key = re.sub(r"\s+", " ", (v.get("ref") or "").lower().strip())
        if ref_key and ref_key in seen_refs:
            continue
        if ref_key:
            seen_refs.add(ref_key)
        parts.insert(-2, b.verse_block(v["ref"], v["text"], v["highlights"]))

    parts.extend([
        b.h2("🎯 The Takeaway"),
        b.ordered_list(job.takeaway or ["💚 <strong>Stand in grace</strong> — righteousness is a gift in Christ."]),
        b.separator(),
        b.footer(job.topic),
    ])
    return "\n\n".join(parts)


MIN_SECTIONS = 8
