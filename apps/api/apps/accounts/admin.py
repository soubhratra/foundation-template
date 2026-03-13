"""UserAdmin with django-unfold theme and django-hijack impersonation."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from hijack.contrib.admin import HijackUserAdminMixin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User


@admin.register(User)
class UserAdmin(HijackUserAdminMixin, BaseUserAdmin, ModelAdmin):
    """UserAdmin with impersonation button on change page.

    MRO order is critical:
    - HijackUserAdminMixin must come first (adds impersonate button)
    - BaseUserAdmin second (provides password management)
    - ModelAdmin (unfold) last (provides theme)

    Unfold forms must be set explicitly — base UserAdmin forms lack
    unfold styling and cause broken password forms.
    """

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("email", "username", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active", "is_superuser")
    search_fields = ("email", "username")
