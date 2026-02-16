import dataclasses
import uuid
from typing import Any, Optional

from django import forms
from django.contrib.auth import get_user_model
from django.db import models
from django.http import HttpRequest

from allauth.account import app_settings as account_settings
from allauth.account.models import EmailAddress
from allauth.account.utils import user_display, user_username
from allauth.core.internal.httpkit import get_authorization_credential
from allauth.headless import app_settings as headless_settings
from allauth.headless.adapter import DefaultHeadlessAdapter
from allauth.headless.base.response import AuthenticationResponse
from allauth.headless.constants import Client
from allauth.headless.internal.restkit.response import APIResponse


def _resolve_user_name(user) -> str:
    if hasattr(user, "full_name"):
        full_name = getattr(user, "full_name")
        if full_name:
            return str(full_name)
    try:
        full_name = user.get_full_name().strip()
    except AttributeError:
        full_name = ""
    if full_name:
        return full_name
    if hasattr(user, "first_name") and getattr(user, "first_name"):
        return str(getattr(user, "first_name"))
    return ""


class HeadlessSignupForm(forms.Form):
    name = forms.CharField(max_length=255)

    def signup(self, request, user):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            return
        fields_to_update = []
        if hasattr(user, "full_name"):
            setattr(user, "full_name", name)
            fields_to_update.append("full_name")
        elif hasattr(user, "first_name"):
            setattr(user, "first_name", name)
            fields_to_update.append("first_name")
        if fields_to_update:
            user.save(update_fields=fields_to_update)


class SessionAwareJWTTokenStrategy:
    """
    A JWT token strategy wrapper that omits JWT tokens for session-based logins.
    
    JWT access/refresh tokens should only be issued by JWT-specific endpoints
    (like token refresh), not by session-based login/signup endpoints.
    
    This wrapper delegates to the underlying JWTTokenStrategy but only
    creates access token payloads when the request includes an Authorization
    header (indicating it's already using JWT authentication).
    """
    
    def __init__(self):
        from allauth.headless.tokens.strategies.jwt import JWTTokenStrategy
        self._strategy = JWTTokenStrategy()
    
    def __getattr__(self, name):
        """Delegate all attribute access to the underlying strategy."""
        return getattr(self._strategy, name)
    
    def create_access_token_payload(self, request: HttpRequest) -> Optional[dict]:
        """
        Only create access token payload if request already has JWT auth.
        
        This prevents session-based logins from receiving JWT tokens in
        the response, while still allowing JWT token refresh flows.
        """
        # Check if the request came with an Authorization header
        # If not, this is a session-based login - don't issue JWTs
        auth_header = get_authorization_credential(
            request, headless_settings.JWT_AUTHORIZATION_HEADER_SCHEME
        )
        if auth_header is None:
            # No Authorization header = session-based login
            # Don't issue JWT tokens for session logins
            return None
        
        # Request has Authorization header - delegate to underlying strategy
        return self._strategy.create_access_token_payload(request)


class HeadlessAdapter(DefaultHeadlessAdapter):
    def user_as_dataclass(self, user):
        UserDc = self.get_user_dataclass()
        kwargs: dict[str, Any] = {}
        User = get_user_model()
        pk_field_class = type(User._meta.pk)
        if not user.pk:
            id_dc = None
        elif issubclass(pk_field_class, models.IntegerField):
            id_dc = user.pk
        else:
            id_dc = str(user.pk)
        if account_settings.USER_MODEL_USERNAME_FIELD:
            kwargs["username"] = user_username(user)
        if user.pk:
            email = EmailAddress.objects.get_primary_email(user)
        else:
            email = None
        kwargs.update(
            {
                "id": id_dc,
                "email": email if email else None,
                "display": user_display(user),
                "has_usable_password": user.has_usable_password(),
                "name": _resolve_user_name(user),
            }
        )
        return UserDc(**kwargs)

    def get_user_dataclass(self):
        fields = []
        User = get_user_model()
        pk_field_class = type(User._meta.pk)
        if issubclass(pk_field_class, models.UUIDField):
            id_type = str
            id_example = str(uuid.uuid4())
        elif issubclass(pk_field_class, models.IntegerField):
            id_type = int
            id_example = 123
        else:
            id_type = str
            id_example = "uid"

        def dc_field(attr, typ, description, example):
            return (
                attr,
                typ,
                dataclasses.field(
                    metadata={
                        "description": description,
                        "example": example,
                    }
                ),
            )

        fields.extend(
            [
                dc_field("id", Optional[id_type], "The user ID.", id_example),
                dc_field(
                    "display", str, "The display name for the user.", "Magic Wizard"
                ),
                dc_field(
                    "email", Optional[str], "The email address.", "email@domain.org"
                ),
                dc_field(
                    "has_usable_password",
                    bool,
                    "Whether or not the account has a password set.",
                    True,
                ),
                dc_field(
                    "name",
                    Optional[str],
                    "The user's full name.",
                    "Ada Lovelace",
                ),
            ]
        )
        if account_settings.USER_MODEL_USERNAME_FIELD:
            fields.append(dc_field("username", str, "The username.", "wizard"))
        return dataclasses.make_dataclass("User", fields)

