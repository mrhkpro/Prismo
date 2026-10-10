#!/usr/bin/env python3
"""
ابزار خط‌فرمان برای تست واقعیِ کشف مدل در برابر یک provider واقعی (مثل
OpenRouter) -- دقیقاً همان مسیر کدی که دکمه‌ی «دریافت مدل‌ها»/«دریافت
مدل‌های Embedding» در داشبورد اجرا می‌کند، اما بدون نیاز به اجرای کل سرور.

استفاده:
    cd Main
    python scripts/verify_model_discovery.py \
        --base-url https://openrouter.ai/api/v1 \
        --api-key sk-or-...

    # برای تست کلید embedding جداگانه:
    python scripts/verify_model_discovery.py \
        --base-url https://openrouter.ai/api/v1 --api-key sk-or-... \
        --embedding-base-url https://openrouter.ai/api/v1 --embedding-api-key sk-or-...

خروجی دقیقاً نشان می‌دهد: چند مدل کلاً در کاتالوگ provider هست، چند تا probe
شدند (و اگر سقف probe فعال شده، کدام‌ها حذف شدند)، و در نهایت کدام مدل‌ها
واقعاً روی چت و embedding جواب داده‌اند.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_MODE", "local")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SECRET_KEY", "verify-script-secret-key-32-chars-ok")

from app.services import llm_client  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", required=True, help="e.g. https://openrouter.ai/api/v1")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--embedding-base-url", default=None)
    parser.add_argument("--embedding-api-key", default=None)
    args = parser.parse_args()

    print(f"Discovering models at {args.base_url} ...")
    t0 = time.time()
    try:
        result = llm_client.discover_model_capabilities(
            args.base_url, args.api_key, args.embedding_base_url, args.embedding_api_key
        )
    except Exception as exc:
        print(f"FAILED: {exc}")
        sys.exit(1)
    elapsed = time.time() - t0

    print(f"\nDone in {elapsed:.2f}s")
    print(f"Total models in catalog: {result['total_models_found']}")
    print(f"Chat candidates probed:      {result['chat_candidates_probed']}"
          f"{'  (TRUNCATED -- raise MAX_CHAT_MODEL_PROBES)' if result['chat_candidates_truncated'] else ''}")
    print(f"Embedding candidates probed: {result['embedding_candidates_probed']}"
          f"{'  (TRUNCATED -- raise MAX_EMBEDDING_MODEL_PROBES)' if result['embedding_candidates_truncated'] else ''}")
    print(f"\nVerified chat models ({len(result['chat_models'])}):")
    for m in result["chat_models"]:
        print(f"  - {m}")
    print(f"\nVerified embedding models ({len(result['embedding_models'])}):")
    for m in result["embedding_models"]:
        print(f"  - {m}")
    if result["dual_capable_models"]:
        print(f"\nModels that work for BOTH chat and embedding: {result['dual_capable_models']}")


if __name__ == "__main__":
    main()
