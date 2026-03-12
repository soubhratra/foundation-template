"""SOCIAL-01 + SOCIAL-02: Tests for _configure_social_providers conditional registration.

These tests call _configure_social_providers(env_dict) directly (pure function).
The function does not yet exist — each test fails RED with pytest.fail() on the
import attempt within the test body.
"""

import pytest


def _get_configure_social_providers():
    """Import _configure_social_providers or fail RED."""
    try:
        from config.settings.base import _configure_social_providers

        return _configure_social_providers
    except ImportError:
        pytest.fail(
            "_configure_social_providers not yet implemented in base.py — "
            "implement it as a pure function that accepts an env dict and returns "
            "a dict with keys: extra_installed_apps (list), providers (dict), "
            "auto_connect (bool)"
        )


class TestGoogleProviderRegistration:
    """SOCIAL-01: Google OAuth conditional registration."""

    def test_google_provider_registered(self) -> None:
        """Google provider added when credentials present."""
        _configure_social_providers = _get_configure_social_providers()
        result = _configure_social_providers(
            {
                "GOOGLE_CLIENT_ID": "test-google-id",  # pragma: allowlist secret
                "GOOGLE_CLIENT_SECRET": "test-google-secret",  # pragma: allowlist secret
            }
        )
        assert "allauth.socialaccount.providers.google" in result["extra_installed_apps"], (
            "Expected allauth.socialaccount.providers.google in extra_installed_apps"
        )
        assert "google" in result["providers"], "Expected 'google' key in providers dict"

    def test_github_provider_registered(self) -> None:
        """GitHub provider added when credentials present."""
        _configure_social_providers = _get_configure_social_providers()
        result = _configure_social_providers(
            {
                "GITHUB_CLIENT_ID": "test-github-id",  # pragma: allowlist secret
                "GITHUB_CLIENT_SECRET": "test-github-secret",  # pragma: allowlist secret
            }
        )
        assert "allauth.socialaccount.providers.github" in result["extra_installed_apps"], (
            "Expected allauth.socialaccount.providers.github in extra_installed_apps"
        )
        assert "github" in result["providers"], "Expected 'github' key in providers dict"

    def test_google_provider_absent_without_credentials(self) -> None:
        """Google provider NOT added when credentials are absent."""
        _configure_social_providers = _get_configure_social_providers()
        result = _configure_social_providers({})
        assert "allauth.socialaccount.providers.google" not in result["extra_installed_apps"], (
            "allauth.socialaccount.providers.google should NOT be in extra_installed_apps "
            "when GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are absent"
        )

    def test_google_provider_absent_when_only_client_id_set(self) -> None:
        """Google provider NOT added when only one credential is present."""
        _configure_social_providers = _get_configure_social_providers()
        result = _configure_social_providers(
            {"GOOGLE_CLIENT_ID": "test-id"}  # pragma: allowlist secret
        )
        assert "allauth.socialaccount.providers.google" not in result["extra_installed_apps"]

    def test_github_provider_absent_without_credentials(self) -> None:
        """GitHub provider NOT added when credentials are absent."""
        _configure_social_providers = _get_configure_social_providers()
        result = _configure_social_providers({})
        assert "allauth.socialaccount.providers.github" not in result["extra_installed_apps"]


class TestAppleProviderRegistration:
    """SOCIAL-01 + SOCIAL-03: Apple Sign In conditional registration and settings."""

    def test_apple_settings_hidden(self) -> None:
        """Apple APPS[0].settings.hidden == True to suppress Apple button on web UI."""
        _configure_social_providers = _get_configure_social_providers()
        result = _configure_social_providers(
            {
                "APPLE_CLIENT_ID": "test",
                "APPLE_TEAM_ID": "T",
                "APPLE_KEY_ID": "K",
                "APPLE_PRIVATE_KEY": "",
            }
        )
        apple_provider = result["providers"].get("apple", {})
        apps = apple_provider.get("APPS", [])
        assert len(apps) > 0, "Apple provider APPS list should not be empty"
        assert apps[0].get("settings", {}).get("hidden") is True, (
            "Apple provider APPS[0].settings.hidden must be True to hide the button on web"
        )

    def test_apple_provider_registered_with_credentials(self) -> None:
        """Apple provider added when all Apple credentials are present."""
        _configure_social_providers = _get_configure_social_providers()
        # fmt: off
        fake_pem = "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"  # pragma: allowlist secret  # noqa: E501
        # fmt: on
        result = _configure_social_providers(
            {
                "APPLE_CLIENT_ID": "com.example.app",
                "APPLE_TEAM_ID": "ABCDE12345",
                "APPLE_KEY_ID": "KEYID12345",
                "APPLE_PRIVATE_KEY": fake_pem,
            }
        )
        assert "allauth.socialaccount.providers.apple" in result["extra_installed_apps"], (
            "Expected allauth.socialaccount.providers.apple in extra_installed_apps"
        )
        assert "apple" in result["providers"]


class TestSocialAccountAutoConnect:
    """SOCIAL-02: Email auto-merge settings."""

    def test_socialaccount_auto_connect_enabled(self) -> None:
        """auto_connect == True so Google/GitHub accounts merge with existing accounts."""
        _configure_social_providers = _get_configure_social_providers()
        result = _configure_social_providers({})
        assert result.get("auto_connect") is True, (
            "auto_connect must be True — SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT "
            "should be enabled for Google and GitHub"
        )

    def test_both_providers_registered_simultaneously(self) -> None:
        """Both Google and GitHub can be registered at the same time."""
        _configure_social_providers = _get_configure_social_providers()
        result = _configure_social_providers(
            {
                "GOOGLE_CLIENT_ID": "test-google-id",  # pragma: allowlist secret
                "GOOGLE_CLIENT_SECRET": "test-google-secret",  # pragma: allowlist secret
                "GITHUB_CLIENT_ID": "test-github-id",  # pragma: allowlist secret
                "GITHUB_CLIENT_SECRET": "test-github-secret",  # pragma: allowlist secret
            }
        )
        assert "allauth.socialaccount.providers.google" in result["extra_installed_apps"]
        assert "allauth.socialaccount.providers.github" in result["extra_installed_apps"]
        assert "google" in result["providers"]
        assert "github" in result["providers"]
