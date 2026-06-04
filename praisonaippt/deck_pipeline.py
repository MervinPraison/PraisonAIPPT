"""Deck QA pipeline: validate, sync, gates, and optional build/export via protocols."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import yaml

from .ffmpeg_composer import (
    ffprobe_duration,
    ffprobe_has_audio,
    ffprobe_media_size,
    ffprobe_video_fps,
)
from .schema import validate_verses
from .transcript_loader import load_whisper_json
from .utils import resolve_asset_path
from .pipeline_protocols import (
    BuildFn,
    ExportFn,
    default_build_presentation,
    default_export_deck_video,
)
from .variant_sync import sync_variants_from_master, variants_drift
from .video_presets import expected_video_spec

RIGHTS_CHECKLIST = [
    "HeyGen avatar and voice licence permits this use",
    "Background music (if any) is licensed for distribution",
    "Stock images in deck are licensed or owned",
    "Script matches published article / approved copy",
]

# CI gate names (stable keys for report.json → gates)
GATE_UNIFIED_PIPELINE = "unified_pipeline"
GATE_PRE_RENDER = "pre_render"
GATE_POST_RENDER = "post_render"
GATE_AV_SYNC = "av_sync"
GATE_PIP_CENTRING = "pip_centring"
GATE_SLIDE_JPEG_GOLDEN = "slide_jpeg_golden"
GATE_PLAN_APPROVAL = "plan_approval"
GATE_RIGHTS = "rights_licensing"


def _expected_video_spec(data: dict) -> Dict[str, int]:
    """Backward-compatible alias for :func:`video_presets.expected_video_spec`."""
    return expected_video_spec(data)


@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineReport:
    ok: bool
    deck_yaml: str
    started_at: str
    steps: List[StepResult] = field(default_factory=list)
    outputs: Dict[str, str] = field(default_factory=dict)
    rights_checklist: List[str] = field(default_factory=lambda: list(RIGHTS_CHECKLIST))

    def add(self, step: StepResult) -> None:
        self.steps.append(step)
        if not step.ok:
            self.ok = False

    def gates_summary(self) -> Dict[str, Dict[str, Any]]:
        """Map CI gate names to latest step outcome."""
        mapping = {
            GATE_PLAN_APPROVAL: ("plan_approval",),
            GATE_RIGHTS: ("rights_licensing",),
            GATE_PRE_RENDER: ("schema", "assets"),
            GATE_AV_SYNC: ("av_sync", "timing_drift"),
            GATE_PIP_CENTRING: ("pip_centring",),
            GATE_SLIDE_JPEG_GOLDEN: ("slide_jpegs",),
            GATE_POST_RENDER: ("post_render",),
            GATE_UNIFIED_PIPELINE: ("export_mp4", "build_pptx"),
        }
        by_name = {s.name: s for s in self.steps}
        out: Dict[str, Dict[str, Any]] = {}
        for gate, names in mapping.items():
            steps = [by_name[n] for n in names if n in by_name]
            if not steps:
                out[gate] = {"ok": None, "detail": "not run", "validated": False}
                continue
            ok = all(s.ok for s in steps)
            out[gate] = {
                "ok": ok,
                "detail": "; ".join(s.detail for s in steps),
                "validated": True,
            }
        return out

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "exit_code": 0 if self.ok else 1,
            "deck_yaml": self.deck_yaml,
            "started_at": self.started_at,
            "steps": [asdict(s) for s in self.steps],
            "gates": self.gates_summary(),
            "outputs": self.outputs,
            "rights_checklist": self.rights_checklist,
        }

    def write_json(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return p


def iter_verses(data: dict) -> List[dict]:
    out: List[dict] = []
    for sec in data.get("sections") or []:
        out.extend(sec.get("verses") or [])
    return out


def expected_deck_duration(data: dict) -> float:
    vex = data.get("video_export") or {}
    title = float(vex.get("slide_duration_sec") or 3.0)
    return title + sum(float(v.get("duration_sec") or 0) for v in iter_verses(data))


def validate_deck_schema(data: dict) -> StepResult:
    try:
        validate_verses(data)
        return StepResult("schema", True, "Deck passed schema validation")
    except Exception as e:
        return StepResult("schema", False, str(e))


def validate_deck_assets(data: dict, *, source_file: Optional[str] = None) -> StepResult:
    """Pre-render ffprobe checks for referenced media paths."""
    missing: List[str] = []
    bad: List[str] = []
    checked: Dict[str, Any] = {}

    def _check(path: str, label: str) -> None:
        resolved = resolve_asset_path(path, source_file=source_file) or path
        p = Path(resolved)
        if not p.is_file():
            missing.append(f"{label}: {path}")
            return
        try:
            if p.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}:
                dur = ffprobe_duration(str(p))
                w, h = ffprobe_media_size(str(p))
                checked[label] = {
                    "path": str(p),
                    "duration_sec": round(dur, 3),
                    "width": w,
                    "height": h,
                    "has_audio": ffprobe_has_audio(str(p)),
                }
            elif p.suffix.lower() in {".mp3", ".wav", ".m4a", ".aac"}:
                checked[label] = {
                    "path": str(p),
                    "duration_sec": round(ffprobe_duration(str(p)), 3),
                }
        except Exception as e:
            bad.append(f"{label}: {e}")

    for v in iter_verses(data):
        if v.get("avatar_video_path"):
            _check(str(v["avatar_video_path"]), "avatar_video")
            break
    for v in iter_verses(data):
        if v.get("audio_path"):
            _check(str(v["audio_path"]), "narration_audio")
            break

    if missing or bad:
        detail = "; ".join(missing + bad)
        return StepResult("assets", False, detail, {"checked": checked})
    return StepResult("assets", True, f"Checked {len(checked)} media file(s)", {"checked": checked})


def check_timing_drift(
    data: dict,
    transcript_path: str | Path,
    *,
    max_start_drift_sec: float = 1.5,
    max_duration_drift_sec: float = 2.0,
) -> StepResult:
    """Compare verse audio_start_sec / duration_sec to Whisper segment groups."""
    td = load_whisper_json(transcript_path)
    from .plan_slides import draft_verses_from_transcript

    ref = draft_verses_from_transcript(td)
    actual = iter_verses(data)
    drifts: List[str] = []
    for i, (a, r) in enumerate(zip(actual, ref)):
        ds = abs(float(a.get("audio_start_sec") or 0) - float(r["audio_start_sec"]))
        dd = abs(float(a.get("duration_sec") or 0) - float(r["duration_sec"]))
        if ds > max_start_drift_sec:
            drifts.append(f"verse[{i}] start drift {ds:.2f}s")
        if dd > max_duration_drift_sec:
            drifts.append(f"verse[{i}] duration drift {dd:.2f}s")
    if len(actual) != len(ref):
        drifts.append(f"verse count deck={len(actual)} transcript={len(ref)}")
    whisper_end = td.segments[-1].end if td.segments else td.duration
    deck_end = float(actual[-1].get("audio_start_sec") or 0) + float(actual[-1].get("duration_sec") or 0) if actual else 0
    if abs(deck_end - whisper_end) > max_duration_drift_sec + 1.0:
        drifts.append(f"wall-clock end drift {abs(deck_end - whisper_end):.2f}s")
    if drifts:
        return StepResult("timing_drift", False, "; ".join(drifts), {"drifts": drifts})
    return StepResult("timing_drift", True, "Timing aligned with Whisper verse reference")


def validate_plan_approval(
    pipe: dict,
    *,
    base_dir: Optional[Path] = None,
) -> StepResult:
    from .plan_slides import check_plan_approval_gate

    ok, detail = check_plan_approval_gate(pipe, base_dir=base_dir)
    return StepResult("plan_approval", ok, detail)


def validate_rights_licensing(pipe: dict) -> StepResult:
    """Publish blocker when pipeline.require_rights_ack and not acknowledged."""
    require = bool(pipe.get("require_rights_ack"))
    ack = bool(pipe.get("rights_acknowledged"))
    data = {"items": list(RIGHTS_CHECKLIST), "acknowledged": ack, "required": require}
    if not require:
        return StepResult(
            "rights_licensing",
            True,
            "Rights checklist recorded (set require_rights_ack for CI blocker)",
            data,
        )
    if not ack:
        return StepResult(
            "rights_licensing",
            False,
            "Set pipeline.rights_acknowledged: true after reviewing rights_checklist",
            data,
        )
    return StepResult("rights_licensing", True, "Rights/licensing acknowledged", data)


def _media_paths_from_deck(data: dict, *, source_file: Optional[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for v in iter_verses(data):
        if v.get("avatar_video_path") and "avatar_video" not in out:
            av = str(v["avatar_video_path"])
            out["avatar_video"] = resolve_asset_path(av, source_file=source_file) or av
        if v.get("audio_path") and "narration_audio" not in out:
            ap = str(v["audio_path"])
            out["narration_audio"] = resolve_asset_path(ap, source_file=source_file) or ap
    return out


def check_av_sync(
    data: dict,
    *,
    source_file: Optional[str] = None,
    transcript_path: Optional[str | Path] = None,
    duration_tolerance_sec: float = 2.5,
) -> StepResult:
    """Numeric A/V checks: ffprobe media duration vs deck wall-clock and Whisper."""
    media = _media_paths_from_deck(data, source_file=source_file)
    expected = expected_deck_duration(data)
    issues: List[str] = []
    metrics: Dict[str, Any] = {"expected_deck_sec": round(expected, 3)}

    whisper_dur: Optional[float] = None
    if transcript_path and Path(transcript_path).is_file():
        td = load_whisper_json(transcript_path)
        whisper_dur = float(td.duration or (td.segments[-1].end if td.segments else 0))
        metrics["whisper_duration_sec"] = round(whisper_dur, 3)

    for label, path in media.items():
        p = Path(path)
        if not p.is_file():
            continue
        try:
            dur = ffprobe_duration(str(p))
        except Exception as e:
            issues.append(f"{label} ffprobe: {e}")
            continue
        metrics[f"{label}_duration_sec"] = round(dur, 3)
        if abs(dur - expected) > duration_tolerance_sec + 3.0:
            issues.append(
                f"{label} duration {dur:.1f}s vs deck {expected:.1f}s "
                f"(tol {duration_tolerance_sec}s)",
            )
        if whisper_dur is not None and abs(dur - whisper_dur) > duration_tolerance_sec + 2.0:
            issues.append(
                f"{label} duration {dur:.1f}s vs Whisper {whisper_dur:.1f}s",
            )

    if whisper_dur is not None:
        actual = iter_verses(data)
        if actual:
            deck_end = float(actual[-1].get("audio_start_sec") or 0) + float(
                actual[-1].get("duration_sec") or 0,
            )
            metrics["deck_wall_clock_end_sec"] = round(deck_end, 3)
            if abs(deck_end - whisper_dur) > duration_tolerance_sec + 1.0:
                issues.append(
                    f"deck wall-clock end {deck_end:.1f}s vs Whisper {whisper_dur:.1f}s",
                )

    if issues:
        return StepResult("av_sync", False, "; ".join(issues), metrics)
    return StepResult("av_sync", True, "Media durations align with deck and Whisper", metrics)


def _pip_probe_passes(
    metrics: Any,
    advice: Any,
    *,
    max_offset_x: float,
    max_offset_y: float,
    max_lr_delta: float = 0.08,
) -> bool:
    """True when face is detected and centring matches integration-test limits."""
    if metrics.face_fx is None:
        return False
    if advice.is_centred:
        return True
    lr = metrics.margin_lr_delta
    lr_ok = lr is None or abs(lr) <= max_lr_delta
    return (
        abs(metrics.centre_offset_x) <= max_offset_x
        and abs(metrics.centre_offset_y) <= max_offset_y
        and lr_ok
    )


def validate_pip_centring(
    data: dict,
    *,
    source_file: Optional[str] = None,
    max_offset_x: float = 0.05,
    max_offset_y: float = 0.08,
    slide_index: Optional[int] = None,
    require_all_seeks: bool = False,
) -> StepResult:
    from .avatar_calibrate import (
        collect_avatar_seek_samples,
        maybe_auto_calibrate_deck,
        pip_probe_size_px,
    )
    from .pip_face_measure import centring_advice, measure_pip_video

    data = maybe_auto_calibrate_deck(
        dict(data),
        source_file=source_file,
    )
    pip = ((data.get("slide_style") or {}).get("layouts") or {}).get("pip") or {}
    crop_x = float(pip.get("crop_x_ratio") or 0.5)
    crop_y = float(pip.get("crop_y_ratio") or 0.03)
    zoom = float(pip.get("zoom_ratio") or 1.45)
    shape = str(pip.get("shape") or pip.get("pip_shape") or "circle")
    from .avatar_calibrate import pip_probe_dims_for_shape

    pw, ph = pip_probe_dims_for_shape(data.get("slide_style") or {}, shape)

    verses = iter_verses(data)
    probes: List[dict] = []
    passes = 0

    if slide_index is not None and 1 <= slide_index <= len(verses):
        seek_jobs: List[Tuple[Optional[int], str, float]] = []
        verse = verses[slide_index - 1]
        av = verse.get("avatar_video_path")
        if av:
            seek_jobs.append((
                slide_index,
                str(av),
                max(0.0, float(verse.get("audio_start_sec") or 0) + 0.35),
            ))
    else:
        samples = collect_avatar_seek_samples(data)
        seek_jobs = []
        for av_path, seeks in samples.items():
            for seek in seeks:
                seek_jobs.append((None, av_path, seek))

    if not seek_jobs:
        return StepResult("pip_centring", True, "No avatar slides to validate")

    for slide_n, av, seek in seek_jobs:
        resolved = resolve_asset_path(av, source_file=source_file) or av
        metrics, probe = measure_pip_video(
            resolved,
            seek_sec=seek,
            crop_x=crop_x,
            crop_y=crop_y,
            zoom=zoom,
            width=pw,
            height=ph,
            shape=shape,
        )
        advice = centring_advice(metrics)
        ok = _pip_probe_passes(
            metrics, advice,
            max_offset_x=max_offset_x,
            max_offset_y=max_offset_y,
        )
        if ok:
            passes += 1
        probes.append({
            "slide": slide_n,
            "seek_sec": seek,
            "centred": advice.is_centred,
            "pass": ok,
            "offset_x": advice.offset_x,
            "offset_y": advice.offset_y,
            "probe": str(probe),
            "face_detected": metrics.face_fx is not None,
        })

    if passes == 0:
        no_face = all(not p.get("face_detected") for p in probes)
        detail = (
            "Face not detected on any calibration seek"
            if no_face
            else "No seek passed PiP centring QA; adjust crop_x/crop_y or re-calibrate"
        )
        return StepResult("pip_centring", False, detail, {"probes": probes})

    if require_all_seeks and passes < len(probes):
        return StepResult(
            "pip_centring",
            False,
            f"Strict PiP QA: {passes}/{len(probes)} seeks passed (all required)",
            {"probes": probes},
        )

    best = min(probes, key=lambda p: abs(p["offset_x"]) + abs(p["offset_y"]))
    return StepResult(
        "pip_centring",
        True,
        f"PiP centred on {passes}/{len(probes)} seek(s) (best seek={best['seek_sec']:.2f}s)",
        {"probes": probes},
    )


def post_render_qc(
    mp4_path: str | Path,
    *,
    expected_duration_sec: Optional[float] = None,
    duration_tolerance_sec: float = 3.0,
    require_audio: bool = True,
    min_width: int = 640,
    expected_width: Optional[int] = None,
    expected_height: Optional[int] = None,
    expected_fps: Optional[float] = None,
    fps_tolerance: float = 2.0,
) -> StepResult:
    p = Path(mp4_path)
    if not p.is_file():
        return StepResult("post_render", False, f"MP4 not found: {p}")
    try:
        dur = ffprobe_duration(str(p))
        w, h = ffprobe_media_size(str(p))
        has_audio = ffprobe_has_audio(str(p))
        fps = ffprobe_video_fps(str(p))
    except Exception as e:
        return StepResult("post_render", False, str(e))

    issues: List[str] = []
    if w < min_width:
        issues.append(f"width {w} < {min_width}")
    if require_audio and not has_audio:
        issues.append("no audio stream")
    if expected_duration_sec is not None:
        if abs(dur - expected_duration_sec) > duration_tolerance_sec:
            issues.append(
                f"duration {dur:.1f}s vs expected {expected_duration_sec:.1f}s "
                f"(±{duration_tolerance_sec}s)",
            )
    if expected_width and w != expected_width:
        issues.append(f"width {w} != expected {expected_width}")
    if expected_height and h != expected_height:
        issues.append(f"height {h} != expected {expected_height}")
    if expected_fps and abs(fps - expected_fps) > fps_tolerance:
        issues.append(f"fps {fps:.2f} != expected {expected_fps} (±{fps_tolerance})")
    info = {
        "duration_sec": round(dur, 3),
        "width": w,
        "height": h,
        "fps": round(fps, 3),
        "has_audio": has_audio,
    }
    if issues:
        return StepResult("post_render", False, "; ".join(issues), info)
    return StepResult(
        "post_render",
        True,
        f"MP4 OK ({w}×{h} @ {fps:.1f}fps, {dur:.1f}s)",
        info,
    )


def _file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_slide_jpegs(
    data: dict,
    *,
    source_file: Optional[str] = None,
    golden_dir: Optional[str | Path] = None,
    min_bytes: int = 5000,
) -> StepResult:
    rel = data.get("slide_images_dir")
    if not rel:
        return StepResult("slide_jpegs", True, "slide_images_dir not set (skipped)")
    base = Path(source_file).parent if source_file else Path.cwd()
    img_dir = base / rel
    if not img_dir.is_dir():
        return StepResult("slide_jpegs", False, f"Missing directory: {img_dir}")

    jpgs = sorted(img_dir.glob("slide-*.jpg")) + sorted(img_dir.glob("slide-*.jpeg"))
    if not jpgs:
        return StepResult("slide_jpegs", False, f"No slide JPEGs in {img_dir}")

    small = [j.name for j in jpgs if j.stat().st_size < min_bytes]
    if small:
        return StepResult("slide_jpegs", False, f"Suspiciously small JPEGs: {', '.join(small)}")

    mismatches: List[str] = []
    hash_diffs: List[str] = []
    if golden_dir:
        gold = Path(golden_dir)
        for j in jpgs:
            g = gold / j.name
            if not g.is_file():
                mismatches.append(f"missing golden {j.name}")
                continue
            if g.stat().st_size != j.stat().st_size:
                mismatches.append(f"size differs {j.name}")
            if _file_md5(j) != _file_md5(g):
                hash_diffs.append(j.name)

    if mismatches or hash_diffs:
        detail_parts = mismatches + (
            [f"hash differs {n}" for n in hash_diffs] if hash_diffs else []
        )
        return StepResult(
            "slide_jpegs",
            False,
            "; ".join(detail_parts),
            {"count": len(jpgs), "golden_dir": str(golden_dir), "hash_mismatches": hash_diffs},
        )
    mode = "golden MD5 match" if golden_dir else "presence"
    return StepResult(
        "slide_jpegs",
        True,
        f"{len(jpgs)} slide JPEG(s) ({mode})",
        {"count": len(jpgs), "dir": str(img_dir)},
    )


def run_whisper_transcribe(
    audio_path: str | Path,
    output_json: str | Path,
    *,
    model: str = "base",
) -> StepResult:
    """Run openai-whisper CLI when installed."""
    audio = Path(audio_path)
    out = Path(output_json)
    if not audio.is_file():
        return StepResult("transcribe", False, f"Audio not found: {audio}")
    exe = shutil.which("whisper")
    if not exe:
        return StepResult(
            "transcribe",
            False,
            "whisper CLI not on PATH (pip install openai-whisper)",
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = out.parent
    cmd = [
        exe,
        str(audio),
        "--model",
        model,
        "--output_format",
        "json",
        "--output_dir",
        str(tmp_dir),
        "--word_timestamps",
        "True",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, check=False)
    except subprocess.TimeoutExpired:
        return StepResult("transcribe", False, "whisper timed out")
    if proc.returncode != 0:
        return StepResult("transcribe", False, (proc.stderr or proc.stdout or "whisper failed")[:500])

    produced = tmp_dir / f"{audio.stem}.json"
    if not produced.is_file():
        return StepResult("transcribe", False, f"Expected {produced}")
    if produced.resolve() != out.resolve():
        shutil.copy2(produced, out)
    return StepResult("transcribe", True, f"Wrote {out}", {"path": str(out)})


@dataclass
class PipelineOptions:
    deck_yaml: str
    content_master: Optional[str] = None
    transcript_json: Optional[str] = None
    output_pptx: Optional[str] = None
    output_mp4: Optional[str] = None
    report_path: Optional[str] = None
    template: Optional[str] = None
    sync_variants: bool = True
    check_variant_drift: bool = True
    validate_assets: bool = True
    validate_timing: bool = True
    validate_pip: bool = True
    validate_schema: bool = True
    build_pptx: bool = True
    export_mp4: bool = False
    export_slide_jpegs: bool = False
    calibrate_force: bool = False
    pip_validation_image: Optional[str] = None
    golden_slide_dir: Optional[str] = None
    post_render_qc: bool = True
    strict_post_render: bool = False
    transcribe_audio: Optional[str] = None
    seed_timing: bool = False
    variant_prefix: str = "heygen-50590"
    fail_fast: bool = True
    strict_pip: bool = False
    validate_rights: bool = True
    validate_plan: bool = True
    build_fn: Optional[BuildFn] = None
    export_fn: Optional[ExportFn] = None

    @classmethod
    def merge_pipeline_yaml(
        cls,
        opts: "PipelineOptions",
        pipe: Optional[dict],
        *,
        avatar_calibration: Optional[dict] = None,
    ) -> "PipelineOptions":
        """Apply ``pipeline`` / ``avatar_calibration`` defaults (CLI flags already set on *opts* win)."""
        pipe = pipe or {}
        ac = avatar_calibration or {}
        if pipe.get("variant_prefix") and opts.variant_prefix == "heygen-50590":
            opts.variant_prefix = str(pipe["variant_prefix"])
        if opts.golden_slide_dir is None and pipe.get("golden_slide_dir"):
            opts.golden_slide_dir = str(pipe["golden_slide_dir"])
        if "validate_plan" in pipe:
            opts.validate_plan = bool(pipe["validate_plan"])
        if "validate_rights" in pipe:
            opts.validate_rights = bool(pipe["validate_rights"])
        if "fail_fast" in pipe:
            opts.fail_fast = bool(pipe["fail_fast"])
        if "post_render_qc" in pipe:
            opts.post_render_qc = bool(pipe["post_render_qc"])
        if "strict_post_render" in pipe:
            opts.strict_post_render = bool(pipe["strict_post_render"])
        if "seed_timing" in pipe and not opts.seed_timing:
            opts.seed_timing = bool(pipe["seed_timing"])
        if "export_slide_jpegs" in pipe and not opts.export_slide_jpegs:
            opts.export_slide_jpegs = bool(pipe["export_slide_jpegs"])
        if pipe.get("export_mp4") and not opts.export_mp4:
            opts.export_mp4 = bool(pipe["export_mp4"])
        if ac.get("force"):
            opts.calibrate_force = True
        return opts


def run_pipeline(opts: PipelineOptions) -> PipelineReport:
    """Execute pipeline steps; return report (ok=False if any required step failed)."""
    deck_path = Path(opts.deck_yaml).resolve()
    report = PipelineReport(
        ok=True,
        deck_yaml=str(deck_path),
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    if opts.transcribe_audio:
        out_json = opts.transcript_json or str(deck_path.parent / "transcript.json")
        report.add(run_whisper_transcribe(opts.transcribe_audio, out_json))
        if not report.ok and opts.fail_fast:
            _write_report(report, opts)
            return report
        opts.transcript_json = out_json

    from .loader import load_deck_mapping

    try:
        data_early = load_deck_mapping(deck_path)
    except (ValueError, OSError) as e:
        report.add(StepResult("load_deck", False, str(e)))
        _write_report(report, opts)
        return report
    pipe_cfg = data_early.get("pipeline") or {}
    if opts.validate_plan:
        report.add(validate_plan_approval(pipe_cfg, base_dir=deck_path.parent))
        if not report.ok and opts.fail_fast:
            _write_report(report, opts)
            return report
    if opts.validate_rights:
        report.add(validate_rights_licensing(pipe_cfg))
        if not report.ok and opts.fail_fast:
            _write_report(report, opts)
            return report

    master = Path(opts.content_master).resolve() if opts.content_master else None
    if opts.sync_variants and master and master.is_file():
        written = sync_variants_from_master(
            master,
            master.parent,
            prefix=opts.variant_prefix,
        )
        report.add(
            StepResult(
                "sync_variants",
                True,
                f"Synced {len(written)} variant YAML(s) from {master.name}",
                {"files": [str(p) for p in written]},
            ),
        )
    elif opts.sync_variants and not master:
        report.add(StepResult("sync_variants", True, "No content_master (skipped)"))

    if opts.check_variant_drift and master and master.is_file():
        ok, issues = variants_drift(master, master.parent, prefix=opts.variant_prefix)
        report.add(
            StepResult(
                "variant_drift",
                ok,
                "Variants match master" if ok else "; ".join(issues),
                {"issues": issues},
            ),
        )
        if not ok and opts.fail_fast:
            _write_report(report, opts)
            return report

    from .loader import load_verses_from_file

    data = load_verses_from_file(str(deck_path), template=opts.template)
    if not data:
        report.add(StepResult("load_deck", False, f"Failed to load {deck_path.name}"))
        _write_report(report, opts)
        return report
    sf = data.get("_source_file") or str(deck_path)
    pipe_cfg = data.get("pipeline") or pipe_cfg
    opts = PipelineOptions.merge_pipeline_yaml(
        opts, pipe_cfg, avatar_calibration=data.get("avatar_calibration"),
    )

    if opts.seed_timing:
        tpath = opts.transcript_json or pipe_cfg.get("transcript_path")
        if tpath and Path(tpath).is_file():
            from .plan_slides import seed_timing_from_transcript

            data = seed_timing_from_transcript(data, tpath)
            report.add(StepResult("seed_timing", True, f"Updated timings from {tpath}"))
        else:
            report.add(StepResult("seed_timing", False, "No transcript for seed_timing"))

    if opts.validate_schema:
        report.add(validate_deck_schema(data))
        if not report.ok and opts.fail_fast:
            _write_report(report, opts)
            return report

    if opts.validate_assets:
        report.add(validate_deck_assets(data, source_file=sf))
        if not report.ok and opts.fail_fast:
            _write_report(report, opts)
            return report

    tpath = opts.transcript_json or pipe_cfg.get("transcript_path")
    if tpath and not Path(tpath).is_file():
        tpath = str(Path(sf).parent / tpath) if sf else tpath
    if opts.validate_timing and tpath and Path(tpath).is_file():
        report.add(check_timing_drift(data, tpath))
        if not report.ok and opts.fail_fast:
            _write_report(report, opts)
            return report

    if tpath and Path(tpath).is_file():
        report.add(check_av_sync(data, source_file=sf, transcript_path=tpath))
        if not report.ok and opts.fail_fast:
            _write_report(report, opts)
            return report

    from .avatar_calibrate import maybe_auto_calibrate_deck

    if opts.calibrate_force:
        ac = dict(data.get("avatar_calibration") or {})
        ac["force"] = True
        data["avatar_calibration"] = ac
    data = maybe_auto_calibrate_deck(data, source_file=sf)

    if opts.validate_pip:
        strict_pip = opts.strict_pip or bool(pipe_cfg.get("strict_pip"))
        step = validate_pip_centring(
            data, source_file=sf, require_all_seeks=strict_pip,
        )
        report.add(step)
        if opts.pip_validation_image is not None and step.data.get("probes"):
            from .pip_face_measure import save_pip_validation_diagram

            probes = step.data["probes"]
            best = next((p for p in probes if p.get("pass")), probes[0])
            probe = Path(best["probe"])
            out_img = opts.pip_validation_image or str(
                probe.with_name(f"{probe.stem}_pip_validation.png"),
            )
            if probe.is_file():
                from .pip_face_measure import measure_pip_image

                metrics, _ = measure_pip_image(probe)
                pip_shape = str(
                    ((data.get("slide_style") or {}).get("layouts") or {})
                    .get("pip", {})
                    .get("shape", "circle")
                )
                save_pip_validation_diagram(probe, metrics, out_img, frame_shape=pip_shape)
                report.outputs["pip_validation_image"] = out_img
        if not report.ok and opts.fail_fast:
            _write_report(report, opts)
            return report

    pptx_path = opts.output_pptx or str(deck_path.with_suffix(".pptx"))
    mp4_path = opts.output_mp4 or str(Path(pptx_path).with_suffix(".mp4"))

    if opts.build_pptx:
        build = opts.build_fn or default_build_presentation
        out = build(data, output_file=pptx_path)
        if not out:
            report.add(StepResult("build_pptx", False, "deck build failed"))
            _write_report(report, opts)
            return report
        report.add(StepResult("build_pptx", True, f"Wrote {out}"))
        report.outputs["pptx"] = out
        pptx_path = out

    if opts.build_pptx and (opts.export_slide_jpegs or data.get("slide_images_dir")):
        from .slide_images import export_pptx_slide_jpegs, resolve_slide_images_dir

        try:
            out_dir = str(resolve_slide_images_dir(data, pptx_path=pptx_path, source_file=sf))
            export_pptx_slide_jpegs(pptx_path, out_dir)
            report.add(StepResult("slide_jpegs_export", True, f"Exported to {out_dir}"))
        except Exception as e:
            report.add(StepResult("slide_jpegs_export", False, str(e)))
            if opts.fail_fast:
                _write_report(report, opts)
                return report
    golden = opts.golden_slide_dir or pipe_cfg.get("golden_slide_dir")
    if data.get("slide_images_dir"):
        report.add(check_slide_jpegs(data, source_file=sf, golden_dir=golden))
        if not report.ok and opts.fail_fast:
            _write_report(report, opts)
            return report

    if opts.export_mp4:
        from .video_exporter import VideoOptions

        export = opts.export_fn or default_export_deck_video
        try:
            vopts = VideoOptions.from_dict(data.get("video_export"), data)
            vopts.output_path = mp4_path
            result = export(data, pptx_path, video_options=vopts)
            report.add(StepResult("export_mp4", True, f"Wrote {result}"))
            report.outputs["mp4"] = result
            if opts.post_render_qc:
                vex = data.get("video_export") or {}
                require_audio = vex.get("narration_mode") not in ("fixed",)
                spec = expected_video_spec(data)
                qc = post_render_qc(
                    result,
                    expected_duration_sec=expected_deck_duration(data),
                    require_audio=require_audio,
                    expected_width=spec.get("width"),
                    expected_height=spec.get("height"),
                    expected_fps=float(spec.get("fps", 30)),
                )
                report.add(qc)
                if not qc.ok and opts.strict_post_render and opts.fail_fast:
                    _write_report(report, opts)
                    return report
        except Exception as e:
            report.add(StepResult("export_mp4", False, str(e)))
            if opts.fail_fast:
                _write_report(report, opts)
                return report

    _write_report(report, opts)
    return report


def _write_report(report: PipelineReport, opts: PipelineOptions) -> None:
    if opts.report_path:
        path = opts.report_path
    else:
        deck = Path(opts.deck_yaml)
        path = deck.parent / ".praisonaippt" / f"{deck.stem}.pipeline-report.json"
    report.write_json(path)
    report.outputs["report_json"] = str(path)
