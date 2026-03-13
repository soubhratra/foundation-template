"""Tests for API_KEY_SCOPES manage.py check system validator.

Requirements: AKEY-01 (startup validation of scope catalog).
"""

from django.test import override_settings

from apps.api_keys.checks import check_api_key_scopes


class TestApiKeyScopesCheck:
    def test_valid_scopes_produces_no_warnings(self):
        scopes = {
            "read": {"description": "Read-only access"},
            "write": {"description": "Write access"},
        }
        with override_settings(API_KEY_SCOPES=scopes):
            errors = check_api_key_scopes(None)
        assert errors == []

    def test_missing_setting_produces_warning(self):
        with override_settings(API_KEY_SCOPES=None):
            errors = check_api_key_scopes(None)
        assert len(errors) == 1
        assert errors[0].id == "api_keys.W001"

    def test_non_dict_scopes_produces_warning(self):
        with override_settings(API_KEY_SCOPES=["read", "write"]):
            errors = check_api_key_scopes(None)
        assert any(e.id == "api_keys.W002" for e in errors)

    def test_scope_missing_description_produces_warning(self):
        scopes = {"read": {}}  # missing 'description'
        with override_settings(API_KEY_SCOPES=scopes):
            errors = check_api_key_scopes(None)
        assert any(e.id == "api_keys.W003" for e in errors)
