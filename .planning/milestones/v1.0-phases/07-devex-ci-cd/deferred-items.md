# Deferred Items - Phase 07

## Out of Scope Items Discovered During Execution

### Pre-existing mypy Type Errors

**Discovered during:** Plan 07-01, Task 2 verification
**Context:** Running `pnpm type-check` revealed 28 pre-existing mypy errors in the API codebase

**Errors include:**

- Missing library stubs for third-party packages (pgvector, allauth, celery, langchain)
- Type annotation issues in apps/accounts/services.py (User type alias)
- Import-untyped warnings throughout the codebase
- Used-before-def error in apps/ai/tasks.py

**Why deferred:**

- These errors existed before Phase 07 work began
- Not caused by pre-commit hook installation
- TypeScript type checking passes cleanly for web/mobile
- Python tooling (mypy) is properly installed and functional

**Recommendation:**

- Add type stubs for third-party libraries or configure mypy to ignore missing stubs
- Fix User type alias issues in accounts/services.py
- Address used-before-def error in ai/tasks.py
- Consider adding mypy to CI pipeline with baseline exclusions

**Impact:**

- Low priority - does not block development
- Type checking is available and functional
- Pre-commit hooks work correctly for formatting and linting
