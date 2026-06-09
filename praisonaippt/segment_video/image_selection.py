"""Image selection — relevance filter, per-sentence pairing, cue ordering."""
from __future__ import annotations

import re
from typing import Any


def tokenise(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def script_alignment(script: str, image: dict) -> float:
    blob = " ".join(
        str(image.get(k, ""))
        for k in ("vision_description", "relevance_reason", "asset_type")
    )
    script_tokens = tokenise(script)
    image_tokens = tokenise(blob)
    if not script_tokens:
        return 0.0
    overlap = len(script_tokens & image_tokens) / len(script_tokens)
    relevance = float(image.get("topic_relevance_score") or 0)
    return round(0.45 * relevance + 0.55 * min(overlap * 4, 1.0), 3)


def sentence_groups(script: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", script.strip()) if p.strip()]
    return parts or [script.strip()]


def is_relevant_image(image: dict, rules: dict) -> bool:
    label = str(image.get("topic_relevance_label") or "")
    score = float(image.get("topic_relevance_score") or 0)
    required = rules.get("require_topic_relevance_label", "relevant")
    if required and label == required:
        return True
    if required and label and label not in ("", required):
        return False
    return score >= float(rules.get("min_topic_relevance", 0.7))


def filter_relevant(images: list[dict], rules: dict) -> list[dict]:
    relevant = [img for img in images if is_relevant_image(img, rules)]
    if relevant:
        return relevant
    if rules.get("no_fallback_to_marginal"):
        return []
    return images[:3]


CHART_SPEECH = re.compile(
    r"\b(throughput|benchmark|inference|five times|5x|cost|performance|accuracy|mmlu|chart|efficiency)\b",
    re.I,
)


def asset_type_boost(sentence: str, image: dict) -> float:
    """Prefer charts when speech mentions benchmarks; penalise mismatched types."""
    at = str(image.get("asset_type") or "")
    if CHART_SPEECH.search(sentence):
        if at == "benchmark_chart":
            return 0.18
        if at in ("architecture_diagram", "og_hero") and re.search(r"throughput|5x|five times|benchmark", sentence, re.I):
            return -0.10
    return 0.0


def rank_images(images: list[dict], sentence: str, rules: dict) -> list[tuple[float, dict]]:
    scored = [
        (script_alignment(sentence, img) + asset_type_boost(sentence, img), img)
        for img in images
    ]
    scored.sort(
        key=lambda x: (
            -x[0],
            -float(x[1].get("editorial_rank") or 999),
            -float(x[1].get("topic_relevance_score") or 0),
        ),
    )
    return scored


def pick_for_sentence(
    sentence: str,
    images: list[dict],
    rules: dict,
    used_files: set[str],
) -> dict | None:
    for score, img in rank_images(images, sentence, rules):
        if img["filename"] in used_files:
            continue
        if score < float(rules.get("min_script_alignment", 0.35)):
            continue
        if not is_relevant_image(img, rules):
            continue
        return {
            **img,
            "script_alignment": score,
            "script_fragment": sentence,
            "alignment_method": "heuristic",
        }
    return None


def build_cue_plan(
    script: str,
    images: list[dict],
    rules: dict,
) -> tuple[list[dict], list[dict]]:
    """Return (accepted cue picks, rejected images with reasons)."""
    relevant_pool = filter_relevant(images, rules)
    sentences = sentence_groups(script)
    max_cues = int(rules.get("max_cues_per_segment", 4))
    min_sentences = int(rules.get("multi_cue_requires_sentences", 1))

    rejected: list[dict] = []
    for img in images:
        if img not in relevant_pool and not any(
            r.get("source_filename") == img.get("filename") for r in rejected
        ):
            reason = "not_relevant"
            if img not in images[:3] or rules.get("no_fallback_to_marginal"):
                rejected.append({
                    "source_filename": img.get("filename"),
                    "topic_relevance_score": img.get("topic_relevance_score"),
                    "topic_relevance_label": img.get("topic_relevance_label"),
                    "reject_stage": "relevance_filter",
                    "reject_reason": reason,
                })

    cues: list[dict] = []
    used: set[str] = set()
    if len(sentences) >= min_sentences and len(relevant_pool) >= 1:
        for i, sentence in enumerate(sentences[:max_cues]):
            pick = pick_for_sentence(sentence, relevant_pool, rules, used)
            if not pick:
                continue
            used.add(pick["filename"])
            pick["sentence_index"] = i
            pick["narrative_order"] = len(cues) + 1
            pick["relevance_rank"] = len(cues) + 1
            cues.append(pick)

    # Second pass: assign best remaining image to uncovered sentences (lower bar)
    relaxed = float(rules.get("min_script_alignment_uncovered", 0.28))
    for i, sentence in enumerate(sentences[:max_cues]):
        if any(c.get("sentence_index") == i for c in cues):
            continue
        best_score, best_img = -1.0, None
        for score, img in rank_images(relevant_pool, sentence, rules):
            if img["filename"] in used:
                continue
            if score >= relaxed and score > best_score:
                best_score, best_img = score, img
        if best_img:
            used.add(best_img["filename"])
            cues.append({
                **best_img,
                "script_alignment": round(best_score, 3),
                "script_fragment": sentence,
                "sentence_index": i,
                "narrative_order": len(cues) + 1,
                "relevance_rank": len(cues) + 1,
                "alignment_method": "uncovered_fallback",
            })

    if not cues and relevant_pool:
        if rules.get("no_fallback_to_marginal"):
            best = None
            best_score = -1.0
            for img in relevant_pool:
                sc = script_alignment(script, img)
                if sc > best_score and is_relevant_image(img, rules):
                    best_score = sc
                    best = img
            if best:
                cues.append({
                    **best,
                    "script_alignment": best_score,
                    "script_fragment": script,
                    "sentence_index": 0,
                    "narrative_order": 1,
                    "relevance_rank": 1,
                    "alignment_method": "heuristic",
                    "validated": best_score >= float(rules.get("min_script_alignment", 0.35)),
                })
        else:
            best = max(relevant_pool, key=lambda img: script_alignment(script, img))
            score = script_alignment(script, best)
            cues.append({
                **best,
                "script_alignment": score,
                "script_fragment": script,
                "sentence_index": 0,
                "narrative_order": 1,
                "relevance_rank": 1,
                "alignment_method": "heuristic",
                "validated": score >= float(rules.get("min_script_alignment", 0.35)),
            })

    if not cues and images:
        tops = [fn for fn in (rules.get("_topic_top_picks") or []) if fn]
        for fn in tops:
            img = next((x for x in images if x.get("filename") == fn), None)
            if not img:
                continue
            score = script_alignment(script, img)
            cues.append({
                **img,
                "script_alignment": score,
                "script_fragment": script,
                "sentence_index": 0,
                "narrative_order": 1,
                "relevance_rank": 1,
                "alignment_method": "top_pick_fallback",
                "validated": score >= float(rules.get("min_script_alignment", 0.35)),
            })
            break

    if not cues and images and rules.get("_allow_marginal_manual"):
        best = max(images, key=lambda img: float(img.get("topic_relevance_score") or 0))
        if float(best.get("topic_relevance_score") or 0) > 0:
            score = script_alignment(script, best)
            cues.append({
                **best,
                "script_alignment": score,
                "script_fragment": script,
                "sentence_index": 0,
                "narrative_order": 1,
                "relevance_rank": 1,
                "alignment_method": "manual_asset_fallback",
                "validated": score >= float(rules.get("min_script_alignment", 0.35)),
            })

    return cues, rejected


def validate_cue(cue: dict, rules: dict, *, exists: bool) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if not exists:
        issues.append(f"missing file {cue.get('file')}")
    if float(cue.get("script_alignment") or 0) < float(rules.get("min_script_alignment", 0.35)):
        issues.append(f"low alignment {cue.get('script_alignment')}")
    if not is_relevant_image(cue, rules):
        issues.append(f"not relevant score={cue.get('topic_relevance_score')}")
    return (len(issues) == 0, issues)
