"""Sync canonical images and HD motion clips for daily_single projects."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import re

from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.segment_video.assets.canonical_crawl import (
    crawl_topic,
    extract_image_urls,
    fetch_page,
)

_CRAWL_HASH = re.compile(r"^[a-f0-9]{12}\.(png|jpe?g|webp)$", re.I)

# Core images from the Anthropic news page (named handoff entries).
CORE_IMAGE_NAMES = frozenset({
    "benchmark-table.png",
    "cyber-classifier.png",
    "jailbreak-resistance.png",
    "bio-aav-chart.png",
    "alignment-chart.png",
    "protein-complexes.png",
    "gpt-image-safeguard-fallback.png",
    "vision-demo-hero.png",
    "cyber-eval-results.png",
    "distillation-safeguard.png",
})
MIN_VIDEO_HEIGHT = 720
MAX_VIDEO_SEC = 60
YTDLP_FORMAT = (
    "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
    "bestvideo[height<=1080]+bestaudio/"
    "best[height<=1080]/best"
)

# Extra Sanity CDN assets on the Fable launch page (named for beat-map use).
FABLE_EXTRA_IMAGES: list[tuple[str, str, str]] = [
    (
        "vision-demo-hero.png",
        "https://cdn.sanity.io/images/4zrzovbb/website/"
        "b7055119423427c40a0e4d84054aed17682b50a2-2880x1620.png",
        "vision demo carousel hero",
    ),
    (
        "cyber-eval-results.png",
        "https://cdn.sanity.io/images/4zrzovbb/website/"
        "036229d8f9be9a5a911dbbd863b3c6cc09a79a70-3840x2160.png",
        "cyber evaluation results chart",
    ),
    (
        "distillation-safeguard.png",
        "https://cdn.sanity.io/images/4zrzovbb/website/"
        "d3c3efe0e8ab310856368cee2b2161439db6676a-1920x1080.png",
        "distillation safeguard chart",
    ),
]


def _handoff_path(project: DailySingleProject) -> Path:
    return project.research_dir / "video-handoff.json"


def load_handoff_topic(project: DailySingleProject) -> dict[str, Any]:
    path = _handoff_path(project)
    if not path.is_file():
        return {"topic_slug": project.slug, "canonical_url": "", "images": [], "videos": [], "youtube": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    for topic in data.get("topics") or []:
        if topic.get("topic_slug") == project.slug:
            return topic
    topics = data.get("topics") or []
    return topics[0] if topics else {}


def video_height(path: Path) -> int:
    if not path.is_file():
        return 0
    r = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=height", "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return 0
    try:
        return int(float(r.stdout.strip()))
    except ValueError:
        return 0


def video_duration(path: Path) -> float | None:
    r = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return None
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def download_youtube_hd(video_id: str, dest: Path, *, timeout: int = 180) -> tuple[bool, str]:
    """Download merged MP4 up to 1080p (not the 360p progressive `best[ext=mp4]` stream)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    template = str(dest.parent / f"{dest.stem}.%(ext)s")
    for old in dest.parent.glob(f"{dest.stem}.*"):
        if old.suffix in {".mp4", ".m4a", ".webm", ".part"}:
            old.unlink(missing_ok=True)
    cmd = [
        "yt-dlp", "--no-warnings", "--no-playlist", "--max-downloads", "1",
        "-f", YTDLP_FORMAT, "--merge-output-format", "mp4",
        "-o", template,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "yt-dlp timed out"
    merged = dest if dest.is_file() else None
    if not merged:
        for candidate in dest.parent.glob(f"{dest.stem}*.mp4"):
            if candidate.is_file():
                merged = candidate
                break
    if not merged:
        err = (r.stderr or r.stdout or "yt-dlp failed").strip()
        return False, err[:200]
    dur = video_duration(merged)
    if dur is not None and dur > MAX_VIDEO_SEC:
        merged.unlink(missing_ok=True)
        return False, f"video too long ({dur:.0f}s > {MAX_VIDEO_SEC}s)"
    if merged != dest:
        dest.unlink(missing_ok=True)
        merged.rename(dest)
    if r.returncode != 0 and video_height(dest) < MIN_VIDEO_HEIGHT:
        err = (r.stderr or r.stdout or "yt-dlp failed").strip()
        return False, err[:200]
    return True, ""


def download_direct(url: str, dest: Path, *, timeout: int = 120) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [
            "curl", "-fsSL", "-A", "Mozilla/5.0 (compatible; praisonaippt/1.0)",
            "--max-time", str(timeout), "-o", str(dest), url,
        ],
        capture_output=True,
    )
    return r.returncode == 0 and dest.is_file() and dest.stat().st_size > 0


def _videos_dir(project: DailySingleProject) -> Path:
    return project.assets_dir / "videos"


def sync_videos(project: DailySingleProject, *, force_hd: bool = False) -> dict[str, Any]:
    """Download handoff videos; upgrade YouTube clips below MIN_VIDEO_HEIGHT."""
    topic = load_handoff_topic(project)
    dest_dir = _videos_dir(project)
    dest_dir.mkdir(parents=True, exist_ok=True)
    logs: list[str] = []
    rows: list[dict[str, Any]] = []

    for entry in list(topic.get("videos") or []) + list(topic.get("youtube") or []):
        fn = entry.get("filename") or "clip.mp4"
        dest = dest_dir / fn
        video_id = entry.get("video_id")
        url = entry.get("url") or entry.get("source_url") or ""
        height = video_height(dest) if dest.is_file() else 0
        needs = not dest.is_file() or (force_hd and height < MIN_VIDEO_HEIGHT)
        backup: Path | None = None

        if not needs:
            logs.append(f"skip {fn} ({height}p)")
            rows.append({"filename": fn, "ok": True, "height": height, "skipped": True})
            continue

        if dest.is_file() and force_hd and height < MIN_VIDEO_HEIGHT:
            backup = dest.with_suffix(".bak.mp4")
            dest.rename(backup)
            logs.append(f"upgrade {fn} ({height}p → HD)")

        ok, err = False, ""
        if video_id:
            ok, err = download_youtube_hd(video_id, dest)
        elif url:
            ok = download_direct(url, dest)
            err = "" if ok else "curl failed"
        else:
            err = "no url or video_id"

        if not ok and backup and backup.is_file():
            backup.rename(dest)
            err = f"{err} (kept previous {height}p)"
        elif ok and backup:
            backup.unlink(missing_ok=True)

        height = video_height(dest) if ok else height
        logs.append(f"{'ok' if ok else 'fail'} {fn} ({height}p)" + (f": {err}" if err and not ok else ""))
        rows.append({"filename": fn, "ok": ok, "height": height, "error": err or None})

    return {"logs": logs, "videos": rows, "ok": all(r["ok"] for r in rows)}


def sync_canonical_images(project: DailySingleProject) -> dict[str, Any]:
    """Crawl canonical URL and download named extras into review-assets."""
    topic = load_handoff_topic(project)
    canonical = topic.get("canonical_url") or ""
    logs: list[str] = []
    new_records: list[dict] = []

    if canonical:
        records, crawl_logs = crawl_topic(
            topic, project.assets_dir, aggressive=True, max_images=16,
        )
        new_records.extend(records)
        logs.extend(crawl_logs)

    if project.slug == "anthropic-claude-fable-5-mythos-5":
        for fn, url, alt in FABLE_EXTRA_IMAGES:
            dest = project.assets_dir / fn
            if dest.is_file() and dest.stat().st_size > MIN_IMAGE_BYTES:
                logs.append(f"skip {fn}")
                continue
            if download_direct(url, dest):
                logs.append(f"saved {fn}")
                new_records.append({"filename": fn, "source_url": url, "alt": alt})
            else:
                logs.append(f"fail {fn}")

    return {"logs": logs, "new_images": len(new_records), "ok": True}


MIN_IMAGE_BYTES = 8000


def patch_beat_map(project: DailySingleProject) -> dict[str, Any]:
    """Ensure beat-map references all crawled images and carousel clips."""
    if not project.beat_map_path.is_file():
        return {"ok": False, "error": "beat-map missing"}
    bm = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    beats = bm.setdefault("beats", {})
    changes: list[str] = []
    assets = project.assets_dir
    videos = assets / "videos"

    def _img(fn: str, beat: int, role: str) -> dict:
        p = assets / fn
        return {"filename": fn, "path": str(p.resolve()), "beat": beat, "role": role}

    def _clip(fn: str, beat: int) -> dict | None:
        p = videos / fn
        if not p.is_file():
            return None
        dur = video_duration(p) or 15.0
        return {
            "filename": fn,
            "path": str(p.resolve()),
            "in_sec": 0.0,
            "out_sec": min(dur, MAX_VIDEO_SEC),
            "analysis_method": "media_sync",
        }

    # Beat 5 — solar, pokemon, optional fluid + stat card
    b5 = beats.setdefault("5", {"beat": 5, "clips": [], "images": [], "generated": []})
    want_clips = ["carousel-solar.mp4", "pokemon-timelapse.mp4", "carousel-fluid.mp4"]
    existing = {c.get("filename") for c in b5.get("clips") or []}
    clips = list(b5.get("clips") or [])
    for fn in want_clips:
        if fn in existing:
            continue
        rec = _clip(fn, 5)
        if rec:
            clips.append(rec)
            changes.append(f"beat 5 +clip {fn}")
    if clips:
        order = {n: i for i, n in enumerate(want_clips)}
        clips.sort(key=lambda c: order.get(c.get("filename", ""), 99))
        b5["clips"] = clips

    # Beat 6 — biology chart from page
    b6 = beats.setdefault("6", {"beat": 6, "clips": [], "images": [], "generated": []})
    imgs = list(b6.get("images") or [])
    img_names = {i.get("filename") for i in imgs}
    for fn, role in (
        ("bio-aav-chart.png", "biology_classifier"),
        ("distillation-safeguard.png", "distillation"),
        ("vision-demo-hero.png", "vision_hero"),
    ):
        if fn not in img_names and (assets / fn).is_file():
            imgs.append(_img(fn, 6, role))
            img_names.add(fn)
            changes.append(f"beat 6 +image {fn}")
    b6["images"] = imgs

    if changes:
        bm["include_carousel_fluid"] = True
        project.beat_map_path.write_text(json.dumps(bm, indent=2), encoding="utf-8")

    return {"ok": True, "changes": changes}


def validate_media_inventory(project: DailySingleProject) -> tuple[bool, dict[str, Any]]:
    """Check handoff images exist and motion clips meet MIN_VIDEO_HEIGHT."""
    topic = load_handoff_topic(project)
    issues: list[str] = []
    images: list[dict] = []
    videos: list[dict] = []

    for img in topic.get("images") or []:
        fn = img.get("filename") or ""
        if _CRAWL_HASH.match(fn) and fn not in CORE_IMAGE_NAMES:
            continue
        path = Path(img.get("path") or project.assets_dir / fn)
        if not path.is_file():
            path = project.assets_dir / fn
        ok = path.is_file()
        if not ok:
            issues.append(f"missing image {fn}")
        images.append({"filename": fn, "ok": ok})

    for entry in list(topic.get("videos") or []) + list(topic.get("youtube") or []):
        fn = entry.get("filename") or ""
        path = Path(entry.get("path") or _videos_dir(project) / fn)
        height = video_height(path) if path.is_file() else 0
        ok = path.is_file() and height >= MIN_VIDEO_HEIGHT
        if not path.is_file():
            issues.append(f"missing video {fn}")
        elif height < MIN_VIDEO_HEIGHT:
            issues.append(f"low resolution {fn} ({height}p < {MIN_VIDEO_HEIGHT}p)")
        videos.append({"filename": fn, "ok": ok, "height": height})

    canonical = topic.get("canonical_url") or ""
    page_urls: list[str] = []
    if canonical:
        html, _ = fetch_page(canonical)
        if html:
            page_urls = [u for u, _ in extract_image_urls(html, canonical)]

    report = {
        "images": images,
        "videos": videos,
        "canonical_url": canonical,
        "page_image_count": len(page_urls),
        "issues": issues,
    }
    return len(issues) == 0, report


def run_sync_assets(project: DailySingleProject, *, force_hd: bool = True, crawl: bool = True) -> dict[str, Any]:
    """Full asset sync: crawl images → HD videos → beat-map patch → inventory."""
    image_report = sync_canonical_images(project) if crawl else {"ok": True, "logs": [], "new_images": 0}
    video_report = sync_videos(project, force_hd=force_hd)
    beat_report = patch_beat_map(project)
    ok, inventory = validate_media_inventory(project)
    out_path = project.merge_dir / "asset_sync_report.json"
    project.merge_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "ok": ok and video_report.get("ok", True),
        "images": image_report,
        "videos": video_report,
        "beat_map": beat_report,
        "inventory": inventory,
    }
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
