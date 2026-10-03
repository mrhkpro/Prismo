# Git History

تاریخچه پروژه به‌صورت feature-branch و mergeهای `--no-ff` نگه‌داری می‌شود تا هر دسته تغییر در graph قابل تشخیص باشد.

## Release line

```text
main
├─ feature/repository-foundation
├─ feature/vercel-ai-resilience
├─ feature/deployment-docs
├─ feature/release-cleanup
├─ feature/release-notes
├─ feature/release-notes-doc
├─ feature/chat-performance
├─ feature/model-switching
├─ feature/chat-observability
└─ docs/vercel-chat-runbook
```

## Convention

- `feat:` برای قابلیت جدید
- `fix:` برای اصلاح رفتار
- `perf:` برای بهبود سرعت/مصرف
- `test:` برای قراردادهای تست
- `docs:` برای مستندات
- `chore:` برای نگه‌داری repository

برای حفظ graph، ادغام branchهای feature در `main` با `git merge --no-ff` انجام می‌شود.
