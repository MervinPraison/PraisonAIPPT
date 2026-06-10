"""Record scroll-down or zoom-in capture of the canonical news page for hook attention."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from praisonaippt.daily_single.media_sync import load_handoff_topic
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.visual_audit import _gray_array, export_frame
from praisonaippt.segment_video.media import ffprobe_duration

SCROLL_FILENAME = "canonical-scroll.mp4"
W, H = 1920, 1080
FPS = 30
MIN_SCROLL_PX = 160
MIN_MOTION = 0.008
PAN_SCALE_W = 3200


def scroll_video_path(project: DailySingleProject) -> Path | None:
    path = project.assets_dir / "videos" / SCROLL_FILENAME
    return path if path.is_file() else None


def canonical_url(project: DailySingleProject) -> str:
    topic = load_handoff_topic(project)
    return str(topic.get("canonical_url") or "").strip()


def _run_ffmpeg(args: list[str]) -> None:
    subprocess.run(args, check=True, capture_output=True)


def _image_height(path: Path) -> int:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=height", "-of", "csv=p=0", str(path),
        ],
        text=True,
    ).strip()
    return int(out or H)


def frame_motion(a: Path, b: Path, *, w: int = 960, h: int = 540) -> float:
    ga = _gray_array(a, w=w, h=h)
    gb = _gray_array(b, w=w, h=h)
    if ga is None or gb is None:
        return 0.0
    mse = float(np.mean((ga.astype(np.float32) - gb.astype(np.float32)) ** 2))
    return max(0.0, 1.0 - mse / 65025.0)


def video_has_motion(path: Path, *, min_motion: float = MIN_MOTION) -> bool:
    """Return True when two samples from the clip differ enough (not a static hold)."""
    dur = ffprobe_duration(path)
    if dur <= 0.2:
        return False
    with tempfile.TemporaryDirectory() as tmp:
        tdir = Path(tmp)
        a = tdir / "a.jpg"
        b = tdir / "b.jpg"
        export_frame(path, 0.08, a)
        export_frame(path, min(dur * 0.55, dur - 0.08), b)
        return frame_motion(a, b) >= min_motion


def _pan_filter(*, duration: float, overscale_w: int = PAN_SCALE_W) -> str:
    """Pan down an overscaled frame — reads as scroll/zoom on viewport-sized pages."""
    return (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
        f"scale={overscale_w}:-1,"
        f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*t/{duration:.4f}"
    )


def build_zoom_video(src: Path, dest: Path, *, duration: float) -> None:
    """Slow zoom-in / pan-down on a page screenshot."""
    _run_ffmpeg([
        "ffmpeg", "-y", "-framerate", str(FPS), "-loop", "1", "-i", str(src),
        "-vf", _pan_filter(duration=duration), "-t", f"{duration:.3f}",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(dest),
    ])


def build_scroll_video(src: Path, dest: Path, *, duration: float) -> None:
    """Scroll down a tall full-page screenshot."""
    scaled = dest.with_suffix(".scaled.png")
    _run_ffmpeg([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", f"scale={W}:-1,setsar=1", "-frames:v", "1", str(scaled),
    ])
    ih = _image_height(scaled)
    travel = max(0, ih - H)
    if travel < MIN_SCROLL_PX:
        build_zoom_video(scaled, dest, duration=duration)
        scaled.unlink(missing_ok=True)
        return
    vf = f"scale={W}:-1,setsar=1,crop={W}:{H}:0:(ih-{H})*t/{duration:.4f}"
    _run_ffmpeg([
        "ffmpeg", "-y", "-framerate", str(FPS), "-loop", "1", "-i", str(scaled),
        "-vf", vf, "-t", f"{duration:.3f}",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(dest),
    ])
    scaled.unlink(missing_ok=True)


def _capture_page_shot(page_url: str, dest: Path, *, settle_ms: int, max_attempts: int = 3) -> dict | None:
    from playwright.sync_api import sync_playwright

    from praisonaippt.daily_single.content_framing import detect_dom_content_bbox
    from praisonaippt.daily_single.page_capture_quality import validate_live_page

    last_issues: list[str] = []
    dom_bbox_dict: dict | None = None
    ua = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for attempt in range(1, max_attempts + 1):
            page = browser.new_page(viewport={"width": W, "height": H}, user_agent=ua)
            response = page.goto(
                page_url, wait_until="domcontentloaded", timeout=60_000,
            )
            page.wait_for_timeout(settle_ms)
            try:
                page.wait_for_selector("h1, article, main", timeout=15_000)
            except Exception:
                pass
            ok, issues = validate_live_page(page, page_url, response=response)
            if not ok:
                last_issues = issues
                page.close()
                if attempt < max_attempts:
                    continue
                browser.close()
                raise RuntimeError(
                    f"Canonical page failed validation after {max_attempts} attempts: "
                    + "; ".join(issues)
                )
            scroll_h = page.evaluate(
                "() => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"
            )
            tall = min(max(H, int(scroll_h)), 12_000)
            if tall > H:
                page.set_viewport_size({"width": W, "height": tall})
                page.wait_for_timeout(400)
            dom = detect_dom_content_bbox(page)
            if dom is not None:
                dom_bbox_dict = dom.to_dict()
            page.screenshot(path=str(dest), full_page=False)
            page.close()
            break
        browser.close()
    if not dest.is_file():
        raise RuntimeError(f"Failed to capture screenshot: {'; '.join(last_issues) or 'unknown'}")
    return dom_bbox_dict


def record_canonical_scroll(
    project: DailySingleProject,
    *,
    url: str | None = None,
    duration: float = 5.0,
    settle_ms: int = 1500,
    mode: str = "auto",
) -> Path:
    """Capture hook attention clip — scroll down when page is tall, otherwise zoom/pan in."""
    page_url = (url or canonical_url(project)).strip()
    if not page_url:
        raise ValueError("No canonical_url in handoff — pass url= explicitly")
    if mode not in ("auto", "scroll", "zoom"):
        raise ValueError("mode must be auto, scroll, or zoom")

    dest = project.assets_dir / "videos" / SCROLL_FILENAME
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = dest.parent / ".scroll-capture"
    if tmp_dir.is_dir():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

    try:
        dom_bbox_dict = _capture_page_shot(page_url, tmp_dir / "page.png", settle_ms=settle_ms)
    except ImportError as exc:
        raise RuntimeError(
            "Playwright required: pip install playwright && playwright install chromium"
        ) from exc

    shot = tmp_dir / "page.png"
    if not shot.is_file():
        raise RuntimeError("Failed to capture canonical page screenshot")

    from praisonaippt.daily_single.content_framing import (
        ContentFrame,
        MAX_SCROLL_PX_PER_SEC,
        TARGET_SCROLL_PX_PER_SEC,
        measure_framing,
        reframe_page_shot,
        save_framing_diagram,
        validate_framing,
        validate_scroll_speed,
        write_framing_report,
    )
    from praisonaippt.daily_single.page_capture_quality import (
        capture_qa_dir,
        persist_capture_artefacts,
        screenshot_looks_like_error_page,
    )

    bad, shot_issues = screenshot_looks_like_error_page(shot)
    if bad:
        persist_capture_artefacts(
            project, screenshot=shot, page_url=page_url, ok=False, issues=shot_issues,
        )
        raise RuntimeError(
            "Screenshot looks like a browser error page: " + "; ".join(shot_issues)
        )

    dom_frame = None
    if dom_bbox_dict:
        dom_frame = ContentFrame(**{k: dom_bbox_dict[k] for k in ("x0", "y0", "x1", "y1")}, source="dom", confidence=1.0)
    encode_src, content_frame, _raw_metrics = reframe_page_shot(
        shot, dom_bbox=dom_frame, dest=tmp_dir / "page-reframed.png",
    )
    framing_metrics = measure_framing(encode_src)
    qa = capture_qa_dir(project)
    save_framing_diagram(shot, framing_metrics, qa / "framing-diagram.png")
    post_framing_ok, framing_issues = validate_framing(framing_metrics)
    write_framing_report(qa, framing_metrics, ok=post_framing_ok, issues=framing_issues)

    use_scroll = mode == "scroll"
    if mode == "auto":
        use_scroll = _image_height(encode_src) >= H + MIN_SCROLL_PX

    travel = max(0, _image_height(encode_src) - H)
    max_travel = int(TARGET_SCROLL_PX_PER_SEC * duration * 0.6)
    if use_scroll and travel > max_travel:
        trimmed = tmp_dir / "page-trimmed.png"
        from praisonaippt.daily_single.content_framing import trim_for_hook_scroll
        trim_for_hook_scroll(encode_src, trimmed, max_travel_px=max_travel)
        encode_src = trimmed
        travel = max_travel
    encode_duration = duration
    speed_ok, speed_issues = validate_scroll_speed(travel, encode_duration)

    if use_scroll:
        build_scroll_video(encode_src, dest, duration=encode_duration)
        motion = "scroll"
    else:
        build_zoom_video(encode_src, dest, duration=encode_duration)
        motion = "zoom"

    if not video_has_motion(dest):
        build_zoom_video(encode_src, dest, duration=encode_duration)
        motion = "zoom"
        if not video_has_motion(dest):
            raise RuntimeError("Hook attention clip has no visible motion — check canonical URL")

    persist_capture_artefacts(
        project,
        screenshot=shot,
        page_url=page_url,
        ok=post_framing_ok and speed_ok,
        issues=framing_issues + speed_issues,
        motion_mode=motion,
        framing=framing_metrics.to_dict(),
        scroll_travel_px=travel,
        scroll_duration_sec=round(encode_duration, 2),
        scroll_speed_px_per_sec=round(travel / encode_duration, 1) if encode_duration > 0 and travel > 0 else 0,
    )
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"Wrote {dest} ({ffprobe_duration(dest):.1f}s, {motion}) from {page_url}")
    return dest
