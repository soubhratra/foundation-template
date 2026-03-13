from django.apps import AppConfig


class WebhooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.webhooks"
    label = "webhooks"

    def ready(self) -> None:
        import apps.webhooks.checks  # noqa: F401
