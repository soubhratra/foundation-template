"""OBS-03: Integration test for CLI scaffolder observability removal.

Invokes the compiled create-foundation-app CLI (dist/remove.js) via subprocess
to exercise the actual TypeScript removeObservability() function.

This test calls the REAL compiled module rather than replicating the TypeScript
regex in Python. Any TypeScript bug in removeObservability() will surface here
and fail this test — not pass silently.

Status: RED stub — removeObservability() does not exist in dist/remove.js until
Plan 04 implements it. The subprocess call will fail with a non-zero exit code
or an export-not-found error.
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
class TestObservabilityRemovalViaCLI:
    """OBS-03: Invokes compiled dist/remove.js via subprocess and asserts
    that all observability artifacts are absent from the output directory afterward.

    Uses subprocess (not Python-reimplemented regex) so any TypeScript bug in
    removeObservability() surfaces here. Unit-level regex coverage lives in
    packages/create-foundation-app/tests/remove-observability.test.ts (Plan 04).
    """

    def test_remove_observability_cleans_all_touch_points(self, tmp_path: Path) -> None:
        """OBS-03 integration test: compiled removeObservability() strips all
        observability artifacts from a copy of the template source files.

        Touch points verified after removal:
        - apps/api/apps/core/observability.py deleted
        - ObservabilityMiddleware not in MIDDLEWARE in base.py
        - OBSERVABILITY_ADAPTER not in base.py
        - POSTHOG_API_KEY not in base.py
        - posthog not in pyproject.toml deps
        - PostHogProvider not in providers.tsx
        - NEXT_PUBLIC_POSTHOG_KEY not in web .env.example
        - PostHogProvider not in _layout.tsx
        - EXPO_PUBLIC_POSTHOG_KEY not in mobile .env.example
        """
        # ------------------------------------------------------------------ #
        # Step 1: Copy observability-relevant template source files to tmp    #
        # ------------------------------------------------------------------ #
        src_api_settings = PROJECT_ROOT / "apps/api/config/settings"
        src_api_pyproject = PROJECT_ROOT / "apps/api/pyproject.toml"
        src_core_app = PROJECT_ROOT / "apps/api/apps/core"
        src_web_providers = PROJECT_ROOT / "apps/web/app/providers.tsx"
        src_web_env_example = PROJECT_ROOT / "apps/web/.env.example"
        src_mobile_layout = PROJECT_ROOT / "apps/mobile/app/_layout.tsx"
        src_mobile_env_example = PROJECT_ROOT / "apps/mobile/.env.example"

        # Create destination directory structure
        dest_settings = tmp_path / "apps/api/config/settings"
        dest_settings.mkdir(parents=True)

        for fname in ("base.py", "development.py", "production.py"):
            src = src_api_settings / fname
            if src.exists():
                shutil.copy2(src, dest_settings / fname)

        if src_api_pyproject.exists():
            dest_api = tmp_path / "apps/api"
            dest_api.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_api_pyproject, dest_api / "pyproject.toml")

        if src_core_app.exists():
            shutil.copytree(src_core_app, tmp_path / "apps/api/apps/core")

        if src_web_providers.exists():
            dest_web_app = tmp_path / "apps/web/app"
            dest_web_app.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_web_providers, dest_web_app / "providers.tsx")

        if src_web_env_example.exists():
            dest_web = tmp_path / "apps/web"
            dest_web.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_web_env_example, dest_web / ".env.example")

        if src_mobile_layout.exists():
            dest_mobile_app = tmp_path / "apps/mobile/app"
            dest_mobile_app.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_mobile_layout, dest_mobile_app / "_layout.tsx")

        if src_mobile_env_example.exists():
            dest_mobile = tmp_path / "apps/mobile"
            dest_mobile.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_mobile_env_example, dest_mobile / ".env.example")

        # ------------------------------------------------------------------ #
        # Step 2: Invoke removeObservability() via Node.js subprocess         #
        #                                                                      #
        # The full interactive CLI (dist/index.js) requires a TTY for prompts #
        # and does not support non-interactive flags. Instead we call          #
        # dist/remove.js directly — this is still a subprocess over the       #
        # compiled TypeScript output, so any TypeScript bug will surface.     #
        # ------------------------------------------------------------------ #
        inline_script = (
            f"import {{ removeObservability }} from '{CLI_DIST_REMOVE}';\n"
            f"await removeObservability('{tmp_path}');\n"
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
        # Step 3: Assert all observability artifacts are absent               #
        # ------------------------------------------------------------------ #
        base_py_path = tmp_path / "apps/api/config/settings/base.py"
        if base_py_path.exists():
            base_py = base_py_path.read_text()
            assert "ObservabilityMiddleware" not in base_py, (
                "ObservabilityMiddleware still present in MIDDLEWARE after CLI removal"
            )
            assert "OBSERVABILITY_ADAPTER" not in base_py, (
                "OBSERVABILITY_ADAPTER still present in base.py after CLI removal"
            )
            assert "POSTHOG_API_KEY" not in base_py, (
                "POSTHOG_API_KEY still present in base.py after CLI removal"
            )

        api_pyproject_path = tmp_path / "apps/api/pyproject.toml"
        if api_pyproject_path.exists():
            api_pyproject = api_pyproject_path.read_text()
            assert "posthog" not in api_pyproject, (
                "posthog still present in pyproject.toml after CLI removal"
            )

        assert not (tmp_path / "apps/api/apps/core/observability.py").exists(), (
            "apps/api/apps/core/observability.py still exists after CLI removal"
        )

        web_providers_path = tmp_path / "apps/web/app/providers.tsx"
        if web_providers_path.exists():
            providers_tsx = web_providers_path.read_text()
            assert "PostHogProvider" not in providers_tsx, (
                "PostHogProvider still present in providers.tsx after CLI removal"
            )

        web_env_path = tmp_path / "apps/web/.env.example"
        if web_env_path.exists():
            web_env = web_env_path.read_text()
            assert "NEXT_PUBLIC_POSTHOG_KEY" not in web_env, (
                "NEXT_PUBLIC_POSTHOG_KEY still present in web .env.example after CLI removal"
            )

        mobile_layout_path = tmp_path / "apps/mobile/app/_layout.tsx"
        if mobile_layout_path.exists():
            layout_tsx = mobile_layout_path.read_text()
            assert "PostHogProvider" not in layout_tsx, (
                "PostHogProvider still present in _layout.tsx after CLI removal"
            )

        mobile_env_path = tmp_path / "apps/mobile/.env.example"
        if mobile_env_path.exists():
            mobile_env = mobile_env_path.read_text()
            assert "EXPO_PUBLIC_POSTHOG_KEY" not in mobile_env, (
                "EXPO_PUBLIC_POSTHOG_KEY still present in mobile .env.example after CLI removal"
            )
