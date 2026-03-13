from django.apps import AppConfig


class OrgsConfig(AppConfig):
    """Django app config for the orgs B2B module.

    Wires up the post_save signal that auto-creates OrgCustomer
    whenever a new Organization is saved.
    """

    name = "apps.orgs"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        import apps.orgs.signals  # noqa: F401
