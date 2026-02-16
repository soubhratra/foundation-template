from typing import Any, Mapping


class ServiceError(Exception):
    """Base exception for service layer errors."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(ServiceError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(code="RESOURCE_001", message=message, status_code=404)


class PermissionDeniedError(ServiceError):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(code="AUTH_005", message=message, status_code=403)


class ConflictError(ServiceError):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(code="CONFLICT_001", message=message, status_code=409)
