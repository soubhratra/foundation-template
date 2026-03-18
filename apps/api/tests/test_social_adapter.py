"""SOCIAL-04: Tests for FoundationSocialAccountAdapter relay email auto-connect suppression.

Apple relay addresses (@privaterelay.appleid.com) must NOT be auto-connected to
existing accounts via email matching. Real email addresses (Gmail, etc.) can be
auto-connected as normal.

The adapter under test (apps.accounts.social_adapter) does not yet exist — each
test fails RED with pytest.fail() when the import is attempted inside the test body.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _make_sociallogin_mock(email: str) -> MagicMock:
    """Create a minimal SocialLogin mock with the given email address."""
    sociallogin = MagicMock()
    sociallogin.email_addresses = [MagicMock(email=email)]
    return sociallogin


def _get_adapter():
    """Import FoundationSocialAccountAdapter or fail RED."""
    try:
        from apps.accounts.social_adapter import FoundationSocialAccountAdapter

        return FoundationSocialAccountAdapter
    except ImportError:
        pytest.fail(
            "FoundationSocialAccountAdapter not yet implemented — "
            "create apps/accounts/social_adapter.py with a "
            "FoundationSocialAccountAdapter class that overrides "
            "can_authenticate_by_email() to return False for relay addresses"
        )


class TestRelayEmailAutoConnect:
    """SOCIAL-04: Apple relay addresses bypass email-based account auto-connect."""

    @pytest.mark.req("SOCIAL-01")
    def test_relay_email_not_auto_connected(self) -> None:
        """can_authenticate_by_email returns False for @privaterelay.appleid.com addresses."""
        FoundationSocialAccountAdapter = _get_adapter()
        adapter = FoundationSocialAccountAdapter()
        sociallogin = _make_sociallogin_mock("user@privaterelay.appleid.com")
        result = adapter.can_authenticate_by_email(sociallogin, "user@privaterelay.appleid.com")
        assert result is False, (
            "can_authenticate_by_email must return False for Apple relay addresses "
            "(@privaterelay.appleid.com) — relay addresses don't reliably map to "
            "a real email and should not trigger account merging"
        )

    @pytest.mark.req("SOCIAL-01")
    def test_real_email_can_auto_connect(self) -> None:
        """can_authenticate_by_email returns True for real email addresses."""
        FoundationSocialAccountAdapter = _get_adapter()
        adapter = FoundationSocialAccountAdapter()
        sociallogin = _make_sociallogin_mock("user@gmail.com")
        result = adapter.can_authenticate_by_email(sociallogin, "user@gmail.com")
        assert result is True, (
            "can_authenticate_by_email must return True for real email addresses — "
            "Google and GitHub social logins with matching emails should auto-connect "
            "to existing password accounts"
        )

    @pytest.mark.req("SOCIAL-01")
    def test_another_relay_address_not_auto_connected(self) -> None:
        """Any @privaterelay.appleid.com address is blocked."""
        FoundationSocialAccountAdapter = _get_adapter()
        adapter = FoundationSocialAccountAdapter()
        relay_email = "abc123xyz@privaterelay.appleid.com"
        sociallogin = _make_sociallogin_mock(relay_email)
        result = adapter.can_authenticate_by_email(sociallogin, relay_email)
        assert result is False

    @pytest.mark.req("SOCIAL-01")
    def test_corporate_email_can_auto_connect(self) -> None:
        """Non-relay corporate email addresses can auto-connect."""
        FoundationSocialAccountAdapter = _get_adapter()
        adapter = FoundationSocialAccountAdapter()
        corporate_email = "alice@company.com"
        sociallogin = _make_sociallogin_mock(corporate_email)
        result = adapter.can_authenticate_by_email(sociallogin, corporate_email)
        assert result is True
