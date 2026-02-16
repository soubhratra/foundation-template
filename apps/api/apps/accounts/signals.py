from allauth.account.signals import password_reset
from django.dispatch import receiver

from .services import invalidate_user_sessions, invalidate_user_tokens


@receiver(password_reset)
def invalidate_auth_on_password_reset(sender, request, user, **kwargs):
    """
    Invalidate all authentication for a user after password reset.

    This clears both Django sessions and JWT tokens to ensure that
    any existing authentication (from any device) is invalidated.
    """
    # Invalidate all Django sessions
    invalidate_user_sessions(user_id=user.id)
    # Invalidate all JWT tokens (refresh tokens and track access tokens)
    invalidate_user_tokens(user_id=user.id)
