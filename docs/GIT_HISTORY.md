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
## v2.2.2 release chain

- `feature/provider-diagnostics` → actionable upstream error classification
- `feature/error-surface` → dashboard/chat error details
- `feature/vercel-connection-tuning` → longer hosted provider windows
- `docs/provider-diagnostics` → deployment troubleshooting guide
- `docs/release-v2.2.2` → release notes

All branches were merged into `main` with `--no-ff` to preserve the graph.

