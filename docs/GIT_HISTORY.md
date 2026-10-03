# Git History

This repository history was rebuilt from the supplied working tree on 2026-10-03. The goal is a readable, intentional graph rather than a sequence of ad-hoc repair commits.

## Branches rebuilt

1. `feature/repository-foundation` — repository hygiene and deterministic ignore rules.
2. `feature/vercel-ai-resilience` — hosted AI connection timeout/retry behavior and safe diagnostics.
3. `feature/deployment-docs` — Vercel environment and AI connectivity troubleshooting documentation.
4. `feature/release-cleanup` — final documentation/changelog cleanup.

Each branch is merged with `--no-ff` so the graph visibly records the feature boundary.

## Verification

- Python syntax compilation: passed.
- AI provider unit tests with local SQLite override: passed.
- Full suite requires the project's `.venv` because the supplied runtime archive does not include installed dependencies.
- No `.venv` is included in the release archive.

## Secret handling

The supplied `.env` remains a local working file and is intentionally not committed to Git. The project archive may contain it for local execution, but Git history does not.
