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

## v2.4.0 release chain

Baseline first, then the redesign, then tests and the fixes they uncovered. Every branch was merged into `main` with `--no-ff`.

- `chore/v2.3.0-snapshot` → records the uncommitted v2.3.0 working tree as a baseline
- `test/admin-inspect-baseline` → tracks the existing admin inspection regression test
- `style/dual-theme-tokens` → violet night + gold day design tokens
- `style/base-controls` → base, buttons, inputs, badges, toasts
- `style/app-shell-components` → sidebar, cards, tables, chat, modals (removes the v2.3 override block)
- `style/landing-auth` → landing showcase and sign-in card
- `style/widget-dual-theme` → widget palettes, accent-aware text, theme-aware preview
- `fix/theme-visual-regressions` → preview iframe canvas, Persian mono fallback
- `fix/asset-cache-bust-2.4.0` → `?v=2.4.0` everywhere including the embed snippet
- `test/full-platform-flow` → 46-scenario end-to-end API suite
- `fix/dark-button-contrast` → WCAG AA for the dark primary button
- `test/theme-contracts` → static theme/contrast/wiring contracts
- `fix/widget-session-source-scope` → public widget only continues widget sessions
- `fix/knowledge-clear-order` → chunks deleted before documents on "clear all"
- `fix/playground-session-source-scope` → playground only continues playground sessions
- `docs/release-2.4.0` → changelog and this history

