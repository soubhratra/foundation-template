"""EMAIL-05: Integration test for CLI scaffolder email removal.

Invokes the compiled create-foundation-app CLI (dist/remove.js) via subprocess
to exercise the actual TypeScript removeEmailModule() function.

This test calls the REAL compiled module rather than replicating the TypeScript
regex in Python. Any TypeScript bug in removeEmailModule() will surface here
and fail this test — not pass silently. Unit-level regex coverage lives in
packages/create-foundation-app/tests/remove-email.test.ts (Plan 19-04).

Test is SKIPPED if dist/remove.js is not yet built.
Test is RED once dist exists but removeEmailModule() is absent (Plan 19-04 adds it).
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
class TestEmailRemovalViaCLI:
    """EMAIL-05: Invokes compiled dist/remove.js via subprocess and asserts
    that all email artifacts are absent from the output directory afterward.

    Uses subprocess (not Python-reimplemented regex) so any TypeScript bug in
    removeEmailModule() surfaces here. Unit-level regex coverage lives in
    packages/create-foundation-app/tests/remove-email.test.ts (Plan 19-04).
    """

    def test_email_removal_via_cli(self, tmp_path: Path) -> None:
        """EMAIL-05 integration test: compiled removeEmailModule() strips all
        email artifacts from a copy of the template source files.

        Uses a Node.js inline script passed to `node --input-type=module` so
        that the compiled ESM dist/remove.js is exercised without requiring the
        interactive TTY that dist/index.js demands.
        """
        # ------------------------------------------------------------------ #
        # Step 1: Copy email-relevant template source files to tmp_path       #
        # ------------------------------------------------------------------ #
        src_api_settings = PROJECT_ROOT / "apps/api/config/settings"
        src_notifications_app = PROJECT_ROOT / "apps/api/apps/notifications"

        # Create destination directory structure
        dest_settings = tmp_path / "apps/api/config/settings"
        dest_settings.mkdir(parents=True)
        shutil.copy2(src_api_settings / "base.py", dest_settings / "base.py")
        shutil.copy2(src_api_settings / "development.py", dest_settings / "development.py")

        # Copy the notifications app if it exists (will exist after Plan 19-03)
        if src_notifications_app.exists():
            shutil.copytree(
                src_notifications_app,
                tmp_path / "apps/api/apps/notifications",
            )
        else:
            # Create a minimal stub so removal logic has something to remove
            stub_notifications = tmp_path / "apps/api/apps/notifications"
            stub_notifications.mkdir(parents=True)
            (stub_notifications / "__init__.py").write_text("")
            (stub_notifications / "apps.py").write_text(
                "from django.apps import AppConfig\n\n\n"
                "class NotificationsConfig(AppConfig):\n"
                "    default_auto_field = 'django.db.models.BigAutoField'\n"
                "    name = 'apps.notifications'\n"
            )

        # ------------------------------------------------------------------ #
        # Step 2: Invoke removeEmailModule() via Node.js subprocess           #
        #                                                                     #
        # The full interactive CLI (dist/index.js) requires a TTY for prompts #
        # and does not support --output-dir / --non-interactive flags. Instead #
        # we call dist/remove.js directly — this is still a subprocess over  #
        # the compiled TypeScript output, so any TypeScript bug will surface. #
        # ------------------------------------------------------------------ #
        inline_script = (
            f"import {{ removeEmailModule }} from '{CLI_DIST_REMOVE}';\n"
            f"await removeEmailModule('{tmp_path}');\n"
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
        # Step 3: Assert all email artifacts are absent                       #
        # ------------------------------------------------------------------ #
        base_py = (tmp_path / "apps/api/config/settings/base.py").read_text()

        assert "apps.notifications" not in base_py, (
            "apps.notifications still present in INSTALLED_APPS after CLI removal"
        )
        assert "anymail" not in base_py, "anymail line not removed from base.py after CLI removal"
        assert "RESEND_API_KEY" not in base_py, (
            "RESEND_API_KEY setting not removed from base.py after CLI removal"
        )
        assert "EMAIL MODULE" not in base_py, (
            "EMAIL MODULE block marker not removed from base.py after CLI removal"
        )
        assert not (tmp_path / "apps/api/apps/notifications").exists(), (
            "apps/api/apps/notifications directory still exists after CLI removal"
        )
