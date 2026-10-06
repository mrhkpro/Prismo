"""صفحه‌ی راه‌اندازی لوکال را قبل از اجرای FastAPI اصلی سرو می‌کند."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SETUP_HTML = BASE_DIR / "frontend" / "setup.html"
HOST = "127.0.0.1"
PORT = 8000


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
    server_version = "QuasarSetup/2.6"

    def _json(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):  # noqa: N802
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
            self._json(200, {"ok": True, "mode": mode})
        except Exception as exc:  # noqa: BLE001
            self._json(400, {"detail": str(exc)})
            return

        self.server.selected_mode = mode
        threading.Timer(0.15, self.server.shutdown).start()

    def log_message(self, *_args):
        return


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), SetupHandler)
    server.selected_mode = None
    print(f"Quasar setup page: http://{HOST}:{PORT}/setup.html")
    threading.Timer(0.7, lambda: webbrowser.open(f"http://{HOST}:{PORT}/setup.html")).start()
    server.serve_forever()

    # بعد از انتخاب، bootstrap کامل از پورت خارج می‌شود و سپس برنامه اصلی
    # را روی همان پورت بالا می‌آورد؛ بنابراین race بین دو سرور نداریم.
    if server.selected_mode in {"local", "supabase"}:
        cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(PORT)]
        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        subprocess.Popen(cmd, cwd=str(BASE_DIR), creationflags=creationflags)


if __name__ == "__main__":
    main()
