from django.http import HttpRequest
from ninja_extra import ControllerBase
from ninja_extra.permissions import BasePermission

KNOWN_ROLES: frozenset[str] = frozenset({"admin", "member"})


class RequireRole(BasePermission):
    """Gate access to users who are members of a specific Django Group.

    Usage:
        permissions=[IsAuthenticated, RequireRole("admin")]

    IsAuthenticated MUST be listed before RequireRole — RequireRole assumes
    request.user is authenticated. The IsAuthenticated check runs first
    because ninja-extra evaluates the permissions list left-to-right.

    When the role check fails, raises PermissionDenied which is caught by
    the global permission_denied_handler in config/urls.py and returned
    as HTTP 403 with JSON body {"error": {"code": "AUTH_005", ...}}.
    """

    def __init__(self, role: str) -> None:
        self.role = role

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if not user.groups.filter(name=self.role).exists():
            return False
        return True
