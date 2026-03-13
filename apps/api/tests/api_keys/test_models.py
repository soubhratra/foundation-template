"""Tests for APIKey model and generate_key() static method.

Requirements: AKEY-01 (key creation — raw key shown once, prefix + hash stored).
"""

import hashlib

import pytest

from apps.api_keys.models import APIKey


@pytest.mark.django_db
class TestAPIKeyGeneration:
    def test_generate_key_returns_three_tuple(self):
        raw_key, prefix, key_hash = APIKey.generate_key()
        assert isinstance(raw_key, str)
        assert isinstance(prefix, str)
        assert isinstance(key_hash, str)

    def test_raw_key_starts_with_prefix_setting(self, settings):
        settings.API_KEY_PREFIX = "ft_"  # pragma: allowlist secret
        raw_key, prefix, key_hash = APIKey.generate_key()
        assert raw_key.startswith("ft_")

    def test_stored_prefix_is_prefix_plus_8_chars(self, settings):
        settings.API_KEY_PREFIX = "ft_"  # pragma: allowlist secret
        raw_key, stored_prefix, key_hash = APIKey.generate_key()
        # stored_prefix = "ft_" + first 8 chars of random = 11 chars total
        assert stored_prefix.startswith("ft_")
        assert len(stored_prefix) == len("ft_") + 8

    def test_key_hash_is_sha256_of_raw_key(self):
        raw_key, prefix, key_hash = APIKey.generate_key()
        expected_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        assert key_hash == expected_hash

    def test_raw_key_not_stored_in_db(self, api_user):
        raw_key, stored_prefix, key_hash = APIKey.generate_key()
        key = APIKey.objects.create(
            user=api_user,
            prefix=stored_prefix,
            key_hash=key_hash,
            scopes=["read"],
            name="Test",
        )
        key.refresh_from_db()
        # raw_key must NOT be a field on the model
        assert not hasattr(key, "raw_key")
        # key_hash stored as SHA-256 hex (64 chars)
        assert len(key.key_hash) == 64

    def test_two_generated_keys_have_different_prefixes(self):
        _, prefix1, _ = APIKey.generate_key()
        _, prefix2, _ = APIKey.generate_key()
        assert prefix1 != prefix2
