"""EMAIL-03: Test stub for CSS inlining in send_email_task.

These tests are RED until Plan 19-03 delivers the notifications app.

EMAIL-03: Emails rendered from HTML templates must have CSS inlined as
          style="" attributes. No <style> blocks should remain in the output.
"""

from django.test import override_settings

# This import will raise ImportError until Plan 19-03 creates the module.
from apps.notifications.tasks import send_email_task


class TestCssIsInlined:
    """EMAIL-03: send_email_task must produce emails with inlined CSS."""

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_css_is_inlined(self, tmp_path) -> None:
        """Rendered email body must contain style="" attributes, no <style> block.

        The task renders an HTML template that includes a <style> block.
        After CSS inlining (via premailer or equivalent), the output must:
          - Contain at least one style="" attribute
          - Not contain any <style> element

        The Celery task is exercised via its underlying implementation function
        (send_email_task.run() or _send_email_impl()) to bypass the broker.
        """
        import django.core.mail

        # Clear the outbox before the test
        django.core.mail.outbox = []

        # Call the task function directly (bypassing Celery broker)
        # The task should expose a .run() method or the underlying function
        # should be callable via send_email_task.run(...)
        send_email_task.run(
            to="css-test@example.com",
            template_name="notifications/welcome.html",
            context={"name": "CSS Test"},
        )

        assert len(django.core.mail.outbox) == 1, (
            "Expected exactly one email in the outbox after calling send_email_task.run()"
        )

        email = django.core.mail.outbox[0]
        # The email body should be HTML with inlined styles
        body = email.body if hasattr(email, "body") else ""

        # Check for inlined styles — at least one style attribute present
        assert 'style="' in body, (
            "Email body must contain inlined style= attributes after CSS inlining. "
            f"Got body: {body[:500]}"
        )

        # Check that no <style> block remains in the body
        assert "<style>" not in body, (
            "Email body must NOT contain a <style> block after CSS inlining. "
            f"Got body: {body[:500]}"
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_plain_text_alternative_present(self) -> None:
        """Rendered email must include a plain-text alternative part.

        Proper transactional emails include both HTML and plain-text parts
        for email clients that do not render HTML.
        """
        import django.core.mail

        django.core.mail.outbox = []

        send_email_task.run(
            to="plaintext-test@example.com",
            template_name="notifications/welcome.html",
            context={"name": "Plain Text Test"},
        )

        assert len(django.core.mail.outbox) == 1, "Expected exactly one email in the outbox"

        email = django.core.mail.outbox[0]
        # EmailMultiAlternatives stores alternatives as list of (content, mimetype)
        alternatives = getattr(email, "alternatives", [])
        html_alternatives = [alt for alt in alternatives if alt[1] == "text/html"]
        assert html_alternatives, (
            "Email must have an HTML alternative attached via EmailMultiAlternatives"
        )
