# Development Guide

## Project layout

- `app/` — FastAPI application, routers, services, SQLAlchemy models and configuration.
- `frontend/` — Vanilla HTML/CSS/JS for login, dashboard, admin and the embeddable widget.
- `tests/` — unit, API/integration and contract tests.
- `docs/` — architecture, API, security, RAG, deployment and Git documentation.
- `data/` — local SQLite database and embedded vector data. Runtime data is not a source-controlled artifact.

## Local setup

### Windows

Run `setup.bat` from the repository root.

### Linux / macOS

```bash
chmod +x run.sh
./run.sh
```

For a non-local bind:

```bash
HOST=0.0.0.0 PORT=8000 OPEN_BROWSER=false ./run.sh
```

## Manual development run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload --port 8000
```

The test suite is configured to import the repository root through `pytest.ini`, so no manual `PYTHONPATH` setting is required.

## Development flow

1. Start from `main` and pull the latest changes.
2. Create a focused branch such as `feature/rag-retrieval`.
3. Make a small, reviewable change.
4. Add or update a real test for behavior that changed.
5. Run `pytest -q` and any targeted checks.
6. Commit with Conventional Commits.
7. Merge into `main` with `--no-ff` after verification.
8. Delete the feature branch after the merge.

## Quality rules

- Preserve the current FastAPI + SQLAlchemy + SQLite + Vanilla JS architecture unless a change is necessary.
- Keep tenant data scoped by `user_id`.
- Do not place API keys or `.env` files in Git.
- Do not store raw suspicious prompt text as a security-flag reason.
- Do not turn heuristic prompt detection into a claim of complete security.
- Prefer measurable performance fixes over speculative optimization.
- Keep API errors understandable to clients and detailed internals in logs only.
