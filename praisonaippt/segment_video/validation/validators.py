"""Pluggable validators — each returns a ValidatorReport."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

from ..image_audit import audit_project_images, hook_topic_phrase
from ..image_selection import sentence_groups
from ..manifest import load_manifest
from ..media import ffprobe_duration
from ..project import SegmentVideoProject
from ..validate_sync import validate_segment_sync
from .base import CheckResult, ValidatorReport

ValidatorFn = Callable[[SegmentVideoProject, dict], ValidatorReport]

REGISTRY: dict[str, ValidatorFn] = {}


def register(name: str) -> Callable[[ValidatorFn], ValidatorFn]:
    def deco(fn: ValidatorFn) -> ValidatorFn:
        REGISTRY[name] = fn
        return fn

    return deco


def _report(vid: str, required: bool, checks: list[CheckResult]) -> ValidatorReport:
    ok = all(c.ok for c in checks if c.severity == "error")
    return ValidatorReport(id=vid, ok=ok, required=required, checks=checks)


def _cfg(protocol: dict) -> dict:
    return protocol.get("validation_suite") or {}


@register("tools")
def validate_tools(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    cfg = _cfg(protocol)
    required = bool((cfg.get("validators") or [{}])[0])  # default true
    tools = ["ffprobe", "ffmpeg", "praisonaippt", "zsh"]
    optional = ["praisonaiwp", "whisper"]
    checks: list[CheckResult] = []
    for tool in tools:
        checks.append(CheckResult(
            id=f"tool:{tool}",
            ok=shutil.which(tool) is not None,
            severity="error",
            message=f"{tool} on PATH" if shutil.which(tool) else f"missing tool: {tool}",
        ))
    for tool in optional:
        present = shutil.which(tool) is not None
        checks.append(CheckResult(
            id=f"tool:{tool}",
            ok=True,
            severity="info" if present else "warn",
            message=f"{tool} available" if present else f"optional tool missing: {tool} (word-level hook timing)",
            details={"present": present},
        ))
    return _report("tools", True, checks)


@register("artifacts")
def validate_artifacts(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    manifest = load_manifest(project.root)
    checks: list[CheckResult] = []
    for name in ("media_assets.json", "merge/final-roundup.mp4", "merge/final-roundup.srt"):
        p = project.root / name
        checks.append(CheckResult(
            id=f"file:{name}",
            ok=p.is_file(),
            severity="error",
            message=f"present: {name}" if p.is_file() else f"missing: {name}",
        ))
    for seg in manifest.get("segments", []):
        d = seg["dir"]
        seg_dir = project.root / "segments" / d
        for fname in ("script.md", "heygen.mp4", "segment.mp4"):
            p = seg_dir / fname
            checks.append(CheckResult(
                id=f"{d}:{fname}",
                ok=p.is_file(),
                severity="error",
                message=f"{d}: {fname} ok" if p.is_file() else f"{d}: missing {fname}",
            ))
        if seg.get("slide_type") in ("avatar_media_3", "big_number"):
            ct = seg_dir / "cue_timings.json"
            if (project.root / "media_assets.json").is_file():
                assets = json.loads((project.root / "media_assets.json").read_text())
                n_cues = len((assets.get("segments", {}).get(d) or {}).get("cues") or [])
                if n_cues > 1:
                    checks.append(CheckResult(
                        id=f"{d}:cue_timings",
                        ok=ct.is_file(),
                        severity="error",
                        message=f"{d}: cue_timings.json" if ct.is_file() else f"{d}: missing cue_timings ({n_cues} cues)",
                    ))
    return _report("artifacts", True, checks)


@register("hook_montage")
def validate_hook_montage(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    hook_cfg = protocol.get("hook_montage") or {}
    if not hook_cfg.get("enabled"):
        return _report("hook_montage", True, [CheckResult(
            id="hook:disabled", ok=True, severity="info", message="hook montage disabled",
        )])

    manifest = load_manifest(project.root)
    max_cues = int(hook_cfg.get("max_cues", 15))
    topic_segs = [s for s in manifest["segments"] if s.get("slide_type") == "avatar_media_3"]
    checks: list[CheckResult] = []

    assets_path = project.root / "media_assets.json"
    hook_cues: list[dict] = []
    if assets_path.is_file():
        hook_cues = (json.loads(assets_path.read_text()).get("segments", {}).get("00-hook") or {}).get("cues") or []

    checks.append(CheckResult(
        id="hook:cue_count",
        ok=len(hook_cues) == max_cues,
        severity="error",
        message=f"hook has {len(hook_cues)}/{max_cues} montage cues",
    ))

    mismatches: list[str] = []
    for i, (cue, seg) in enumerate(zip(hook_cues, topic_segs[:max_cues])):
        exp_slug = seg.get("slug")
        got_slug = cue.get("topic_slug")
        exp_phrase = hook_topic_phrase(seg)
        got_phrase = cue.get("script_fragment") or ""
        if got_slug != exp_slug:
            mismatches.append(f"cue {i}: slug {got_slug} != {exp_slug}")
        if got_phrase.strip().lower() != exp_phrase.strip().lower():
            mismatches.append(f"cue {i}: phrase mismatch")

    checks.append(CheckResult(
        id="hook:topic_pairing",
        ok=len(mismatches) == 0,
        severity="error",
        message="15/15 topic heroes paired to speech" if not mismatches else f"pairing errors: {len(mismatches)}",
        details={"mismatches": mismatches[:10]},
    ))

    ct_path = project.root / "segments" / "00-hook" / "cue_timings.json"
    if ct_path.is_file():
        n_timings = len(json.loads(ct_path.read_text()).get("cues") or [])
        checks.append(CheckResult(
            id="hook:timings",
            ok=n_timings == len(hook_cues),
            severity="error",
            message=f"cue_timings {n_timings} vs media {len(hook_cues)}",
        ))

    heygen = project.root / "segments" / "00-hook" / "heygen.mp4"
    seg_mp4 = project.root / "segments" / "00-hook" / "segment.mp4"
    if heygen.is_file() and seg_mp4.is_file():
        hg = ffprobe_duration(heygen)
        sm = ffprobe_duration(seg_mp4)
        drift = abs(hg - sm)
        checks.append(CheckResult(
            id="hook:duration_drift",
            ok=drift <= 1.0,
            severity="error" if drift > 2.0 else "warn",
            message=f"heygen {hg:.1f}s vs segment.mp4 {sm:.1f}s (drift {drift:.1f}s)",
        ))

    return _report("hook_montage", True, checks)


@register("script_policy")
def validate_script_policy(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    policy = (_cfg(protocol).get("script_policy") or {})
    forbidden = [s.lower() for s in policy.get("forbidden_in_voice", [])]
    hook_must = [s.lower() for s in policy.get("hook_must_include", [])]
    hook_must_not = [s.lower() for s in policy.get("hook_must_not_include", [])]
    outro_must = [s.lower() for s in policy.get("outro_must_include", [])]

    checks: list[CheckResult] = []
    for seg_dir, label in (("00-hook", "hook"), ("16-outro", "outro")):
        sp = project.root / "segments" / seg_dir / "script.md"
        if not sp.is_file():
            checks.append(CheckResult(
                id=f"script:{label}:missing", ok=False, severity="error", message=f"missing {seg_dir}/script.md",
            ))
            continue
        text = sp.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            if phrase in text:
                checks.append(CheckResult(
                    id=f"script:{label}:forbidden",
                    ok=False,
                    severity="error",
                    message=f"{label} contains forbidden phrase: {phrase!r}",
                ))
        if label == "hook":
            if hook_must and not any(m in text for m in hook_must):
                checks.append(CheckResult(
                    id="script:hook:transition",
                    ok=False,
                    severity="error",
                    message="hook missing transition phrase (e.g. let's get started)",
                ))
            for phrase in hook_must_not:
                if phrase in text:
                    checks.append(CheckResult(
                        id="script:hook:legacy",
                        ok=False,
                        severity="error",
                        message=f"hook contains legacy phrase: {phrase!r}",
                    ))
        if label == "outro":
            missing = [m for m in outro_must if m not in text]
            if missing:
                checks.append(CheckResult(
                    id="script:outro:cta",
                    ok=False,
                    severity="error",
                    message=f"outro missing CTA tokens: {missing}",
                ))

    failed = [c for c in checks if not c.ok and c.severity == "error"]
    if not failed:
        checks.append(CheckResult(
            id="script:policy", ok=True, severity="info", message="hook/outro script policy satisfied",
        ))
    return _report("script_policy", True, checks)


@register("image_audit")
def validate_image_audit(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    cfg = _cfg(protocol)
    entry = next((v for v in (cfg.get("validators") or []) if v.get("id") == "image_audit"), {})
    run_fresh = entry.get("run_fresh", True)

    manifest = load_manifest(project.root)
    if run_fresh:
        report = audit_project_images(project.root, manifest, protocol)
        out = project.root / "image_audit_report.json"
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    else:
        out = project.root / "image_audit_report.json"
        report = json.loads(out.read_text()) if out.is_file() else {"ok": False, "failed_count": 99}

    failed = [s for s in report.get("segments", []) if not s.get("ok") and not s.get("skipped")]
    checks = [
        CheckResult(
            id="image_audit:gate",
            ok=bool(report.get("ok")),
            severity="error",
            message=f"image audit {report.get('summary', {}).get('passed', 0)}/{report.get('summary', {}).get('total', 0)} segments pass",
            details={"failed_dirs": [s.get("dir") for s in failed]},
        ),
    ]
    for seg in failed[:8]:
        for issue in (seg.get("issues") or [])[:3]:
            checks.append(CheckResult(
                id=f"image_audit:{seg.get('dir')}",
                ok=False,
                severity="warn",
                message=str(issue),
            ))
    return _report("image_audit", True, checks)


@register("segment_sync")
def validate_segment_sync_all(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    manifest = load_manifest(project.root)
    sync_cfg = protocol.get("sync_validation") or {}
    min_overlap = float(sync_cfg.get("min_fragment_overlap", 0.45))
    max_drift = float(sync_cfg.get("max_start_drift_sec", 0.5))
    checks: list[CheckResult] = []

    for seg in manifest.get("segments", []):
        if seg.get("slide_type") not in ("avatar_media_3", "big_number"):
            continue
        seg_dir = project.root / "segments" / seg["dir"]
        ok, issues = validate_segment_sync(seg_dir, min_overlap=min_overlap, max_drift=max_drift)
        checks.append(CheckResult(
            id=f"sync:{seg['dir']}",
            ok=ok,
            severity="warn" if seg["dir"] == "00-hook" and not ok else "error",
            message=f"{seg['dir']}: sync ok" if ok else f"{seg['dir']}: {issues[0]}",
            details={"issues": issues[:5]},
        ))
    return _report("segment_sync", True, checks)


@register("merge_output")
def validate_merge_output(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    coverage = (_cfg(protocol).get("coverage") or {})
    min_dur = float(coverage.get("min_merge_duration_sec", 300))
    max_dur = float(coverage.get("max_merge_duration_sec", 720))
    manifest = load_manifest(project.root)

    checks: list[CheckResult] = []
    mp4 = project.root / "merge" / "final-roundup.mp4"
    srt = project.root / "merge" / "final-roundup.srt"
    timeline = project.root / "merge" / "timeline.json"

    for name, path in (("final-roundup.mp4", mp4), ("final-roundup.srt", srt), ("timeline.json", timeline)):
        checks.append(CheckResult(
            id=f"merge:{name}",
            ok=path.is_file(),
            severity="error",
            message=f"merge/{name} present" if path.is_file() else f"missing merge/{name}",
        ))

    if mp4.is_file():
        dur = ffprobe_duration(mp4)
        target = float(manifest.get("target_duration_sec") or 600)
        checks.append(CheckResult(
            id="merge:duration",
            ok=min_dur <= dur <= max_dur,
            severity="warn",
            message=f"merged {dur:.1f}s (target {target}s, allowed {min_dur}-{max_dur}s)",
            details={"duration_sec": dur, "target_sec": target},
        ))

    if timeline.is_file():
        tl = json.loads(timeline.read_text())
        n_seg = len(tl.get("segments") or tl.get("entries") or [])
        exp = len(manifest.get("segments", []))
        checks.append(CheckResult(
            id="merge:timeline_segments",
            ok=n_seg >= exp - 1,
            severity="warn",
            message=f"timeline covers {n_seg} segments (manifest {exp})",
        ))

    return _report("merge_output", True, checks)


@register("coverage")
def validate_coverage(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    """Sentence ↔ cue coverage for topic segments."""
    manifest = load_manifest(project.root)
    assets_path = project.root / "media_assets.json"
    assets = json.loads(assets_path.read_text()).get("segments", {}) if assets_path.is_file() else {}
    checks: list[CheckResult] = []

    for seg in manifest.get("segments", []):
        if seg.get("slide_type") != "avatar_media_3":
            continue
        seg_dir = project.root / "segments" / seg["dir"]
        script_path = seg_dir / "script.md"
        if not script_path.is_file():
            continue
        script = script_path.read_text(encoding="utf-8").strip()
        n_sentences = len(sentence_groups(script))
        n_cues = len((assets.get(seg["dir"]) or {}).get("cues") or [])
        ratio = n_cues / max(n_sentences, 1)
        ok = n_cues >= n_sentences or ratio >= 0.5
        checks.append(CheckResult(
            id=f"coverage:{seg['dir']}",
            ok=ok,
            severity="warn",
            message=f"{seg['dir']}: {n_cues} cues / {n_sentences} sentences",
            details={"cues": n_cues, "sentences": n_sentences, "ratio": round(ratio, 2)},
        ))

    return _report("coverage", False, checks)


@register("manual_assets")
def validate_manual_assets(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    """Flag topics with known weak/manual hero images from protocol registry."""
    gaps = protocol.get("manual_asset_gaps") or []
    assets_path = project.root / "media_assets.json"
    assets = json.loads(assets_path.read_text()).get("segments", {}) if assets_path.is_file() else {}
    checks: list[CheckResult] = []

    for gap in gaps:
        slug = gap.get("topic_slug") or ""
        status = gap.get("status") or "needs_manual_art"
        approved = gap.get("approved_file")
        seg_dir = None
        for seg in load_manifest(project.root).get("segments", []):
            if seg.get("slug") == slug:
                seg_dir = seg.get("dir")
                break
        if not seg_dir:
            continue
        cues = (assets.get(seg_dir) or {}).get("cues") or []
        hero = cues[0] if cues else {}
        fn = hero.get("file") or hero.get("dest_file") or ""
        ok = bool(approved and fn == approved)
        checks.append(CheckResult(
            id=f"manual:{slug}",
            ok=ok,
            severity="warn",
            message=f"{slug}: {status}" + (f" (approved: {approved})" if approved else ""),
            details={"current_file": fn, "note": gap.get("note")},
        ))

    if not checks:
        checks.append(CheckResult(
            id="manual:none", ok=True, severity="info", message="no manual_asset_gaps in protocol",
        ))
    return _report("manual_assets", False, checks)


@register("hook_speech_sync")
def validate_hook_speech_sync(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    hook_cfg = protocol.get("hook_montage") or {}
    if not hook_cfg.get("enabled"):
        return _report("hook_speech_sync", False, [CheckResult(
            id="hook_sync:disabled", ok=True, severity="info", message="skipped",
        )])

    checks: list[CheckResult] = []
    ts_path = project.root / "segments" / "00-hook" / "timestamps.json"
    if ts_path.is_file():
        ts = json.loads(ts_path.read_text())
        has_words = bool(ts.get("words")) or any(
            s.get("words") for s in (ts.get("segments") or [])
        )
        checks.append(CheckResult(
            id="hook_sync:word_timestamps",
            ok=has_words,
            severity="warn",
            message="word-level timestamps present" if has_words else "no word timestamps (montage uses estimates)",
        ))

    ct_path = project.root / "segments" / "00-hook" / "cue_timings.json"
    forbidden = set(hook_cfg.get("forbidden_match_methods") or ["montage_split"])
    if ct_path.is_file():
        methods = {c.get("match_method") for c in json.loads(ct_path.read_text()).get("cues") or []}
        bad = methods & forbidden
        checks.append(CheckResult(
            id="hook_sync:match_method",
            ok=len(bad) == 0,
            severity="warn",
            message=f"match methods: {sorted(methods)}" + (f" (avoid {sorted(bad)})" if bad else ""),
        ))

    return _report("hook_speech_sync", False, checks)


@register("protocol_stages")
def validate_protocol_stages(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    """Dry check — every protocol stage is registered and deps resolve."""
    from ..protocol import validate_deps

    checks: list[CheckResult] = []
    stage_ids = {s.get("id") for s in protocol.get("stages", [])}
    known = {
        "scripts", "catalogue-media", "crawl-missing-assets", "sync-media", "validate-assets",
        "validate-media", "audit-images",
        "media", "align-cues", "yaml", "build", "validate-sync", "validate-visual",
        "fix-jpegs", "seed-golden", "build-timeline", "normalize-audio", "merge", "publish", "validate-all", "validate-hook", "validate-display",
    }
    for st in protocol.get("stages", []):
        sid = st.get("id")
        for dep in st.get("depends_on", []):
            errs = validate_deps(protocol, sid or "")
            if errs:
                checks.append(CheckResult(id=f"stage:{sid}:deps", ok=False, severity="error", message=errs[0]))
        if sid and sid not in known:
            checks.append(CheckResult(
                id=f"stage:{sid}:unknown", ok=False, severity="warn", message=f"stage {sid} not in SDK runner",
            ))

    checks.append(CheckResult(
        id="protocol:schema",
        ok=int(protocol.get("schema_version", 0)) >= 3,
        severity="info",
        message=f"protocol schema_version {protocol.get('schema_version')}",
    ))
    checks.append(CheckResult(
        id="protocol:stage_count",
        ok=len(stage_ids) >= 15,
        severity="info",
        message=f"{len(stage_ids)} pipeline stages defined",
        details={"stages": sorted(stage_ids)},
    ))
    return _report("protocol_stages", False, checks)


@register("required_assets")
def validate_required_assets(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    from .required_assets import audit_required_assets

    cfg = _cfg(protocol).get("required_assets") or {}
    fetch = bool(cfg.get("fetch_canonical", True))
    report = audit_required_assets(project.root, protocol, fetch_canonical=fetch)
    (project.root / "asset_gaps_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8",
    )

    checks: list[CheckResult] = []
    summ = report.get("summary") or {}
    checks.append(CheckResult(
        id="assets:catalogue",
        ok=bool(report.get("ok")),
        severity="error",
        message=f"required assets {summ.get('total', 0) - summ.get('failed', 0)}/{summ.get('total', 0)} topics ok",
        details={
            "failed_dirs": [t["dir"] for t in (report.get("topics") or []) if not t.get("ok")],
            "needs_crawl": summ.get("needs_crawl", 0),
        },
    ))
    for row in report.get("topics") or []:
        if row.get("ok"):
            continue
        for gap in row.get("gaps") or []:
            if gap.get("type") == "manual_exempt":
                continue
            checks.append(CheckResult(
                id=f"assets:{row['dir']}:{gap['type']}",
                ok=False,
                severity="warn" if gap["type"] == "handoff_uncrawled" else "error",
                message=f"{row['dir']}: {gap['detail']}",
            ))
    return _report("required_assets", True, checks)


@register("display_sync")
def validate_display_sync(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    """Deep audit: catalogue completeness, caption↔slide, speech↔image."""
    from .display_sync import validate_project_display

    cfg = _cfg(protocol).get("display_sync") or {}
    fetch = bool(cfg.get("fetch_canonical", True))
    report = validate_project_display(project.root, protocol, fetch_canonical=fetch)
    (project.root / "display_validation_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8",
    )

    checks: list[CheckResult] = []
    cat = report.get("catalogue") or {}
    checks.append(CheckResult(
        id="display:catalogue",
        ok=bool(cat.get("ok")),
        severity="error",
        message=f"handoff catalogue {cat.get('summary', {}).get('total', 0) - cat.get('summary', {}).get('failed', 0)}/{cat.get('summary', {}).get('total', 0)} topics ok",
        details={"failed_dirs": [t["dir"] for t in (cat.get("topics") or []) if not t.get("ok")]},
    ))

    for seg in report.get("segments") or []:
        d = seg.get("dir") or ""
        cap_ok = (seg.get("caption_slides") or {}).get("ok", True)
        speech_ok = (seg.get("speech_overlap") or {}).get("ok", True)
        checks.append(CheckResult(
            id=f"display:caption:{d}",
            ok=cap_ok,
            severity="error",
            message=f"{d}: caption↔slide {'ok' if cap_ok else 'FAIL'}",
            details={"issues": (seg.get("caption_slides") or {}).get("issues", [])[:5]},
        ))
        if not (seg.get("speech_overlap") or {}).get("skipped"):
            checks.append(CheckResult(
                id=f"display:speech:{d}",
                ok=speech_ok,
                severity="warn" if d == "00-hook" else "error",
                message=f"{d}: speech↔image {'ok' if speech_ok else 'FAIL'}",
                details={"issues": (seg.get("speech_overlap") or {}).get("issues", [])[:5]},
            ))

    return _report("display_sync", True, checks)


@register("audio_loudness")
def validate_audio_loudness(project: SegmentVideoProject, protocol: dict) -> ValidatorReport:
    """Cross-segment loudness consistency on segment.mp4 (post-normalize)."""
    from ..audio_loudness import (
        audit_segments,
        loudness_config,
        measure_loudness,
        validate_loudness_audit,
    )

    cfg = loudness_config(protocol)
    manifest = load_manifest(project.root)
    audit = audit_segments(project.root, manifest)
    ok, issues = validate_loudness_audit(audit, cfg)

    checks: list[CheckResult] = []
    summary = audit.get("summary") or {}
    checks.append(CheckResult(
        id="loudness:spread",
        ok=summary.get("spread_lufs", 999) <= float(cfg.get("max_spread_lufs", 2.0)) if summary.get("spread_lufs") is not None else False,
        severity="error",
        message=(
            f"spread {summary.get('spread_lufs')} LUFS (max {cfg.get('max_spread_lufs')})"
            if summary.get("spread_lufs") is not None
            else "no loudness measurements"
        ),
        details=summary,
    ))

    tgt = float(cfg["target_lufs"])
    tol = float(cfg.get("tolerance_lufs", 1.0))
    for row in audit.get("segments") or []:
        d = row.get("dir") or ""
        m = row.get("metrics") or {}
        lufs = m.get("integrated_lufs")
        if lufs is None:
            checks.append(CheckResult(
                id=f"loudness:{d}",
                ok=False,
                severity="error",
                message=f"{d}: no LUFS measurement",
            ))
            continue
        seg_ok = abs(lufs - tgt) <= tol
        checks.append(CheckResult(
            id=f"loudness:{d}",
            ok=seg_ok,
            severity="error",
            message=f"{d}: {lufs:.1f} LUFS (target {tgt})",
            details=m,
        ))

    final_mp4 = project.root / "merge" / "final-roundup.mp4"
    if final_mp4.is_file():
        try:
            fm = measure_loudness(final_mp4)
            checks.append(CheckResult(
                id="loudness:final-roundup",
                ok=True,
                severity="info",
                message=f"final: {fm.integrated_lufs:.1f} LUFS" if fm.integrated_lufs else "final: measured",
                details=fm.as_dict(),
            ))
        except (OSError, RuntimeError):
            pass

    if issues:
        checks.append(CheckResult(
            id="loudness:issues",
            ok=ok,
            severity="error",
            message=f"{'ok' if ok else 'FAIL'}: {len(issues)} issue(s)",
            details={"issues": issues[:10]},
        ))

    return _report("audio_loudness", True, checks)
