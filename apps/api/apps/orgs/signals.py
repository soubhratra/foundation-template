"""Signal receivers for the orgs app.

Wired up via OrgsConfig.ready() in apps.py.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.orgs.models import Organization, OrgCustomer


@receiver(post_save, sender=Organization)
def create_org_customer(
    sender: type, instance: Organization, created: bool, **kwargs: object
) -> None:
    """Auto-create OrgCustomer when Organization is created.

    Mirrors the Customer auto-create signal in apps/billing/signals.py.
    Uses get_or_create to be idempotent in case of retries or duplicate signals.
    """
    if created:
        OrgCustomer.objects.get_or_create(org=instance)
