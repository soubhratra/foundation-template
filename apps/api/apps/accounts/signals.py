from allauth.account.signals import password_reset
from django.dispatch import receiver

from .services import invalidate_user_sessions


@receiver(password_reset)
def invalidate_auth_on_password_reset(sender, request, user, **kwargs):
    invalidate_user_sessions(user_id=user.id)
