"""normalize-audio stage — EBU R128 loudnorm per segment.mp4 before merge."""
from __future__ import annotations

import json
from typing import Callable

from ..audio_loudness import (
    audit_segments,
    loudness_config,
    measure_loudness,
    normalize_file,
    write_loudness_report,
)
from ..manifest import load_manifest
from ..project import SegmentVideoProject


def run_normalize_audio(
    project: SegmentVideoProject,
    *,
    segments: list[str] | None = None,
    force: bool = False,
    log: Callable[[str], None] | None = None,
) -> int:
    emit = log or print
    protocol = project.load_protocol()
    cfg = loudness_config(protocol)
    manifest = load_manifest(project.root)
    target_lufs = float(cfg["target_lufs"])
    skip_within = float(cfg.get("skip_if_within_lufs", 0.5))

    emit("normalize-audio: measuring segment loudness…")
    before_audit = audit_segments(project.root, manifest, segments=segments)

    results: list[dict] = []
    normalized = 0
    skipped = 0

    for row in before_audit.get("segments") or []:
        d = row["dir"]
        if not row.get("ok"):
            emit(f"  skip {d}: {row.get('error', 'missing')}")
            results.append({"dir": d, "action": "skip", "reason": row.get("error")})
            continue

        mp4 = project.root / "segments" / d / "segment.mp4"
        before_lufs = (row.get("metrics") or {}).get("integrated_lufs")
        if (
            not force
            and before_lufs is not None
            and abs(before_lufs - target_lufs) <= skip_within
        ):
            emit(f"  skip {d}: {before_lufs:.1f} LUFS (within ±{skip_within} of {target_lufs})")
            skipped += 1
            results.append({
                "dir": d,
                "action": "skip",
                "before": row.get("metrics"),
                "after": row.get("metrics"),
            })
            continue

        emit(f"  normalize {d}…")
        try:
            before_m, after_m = normalize_file(mp4, cfg)
            normalized += 1
            results.append({
                "dir": d,
                "action": "normalized",
                "before": before_m.as_dict(),
                "after": after_m.as_dict(),
            })
            after_lufs = after_m.integrated_lufs
            emit(f"    {before_m.integrated_lufs:.1f} → {after_lufs:.1f} LUFS" if before_m.integrated_lufs and after_lufs else f"    normalized {d}")
        except (OSError, RuntimeError) as exc:
            emit(f"  FAIL {d}: {exc}")
            results.append({"dir": d, "action": "error", "error": str(exc)})

    after_audit = audit_segments(project.root, manifest, segments=segments)
    report = {
        "schema_version": 1,
        "target": cfg,
        "before": before_audit,
        "after": after_audit,
        "actions": results,
        "summary": {
            "normalized": normalized,
            "skipped": skipped,
            "errors": sum(1 for r in results if r.get("action") == "error"),
        },
    }
    out = project.root / "loudness_report.json"
    write_loudness_report(out, report)
    emit(f"normalize-audio → {out} ({normalized} normalized, {skipped} skipped)")

    if any(r.get("action") == "error" for r in results):
        return 1
    return 0
