from typing import Any

from ninja import Field, Schema


class ErrorDetail(Schema):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorOut(Schema):
    error: ErrorDetail

