"""Local HTTP studio server wrapping PipelineEngine."""
from __future__ import annotations

import json
import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from ..engine import PipelineEngine
from ..manifest import load_manifest
from ..project import SegmentVideoProject
from ..state import get_job
from ..timeline import build_segment_timeline, resolve_at_time
from ..validate_sync import validate_segment_sync

STATIC_DIR = Path(__file__).resolve().parent / "static"
LOCALHOST_ONLY = "127.0.0.1"


class StudioHandler(BaseHTTPRequestHandler):
    project: SegmentVideoProject
    engine: PipelineEngine

    def log_message(self, fmt: str, *args) -> None:
        pass

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._serve_static("index.html")
        if path.startswith("/static/"):
            return self._serve_static(path.split("/static/", 1)[1])
        if path == "/api/project":
            return self._api_project()
        if path == "/api/segments":
            return self._api_segments()
        m = re.match(r"^/api/segments/([^/]+)/timeline$", path)
        if m:
            return self._api_segment_timeline(unquote(m.group(1)))
        m = re.match(r"^/api/segments/([^/]+)/at$", path)
        if m:
            return self._api_segment_at(unquote(m.group(1)), urlparse(self.path).query)
        m = re.match(r"^/api/segments/([^/]+)/sync-check$", path)
        if m:
            return self._api_sync_check(unquote(m.group(1)))
        m = re.match(r"^/api/segments/([^/]+)$", path)
        if m:
            return self._api_segment_detail(unquote(m.group(1)))
        if path == "/api/project/timeline":
            return self._api_project_timeline()
        m = re.match(r"^/api/project/at$", path)
        if m:
            return self._api_project_at(urlparse(self.path).query)
        m = re.match(r"^/api/jobs/([^/]+)$", path)
        if m:
            job = get_job(self.project.state_dir, m.group(1))
            return self._json(200 if job else 404, job or {"error": "not found"})
        if path.startswith("/assets/"):
            return self._serve_asset(path[len("/assets/"):])
        self._json(404, {"error": "not found"})

    def do_PATCH(self) -> None:
        m = re.match(r"^/api/segments/([^/]+)/script$", urlparse(self.path).path)
        if not m:
            return self._json(404, {"error": "not found"})
        seg_dir = unquote(m.group(1))
        data = self._read_json()
        text = data.get("text", "")
        script = self.project.root / "segments" / seg_dir / "script.md"
        if not script.parent.is_dir():
            return self._json(404, {"error": "segment not found"})
        script.write_text(text.strip() + "\n", encoding="utf-8")
        self._json(200, {"ok": True, "dir": seg_dir})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/run":
            return self._api_run()
        if path == "/api/regenerate":
            return self._api_regenerate()
        if path == "/api/protocol/merge-transitions":
            return self._api_merge_transitions()
        self._json(404, {"error": "not found"})

    def _api_project(self) -> None:
        manifest = load_manifest(self.project.root)
        protocol = self.project.load_protocol()
        status = self.engine.status()
        self._json(200, {
            "manifest": manifest,
            "protocol": protocol,
            "status": status,
            "merge_transitions": protocol.get("merge_transitions"),
        })

    def _api_segments(self) -> None:
        manifest = load_manifest(self.project.root)
        out = []
        for seg in manifest.get("segments", []):
            d = seg["dir"]
            base = self.project.root / "segments" / d
            thumb = base / "slide_jpegs" / "slide-001.jpg"
            st = self.project.segment_status(d)
            script = ""
            sp = base / "script.md"
            if sp.is_file():
                script = sp.read_text(encoding="utf-8")
            out.append({
                **st,
                "title": seg.get("title") or seg.get("headline") or d,
                "thumbnail": f"/assets/segments/{d}/slide_jpegs/slide-001.jpg" if thumb.is_file() else None,
                "preview": f"/assets/segments/{d}/segment.mp4" if st["checks"]["mp4"] else None,
                "script": script,
            })
        self._json(200, {"segments": out})

    def _api_segment_detail(self, seg_dir: str) -> None:
        base = self.project.root / "segments" / seg_dir
        if not base.is_dir():
            return self._json(404, {"error": "not found"})
        script = (base / "script.md").read_text(encoding="utf-8") if (base / "script.md").is_file() else ""
        self._json(200, {
            "dir": seg_dir,
            "script": script,
            "status": self.project.segment_status(seg_dir),
        })

    def _api_run(self) -> None:
        data = self._read_json()
        job = self.engine.run_job_async(
            data.get("stage", ""),
            segments=data.get("segments"),
            force=bool(data.get("force")),
            no_transitions=bool(data.get("no_transitions")),
        )
        self._json(202, job)

    def _api_regenerate(self) -> None:
        data = self._read_json()
        try:
            job = self.engine.regenerate_from_async(
                data.get("change", ""),
                data.get("segment"),
                force=bool(data.get("force", True)),
                no_transitions=bool(data.get("no_transitions")),
            )
        except ValueError as exc:
            return self._json(400, {"error": str(exc)})
        self._json(202, job)

    def _load_timeline(self, seg_dir: str) -> dict | None:
        base = self.project.root / "segments" / seg_dir
        tl = base / "timeline.json"
        if not tl.is_file() and (base / "segment.yaml").is_file():
            return build_segment_timeline(base, self.project.root)
        if tl.is_file():
            return json.loads(tl.read_text(encoding="utf-8"))
        return None

    def _api_segment_timeline(self, seg_dir: str) -> None:
        tl = self._load_timeline(seg_dir)
        if not tl:
            return self._json(404, {"error": "timeline not found"})
        for c in tl.get("cues") or []:
            if c.get("jpeg_rel"):
                c["jpeg_url"] = f"/assets/{c['jpeg_rel']}"
            for tag, rel in (c.get("frames") or {}).items():
                c.setdefault("frame_urls", {})[tag] = f"/assets/{rel}"
        self._json(200, tl)

    def _api_segment_at(self, seg_dir: str, query: str) -> None:
        tl = self._load_timeline(seg_dir)
        if not tl:
            return self._json(404, {"error": "timeline not found"})
        params = parse_qs(query)
        t = float((params.get("t") or ["0"])[0])
        for c in tl.get("cues") or []:
            if c.get("jpeg_rel"):
                c["jpeg_url"] = f"/assets/{c['jpeg_rel']}"
            for tag, rel in (c.get("frames") or {}).items():
                c.setdefault("frame_urls", {})[tag] = f"/assets/{rel}"
        out = resolve_at_time(tl, t)
        slide = out.get("slide") or {}
        if slide.get("jpeg_rel"):
            slide["jpeg_url"] = f"/assets/{slide['jpeg_rel']}"
        for tag, rel in (slide.get("frames") or {}).items():
            slide.setdefault("frame_urls", {})[tag] = f"/assets/{rel}"
        self._json(200, out)

    def _api_sync_check(self, seg_dir: str) -> None:
        base = self.project.root / "segments" / seg_dir
        protocol = self.project.load_protocol()
        sv = protocol.get("sync_validation") or {}
        ok, issues = validate_segment_sync(
            base,
            min_overlap=float(sv.get("min_fragment_overlap", 0.45)),
            max_drift=float(sv.get("max_start_drift_sec", 0.5)),
        )
        self._json(200, {"ok": ok, "issues": issues})

    def _api_project_timeline(self) -> None:
        path = self.project.root / "merge" / "timeline.json"
        if path.is_file():
            return self._json(200, json.loads(path.read_text(encoding="utf-8")))
        manifest = load_manifest(self.project.root)
        from ..timeline import build_project_timeline
        return self._json(200, build_project_timeline(self.project.root, manifest, self.project.load_protocol()))

    def _api_project_at(self, query: str) -> None:
        params = parse_qs(query)
        t = float((params.get("t") or ["0"])[0])
        tl_path = self.project.root / "merge" / "timeline.json"
        if not tl_path.is_file():
            manifest = load_manifest(self.project.root)
            from ..timeline import build_project_timeline
            proj_tl = build_project_timeline(self.project.root, manifest, self.project.load_protocol())
        else:
            proj_tl = json.loads(tl_path.read_text(encoding="utf-8"))
        hit = None
        for seg in proj_tl.get("segments") or []:
            start = float(seg.get("global_start_sec") or 0)
            end = start + float(seg.get("duration_sec") or 0)
            if start <= t < end:
                hit = seg
                local_t = t - start
                break
        if not hit:
            return self._json(404, {"error": "no segment at time"})
        seg_tl = self._load_timeline(hit["dir"])
        if not seg_tl:
            return self._json(404, {"error": "segment timeline missing"})
        out = resolve_at_time(seg_tl, local_t)
        out["global_t"] = t
        out["segment_dir"] = hit["dir"]
        out["local_t"] = local_t
        slide = out.get("slide") or {}
        if slide.get("jpeg_rel"):
            slide["jpeg_url"] = f"/assets/{slide['jpeg_rel']}"
        for tag, rel in (slide.get("frames") or {}).items():
            slide.setdefault("frame_urls", {})[tag] = f"/assets/{rel}"
        self._json(200, out)

    def _api_merge_transitions(self) -> None:
        data = self._read_json()
        protocol = self.project.load_protocol()
        protocol["merge_transitions"] = {
            "default": data.get("default", "crossfade"),
            "duration_sec": float(data.get("duration_sec", 0.30)),
        }
        self.project.save_protocol(protocol)
        self._json(200, {"merge_transitions": protocol["merge_transitions"]})

    def _serve_static(self, name: str) -> None:
        fp = (STATIC_DIR / name).resolve()
        if not str(fp).startswith(str(STATIC_DIR.resolve())) or not fp.is_file():
            return self._json(404, {"error": "static not found"})
        body = fp.read_bytes()
        ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_asset(self, rel: str) -> None:
        rel = unquote(rel)
        fp = (self.project.root / rel).resolve()
        root = self.project.root.resolve()
        if not str(fp).startswith(str(root)) or not fp.is_file():
            return self._json(404, {"error": "asset not found"})
        body = fp.read_bytes()
        ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_studio(project: SegmentVideoProject, *, host: str = LOCALHOST_ONLY, port: int = 8765) -> None:
    if host != LOCALHOST_ONLY:
        raise ValueError(f"Studio must bind to {LOCALHOST_ONLY} only (got {host})")
    handler = type(
        "BoundStudioHandler",
        (StudioHandler,),
        {
            "project": project,
            "engine": PipelineEngine(project),
        },
    )
    server = ThreadingHTTPServer((host, port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
