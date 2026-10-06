"""صفحه‌ی راه‌اندازی لوکال را قبل از اجرای FastAPI اصلی سرو می‌کند."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SETUP_HTML = BASE_DIR / "frontend" / "setup.html"
HOST = "127.0.0.1"
SETUP_PORT = 8765
APP_PORT = 8000


def _upsert_env(name: str, value: str) -> None:
    env_path = BASE_DIR / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    prefix = name + "="
    replaced = False
    out: list[str] = []
    for line in lines:
        if line.startswith(prefix):
            out.append(prefix + value)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        if out and out[-1] != "":
            out.append("")
        out.append(prefix + value)
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


class SetupHandler(BaseHTTPRequestHandler):
    server_version = "QuasarSetup/2.6.6"

    def _json(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):  # noqa: N802
        if self.path == "/__setup/status":
            proc = getattr(self.server, "app_process", None)
            if proc is None:
                self._json(200, {"state": "idle"})
                return
            code = proc.poll()
            if code is None:
                self._json(200, {"state": "starting"})
                return
            log_path = BASE_DIR / "data" / "quasar-startup.log"
            detail = ""
            if log_path.exists():
                try:
                    detail = "\n".join(log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-12:])
                except Exception:
                    detail = ""
            self._json(200, {"state": "failed", "returncode": code, "detail": detail[-3000:]})
            return
        if self.path in {"/", "/setup", "/setup.html"}:
            raw = SETUP_HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        self._json(404, {"detail": "صفحه پیدا نشد."})

    def do_POST(self):  # noqa: N802
        if self.path != "/__setup/choose":
            self._json(404, {"detail": "مسیر پیدا نشد."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            mode = payload.get("mode")
            if mode not in {"local", "supabase"}:
                raise ValueError("حالت دیتابیس نامعتبر است.")
            _upsert_env("DATABASE_MODE", mode)
        except Exception as exc:  # noqa: BLE001
            self._json(400, {"detail": str(exc)})
            return

        self.server.selected_mode = mode
        try:
            log_path = BASE_DIR / "data" / "quasar-startup.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_handle = open(log_path, "w", encoding="utf-8")
            cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(APP_PORT)]
            creationflags = 0
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            self.server.app_process = subprocess.Popen(
                cmd, cwd=str(BASE_DIR), creationflags=creationflags,
                stdout=log_handle, stderr=subprocess.STDOUT,
            )
        except Exception as exc:
            self._json(500, {"detail": f"اجرای برنامه اصلی شروع نشد: {exc}"})
            return
        self._json(200, {"ok": True, "mode": mode, "app_port": APP_PORT})

        def _close_when_ready():
            for _ in range(50):
                try:
                    with urllib.request.urlopen(f"http://{HOST}:{APP_PORT}/api/runtime", timeout=0.5) as resp:
                        if resp.status == 200:
                            time.sleep(0.35)
                            self.server.shutdown()
                            return
                except Exception:
                    time.sleep(0.2)
            # Keep the setup server alive if startup failed so the page can show
            # the log instead of disappearing before the user sees the error.

        threading.Thread(target=_close_when_ready, daemon=True).start()

    def log_message(self, *_args):
        return


def main() -> None:
    server = ThreadingHTTPServer((HOST, SETUP_PORT), SetupHandler)
    server.selected_mode = None
    server.app_process = None
    print(f"Quasar setup page: http://{HOST}:{SETUP_PORT}/setup.html")
    threading.Timer(0.7, lambda: webbrowser.open(f"http://{HOST}:{SETUP_PORT}/setup.html")).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
