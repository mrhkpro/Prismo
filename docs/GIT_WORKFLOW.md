# Git Workflow

The repository uses a lightweight feature-branch workflow designed for a small team while keeping the history readable.

## Branch lifecycle

```text
main
  └─ feature/<focused-change>
       ├─ implementation commit(s)
       ├─ test/documentation commit(s)
       └─ merge --no-ff → main
```

Typical commands:

```bash
git checkout main
git pull
git checkout -b feature/<name>

# work + test
git add <files>
git commit -m "feat(scope): describe the real change"

git checkout main
git merge --no-ff feature/<name> -m "merge: describe the completed feature"
git branch -d feature/<name>
```

## Commit convention

Use Conventional Commits and keep each commit meaningful:

- `feat` — new behavior
- `fix` — defect correction
- `refactor` — structure without changing intended behavior
- `test` — real test coverage
- `security` — security-focused change
- `perf` — measured or targeted performance improvement
- `docs` — documentation of implemented behavior
- `style` — UI/code style change with no domain behavior change
- `chore` — project/tooling maintenance

Avoid placeholders such as `update`, `changes`, `final`, `temp`, or `aaa`.

## Merge policy

A feature is merged only after its relevant tests pass. `--no-ff` is intentional: the merge commit keeps the feature boundary visible in the repository graph.

The authoritative record of the completed feature branches and real commit hashes is `docs/GIT_HISTORY.md`.
