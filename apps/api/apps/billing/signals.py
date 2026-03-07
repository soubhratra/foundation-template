from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_for_user(
    sender: type, instance: object, created: bool, **kwargs: object
) -> None:
    """Auto-create a Customer record when a new User is created.

    The `if created:` guard is load-bearing — it prevents a duplicate Customer
    from being created each time an existing User is saved (e.g., profile updates).
    """
    if created:
        from .models import Customer

        Customer.objects.get_or_create(user=instance)
