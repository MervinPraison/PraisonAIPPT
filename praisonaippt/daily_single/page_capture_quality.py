"""Validate Playwright page captures — reject error pages before encoding hook scroll."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np

from praisonaippt.daily_single.media_sync import load_handoff_topic
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.visual_audit import _gray_array, export_frame, pixel_similarity
from praisonaippt.segment_video.media import ffprobe_duration

ERROR_TEXT = re.compile(
    r"couldn'?t load|could not load|this page couldn'?t|"
    r"page isn'?t working|404|not found|access denied|"
    r"verify you are human|cloudflare|err_connection|"
    r"dns_probe|unable to connect|something went wrong",
    re.I,
)
MIN_BODY_KEYWORDS = ("anthropic", "claude", "fable")
MIN_IMAGE_STD = 22.0
MIN_WHITE_RATIO_ERROR = 0.95
MIN_MEAN_GRAY_ERROR = 252.0
CAPTURE_QA_DIR = "canonical_capture"


def capture_qa_dir(project: DailySingleProject) -> Path:
    return project.merge_dir / "qa" / CAPTURE_QA_DIR


def capture_report_path(project: DailySingleProject) -> Path:
    return capture_qa_dir(project) / "capture_report.json"


def saved_screenshot_path(project: DailySingleProject) -> Path:
    return capture_qa_dir(project) / "page.png"


def validate_live_page(page: Any, expected_url: str, *, response: Any | None = None) -> tuple[bool, list[str]]:
    """Check Playwright page is not an error interstitial and matches expected host."""
    issues: list[str] = []
    if response is not None and hasattr(response, "status") and response.status >= 400:
        issues.append(f"HTTP {response.status} for {expected_url}")
    final_url = str(getattr(page, "url", "") or "")
    exp = urlparse(expected_url)
    got = urlparse(final_url)
    if exp.netloc and got.netloc and exp.netloc.replace("www.", "") not in got.netloc.replace("www.", ""):
        issues.append(f"unexpected host after navigation: {got.netloc} (wanted {exp.netloc})")
    try:
        title = page.title() or ""
        body = page.inner_text("body")[:8000]
    except Exception as exc:
        issues.append(f"could not read page text: {exc}")
        return False, issues
    blob = f"{title}\n{body}".lower()
    if ERROR_TEXT.search(blob):
        issues.append("browser error or block page detected in title/body text")
    if not any(k in blob for k in MIN_BODY_KEYWORDS):
        issues.append(f"page missing launch keywords: {', '.join(MIN_BODY_KEYWORDS)}")
    return len(issues) == 0, issues


def screenshot_looks_like_error_page(path: Path) -> tuple[bool, list[str]]:
    """Detect near-blank white Chromium error pages and failed captures."""
    gray = _gray_array(path, w=1920, h=1080)
    if gray is None:
        return True, ["unreadable screenshot"]
    mean = float(np.mean(gray))
    white = float(np.mean(gray > 245))
    std = float(np.std(gray))
    issues: list[str] = []
    if mean >= MIN_MEAN_GRAY_ERROR and white >= MIN_WHITE_RATIO_ERROR:
        issues.append(f"near-blank white page (mean={mean:.0f}, white={white:.2f})")
    if std < MIN_IMAGE_STD and white >= 0.90:
        issues.append(f"extremely low detail (std={std:.1f}) — likely error or failed load")
    return len(issues) > 0, issues


def frame_looks_like_browser_error(path: Path) -> bool:
    bad, _ = screenshot_looks_like_error_page(path)
    return bad


def persist_capture_artefacts(
    project: DailySingleProject,
    *,
    screenshot: Path,
    page_url: str,
    ok: bool,
    issues: list[str],
    motion_mode: str = "",
) -> Path:
    qa = capture_qa_dir(project)
    qa.mkdir(parents=True, exist_ok=True)
    dest_shot = saved_screenshot_path(project)
    dest_shot.write_bytes(screenshot.read_bytes())
    report = {
        "schema_version": 1,
        "ok": ok,
        "page_url": page_url,
        "screenshot": str(dest_shot.relative_to(project.root)),
        "motion_mode": motion_mode,
        "issues": issues,
    }
    out = capture_report_path(project)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out


def validate_scroll_asset(project: DailySingleProject, scroll_path: Path) -> tuple[bool, dict[str, Any]]:
    """Post-encode gate: scroll clip exists, moves, and first frame is not an error page."""
    issues: list[str] = []
    if not scroll_path.is_file():
        return False, {"issues": [f"missing {scroll_path}"]}
    dur = ffprobe_duration(scroll_path)
    if dur < 2.0:
        issues.append(f"scroll clip too short ({dur:.1f}s)")
    qa = capture_qa_dir(project)
    qa.mkdir(parents=True, exist_ok=True)
    frame = qa / "scroll-frame-0.jpg"
    export_frame(scroll_path, 0.12, frame)
    if frame_looks_like_browser_error(frame):
        issues.append("scroll clip frame shows browser error page")
    report_path = capture_report_path(project)
    if report_path.is_file():
        cap = json.loads(report_path.read_text(encoding="utf-8"))
        if not cap.get("ok"):
            issues.append("capture_report.json marked failed capture")
    elif saved_screenshot_path(project).is_file():
        if frame_looks_like_browser_error(saved_screenshot_path(project)):
            issues.append("saved page.png looks like error page")
    topic = load_handoff_topic(project)
    title_blob = " ".join(
        str(topic.get(k, "")) for k in ("title", "slug", "canonical_url")
    ).lower()
    expect = tuple(w for w in ("anthropic", "claude", "fable") if w in title_blob) or MIN_BODY_KEYWORDS
    return len(issues) == 0, {"issues": issues, "duration_sec": round(dur, 2), "expected_keywords": expect}
