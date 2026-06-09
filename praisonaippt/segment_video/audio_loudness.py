"""Measure and normalise segment audio loudness (EBU R128 via ffmpeg loudnorm)."""
from __future__ import annotations

import json
import re
import statistics
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_TARGET = {
    "target_lufs": -16.0,
    "true_peak_db": -1.5,
    "lra": 11.0,
    "max_spread_lufs": 2.0,
    "tolerance_lufs": 1.0,
    "skip_if_within_lufs": 0.5,
}


@dataclass
class LoudnessMetrics:
    integrated_lufs: float | None = None
    true_peak_dbtp: float | None = None
    lra: float | None = None
    threshold_lufs: float | None = None
    offset: float | None = None
    mean_volume_db: float | None = None
    max_volume_db: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def loudness_config(protocol: dict) -> dict[str, float]:
    cfg = dict(DEFAULT_TARGET)
    cfg.update(protocol.get("audio_loudness") or {})
    return cfg


def _run_ffmpeg(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", *args],
        capture_output=True,
        text=True,
    )


def parse_loudnorm_summary(stderr: str) -> LoudnessMetrics:
    """Parse loudnorm print_format=summary lines from ffmpeg stderr."""
    m = LoudnessMetrics()

    def _float(pattern: str) -> float | None:
        hit = re.search(pattern, stderr, re.I)
        if not hit:
            return None
        try:
            return float(hit.group(1))
        except ValueError:
            return None

    m.integrated_lufs = _float(r"Input Integrated:\s*([-\d.]+)")
    m.true_peak_dbtp = _float(r"Input True Peak:\s*([-\d.]+)")
    m.lra = _float(r"Input LRA:\s*([-\d.]+)")
    m.threshold_lufs = _float(r"Input Threshold:\s*([-\d.]+)")
    m.offset = _float(r"Target Offset:\s*([+\-]?\d+(?:\.\d+)?)")
    if m.integrated_lufs is None:
        m.integrated_lufs = _float(r"Output Integrated:\s*([-\d.]+)")
    if m.true_peak_dbtp is None:
        m.true_peak_dbtp = _float(r"Output True Peak:\s*([-\d.]+)")
    return m


def parse_volumedetect(stderr: str) -> LoudnessMetrics:
    m = LoudnessMetrics()
    mean = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", stderr)
    peak = re.search(r"max_volume:\s*([-\d.]+)\s*dB", stderr)
    if mean:
        m.mean_volume_db = float(mean.group(1))
    if peak:
        m.max_volume_db = float(peak.group(1))
    return m


def measure_loudness(path: Path) -> LoudnessMetrics:
    """Measure integrated LUFS and true peak via loudnorm summary pass."""
    if not path.is_file():
        raise FileNotFoundError(path)
    proc = _run_ffmpeg([
        "-i", str(path),
        "-vn",
        "-af", "loudnorm=print_format=summary",
        "-f", "null", "-",
    ])
    text = (proc.stderr or "") + (proc.stdout or "")
    metrics = parse_loudnorm_summary(text)
    if metrics.integrated_lufs is None:
        vd = _run_ffmpeg(["-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-"])
        vol = parse_volumedetect((vd.stderr or "") + (vd.stdout or ""))
        metrics.mean_volume_db = vol.mean_volume_db
        metrics.max_volume_db = vol.max_volume_db
    return metrics


def measure_volumedetect(path: Path) -> LoudnessMetrics:
    if not path.is_file():
        raise FileNotFoundError(path)
    proc = _run_ffmpeg(["-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-"])
    return parse_volumedetect((proc.stderr or "") + (proc.stdout or ""))


def _loudnorm_filter(measured: LoudnessMetrics, target: dict[str, float], *, linear: bool) -> str:
    i = target["target_lufs"]
    tp = target["true_peak_db"]
    lra = target["lra"]
    parts = [f"I={i}", f"TP={tp}", f"LRA={lra}", "print_format=summary"]
    if linear and measured.integrated_lufs is not None:
        parts.extend([
            f"measured_I={measured.integrated_lufs}",
            f"measured_TP={measured.true_peak_dbtp or tp}",
            f"measured_LRA={measured.lra or lra}",
            f"measured_thresh={measured.threshold_lufs or -70}",
            f"offset={measured.offset or 0}",
            "linear=true",
        ])
    return f"loudnorm={':'.join(parts)}"


def normalize_file(
    path: Path,
    target: dict[str, float],
    *,
    dry_run: bool = False,
) -> tuple[LoudnessMetrics, LoudnessMetrics]:
    """Two-pass EBU R128 normalisation; video stream copied, audio re-encoded AAC."""
    before = measure_loudness(path)
    if dry_run:
        return before, before

    filt = _loudnorm_filter(before, target, linear=True)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        proc = _run_ffmpeg([
            "-i", str(path),
            "-af", filt,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-y", str(tmp_path),
        ])
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg loudnorm failed: {(proc.stderr or '')[-500:]}")
        after = measure_loudness(tmp_path)
        tmp_path.replace(path)
        return before, after
    except Exception:
        if tmp_path.is_file():
            tmp_path.unlink(missing_ok=True)
        raise


def audit_segments(
    project_root: Path,
    manifest: dict,
    *,
    segments: list[str] | None = None,
) -> dict[str, Any]:
    """Measure loudness for each segment.mp4; return summary stats."""
    rows: list[dict[str, Any]] = []
    for seg in manifest.get("segments") or []:
        d = seg["dir"]
        if segments and d not in segments:
            continue
        mp4 = project_root / "segments" / d / "segment.mp4"
        if not mp4.is_file():
            rows.append({"dir": d, "ok": False, "error": "missing segment.mp4"})
            continue
        try:
            m = measure_loudness(mp4)
            rows.append({
                "dir": d,
                "ok": m.integrated_lufs is not None,
                "path": str(mp4.relative_to(project_root)),
                "metrics": m.as_dict(),
            })
        except (OSError, RuntimeError) as exc:
            rows.append({"dir": d, "ok": False, "error": str(exc)})

    lufs_vals = [
        r["metrics"]["integrated_lufs"]
        for r in rows
        if r.get("ok") and r.get("metrics", {}).get("integrated_lufs") is not None
    ]
    summary: dict[str, Any] = {
        "count": len(rows),
        "measured": len(lufs_vals),
    }
    if lufs_vals:
        summary["median_lufs"] = round(statistics.median(lufs_vals), 2)
        summary["min_lufs"] = round(min(lufs_vals), 2)
        summary["max_lufs"] = round(max(lufs_vals), 2)
        summary["spread_lufs"] = round(max(lufs_vals) - min(lufs_vals), 2)

    return {"schema_version": 1, "segments": rows, "summary": summary}


def validate_loudness_audit(
    audit: dict[str, Any],
    target: dict[str, float],
) -> tuple[bool, list[str]]:
    """Return (ok, issues) for segment loudness spread and target tolerance."""
    issues: list[str] = []
    tgt = float(target["target_lufs"])
    tol = float(target.get("tolerance_lufs", 1.0))
    max_spread = float(target.get("max_spread_lufs", 2.0))
    warn_peak = float(target.get("warn_true_peak_dbtp", -1.0))

    for row in audit.get("segments") or []:
        if not row.get("ok"):
            issues.append(f"{row['dir']}: {row.get('error', 'measure failed')}")
            continue
        m = row.get("metrics") or {}
        lufs = m.get("integrated_lufs")
        if lufs is None:
            issues.append(f"{row['dir']}: no integrated LUFS")
            continue
        if abs(lufs - tgt) > tol:
            issues.append(f"{row['dir']}: {lufs:.1f} LUFS (target {tgt}, tol ±{tol})")
        peak = m.get("true_peak_dbtp")
        if peak is not None and peak > warn_peak:
            issues.append(f"{row['dir']}: true peak {peak:.1f} dBTP > {warn_peak} (warn)")

    spread = (audit.get("summary") or {}).get("spread_lufs")
    if spread is not None and spread > max_spread:
        issues.append(f"spread {spread:.1f} LUFS > max {max_spread}")

    errors = [i for i in issues if not i.endswith("(warn)")]
    return len(errors) == 0, issues


def write_loudness_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
