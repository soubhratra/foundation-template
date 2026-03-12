"""
Custom SocialAccountAdapter for Foundation Template.

Overrides can_authenticate_by_email to prevent Apple relay addresses
(@privaterelay.appleid.com) from triggering SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT.
Relay addresses do not confirm identity ownership — they are Apple-issued forwarding
addresses that should never be silently linked to an existing password account.
"""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

APPLE_RELAY_DOMAIN = "privaterelay.appleid.com"


class FoundationSocialAccountAdapter(DefaultSocialAccountAdapter):
    def can_authenticate_by_email(self, login, email: str) -> bool:
        """
        Block email-based auto-connect for Apple relay addresses.
        All other emails delegate to the default logic (respects
        SOCIALACCOUNT_EMAIL_AUTHENTICATION and per-provider EMAIL_AUTHENTICATION).
        """
        if email and email.endswith(f"@{APPLE_RELAY_DOMAIN}"):
            return False
        return bool(super().can_authenticate_by_email(login, email))
