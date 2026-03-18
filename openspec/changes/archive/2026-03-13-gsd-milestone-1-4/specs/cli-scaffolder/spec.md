## ADDED Requirements

### Requirement: B2B Module Opt-In via --with b2b

The `create-foundation-app` CLI SHALL support an opt-in `--with b2b` flag that includes the complete B2B module in the scaffolded project.

#### Scenario: B2B excluded by default

- **WHEN** the user runs `create-foundation-app` without `--with b2b`
- **THEN** the B2B module SHALL NOT be included in the generated project
- **AND** the interactive features multiselect SHALL show "B2B Module" as unchecked by default

#### Scenario: --with b2b flag includes full B2B module

- **WHEN** the user runs `create-foundation-app --with b2b`
- **THEN** the B2B module SHALL be included (apps/orgs/, apps/api_keys/, apps/webhooks/, apps/audit/)
- **AND** `django-pghistory` and `django-hijack` SHALL remain in `pyproject.toml`
- **AND** all `# B2B_START` / `# B2B_END` marker blocks SHALL be retained in Python files

#### Scenario: removeB2BModule() strips all B2B artifacts cleanly

- **WHEN** B2B is not selected during scaffolding
- **THEN** `removeB2BModule(outputDir)` SHALL:
  - Delete `apps/api/apps/orgs/`, `apps/api/apps/api_keys/`, `apps/api/apps/webhooks/`, `apps/api/apps/audit/` directories
  - Remove `django-pghistory` and `django-hijack` from `pyproject.toml` dependencies
  - Strip all `# B2B_START` / `# B2B_END` fenced blocks from all Python files
  - Collapse consecutive blank lines (max 1) in any modified file

#### Scenario: Post-removal manage.py check passes

- **WHEN** the B2B module is removed via the scaffolder
- **THEN** `manage.py check` SHALL pass with no errors
- **AND** no `# B2B_START` or `# B2B_END` markers SHALL remain in any file
- **AND** `apps.orgs`, `apps.api_keys`, `apps.webhooks`, `apps.audit` SHALL be absent from `INSTALLED_APPS`

#### Scenario: CI validates both B2B-included and B2B-excluded scaffolds

- **WHEN** the CI test suite runs
- **THEN** `test_scaffold_with_b2b` SHALL verify `manage.py check` passes with the full B2B stack
- **AND** `test_scaffold_without_b2b` SHALL verify `manage.py check` passes after removal and assert all four negative conditions (no markers, no INSTALLED_APPS entries, no directories, no pyproject.toml deps)

## Implementation Decisions

### Why --with b2b is opt-in (not opt-out like --without email)

B2B is an enterprise add-on that most solo or B2C products will never need. Making it opt-out would impose B2B complexity on the majority of scaffolded projects. The `--with b2b` opt-in matches how products deliberately choose to enable enterprise infrastructure, consistent with the "start minimal, add what you need" philosophy.

This reverses the convention used for email, social auth, and billing, which are opt-out (included by default). The distinction is intentional: the default experience should be a B2C SaaS app; B2B is a deliberate escalation.

### Why B2B_START/B2B_END markers (not a separate B2B branch or overlay)

A separate branch or overlay would require merge maintenance as the template evolves. Inline markers let B2B code live alongside non-B2B code in the same files, validated continuously by the same CI suite. The marker stripper removes fenced blocks at scaffolding time, producing a clean output without the template's maintenance burden.

**Marker style:** Python comment markers only (`# B2B_START`, `# B2B_END`). TypeScript/frontend B2B code is handled by directory deletion rather than inline markers — the entire B2B frontend pages and components are in dedicated directories.

### Why pyproject.toml deps are removed by string matching (not markers)

TOML file format does not support comment blocks with the same inline-removal semantics as Python. Explicit regex string matching for `django-pghistory` and `django-hijack` in `pyproject.toml` is simpler and more reliable than trying to add marker comments to TOML dependency arrays, which would require TOML-aware parsing.

### Why CI runs manage.py check (not just import tests)

`manage.py check` runs Django's full system checks — it validates `INSTALLED_APPS`, URL conf imports, model consistency, and all registered checks including the ones added for `WEBHOOK_EVENTS` and `API_KEY_SCOPES` validation. An import-only test would not catch missing app registrations or misconfigured settings. `manage.py check` is the ground truth for "does this project start cleanly."
