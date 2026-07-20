#!/usr/bin/env python3
"""Validate a biblerevelation sermon article draft before publish."""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))


def strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def ref_in_html(ref: str, html: str) -> bool:
    if ref in html:
        return True
    # Normalise Psalm/Psalms and leading book token
    norm = ref.replace("Psalms", "Psalm").replace("  ", " ").strip()
    if norm in html:
        return True
    book = norm.split()[0] if norm else ""
    return bool(book and book in html)


def load_yaml_refs(path: Path) -> list[str]:
    if yaml is None:
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    refs: list[str] = []
    for section in data.get("sections", []):
        for verse in section.get("verses", []):
            ref = (verse.get("reference") or "").strip()
            if ref:
                refs.append(ref)
    return refs


def heading_titles(html: str, tag: str) -> list[str]:
    raw = re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.S)
    return [re.sub(r"<[^>]+>", "", h).strip() for h in raw]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate biblerevelation sermon HTML draft")
    parser.add_argument("--html", required=True, help="Path to biblerevelation-*.html")
    parser.add_argument("--transcript", help="Path to .transcript.txt")
    parser.add_argument("--yaml", help="Path to PPT YAML deck")
    parser.add_argument("--min-ratio", type=float, default=0.55, help="Min word ratio vs transcript")
    args = parser.parse_args()

    html_path = Path(args.html).expanduser()
    html = html_path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    # Appendix / empty headings
    if "Scripture from the Slides" in html:
        errors.append("Appendix block present — move YAML verses inline")
    for tag in ("h2", "h3"):
        for title in heading_titles(html, tag):
            if title in ("📖", "📖 ") or re.fullmatch(r"[\U0001f4d6📖\s]+", title):
                errors.append(f"Empty {tag} heading: {title!r}")

    # Duplicate headings
    for tag in ("h2", "h3"):
        titles = heading_titles(html, tag)
        for title, count in Counter(titles).items():
            if count > 1:
                errors.append(f"Duplicate {tag}: {title[:70]!r} (x{count})")

    # Broken / portrait image URLs
    if re.search(r"biblerevelation-\d+x\d+\.org", html):
        errors.append("Corrupted image URL (biblerevelation-WIDTHxHEIGHT.org) — fix src")
    portrait_in_url = re.compile(
        r"(?:^|/)[^/]*-(?:683x1024|768x1152|1024x1536)(?:-\d+x\d+)?\.(?:png|jpe?g|webp|gif)",
        re.I,
    )
    for src in re.findall(r'src="([^"]+)"', html):
        if "wp-content/uploads" in src and not re.search(r"\.(png|jpe?g|webp|gif)(?:\?|$)", src, re.I):
            warnings.append(f"Image src may be missing extension: {src[:80]}")
        if portrait_in_url.search(src):
            warnings.append(
                f"Portrait image in article (use 1536x1024 landscape, not 1024x1536): {src[:90]}"
            )

    # Word ratio
    hw = word_count(strip_html(html))
    if args.transcript:
        tw = word_count(Path(args.transcript).expanduser().read_text(encoding="utf-8"))
        ratio = hw / tw if tw else 0
        print(f"words: html≈{hw} transcript={tw} ratio={ratio:.0%}")
        if ratio < args.min_ratio:
            warnings.append(f"Word ratio {ratio:.0%} below {args.min_ratio:.0%} — likely script summary")

    # YAML verse coverage (best-effort: reference substring in HTML)
    if args.yaml and yaml is not None:
        refs = load_yaml_refs(Path(args.yaml).expanduser())
        missing = [r for r in refs if not ref_in_html(r, html)]
        print(f"yaml_refs: {len(refs)} missing_in_html: {len(missing)}")
        if missing:
            for ref in missing[:8]:
                warnings.append(f"YAML reference not found in HTML: {ref}")
            if len(missing) > 8:
                warnings.append(f"… and {len(missing) - 8} more missing YAML refs")

    # Structure hints
    if "Highlight key" not in html:
        warnings.append("No highlight-key blockquote near top")
    if "Takeaway" not in html and "takeaway" not in html.lower():
        warnings.append("No Takeaway section found")
    if "Based on a Sunday message" not in html:
        warnings.append("No closing footer paragraph")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"FAIL: {e}")

    if errors:
        print("\nResult: FAIL")
        return 1
    print("\nResult: PASS" + (" (with warnings)" if warnings else ""))
    return 0 if not warnings else 0


if __name__ == "__main__":
    sys.exit(main())
