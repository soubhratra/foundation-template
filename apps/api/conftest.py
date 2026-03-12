"""
Root conftest.py for apps/api.

Sets DYLD_LIBRARY_PATH on macOS so WeasyPrint can find Homebrew-installed
system libraries (pango, glib, fontconfig). Linux Docker containers have
these installed at standard paths — no special configuration needed there.
"""

import functools
import os
import platform
import sys
import types

import pytest

if platform.system() == "Darwin":
    # Ensure Homebrew library path is included so WeasyPrint's cffi bindings
    # can load libgobject-2.0, libpango-1.0, etc.
    homebrew_lib = "/usr/local/lib"
    current = os.environ.get("DYLD_LIBRARY_PATH", "")
    if homebrew_lib not in current:
        paths = [homebrew_lib] + [p for p in current.split(":") if p]
        os.environ["DYLD_LIBRARY_PATH"] = ":".join(paths)


# --- nplusone: N+1 query detection (DEV-04) ---
# This autouse fixture activates nplusone for EVERY pytest test in apps/api.
#
# Failure mode: RAISE IMMEDIATELY (locked decision from CONTEXT.md).
# NPlusOneError is raised the instant a lazy load (N+1 query) is detected
# DURING the test body. This is NOT deferred to teardown; the test fails
# at the line that triggers the N+1.
#
# NOTE: Only lazy loads (N+1) are detected — unused eager loads (select_related
# optimisations that are correct but happen not to be accessed in a test) are
# intentionally excluded to prevent false positives in existing tests.
#
# To annotate an intentional N+1 (document it in code review):
#   from nplusone.ext.pytest import allow_lazy_load
#
#   @allow_lazy_load
#   def test_something_with_intentional_n_plus_one():
#       ...
#
# nplusone.ext.pytest (allow_lazy_load) is provided here for compatibility —
# nplusone 1.0.0 does not ship a pytest plugin; we implement the equivalent.

# Activate Django ORM patch so nplusone signals fire on ORM calls.
import nplusone.ext.django.patch  # noqa: F401
from nplusone.core import exceptions as _nplusone_exceptions
from nplusone.core import listeners as _nplusone_listeners


class _LazyLoadProfiler:
    """Context manager that raises NPlusOneError immediately on lazy loads (N+1).

    Unlike nplusone's full Profiler, this activates ONLY the LazyListener —
    not the EagerListener — so unused eager loads (unnecessary select_related)
    are not flagged. This prevents false positives in tests where production
    code uses select_related correctly but the test's assertion scope doesn't
    touch all prefetched relations.
    """

    def __enter__(self):
        from nplusone.core import signals as _signals

        self._listener = _nplusone_listeners.LazyListener(self)
        self._listener.setup()
        # Track which signals were connected so we can disconnect them on exit.
        # blinker connects with weak references by default, but we hold a strong
        # reference via self._listener, so we must disconnect explicitly.
        self._signals = _signals
        return self

    def __exit__(self, *exc):
        # Disconnect all signal handlers registered during setup() to prevent
        # this listener's handlers from firing in subsequent tests.
        worker = self._signals.get_worker()
        self._signals.load.disconnect(self._listener.handle_load, sender=worker)
        self._signals.ignore_load.disconnect(self._listener.handle_ignore, sender=worker)
        self._signals.lazy_load.disconnect(self._listener.handle_lazy, sender=worker)
        self._listener.teardown()

    def notify(self, message):
        raise _nplusone_exceptions.NPlusOneError(message.message)


def allow_lazy_load(func):
    """Decorator to suppress NPlusOneError for a specific test.

    Use this to document intentional N+1 accesses that are acceptable.
    Requires review justification in code review.

    Example::

        from nplusone.ext.pytest import allow_lazy_load

        @allow_lazy_load
        def test_something_with_intentional_n_plus_one(db):
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper._allow_lazy_load = True
    return wrapper


# Register allow_lazy_load under nplusone.ext.pytest so tests can import it:
#   from nplusone.ext.pytest import allow_lazy_load
_pytest_module = types.ModuleType("nplusone.ext.pytest")
_pytest_module.allow_lazy_load = allow_lazy_load
sys.modules["nplusone.ext.pytest"] = _pytest_module


@pytest.fixture(autouse=True)
def _nplusone_guard(request):
    """Activate nplusone lazy-load (N+1) detection for this test.

    NPlusOneError is raised during the test body (not at teardown) whenever
    a lazy load (N+1 query) is detected.

    Tests decorated with @allow_lazy_load skip this guard entirely.
    """
    # Skip if the test function is annotated with @allow_lazy_load
    test_func = request.node.function if hasattr(request.node, "function") else None
    if test_func is not None and getattr(test_func, "_allow_lazy_load", False):
        yield
        return

    with _LazyLoadProfiler():
        yield  # NPlusOneError raised during test body, not at teardown
