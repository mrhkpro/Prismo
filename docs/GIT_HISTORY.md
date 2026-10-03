# Git History

This file records the completed feature-branch work and real Git hashes in the sanitized repository history. It was generated after commit `5de6826` and therefore does not include the commit that refreshes this file.

## Workflow

Feature branches were implemented, verified, merged into `main` with `--no-ff`, and deleted. The improvement pass preserves the feature/merge topology while removing the historically tracked `.env` from reachable Git history.

## 1. feature/ai-provider

- **Merge:** `3b8097d9` — `merge: add AI provider model discovery`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `31adb9c1`
- **Message:** `feat(provider): add custom model discovery and connection testing`
- **Files:** `app/routers/settings.py`, `app/schemas.py`, `app/services/llm_client.py`, `frontend/assets/js/dashboard.js`, `frontend/dashboard.html`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `f042dfe7`
- **Message:** `test(provider): cover model discovery without persistence`
- **Files:** `docs/API.md`, `tests/test_ai_provider.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 2. feature/registration

- **Merge:** `7decf3b8` — `merge: harden registration flow`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `366d1b85`
- **Message:** `feat(auth): normalize usernames and handle duplicate registration safely`
- **Files:** `app/routers/auth.py`, `app/schemas.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `e300477d`
- **Message:** `test(auth): cover normalized registration and login input`
- **Files:** `app/routers/auth.py`, `tests/test_registration.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 3. feature/backend-architecture

- **Merge:** `f362d611` — `merge: centralize API error handling`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `1f27ead7`
- **Message:** `refactor(core): centralize application and provider errors`
- **Files:** `app/exceptions.py`, `app/main.py`, `app/services/llm_client.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `43818b30`
- **Message:** `refactor(api): use centralized provider error handling`
- **Files:** `app/routers/knowledge.py`, `app/routers/playground.py`, `app/routers/public_widget.py`, `app/routers/settings.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 4. feature/dashboard

- **Merge:** `fc16118b` — `merge: add user dashboard summary`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `1f4bdd30`
- **Message:** `feat(dashboard): add user-scoped summary endpoint`
- **Files:** `app/main.py`, `app/routers/dashboard.py`, `app/schemas.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `c797b7ea`
- **Message:** `style(dashboard): surface user metrics and service health`
- **Files:** `frontend/assets/css/style.css`, `frontend/assets/js/dashboard.js`, `frontend/dashboard.html`
- **Validation:** relevant feature tests and branch verification

### Commit 3
- **Hash:** `a34dfca6`
- **Message:** `test(dashboard): verify scoped metrics and session counts`
- **Files:** `tests/test_dashboard.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 5. feature/api-hardening

- **Merge:** `c0191f48` — `merge: harden API input validation`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `159b3b00`
- **Message:** `feat(api): constrain public input and validate provider URLs`
- **Files:** `app/config.py`, `app/schemas.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `c2a0c012`
- **Message:** `test(api): cover input limits and validation contracts`
- **Files:** `tests/test_api_hardening.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 6. feature/login

- **Merge:** `9f525a00` — `merge: harden login token validation`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `0dcdb606`
- **Message:** `fix(auth): reject malformed token subjects and authenticate failures clearly`
- **Files:** `app/routers/auth.py`, `app/security.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `8e886bb1`
- **Message:** `test(auth): cover malformed JWT subject handling`
- **Files:** `tests/test_login_security.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 7. feature/rag-pipeline

- **Merge:** `d89ca014` — `merge: strengthen RAG message assembly`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `81b2657a`
- **Message:** `refactor(rag): isolate context assembly and bound conversation history`
- **Files:** `app/services/rag_pipeline.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `f490d201`
- **Message:** `test(rag): cover context boundaries and history budget`
- **Files:** `tests/test_rag_pipeline.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 8. feature/rag-retrieval

- **Merge:** `b060eb18` — `merge: improve RAG retrieval filtering`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `db284448`
- **Message:** `feat(retrieval): add configurable semantic similarity threshold`
- **Files:** `app/config.py`, `app/models.py`, `app/routers/playground.py`, `app/routers/settings.py`, `app/schemas.py`, `app/services/rag_pipeline.py`, `app/services/rag_store.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `3e9af20f`
- **Message:** `feat(retrieval): expose threshold tuning in the RAG settings UI`
- **Files:** `frontend/assets/js/dashboard.js`, `frontend/dashboard.html`, `tests/test_rag_store.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 9. feature/knowledge-base

- **Merge:** `5d564720` — `merge: add knowledge base reindexing`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `64e39946`
- **Message:** `feat(knowledge): add explicit document reindex operation`
- **Files:** `app/routers/knowledge.py`, `docs/API.md`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `6aa59ef3`
- **Message:** `test(knowledge): verify safe document reindexing`
- **Files:** `tests/test_knowledge_reindex.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 10. feature/chat-playground

- **Merge:** `b32615da` — `merge: improve playground session lifecycle`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `cced0eae`
- **Message:** `feat(chat): add owned playground session cleanup`
- **Files:** `app/routers/playground.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `d74df541`
- **Message:** `feat(chat): clear persisted playground sessions from the UI`
- **Files:** `frontend/assets/js/dashboard.js`, `tests/test_chat_session_cleanup.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 11. feature/widget

- **Merge:** `cef1945e` — `merge: improve embeddable widget experience`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `4c709fe2`
- **Message:** `feat(widget): ship resilient embeddable preview and cache-busted embed code`
- **Files:** `app/routers/widget.py`, `frontend/widget-preview.html`, `frontend/widget.js`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `18c7bf2b`
- **Message:** `test(widget): verify embed and Shadow DOM contracts`
- **Files:** `tests/test_widget_contract.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 12. feature/widget-security

- **Merge:** `07b906e2` — `merge: protect public widget endpoints`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `8d6af7de`
- **Message:** `security(widget): add bounded in-memory rate limiting to public chat`
- **Files:** `app/config.py`, `app/routers/public_widget.py`, `app/services/rate_limit.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `935ad168`
- **Message:** `test(widget): cover public rate limiting behavior`
- **Files:** `tests/test_widget_rate_limit.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 13. feature/prompt-security

- **Merge:** `da5bb70a` — `merge: strengthen prompt injection monitoring`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `0e020d26`
- **Message:** `security(prompt): normalize input and categorize injection flags`
- **Files:** `app/services/injection_scanner.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `82e4b8f5`
- **Message:** `test(prompt): cover normalized injection detection and safe flag reasons`
- **Files:** `tests/test_prompt_security.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 14. feature/model-battle

- **Merge:** `8fd05686` — `merge: improve model battle execution`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `3bffc5c3`
- **Message:** `perf(battle): run model comparisons concurrently`
- **Files:** `app/routers/playground.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `5da6976d`
- **Message:** `test(battle): verify parallel model execution`
- **Files:** `tests/test_model_battle.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 15. feature/admin-panel

- **Merge:** `1d8552c5` — `merge: paginate admin monitoring queries`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `f2210795`
- **Message:** `feat(admin): paginate management and security monitoring queries`
- **Files:** `app/routers/admin.py`, `docs/API.md`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `93e8af1d`
- **Message:** `fix(admin): apply pagination before materializing management results`
- **Files:** `app/routers/admin.py`, `tests/test_admin_pagination.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 16. feature/rbac

- **Merge:** `e2dbf1df` — `merge: harden role and administrator controls`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `067ad754`
- **Message:** `security(rbac): prevent removing the last active administrator`
- **Files:** `app/routers/admin.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `f6e9f389`
- **Message:** `test(rbac): cover administrator lockout safeguards`
- **Files:** `tests/test_rbac_safety.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 17. feature/testing

- **Merge:** `45b1587a` — `merge: expand API test coverage`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `29e90983`
- **Message:** `test(core): centralize offline OpenAI test stubs`
- **Files:** `tests/conftest.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `8be32870`
- **Message:** `test(api): cover authentication and tenant data isolation`
- **Files:** `tests/test_api_integration.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 18. feature/logging

- **Merge:** `4e5a3666` — `merge: add request logging and correlation IDs`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `68644b82`
- **Message:** `chore(logging): add request IDs and structured request timing logs`
- **Files:** `app/main.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `640edcd6`
- **Message:** `test(logging): verify request IDs are returned to clients`
- **Files:** `tests/test_logging.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 19. feature/performance

- **Merge:** `4ee85a2f` — `merge: optimize repeated aggregate queries`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `d1325804`
- **Message:** `perf(knowledge): count document chunks in one grouped query`
- **Files:** `app/routers/knowledge.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `031b8abe`
- **Message:** `perf(admin): batch document and session counts for user listings`
- **Files:** `app/routers/admin.py`
- **Validation:** relevant feature tests and branch verification

### Commit 3
- **Hash:** `151e59c5`
- **Message:** `test(perf): verify optimized aggregate query contracts`
- **Files:** `tests/test_performance_queries.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 20. feature/security-hardening

- **Merge:** `e4c3721f` — `merge: harden runtime secret handling`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `9ed70b22`
- **Message:** `security(repo): remove committed secrets and require production secret configuration`
- **Files:** `.env.example`, `.gitignore`, `README.md`, `app/config.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `9e1984b9`
- **Message:** `test(security): enforce runtime secret requirements and env hygiene`
- **Files:** `app/config.py`, `tests/test_security_hardening.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 21. feature/frontend-ux

- **Merge:** `f10093c5` — `merge: polish frontend experience`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `500f4143`
- **Message:** `style(frontend): add theme switching and responsive dashboard polish`
- **Files:** `frontend/admin.html`, `frontend/assets/css/style.css`, `frontend/assets/js/theme.js`, `frontend/index.html`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `51c89818`
- **Message:** `feat(frontend): add fetch timeouts and accessible toast notifications`
- **Files:** `frontend/assets/js/api.js`
- **Validation:** relevant feature tests and branch verification

### Commit 3
- **Hash:** `80d0d0f8`
- **Message:** `test(frontend): cover theme assets and client request contracts`
- **Files:** `tests/test_frontend_contracts.py`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 22. feature/deployment

- **Merge:** `f40f7084` — `merge: prepare deployment configuration`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `c40262c3`
- **Message:** `security(config): require explicit production secret configuration`
- **Files:** `app/config.py`
- **Validation:** relevant feature tests and branch verification

### Commit 2
- **Hash:** `3d16bbcf`
- **Message:** `chore(deployment): make Windows setup encoding-safe and deterministic`
- **Files:** `setup.bat`, `tests/test_security_hardening.py`
- **Validation:** relevant feature tests and branch verification

### Commit 3
- **Hash:** `54d2281b`
- **Message:** `feat(deployment): make the launcher configurable for local or hosted runs`
- **Files:** `run.sh`
- **Validation:** relevant feature tests and branch verification

### Commit 4
- **Hash:** `3984fbee`
- **Message:** `docs(deployment): document local and hosted runtime configuration`
- **Files:** `docs/DEPLOYMENT.md`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## 23. chore/test-runner

- **Merge:** `1d5e8663` — `merge: standardize test runner configuration`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `d3080e38`
- **Message:** `chore(test): make pytest imports work from repository root`
- **Files:** `pytest.ini`
- **Validation:** relevant feature tests and branch verification

**Merge strategy:** `git merge --no-ff`

## Post-feature documentation commits

### `1c9a6245` — docs(core): document development workflow and current API architecture
- Files: `docs/API.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT.md`, `docs/GIT_WORKFLOW.md`

### `ce954154` — docs(security): document RAG boundaries and security controls
- Files: `docs/RAG.md`, `docs/SECURITY.md`

### `5de6826f` — docs(readme): refresh project overview and release changelog
- Files: `README.md`, `docs/CHANGELOG.md`

## 24. feature/setup-network-resilience

- **Merge:** `fb7c0e6` — `merge: add resilient windows dependency setup`
- **Date:** 2026-10-01

### Commit 1
- **Hash:** `8f933e6`
- **Message:** `fix(setup): add pip index fallback for dns failures`
- **Files:** `setup.bat`
- **Validation:** static installer checks; full pytest suite passed

### Commit 2
- **Hash:** `73fd687`
- **Message:** `docs(deployment): document resilient windows installer`
- **Files:** `docs/DEPLOYMENT.md`
- **Validation:** documentation review

### Commit 3
- **Hash:** `9e3165d`
- **Message:** `docs(changelog): record setup network fix`
- **Files:** `docs/CHANGELOG.md`
- **Validation:** documentation review

**Merge strategy:** `git merge --no-ff`
