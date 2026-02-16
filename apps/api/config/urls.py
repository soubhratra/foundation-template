import logging

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404, HttpResponseForbidden
from django.urls import include, path
from ninja.errors import HttpError
from ninja.openapi.urls import get_openapi_urls
from ninja_extra import NinjaExtraAPI
from pydantic import ValidationError as PydanticValidationError

from allauth.headless.constants import Client
from apps.accounts.headless import HeadlessSessionView
from apps.core.exceptions import ServiceError


def docs_guard(view_func):
    def _wrapped(request, *args, **kwargs):
        if not settings.DEBUG:
            if not request.user.is_authenticated or not request.user.is_staff:
                raise Http404()
        elif not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication required.")
        return view_func(request, *args, **kwargs)

    return _wrapped


api = NinjaExtraAPI(
    title="Foundation API",
    version="1.0.0",
    urls_namespace="api_v1",
    docs_decorator=docs_guard,
)


def _error_response(request, *, code: str, message: str, status: int, details=None):
    return api.create_response(
        request,
        {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
        status=status,
    )


def _format_error_field(location) -> str:
    if not location:
        return "__all__"
    if location[0] in {"body", "query", "path", "header"}:
        location = location[1:]
    if not location:
        return "__all__"
    return ".".join(str(part) for part in location)


@api.exception_handler(ServiceError)
def service_error_handler(request, exc: ServiceError):
    return _error_response(
        request,
        code=exc.code,
        message=exc.message,
        status=exc.status_code,
        details=exc.details,
    )


@api.exception_handler(PydanticValidationError)
def pydantic_validation_error_handler(request, exc: PydanticValidationError):
    field_errors: dict[str, list[str]] = {}
    for error in exc.errors():
        field = _format_error_field(error.get("loc", ()))
        field_errors.setdefault(field, []).append(error.get("msg", "Invalid value"))
    return _error_response(
        request,
        code="VALIDATION_001",
        message="Validation failed.",
        status=400,
        details={"field_errors": field_errors},
    )


@api.exception_handler(DjangoValidationError)
def django_validation_error_handler(request, exc: DjangoValidationError):
    field_errors: dict[str, list[str]] = {}
    if hasattr(exc, "message_dict"):
        for field, messages in exc.message_dict.items():
            field_errors[field] = [str(message) for message in messages]
    elif exc.messages:
        field_errors["__all__"] = [str(message) for message in exc.messages]
    details = {"field_errors": field_errors} if field_errors else {}
    return _error_response(
        request,
        code="VALIDATION_002",
        message="Validation failed.",
        status=400,
        details=details,
    )


@api.exception_handler(Http404)
def not_found_handler(request, exc: Http404):
    return _error_response(
        request,
        code="RESOURCE_001",
        message="Resource not found.",
        status=404,
    )


@api.exception_handler(PermissionDenied)
def permission_denied_handler(request, exc: PermissionDenied):
    return _error_response(
        request,
        code="AUTH_005",
        message="You do not have permission to perform this action.",
        status=403,
    )


@api.exception_handler(HttpError)
def http_error_handler(request, exc: HttpError):
    status_code = exc.status_code
    if status_code == 401:
        code = "AUTH_001"
    elif status_code == 403:
        code = "AUTH_005"
    elif status_code == 404:
        code = "RESOURCE_001"
    elif status_code == 409:
        code = "CONFLICT_001"
    elif status_code == 429:
        code = "RATE_001"
    elif 400 <= status_code < 500:
        code = "VALIDATION_003"
    else:
        code = "SERVER_001"
    return _error_response(
        request,
        code=code,
        message=str(exc),
        status=status_code,
    )


@api.exception_handler(Exception)
def unhandled_exception_handler(request, exc: Exception):
    logger = logging.getLogger("foundation.unhandled")
    logger.exception("Unhandled exception", exc_info=exc)
    return _error_response(
        request,
        code="SERVER_001",
        message="An unexpected error occurred. Please try again later.",
        status=500,
    )


api.auto_discover_controllers()


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/v1/auth/browser/v1/auth/session",
        HeadlessSessionView.as_api_view(client=Client.BROWSER),
        name="headless_session_browser",
    ),
    path(
        "api/v1/auth/app/v1/auth/session",
        HeadlessSessionView.as_api_view(client=Client.APP),
        name="headless_session_app",
    ),
    path("api/v1/auth/", include("allauth.headless.urls")),
    path("api/", include((get_openapi_urls(api), "api-docs"))),
    path("api/v1/", api.urls),
]
