import dataclasses
import uuid
from typing import Any, Optional

from django import forms
from django.contrib.auth import get_user_model
from django.db import models

from allauth.account import app_settings as account_settings
from allauth.account.models import EmailAddress
from allauth.account.utils import user_display, user_username
from allauth.headless.adapter import DefaultHeadlessAdapter


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

