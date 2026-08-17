"""File helpers used by Zalo Bot service actions."""
from __future__ import annotations

import json
import logging
import mimetypes
import os
import shutil
import socket
import subprocess
import threading
import time
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

PUBLIC_DIR: str | None = None
_PUBLIC_CACHE_MAX_AGE = 6 * 60 * 60
_PUBLIC_CACHE_MAX_FILES = 500



def is_local_zalo_server(zalo_server: str) -> bool:
    """Return True only for loopback Zalo Server hosts (not substring matches)."""
    try:
        host = (urllib.parse.urlsplit(str(zalo_server)).hostname or "").lower()
    except ValueError:
        return False
    return host in {"localhost", "127.0.0.1", "::1"}


def _get_local_ip() -> str:
    """Best-effort LAN address without sending application data externally."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except (socket.error, OSError):
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.error:
            return "127.0.0.1"


def serve_files_temporarily(file_paths: list[str], duration: int = 60) -> list[str]:
    """Serve multiple local files from one temporary HTTP server.

    This is substantially cheaper than opening one port/server/thread pair per image
    when a multi-image Home Assistant action is used.
    """
    valid_paths = [os.path.abspath(path) for path in file_paths if os.path.isfile(path)]
    if not valid_paths:
        return []

    mapping: dict[str, str] = {}
    url_names: list[str] = []
    for file_path in valid_paths:
        ext = Path(file_path).suffix
        public_name = f"{uuid.uuid4().hex}{ext}"
        encoded = urllib.parse.quote(public_name)
        mapping[f"/{encoded}"] = file_path
        url_names.append(encoded)

    class MultiFileHandler(BaseHTTPRequestHandler):
        def _send_file_headers(self, file_path: str) -> None:
            content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(os.path.getsize(file_path)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

        def do_GET(self):  # noqa: N802
            file_path = mapping.get(self.path)
            if not file_path:
                self.send_error(404, "File Not Found")
                return
            try:
                self._send_file_headers(file_path)
                with open(file_path, "rb") as file_handle:
                    shutil.copyfileobj(file_handle, self.wfile, length=64 * 1024)
            except (BrokenPipeError, ConnectionResetError):
                _LOGGER.debug("Client disconnected while downloading %s", file_path)
            except OSError as err:
                _LOGGER.warning("Không thể phục vụ file %s: %s", file_path, err)

        def do_HEAD(self):  # noqa: N802
            file_path = mapping.get(self.path)
            if not file_path:
                self.send_error(404, "File Not Found")
                return
            try:
                self._send_file_headers(file_path)
            except OSError:
                self.send_error(404, "File Not Found")

        def log_message(self, _format, *_args):
            return

    # Bind directly to port 0 so the OS selects an available port atomically.
    # This avoids the race between "find a free port" and opening the server.
    httpd = ThreadingHTTPServer(("0.0.0.0", 0), MultiFileHandler)
    httpd.daemon_threads = True
    port = int(httpd.server_address[1])
    local_ip = _get_local_ip()
    urls = [f"http://{local_ip}:{port}/{name}" for name in url_names]

    server_thread = threading.Thread(
        target=httpd.serve_forever,
        name=f"zalo-file-server-{port}",
        daemon=True,
    )
    server_thread.start()

    def close_server() -> None:
        time.sleep(duration)
        httpd.shutdown()
        httpd.server_close()
        _LOGGER.debug("Temporary Zalo file server on port %s stopped", port)

    threading.Thread(
        target=close_server,
        name=f"zalo-file-cleanup-{port}",
        daemon=True,
    ).start()

    _LOGGER.debug("Serving %d Zalo file(s) on port %d for %ds", len(urls), port, duration)
    return urls


def serve_file_temporarily(file_path: str, duration: int = 60) -> str | None:
    """Serve one local file temporarily and return its URL."""
    urls = serve_files_temporarily([file_path], duration)
    return urls[0] if urls else None


def get_video_duration_ms(video_path: str) -> int:
    """Return video duration in milliseconds using ffprobe, with a safe fallback."""
    if not os.path.isfile(video_path):
        _LOGGER.warning("Video file not found: %s", video_path)
        return 10000

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                video_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            _LOGGER.warning("ffprobe failed for %s: %s", video_path, result.stderr)
            return 10000
        duration_seconds = float(json.loads(result.stdout)["format"]["duration"])
        return max(int(duration_seconds * 1000), 1000)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as err:
        _LOGGER.warning("ffprobe error for %s: %s", video_path, err)
        return 10000


def _cleanup_public_cache() -> None:
    """Bound the dedicated Zalo public cache to avoid filling HA storage over time."""
    if not PUBLIC_DIR or not os.path.isdir(PUBLIC_DIR):
        return
    now = time.time()
    try:
        files = [entry for entry in os.scandir(PUBLIC_DIR) if entry.is_file()]
        # Delete stale transient copies first.
        for entry in files:
            try:
                if now - entry.stat().st_mtime > _PUBLIC_CACHE_MAX_AGE:
                    os.remove(entry.path)
            except OSError:
                pass
        files = [entry for entry in os.scandir(PUBLIC_DIR) if entry.is_file()]
        if len(files) > _PUBLIC_CACHE_MAX_FILES:
            files.sort(key=lambda entry: entry.stat().st_mtime)
            for entry in files[: len(files) - _PUBLIC_CACHE_MAX_FILES]:
                try:
                    os.remove(entry.path)
                except OSError:
                    pass
    except OSError as err:
        _LOGGER.debug("Không thể dọn cache public Zalo: %s", err)


def copy_to_public(src_path: str, zalo_server: str) -> str | None:
    """Copy a local file to the dedicated HA/Zalo shared public directory."""
    if not os.path.isfile(src_path):
        _LOGGER.error("Không tìm thấy file: %s", src_path)
        return None
    if PUBLIC_DIR is None:
        _LOGGER.error("PUBLIC_DIR chưa được khởi tạo")
        return None

    os.makedirs(PUBLIC_DIR, exist_ok=True)
    _cleanup_public_cache()

    filename = os.path.basename(src_path)
    stem, ext = os.path.splitext(filename)
    unique_filename = f"{stem}-{uuid.uuid4().hex[:12]}{ext}"
    dst_path = os.path.join(PUBLIC_DIR, unique_filename)
    shutil.copy2(src_path, dst_path)

    encoded_filename = urllib.parse.quote(unique_filename)
    relative_url = f"/local/zalo-server/{encoded_filename}"
    if is_local_zalo_server(zalo_server):
        return f"{zalo_server.rstrip('/')}/{encoded_filename}"
    return relative_url
