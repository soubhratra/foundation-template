"""RED test stubs for OBS-05: example periodic Celery task.

These tests are intentionally in RED state — apps.core.tasks does not exist yet.
Plan 15-03 will create that module and turn these GREEN.

Task under test: example_periodic_task
  - Bound Celery task (bind=True)
  - Delegates internal work to _do_work() helper
  - Retries on transient errors via self.retry()
"""

import unittest.mock

import pytest


@pytest.mark.req("OBS-06")
@pytest.mark.django_db
def test_example_task_succeeds_and_returns_result():
    """Task completes successfully when _do_work runs without error."""
    from apps.core.tasks import example_periodic_task  # RED: module not yet created

    result = example_periodic_task.apply()
    assert result.successful()


@pytest.mark.req("OBS-06")
@pytest.mark.django_db
def test_example_task_retries_on_transient_error():
    """Task raises Retry when _do_work raises a transient error."""
    from celery.exceptions import Retry

    from apps.core.tasks import example_periodic_task  # RED: module not yet created

    with unittest.mock.patch("apps.core.tasks._do_work", side_effect=Exception("transient")):
        with pytest.raises(Retry):
            example_periodic_task.apply(throw=True)
