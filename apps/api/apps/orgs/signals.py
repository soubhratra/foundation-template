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


def consume_pending_invite_on_signup(sender, request, user, **kwargs):
    """Accept a pending org invite stored in session when a new user signs up.

    When an unauthenticated user follows an invite link, InvitationService
    stores the token in request.session[PENDING_INVITE_SESSION_KEY]. After
    allauth completes signup, this signal pops the token and accepts the
    invitation on the newly-created user's behalf.

    Connected to allauth's user_signed_up signal in OrgsConfig.ready().
    Uses a separate connection call (not @receiver decorator) to avoid importing
    allauth at module load time — allauth is optional in some project setups.
    """
    from apps.orgs.services import PENDING_INVITE_SESSION_KEY, InvitationService

    token = request.session.pop(PENDING_INVITE_SESSION_KEY, None)
    if token:
        try:
            from apps.orgs.models import Invitation

            invitation = Invitation.objects.filter(token=token).first()
            if invitation:
                InvitationService.accept(invitation=invitation, user=user, request=request)
        except Exception:
            # Log but do not crash the signup flow if invite acceptance fails.
            import structlog

            structlog.get_logger(__name__).warning(
                "pending_invite_accept_failed",
                token=token,
                user_id=user.pk,
            )
