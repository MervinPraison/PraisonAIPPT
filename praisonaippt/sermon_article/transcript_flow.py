"""Transcript-ordered article flows — full coverage in digest format."""
from __future__ import annotations

import re
from typing import Any

from . import blocks as b
from .deck import deck_verses, load_deck
from .protocol import SermonJob, SermonPack

# Each section: title, intro, bullets?, ordered?, table?, verse_refs?, quote?
FULL_RESTORATION_FLOW: list[dict[str, Any]] = [
    {
        "title": "💯 God's Aim — 100% Full Restoration",
        "intro": (
            "God is going to <strong>fully restore you</strong> — not 50%, not 80%, not 90%, "
            "but <mark style=\"background-color:#bbf7d0\"><strong>100%</strong></mark>. "
            "Bible says He will turn your days like the <strong>days of your youth</strong>."
        ),
        "bullets": [
            "🌸 Close your eyes — remember how you jumped, ran, and looked in the mirror in your youth",
            "👑 <strong>Sarah at 90</strong> — bore a child; kings marry beauty; she still looked young",
            "👩 Bible calls women <strong>daughters of Sarah</strong> — not daughters of Ruth",
            "👨 Men are <strong>sons of Abraham</strong> — Scripture shows how they were restored so we can be too",
        ],
        "table": (
            ["Mindset", "Result"],
            [
                ("Partial healing (leg pain fading slowly)", "❌ Not God's aim"),
                ("Settle for 80–90%", "❌ Still not full"),
                ("<strong>Desire 100% restoration</strong>", "✅ Full restoration"),
            ],
        ),
    },
    {
        "title": "📖 Recap — Wisdom, Faith, Desire, His Righteousness",
        "intro": (
            "Last week we saw a psalmist who <strong>fell and rose again</strong>. "
            "Four keys carry into today's message — and the third is critical: "
            "<em>if you don't desire 100% restoration, it won't come to you.</em>"
        ),
        "ordered": [
            "🧠 <strong>Have wisdom</strong> — see danger and take refuge (Proverbs 22:3)",
            "🙏 <strong>Have faith</strong> — unbelief kept Israel from entering rest",
            "💛 <strong>Desire the blessing</strong> — if you don't desire it, it runs away from you",
            "✝️ <strong>Focus on God's righteousness</strong> — not your own (Matthew 6:33)",
        ],
        "bullets": [
            "📖 First <strong>know</strong> from Scripture that 100% restoration is possible",
            "💛 Then <strong>desire</strong> youth, healing, and full restoration",
            "🎁 If you believe it is in the Bible, it <em>will</em> happen in your life",
        ],
        "verse_refs": ["Proverbs 22:3", "Hebrew 3:19", "Psalm 109:17"],
    },
    {
        "title": "🌸 Don't Worry — Seek His Kingdom First (Matthew 6)",
        "intro": (
            "<em>Do not worry</em> — trust Him for <strong>full</strong> restoration, not half. "
            "God feeds the birds; not one falls dead without food. "
            "<mark style=\"background-color:#bbf7d0\"><strong>How much more valuable are you?</strong></mark>"
        ),
        "bullets": [
            "🕊️ Birds don't plan tomorrow's meals — yet your Father feeds them all",
            "🌸 Flowers of the field — <strong>not even Solomon</strong> was dressed like one of these",
            "👑 Seek <strong>His righteousness</strong> (not yours) — then <em>all these things</em> are added",
            "✨ Even <strong>much more</strong> than Solomon — God will clothe and restore you",
        ],
        "table": (
            ["Worry says", "Jesus says"],
            [
                ("What shall I eat, drink, wear?", "<strong>Your Father knows</strong> what you need"),
                ("Focus on tomorrow", "Seek first <strong>His kingdom and righteousness</strong>"),
                ("Half restoration is enough", "<strong>All these things</strong> shall be added unto you"),
            ],
        ),
        "verse_refs": ["Matthew 6:33", "Matthew 6:31"],
    },
    {
        "title": "📋 Three Steps in John 10 — Saved → Life → Full",
        "intro": (
            "We see <strong>only three things</strong> in John 10:9–10 — "
            "the path from rescue to <em>life to the full</em>."
        ),
        "ordered": [
            "<strong>Step 1 — Saved:</strong> I am the gate; those who enter will be saved",
            "<strong>Step 2 — Life:</strong> I have come that they may have life (<em>zōē</em>)",
            "<strong>Step 3 — Full:</strong> And have it <mark style=\"background-color:#fde68a\"><strong>to the full</strong></mark>",
        ],
        "table": (
            ["Stage", "Meaning", "Full?"],
            [
                ("Saved", "Rescued, healed, preserved", "Entry point"),
                ("Life", "God's breath (<em>zōē</em>) inside you", "Growing"),
                ("Full", "Zero sickness · zero pain · zero sorrow", "✅ 100%"),
            ],
        ),
        "verse_refs": ["John 10:9", "John 10:10"],
    },
    {
        "title": "🚪 Step 1: Saved — The Gate and Sōzó",
        "intro": (
            "The day you accept Christ you are <strong>saved</strong> — but know <em>how</em> you are saved. "
            "Not by your works, intelligence, or circle of friends — "
            "<mark style=\"background-color:#bbf7d0\"><strong>by grace through faith</strong></mark>, a gift of God."
        ),
        "bullets": [
            "💾 Greek <strong>sōzó</strong> — to heal · preserve · save · deliver · rescue",
            "🩸 Woman bleeding <strong>12 years</strong> — Jesus: <em>your faith has healed you</em>",
            "🛡️ God heals first, then <strong>preserves</strong> — permanent healing, not sick again tomorrow",
            "🙏 Confess: <em>I am saved — I am not going to get this back</em>",
        ],
        "table": (
            ["Adam's line", "Christ's line"],
            [
                ("One man's <strong>disobedience</strong> → many sinners", "One Man's <strong>obedience</strong> → many righteous"),
                ("Sin by Adam", "Righteousness by <strong>Jesus</strong> — not your effort"),
                ("Gift of death", "<mark style=\"background-color:#fde68a\"><strong>Gift of righteousness</strong></mark>"),
            ],
        ),
        "verse_refs": ["Ephesians 2", "Romans 5:17", "Romans 5:19"],
        "quote": (
            "💾 <strong>Sōzó (σῴζω) means:</strong> to heal · to preserve · to save · "
            "to deliver · to rescue — God protecting, healing, saving, and rescuing you."
        ),
    },
    {
        "title": "🔢 Simple Math — Zero Sickness, Zero Pain",
        "intro": (
            "Jesus said: <em>I have taken all your sickness.</em> That is basic math — "
            "if there are a thousand sicknesses in the world and Christ took <strong>all</strong> of yours, "
            "how many remain? <mark style=\"background-color:#bbf7d0\"><strong>Zero.</strong></mark>"
        ),
        "bullets": [
            "🩹 <strong>All sickness taken</strong> → you should have zero sickness",
            "😢 <strong>All pain taken</strong> → you should have zero pain",
            "⏳ He <strong>died young</strong> so that you may live long — He wants you young always",
            "🚪 Jesus is the <strong>only way</strong> — friendship, family, every lack restored to full",
        ],
        "table": (
            ["What Jesus took", "What remains in you"],
            [
                ("All your sickness", "<strong>Zero</strong> sickness"),
                ("All your pain", "<strong>Zero</strong> pain"),
                ("All your sorrow", "<strong>Zero</strong> sorrow"),
            ],
        ),
        "verse_refs": ["John 10:10"],
    },
    {
        "title": "🌱 Step 2: Zōē Life — Made in God's Image",
        "intro": (
            "Now one step higher — from saved to <strong>zōē life</strong>. "
            "God made mankind in His own image — like a <em>photocopy</em> of the original: "
            "you cannot see the difference. The devil is jealous because when he sees you, he sees <strong>Christ in you</strong>."
        ),
        "bullets": [
            "🌿 <strong>Bios</strong> — plant life (lowest): grass, flowers",
            "🐾 <strong>Psyche</strong> — animal/soul life: average human existence",
            "✨ <strong>Zōē</strong> — God's own life: <em>zero sickness, zero pain, zero sorrow</em>",
            "🌬️ God <strong>breathed</strong> into Adam's nostrils — that breath is <em>zōē</em>; Adam lost it through sin",
        ],
        "table": (
            ["Greek", "Level", "What Pastor teaches"],
            [
                ("Bios", "Plant life", "Lowest form of life"),
                ("Psyche", "Animal life", "Average person in the world"),
                ("<strong>Zōē</strong>", "God's own life", "What Adam had · what Pentecost restores"),
            ],
        ),
        "verse_refs": ["Genesis 1:26", "Genesis 2:7"],
    },
    {
        "title": "🦴 Ezekiel 37 — Our Dry Bones Live Again",
        "intro": (
            "This is <strong>not someone else's</strong> dry bones — it is ours. "
            "Born young → sickness comes → death → bones dry. "
            "That was never God's original design for Adam and Eve."
        ),
        "bullets": [
            "💀 Before salvation, in spiritual eyes we looked like <strong>dry bones</strong>",
            "🌬️ Sovereign Lord: <em>I will make breath enter you and you will come to life</em>",
            "📖 Then you will know that <strong>I am the Lord</strong>",
            "✅ Flesh, tendons, skin — everything becomes alive when God's breath enters",
        ],
        "verse_refs": ["Proverbs 22:3"],
    },
    {
        "title": "🌬️ Pentecost — Holy Spirit Restores Adam's Breath",
        "intro": (
            "Where does God breathe inside us again? <strong>Acts 2</strong> — violent wind, tongues of fire, "
            "all filled with the Holy Spirit. Men lost Adam's intended life; "
            "when you are saved the Spirit <em>comes inside you</em>; "
            "when baptized in the Spirit you are <strong>immersed in Him</strong>."
        ),
        "bullets": [
            "💧 Saved = drinking water; baptized in the Spirit = <strong>jumping into the water</strong>",
            "🌬️ Same <em>zōē</em> breath Adam had — <strong>100% zero sickness</strong> is the plan",
            "💛 When you <strong>desire</strong> it, blessing chases you",
            "📈 Saved → life → now stepping toward <strong>full restoration</strong>",
        ],
        "verse_refs": ["Acts 2:1-4"],
    },
    {
        "title": "💯 Step 3: Full Restoration — On Earth, Not Heaven Only",
        "intro": (
            "Do not push every blessing to heaven while living in poverty on earth. "
            "If healing is only in heaven, what is the point? "
            "<em>He wants to heal you 100% here</em> — because in heaven there is no sickness left to heal."
        ),
        "bullets": [
            "😢 Jesus took <strong>all sorrow</strong> — so you can live a sorrow-free life on earth",
            "☮️ He was not at peace on the cross — so you can have <strong>full peace</strong> now",
            "🌍 Jesus came so you can live <strong>happily on earth</strong>, not only in heaven",
            "👑 What Adam lost: communion, glory, authority — <strong>much more</strong> than health alone is restored",
        ],
        "table": (
            ["What Adam lost", "What Christ restores"],
            [
                ("Communion with God", "Fellowship restored in Christ"),
                ("Glory and image", "Crowned with glory — Psalm 8"),
                ("Authority over creation", "<strong>Rule, subdue, heir of the world</strong>"),
            ],
        ),
        "verse_refs": ["Revelation 21:4", "2 Cor 5:17", "Genesis 1:28", "Psalm 8:4-8", "Jeremiah 23:4", "Jeremiah 23:6"],
    },
    {
        "title": "🌳 Two Trees — Christ Is the Fruit of Life",
        "intro": (
            "Eden had <strong>two trees</strong>. Adam ate knowledge of good and evil — "
            "but God wanted him to eat from the <strong>tree of life</strong>, a realm even higher than <em>zōē</em>. "
            "<em>That fruit is nothing other than Jesus.</em>"
        ),
        "bullets": [
            "🌳 Tree of knowledge — Adam ate; tree of life — Adam could not eat after the fall",
            "✝️ <strong>We can eat the fruit of life</strong> — Jesus said: I am the life; eat My body",
            "🩸 Woman with issue of blood — healed through faith while Jesus walked the earth",
            "⚖️ By <strong>one Man's obedience</strong> many made righteous — ground for the next level",
        ],
        "table": (
            ["Tree of knowledge", "Tree of life (Christ)"],
            [
                ("Adam ate — fell", "Adam could not eat — lost"),
                ("Death and curse entered", "<strong>In Christ</strong> we eat life again"),
                ("Partial existence", "<strong>Better than Adam had</strong> — full authority restored"),
            ],
        ),
        "verse_refs": ["Romans 4:13", "Galatians 3:29", "Joshua 1:3", "Psalm 71:20", "Genesis 3:7", "Genesis 3:21", "Genesis 4:3-4"],
    },
    {
        "title": "👑 Heir of the World — Authority Through Faith",
        "intro": (
            "Abraham and Sarah were <strong>fully restored</strong> — a clue for us. "
            "<em>Heir of the world</em> through righteousness that comes by faith — not law. "
            "If you belong to Christ, you are <strong>Abraham's seed</strong> and heirs of the promise."
        ),
        "bullets": [
            "🌍 Adam lost authority over earth — God restores you as <strong>heir of the world</strong>",
            "🔑 Only key: <strong>righteousness by faith</strong> — seek first His kingdom and His righteousness",
            "📖 Romans 4:14 — law heirs void faith; promise comes by faith alone",
            "🎁 God will <strong>fulfil the desires of your heart</strong> — but you must desire first",
        ],
        "table": (
            ["Desire", "What God gives"],
            [
                ("Desire to be <strong>saved</strong>", "Rescue and preservation"),
                ("Desire <strong>zōē life</strong>", "Adam's breath restored"),
                ("Desire <strong>full restoration</strong>", "Zero sickness · zero pain · zero sorrow · full authority"),
            ],
        ),
        "verse_refs": ["Romans 4:14", "Deuteronomy 28:1", "Genesis 13:15", "Psalm 71:2"],
    },
]

GOSPEL_FLOW: list[dict[str, Any]] = [
    {
        "title": "🕊️ In His Presence — Deliverance and Light",
        "intro": (
            "In His presence there is <strong>deliverance</strong>, <strong>solution</strong>, and "
            "<strong>light</strong>. Kings went to battle with their own plans — but when they "
            "<em>inquired of the Lord</em>, the valley was filled without wind or rain."
        ),
        "bullets": [
            "💧 Promise verse: valley filled with water — <strong>2 Kings 3:17</strong>",
            "🔍 First step when stuck: <em>inquire of the Lord</em> through His prophet",
            "👂 Hearing brings deliverance, healing, and prosperity",
            "📖 Today's focus: <strong>hearing the gospel of Christ</strong> — the right covenant",
        ],
        "verse_refs": ["2 Kings 3:17", "2 Kings 3:11"],
    },
    {
        "title": "👂 Four Blessings of Hearing the Word",
        "intro": (
            "By the <em>foolishness of preaching</em> God delivers — worldly people must "
            "<strong>do</strong> something; biblical faith receives by <strong>hearing</strong> alone."
        ),
        "ordered": [
            "🏆 <strong>Victorious</strong> — overcome enemies when you hear",
            "👑 <strong>Noble</strong> — like Bereans, search Scripture daily",
            "📈 <strong>Grace multiplied</strong> — blessings come quickly",
            "🩺 <strong>Healed</strong> — the Lystra cripple heard Paul and leaped",
        ],
        "table": (
            ["World's way", "God's way"],
            [
                ("Must work to get delivered", "<strong>Hear</strong> — faith comes by hearing"),
                ("Random YouTube won't heal", "Hear the <strong>word of Christ</strong>"),
                ("Study wrong syllabus", "Study the <strong>right covenant</strong>"),
            ],
        ),
    },
    {
        "title": "🍞 Eating Is Fighting — Lechem and Lacham",
        "intro": (
            "Hebrew <strong>lechem</strong> (לֶחֶם) means bread; <strong>lacham</strong> (לָחַם) means "
            "<em>fighting</em>. Same consonants — vowels shift the meaning: "
            "<mark style=\"background-color:#bbf7d0\"><strong>eating is fighting</strong></mark>."
        ),
        "bullets": [
            "🍽️ Psalm 23:5 — He prepares a table <em>before your enemies</em> so you eat and fight",
            "🍞 Feed on <strong>Christ</strong> as living bread — not random messages",
            "⚔️ The cripple from birth <strong>kept hearing</strong> Paul — continuous tense",
            "✝️ Deliverance comes through <em>knowledge of Jesus Christ</em> alone",
        ],
        "verse_refs": ["Psalm 23", "John 6:51", "Romans 10"],
    },
    {
        "title": "📜 First Covenant Had Fault — Study the Right Syllabus",
        "intro": (
            "Studying the wrong exam paper fails you — if the <strong>first covenant had fault</strong>, "
            "a <em>second covenant</em> was sought. Hear the right syllabus or the four blessings cannot come."
        ),
        "bullets": [
            "📖 Hebrews 8:7 — if the first were faultless, no second would be needed",
            "⚠️ Hearing about the <strong>faulty covenant</strong> ministers fault to your life",
            "✝️ Hear the <strong>word of Christ</strong> — faith comes by hearing Him",
            "🎓 Know <em>what to hear</em> and <em>what not to hear</em>",
        ],
        "table": (
            ["Old covenant", "Gospel of Christ"],
            [
                ("First covenant had <strong>fault</strong>", "New covenant — <strong>right syllabus</strong>"),
                ("Law on stones", "Hear the <strong>word of Christ</strong>"),
                ("Blessed because you obey", "Blessed because <strong>He obeyed</strong>"),
            ],
        ),
        "verse_refs": ["Hebrews 8:7", "Hebrews 8"],
    },
    {
        "title": "☠️ Ministry of Death — Law Written on Stones",
        "intro": (
            "The <strong>ministry of death</strong> is engraved on stones — the letter kills. "
            "The <em>sting of death is sin</em>; the <strong>strength of sin is the law</strong>."
        ),
        "bullets": [
            "☠️ 2 Corinthians 3:7 — ministry of death, written and engraved on stones",
            "📜 The letter kills; the Spirit gives life — 2 Corinthians 3:6",
            "⚖️ Law = blessed based on <em>how good you are</em>",
            "✝️ Gospel = healed because <strong>He took all sickness</strong> at the cross",
        ],
        "verse_refs": ["2 Corinthians 3:7", "2 Corinthians 3:6", "Romans 7:10", "1 Corinthians 15:56"],
    },
    {
        "title": "✝️ Gospel of Christ — Power, Teaching, Preaching, Healing",
        "intro": (
            "Romans 1:16 — the gospel of Christ is the <strong>power of God</strong>. "
            "Jesus went about <em>teaching, preaching, and healing</em> — all three together."
        ),
        "bullets": [
            "📢 Galatians 1:8–9 — any other gospel is accursed",
            "🩺 Matthew 4:23 / 9:35 — teaching + preaching + healing every disease",
            "📖 Luke 24:27 — Moses and the Prophets speak of <strong>Himself</strong>",
            "🎁 Blessings are definite — not because of who you are, but <strong>whose you are</strong>",
        ],
        "table": (
            ["Law message", "Gospel message"],
            [
                ("Healed because you are good", "Healed because <strong>He took sickness</strong>"),
                ("Brightness by your deeds", "Brightness by <strong>what He did</strong>"),
                ("Works and wages", "Gospel = <strong>power</strong> — gift of God"),
            ],
        ),
        "verse_refs": ["Romans 1:16", "Matthew 4:23", "Matthew 9:35", "Mark 10:30"],
    },
    {
        "title": "🐑 Bible Pictures of Christ — From Eden to the Cross",
        "intro": (
            "The whole Bible speaks of <strong>Jesus</strong> — the first lamb killed in Eden, "
            "Abel's sacrifice, Abraham's ram, and every Old Testament offering pictured Christ."
        ),
        "bullets": [
            "🐑 Eden's first lamb and Abel's offering — picture of the coming Saviour",
            "🏔️ Abraham saw the Lamb on the mountain — that Lamb is Christ",
            "✝️ At the cross Jesus called <em>My God, My God</em> — bore our sin as a sinner",
            "👑 All blessings are <strong>definite</strong> — quicker than you expected",
        ],
        "verse_refs": ["Luke 24:27", "Galatians 1:8"],
    },
    {
        "title": "🍽️ Psalm 23 — Eat and Fight Before Your Enemies",
        "intro": (
            "Psalm 22 — <em>My God, my God, why have You forsaken Me?</em> — Jesus spoke this at the cross "
            "so Psalm 23's table of blessing follows: <strong>goodness and mercy all the days of your life</strong>."
        ),
        "bullets": [
            "🍽️ He prepares a table before you in the presence of enemies",
            "💛 Goodness and mercy shall follow you — <em>not one day missed</em>",
            "🩸 Jesus became sin at the cross so you can call God <strong>Father</strong>",
            "🎁 Hundredfold <strong>now</strong> — Mark 10:30 through the gospel of Christ",
        ],
        "verse_refs": ["Mark 10:30", "Psalm 22", "Matthew 4:23"],
    },
    {
        "title": "📖 Live From the Gospel — 1 Corinthians 9:14",
        "intro": (
            "Those who preach the gospel should <strong>live from the gospel</strong> — "
            "Psalm 133 — unity and anointing flow when we hear the right covenant together."
        ),
        "bullets": [
            "📖 1 Corinthians 9:14 — live from the gospel, not from law wages",
            "🛢️ Psalm 133:2 — precious oil on Aaron's head, running down",
            "✝️ Galatians 1:8–9 — no other gospel",
            "🎁 Hundredfold <strong>now</strong> — houses, lands, family in this time",
        ],
        "verse_refs": ["1 Corinthians 9:14", "Psalm 133:2", "Galatians 1:8", "Galatians 1:9"],
    },
]

MIRACLES_STAND_FLOW: list[dict[str, Any]] = [
    {
        "title": "⚡ God Is a Miracle-Working God — Next Level, Not Normal",
        "intro": (
            "God did not call you to loop through the same situation for years. "
            "He wants to take you to the <mark style=\"background-color:#bbf7d0\"><strong>next level</strong></mark> — "
            "from need to giving, from employee to employer, from struggle to helping others."
        ),
        "bullets": [
            "🐟 Peter caught fish daily — Jesus made him <strong>fisher of men</strong>",
            "🌑 He was in darkness at the cross so your life shines with <strong>light</strong>",
            "🩺 He was sick at the cross so you need not remain in sickness",
            "✨ Expect miracles — do not settle for mediocrity",
        ],
    },
    {
        "title": "🔍 Step 1 — Seek the Lord and His Strength",
        "intro": (
            "Do not only seek the Lord — seek also <strong>His strength</strong>. "
            "The Father's glory is revealed when you <em>receive and enjoy</em> what He saved for you at the cross."
        ),
        "bullets": [
            "📖 1 Chronicles 16:11 — seek His face <strong>evermore</strong>",
            "💪 His strength is seen when you are fully healed and different from the world",
            "🙏 Wake up daily: <em>I want the next level — not the same loop</em>",
            "🎯 Twelve spies — only Joshua and Caleb <strong>expected miracles</strong>",
        ],
        "verse_refs": ["1 Chronicles 16:11"],
    },
    {
        "title": "🏔️ Step 2 — Miracles Are Easy — Caleb's Confession",
        "intro": (
            "Ten spies saw giants and thick walls — Joshua and Caleb said "
            "<mark style=\"background-color:#fde68a\"><strong>we are well able — it is easy</strong></mark>. "
            "Only those two who expected miracles entered Canaan."
        ),
        "bullets": [
            "📖 Numbers 13:30 — <em>let us go up at once; we are well able</em>",
            "🧱 Jericho's wall was vehicle-thick — humanly impossible",
            "🎺 They walked, praised, and shouted — the wall fell on day seven",
            "🗣️ Speak today: <strong>easy to conquer</strong> sickness, bondage, and promotion",
        ],
        "table": (
            ["Ten spies", "Joshua and Caleb"],
            [
                ("Saw giants — <strong>impossible</strong>", "Expected miracle — <strong>easy</strong>"),
                ("Prepared with human strength", "Praised and walked — wall fell"),
                ("Never entered Canaan", "Only two who believed entered"),
            ],
        ),
        "verse_refs": ["Numbers 13:30"],
    },
    {
        "title": "🛑 Step 3 — Stand Still and See Yeshua",
        "intro": (
            "Red Sea in front, army behind — Moses said: "
            "<em>stand still and see the salvation of the Lord</em>. "
            "Salvation in Hebrew is <strong>Yeshua</strong> — Jesus."
        ),
        "bullets": [
            "📖 Exodus 14:13–14 — the Lord will <strong>fight for you</strong>; hold your peace",
            "☮️ Psalm 46:10 — be still and know that I am God",
            "365× <em>do not fear</em> — stand still when storms come",
            "🎒 Cast every burden on Christ — He gives rest",
        ],
        "table": (
            ["World's way", "God's way"],
            [
                ("Upskill, strive, prepare harder", "<strong>Stand still</strong> — see salvation"),
                ("Fear the enemy's size", "The Lord will <strong>fight for you</strong>"),
                ("Earn the miracle by works", "Miracles are <strong>free</strong> — by grace"),
            ],
        ),
        "verse_refs": ["Exodus 14:13", "Psalm 46:10"],
    },
    {
        "title": "🙏 Step 4 — Humble Faith — Pharisee vs Tax Collector",
        "intro": (
            "Two men prayed for a miracle — the Pharisee trusted his fasting and tithes; "
            "the tax collector said <em>God, be merciful to me, a sinner</em>. "
            "<strong>Only the humble man went home justified.</strong>"
        ),
        "bullets": [
            "📖 Luke 18 — whoever exalts himself will be humbled",
            "🙏 Trust <strong>His ability</strong>, not your intelligence or doctors' reports",
            "🛑 Standing still = resting in Him while the storm rages",
            "✨ When you trust Him completely, the miracle is <strong>easy</strong>",
        ],
        "verse_refs": ["Luke 18", "Ephesians 2:8"],
    },
    {
        "title": "🎁 Miracles Are Free — Gift of God, Not Wages",
        "intro": (
            "Ephesians 2:8–9 — by grace through faith; <strong>not of works</strong>. "
            "The righteous receive before they ask — miracles are a <em>gift</em>, not wages."
        ),
        "bullets": [
            "🎁 If it is by grace, it is no longer on the basis of works",
            "👑 Righteousness is the greatest gift — then every request is granted",
            "🗣️ Confess: <em>not by my obedience — by His obedience I am righteous</em>",
            "💪 Is anything too hard for the Lord? <strong>Nothing.</strong>",
        ],
        "ordered": [
            "🔍 <strong>Seek</strong> miracles daily",
            "🏔️ Believe miracles are <strong>easy</strong>",
            "🛑 <strong>Stand still</strong> — see Yeshua",
            "🎁 Receive by <strong>grace</strong> — miracles are free",
        ],
        "verse_refs": ["Ephesians 2:8", "Ephesians 2:9"],
    },
    {
        "title": "🌟 Nothing Too Hard — Receive Your Miracle Today",
        "intro": (
            "Genesis 18:14 — <em>Is anything too hard for the Lord?</em> "
            "Romans 5:19 — by one Man's obedience many made righteous; "
            "then miracles follow as a <strong>gift</strong>, not wages."
        ),
        "bullets": [
            "📖 Romans 11:6 — if by grace, no longer by works",
            "⚖️ James 2:10 — one failure makes you guilty of all — trust His obedience",
            "✝️ Galatians 6:14 — glory only in the cross of Christ",
            "🌴 Psalm 92:12 — the righteous flourish like a palm tree",
        ],
        "verse_refs": ["Genesis 18:14", "Romans 11:6", "Romans 4:4", "James 2:10", "Galatians 6:14", "Romans 5:19", "Psalm 92:12", "Hebrews 4:1", "1 Corinthians 1:27"],
    },
]

FREEDOM_TROUBLES_FLOW: list[dict[str, Any]] = [
    {
        "title": "🌅 New Grace Every Morning — Restoration Begins",
        "intro": (
            "His grace is <strong>new every morning</strong> — grace upon grace, not worldly ups and downs. "
            "The day you met Christ, the downward trajectory <em>stopped</em>; now He lifts you higher."
        ),
        "bullets": [
            "📈 Grace upon grace — strength upon strength every day",
            "🔄 Restoration: He will <strong>restore your life again</strong> — Psalm 71:20",
            "📖 Bible records how the psalmist fell and rose — learn so you need not fall",
            "🎯 God wants to take you to the <strong>next level</strong>, not repeat the wilderness",
        ],
        "verse_refs": ["Psalm 71:20"],
    },
    {
        "title": "🧠 Key 1 — Have Wisdom",
        "intro": (
            "Proverbs 22:3 — a prudent person sees danger and takes refuge; "
            "the simple walk in and suffer. <strong>Jesus is greater than Solomon</strong> — wisdom is inside you."
        ),
        "bullets": [
            "👑 Solomon's era had <strong>zero wars</strong> — wisdom brings peace",
            "📚 A wise person learns from others' falls; a fool must experience them",
            "🛡️ By hearing God's word together, you <strong>prevent falling</strong>",
            "✝️ Christ Himself is your wisdom",
        ],
        "verse_refs": ["Proverbs 22:3"],
    },
    {
        "title": "🙏 Key 2 — Have Faith",
        "intro": (
            "Israel wandered <strong>40 years</strong> for lack of faith — you need not repeat that. "
            "Faith comes by <em>hearing and hearing the word of Christ</em>."
        ),
        "bullets": [
            "📖 Faith comes by hearing — sit and listen; that is the easy way out",
            "🍞 Lechem = bread; lacham = fighting — more word, more faith, more victory",
            "✝️ Focus on <strong>Jesus</strong> — hearing about Christ delivers you",
            "⏱️ Come out of trouble <strong>quickly</strong> — not 40 years in the wilderness",
        ],
        "verse_refs": ["Hebrews 3:19", "Romans 10"],
    },
    {
        "title": "💛 Key 3 — Desire and Claim the Blessing",
        "intro": (
            "Psalm 109:17 — if you do not <strong>desire blessing</strong>, it runs away from you. "
            "The greatest honour to Christ is believing He took <em>all</em> your sickness, pain, and sorrow."
        ),
        "bullets": [
            "🌑 Do not settle in darkness like soldiers who ran back from bright light",
            "💯 Claim 100% healing, peace, and prosperity — Deuteronomy 28 blessings vs curses",
            "🎁 Jesus received every blessing at the cross — <strong>receive everything from Christ</strong>",
            "📜 Promise verse each month — <em>desire</em> it, do not treat it as random",
        ],
        "table": (
            ["Without desire", "With desire"],
            [
                ("Blessing runs <strong>away</strong>", "Blessing <strong>chases</strong> you"),
                ("Settle for partial healing", "Claim <strong>100%</strong> — zero sickness"),
                ("Sickness feels 'normal'", "Honour Christ — He took <strong>all</strong> sickness"),
            ],
        ),
        "verse_refs": ["Psalm 109:17", "Deuteronomy 28"],
    },
    {
        "title": "✝️ Key 4 — Seek His Righteousness, Not Yours",
        "intro": (
            "Psalm 71 repeats <strong>Your righteousness</strong> four times — not my own. "
            "Matthew 6:33 — seek first His kingdom and <em>His righteousness</em>; all things are added."
        ),
        "bullets": [
            "🧺 My righteousness is a <strong>filthy rag</strong> — Isaiah 64:6",
            "🐍 Moses looked to Christ on the cross — saved from serpents in the wilderness",
            "🐑 Abel's lamb sacrifice focused on Christ; Cain trusted his own strength",
            "🍷 Communion: new covenant — bless me by <strong>Your obedience</strong>, not mine",
        ],
        "table": (
            ["Self-righteousness", "His righteousness"],
            [
                ("Bless me for my obedience", "Bless me for <strong>His obedience</strong>"),
                ("Fig leaves — Adam's cover", "Animal skin — <strong>God's cover</strong>"),
                ("Purchase health by works", "<strong>All things added</strong> — Matthew 6:33"),
            ],
        ),
        "verse_refs": ["Psalm 71:16", "Psalm 71:19", "Matthew 6:33", "Romans 3:21"],
    },
    {
        "title": "⚖️ Righteousness Apart From the Law — Romans 3:21",
        "intro": (
            "The whole gospel is in one verse: <strong>righteousness of God apart from the law</strong>, "
            "witnessed by the law and prophets — meaning Moses, Elijah, and Jesus on the mount."
        ),
        "bullets": [
            "📖 Romans 3:21 — revealed apart from law, witnessed by law and prophets",
            "🔊 Matthew 17:5 — Father's voice: <strong>Hear Him</strong>, not Moses and Elijah equally",
            "🕊️ Acts 10:44 — while Peter preached, Holy Spirit fell on all who heard",
            "⛓️ Galatians 5:4 — justified by law = <strong>separated from Christ</strong>",
        ],
        "verse_refs": ["Romans 3:21", "Matthew 17:5", "Acts 10:44", "Galatians 5:4"],
    },
    {
        "title": "☠️ Ministry of Death — Letter Kills, Spirit Gives Life",
        "intro": (
            "2 Corinthians 3:7 — the ministry engraved on stones had a <strong>passing glory</strong>. "
            "The letter kills; mixing law and gospel ministers death, pain, and sickness."
        ),
        "bullets": [
            "☠️ Ministry of death — engraved on stones",
            "📜 2 Corinthians 3:6 — the letter kills; the Spirit gives life",
            "📉 Fallen from grace when you justify yourself by law",
            "🔊 <strong>Hear Him only</strong> — Holy Spirit falls while the gospel is preached",
        ],
        "table": (
            ["Law path", "Faith path"],
            [
                ("Blessed because you obey", "Blessed because <strong>Christ obeyed</strong>"),
                ("Separated from Christ", "<strong>Holy Spirit falls</strong> while gospel preached"),
                ("Ministry of death", "Spirit gives <strong>life and freedom</strong>"),
            ],
        ),
        "verse_refs": ["2 Corinthians 3:7", "2 Corinthians 3:6", "2 Corinthians 3:17", "Galatians 5:4"],
    },
    {
        "title": "🕊️ Holy Communion — Remember His Obedience",
        "intro": (
            "At the table we confess: <strong>not my obedience — Your obedience</strong> makes me righteous. "
            "Break bread for others' healing; drink the cup proclaiming sins forgiven."
        ),
        "bullets": [
            "🍷 New covenant cup — bless me by what You did, not what I do",
            "🍞 Body broken — pray healing for friends by breaking bread for them",
            "📖 Colossians 2:14 — handwriting of ordinances nailed to the cross",
            "✝️ Communion gives faith to rise from sickness and unbelief",
        ],
        "verse_refs": ["Colossians 2:14", "Luke 9:30", "Luke 24:27", "Revelation 3:15"],
    },
]

FRUITFUL_FLOW: list[dict[str, Any]] = [
    {
        "title": "🌳 Shalom — Fruitful and Multiply in Every Area",
        "intro": (
            "God told Adam: <strong>be fruitful and multiply</strong> — not only children, but health, riches, "
            "calling, sowing and reaping. <em>Shalom</em> means completeness in every area of life."
        ),
        "bullets": [
            "🌬️ Recap: Adam lost <strong>zōē</strong> — Pentecost wind restores breath-life",
            "🌿 Plant life (<em>bios</em>) → psyche → zōē — three levels of life",
            "🆕 Former things passed — sorrow, crying, pain are <strong>old things</strong> — Revelation 21:4",
            "📈 God wants fruitfulness in health, finance, family, and purpose",
            "✝️ In Christ all things become <strong>new</strong> — 2 Corinthians 5:17",
        ],
        "verse_refs": ["Revelation 21:4", "2 Cor 5:17", "John 10:10"],
    },
    {
        "title": "🩸 Twelve Years Sick — Only One Was Healed",
        "intro": (
            "Multitudes <strong>thronged</strong> Jesus — hundreds touched Him; only one was healed. "
            "The difference was <mark style=\"background-color:#bbf7d0\"><strong>faith</strong></mark>: "
            "<em>If only I may touch His garment, I shall be made well.</em>"
        ),
        "bullets": [
            "📖 Matthew 9:20–22 — she spoke to herself <em>before</em> touching",
            "👥 Luke 8:45 — multitudes pressed Him; only faith-touch brought power",
            "⛪ Jesus is in the midst when two or three gather — touch Him by faith",
            "🎯 Learn her four keys — then go to the next level",
        ],
        "verse_refs": ["Matthew 9:20", "Luke 8:45", "Matthew 9:22"],
    },
    {
        "title": "1️⃣ Do Not Be Conformed to This World",
        "intro": (
            "Romans 12:2 — be transformed by the <strong>renewing of your mind</strong>. "
            "Worldly neighbours say trouble is normal; believers must speak Christ's truth."
        ),
        "bullets": [
            "🗣️ She refused neighbours who said sickness is part of life",
            "💭 God cannot bless you <strong>more than you believe</strong>",
            "✝️ John 16:33 spoken to pre-cross disciples — you are born again; <strong>overcome the world</strong>",
            "🛡️ 1 John 5:4 — born of God overcomes the world through faith",
        ],
        "table": (
            ["Worldly mind", "Renewed mind"],
            [
                ("Trouble is part of life", "<strong>Trouble-free</strong> — He took it at the cross"),
                ("Sickness is normal with age", "<strong>Zero sickness</strong> — He took all"),
                ("Conformed to the world", "<strong>Transformed</strong> — speak: I shall be healed"),
            ],
        ),
        "verse_refs": ["Romans 12:2", "1 John 5:4", "Psalm 103:3"],
    },
    {
        "title": "2️⃣ Know You Are a Sinner — Not Eligible by Works",
        "intro": (
            "Luke 18 — Pharisee vs tax collector: only the man who said "
            "<em>God, be merciful to me, a sinner</em> went home <strong>justified</strong>."
        ),
        "bullets": [
            "👥 Two groups always follow Jesus: self-righteous and sinners",
            "✝️ Jesus stands with the <strong>weak</strong> — not those who demand they are good",
            "📖 Matthew 9:12 — I came for the sick, not the healthy",
            "🎁 Base blessing on the <strong>cross</strong>, not your fasting or tithes",
        ],
        "verse_refs": ["Luke 18:10", "Matthew 9:12", "Romans 3:10"],
    },
    {
        "title": "3️⃣ Do Not Drink Milk — Skilled in Righteousness",
        "intro": (
            "Hebrews 5:13–14 — milk drinkers are unskilled in the word of righteousness. "
            "If you say God blesses you for <em>your</em> goodness, you are still a babe."
        ),
        "bullets": [
            "🥛 Milk = righteousness by <strong>my</strong> works",
            "🍖 Solid food = blessed because of <strong>His obedience</strong> — Romans 5:19",
            "👗 She touched the <strong>hem</strong> — Isaiah 61:10 robe of <em>His</em> righteousness",
            "💯 Limitless blessing flows when you focus on how big the cross is",
        ],
        "verse_refs": ["Hebrews 5:13", "Romans 5:19", "Isaiah 61:10"],
    },
    {
        "title": "4️⃣ His Righteousness — Why She Was Sick 12 Years",
        "intro": (
            "Isaiah 64:6 — our righteousness is filthy rags (sanitary cloth). "
            "Twelve years in self-righteousness brought twelve years of sickness — "
            "touching <strong>His righteousness</strong> restored her."
        ),
        "bullets": [
            "👗 Hem of garment = robe of <strong>His righteousness</strong>",
            "🗣️ Speak: I am healed, wealthy, prosperous — He took it at the cross",
            "🌳 Be fruitful — bear fruit in every area God assigned",
            "✝️ Jesus sides with the undeserving — come as you are",
        ],
        "table": (
            ["Her old path", "Her faith path"],
            [
                ("12 years self-righteousness", "Touched <strong>His righteousness</strong>"),
                ("Filthy rags — Isaiah 64:6", "Robe of righteousness — Isaiah 61:10"),
                ("Not fruitful", "<strong>Made well</strong> — fruitful again"),
            ],
        ),
        "verse_refs": ["Isaiah 64:6", "Romans 5:19", "Matthew 9:22"],
    },
    {
        "title": "🌾 Dominion and Blessing — Genesis Calling",
        "intro": (
            "God's original mandate stands: <strong>be fruitful and multiply</strong> in every area. "
            "Saved → zōē life → full — sowing, reaping, and dominion restored in Christ."
        ),
        "bullets": [
            "🚪 John 10:9–10 — saved, life, and life to the full",
            "💾 Sōzó — heal, preserve, save, deliver, rescue",
            "📖 Psalm 109:17 — desire blessing or it runs from you",
            "🌍 Genesis 13:15 — heir of the land through promise",
        ],
        "verse_refs": ["John 10:9", "John 10:10", "Psalm 109:17", "Genesis 13:15"],
    },
]

DELAY_FLOW: list[dict[str, Any]] = [
    {
        "title": "⏱️ Why Delay? — God Wants Instant Blessing",
        "intro": (
            "Delay is usually <strong>unbelief</strong>, not God's reluctance. "
            "A wise person learns from Abraham's 25-year wait — "
            "Jesus, greater than Solomon, is your wisdom."
        ),
        "bullets": [
            "🗺️ Egypt to Canaan: 40 days on the map — Israel took <strong>40 years</strong>",
            "👨 Earthly parents rush to help sick children — how much more your heavenly Father",
            "📖 God wants to <strong>instantly</strong> heal, bless, and restore you",
            "🧠 Learn from others' mistakes — do not repeat Abraham's delay",
        ],
    },
    {
        "title": "👴 Abraham at 75 — Promise vs 25-Year Wait",
        "intro": (
            "Genesis 12:2 — at age <strong>75</strong> God promised a nation and blessing; "
            "Isaac came at <strong>100</strong>. Three reasons for delay — learn them now."
        ),
        "bullets": [
            "🎯 Ultimate goal: no death, sorrow, crying, or pain — Revelation 21:4",
            "🆕 In Christ, old things passed — former things are <strong>gone now</strong>",
            "👑 Heir of the world through <strong>righteousness of faith</strong> — Romans 4:13",
            "🌟 Abraham was God's <strong>friend</strong> — a friend asks and receives immediately",
        ],
        "verse_refs": ["Genesis 12:2", "Revelation 21:4", "2 Cor 5:17", "Romans 4:13"],
    },
    {
        "title": "1️⃣ El Shaddai — 100% His Power, Not 50/50",
        "intro": (
            "Genesis 17:1 — at <strong>99</strong>, God first revealed Himself as <strong>Almighty</strong>. "
            "Until then Abraham trusted his own strength — 75% self, 25% God, then 50/50."
        ),
        "bullets": [
            "💪 Young strength fades — supernatural power needed at old age",
            "📖 At 99 his body was <em>as good as dead</em> — then God gave strength",
            "🎯 Even with strength, trust <strong>100% in God</strong> — not a mixed glory",
            "✝️ Learn from Abraham — do not wait until 99 to call Him Almighty",
        ],
        "table": (
            ["Mixed trust", "Full trust"],
            [
                ("75% my power, 25% God", "<strong>100% El Shaddai</strong> — zero self"),
                ("Half glory to me at 50/50", "<strong>All glory</strong> to Christ alone"),
                ("Delay until strength fails", "<strong>Instant</strong> blessing at 75"),
            ],
        ),
        "verse_refs": ["Genesis 17:1"],
    },
    {
        "title": "2️⃣ Faith Speaks — Abram Becomes Abraham",
        "intro": (
            "Genesis 17:5 — name change at 99: Abram → <strong>Abraham</strong> (father of many); "
            "Sarai → <strong>Sarah</strong> (princess). In Hebrew culture, name = character."
        ),
        "bullets": [
            "🗣️ Faith is the substance of things <strong>not yet seen</strong>",
            "👴 They called each other father of many and princess — before Isaac was born",
            "📢 Let the weak say I am strong; let the poor say I am rich",
            "✨ Speak what you want to see — <em>the truth will set you free</em>",
        ],
        "verse_refs": ["Genesis 17:5", "Genesis 17:15"],
    },
    {
        "title": "3️⃣ His Favour — The Letter Hey (ה)",
        "intro": (
            "Only one letter added to Abram and Sarai — <strong>Hey</strong> (ה), God's favour. "
            "Blessing comes not because you deserve it, but because <strong>He paid at the cross</strong>."
        ),
        "bullets": [
            "🎁 Noah found favour — same favour rests on you",
            "😂 Sarah laughed and lied — yet grace still came",
            "✝️ Father of faith said <em>how is this possible?</em> — favour, not eligibility",
            "⚡ Realise favour → <strong>instant blessing</strong> — no more 25-year wait",
        ],
        "verse_refs": ["Genesis 17:1", "Romans 4:13"],
    },
    {
        "title": "⚖️ Righteousness by Faith — Heir of the World",
        "intro": (
            "Romans 4:13 — heir of the world <strong>not through law</strong> but through faith. "
            "2 Corinthians 5:21 — He became sin so you become the righteousness of God in Him."
        ),
        "bullets": [
            "🌍 Galatians 3:29 — if you are Christ's, you are Abraham's seed and heirs",
            "⛓️ Galatians 5:4 — mixing law and gospel = fallen from grace",
            "🗣️ Call yourself healed, blessed, anointed — <strong>today</strong>, not after 25 years",
            "👑 Righteousness by faith, not works — receive the promise now",
        ],
        "table": (
            ["Law delay", "Faith now"],
            [
                ("Wait until you are good enough", "<strong>Instant</strong> — His obedience"),
                ("50/50 mix delays blessing", "<strong>100% favour</strong> — Hey added"),
                ("Self-strength until 99", "<strong>El Shaddai</strong> at every age"),
            ],
        ),
        "verse_refs": ["Romans 4:13", "2 Corinthians 5:21", "Galatians 3:29", "Galatians 5:4"],
    },
    {
        "title": "🙏 Stand and Receive — No More 25-Year Wait",
        "intro": (
            "Romans 5:19 — by one Man's obedience many made righteous. "
            "Call yourself healed, blessed, and anointed <strong>today</strong> — "
            "God leads you further as He led you until now."
        ),
        "bullets": [
            "📖 Romans 5:19 — obedience of Christ, not your effort",
            "🗣️ Confess in faith what you want to see manifest",
            "⏱️ El Shaddai + faith speaks + favour = <strong>instant</strong> blessing",
            "👑 Heir of the world — receive the promise now, not at 100",
        ],
        "verse_refs": ["Romans 5:19", "Romans 5:17"],
    },
    {
        "title": "📖 Romans 4 — Fully Convinced God Performs",
        "intro": (
            "Abraham was fully convinced God gives life to the dead and calls "
            "things that are not as though they were — <strong>instant</strong>, not delayed."
        ),
        "bullets": [
            "📖 Romans 4 — against all hope, believed in hope",
            "👴 At 99 both said <em>how is this possible?</em> — favour carried them",
            "🗣️ Speak faith daily — delay ends when self-strength ends",
            "🌍 Heir of the world — Galatians 3:29, Abraham's seed in Christ",
        ],
        "ordered": [
            "⏱️ <strong>El Shaddai</strong> — 100% His power",
            "🗣️ <strong>Faith speaks</strong> — rename yourself in Christ",
            "🎁 <strong>His favour</strong> — Hey (ה) added to your name",
            "⚖️ <strong>Righteousness by faith</strong> — receive now",
        ],
        "verse_refs": ["Romans 4:13", "Romans 4:14", "Galatians 3:29"],
    },
    {
        "title": "🌍 Heir of the World — Shalom Restored",
        "intro": (
            "Adam lost heirship; Christ restores it. <em>Shalom</em> — sickness-free, pain-free, "
            "sorrow-free life — everything that disturbs shalom went onto Jesus at the cross."
        ),
        "bullets": [
            "📖 Revelation 21:4 — no more death, sorrow, crying, or pain",
            "🆕 2 Corinthians 5:17 — new creation; old things passed at the cross",
            "🎁 By His stripes you are healed — stripes took what disturbs your peace",
            "🗣️ Start calling yourself healed, healthy, prosperous, redeemed — today",
        ],
        "table": (
            ["At 75", "At 99"],
            [
                ("Trusted own strength", "Called <strong>El Shaddai</strong>"),
                ("Abram and Sarai", "<strong>Abraham</strong> and <strong>Sarah</strong>"),
                ("25-year wait", "<strong>Instant</strong> favour — Hey added"),
            ],
        ),
        "verse_refs": ["Revelation 21:4", "2 Cor 5:17", "Genesis 12:2", "Genesis 17:1"],
    },
    {
        "title": "🙏 Call Yourself Healed — Delay Ends Today",
        "intro": (
            "God calls you blessed, anointed, healed, and prosperous. "
            "Until now He led you; He is able to lead you further — "
            "<strong>no more 25-year wait</strong> when favour and faith speak now."
        ),
        "bullets": [
            "🗣️ Let the weak say I am strong; let the poor say I am rich",
            "📢 There shall be no more sickness, pain, sorrow, or cry in me",
            "✝️ 2 Corinthians 5:21 — righteousness of God in Christ, not your works",
            "⏱️ Wise learn from Abraham — call El Shaddai before strength fails",
        ],
        "ordered": [
            "👴 <strong>El Shaddai</strong> at every age — not only at 99",
            "🗣️ <strong>Rename</strong> yourself in faith — Abraham and Sarah",
            "🎁 <strong>Favour</strong> — Hey (ה) — gift, not wage",
            "👑 <strong>Heir now</strong> — righteousness apart from works",
        ],
        "verse_refs": ["2 Corinthians 5:21", "Galatians 5:4", "Romans 5:19"],
    },
]

FREEDOM_SPIRIT_FLOW: list[dict[str, Any]] = [
    {
        "title": "🕊️ In His Presence — Deliverance and Miracles",
        "intro": (
            "In His presence there is <strong>deliverance</strong>, <strong>solution</strong>, and "
            "<strong>miracle</strong>. Last week: four benefits of hearing — victorious, noble, "
            "grace multiplied, and healed."
        ),
        "bullets": [
            "👂 Hear again and again — Israelites heard once and stalled 40 years",
            "📈 Grace and peace <strong>multiplied</strong> by knowledge of Christ — 2 Peter 1:2",
            "⚡ You choose the <strong>speed</strong> of your blessing",
            "✝️ Focus on <strong>Jesus only</strong> — not law mixed with gospel",
        ],
        "verse_refs": ["2 Peter 1:2"],
    },
    {
        "title": "🌳 Two Trees — Life vs Knowledge of Good and Evil",
        "intro": (
            "Eden had two trees. Knowing good and evil makes you focus on <strong>yourself</strong>; "
            "knowing Christ makes you focus on <strong>Him</strong> — and give Him the glory."
        ),
        "bullets": [
            "🌳 Tree of life = Jesus — I am the way, truth, and life",
            "🍽️ Eating is fighting — feed on Christ, not self-improvement",
            "📖 Psalm 23 — table prepared before enemies; eat and fight",
            "⚖️ Good and evil knowledge → self-focus; Christ → God gets glory",
        ],
        "table": (
            ["Tree of Knowledge", "Tree of Life"],
            [
                ("Focus on <strong>yourself</strong>", "Focus on <strong>Christ</strong>"),
                ("Earn by reward system", "<strong>Eat freely</strong> — gift of God"),
                ("Mix law and gospel", "Spirit, Son, Father — <strong>freedom</strong>"),
            ],
        ),
    },
    {
        "title": "⛓️ What Separates You From Christ? — Galatians 5:4",
        "intro": (
            "Bible's answer: trying to be <strong>justified by the law</strong>. "
            "Christ becomes of <em>no effect</em> — fallen from grace — even while you pray and read."
        ),
        "bullets": [
            "📖 Romans 3:10 — no one righteous by own effort",
            "👥 Jesus sent the self-righteous away; welcomed sinners",
            "🙏 Pharisees did good works but trusted themselves — Christ had no effect",
            "✝️ Come as you are — He cleanses; sin does not separate the believer",
        ],
        "verse_refs": ["Galatians 5:4", "Romans 3:10"],
    },
    {
        "title": "🕊️ Freedom Through the Spirit",
        "intro": (
            "Where the Spirit of the Lord is, there is <strong>freedom</strong>. "
            "Acts 10:44 — while Peter was still speaking, the Holy Spirit fell on all who heard."
        ),
        "bullets": [
            "🤗 Greek <em>fell</em> = embrace — like the father hugging the prodigal son",
            "📖 Galatians 3:2 — Spirit by hearing with faith, not works of law",
            "✨ Galatians 3:5 — miracles come by hearing of faith",
            "🔊 Specific gospel words bring the Spirit — not random Bible reading",
        ],
        "verse_refs": ["2 Corinthians 3:17", "Acts 10:44", "Galatians 3:2", "Galatians 3:5"],
    },
    {
        "title": "👶 Freedom Through the Son",
        "intro": (
            "If the Son sets you free, you are <strong>free indeed</strong>. "
            "Abide in His word — know the truth; the truth sets you free."
        ),
        "bullets": [
            "📖 John 8:36 — the Son makes you free indeed",
            "🔓 John 8:31–32 — abide in My word; truth sets you free",
            "⛓️ Galatians 5:1 — do not return to the yoke of slavery",
            "☮️ Romans 8:1–2 — no condemnation; Spirit of life sets you free",
        ],
        "verse_refs": ["John 8:36", "John 8:31", "Galatians 5:1", "Romans 8:1"],
    },
    {
        "title": "👨 Freedom Through the Father — Eat Freely",
        "intro": (
            "The prodigal came to himself — the Father's servants had <strong>bread enough</strong>. "
            "Greatest honour: enjoy what Jesus paid for at the cross — <em>eat freely</em>, not earn."
        ),
        "bullets": [
            "🍞 Genesis 2:16 — <strong>freely eat</strong> — gift, not reward",
            "👂 Hear about <strong>Jesus only</strong> — Father said: Hear Him",
            "🎁 Blessing is a gift, not wages — do not return to slavery",
            "✝️ Christ has set us free — choose the Tree of Life daily",
        ],
        "verse_refs": ["Luke 15:14", "Acts 10:43", "Psalm 103:10"],
    },
    {
        "title": "🔊 What Peter Preached — Spirit Falls on Hearers",
        "intro": (
            "Acts 10:43 — forgiveness through His name. "
            "John 5:24 — hears My word and believes → eternal life, no condemnation."
        ),
        "bullets": [
            "📖 Jeremiah 17:10 — God searches the heart; reward is not by self-effort",
            "🕊️ Holy Spirit fell while Peter preached — not during law sermons",
            "👂 Hear Jesus only — transformed Peter's message brings the embrace",
            "✝️ Freedom is complete: Spirit, Son, and Father together",
        ],
        "verse_refs": ["John 5:24", "Jeremiah 17:10", "Acts 10:43"],
    },
]

LISTEN_FLOW: list[dict[str, Any]] = [
    {
        "title": "💧 2 Kings 3:17 — Valley Filled Without Rain",
        "intro": (
            "Kings marched with their own plan and ran out of water — enemies could defeat them easily. "
            "Solution: <strong>inquire of the Lord</strong>. When you hear, the valley fills without wind or rain."
        ),
        "bullets": [
            "🔍 2 Kings 3:11 — is there a prophet? <em>Inquire of the Lord</em>",
            "👂 Hearing brings deliverance, healing, and prosperity",
            "❓ Why come regularly? Each hearing lifts you to a higher level",
            "📖 By the foolishness of preaching God delivers",
        ],
        "verse_refs": ["2 Kings 3:17", "2 Kings 3:11"],
    },
    {
        "title": "👂 Four Blessings of Hearing Summarised",
        "intro": (
            "Four definite outcomes when you hear the <strong>right word</strong>: "
            "victory, nobility, multiplied grace, and healing."
        ),
        "ordered": [
            "🏆 <strong>Victorious</strong> — overcome every enemy",
            "👑 <strong>Noble</strong> — examine Scripture daily like Bereans",
            "📈 <strong>Grace multiplied</strong> — 2 Peter 1:2",
            "🩺 <strong>Healed</strong> — Lystra cripple heard Paul and leaped",
        ],
        "table": (
            ["Hear once", "Hear again and again"],
            [
                ("Stall 40 years like Israel", "<strong>Faith grows</strong> — deliverance comes"),
                ("Random messages", "Hear the <strong>word of Christ</strong>"),
                ("Wrong syllabus", "Right covenant — <strong>four blessings</strong> flow"),
            ],
        ),
    },
    {
        "title": "🍞 Eating Is Fighting — Feed on Christ",
        "intro": (
            "<strong>Lechem</strong> = bread; <strong>lacham</strong> = fighting. "
            "Psalm 23 — table before enemies. Feed on the <em>living bread</em>, not random YouTube sermons."
        ),
        "bullets": [
            "🍞 John 6:51 — I am the living bread from heaven",
            "👂 Cripple heard Paul <strong>continuously</strong> — Greek continuous tense",
            "✝️ Knowledge of Jesus alone brings deliverance and peace",
            "⚔️ More eating = more fighting the enemy",
        ],
        "verse_refs": ["John 6:51", "Acts 14:8", "James 4:7"],
    },
    {
        "title": "👑 Noble Like Bereans — Search the Scriptures",
        "intro": (
            "Acts 17:11 — Bereans were more noble: they received the word with eagerness and "
            "<strong>examined the Scriptures daily</strong>. The word cleanses — John 15:3."
        ),
        "bullets": [
            "📖 Examine Scripture daily — do not accept blindly",
            "🧼 You are clean because of the word Jesus spoke",
            "💧 Ephesians 5:26 — washing of water by the word",
            "📈 Noble character comes through <strong>hearing with examination</strong>",
        ],
        "verse_refs": ["Acts 17:11", "John 15:3", "Ephesians 5:26", "2 Peter 1:2"],
    },
    {
        "title": "🩺 Healing by Hearing — Lystra Cripple",
        "intro": (
            "Acts 14 — a man crippled from birth <strong>heard Paul speaking</strong> and leaped. "
            "Not random hearing — the word of Christ with faith."
        ),
        "bullets": [
            "🦵 Born crippled — one solution: keep hearing Paul",
            "📢 Faith comes by hearing the <strong>word of Christ</strong>",
            "🏆 Victory over death-fear unlocks every other victory",
            "✝️ Authority over sickness through hearing with faith",
        ],
        "verse_refs": ["Acts 14:8", "Acts 14:10"],
    },
    {
        "title": "📜 Right Covenant — First Had Fault",
        "intro": (
            "Hebrews 8:7 — the first covenant had <strong>fault</strong>. "
            "Study the ministry of death on stones and you minister death to your own life."
        ),
        "bullets": [
            "☠️ 2 Corinthians 3:7 — ministry of death engraved on stones",
            "📜 Letter kills; Spirit gives life",
            "⚖️ Law = blessed for your goodness; gospel = blessed for <strong>His cross</strong>",
            "🎓 Final key: know what to hear and what <strong>not</strong> to hear",
        ],
        "table": (
            ["Ministry of death", "Gospel of Christ"],
            [
                ("Law on stones", "Hear <strong>word of Christ</strong>"),
                ("Strength of sin is the law", "Faith comes by <strong>hearing Him</strong>"),
                ("First covenant fault", "New covenant — <strong>right syllabus</strong>"),
            ],
        ),
        "verse_refs": ["Hebrews 8:7", "2 Corinthians 3:7", "2 Corinthians 3:6", "Romans 10"],
    },
    {
        "title": "🏆 Authority Over Death — Hear and Overcome",
        "intro": (
            "Death is God's <strong>enemy</strong>, not His appointment. "
            "Hearing the word of Christ restores authority — "
            "Mark 5:27: touch His garment by faith and be made whole."
        ),
        "bullets": [
            "☠️ 1 Corinthians 15:26 — the last enemy is death",
            "📖 Romans 7:10 — commandment intended for life brought death under law",
            "✝️ Romans 5:20 — where sin abounded, grace abounded much more",
            "🌿 Genesis 2:17 — death entered by disobedience; life by hearing Christ",
        ],
        "verse_refs": ["Mark 5:27", "Romans 7:10", "Romans 5:20", "Genesis 2:17"],
    },
]

HEIR_FLOW: list[dict[str, Any]] = [
    {
        "title": "👑 Supernatural Exaltation — Freedom From All Troubles",
        "intro": (
            "God exalts you <strong>supernaturally</strong> — finishing a 30-year mortgage in five years, "
            "coming out of trouble while others wonder how. Today's anchor: <strong>Romans 3:21</strong>."
        ),
        "bullets": [
            "🌍 Freedom from <strong>all</strong> troubles — not two pending",
            "👁️ Vision zero-trouble life — then it manifests",
            "📖 Romans 3:21 — righteousness apart from law, witnessed by law and prophets",
            "🕊️ Where the Spirit is, there is freedom — 2 Corinthians 3:17",
        ],
        "verse_refs": ["Romans 3:21", "2 Corinthians 3:17"],
    },
    {
        "title": "0️⃣ Zero Troubles — Psalm 34:19",
        "intro": (
            "Many are the afflictions of the righteous — but the Lord <strong>delivers from them all</strong>. "
            "If all troubles are removed, how many remain? <mark style=\"background-color:#bbf7d0\"><strong>Zero.</strong></mark>"
        ),
        "bullets": [
            "📖 Psalm 34:19 — delivered from <strong>all</strong> troubles",
            "⚖️ Proverbs 12:21 — no harm overcomes the righteous",
            "🧠 Jesus's wisdom inside you prevents lack of knowledge",
            "✝️ Do not believe trouble is guaranteed — believe deliverance",
        ],
        "table": (
            ["Wrong belief", "Bible possibility"],
            [
                ("Righteous must have trouble", "<strong>Zero troubles</strong> — all removed"),
                ("Sickness is normal", "Complete peace — <strong>shalom</strong>"),
                ("Worldly ups and downs", "Grace upon grace — always rising"),
            ],
        ),
        "verse_refs": ["Psalm 34:19", "Proverbs 12:21"],
    },
    {
        "title": "🏔️ Mount of Transfiguration — Hear Him",
        "intro": (
            "Romans 3:21's witnesses = Moses (law), Elijah (prophets), Jesus — "
            "the mount of transfiguration. Peter wanted three tabernacles; the Father said: "
            "<strong>Hear Him.</strong>"
        ),
        "bullets": [
            "📖 Matthew 17:5 — this is My beloved Son; <em>hear Him</em>",
            "📺 Do not tune Moses, Elijah, and Jesus as equal YouTube channels",
            "⚠️ Father rejected Peter's mixed message — even the Creator opposed it",
            "🔊 One message saves: the gospel of <strong>Jesus Christ</strong>",
        ],
        "verse_refs": ["Matthew 17:5", "Romans 3:21"],
    },
    {
        "title": "🕊️ Peter Transformed — Holy Spirit Falls While Speaking",
        "intro": (
            "Acts 10:44 — while Peter was <strong>still speaking</strong>, the Holy Spirit fell. "
            "Greek <em>fell</em> = embrace. Compare what Peter preached before vs after the mount."
        ),
        "bullets": [
            "🤗 Holy Spirit hugs you when you speak the right gospel words",
            "📖 Galatians 3:2 — Spirit by hearing with faith, not law",
            "✨ Galatians 3:5 — miracles by hearing of faith",
            "🎯 Speak and hear what transformed Peter preached — then freedom comes",
        ],
        "verse_refs": ["Acts 10:44", "Galatians 3:2", "Galatians 3:5"],
    },
    {
        "title": "✝️ Righteousness Revealed — One Man's Obedience",
        "intro": (
            "Romans 5:19 — by one Man's obedience many made righteous. "
            "At the cross Jesus said <em>My God, My God</em> — divine exchange: He became sin; you become righteous."
        ),
        "bullets": [
            "🔄 Sinner cannot call God Father — Jesus gave you sonship",
            "📖 Psalm 103:10 — not dealt with us according to our sins",
            "🎁 Righteousness is revealed at the cross — not by your works",
            "👑 Apart from law — the whole gospel in one phrase",
        ],
        "verse_refs": ["Romans 5:19", "Psalm 103:10", "Romans 3:21"],
    },
    {
        "title": "⛓️ Four Results of Justifying Yourself by Law",
        "intro": (
            "Believing blessings come from <em>your</em> obedience separates you from Christ, "
            "makes you fall from grace, and brings the curse."
        ),
        "ordered": [
            "⛓️ <strong>Separated from Christ</strong> — Galatians 5:4",
            "📉 <strong>Fallen from grace</strong> — miss Noah-level favour",
            "☠️ <strong>Under the curse</strong> — Galatians 3:10; works of law",
            "💀 <strong>Ministry of death</strong> — 2 Corinthians 3:7 on stones",
        ],
        "table": (
            ["Law path", "Faith path"],
            [
                ("Blessed because you obey", "Blessed because <strong>Christ obeyed</strong>"),
                ("Heir through works", "<strong>Heir of the world</strong> through faith"),
                ("Mix Moses, Elijah, Jesus", "Father's voice: <strong>Hear Him</strong>"),
            ],
        ),
        "verse_refs": ["Galatians 5:4", "Galatians 3:10", "2 Corinthians 3:7", "Galatians 1:8"],
    },
    {
        "title": "🌍 Heir of the World — Romans 4:13",
        "intro": (
            "Promise: <strong>heir of the world</strong> — not through law but through righteousness of faith. "
            "Galatians 3:29 — if you are Christ's, you are Abraham's seed. Sons are free; heirs walk in exaltation."
        ),
        "bullets": [
            "👑 Adam lost the world — faith restores heirship",
            "⚖️ Galatians 2:16 — justified apart from works of law",
            "🕊️ Sons are free — supernatural exaltation before all people",
            "🗣️ Believe: blessed by <strong>His obedience</strong> — Holy Spirit embraces you",
        ],
        "verse_refs": ["Romans 4:13", "Galatians 3:29", "Galatians 2:16", "Romans 4:14"],
    },
    {
        "title": "📜 Witnessed by Law and Prophets — Full Picture",
        "intro": (
            "Romans 3:21 witnessed by Moses and Elijah on the mount — "
            "but the Father commands: <strong>Hear Him</strong>. "
            "Sons are free; heirs walk in supernatural exaltation."
        ),
        "bullets": [
            "📖 Romans 2:13 — hearers of law not justified; hearers of Christ are",
            "💛 Psalm 103:8–9 — slow to anger, abounding in mercy",
            "⛓️ Colossians 2:14 — ordinances nailed to the cross",
            "🕊️ Luke 9:54 — even disciples mixed law-fire with gospel grace",
        ],
        "verse_refs": ["Romans 2:13", "Romans 2:8", "Psalm 103:8", "Colossians 2:14", "Luke 9:54"],
    },
    {
        "title": "🕊️ Supernatural Exaltation — Zero Troubles Life",
        "intro": (
            "Freedom from <strong>all</strong> troubles is Bible-promised — not one or two pending. "
            "When the Spirit embraces you, people marvel how you came out so quickly."
        ),
        "bullets": [
            "📖 Romans 3:28 — justified by faith apart from works of law",
            "⚖️ Galatians 2:16 — not justified by works; faith in Jesus Christ",
            "🌍 Romans 4:14 — law voids promise; faith secures heirship",
            "👑 Sons are free — walk in supernatural exaltation before all people",
        ],
        "table": (
            ["Before mount", "After mount"],
            [
                ("Three tabernacles — mix messages", "<strong>Hear Him</strong> — one gospel"),
                ("Spirit opposed", "Spirit <strong>embraces</strong> hearers"),
                ("Troubles remain", "<strong>Zero troubles</strong> — all removed"),
            ],
        ),
        "verse_refs": ["Romans 3:28", "Galatians 2:16", "Romans 4:14"],
    },
]

COMMUNION_FLOW: list[dict[str, Any]] = [
    {
        "title": "☝️ One Reason — Not Discerning the Lord's Body",
        "intro": (
            "1 Corinthians 11:30 — for <strong>one reason</strong> many are weak, sick, and sleep before their time. "
            "Not many reasons — find the one and receive the remedy."
        ),
        "bullets": [
            "📖 One reason — not <em>reasons</em>",
            "💊 Weak, sick, sleep early — all from the same root",
            "🍷 Context: Holy Communion — remember what He did",
            "🔍 Unworthy <strong>manner</strong>, not unworthy person — go as you are",
        ],
        "verse_refs": ["1 Corinthians 11:30", "1 Corinthians 11:29"],
    },
    {
        "title": "1️⃣ Remember It Is Free — Prevent Falling Like Adam",
        "intro": (
            "Genesis 2:16 — <strong>freely eat</strong>. Eve dropped that one word — thought blessings must be earned. "
            "Adam's fall began by forgetting everything is <em>free</em>."
        ),
        "bullets": [
            "🎁 Gift vs reward — blessing is a gift, not wages",
            "📖 Romans 5:17 — gift of righteousness",
            "🧠 Psalm 103:2 — <strong>forget not</strong> all His benefits",
            "✝️ Forgives all iniquity; heals all diseases — at the cross He saw you",
        ],
        "table": (
            ["Adam's mistake", "Communion remedy"],
            [
                ("Forgot <strong>freely</strong> eat", "Remember — <strong>all free</strong>"),
                ("Earn like God — ate knowledge tree", "Receive gift — prevent falling"),
                ("Devil: do this to get that", "God: already gave everything"),
            ],
        ),
        "verse_refs": ["Genesis 2:16", "Genesis 3:2", "Psalm 103:1", "Romans 5:17"],
    },
    {
        "title": "2️⃣ Open Your Eyes — Provision Is Near",
        "intro": (
            "Hagar in the wilderness — water was <strong>right beside her</strong>. "
            "God opened her eyes. Adam's eyes opened to <em>lack</em>; communion opens eyes to <strong>provision</strong>."
        ),
        "bullets": [
            "💧 Genesis 21:19 — God opened her eyes; she saw the well",
            "👁️ Genesis 3:7 — knowledge tree opened eyes to nakedness and poverty",
            "🍞 Luke 24:31 — Emmaus: eyes opened when they broke bread",
            "🎯 Holy Communion opens eyes to Jesus and His blessing",
        ],
        "verse_refs": ["Genesis 21:19", "Genesis 3:7", "Luke 24:31"],
    },
    {
        "title": "3️⃣ Redeemed From Bondage — Passover Lamb",
        "intro": (
            "430 years in bondage — Moses' plagues could not free them. "
            "Blood on the doorpost and eating the lamb — <strong>first Holy Communion</strong> — broke every chain."
        ),
        "bullets": [
            "🩸 Exodus 12:7–9 — blood on lintel; eat the roasted lamb",
            "⛓️ Next morning: bondage broken, gold and silver restored",
            "✝️ Jesus: I am the true Lamb — eat My body, drink My blood",
            "🚪 Angel of death cannot enter when blood is applied",
        ],
        "verse_refs": ["Exodus 12:7", "Exodus 12:40"],
    },
    {
        "title": "4️⃣ Heal — Zero Feeble Among Their Tribes",
        "intro": (
            "Psalm 105:37 — after Passover, <strong>not one feeble person</strong> among millions. "
            "Discern the body: bread broken for <em>healing</em>; blood shed for forgiveness."
        ),
        "bullets": [
            "🩹 Isaiah 53 — His body broken so you are healed",
            "🍷 Blood = forgiveness of sins; body = healing — do not mix them up",
            "📖 Matthew 26 — new covenant in blood; body reason kept for faith-seekers",
            "💪 Worthy manner = discerning what body and blood each accomplish",
        ],
        "verse_refs": ["Psalm 105:37", "Matthew 26:26", "Isaiah 53"],
    },
    {
        "title": "🌳 Eat the Tree of Life — Reverse Adam's Curse",
        "intro": (
            "Adam ate the tree of knowledge — death entered by <strong>eating</strong>. "
            "God reverses the curse through eating: communion proclaims the Lord's death till He comes."
        ),
        "bullets": [
            "🌳 Tree of life = Jesus — Adam never ate it; we can",
            "🍞 Eat as often as needed — house to house breaking bread",
            "👑 Kings and priests — you may break bread as priest",
            "✨ Go higher than Adam — eat life, live sickness-free, pain-free, sorrow-free",
        ],
        "table": (
            ["Tree of knowledge", "Tree of life (Communion)"],
            [
                ("Adam ate — curse entered", "Eat Christ — <strong>curse reversed</strong>"),
                ("Eyes opened to lack", "Eyes opened to <strong>provision</strong>"),
                ("Reward system", "<strong>Gift</strong> — freely eat"),
            ],
        ),
        "verse_refs": ["1 Corinthians 11:23", "1 Corinthians 11:26"],
    },
    {
        "title": "🛡️ Discern the Body — Strong, No Sickness, Long Life",
        "intro": (
            "Worthy manner means knowing what the <strong>body</strong> and <strong>blood</strong> accomplish. "
            "Proclaim His death till He comes — weakness and sickness end when you discern correctly."
        ),
        "bullets": [
            "🍞 Body broken for <strong>healing</strong> — Isaiah 53",
            "🩸 Blood shed for <strong>forgiveness</strong> — do not confuse the two",
            "🏠 Break bread house to house — eat whenever you need strength",
            "👑 Kings and priests — you may take communion at home in need",
        ],
        "verse_refs": ["1 Corinthians 11:27", "1 Corinthians 11:28", "Matthew 26:26"],
    },
    {
        "title": "🍷 As Often As You Eat — Proclaim His Death",
        "intro": (
            "1 Corinthians 11:23–32 — as often as you eat, you proclaim the Lord's death. "
            "Judge yourself, discern the body, and receive strength — not weakness."
        ),
        "bullets": [
            "📖 1 Corinthians 11:23–26 — do this in remembrance; proclaim till He comes",
            "🩸 New covenant in blood — sins forgiven, not earned",
            "🍞 Body broken — healing is the body's purpose at communion",
            "💪 Strong, no sickness, long life — the promise when you discern rightly",
        ],
        "ordered": [
            "1️⃣ <strong>Remember free</strong> — prevent falling",
            "2️⃣ <strong>Open eyes</strong> — see provision near",
            "3️⃣ <strong>Redeem bondage</strong> — Passover lamb",
            "4️⃣ <strong>Heal</strong> — discern the Lord's body",
        ],
        "verse_refs": ["1 Corinthians 11:23", "1 Corinthians 11:30", "Psalm 105:37"],
    },
    {
        "title": "🌳 Two Trees — Eat Life, Reverse the Curse",
        "intro": (
            "Adam ate knowledge of good and evil — curse by <strong>eating</strong>. "
            "God reverses through communion: eat the <strong>Tree of Life</strong> — "
            "Jesus, the way, truth, and life."
        ),
        "bullets": [
            "🌳 Tree of knowledge = reward system; Tree of life = Christ Himself",
            "🍞 Eat as often as needed — house to house breaking bread",
            "👑 Kings and priests — proclaim His death wherever you eat",
            "✨ Go higher than Adam — he never ate life; you can",
        ],
        "table": (
            ["Unworthy manner", "Worthy manner"],
            [
                ("Body = forgiveness only", "Body = <strong>healing</strong>; blood = forgiveness"),
                ("Don't know what body is for", "<strong>Discern</strong> the Lord's body"),
                ("Weak, sick, sleep early", "<strong>Strong</strong>, no sickness, long life"),
            ],
        ),
        "verse_refs": ["Exodus 12:7", "Exodus 12:40", "Luke 24:31"],
    },
]

MIRACLES_NEXT_FLOW: list[dict[str, Any]] = [
    {
        "title": "🚀 Go to the Next Level — Leave the Loop",
        "intro": (
            "God did not call you to repeat the same situation for years. "
            "Today you may be in need — tomorrow He wants you <strong>helping the needy</strong>. "
            "That next level is miracles."
        ),
        "bullets": [
            "🔄 Normal life = wake, work, pay bills, repeat — God wants transformation",
            "🐟 Peter: daily fish → <strong>fishes of men</strong> — ten fishing for you",
            "🌑 Cross darkness → your life in <strong>brightness</strong>",
            "✨ Do not passively wait — <strong>seek</strong> miracles actively",
        ],
    },
    {
        "title": "🔍 Seek His Face and His Strength",
        "intro": (
            "1 Chronicles 16:11 — seek the Lord <strong>and His strength</strong>. "
            "The Father's glory shows when you receive what He saved for you at the cross."
        ),
        "bullets": [
            "💪 Strength revealed when you are healed and at the next level",
            "🙏 Daily prayer: <em>I want the next level — not this loop</em>",
            "👥 Twelve spies — only two expected miracles and entered Canaan",
            "❤️ God is close to the <strong>brokenhearted</strong> — He came to heal you",
        ],
        "verse_refs": ["1 Chronicles 16:11"],
    },
    {
        "title": "🏔️ Miracles Are Easy — Numbers 13:30",
        "intro": (
            "Caleb quieted the people: <em>we are well able — it is easy to overcome</em>. "
            "Jericho's wall was vehicle-thick — they walked, praised, and shouted; it fell."
        ),
        "bullets": [
            "🗣️ Speak: easy to conquer sickness, bondage, exams, promotion",
            "🎺 Seven days of praise — not JCBs and human preparation",
            "👁️ Ten spies saw natural impossibility; two saw God's miracle",
            "📈 Going to the next level can be as easy as walking and shouting",
        ],
        "table": (
            ["Natural eyes", "Faith eyes"],
            [
                ("Giants too big — impossible", "<strong>Easy</strong> to overcome"),
                ("Upskill and strive", "Praise and <strong>stand still</strong>"),
                ("Stay in same level", "<strong>Next level</strong> by grace"),
            ],
        ),
        "verse_refs": ["Numbers 13:30"],
    },
    {
        "title": "🛑 Stand Still — See the Salvation of the Lord",
        "intro": (
            "Exodus 14 — Red Sea ahead, army behind. "
            "<em>Stand still</em> — salvation (<strong>Yeshua</strong>) will accomplish deliverance today."
        ),
        "bullets": [
            "☮️ Psalm 46:10 — be still and know that I am God",
            "🎒 Matthew 11 — come unto Me, all who are heavy laden",
            "365× do not fear — stand still when afraid",
            "🛑 Standing still = trusting while the storm rages",
        ],
        "verse_refs": ["Exodus 14:13", "Psalm 46:10"],
    },
    {
        "title": "🙏 Humble Yourself — The Tax Collector's Miracle",
        "intro": (
            "Luke 18 — Pharisee trusted fasting and tithes; tax collector said "
            "<em>be merciful to me, a sinner</em>. The humble man went home <strong>justified</strong>."
        ),
        "bullets": [
            "🙏 Not eligible by skill — eligible by <strong>His grace</strong>",
            "🛑 Trust God in the storm — do not strive in your own strength",
            "✨ Humble faith makes miracles <strong>easy</strong>",
            "👑 Exalt yourself → humbled; humble yourself → exalted",
        ],
        "verse_refs": ["Luke 18", "Ephesians 2:8"],
    },
    {
        "title": "🎁 Miracles Are Free — Grace, Not Wages",
        "intro": (
            "Ephesians 2:8–9 — saved by grace through faith; not of works. "
            "The righteous receive miracles as a <strong>gift</strong> — standing still trusts His finished work."
        ),
        "bullets": [
            "🎁 Miracle is the greatest gift — righteousness unlocks every request",
            "🗣️ Not by my obedience — by <strong>His obedience</strong> I am righteous",
            "💪 Nothing too hard for the Lord — easy through God",
            "📋 Four steps: seek → easy → stand still → free by grace",
        ],
        "ordered": [
            "🔍 <strong>Seek</strong> miracles — next level daily",
            "🏔️ Confess miracles are <strong>easy</strong>",
            "🛑 <strong>Stand still</strong> — see Yeshua",
            "🎁 Receive by <strong>grace</strong> — miracles are free",
        ],
        "table": (
            ["World's way", "God's way"],
            [
                ("Prepare harder, upskill, strive", "<strong>Stand still</strong> — see salvation"),
                ("Earn miracle by works", "Miracles are <strong>free</strong> — gift of God"),
                ("Same level for years", "<strong>Next level</strong> through humble faith"),
            ],
        ),
        "verse_refs": ["Ephesians 2:8", "Ephesians 2:9"],
    },
    {
        "title": "🌟 Nothing Too Hard — Next Level by Grace",
        "intro": (
            "Genesis 18:14 — is anything too hard for the Lord? "
            "Hebrews 4:1 — enter His rest; the miracle is already finished."
        ),
        "bullets": [
            "📖 Romans 11:6 — grace excludes boasting in works",
            "✝️ Galatians 6:14 — glory only in the cross",
            "🌴 Psalm 92:12 — righteous flourish when they trust His strength",
            "🙏 Declare: healthy, next level, blessed — miracles are free",
        ],
        "verse_refs": ["Genesis 18:14", "Romans 11:6", "Romans 4:4", "James 2:10", "Galatians 6:14", "Romans 5:19", "Psalm 92:12", "Hebrews 4:1", "1 Corinthians 1:27"],
    },
    {
        "title": "📖 Faith Comes by Hearing — Go to the Next Level",
        "intro": (
            "Do not remain in the same situation — hear, believe, stand still, receive. "
            "1 Corinthians 1:27 — God chose the weak to confound the wise."
        ),
        "bullets": [
            "👂 Faith comes by hearing the word of Christ again and again",
            "🚀 Next level: from need to giving, from employee to employer",
            "🛑 Stand still — Yeshua accomplishes salvation today",
            "🎁 Ephesians 2:8–9 — miracle is a gift; boast only in the cross",
        ],
        "table": (
            ["Pharisee prayer", "Tax collector prayer"],
            [
                ("I fast, I tithe — I deserve", "<em>Be merciful — I am a sinner</em>"),
                ("Trusts own effort", "Trusts <strong>grace alone</strong>"),
                ("Went home unchanged", "Went home <strong>justified</strong>"),
            ],
        ),
        "verse_refs": ["1 Corinthians 1:27", "1 Corinthians 1:28", "Ephesians 2:8"],
    },
]

SHAME_FLOW: list[dict[str, Any]] = [
    {
        "title": "🛡️ Whoever Believes Will Not Be Put to Shame",
        "intro": (
            "Romans 10 opens with a promise for every believer: "
            "<strong>whoever believes on Him will not be put to shame</strong>. "
            "Shame is not God's plan for your body, finances, or future."
        ),
        "bullets": [
            "📖 Romans 9:33 — stumbling stone for some; <strong>no shame</strong> for believers",
            "🙏 Romans 10:1 — Paul's heart: that Israel may be saved",
            "✝️ Salvation is for <strong>whoever calls</strong> on the Lord",
            "💚 Shame ends where <mark style=\"background-color:#bbf7d0\"><strong>faith in Christ</strong></mark> begins",
        ],
        "verse_refs": ["Romans 9:33", "Romans 10:1", "Romans 10:11", "Romans 10:13"],
    },
    {
        "title": "📤 Step 1 — Sent: How Shall They Preach?",
        "intro": (
            "Faith does not start with your effort alone. "
            "Romans 10:15 asks the first link in the chain: "
            "<strong>how shall they preach unless they are sent?</strong>"
        ),
        "ordered": [
            "📤 <strong>Sent</strong> — gospel messengers commissioned by God",
            "👂 <strong>Hear</strong> — faith comes by hearing",
            "👁️ <strong>See</strong> — eyes of the heart enlightened",
            "🗣️ <strong>Speak</strong> — righteousness of faith speaks",
        ],
        "table": (
            ["Self-effort path", "Faith chain path"],
            [
                ("Try to believe alone", "<strong>Sent</strong> preachers bring the word"),
                ("Random scrolling", "<strong>Hear</strong> the word of God"),
                ("Focus on problems", "<strong>See</strong> with heart-faith"),
                ("Stay silent", "<strong>Speak</strong> what you believe"),
            ],
        ),
        "verse_refs": ["Romans 10:15", "Malachi 3:10"],
    },
    {
        "title": "👂 Step 2 — Hear: Faith Comes by Hearing",
        "intro": (
            "Romans 10:17 is the engine of the Christian life: "
            "<strong>faith comes by hearing, and hearing by the word of God</strong>. "
            "You cannot skip hearing and still expect strong faith."
        ),
        "bullets": [
            "📖 Romans 10:14 — how shall they believe without hearing?",
            "👂 Continuous hearing builds continuous faith",
            "🎁 Tithe and storehouse — open heaven for provision to <strong>send</strong> the word",
            "✝️ Hear Christ, not mixed law-and-grace messages",
        ],
        "verse_refs": ["Romans 10:14", "Romans 10:17"],
    },
    {
        "title": "👁️ Step 3 — See with the Eyes of Your Heart",
        "intro": (
            "Believing is not blind optimism. "
            "Ephesians 1:18 prays that the <strong>eyes of your heart</strong> "
            "may be enlightened to know the hope of His calling."
        ),
        "bullets": [
            "👁️ See healing while symptoms remain — Abraham against hope believed",
            "💰 See provision while bills exist — faith sees unseen realities",
            "🕊️ See freedom while trouble surrounds you",
            "📖 Hope that is seen is not hope — Romans 8:24",
        ],
        "verse_refs": ["Ephesians 1:18", "Romans 10:14"],
    },
    {
        "title": "🗣️ Step 4 — Speak: Righteousness of Faith Speaks",
        "intro": (
            "Romans 10:6–8 — the <strong>righteousness of faith speaks</strong>. "
            "Do not say in your heart who will ascend; the word is near — in your mouth and heart."
        ),
        "bullets": [
            "🗣️ Mark 11:23 — say to the mountain; believe you receive",
            "💬 Speak the finished work, not the problem",
            "🔇 Faith dies when you stop speaking the word",
            "✝️ Confession aligns your mouth with your heart",
        ],
        "verse_refs": ["Romans 10:6", "Romans 10:8", "Mark 11:23"],
    },
    {
        "title": "📻 Have They Not Heard? — Mix Faith When You Hear",
        "intro": (
            "Hebrews 4:2 — the gospel was preached to them as to us, "
            "but the word did not profit them because it was "
            "<strong>not mixed with faith</strong> in those who heard."
        ),
        "table": (
            ["Israel's hearing", "Your hearing"],
            [
                ("Heard but sought righteousness by law", "Hear and <strong>believe</strong> unto righteousness"),
                ("Zeal without knowledge — Romans 10:2", "Knowledge of God's righteousness"),
                ("Stumbled at the stumbling stone", "Stand on the Rock — <strong>no shame</strong>"),
            ],
        ),
        "verse_refs": ["Romans 10:18", "Hebrews 4:2"],
    },
    {
        "title": "⚖️ True Faith vs Works of the Law",
        "intro": (
            "Romans 9:30–32 — Gentiles attained righteousness by faith; "
            "Israel pursued law-righteousness and stumbled. "
            "Christ is the <strong>end of the law</strong> for everyone who believes."
        ),
        "bullets": [
            "📖 Romans 10:3 — seeking to establish their own righteousness",
            "✝️ Romans 10:4 — Christ is the end of the law for believers",
            "🗣️ Romans 10:9–10 — confess with mouth, believe in heart",
            "🌍 Romans 10:12 — same Lord rich to all who call on Him",
        ],
        "verse_refs": ["Romans 9:30", "Romans 9:31", "Romans 9:32", "Romans 10:2", "Romans 10:3", "Romans 10:4"],
    },
    {
        "title": "🏆 Confess, Believe, Call — and You Will Not Be Ashamed",
        "intro": (
            "The sermon closes the Romans 10 chain: "
            "<strong>send, hear, see, speak</strong> — then faith produces victory. "
            "Whoever believes on Him <strong>will not be put to shame</strong>."
        ),
        "bullets": [
            "📤 First — align with sent gospel preaching",
            "👂 Second — hear the word daily",
            "👁️ Third — see with heart-faith",
            "🗣️ Fourth — speak what you believe",
        ],
        "verse_refs": ["Romans 10:9", "Romans 10:10", "Romans 10:11", "Romans 10:12"],
    },
    {
        "title": "📚 Romans 10 Chain — Study Notes",
        "intro": (
            "Paul contrasts wage-righteousness with "
            "<strong>gift-righteousness through faith</strong>."
        ),
        "bullets": [
            "📖 Shame belongs to the old covenant of self-justification — not to the believer in Christ",
            "👂 Hearing is not passive background noise; it is the furnace where faith is formed",
            "👁️ Heart-eyes see inheritance, healing, and peace before the body catches up",
            "🗣️ Speaking locks in what hearing deposited — silence lets faith leak away",
            "🎁 Tithe and storehouse imagery points to provision to <strong>send</strong> the gospel",
            "⚖️ Law-righteousness and faith-righteousness cannot be mixed without falling from grace",
            "🏆 Victory is not boasting in works but standing unashamed on the Rock",
        ],
        "quote": (
            "<em>\"Faith comes by hearing, and hearing by the word of God\" — "
            "build the chain daily: sent word, attentive hearing, faith-seeing, bold speaking.</em>"
        ),
        "verse_refs": ["Romans 10:17", "Romans 10:11"],
    },
    {
        "title": "🔊 Daily Practice — Build the Faith Chain",
        "intro": (
            "Put Romans 10 into daily practice under "
            "<strong>sent gospel preaching</strong>."
        ),
        "bullets": [
            "📅 Schedule hearing before striving",
            "📝 Write one promise; speak it three times today",
            "❓ In trouble ask: heard, seen, spoken — or only analysed?",
            "🛡️ Shame loses power when the chain stays intact",
        ],
        "ordered": [
            "🌅 Morning — hear one chapter; note one promise",
            "📝 Midday — speak that promise over your situation",
            "🌙 Evening — thank God for one answered word",
        ],
        "verse_refs": ["Romans 10:8", "Romans 10:10"],
    },
    {
        "title": "💚 Stand Unashamed Today",
        "intro": (
            "Whatever your past, your sickness, or your debt — "
            "<strong>whoever believes on Him will not be put to shame</strong>. "
            "That is not hype; it is Scripture. Build the chain today and stand."
        ),
        "verse_refs": ["Romans 10:11", "Romans 10:13"],
    },
]

RENEWING_MIND_FLOW: list[dict[str, Any]] = [
    {
        "title": "🧠 Be Transformed by Renewing Your Mind",
        "intro": (
            "Romans 12:2 — do not be conformed to this world, but "
            "<strong>be transformed by the renewing of your mind</strong>. "
            "Your outer life follows your inner thoughts."
        ),
        "bullets": [
            "📖 Proverbs 23:7 — as a man thinks in his heart, so is he",
            "🎁 Romans 12:1 — present your body a living sacrifice",
            "💚 God's will: good, acceptable, and perfect",
            "🔄 Transformation is inward first, outward second",
        ],
        "verse_refs": ["Romans 12:1", "Romans 12:2", "Proverbs 23:7"],
    },
    {
        "title": "✝️ Key 1 — Obedience of Christ",
        "intro": (
            "Romans 5:19 — by one Man's obedience many are made righteous. "
            "Your standing is not built on your track record but on "
            "<strong>Christ's obedience</strong>."
        ),
        "table": (
            ["Works mindset", "Obedience-of-Christ mindset"],
            [
                ("Am I good enough?", "<strong>Made righteous</strong> by one Man's obedience"),
                ("Fight in the flesh", "Bring every thought captive to Christ"),
                ("Condemnation when weak", "Reconciled — saved by His life"),
            ],
        ),
        "verse_refs": ["Romans 5:10", "Romans 5:19", "2 Corinthians 10:5"],
    },
    {
        "title": "💛 Key 2 — Love of the Father",
        "intro": (
            "Romans 5:5 — the <strong>love of God is poured out</strong> in our hearts "
            "by the Holy Spirit. 1 John 2:15 — do not love the world; "
            "the love of the Father is not in worldly pursuit."
        ),
        "bullets": [
            "💛 Father's love is already in you — not earned daily",
            "🌍 Worldly conformity blocks renewed thinking",
            "🩺 3 John 2 — prosper and be in health as your soul prospers",
            "👣 Walk as beloved children, not orphans",
        ],
        "verse_refs": ["Romans 5:5", "1 John 2:15", "3 John 2"],
    },
    {
        "title": "🕊️ Key 3 — Forgiveness of God",
        "intro": (
            "Luke 7:47 — she loved much because she was forgiven much. "
            "The measure of forgiveness you receive shapes the "
            "<strong>love and peace</strong> flowing from your renewed mind."
        ),
        "bullets": [
            "🕊️ Receive full forgiveness — do not live in partial guilt",
            "💚 Much forgiven → much love → much transformation",
            "📖 Romans 8:1 — no condemnation in Christ Jesus",
            "🤝 Forgiven people become helpers, givers, and kind",
        ],
        "verse_refs": ["Luke 7:47", "Romans 8:1"],
    },
    {
        "title": "⛵ Peace in the Storm — Christ Asleep, Disciples Afraid",
        "intro": (
            "In the storm, disciples panicked while Jesus slept in peace. "
            "Your circumstance is not the first battle — "
            "<strong>your thought life</strong> is."
        ),
        "bullets": [
            "🌊 Circumstances rage outside; peace can reign inside",
            "😌 Renewed mind stays calm before the miracle",
            "✝️ Jesus rebuked the wind — peace commands the storm",
            "🧠 Win the inner battle first",
        ],
        "verse_refs": ["Mark 4:39", "Philippians 4:7"],
    },
    {
        "title": "🛡️ Put On the Whole Armour of God",
        "intro": (
            "Ephesians 6:11–12 — we do not wrestle against flesh and blood. "
            "People are not your deepest enemy; "
            "<strong>strongholds in the mind</strong> are."
        ),
        "table": (
            ["Flesh-and-blood fight", "Spiritual reality"],
            [
                ("Blame people around you", "Wrestle against principalities and powers"),
                ("Try harder in your strength", "<strong>Put on</strong> God's armour"),
                ("Anxiety and confusion", "Stand — mind renewed in Christ"),
            ],
        ),
        "verse_refs": ["Ephesians 6:11", "Ephesians 6:12"],
    },
    {
        "title": "🔄 Romans 12 Order — Obedience, Love, Forgiveness",
        "intro": (
            "Romans 12 lays the order of transformation: "
            "focus on <strong>Christ's obedience</strong>, "
            "the <strong>Father's love</strong>, and "
            "<strong>God's forgiveness</strong> — then your life reflects His character."
        ),
        "ordered": [
            "✝️ <strong>Obedience of Christ</strong> — righteous standing",
            "💛 <strong>Love of the Father</strong> — poured out in your heart",
            "🕊️ <strong>Forgiveness of God</strong> — much love, much change",
            "🛡️ <strong>Whole armour</strong> — stand against the devil's wiles",
        ],
        "verse_refs": ["Romans 12:2", "Romans 5:5", "Romans 5:19"],
    },
    {
        "title": "🌅 Live Transformed — Healthy, Prosperous, Upward",
        "intro": (
            "God wants your life transformed — health, prosperity, and upward direction. "
            "That begins when your mind is renewed in "
            "<strong>obedience, love, and forgiveness</strong>."
        ),
        "bullets": [
            "📈 Life goes upward when thoughts align with gospel truth",
            "💪 Strongholds fall when Christ's obedience is your anchor",
            "🤲 You become a helper and giver — reflecting His character",
            "🎯 Three keys daily: obedience, love, forgiveness",
        ],
        "verse_refs": ["Romans 12:1", "Ephesians 6:11"],
    },
    {
        "title": "📚 Mind Renewal — Study Notes",
        "intro": (
            "Romans 12: your mind is the control room — "
            "<strong>renewed thinking</strong> precedes renewed living."
        ),
        "bullets": [
            "🧠 Proverbs 23:7 — thinking shapes being; change thought patterns first",
            "✝️ Christ's obedience is your righteousness — stop re-trying what He finished",
            "💛 The Father's love is already poured out — you are not persuading Him to love you",
            "🕊️ Forgiveness received fully produces love that overflows to others",
            "⛵ Peace in the storm models faith: calm heart, then calm sea",
            "🛡️ Armour of God addresses spiritual warfare — not arguing with people as the main enemy",
            "🔄 Transformation shows as kindness, generosity, and Christlike character",
        ],
        "quote": (
            "<em>\"Be transformed by the renewing of your mind\" — "
            "obedience of Christ, love of the Father, forgiveness of God: "
            "the three lenses for every renewed thought.</em>"
        ),
        "verse_refs": ["Romans 12:2", "Romans 5:19", "Romans 5:5"],
    },
    {
        "title": "🧭 World Conformity vs Gospel Renewal",
        "intro": (
            "Conformity sneaks in through worry and lack-talk. "
            "Romans 12:2 calls you to <strong>prove</strong> God's good will."
        ),
        "bullets": [
            "🗣️ Healthier speech follows renewed thinking",
            "🤲 Generous action flows from forgiven hearts",
            "☮️ Stable peace — confidence in finished work",
            "💛 Three meditations: obedience, love, forgiveness",
        ],
        "table": (
            ["Conformed thinking", "Renewed thinking"],
            [
                ("\"This sickness is my portion\"", "<strong>By His stripes</strong> — health is my heritage"),
                ("\"I must earn God's favour\"", "Love <strong>poured out</strong> already"),
                ("\"My past defines me\"", "<strong>Forgiven much</strong> — love much"),
                ("\"People are my enemy\"", "<strong>Armour of God</strong> — spiritual battle"),
            ],
        ),
        "verse_refs": ["Romans 12:2", "Luke 7:47"],
    },
    {
        "title": "🙏 Daily Renewal Prayer Pattern",
        "intro": (
            "Close each day with the Romans 12 triad — "
            "<strong>obedience, love, forgiveness</strong>."
        ),
        "bullets": [
            "✝️ Thank God for Christ's obedience — you are righteous",
            "💛 Receive the Father's love afresh — kindness outward",
            "🕊️ Rehearse forgiveness until condemnation leaves",
            "🛡️ Armour on; speak peace over your storm",
        ],
        "ordered": [
            "✝️ Thank God for obedience that made you righteous",
            "💛 Receive the Father's love — let it displace fear",
            "🕊️ Confess full forgiveness — love much, give much",
            "🛡️ Stand in armour — thoughts captive to Christ",
        ],
        "verse_refs": ["Ephesians 6:12", "Philippians 4:7", "Romans 8:1"],
    },
    {
        "title": "💚 Character of the Renewed Mind",
        "intro": (
            "A renewed mind is visible. You become helpful, kind, and generous — "
            "not because you try harder, but because obedience, love, and forgiveness "
            "have rewired your inner conversation. You reflect Christ: His obedience, "
            "His love, His forgiveness. That is the fruit Romans 12 promises when "
            "transformation starts in the mind and finishes in daily character."
        ),
        "bullets": [
            "🤲 Helper — you lift others because you are lifted",
            "💛 Kind — love of the Father spills outward",
            "🎁 Giver — forgiven people give freely",
            "✝️ Christlike — obedience of Christ is your mirror",
        ],
        "verse_refs": ["Romans 12:1", "Romans 5:19", "Luke 7:47"],
    },
    {
        "title": "🎯 Three Keys — Recap",
        "intro": (
            "Romans 12 closes with practical armour — but the sequence is clear."
        ),
        "ordered": [
            "✝️ <strong>Obedience of Christ</strong> — righteous standing",
            "💛 <strong>Love of the Father</strong> — poured out in your heart",
            "🕊️ <strong>Forgiveness of God</strong> — love much, give much",
            "🛡️ <strong>Whole armour</strong> — stand; mind renewed",
        ],
        "table": (
            ["Old mind", "Renewed mind"],
            [
                ("Condemnation", "<strong>No condemnation</strong> in Christ"),
                ("Fear of lack", "Father's love <strong>poured out</strong>"),
                ("Bitterness", "<strong>Forgiven</strong> — helper and giver"),
            ],
        ),
        "verse_refs": ["Romans 12:2", "Romans 8:1", "Ephesians 6:11"],
    },
]

FLOW_BY_SLUG: dict[str, list[dict[str, Any]]] = {
    "full-restoration-hundred-percent-in-christ": FULL_RESTORATION_FLOW,
    "gospel-of-christ-hear-right-covenant": GOSPEL_FLOW,
    "miracles-are-easy-stand-still": MIRACLES_STAND_FLOW,
    "freedom-from-troubles-righteousness-apart-from-works": FREEDOM_TROUBLES_FLOW,
    "be-fruitful-and-multiply-every-area": FRUITFUL_FLOW,
    "why-delay-abraham-instant-blessing": DELAY_FLOW,
    "freedom-in-the-spirit-son-and-father": FREEDOM_SPIRIT_FLOW,
    "why-listen-to-the-word-of-god": LISTEN_FLOW,
    "heir-of-the-world-through-faith-not-law": HEIR_FLOW,
    "holy-communion-one-reason-for-sickness": COMMUNION_FLOW,
    "miracles-are-easy-next-level-faith": MIRACLES_NEXT_FLOW,
    "he-will-not-put-to-shame-romans-10-faith-chain": SHAME_FLOW,
    "renewing-mind-obedience-love-forgiveness-romans-12": RENEWING_MIND_FLOW,
}


def _verse_key(v: dict) -> str:
    ref = re.sub(r"\s+", " ", (v.get("ref") or "").strip().lower())
    if ref:
        return ref
    text = (v.get("text") or "")[:60].lower()
    return text


def _match_ref(v: dict, wanted: str) -> bool:
    ref = (v.get("ref") or "").strip().lower()
    text = (v.get("text") or "").lower()
    w = wanted.lower().strip()
    if ref:
        if w in ref or ref in w:
            return True
        # "Matthew 6" matches ref "Matthew 6:33" prefix
        if w.split(":")[0] in ref:
            return True
    if ":" in w and w in text:
        return True
    return False


def _pick_verses(verses: list[dict], refs: list[str], seen: set[str]) -> list[dict]:
    picked: list[dict] = []
    for wanted in refs:
        candidates = [
            v for v in verses
            if _verse_key(v) not in seen and _match_ref(v, wanted)
        ]
        if not candidates:
            continue
        candidates.sort(
            key=lambda v: (
                0 if re.search(r"\d+:\d+", v.get("ref") or "") else 1,
                len(v.get("ref") or ""),
            )
        )
        v = candidates[0]
        picked.append(v)
        seen.add(_verse_key(v))
    return picked


def _is_scripture_verse(v: dict) -> bool:
    ref = (v.get("ref") or "").strip()
    text = (v.get("text") or "").strip()
    if not text or len(text) < 15:
        return False
    if re.search(r"\d+:\d+", ref):
        return True
    if re.search(r"\d+:\d+", text):
        return True
    return len(text) > 80


def build_transcript_flow(job: SermonJob, pack: SermonPack, flow: list[dict[str, Any]]) -> str:
    ypath = job.yaml_path(pack.pack_dir)
    verses = deck_verses(ypath)
    anchor = next((v for v in verses if _is_scripture_verse(v)), verses[0] if verses else None)
    anchor_body = b.apply_highlights(anchor["text"].strip().strip('"'), anchor.get("highlights") or []) if anchor else job.title
    anchor_ref = (anchor or {}).get("ref", "")

    parts = [
        b.h3(f"💯 {job.title}"),
        b.quote(f'<em>"{anchor_body}"</em>' + (f" — <strong>{anchor_ref}</strong>" if anchor_ref else "")),
        b.highlight_key(),
        b.separator(),
    ]

    seen: set[str] = set()
    for section in flow:
        parts.append(b.h2(section["title"]))
        if section.get("intro"):
            parts.append(b.paragraph(section["intro"]))
        if section.get("ordered"):
            parts.append(b.ordered_list(section["ordered"]))
        if section.get("bullets"):
            parts.append(b.bullet_list(section["bullets"]))
        if section.get("table"):
            hdrs, rows = section["table"]
            parts.append(b.table(hdrs, rows))
        if section.get("quote"):
            parts.append(b.quote(section["quote"]))
        for v in _pick_verses(verses, section.get("verse_refs", []), seen):
            if _is_scripture_verse(v):
                parts.append(b.verse_block(v["ref"], v["text"], v.get("highlights")))
        parts.append(b.separator())

    # Weave any deck verses not yet cited — satisfies YAML audit and word ratio
    remaining = [
        v for v in verses
        if _is_scripture_verse(v) and _verse_key(v) not in seen
    ]
    if remaining:
        parts.append(b.h2("📖 Scripture Foundations from the Deck"))
        parts.append(b.paragraph(
            "These verses anchor today's teaching — read them as "
            "<strong>gospel promises</strong>, not a wage list."
        ))
        for v in remaining:
            parts.append(b.verse_block(v["ref"], v["text"], v.get("highlights")))
            seen.add(_verse_key(v))
        parts.append(b.separator())

    parts.extend([
        b.h2("🎯 The Takeaway"),
        b.ordered_list(job.takeaway or ["💯 <strong>Full restoration</strong> — 100%, not partial."]),
        b.separator(),
        b.footer(job.topic),
    ])
    return "\n\n".join(parts)
