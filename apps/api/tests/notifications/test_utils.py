"""EMAIL-01 / EMAIL-02: Test stubs for apps.notifications.utils.send_email.

These tests are RED until Plan 19-03 delivers the notifications app.

EMAIL-01: send_email() enqueues a Celery task (not blocking the request).
EMAIL-02: send_email() called inside a rolled-back transaction does NOT
          enqueue the task (on_commit protection).
"""

from unittest.mock import patch

import pytest
from django.db import transaction

# This import will raise ImportError until Plan 19-03 creates the module.
from apps.notifications.utils import send_email


class TestSendEmailQueuesTask:
    """EMAIL-01: send_email() must enqueue send_email_task.delay()."""

    @pytest.mark.req("EMAIL-01")
    def test_send_email_queues_task(self) -> None:
        """Calling send_email() should enqueue send_email_task via .delay().

        The underlying Celery task is patched at its dotted path to avoid
        needing a real Celery broker in CI.
        """
        with patch("apps.notifications.tasks.send_email_task.delay") as mock_delay:
            send_email(
                to="test@example.com",
                template_name="welcome.html",
                context={"name": "Test"},
            )

            mock_delay.assert_called_once()
            call_kwargs = mock_delay.call_args.kwargs
            assert call_kwargs.get("to") == "test@example.com", (
                "send_email_task.delay must be called with to='test@example.com'"
            )
            assert call_kwargs.get("template_name") == "welcome.html", (
                "send_email_task.delay must be called with template_name='welcome.html'"
            )

    @pytest.mark.req("EMAIL-01")
    def test_send_email_with_optional_params(self) -> None:
        """send_email() should forward optional from_email and reply_to kwargs."""
        with patch("apps.notifications.tasks.send_email_task.delay") as mock_delay:
            send_email(
                to="recipient@example.com",
                template_name="notification.html",
                context={"key": "value"},
                from_email="no-reply@example.com",
                reply_to="support@example.com",
            )

            mock_delay.assert_called_once()


class TestSendEmailOnCommitRollback:
    """EMAIL-02: send_email() inside a rolled-back transaction must NOT enqueue."""

    @pytest.mark.req("EMAIL-01")
    @pytest.mark.django_db(transaction=True)
    def test_send_email_on_commit_rollback(self) -> None:
        """Task must NOT be enqueued when the wrapping transaction rolls back.

        Django's on_commit() hooks only fire after a successful COMMIT.
        Rolling back the transaction should prevent any task enqueue.
        """
        with patch("apps.notifications.tasks.send_email_task.delay") as mock_delay:
            try:
                with transaction.atomic():
                    send_email(
                        to="test@example.com",
                        template_name="welcome.html",
                        context={"name": "Rollback Test"},
                    )
                    # Force a rollback by raising an exception inside atomic()
                    raise ValueError("Forced rollback")
            except ValueError:
                pass

            # After rollback, on_commit callbacks must NOT have fired
            mock_delay.assert_not_called()
