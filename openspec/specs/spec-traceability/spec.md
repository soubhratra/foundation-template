## Requirements

### Requirement: pytest requirement markers

Every pytest test function that exercises a specific OpenSpec requirement SHALL carry a `@pytest.mark.req()` marker linking it to one or more requirement IDs.

#### Scenario: Single-requirement test

- **WHEN** a test function covers exactly one requirement
- **THEN** it MUST be decorated with `@pytest.mark.req("REQ-ID")`
- **THEN** `REQ-ID` MUST match an ID listed in ROADMAP.md

#### Scenario: Multi-requirement test

- **WHEN** a test function exercises multiple requirements simultaneously
- **THEN** it MUST be decorated with `@pytest.mark.req("REQ-01", "REQ-02")`
- **THEN** all listed IDs MUST appear in the `Requirements` column of FAILURES.md when that test fails

#### Scenario: Marker registered to suppress warnings

- **WHEN** pytest runs
- **THEN** `req` MUST be declared in `pytest.ini` or `pyproject.toml` under `[tool.pytest.ini_options]` `markers`
- **THEN** no `PytestUnknownMarkWarning` is emitted for `@pytest.mark.req()`

#### Scenario: Tests without a traceable requirement

- **WHEN** a test function covers internal implementation details with no corresponding OpenSpec requirement
- **THEN** the `@pytest.mark.req()` decorator MAY be omitted
- **THEN** `check-req-coverage.py` MUST NOT flag this as a coverage gap

### Requirement: Playwright requirement comments

Every Playwright test that exercises a specific OpenSpec requirement SHALL carry a `// @spec:` comment at the start of the test body linking it to one or more requirement IDs.

#### Scenario: Single-requirement Playwright test

- **WHEN** a Playwright `test()` block covers one requirement
- **THEN** the first line of the test body MUST be `// @spec: REQ-ID`

#### Scenario: Multi-requirement Playwright test

- **WHEN** a Playwright `test()` block covers multiple requirements
- **THEN** the comment MUST be `// @spec: REQ-01, REQ-02`

#### Scenario: Coverage checker counts Playwright markers

- **WHEN** `check-req-coverage.py` runs
- **THEN** it MUST count `// @spec: REQ-ID` comments as coverage evidence equivalent to `@pytest.mark.req()`
- **THEN** a requirement covered only by Playwright (not pytest) MUST appear as `covered`, not `uncovered`

### Requirement: Spec traceability enforcement at phase completion

No GSD phase that introduces user-facing features SHALL be marked complete unless `check-req-coverage.py` reports zero uncovered requirements for that phase's requirement IDs.

#### Scenario: Phase marked complete with uncovered requirements

- **WHEN** a GSD phase is being verified
- **THEN** the verifier MUST run `scripts/check-req-coverage.py`
- **THEN** if any requirement ID from that phase appears as `uncovered`, the phase MUST NOT be marked complete

#### Scenario: Phase marked complete with full coverage

- **WHEN** `check-req-coverage.py` reports all phase requirement IDs as `covered` or `partial`
- **THEN** the phase MAY be marked complete with respect to spec traceability

### Requirement: Retrofitted markers on existing tests

All existing pytest test functions in `apps/api/tests/` that exercise v1.1–v1.4 features SHALL have `@pytest.mark.req()` markers added.

#### Scenario: Marker retrofit does not change test behavior

- **WHEN** `@pytest.mark.req()` is added to an existing test
- **THEN** the test MUST produce the same pass/fail result as before the marker was added
- **THEN** no test logic, assertions, or fixtures are modified

#### Scenario: Coverage baseline after retrofit

- **WHEN** all retrofitted markers have been added
- **THEN** `check-req-coverage.py` MUST report zero uncovered requirements for requirements AUTO-01 through E2E-10 (phases 35–38 are excluded from this baseline check — they are new tests, not retrofits)
