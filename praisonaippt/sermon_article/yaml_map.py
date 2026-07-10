"""Transcript ↔ YAML deck mapping audit for sermon packs."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_yaml_refs(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    title = ""
    sections: list[str] = []
    refs: list[str] = []
    for line in text.splitlines():
        if line.startswith("presentation_title:"):
            title = line.split(":", 1)[1].strip().strip("\"'")
        if line.strip().startswith("- section:"):
            sections.append(line.split(":", 1)[1].strip().strip("'\""))
        m = re.search(r"reference:\s*(.+)", line)
        if m:
            refs.append(m.group(1).strip().strip("'\""))
    return {"title": title, "sections": sections, "refs": refs}


def sermon_signals(transcript: str) -> list[str]:
    t = transcript.lower()
    signals: list[str] = []
    patterns = [
        ("job 23", "Job 23 / God's will"),
        ("jeremiah 29", "Jeremiah 29"),
        ("first adam", "First Adam"),
        ("last adam", "Last Adam"),
        ("psalm 34", "Psalm 34"),
        ("full restoration", "full restoration"),
        ("fully restore", "full restoration"),
        ("fruitful and multiply", "be fruitful and multiply"),
        ("why delay", "why delay"),
        ("abraham", "Abraham"),
        ("el shaddai", "El Shaddai"),
        ("heir of the world", "heir of the world"),
        ("three level", "3 levels of life"),
        ("milk and honey", "milk and honey"),
        ("broken heart", "broken hearted / miracles"),
        ("miracles are easy", "miracles are easy"),
        ("stand still", "stand still (miracles)"),
        ("break your curse", "break curse"),
        ("generational curse", "generational curse"),
        ("galatians 5", "Galatians 5"),
        ("christ is of no effect", "Gal 5:4 Christ of no effect"),
        ("holy communion", "Holy Communion"),
        ("1 corinthians 11", "1 Cor 11 communion"),
        ("only one reason", "only one reason sickness"),
        ("gospel", "gospel"),
        ("became a curse", "became a curse"),
        ("faith comes", "faith comes"),
        ("mark 11", "Mark 11"),
        ("deliverance", "deliverance / word of God"),
        ("1 corinthians 15:56", "1 Cor 15:56 death/sin"),
        ("righteousness of god", "righteousness of God"),
        ("exalt you", "God exalts you"),
        ("jude 3", "Jude 3"),
        ("phases of life", "phases of life"),
        ("woman with the issue of blood", "woman issue of blood"),
        ("isaiah 32", "Isaiah 32 peaceful dwelling"),
    ]
    for pat, label in patterns:
        if pat in t:
            signals.append(label)
    return signals


def ref_in_transcript(ref: str, transcript: str) -> bool:
    t = transcript.lower()
    ref_l = re.sub(r"\s*\([^)]+\)", "", ref.lower()).strip()
    if ref_l in t:
        return True
    m = re.match(r"([1-3]?\s?[a-z]+)\s*(\d+)[:\s]", ref_l)
    if m:
        book = m.group(1).replace(" ", "")
        ch = m.group(2)
        for v in (f"{book} {ch}", f"{book}{ch}", ref_l.split(":")[0] if ":" in ref_l else ref_l):
            if v in t:
                return True
    return False


def suggest_alternate(signals: list[str], current_yaml: str) -> str | None:
    rules = [
        ({"job 23", "jeremiah 29"}, "god_is_good_all_the_time.yaml — weak; consider dedicated Gods Will deck"),
        ({"3 levels", "isaiah 32", "milk and honey"}, "how_to_become_heir_of_the_world.yaml or reign_in_life.yaml"),
        ({"first adam", "last adam", "psalm 34"}, "first_adam_vs_last_adam.yaml ✓"),
        ({"full restoration", "fully restore"}, "full_restoration.yaml ✓"),
        ({"fruitful and multiply"}, "be_fruitful_and_multiply.yaml ✓"),
        ({"why delay", "abraham", "el shaddai"}, "why_delay.yaml ✓"),
        ({"break curse", "generational curse"}, "freedom_from_all_your_troubles.yaml"),
        ({"miracles are easy", "stand still"}, "miracles_are_easy.yaml ✓"),
        ({"holy communion", "1 cor 11"}, "only_one_reason_sickness.yaml ✓"),
        ({"gal 5:4", "galatians 5"}, "freedom_in_spirit.yaml"),
        ({"1 cor 15:56"}, "why_listen_word_of_god.yaml — partial"),
        ({"heir of the world"}, "how_to_become_heir_of_the_world.yaml ✓"),
        ({"faith comes"}, "great_faith.yaml ✓"),
        ({"became a curse", "gospel"}, "gospel.yaml ✓"),
    ]
    sig_set = {s.lower() for s in signals}
    for keys, suggestion in rules:
        if keys & sig_set or any(any(k in s.lower() for k in keys) for s in signals):
            if current_yaml not in suggestion:
                return suggestion
    return None


def score_mapping(item: dict[str, Any]) -> dict[str, Any]:
    yaml_path = Path(item["yaml_source"])
    txt_path = Path(item["transcript_txt"])
    transcript = txt_path.read_text(encoding="utf-8")
    yaml_info = load_yaml_refs(yaml_path)
    matched_refs = [r for r in yaml_info["refs"] if ref_in_transcript(r, transcript)]
    ref_ratio = len(matched_refs) / max(len(yaml_info["refs"]), 1)
    signals = sermon_signals(transcript)

    return {
        "video_id": item["video_id"],
        "pack_name": item["pack_name"],
        "yaml_file": yaml_path.name,
        "yaml_title": yaml_info["title"],
        "yaml_refs_total": len(yaml_info["refs"]),
        "yaml_refs_matched": len(matched_refs),
        "ref_match_pct": round(100 * ref_ratio, 1),
        "matched_refs": matched_refs[:12],
        "yaml_sections": yaml_info["sections"][:8],
        "sermon_signals": signals,
        "opening": transcript[:400].replace("\n", " "),
    }


def verdict_for(score: dict[str, Any], alt: str | None) -> str:
    if score["ref_match_pct"] >= 25 or len(score["matched_refs"]) >= 3:
        v = "OK"
    elif score["ref_match_pct"] >= 10:
        v = "WEAK"
    else:
        v = "MISMATCH"
    if alt and "✓" not in alt:
        if v == "OK":
            return "REVIEW"
        if v == "WEAK":
            return "REVIEW"
    return v


def audit_pack_map(map_json: Path, *, report_path: Path | None = None) -> list[dict[str, Any]]:
    items = json.loads(map_json.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for i, item in enumerate(items, 1):
        r = score_mapping(item)
        r["index"] = i
        alt = suggest_alternate(r["sermon_signals"], r["yaml_file"])
        r["alternate_suggestion"] = alt
        r["verdict"] = verdict_for(r, alt)
        results.append(r)
    if report_path:
        report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results
