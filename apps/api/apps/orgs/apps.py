from django.apps import AppConfig


class OrgsConfig(AppConfig):
    """Django app config for the orgs B2B module.

    Wires up the post_save signal that auto-creates OrgCustomer
    whenever a new Organization is saved.
    """

    name = "apps.orgs"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        # Wire up user_signed_up signal for session-based invite consumption.
        # Import here (not at module level) to avoid importing allauth before
        # Django's app registry is ready.
        from allauth.account.signals import user_signed_up

        import apps.orgs.signals  # noqa: F401
        from apps.orgs.signals import consume_pending_invite_on_signup

        user_signed_up.connect(consume_pending_invite_on_signup)
