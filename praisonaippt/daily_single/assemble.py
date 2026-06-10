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
    attention_hero,
    build_hook_montage_plan,
    hook_sentence_durations,
    montage_cue_durations,
)
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
    heygen: Path,
    launch: Path,
    dest: Path,
    dur: float,
) -> None:
    """June-style hook: hero attention → phrase montage → HeyGen bridge."""
    script = project.segment_script("00-hook").read_text(encoding="utf-8")
    plan = build_hook_montage_plan(project)
    cues = [c for c in plan.get("cues") or [] if c.get("ok") and c.get("path")]
    if len(cues) < 3:
        _hook_with_launch(heygen, launch, dest, dur)
        return

    att, overview, bridge = hook_sentence_durations(dur, script)
    parts_dir = dest.parent / "hook-parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    hero = attention_hero(cues)
    hero_path = Path(hero["path"])
    intro = parts_dir / "intro.mp4"
    _video_from_image(hero_path, intro, att)

    montage_clips: list[Path] = []
    for i, (cue, cdur) in enumerate(zip(cues, montage_cue_durations(overview, cues))):
        part = parts_dir / f"montage-{i:02d}.mp4"
        _video_from_image(Path(cue["path"]), part, cdur)
        montage_clips.append(part)
    montage = parts_dir / "montage.mp4"
    _concat_videos(montage_clips, montage)

    hg_part = parts_dir / "avatar.mp4"
    _heygen_bookend_segment(heygen, hg_part, bridge)
    bg_tail = parts_dir / "bg-tail.mp4"
    _video_from_image(hero_path, bg_tail, bridge)
    tail_v = parts_dir / "tail.mp4"
    _run([
        "ffmpeg", "-y", "-i", str(bg_tail), "-i", str(hg_part),
        "-filter_complex",
        f"[1:v]scale=480:-1[pip];[0:v]{_scale_pad_filter()}[bg];"
        f"[bg][pip]overlay=W-w-60:H-h-60[v]",
        "-map", "[v]", "-t", f"{bridge:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(tail_v),
    ])
    _concat_videos([intro, montage, tail_v], dest)


def _hook_with_launch(heygen: Path, launch: Path, dest: Path, dur: float) -> None:
    """B-roll full-screen for hook + overview; presenter pip for the bridge."""
    launch_dur = min(30.0, ffprobe_duration(launch))
    split = max(4.0, dur * 0.72)
    tail = max(2.0, dur - split)
    launch_part = dest.parent / "hook-launch.mp4"
    _trim_clip(launch, launch_part, 0, min(launch_dur, split + 2.0))
    intro = dest.parent / "hook-intro.mp4"
    _extend_or_trim(launch_part, intro, split)
    hg_part = dest.parent / "hook-avatar.mp4"
    _heygen_bookend_segment(heygen, hg_part, tail)
    bg_tail = dest.parent / "hook-bg-tail.mp4"
    _extend_or_trim(launch_part, bg_tail, tail)
    tail_v = dest.parent / "hook-tail.mp4"
    _run([
        "ffmpeg", "-y", "-i", str(bg_tail), "-i", str(hg_part),
        "-filter_complex",
        f"[1:v]scale=480:-1[pip];[0:v]{_scale_pad_filter()}[bg];"
        f"[bg][pip]overlay=W-w-60:H-h-60[v]",
        "-map", "[v]", "-t", f"{tail:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(tail_v),
    ])
    _concat_videos([intro, tail_v], dest)


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


def _build_beat_video(beat: int, spec: dict, dur: float, out_dir: Path, assets: Path) -> Path:
    parts_dir = out_dir / f"beat-{beat:02d}-parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"beat-{beat:02d}.mp4"
    clips = spec.get("clips") or []
    generated = _unique_assets(spec.get("generated") or [])
    images = _unique_assets(spec.get("images") or [])

    if beat == 7:
        table = next((g for g in generated if "beat7" in g.get("filename", "")), None)
        table_dur = min(28.0, max(12.0, dur * 0.5))
        rest = max(1.0, dur - table_dur)
        flow = assets / "gpt-image-safeguard-fallback.png"
        parts: list[Path] = []
        if table:
            parts.append(parts_dir / "table.mp4")
            _video_from_image(Path(table["path"]), parts[0], table_dur)
        if flow.is_file() and rest > 0:
            parts.append(parts_dir / "flow.mp4")
            _video_from_image(flow, parts[-1], rest)
        elif table:
            _extend_or_trim(parts[0], out, dur)
            return out
        else:
            _video_from_image(assets / "generated" / "beat7-api-table.png", out, dur)
            return out
        merged = parts_dir / "merged.mp4"
        _concat_videos(parts, merged)
        _extend_or_trim(merged, out, dur)
        return out

    if beat == 1 and generated:
        _video_from_image(Path(generated[0]["path"]), out, dur)
        return out

    if beat == 3 and generated and clips:
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
        order = ("safeguard", "fallback", "bio-aav", "cyber", "jailbreak", "distillation", "d3c3efe0")
        ranked = sorted(
            images,
            key=lambda i: next((n for n, k in enumerate(order) if k in i.get("filename", "").lower()), 99),
        )
        vparts = _slideshow(parts_dir, ranked[:4], dur, "img")
        merged = parts_dir / "merged.mp4"
        _concat_videos(vparts, merged)
        shutil.copy2(merged, out)
        return out

    if beat == 8 and generated:
        slides = generated + [i for i in images if "protein" in i.get("filename", "")]
        vparts = _slideshow(parts_dir, slides[:2], dur, "img")
        merged = parts_dir / "merged.mp4"
        _concat_videos(vparts, merged)
        shutil.copy2(merged, out)
        return out

    if beat == 4 and generated and images:
        slides = images[:1] + generated
        vparts = _slideshow(parts_dir, slides, dur, "img")
        merged = parts_dir / "merged.mp4"
        _concat_videos(vparts, merged)
        shutil.copy2(merged, out)
        return out

    if beat == 10:
        align = next((i for i in images if "alignment" in i.get("filename", "")), None)
        jail = next((i for i in images if "jailbreak" in i.get("filename", "")), None)
        if not jail and (assets / "jailbreak-resistance.png").is_file():
            jail = {"path": str(assets / "jailbreak-resistance.png"), "filename": "jailbreak-resistance.png"}
        if not align and (assets / "alignment-chart.png").is_file():
            align = {"path": str(assets / "alignment-chart.png"), "filename": "alignment-chart.png"}
        weighted = [(jail, 0.65), (align, 0.35)]
        slides = [s for s, _ in weighted if s]
        if not slides and images:
            slides = [images[0]]
        if slides:
            parts: list[Path] = []
            for spec, frac in weighted:
                if not spec:
                    continue
                part = parts_dir / f"close-{spec['filename']}.mp4"
                _video_from_image(Path(spec["path"]), part, dur * frac)
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
            heygen_hook = project.segments_dir / "00-hook" / "heygen.mp4"
            launch = project.assets_dir / "videos" / "claudeai-launch.mp4"
            if heygen_hook.is_file() and launch.is_file():
                _hook_montage(project, heygen_hook, launch, hook_v, dur)
            elif heygen_hook.is_file():
                _heygen_bookend_segment(heygen_hook, hook_v, dur)
            elif launch.is_file():
                _hook_launch_only(launch, hook_v, dur)
            else:
                _video_from_image(project.assets_dir / "generated" / "beat2-tier-diagram.png", hook_v, dur)
            vparts.append(hook_v)
        elif label == "99-outro":
            outro_v = project.beats_dir / "99-outro.mp4"
            heygen_out = project.segments_dir / "99-outro" / "heygen.mp4"
            if heygen_out.is_file():
                _heygen_bookend_segment(heygen_out, outro_v, dur)
            else:
                api_card = project.assets_dir / "generated" / "beat7-api-table.png"
                _video_from_image(api_card if api_card.is_file() else project.assets_dir / "generated" / "beat9-pricing.png", outro_v, dur)
            vparts.append(outro_v)
        else:
            spec = beats[str(beat)]
            beat_v = _build_beat_video(beat, spec, dur, project.beats_dir, project.assets_dir)
            vparts.append(beat_v)
            print(f"Beat {beat}: {dur:.1f}s")
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
