"""Convert deck Word exports to PDF (LibreOffice or Google Drive)."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"


def convert_docx_to_pdf_via_gdrive(docx_path: str, pdf_path: str) -> str:
    """Upload DOCX as a native Google Doc, export PDF, delete the temp Doc."""
    import io

    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

    from ..gdrive_uploader import GDriveUploader

    uploader = GDriveUploader()
    service = uploader._get_service()

    metadata = {"name": "_docx_to_pdf_tmp", "mimeType": GOOGLE_DOC_MIME}
    media = MediaFileUpload(docx_path, mimetype=DOCX_MIME)
    doc_file = service.files().create(body=metadata, media_body=media, fields="id").execute()
    doc_id = doc_file["id"]

    try:
        request = service.files().export_media(fileId=doc_id, mimeType="application/pdf")
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)
        with open(pdf_path, "wb") as f:
            f.write(fh.getvalue())
    finally:
        try:
            service.files().delete(fileId=doc_id).execute()
        except Exception:
            pass

    return pdf_path


def _resolve_soffice() -> Optional[str]:
    """Return a LibreOffice ``soffice`` binary that responds to ``--version``."""
    import glob
    import platform
    import shutil

    candidates: list[str] = []
    system = platform.system().lower()
    if system == "darwin":
        candidates.extend(
            [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                "/Applications/LibreOffice.app/Contents/MacOS/libreoffice",
            ]
        )
        candidates.extend(
            glob.glob("/opt/homebrew/Caskroom/libreoffice/*/LibreOffice.app/Contents/MacOS/soffice")
        )
    elif system == "windows":
        candidates.extend(
            [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
        )
    else:
        candidates.extend(
            [
                "/usr/bin/soffice",
                "/usr/bin/libreoffice",
                "/opt/libreoffice/program/soffice",
            ]
        )

    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            candidates.append(found)

    seen: set[str] = set()
    for path in candidates:
        if not path or path in seen:
            continue
        seen.add(path)
        if not os.path.isfile(path):
            continue
        try:
            proc = subprocess.run(
                [path, "--version"],
                capture_output=True,
                timeout=8,
            )
            if proc.returncode == 0:
                return path
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None


def convert_docx_to_pdf_local(docx_path: str, pdf_path: str) -> str:
    """Headless LibreOffice Writer export (isolated profile per run)."""
    soffice = _resolve_soffice()
    if not soffice:
        raise RuntimeError("LibreOffice is not installed or the soffice wrapper is broken")

    docx_path = os.path.abspath(docx_path)
    pdf_path = os.path.abspath(pdf_path)
    output_dir = os.path.dirname(pdf_path) or "."
    os.makedirs(output_dir, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="lo-profile-") as profile_dir:
        profile_uri = Path(profile_dir).as_uri()
        cmd = [
            soffice,
            f"-env:UserInstallation={profile_uri}",
            "--headless",
            "--norestore",
            "--convert-to",
            "pdf:writer_pdf_Export",
            "--outdir",
            output_dir,
            docx_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(
                f"LibreOffice DOCX→PDF failed: {result.stderr or result.stdout}"
            )

    expected = os.path.join(output_dir, Path(docx_path).stem + ".pdf")
    if not os.path.isfile(expected):
        raise RuntimeError("LibreOffice did not produce a PDF file")

    if expected != pdf_path:
        os.replace(expected, pdf_path)
    return pdf_path


def convert_docx_to_pdf_with_fallback(docx_path: str, pdf_path: Optional[str] = None) -> str:
    """Prefer local LibreOffice; fall back to Google Drive export."""
    if pdf_path is None:
        pdf_path = str(Path(docx_path).with_suffix(".pdf"))
    try:
        return convert_docx_to_pdf_local(docx_path, pdf_path)
    except Exception as primary_err:
        logger.warning(
            "Local DOCX→PDF failed (%s); trying Google Drive export",
            primary_err,
        )
        try:
            return convert_docx_to_pdf_via_gdrive(docx_path, pdf_path)
        except Exception as gdrive_err:
            raise RuntimeError(
                f"DOCX→PDF failed (local: {primary_err}; gdrive: {gdrive_err})"
            ) from gdrive_err
