#!/usr/bin/env python3
"""Deep YAML verse audit — catches text-only refs validate_article.py skips."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

VERSE_IN_TEXT = re.compile(
    r"^(?:[\d\s\w]+?\s+\d+:\d+(?:\s*[–\-]\s*\d+)?)\s*$",
    re.I,
)
BOOK_CH_VERSE = re.compile(
    r"([\d\s\w]+?\s+\d+:\d+)(?:\s*[–\-]\s*(\d+))?",
    re.I,
)


def parse_ref(ref: str) -> tuple[str, int, int] | None:
    ref = re.sub(r"\s*\([^)]+\)\s*", " ", ref).strip()
    ref = re.sub(r"^[^\w\d]+", "", ref)  # strip emoji prefix
    ref = re.sub(r"\s*-\s*.*$", "", ref).strip()
    m = BOOK_CH_VERSE.match(ref)
    if not m:
        return None
    base, end = m.group(1), m.group(2)
    book_ch, start = base.rsplit(":", 1)
    start_i = int(start)
    end_i = int(end) if end else start_i
    return book_ch.strip(), start_i, end_i


def ref_variants(ref: str) -> set[str]:
    ref = ref.strip()
    clean = re.sub(r"\s*\([^)]+\)\s*", " ", ref).strip()
    clean = re.sub(r"^[^\w\d]+", "", clean)
    clean = re.sub(r"\s*-\s*.*$", "", clean).strip()
    variants = {ref, clean}
    parsed = parse_ref(ref)
    if parsed:
        book_ch, start, end = parsed
        for v in range(start, end + 1):
            variants.add(f"{book_ch}:{v}")
        if end > start:
            variants.add(f"{book_ch}:{start}–{end}")
            variants.add(f"{book_ch}:{start}-{end}")
    norm = clean.replace("Psalms", "Psalm")
    variants.add(norm)
    return {v for v in variants if v}


def load_yaml_entries(path: Path) -> list[dict]:
    if yaml is None:
        raise SystemExit("pyyaml required: pip install pyyaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    entries: list[dict] = []
    for section in data.get("sections", []):
        for verse in section.get("verses", []):
            ref = (verse.get("reference") or "").strip()
            text = (verse.get("text") or "").strip()
            entries.append({"reference": ref, "text": text})
    return entries


def effective_ref(entry: dict) -> str | None:
    ref = entry["reference"]
    text = entry["text"]
    if ref and BOOK_CH_VERSE.search(ref):
        return ref
    if not ref and text and VERSE_IN_TEXT.match(text.strip()):
        return text.strip()
    return ref if ref and BOOK_CH_VERSE.search(ref) else None


def content_in_html(snippet: str, html: str) -> bool:
    words = [w for w in re.findall(r"\w+", snippet) if len(w) > 4][:8]
    if not words:
        return False
    hits = sum(1 for w in words if w.lower() in html.lower())
    return hits >= max(2, len(words) // 2)


def ref_in_html(ref: str, html: str) -> tuple[bool, str | None]:
    for v in ref_variants(ref):
        if v in html:
            return True, v
    return False, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit YAML verses vs sermon HTML")
    parser.add_argument("--html", required=True)
    parser.add_argument("--yaml", required=True)
    parser.add_argument(
        "--check-labels",
        action="store_true",
        help="Also warn on teaching labels (True Faith, Identity) missing from HTML",
    )
    args = parser.parse_args()

    html = Path(args.html).expanduser().read_text(encoding="utf-8")
    entries = load_yaml_entries(Path(args.yaml).expanduser())

    scripture_entries = [e for e in entries if effective_ref(e)]
    missing: list[tuple[str, str, str]] = []
    partial: list[tuple[str, str]] = []
    ok = 0

    for entry in scripture_entries:
        ref = effective_ref(entry) or entry["reference"]
        snippet = entry["text"][:100]
        found, matched = ref_in_html(ref, html)
        if found:
            ok += 1
            if matched and matched != ref.split("(")[0].strip():
                partial.append((ref, matched))
        elif content_in_html(entry["text"], html):
            missing.append((ref, "CONTENT PRESENT, citation missing/split", snippet))
        else:
            missing.append((ref, "MISSING ref + content", snippet))

    print(f"yaml_scripture_entries: {len(scripture_entries)}")
    print(f"ok: {ok} gaps: {len(missing)}")

    for ref, status, snip in missing:
        print(f"  [{status}] {ref}")
        if snip:
            print(f"      YAML: {snip}...")

    if args.check_labels:
        for entry in entries:
            ref = entry["reference"]
            if not ref or BOOK_CH_VERSE.search(ref):
                continue
            if ref and not content_in_html(entry["text"] or ref, html):
                print(f"  [LABEL?] {ref}")

    if any(s.startswith("MISSING") for _, s, _ in missing):
        print("\nResult: FAIL — fix MISSING entries before publish")
        return 1
    if missing:
        print("\nResult: PASS (with citation splits — review optional)")
        return 0
    print("\nResult: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
