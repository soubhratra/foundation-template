"""Celery task for sending transactional emails.

send_email_task:
- Renders an HTML template from templates/email/{template_name}
- Extracts the email subject from the first-line <!-- SUBJECT: ... --> sentinel
- Inlines CSS using premailer (allow_network=False for security)
- Sends via EmailMultiAlternatives (HTML + plain-text fallback)
- Retries with exponential backoff on failure (max 3 retries)
- After max retries: CRITICAL log + observability adapter capture
"""

import random
from typing import Any

import structlog
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from premailer import transform

from apps.core.observability import get_observability_adapter

logger = structlog.get_logger(__name__)


def _extract_subject(full_html: str) -> tuple[str, str]:
    """Extract subject from first-line <!-- SUBJECT: ... --> sentinel.

    Each email template starts with an HTML comment on its own line:
        <!-- SUBJECT: Welcome to the app -->
    This function splits out that subject and returns it along with the
    remaining body HTML.

    Args:
        full_html: Full rendered template string.

    Returns:
        Tuple of (subject, body_html) where subject has been stripped from body.
    """
    first_line, _, body = full_html.partition("\n")
    subject = first_line.replace("<!-- SUBJECT:", "").replace("-->", "").strip()
    return subject, body


def _html_to_plain_text(html: str) -> str:
    """Generate a minimal plain-text fallback from HTML.

    Strips all HTML tags for a readable plain-text alternative.
    """
    import re

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    default_retry_delay=2,
)
def send_email_task(
    self: Any,
    to: str,
    template_name: str,
    context: dict,
    from_email: str | None = None,
    reply_to: str | None = None,
) -> None:
    """Render an email template, inline CSS, and send via Django mail backend.

    Args:
        to: Recipient email address.
        template_name: Template filename under templates/email/ (e.g. "welcome.html").
        context: Template context dict — values must be JSON-serializable.
        from_email: Optional sender address; defaults to DEFAULT_FROM_EMAIL.
        reply_to: Optional reply-to address.
    """
    try:
        # Render the HTML template
        rendered_html = render_to_string(f"email/{template_name}", context)

        # Extract subject from first-line sentinel: <!-- SUBJECT: ... -->
        subject, html_body = _extract_subject(rendered_html)

        # Inline CSS using premailer (allow_network=False prevents external requests)
        html_inlined = transform(html_body, allow_network=False)

        # Build the email message.
        # body = HTML with inlined styles (email clients that render .body use this)
        # alternatives = also attach HTML part for clients using MIME multipart
        msg = EmailMultiAlternatives(
            subject=subject,
            body=html_inlined,
            from_email=from_email,
            to=[to],
            reply_to=[reply_to] if reply_to else None,
        )
        msg.attach_alternative(html_inlined, "text/html")
        msg.content_subtype = "html"
        msg.send()

        logger.info("email_sent", to=to, template_name=template_name, subject=subject)

    except Exception as exc:
        retries = self.request.retries
        countdown = (2**retries) + random.uniform(-1, 1)  # noqa: S311

        if retries >= self.max_retries:
            logger.critical(
                "email_dispatch_failed_max_retries",
                to=to,
                template_name=template_name,
                error=str(exc),
                exc_info=True,
            )
            get_observability_adapter().capture_exception(
                exc,
                {
                    "task": "send_email_task",
                    "to": to,
                    "template_name": template_name,
                },
            )
            return

        logger.warning(
            "email_dispatch_retrying",
            to=to,
            template_name=template_name,
            attempt=retries + 1,
            max_retries=self.max_retries,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=countdown) from exc
