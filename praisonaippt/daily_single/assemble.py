"""VO-driven ffmpeg assembly for daily_single projects."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from praisonaippt.daily_single.env import load_env, require_keys
from praisonaippt.daily_single.project import DailySingleProject
from praisonaippt.daily_single.protocol import SEGMENT_ORDER
from praisonaippt.daily_single.hook_montage import (
    attention_visual,
    build_hook_montage_plan,
    hook_attention_durations,
    montage_cue_durations,
    overview_montage_start_sec,
)
from praisonaippt.daily_single.brand_bumper import BUMPER_STEM, prepare_brand_bumper
from praisonaippt.daily_single.avatar_pip import overlay_circle_pip
from praisonaippt.daily_single.beat01_timing import beat01_views_duration_sec
from praisonaippt.daily_single.canonical_scroll import scroll_video_path
from praisonaippt.daily_single.beat10_timing import beat10_chart_durations
from praisonaippt.daily_single.segment_cue_timing import (
    beat4_visual_durations,
    beat8_clip_durations,
    beat9_visual_durations,
    clip_durations_for_cues,
)
from praisonaippt.daily_single.publish_quality_config import beat_map_variant
from praisonaippt.daily_single.text_slide import outro_slide_specs, render_slide_group, slide_specs
from praisonaippt.daily_single.vo import synthesise_segments
from praisonaippt.segment_video.media import ffprobe_duration

W, H = 1920, 1080
FPS = 30
LAUNCH_CLIP_ON_TOPIC_IN_SEC = 5.8


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def _scale_pad_filter() -> str:
    return (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps={FPS}"
    )


def _video_from_image(src: Path, dest: Path, dur: float) -> None:
    _run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", f"{dur:.3f}",
        "-vf", _scale_pad_filter(), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(dest),
    ])


def _asset_to_clip(src: Path, dest: Path, dur: float, *, in_sec: float = 0.0) -> None:
    """Still image or motion clip scaled to target duration."""
    if src.suffix.lower() == ".mp4":
        start = max(0.0, in_sec)
        clip_d = min(dur, max(0.5, ffprobe_duration(src) - start))
        _trim_clip(src, dest, start, start + clip_d)
        _extend_or_trim(dest, dest, dur)
        return
    _video_from_image(src, dest, dur)


def _trim_clip(src: Path, dest: Path, start: float, end: float) -> None:
    dur = max(0.5, end - start)
    _run([
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{dur:.3f}",
        "-vf", _scale_pad_filter(), "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(dest),
    ])


def _extend_or_trim(src: Path, dest: Path, target_dur: float) -> None:
    src_dur = ffprobe_duration(src)
    if abs(src_dur - target_dur) < 0.15 and src.resolve() == dest.resolve():
        return
    if abs(src_dur - target_dur) < 0.15:
        shutil.copy2(src, dest)
        return
    tmp = dest if src.resolve() != dest.resolve() else dest.with_suffix(".tmp.mp4")
    if src_dur >= target_dur:
        _run(["ffmpeg", "-y", "-i", str(src), "-t", f"{target_dur:.3f}", "-c", "copy", str(tmp)])
    else:
        _run([
            "ffmpeg", "-y", "-i", str(src), "-filter_complex",
            f"[0:v]tpad=stop_mode=clone:stop_duration={target_dur - src_dur:.3f}[v]",
            "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(tmp),
        ])
    if tmp != dest:
        shutil.move(str(tmp), str(dest))


def _overlay_png(base: Path, png: Path, dest: Path, dur: float) -> None:
    _run([
        "ffmpeg", "-y", "-i", str(base), "-i", str(png),
        "-filter_complex",
        f"[0:v]{_scale_pad_filter()}[bg];[1:v]scale=640:-1[ov];"
        f"[bg][ov]overlay=(W-w)/2:H-h-80:enable='between(t,0,{dur:.3f})'[v]",
        "-map", "[v]", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(dest),
    ])


def _heygen_bookend_segment(heygen: Path, dest: Path, dur: float) -> None:
    _run([
        "ffmpeg", "-y", "-i", str(heygen),
        "-vf", _scale_pad_filter(), "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(dest),
    ])


def _hook_montage(
    project: DailySingleProject,
    launch: Path,
    dest: Path,
    dur: float,
) -> None:
    """Hook: scroll attention → phrase montage → bridge (full-frame video, no avatar)."""
    script = project.segment_script("00-hook").read_text(encoding="utf-8")
    plan = build_hook_montage_plan(project)
    cues = [c for c in plan.get("cues") or [] if c.get("ok") and c.get("path")]
    if len(cues) < 3:
        _hook_launch_only(launch, dest, dur)
        return

    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    skip_scroll = beat_map.get("variant") in ("trust-audit", "social-comparison")
    att, overview, bridge = hook_attention_durations(
        dur,
        script,
        motion_clip=bool(scroll_video_path(project)) and not skip_scroll,
    )
    seg_srt = project.segments_dir / "00-hook" / "segment.srt"
    if seg_srt.is_file():
        from praisonaippt.daily_single.cue_slide_sync import _parse_segment_srt

        rows = _parse_segment_srt(seg_srt)
        if len(rows) >= 3:
            att = max(att, rows[0][1])
            overview = max(0.5, rows[1][1] - att)
            bridge = max(0.5, rows[2][1] - rows[1][1])
            drift = dur - att - overview - bridge
            if abs(drift) > 0.05:
                bridge = max(0.5, bridge + drift)
    montage_t0 = overview_montage_start_sec(project.root)
    if montage_t0 is not None and montage_t0 > att:
        att = montage_t0
        if seg_srt.is_file():
            rows = _parse_segment_srt(seg_srt)
            if len(rows) >= 3:
                overview = max(0.5, rows[1][1] - att)
                bridge = max(0.5, rows[2][1] - rows[1][1])
                drift = dur - att - overview - bridge
                if abs(drift) > 0.05:
                    bridge = max(0.5, bridge + drift)
            else:
                overview = max(0.5, dur - att - bridge)
        else:
            overview = max(0.5, dur - att - bridge)
    parts_dir = dest.parent / "hook-parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    hero = attention_visual(project, cues, script=script)
    intro = parts_dir / "intro.mp4"
    scroll_path = Path(hero["path"]) if hero.get("file") == "canonical-scroll.mp4" and hero.get("path") else None
    if scroll_path and scroll_path.is_file():
        clip_d = min(att, ffprobe_duration(scroll_path))
        _trim_clip(scroll_path, intro, 0.0, clip_d)
        if ffprobe_duration(intro) < att - 0.15:
            _extend_or_trim(intro, intro, att)
    else:
        hero_path = Path(hero["path"]) if hero.get("path") else Path(cues[0]["path"])
        _asset_to_clip(hero_path, intro, att, in_sec=float(hero.get("in_sec") or 0))

    montage_clips: list[Path] = []
    montage_lens = montage_cue_durations(overview, cues, project_root=project.root)
    for i, (cue, cdur) in enumerate(zip(cues, montage_lens)):
        part = parts_dir / f"montage-{i:02d}.mp4"
        _asset_to_clip(Path(cue["path"]), part, cdur, in_sec=float(cue.get("in_sec") or 0))
        montage_clips.append(part)
    montage = parts_dir / "montage.mp4"
    _concat_videos(montage_clips, montage)

    bridge_bg = parts_dir / "bridge-bg.mp4"
    use_scroll_bridge = (
        scroll_path
        and scroll_path.is_file()
        and not skip_scroll
    )
    bridge_src = scroll_path if use_scroll_bridge else Path(cues[0]["path"])
    _asset_to_clip(bridge_src, bridge_bg, bridge)

    body = parts_dir / "body.mp4"
    _concat_videos([intro, montage, bridge_bg], body)
    _extend_or_trim(body, dest, dur)


def _hook_with_launch(launch: Path, dest: Path, dur: float) -> None:
    """Launch B-roll hook for the full segment (no avatar)."""
    _hook_launch_only(launch, dest, dur)


def _outro_with_avatar(heygen: Path, dest: Path, dur: float, bg_png: Path) -> None:
    """Outro CTA slide + circle HeyGen PiP (June roundup deck_thank_you style)."""
    bg_v = dest.parent / "outro-bg.mp4"
    _video_from_image(bg_png, bg_v, dur)
    hg_trim = dest.parent / "outro-heygen.mp4"
    _heygen_bookend_segment(heygen, hg_trim, dur)
    overlay_circle_pip(bg_v, hg_trim, dest, dur)


def _concat_av(parts_v: list[Path], parts_a: list[Path], dest_v: Path, dest_a: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in parts_v:
            f.write(f"file '{p.resolve()}'\n")
        vl = f.name
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in parts_a:
            f.write(f"file '{p.resolve()}'\n")
        al = f.name
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", vl, "-c", "copy", str(dest_v)])
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", al, "-c", "copy", str(dest_a)])


def _mux(v: Path, a: Path, dest: Path) -> None:
    _run([
        "ffmpeg", "-y", "-i", str(v), "-i", str(a),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(dest),
    ])


def _loudnorm(in_path: Path, out_path: Path) -> None:
    _run([
        "ffmpeg", "-y", "-i", str(in_path),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=summary",
        "-c:v", "copy", "-c:a", "aac", str(out_path),
    ])


def _concat_videos(parts: list[Path], dest: Path) -> None:
    if len(parts) == 1:
        shutil.copy2(parts[0], dest)
        return
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in parts:
            f.write(f"file '{p.resolve()}'\n")
        lst = f.name
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", str(dest)])


def _clip_part(parts_dir: Path, clip: dict, seg_len: float, name: str) -> Path:
    part = parts_dir / name
    start = float(clip.get("in_sec") or 0)
    end = float(clip.get("out_sec") or start + seg_len)
    _trim_clip(Path(clip["path"]), part, start, end)
    _extend_or_trim(part, part, seg_len)
    return part


def _assemble_clips_from_lens(
    parts_dir: Path,
    clips: list[dict],
    lens: list[float],
    out: Path,
    dur: float,
) -> Path:
    parts: list[Path] = []
    for i, c in enumerate(clips):
        if i >= len(lens) or lens[i] < 0.25:
            continue
        parts.append(_clip_part(parts_dir, c, lens[i], f"clip-{i}.mp4"))
    merged = parts_dir / "merged.mp4"
    _concat_videos(parts, merged)
    _extend_or_trim(merged, out, dur)
    return out


def _unique_assets(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in items:
        key = item.get("filename") or item.get("path", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _slideshow(parts_dir: Path, assets: list[dict], dur: float, prefix: str) -> list[Path]:
    per = dur / max(1, len(assets))
    vparts: list[Path] = []
    for i, item in enumerate(assets):
        part = parts_dir / f"{prefix}-{i}.mp4"
        _video_from_image(Path(item["path"]), part, per)
        vparts.append(part)
    return vparts


def _point_slideshow(parts_dir: Path, group_key: str, dur: float, prefix: str) -> list[Path]:
    """One rendered text card per talking point — progressive slide feel."""
    specs = slide_specs()[group_key]
    slide_dir = parts_dir / f"{prefix}-slides"
    pngs = render_slide_group(specs, slide_dir)
    per = dur / max(1, len(pngs))
    vparts: list[Path] = []
    for i, png in enumerate(pngs):
        part = parts_dir / f"{prefix}-{i}.mp4"
        _video_from_image(png, part, per)
        vparts.append(part)
    return vparts


def _hook_launch_only(launch: Path, dest: Path, dur: float) -> None:
    """Hook without HeyGen — launch B-roll matches spoken walkthrough intro."""
    launch_dur = min(dur, ffprobe_duration(launch), 15.0)
    _trim_clip(launch, dest, 0.0, launch_dur)
    if launch_dur < dur:
        _extend_or_trim(dest, dest, dur)


def _card_then_clips(
    card: dict,
    clips: list[dict],
    dur: float,
    parts_dir: Path,
    out: Path,
    *,
    card_share: float = 0.38,
) -> Path:
    card_dur = min(14.0, dur * card_share)
    rest = max(1.0, dur - card_dur)
    card_v = parts_dir / "card.mp4"
    _video_from_image(Path(card["path"]), card_v, card_dur)
    clip_dur = rest / max(1, len(clips))
    vparts = [card_v]
    for i, c in enumerate(clips):
        src = Path(c["path"])
        start = float(c.get("in_sec") or 0)
        end = float(c.get("out_sec") or (start + clip_dur))
        part = parts_dir / f"clip-{i}.mp4"
        _trim_clip(src, part, start, end)
        _extend_or_trim(part, part, clip_dur)
        vparts.append(part)
    merged = parts_dir / "merged.mp4"
    _concat_videos(vparts, merged)
    _extend_or_trim(merged, out, dur)
    return out


def _build_beat_video(
    beat: int,
    spec: dict,
    dur: float,
    out_dir: Path,
    assets: Path,
    *,
    merged_srt: Path | None = None,
    beat_t0: float = 0.0,
) -> Path:
    parts_dir = out_dir / f"beat-{beat:02d}-parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"beat-{beat:02d}.mp4"
    clips = spec.get("clips") or []
    generated = _unique_assets(spec.get("generated") or [])
    images = _unique_assets(spec.get("images") or [])

    if beat == 7:
        table = next((g for g in generated if "beat7" in g.get("filename", "")), None)
        gap = next((i for i in images if "fallback-gaps" in i.get("filename", "")), None)
        if not table and not gap and not generated and len(clips) >= 2:
            per = dur / max(1, len(clips))
            parts = []
            for i, c in enumerate(clips):
                part = parts_dir / f"clip-{i}.mp4"
                start = float(c.get("in_sec") or 0)
                end = float(c.get("out_sec") or start + per)
                _trim_clip(Path(c["path"]), part, start, end)
                _extend_or_trim(part, part, per)
                parts.append(part)
            merged = parts_dir / "merged.mp4"
            _concat_videos(parts, merged)
            _extend_or_trim(merged, out, dur)
            return out
        clip_d = 0.0
        parts: list[Path] = []
        if clips:
            clip_d = min(10.0, dur * 0.35)
            clip = clips[0]
            part = parts_dir / "launch-clip.mp4"
            start = float(clip.get("in_sec") or 0)
            end = float(clip.get("out_sec") or start + clip_d)
            _trim_clip(Path(clip["path"]), part, start, end)
            _extend_or_trim(part, part, clip_d)
            parts.append(part)
        table_dur = 0.0
        if table:
            table_dur = min(28.0, max(12.0, (dur - clip_d) * 0.55))
            parts.append(parts_dir / "table.mp4")
            _video_from_image(Path(table["path"]), parts[-1], table_dur)
        rest = max(1.0, dur - clip_d - table_dur)
        if rest > 0.75:
            if gap:
                gap_d = min(18.0, rest * 0.55)
                gap_part = parts_dir / "platform-gaps.mp4"
                _video_from_image(Path(gap["path"]), gap_part, gap_d)
                parts.append(gap_part)
                rest = max(0.0, rest - gap_d)
            if rest > 0.75:
                parts.extend(_point_slideshow(parts_dir, "beat-07-rest", rest, "dev"))
        if not parts and clips:
            clip_dur = dur / max(1, len(clips))
            for i, c in enumerate(clips):
                part = parts_dir / f"clip-{i}.mp4"
                _trim_clip(Path(c["path"]), part, float(c.get("in_sec") or 0), float(c.get("out_sec") or clip_dur))
                _extend_or_trim(part, part, clip_dur)
                parts.append(part)
        if not parts:
            _video_from_image(assets / "generated" / "beat7-api-table.png", out, dur)
            return out
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 1 and clips and not any(
        "views-overlay" in (i.get("filename") or "") for i in images + generated
    ):
        root = out_dir.parent
        lens = clip_durations_for_cues(root, "01-cold-open", dur, [0, 1, 1])
        parts: list[Path] = []
        for i, c in enumerate(clips):
            if i < len(lens):
                parts.append(_clip_part(parts_dir, c, lens[i], f"clip-{i}.mp4"))
        rest = dur - sum(lens[: len(clips)])
        if images and rest > 0.5:
            part = parts_dir / "social.mp4"
            _video_from_image(Path(images[0]["path"]), part, rest)
            parts.append(part)
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 1 and images and not generated:
        headline = next(
            (i for i in images if "headline" in i.get("filename", "") or "views-overlay" in i.get("filename", "")),
            images[0],
        )
        ladder = next(
            (i for i in images if "inequality" in i.get("filename", "") or "social-capture" in i.get("filename", "")),
            images[-1],
        )
        headline_d = dur * 0.20
        parts: list[Path] = []
        off = 0.0
        if clips:
            clip = clips[0]
            clip_d = min(headline_d, dur * 0.22)
            part = parts_dir / "launch.mp4"
            start = float(clip.get("in_sec") or 0)
            end = float(clip.get("out_sec") or start + clip_d)
            _trim_clip(Path(clip["path"]), part, start, end)
            _extend_or_trim(part, part, clip_d)
            parts.append(part)
            off = clip_d
        parts.append(parts_dir / "headline.mp4")
        _video_from_image(Path(headline["path"]), parts[-1], headline_d)
        parts.append(parts_dir / "ladder.mp4")
        _video_from_image(Path(ladder["path"]), parts[-1], max(0.5, dur - off - headline_d))
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 1 and generated:
        ts = out_dir.parent / "segments" / "01-cold-open" / "timestamps.json"
        views_d = beat01_views_duration_sec(
            dur, ts, merged_srt=merged_srt, t0=beat_t0,
        )
        parts = [parts_dir / "views.mp4"]
        _video_from_image(Path(generated[0]["path"]), parts[0], views_d)
        rest = max(0.0, dur - views_d)
        if rest >= 0.75:
            parts.extend(_point_slideshow(parts_dir, "beat-01-rest", rest, "point"))
        if len(parts) == 1:
            _extend_or_trim(parts[0], out, dur)
            return out
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 2 and images and clips:
        img_d = dur * 0.62
        per = img_d / max(1, len(images))
        parts: list[Path] = []
        for i, item in enumerate(images):
            part = parts_dir / f"img-{i}.mp4"
            _video_from_image(Path(item["path"]), part, per)
            parts.append(part)
        clip_d = max(0.5, dur - img_d)
        clip = clips[0]
        part = parts_dir / "clip.mp4"
        start = float(clip.get("in_sec") or 0)
        end = float(clip.get("out_sec") or start + clip_d)
        _trim_clip(Path(clip["path"]), part, start, end)
        _extend_or_trim(part, part, clip_d)
        parts.append(part)
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 2 and generated:
        tier_d = dur * 0.38
        rest = max(0.0, dur - tier_d)
        parts = [parts_dir / "tier.mp4"]
        _video_from_image(Path(generated[0]["path"]), parts[0], tier_d)
        if rest >= 0.75:
            parts.extend(_point_slideshow(parts_dir, "beat-02-extra", rest, "tierpt"))
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 3 and generated and clips:
        social = next(
            (i for i in images if "social-capture" in (i.get("filename") or "").lower()),
            None,
        )
        if social:
            soc_d = min(14.0, dur * 0.32)
            card_d = min(12.0, dur * 0.26)
            rest = max(1.0, dur - soc_d - card_d)
            parts: list[Path] = [
                parts_dir / "social.mp4",
                parts_dir / "card.mp4",
            ]
            _video_from_image(Path(social["path"]), parts[0], soc_d)
            _video_from_image(Path(generated[0]["path"]), parts[1], card_d)
            clip_dur = rest / max(1, len(clips))
            for i, c in enumerate(clips):
                src = Path(c["path"])
                start = float(c.get("in_sec") or 0)
                end = float(c.get("out_sec") or (start + clip_dur))
                part = parts_dir / f"clip-{i}.mp4"
                _trim_clip(src, part, start, end)
                _extend_or_trim(part, part, clip_dur)
                parts.append(part)
            merged = parts_dir / "merged.mp4"
            _concat_videos(parts, merged)
            _extend_or_trim(merged, out, dur)
            return out
        return _card_then_clips(generated[0], clips, dur, parts_dir, out)

    if beat == 5 and clips:
        stat = generated[0] if generated else None
        stat_share = 0.32 if stat else 0.0
        clip_total = max(1.0, dur * (1.0 - stat_share))
        poke = next((c for c in clips if "pokemon" in c.get("filename", "")), None)
        others = sorted(
            [c for c in clips if c is not poke],
            key=lambda c: {"carousel-solar.mp4": 0, "carousel-fluid.mp4": 1}.get(c.get("filename", ""), 99),
        )
        parts: list[Path] = []
        if poke:
            poke_dur = clip_total * 0.55
            part = parts_dir / "poke.mp4"
            start = float(poke.get("in_sec") or 0)
            _trim_clip(Path(poke["path"]), part, start, start + poke_dur)
            _extend_or_trim(part, part, poke_dur)
            parts.append(part)
            rest = clip_total - poke_dur
        else:
            rest = clip_total
        if others and rest > 0:
            per = rest / len(others)
            for i, c in enumerate(others):
                src = Path(c["path"])
                start = float(c.get("in_sec") or 0)
                part = parts_dir / f"clip-{i}.mp4"
                _trim_clip(src, part, start, start + per)
                _extend_or_trim(part, part, per)
                parts.append(part)
        if stat:
            stat_v = parts_dir / "stat.mp4"
            _video_from_image(Path(stat["path"]), stat_v, dur - clip_total)
            parts.append(stat_v)
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 6 and images:
        from praisonaippt.daily_single.cue_slide_sync import assemble_beat6_from_cues

        v2_only = all(
            (i.get("filename") or "").startswith("v2-") for i in images
        )
        if not v2_only:
            project_root = out_dir.parent
            seg_srt = project_root / "segments" / "06-safeguards" / "segment.srt"
            merged_srt = project_root / "merge" / "final.srt"
            t0 = 0.0
            tl_path = project_root / "merge" / "timeline.json"
            if tl_path.is_file():
                tl = json.loads(tl_path.read_text(encoding="utf-8"))
                for row in tl.get("segments") or []:
                    if row.get("id") == "beat-06":
                        t0 = float(row["start_sec"])
                        break
            built = assemble_beat6_from_cues(
                parts_dir, seg_srt, images, out, dur, t0=t0, merged_srt=merged_srt,
            )
            if built:
                return out

    if beat == 8 and generated:
        slides = generated + [i for i in images if "protein" in i.get("filename", "")]
        vparts = _slideshow(parts_dir, slides[:2], dur, "img")
        merged = parts_dir / "merged.mp4"
        _concat_videos(vparts, merged)
        shutil.copy2(merged, out)
        return out

    if beat == 4 and clips and images and not generated:
        chart_d, clip_d, tail_d = beat4_visual_durations(out_dir.parent, dur)
        parts: list[Path] = []
        parts.append(parts_dir / "chart-0.mp4")
        _video_from_image(Path(images[0]["path"]), parts[-1], chart_d)
        parts.append(_clip_part(parts_dir, clips[0], clip_d, "pokemon.mp4"))
        if tail_d >= 0.25:
            parts.append(parts_dir / "chart-1.mp4")
            _video_from_image(Path(images[0]["path"]), parts[-1], tail_d)
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 4 and generated and images:
        parts: list[Path] = []
        off = 0.0
        if clips:
            clip_d = min(14.0, dur * 0.28)
            clip = clips[0]
            part = parts_dir / "demo-clip.mp4"
            start = float(clip.get("in_sec") or 0)
            end = float(clip.get("out_sec") or start + clip_d)
            _trim_clip(Path(clip["path"]), part, start, end)
            _extend_or_trim(part, part, clip_d)
            parts.append(part)
            off = clip_d
        slides = images[:1] + generated
        remain = max(0.5, dur - off)
        per = remain / max(1, len(slides))
        for i, item in enumerate(slides):
            part = parts_dir / f"bench-{i}.mp4"
            _video_from_image(Path(item["path"]), part, per)
            parts.append(part)
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 9 and images and not clips and not generated:
        pricing = next((i for i in images if "pricing" in i.get("filename", "")), images[0])
        bench = next((i for i in images if "benchmark" in i.get("filename", "")), images[-1])
        p_d, b_d, tail_d = beat9_visual_durations(out_dir.parent, dur)
        parts: list[Path] = []
        parts.append(parts_dir / "price-0.mp4")
        _video_from_image(Path(pricing["path"]), parts[-1], p_d)
        parts.append(parts_dir / "bench-0.mp4")
        _video_from_image(Path(bench["path"]), parts[-1], b_d)
        if tail_d >= 0.25:
            parts.append(parts_dir / "price-1.mp4")
            _video_from_image(Path(pricing["path"]), parts[-1], tail_d)
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 9 and images and any("v2-pricing" in i.get("filename", "") for i in images):
        fracs = (0.38, 0.30, 0.32)
        parts: list[Path] = []
        off = 0.0
        for i, item in enumerate(images[:3]):
            frac = fracs[i] if i < len(fracs) else max(0.1, 1.0 - off)
            part = parts_dir / f"price-{i}.mp4"
            seg_d = dur * frac
            _video_from_image(Path(item["path"]), part, seg_d)
            parts.append(part)
            off += frac
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        shutil.copy2(merged, out)
        return out

    if beat == 10 and clips and images:
        clip_d = dur * 0.72
        per = clip_d / max(1, len(clips))
        parts: list[Path] = []
        for i, c in enumerate(clips):
            part = parts_dir / f"clip-{i}.mp4"
            start = float(c.get("in_sec") or 0)
            end = float(c.get("out_sec") or start + per)
            _trim_clip(Path(c["path"]), part, start, end)
            _extend_or_trim(part, part, per)
            parts.append(part)
        rest = max(0.5, dur - clip_d)
        part = parts_dir / "align.mp4"
        _video_from_image(Path(images[0]["path"]), part, rest)
        parts.append(part)
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        shutil.copy2(merged, out)
        return out

    if beat == 10:
        v2_slides = [
            i for i in (images or []) + (generated or [])
            if (i.get("filename") or "").startswith("v2-")
        ]
        if v2_slides:
            vparts = _slideshow(parts_dir, v2_slides, dur, "img")
            merged = parts_dir / "merged.mp4"
            _concat_videos(vparts, merged)
            shutil.copy2(merged, out)
            return out

        align = next((i for i in images if "alignment" in i.get("filename", "")), None)
        jail = next((i for i in images if "jailbreak" in i.get("filename", "")), None)
        if not jail and (assets / "jailbreak-resistance.png").is_file():
            jail = {"path": str(assets / "jailbreak-resistance.png"), "filename": "jailbreak-resistance.png"}
        if not align and (assets / "alignment-chart.png").is_file():
            align = {"path": str(assets / "alignment-chart.png"), "filename": "alignment-chart.png"}
        jail_d, align_d, tail_d = beat10_chart_durations(out_dir.parent, dur)
        weighted = [(jail, jail_d), (align, align_d), (jail, tail_d)]
        slides = [s for s, _ in weighted if s]
        if not slides and images:
            slides = [images[0]]
        if slides:
            parts: list[Path] = []
            for i, (spec, seg_len) in enumerate(weighted):
                if not spec:
                    continue
                part = parts_dir / f"close-{i}-{spec['filename']}.mp4"
                _video_from_image(Path(spec["path"]), part, seg_len)
                parts.append(part)
            merged = parts_dir / "merged.mp4"
            _concat_videos(parts, merged)
            shutil.copy2(merged, out)
            return out

    if images and not clips:
        vparts = _slideshow(parts_dir, images, dur, "img")
        merged = parts_dir / "merged.mp4"
        _concat_videos(vparts, merged)
        shutil.copy2(merged, out)
        return out

    beat_cue_clips: dict[int, tuple[str, list[int]]] = {
        2: ("02-mythos-tier", [0, 0, 1]),
        3: ("03-engineers-care", [0, 1, 1, 1]),
        5: ("05-vision-memory", [0, 1, 1]),
        6: ("06-safeguards", [0, 1, 1, 1]),
        7: ("07-api-integration", [0, 1]),
    }
    if beat == 8 and clips and not generated and not images:
        lens = beat8_clip_durations(out_dir.parent, dur)
        if len(lens) == len(clips):
            return _assemble_clips_from_lens(parts_dir, clips, lens, out, dur)
    if beat in beat_cue_clips and clips and not generated and not images:
        seg_dir, cue_map = beat_cue_clips[beat]
        lens = clip_durations_for_cues(out_dir.parent, seg_dir, dur, cue_map)
        if len(lens) == len(clips):
            return _assemble_clips_from_lens(parts_dir, clips, lens, out, dur)

    if clips:
        clip_dur = dur / max(1, len(clips))
        vparts = []
        for i, c in enumerate(clips):
            src = Path(c["path"])
            start = float(c.get("in_sec") or 0)
            end = float(c.get("out_sec") or (start + clip_dur))
            part = parts_dir / f"clip-{i}.mp4"
            _trim_clip(src, part, start, end)
            _extend_or_trim(part, part, clip_dur)
            vparts.append(part)
        base = vparts[0] if len(vparts) == 1 else parts_dir / "merged.mp4"
        if len(vparts) > 1:
            _concat_videos(vparts, base)
        overlay = next((g for g in generated if g.get("filename")), None)
        if overlay and beat not in (1,):
            _overlay_png(base, Path(overlay["path"]), out, dur)
        else:
            _extend_or_trim(base, out, dur)
        return out

    if generated:
        _video_from_image(Path(generated[0]["path"]), out, dur)
        return out
    if images:
        _video_from_image(Path(images[0]["path"]), out, dur)
        return out
    _video_from_image(assets / "generated" / "beat2-tier-diagram.png", out, dur)
    return out


def _segment_audio(project: DailySingleProject, seg_dir: str) -> Path:
    return project.segment_narration(seg_dir)


def assemble(project: DailySingleProject) -> Path:
    """Build beats/*.mp4 and merge/final.mp4 from segment narration + beat-map."""
    load_env()
    require_keys("ELEVEN_API_KEY")
    beat_map = json.loads(project.beat_map_path.read_text(encoding="utf-8"))
    beats = beat_map.get("beats") or {}
    project.beats_dir.mkdir(parents=True, exist_ok=True)
    project.merge_dir.mkdir(parents=True, exist_ok=True)

    narr = project.merge_dir / "narration.mp3"
    if not narr.is_file() or narr.stat().st_size < 5000:
        synthesise_segments(project)

    vparts: list[Path] = []
    aparts: list[Path] = []
    bumper_done = False
    t_cursor = 0.0
    merged_srt = project.merge_dir / "final.srt"

    for label, seg_dir, beat in SEGMENT_ORDER:
        audio = _segment_audio(project, seg_dir)
        if not audio.is_file():
            raise RuntimeError(f"Missing narration: {audio}")
        seg_a = (
            project.beats_dir / f"{label}-a.mp3"
            if label in ("00-hook", "99-outro")
            else project.beats_dir / f"beat-{beat:02d}-a.mp3"
        )
        shutil.copy2(audio, seg_a)
        dur = max(3.0, ffprobe_duration(seg_a))

        if label == "00-hook":
            hook_v = project.beats_dir / "00-hook.mp4"
            launch = project.assets_dir / "videos" / "claudeai-launch.mp4"
            plan = build_hook_montage_plan(project)
            cues = [c for c in plan.get("cues") or [] if c.get("ok") and c.get("path")]
            if len(cues) >= 3:
                _hook_montage(project, launch, hook_v, dur)
            elif launch.is_file():
                _hook_launch_only(launch, hook_v, dur)
            else:
                _video_from_image(project.assets_dir / "generated" / "beat2-tier-diagram.png", hook_v, dur)
            vparts.append(hook_v)
            aparts.append(seg_a)
            t_cursor += dur
            if not bumper_done:
                bumper = prepare_brand_bumper(project.beats_dir)
                if bumper:
                    vparts.append(bumper[0])
                    aparts.append(bumper[1])
                    bumper_done = True
                    t_cursor += ffprobe_duration(bumper[1])
            continue
        elif label == "99-outro":
            outro_v = project.beats_dir / "99-outro.mp4"
            heygen_out = project.segments_dir / "99-outro" / "heygen.mp4"
            cta_dir = project.beats_dir / "outro-slides"
            cta_png = render_slide_group(
                outro_slide_specs(beat_map_variant(project)), cta_dir,
            )[0]
            if heygen_out.is_file():
                _outro_with_avatar(heygen_out, outro_v, dur, cta_png)
            else:
                _video_from_image(cta_png, outro_v, dur)
            vparts.append(outro_v)
        else:
            spec = beats[str(beat)]
            beat_v = _build_beat_video(
                beat, spec, dur, project.beats_dir, project.assets_dir,
                merged_srt=merged_srt if merged_srt.is_file() else None,
                beat_t0=t_cursor if beat == 1 else 0.0,
            )
            vparts.append(beat_v)
            print(f"Beat {beat}: {dur:.1f}s")
            t_cursor += dur
        aparts.append(seg_a)

    silent_v = project.merge_dir / "final-silent.mp4"
    full_a = project.merge_dir / "full-narration-sync.mp3"
    _concat_av(vparts, aparts, silent_v, full_a)
    with_audio = project.merge_dir / "final-with-audio.mp4"
    _mux(silent_v, full_a, with_audio)
    final = project.merge_dir / "final.mp4"
    _loudnorm(with_audio, final)
    print(f"Final: {final} ({ffprobe_duration(final):.1f}s)")
    return final
