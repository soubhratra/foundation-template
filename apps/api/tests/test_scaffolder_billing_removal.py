"""SCAFF-04: Integration test for CLI scaffolder billing removal.

Invokes the compiled create-foundation-app CLI (dist/remove.js) via subprocess
to exercise the actual TypeScript removeBillingModule() function.

This test calls the REAL compiled module rather than replicating the TypeScript
regex in Python. Any TypeScript bug in removeBillingModule() will surface here
and fail this test — not pass silently. Unit-level regex coverage lives in
packages/create-foundation-app/tests/remove-billing.test.ts (Plan 12-02).
"""

import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # workspace/foundation-template/
CLI_DIST_REMOVE = PROJECT_ROOT / "packages/create-foundation-app/dist/remove.js"


@pytest.mark.skipif(
    not CLI_DIST_REMOVE.exists(),
    reason=("CLI not built — run: cd packages/create-foundation-app && pnpm build"),
)
class TestBillingRemovalViaCLI:
    """SCAFF-04: Invokes compiled dist/remove.js via subprocess and asserts
    that all billing artifacts are absent from the output directory afterward.

    Uses subprocess (not Python-reimplemented regex) so any TypeScript bug in
    removeBillingModule() surfaces here. Unit-level regex coverage lives in
    packages/create-foundation-app/tests/remove-billing.test.ts (Plan 12-02).
    """

    def test_billing_removal_via_cli(self, tmp_path: Path) -> None:
        """SCAFF-04 integration test: compiled removeBillingModule() strips all
        billing artifacts from a copy of the template source files.

        Uses a Node.js inline script passed to `node --input-type=module` so
        that the compiled ESM dist/remove.js is exercised without requiring the
        interactive TTY that dist/index.js demands.
        """
        # ------------------------------------------------------------------ #
        # Step 1: Copy billing-relevant template source files to tmp_path      #
        # ------------------------------------------------------------------ #
        src_api_settings = PROJECT_ROOT / "apps/api/config/settings"
        src_urls = PROJECT_ROOT / "apps/api/config/urls.py"
        src_billing_app = PROJECT_ROOT / "apps/api/apps/billing"
        src_web_billing = PROJECT_ROOT / "apps/web/app/(dashboard)/billing"
        src_billing_config = PROJECT_ROOT / "apps/web/billing.config.ts"

        # Create destination directory structure
        dest_settings = tmp_path / "apps/api/config/settings"
        dest_settings.mkdir(parents=True)
        shutil.copy2(src_api_settings / "base.py", dest_settings / "base.py")
        shutil.copy2(src_api_settings / "development.py", dest_settings / "development.py")

        dest_config = tmp_path / "apps/api/config"
        shutil.copy2(src_urls, dest_config / "urls.py")

        if src_billing_app.exists():
            shutil.copytree(src_billing_app, tmp_path / "apps/api/apps/billing")

        if src_web_billing.exists():
            dest_web_billing = tmp_path / "apps/web/app/(dashboard)/billing"
            dest_web_billing.mkdir(parents=True)
            shutil.copytree(src_web_billing, dest_web_billing, dirs_exist_ok=True)

        if src_billing_config.exists():
            dest_web = tmp_path / "apps/web"
            dest_web.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_billing_config, dest_web / "billing.config.ts")

        # ------------------------------------------------------------------ #
        # Step 2: Invoke removeBillingModule() via Node.js subprocess          #
        #                                                                      #
        # The full interactive CLI (dist/index.js) requires a TTY for prompts #
        # and does not support --output-dir / --non-interactive flags. Instead #
        # we call dist/remove.js directly — this is still a subprocess over   #
        # the compiled TypeScript output, so any TypeScript bug will surface.  #
        # ------------------------------------------------------------------ #
        inline_script = (
            f"import {{ removeBillingModule }} from '{CLI_DIST_REMOVE}';\n"
            f"await removeBillingModule('{tmp_path}');\n"
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
        # Step 3: Assert all billing artifacts are absent                      #
        # ------------------------------------------------------------------ #
        base_py = (tmp_path / "apps/api/config/settings/base.py").read_text()
        dev_py = (tmp_path / "apps/api/config/settings/development.py").read_text()
        urls_py = (tmp_path / "apps/api/config/urls.py").read_text()

        assert "apps.billing" not in base_py, (
            "apps.billing still present in INSTALLED_APPS after CLI removal"
        )
        assert "BILLING MODULE" not in base_py, (
            "BILLING MODULE block not removed from base.py after CLI removal"
        )
        assert "BILLING_ADAPTER" not in dev_py, (
            "BILLING_ADAPTER line not removed from development.py after CLI removal"
        )
        assert "from apps.billing" not in urls_py, (
            "billing import not removed from urls.py after CLI removal"
        )
        assert "BILLING_START" not in urls_py, (
            "BILLING_START marker not removed from urls.py after CLI removal"
        )
        assert not (tmp_path / "apps/api/apps/billing").exists(), (
            "apps/api/apps/billing directory still exists after CLI removal"
        )
        assert not (tmp_path / "apps/web/billing.config.ts").exists(), (
            "apps/web/billing.config.ts still exists after CLI removal"
        )
