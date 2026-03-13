"""SCAFF-01: Integration test for CLI scaffolder B2B removal.

Invokes the compiled create-foundation-app CLI (dist/remove.js) via subprocess
to exercise the actual TypeScript removeB2BModule() function.

Two tests:
- test_scaffold_without_b2b: applies removeB2BModule(), asserts all four negative
  conditions (no markers, no B2B apps in INSTALLED_APPS, no B2B dirs, no B2B deps).
- test_scaffold_with_b2b: runs manage.py check on the real template source to
  verify the full B2B stack is correctly installed and configured.

This test will be RED initially: removeB2BModule() is not yet exported from
dist/remove.js (Plan 02 implements it). The skipif guard fires when CLI is not
built; once built, test_scaffold_without_b2b will fail until Plan 02 ships.
"""

import glob
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = (
    Path(__file__).resolve().parents[4]
)  # tests/scaffolder/ → tests/ → api/ → apps/ → foundation-template/
CLI_DIST_REMOVE = PROJECT_ROOT / "packages/create-foundation-app/dist/remove.js"


@pytest.mark.skipif(
    not CLI_DIST_REMOVE.exists(),
    reason="CLI not built — run: cd packages/create-foundation-app && pnpm build",
)
class TestB2BScaffoldViaCLI:
    """SCAFF-01: Invokes compiled dist/remove.js via subprocess and asserts
    that all B2B artifacts are absent from the output directory afterward.

    Uses subprocess (not Python-reimplemented logic) so any TypeScript bug in
    removeB2BModule() surfaces here. Plan 02 implements removeB2BModule().
    """

    def test_scaffold_without_b2b(self, tmp_path: Path) -> None:
        """SCAFF-01: compiled removeB2BModule() strips all B2B artifacts from
        a copy of the relevant template source files.

        Asserts:
        1. No # B2B_START or # B2B_END markers remain in any .py file
        2. apps.orgs, apps.webhooks, apps.api_keys, apps.audit absent from base.py
        3. B2B directories (orgs/, api_keys/, webhooks/, audit/) do not exist
        4. django-pghistory and django-hijack absent from pyproject.toml
        """
        # ------------------------------------------------------------------ #
        # Step 1: Copy B2B-relevant template source files to tmp_path          #
        # ------------------------------------------------------------------ #
        src_settings = PROJECT_ROOT / "apps/api/config/settings"
        src_urls = PROJECT_ROOT / "apps/api/config/urls.py"
        src_apps = PROJECT_ROOT / "apps/api/apps"
        src_pyproject = PROJECT_ROOT / "apps/api/pyproject.toml"

        # settings/base.py and settings/development.py
        dest_settings = tmp_path / "apps/api/config/settings"
        dest_settings.mkdir(parents=True)
        shutil.copy2(src_settings / "base.py", dest_settings / "base.py")
        shutil.copy2(src_settings / "development.py", dest_settings / "development.py")

        # config/urls.py
        dest_config = tmp_path / "apps/api/config"
        shutil.copy2(src_urls, dest_config / "urls.py")

        # B2B app directories
        for b2b_dir in ("orgs", "api_keys", "webhooks", "audit"):
            src_dir = src_apps / b2b_dir
            if src_dir.exists():
                shutil.copytree(src_dir, tmp_path / f"apps/api/apps/{b2b_dir}")

        # accounts/permissions.py (has B2B_START block for hijack permission)
        src_permissions = src_apps / "accounts/permissions.py"
        if src_permissions.exists():
            dest_accounts = tmp_path / "apps/api/apps/accounts"
            dest_accounts.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_permissions, dest_accounts / "permissions.py")

        # billing/tasks.py (has B2B_START blocks for org-billing integration)
        src_billing_tasks = src_apps / "billing/tasks.py"
        if src_billing_tasks.exists():
            dest_billing = tmp_path / "apps/api/apps/billing"
            dest_billing.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_billing_tasks, dest_billing / "tasks.py")

        # pyproject.toml
        shutil.copy2(src_pyproject, tmp_path / "apps/api/pyproject.toml")

        # ------------------------------------------------------------------ #
        # Step 2: Invoke removeB2BModule() via Node.js subprocess              #
        # ------------------------------------------------------------------ #
        inline_script = (
            f"import {{ removeB2BModule }} from '{CLI_DIST_REMOVE}';\n"
            f"await removeB2BModule('{tmp_path}');\n"
        )

        result = subprocess.run(
            ["node", "--input-type=module"],
            input=inline_script,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(PROJECT_ROOT / "packages/create-foundation-app"),
        )

        assert result.returncode == 0, (
            f"Node subprocess exited with code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # ------------------------------------------------------------------ #
        # Step 3: Assert all B2B artifacts are absent                          #
        # ------------------------------------------------------------------ #

        # Assertion 1: No # B2B_START or # B2B_END markers remain in any .py file
        all_py_files = glob.glob(str(tmp_path / "**/*.py"), recursive=True)
        for py_file in all_py_files:
            content = Path(py_file).read_text()
            assert "# B2B_START" not in content, (
                f"# B2B_START marker still present in {py_file} after B2B removal"
            )
            assert "# B2B_END" not in content, (
                f"# B2B_END marker still present in {py_file} after B2B removal"
            )

        # Assertion 2: B2B app names absent from base.py INSTALLED_APPS
        base_py_content = (tmp_path / "apps/api/config/settings/base.py").read_text()
        assert "apps.orgs" not in base_py_content, (
            "apps.orgs still present in base.py after B2B removal"
        )
        assert "apps.webhooks" not in base_py_content, (
            "apps.webhooks still present in base.py after B2B removal"
        )
        assert "apps.api_keys" not in base_py_content, (
            "apps.api_keys still present in base.py after B2B removal"
        )
        assert "apps.audit" not in base_py_content, (
            "apps.audit still present in base.py after B2B removal"
        )

        # Assertion 3: B2B directories do not exist
        assert not (tmp_path / "apps/api/apps/orgs").exists(), (
            "apps/api/apps/orgs directory still exists after B2B removal"
        )
        assert not (tmp_path / "apps/api/apps/api_keys").exists(), (
            "apps/api/apps/api_keys directory still exists after B2B removal"
        )
        assert not (tmp_path / "apps/api/apps/webhooks").exists(), (
            "apps/api/apps/webhooks directory still exists after B2B removal"
        )
        assert not (tmp_path / "apps/api/apps/audit").exists(), (
            "apps/api/apps/audit directory still exists after B2B removal"
        )

        # Assertion 4: B2B pyproject.toml deps absent
        pyproject_content = (tmp_path / "apps/api/pyproject.toml").read_text()
        assert "django-pghistory" not in pyproject_content, (
            "django-pghistory still present in pyproject.toml after B2B removal"
        )
        assert "django-hijack" not in pyproject_content, (
            "django-hijack still present in pyproject.toml after B2B removal"
        )

    def test_scaffold_with_b2b(self, tmp_path: Path) -> None:
        """SCAFF-01: Full B2B stack passes Django system checks.

        Runs manage.py check on the REAL template source (not a copy) to verify
        that all B2B apps, middleware, and settings are correctly configured.
        The test environment has all B2B deps installed (they are in pyproject.toml).

        NOTE: runs against real source (not tmp_path) because manage.py check
        requires the full Django project tree including migrations, templates, etc.
        """
        result = subprocess.run(
            [
                sys.executable,
                "manage.py",
                "check",
                "--settings=config.settings.development",
            ],
            cwd=str(PROJECT_ROOT / "apps/api"),
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, (
            f"manage.py check failed on full B2B template source\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
