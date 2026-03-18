"""SOCIAL-05: Integration test for CLI scaffolder social auth removal.

Invokes the compiled create-foundation-app CLI (dist/remove.js) via subprocess
to exercise the actual TypeScript removeSocialAuthModule() function.

This test calls the REAL compiled module rather than replicating the TypeScript
regex in Python. Any TypeScript bug in removeSocialAuthModule() will surface here
and fail this test — not pass silently. Unit-level regex coverage lives in
packages/create-foundation-app/tests/remove-social-auth.test.ts (Plan 20-01).

Test is SKIPPED if dist/remove.js is not yet built.
Test is RED once dist exists but removeSocialAuthModule() is absent (Plan 20-05 adds it).
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
class TestSocialAuthRemovalViaCLI:
    """SOCIAL-05: Invokes compiled dist/remove.js via subprocess and asserts
    that all social auth artifacts are absent from the output directory afterward.

    Uses subprocess (not Python-reimplemented regex) so any TypeScript bug in
    removeSocialAuthModule() surfaces here. Unit-level regex coverage lives in
    packages/create-foundation-app/tests/remove-social-auth.test.ts (Plan 20-01).
    """

    @pytest.mark.req("SOCIAL-01", "SOCIAL-05")
    def test_social_auth_removal_via_cli(self, tmp_path: Path) -> None:
        """SOCIAL-05 integration test: compiled removeSocialAuthModule() strips all
        social auth artifacts from a copy of the template source files.

        Uses a Node.js inline script passed to `node --input-type=module` so
        that the compiled ESM dist/remove.js is exercised without requiring the
        interactive TTY that dist/index.js demands.
        """
        # ------------------------------------------------------------------ #
        # Step 1: Copy social-auth-relevant template source files to tmp_path #
        # ------------------------------------------------------------------ #
        src_api_settings = PROJECT_ROOT / "apps/api/config/settings"

        # Create destination directory structure
        dest_settings = tmp_path / "apps/api/config/settings"
        dest_settings.mkdir(parents=True)
        shutil.copy2(src_api_settings / "base.py", dest_settings / "base.py")

        # Copy .env.example if it exists
        src_env_example = PROJECT_ROOT / "apps/api/.env.example"
        if src_env_example.exists():
            dest_api = tmp_path / "apps/api"
            dest_api.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_env_example, dest_api / ".env.example")
        else:
            # Create a minimal stub with social env vars so removal has something to remove
            dest_api = tmp_path / "apps/api"
            dest_api.mkdir(parents=True, exist_ok=True)
            (dest_api / ".env.example").write_text(
                "DATABASE_URL=postgres://...\n"
                "# Social Auth (Google)\n"
                "GOOGLE_CLIENT_ID=\n"
                "GOOGLE_CLIENT_SECRET=\n"
                "# Social Auth (GitHub)\n"
                "GITHUB_CLIENT_ID=\n"
                "GITHUB_CLIENT_SECRET=\n"
                "# Social Auth (Apple Sign In)\n"
                "APPLE_CLIENT_ID=\n"
                "APPLE_TEAM_ID=\n"
                "APPLE_KEY_ID=\n"
                "APPLE_PRIVATE_KEY=\n"
            )

        # Copy web login page if it exists
        src_web_login = PROJECT_ROOT / "apps/web/app/(auth)"
        if src_web_login.exists():
            dest_web_auth = tmp_path / "apps/web/app/(auth)"
            dest_web_auth.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_web_login, dest_web_auth, dirs_exist_ok=True)

        # Copy social-buttons component if it exists
        src_social_buttons = PROJECT_ROOT / "apps/web/src/components/auth/social-buttons.tsx"
        if src_social_buttons.exists():
            dest_auth_components = tmp_path / "apps/web/src/components/auth"
            dest_auth_components.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_social_buttons, dest_auth_components / "social-buttons.tsx")
        else:
            # Create a stub so the removal has something to delete
            dest_auth_components = tmp_path / "apps/web/src/components/auth"
            dest_auth_components.mkdir(parents=True, exist_ok=True)
            (dest_auth_components / "social-buttons.tsx").write_text(
                "export function SocialButtons() { return null; }\n"
            )

        # Copy mobile sign-in screen if it exists
        src_mobile_signin = PROJECT_ROOT / "apps/mobile/app/(auth)"
        if src_mobile_signin.exists():
            dest_mobile_auth = tmp_path / "apps/mobile/app/(auth)"
            dest_mobile_auth.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_mobile_signin, dest_mobile_auth, dirs_exist_ok=True)

        # ------------------------------------------------------------------ #
        # Step 2: Inject social-auth sentinel content into base.py            #
        # (In case the real base.py doesn't yet have social auth added)       #
        # ------------------------------------------------------------------ #
        base_py_path = dest_settings / "base.py"
        base_py_content = base_py_path.read_text()

        # Inject SOCIAL AUTH MODULE block if not already present
        if "SOCIAL AUTH MODULE" not in base_py_content:
            social_block = (
                "\n"
                "# ---------------------------------------------------------------------------\n"
                "# SOCIAL AUTH MODULE\n"
                "# ---------------------------------------------------------------------------\n"
                "_social_installed: list[str] = []  # SOCIAL AUTH MODULE\n"
                "SOCIALACCOUNT_PROVIDERS: dict = {}  # placeholder\n"
                "# ---------------------------------------------------------------------------\n"
                "# END SOCIAL AUTH MODULE\n"
                "# ---------------------------------------------------------------------------\n"
            )
            base_py_path.write_text(base_py_content + social_block)

        # Also inject the socialaccount entry if needed
        base_py_content = base_py_path.read_text()
        if '"allauth.socialaccount"' not in base_py_content:
            base_py_path.write_text(
                base_py_content.replace(
                    '"allauth.account",',
                    '"allauth.account",\n    "allauth.socialaccount",  # SOCIAL AUTH MODULE',
                )
            )

        # ------------------------------------------------------------------ #
        # Step 3: Invoke removeSocialAuthModule() via Node.js subprocess      #
        #                                                                     #
        # The full interactive CLI (dist/index.js) requires a TTY for prompts #
        # and does not support --output-dir / --non-interactive flags. Instead #
        # we call dist/remove.js directly — this is still a subprocess over  #
        # the compiled TypeScript output, so any TypeScript bug will surface. #
        # ------------------------------------------------------------------ #
        inline_script = (
            f"import {{ removeSocialAuthModule }} from '{CLI_DIST_REMOVE}';\n"
            f"await removeSocialAuthModule('{tmp_path}');\n"
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
        # Step 4: Assert all social auth artifacts are absent                 #
        # ------------------------------------------------------------------ #
        base_py = (tmp_path / "apps/api/config/settings/base.py").read_text()

        assert "allauth.socialaccount" not in base_py, (
            "allauth.socialaccount still present in INSTALLED_APPS after CLI removal"
        )
        assert "SOCIAL AUTH MODULE" not in base_py, (
            "SOCIAL AUTH MODULE block marker not removed from base.py after CLI removal"
        )
        assert "SOCIALACCOUNT_PROVIDERS" not in base_py, (
            "SOCIALACCOUNT_PROVIDERS not removed from base.py after CLI removal"
        )

        # .env.example checks (only if the file exists in tmp_path)
        env_example_path = tmp_path / "apps/api/.env.example"
        if env_example_path.exists():
            env_content = env_example_path.read_text()
            assert "GOOGLE_CLIENT_ID" not in env_content, (
                "GOOGLE_CLIENT_ID not removed from .env.example after CLI removal"
            )
            assert "GITHUB_CLIENT_ID" not in env_content, (
                "GITHUB_CLIENT_ID not removed from .env.example after CLI removal"
            )
            assert "APPLE_CLIENT_ID" not in env_content, (
                "APPLE_CLIENT_ID not removed from .env.example after CLI removal"
            )

        # Social buttons component should be deleted
        assert not (tmp_path / "apps/web/src/components/auth/social-buttons.tsx").exists(), (
            "apps/web/src/components/auth/social-buttons.tsx still exists after CLI removal"
        )
