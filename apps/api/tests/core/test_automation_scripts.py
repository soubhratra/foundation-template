"""
Tests for Phase 35: Automation Scripts & Spec Traceability (v1.5).

AUTO-01: scripts/run-api-tests.sh exists with pytest runner and FAILURES.md output
AUTO-02: scripts/run-e2e-tests.sh exists with Playwright runner and FAILURES.md output
AUTO-03: scripts/run-all-tests.sh supports --mode=dev and --mode=ci flags
AUTO-04: scripts/check-req-coverage.py exists and produces a coverage table

CI-01: e2e-nightly.yml runs at 2am UTC with Docker Compose + failure issue creation
CI-02: ci.yml includes an e2e-smoke job triggered on PRs
CI-03: e2e-nightly.yml uploads FAILURES.md as a GitHub Actions artifact

DOCS-01: CLAUDE.md documents the two-mode testing pattern with both run-all-tests.sh modes
DOCS-02: CLAUDE.md documents @pytest.mark.req() and // @spec: traceability conventions
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"


# ---------------------------------------------------------------------------
# AUTO-01: run-api-tests.sh
# ---------------------------------------------------------------------------


@pytest.mark.req("AUTO-01")
def test_run_api_tests_script_exists():
    """scripts/run-api-tests.sh exists at repo root."""
    script = SCRIPTS_DIR / "run-api-tests.sh"
    assert script.exists(), f"scripts/run-api-tests.sh not found at {script}"


@pytest.mark.req("AUTO-01")
def test_run_api_tests_script_is_executable():
    """scripts/run-api-tests.sh has executable permission."""
    import os

    script = SCRIPTS_DIR / "run-api-tests.sh"
    assert os.access(script, os.X_OK), "scripts/run-api-tests.sh is not executable"


@pytest.mark.req("AUTO-01")
def test_run_api_tests_script_references_pytest():
    """scripts/run-api-tests.sh invokes pytest and writes FAILURES.md on failure."""
    content = (SCRIPTS_DIR / "run-api-tests.sh").read_text()
    assert "pytest" in content, "run-api-tests.sh must invoke pytest"
    assert "FAILURES" in content, "run-api-tests.sh must reference FAILURES.md output"


# ---------------------------------------------------------------------------
# AUTO-02: run-e2e-tests.sh
# ---------------------------------------------------------------------------


@pytest.mark.req("AUTO-02")
def test_run_e2e_tests_script_exists():
    """scripts/run-e2e-tests.sh exists at repo root."""
    script = SCRIPTS_DIR / "run-e2e-tests.sh"
    assert script.exists(), f"scripts/run-e2e-tests.sh not found at {script}"


@pytest.mark.req("AUTO-02")
def test_run_e2e_tests_script_is_executable():
    """scripts/run-e2e-tests.sh has executable permission."""
    import os

    script = SCRIPTS_DIR / "run-e2e-tests.sh"
    assert os.access(script, os.X_OK), "scripts/run-e2e-tests.sh is not executable"


@pytest.mark.req("AUTO-02")
def test_run_e2e_tests_script_references_playwright_and_base_url():
    """scripts/run-e2e-tests.sh runs Playwright and respects BASE_URL env var."""
    content = (SCRIPTS_DIR / "run-e2e-tests.sh").read_text()
    assert "playwright" in content.lower(), "run-e2e-tests.sh must invoke Playwright"
    assert "BASE_URL" in content, "run-e2e-tests.sh must support BASE_URL env var"
    assert "FAILURES" in content, "run-e2e-tests.sh must reference FAILURES.md output"


# ---------------------------------------------------------------------------
# AUTO-03: run-all-tests.sh
# ---------------------------------------------------------------------------


@pytest.mark.req("AUTO-03")
def test_run_all_tests_script_exists():
    """scripts/run-all-tests.sh exists at repo root."""
    script = SCRIPTS_DIR / "run-all-tests.sh"
    assert script.exists(), f"scripts/run-all-tests.sh not found at {script}"


@pytest.mark.req("AUTO-03")
def test_run_all_tests_script_supports_mode_dev():
    """scripts/run-all-tests.sh supports --mode=dev flag."""
    content = (SCRIPTS_DIR / "run-all-tests.sh").read_text()
    assert "--mode=dev" in content, "run-all-tests.sh must support --mode=dev"


@pytest.mark.req("AUTO-03")
def test_run_all_tests_script_supports_mode_ci():
    """scripts/run-all-tests.sh supports --mode=ci flag."""
    content = (SCRIPTS_DIR / "run-all-tests.sh").read_text()
    assert "--mode=ci" in content, "run-all-tests.sh must support --mode=ci"


@pytest.mark.req("AUTO-03")
def test_run_all_tests_script_produces_failures_md():
    """scripts/run-all-tests.sh writes test-results/FAILURES.md on failure."""
    content = (SCRIPTS_DIR / "run-all-tests.sh").read_text()
    assert "FAILURES" in content, "run-all-tests.sh must reference FAILURES.md"
    assert "test-results" in content, "run-all-tests.sh must write to test-results/"


# ---------------------------------------------------------------------------
# AUTO-04: check-req-coverage.py
# ---------------------------------------------------------------------------


@pytest.mark.req("AUTO-04")
def test_check_req_coverage_script_exists():
    """scripts/check-req-coverage.py exists at repo root."""
    script = SCRIPTS_DIR / "check-req-coverage.py"
    assert script.exists(), f"scripts/check-req-coverage.py not found at {script}"


@pytest.mark.req("AUTO-04")
def test_check_req_coverage_produces_coverage_table():
    """scripts/check-req-coverage.py emits a tabular coverage report."""
    content = (SCRIPTS_DIR / "check-req-coverage.py").read_text()
    assert "covered" in content, "check-req-coverage.py must emit coverage status"
    assert "uncovered" in content, "check-req-coverage.py must flag uncovered requirements"
    assert "REQ-ID" in content or "req_id" in content.lower(), (
        "check-req-coverage.py must produce a per-requirement table"
    )


# ---------------------------------------------------------------------------
# CI-01: e2e-nightly.yml
# ---------------------------------------------------------------------------


@pytest.mark.req("CI-01")
def test_e2e_nightly_workflow_exists():
    """`.github/workflows/e2e-nightly.yml` exists."""
    wf = WORKFLOWS_DIR / "e2e-nightly.yml"
    assert wf.exists(), f"e2e-nightly.yml not found at {wf}"


@pytest.mark.req("CI-01")
def test_e2e_nightly_runs_at_2am_utc():
    """e2e-nightly.yml schedule cron is set to 2am UTC (`0 2 * * *`)."""
    content = (WORKFLOWS_DIR / "e2e-nightly.yml").read_text()
    assert "0 2 * * *" in content, "e2e-nightly.yml cron schedule must be '0 2 * * *' (2am UTC)"


@pytest.mark.req("CI-01")
def test_e2e_nightly_uses_docker_compose():
    """e2e-nightly.yml starts Docker Compose to spin up the full stack."""
    content = (WORKFLOWS_DIR / "e2e-nightly.yml").read_text()
    assert "docker compose" in content.lower() or "docker-compose" in content.lower(), (
        "e2e-nightly.yml must spin up Docker Compose"
    )


@pytest.mark.req("CI-01")
def test_e2e_nightly_creates_github_issue_on_failure():
    """e2e-nightly.yml creates a GitHub issue when the suite fails."""
    content = (WORKFLOWS_DIR / "e2e-nightly.yml").read_text()
    assert "gh issue create" in content, "e2e-nightly.yml must create a GitHub issue on failure"


# ---------------------------------------------------------------------------
# CI-02: ci.yml e2e-smoke job
# ---------------------------------------------------------------------------


@pytest.mark.req("CI-02")
def test_ci_yml_has_e2e_smoke_job():
    """ci.yml includes an `e2e-smoke` job that runs on PRs."""
    content = (WORKFLOWS_DIR / "ci.yml").read_text()
    assert "e2e-smoke" in content, "ci.yml must have an e2e-smoke job for PR smoke testing"


@pytest.mark.req("CI-02")
def test_ci_yml_e2e_smoke_runs_auth_and_health_tests():
    """ci.yml e2e-smoke job runs the auth and health probe E2E tests."""
    content = (WORKFLOWS_DIR / "ci.yml").read_text()
    assert "auth.spec" in content, "ci.yml e2e-smoke must run auth.spec.ts"
    assert "health.spec" in content, "ci.yml e2e-smoke must run health.spec.ts"


# ---------------------------------------------------------------------------
# CI-03: FAILURES.md artifact upload
# ---------------------------------------------------------------------------


@pytest.mark.req("CI-03")
def test_e2e_nightly_uploads_failures_artifact():
    """e2e-nightly.yml uploads FAILURES.md as a GitHub Actions artifact."""
    content = (WORKFLOWS_DIR / "e2e-nightly.yml").read_text()
    assert "upload-artifact" in content, "e2e-nightly.yml must upload a FAILURES.md artifact"
    assert "FAILURES.md" in content or "failures" in content.lower(), (
        "e2e-nightly.yml artifact must reference FAILURES.md"
    )


# ---------------------------------------------------------------------------
# DOCS-01: Two-mode testing pattern in root CLAUDE.md
# ---------------------------------------------------------------------------


@pytest.mark.req("DOCS-01")
def test_claude_md_documents_two_mode_testing_pattern():
    """Root CLAUDE.md contains the Two-Mode Testing Pattern section."""
    content = CLAUDE_MD.read_text()
    assert "Two-Mode Testing Pattern" in content, (
        "CLAUDE.md must document the Two-Mode Testing Pattern"
    )


@pytest.mark.req("DOCS-01")
def test_claude_md_documents_dev_mode():
    """Root CLAUDE.md documents the --mode=dev auto-fix loop command."""
    content = CLAUDE_MD.read_text()
    assert "--mode=dev" in content, "CLAUDE.md must document run-all-tests.sh --mode=dev"


@pytest.mark.req("DOCS-01")
def test_claude_md_documents_ci_mode():
    """Root CLAUDE.md documents the --mode=ci CI report mode command."""
    content = CLAUDE_MD.read_text()
    assert "--mode=ci" in content, "CLAUDE.md must document run-all-tests.sh --mode=ci"


# ---------------------------------------------------------------------------
# DOCS-02: Spec traceability conventions in root CLAUDE.md
# ---------------------------------------------------------------------------


@pytest.mark.req("DOCS-02")
def test_claude_md_documents_pytest_mark_req():
    """Root CLAUDE.md documents the @pytest.mark.req() traceability marker."""
    content = CLAUDE_MD.read_text()
    assert "@pytest.mark.req" in content, (
        "CLAUDE.md must document @pytest.mark.req() for backend test traceability"
    )


@pytest.mark.req("DOCS-02")
def test_claude_md_documents_spec_comment():
    """Root CLAUDE.md documents the // @spec: REQ-ID traceability comment."""
    content = CLAUDE_MD.read_text()
    assert "// @spec:" in content or "@spec:" in content, (
        "CLAUDE.md must document // @spec: REQ-ID for E2E test traceability"
    )


@pytest.mark.req("DOCS-02")
def test_claude_md_enforces_traceability_before_phase_completion():
    """Root CLAUDE.md states that spec markers are REQUIRED before phase completion."""
    content = CLAUDE_MD.read_text()
    assert "Spec Traceability" in content, (
        "CLAUDE.md must include a Spec Traceability section documenting the requirement"
    )
