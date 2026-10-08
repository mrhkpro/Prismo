#!/usr/bin/env bash
# اجرای معادل setup.bat روی لینوکس/مک
set -e
cd "$(dirname "$0")"

echo "================================================================"
echo "  کوازار / Quasar — پلتفرم ویجت هوشمند RAG"
echo "================================================================"
echo

PY_CMD=$(command -v python3 || command -v python || true)
if [ -z "$PY_CMD" ]; then
    echo "[خطا] پایتون ۳ پیدا نشد. لطفاً نصبش کن."
    exit 1
fi

if [ ! -f ".venv/bin/python" ]; then
    echo "[1/4] ساخت محیط مجازی..."
    "$PY_CMD" -m venv .venv
else
    echo "[1/4] محیط مجازی از قبل موجود است."
fi

VENV_PY="$(pwd)/.venv/bin/python"

echo "[2/4] نصب وابستگی‌ها..."
"$VENV_PY" -m pip install --upgrade pip -q
"$VENV_PY" -m pip install -r requirements.txt -q

echo "[3/4] آماده‌سازی پوشه‌ی دیتا..."
mkdir -p data
[ -f ".env" ] || cp ".env.example" ".env"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
OPEN_BROWSER="${OPEN_BROWSER:-true}"

echo "[4/4] Starting FastAPI..."
echo
echo "Application URL: http://${HOST}:${PORT}"
echo "Stop with: Ctrl+C"
echo

if [ "$OPEN_BROWSER" = "true" ] && [ "$HOST" = "127.0.0.1" ]; then
    ( sleep 3 && (command -v open >/dev/null && open "http://127.0.0.1:${PORT}/" || command -v xdg-open >/dev/null && xdg-open "http://127.0.0.1:${PORT}/" || true) ) &
fi

"$VENV_PY" -m uvicorn app.main:app --host "$HOST" --port "$PORT" --no-access-log
