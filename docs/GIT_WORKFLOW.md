# Git Workflow

The repository uses focused feature branches and explicit merge commits.

```text
main
  ├─ feature/repository-foundation ──┐
  ├─ feature/vercel-ai-resilience ───┤
  ├─ feature/deployment-docs ────────┤ → merge --no-ff → main
  └─ feature/release-cleanup ────────┘
```

## Branch lifecycle

```bash
git switch main
git pull
git switch -c feature/<focused-change>

# implement + test
git add <files>
git commit -m "feat(scope): describe the real change"

git switch main
git merge --no-ff feature/<focused-change> -m "merge: describe the completed feature"
git branch -d feature/<focused-change>
```

## Commit convention

Use Conventional Commits: `feat`, `fix`, `refactor`, `test`, `security`, `perf`, `docs`, `style`, `chore`. Avoid placeholder messages such as `a`, `changes`, `final`, or `temp`.

## Release rule

Before deployment, run the relevant tests, inspect `git status`, and verify that `.env`, `.env.local`, `.venv`, `.vercel`, database files and generated caches are not tracked.
