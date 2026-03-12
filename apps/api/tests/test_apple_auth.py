"""SOCIAL-03: Tests for Apple Sign In JWT verification and name persistence.

Tests the custom server-side Apple identity token verification required because
Expo's expo-apple-authentication issues JWTs with aud = Bundle ID (not Services ID),
which differs from allauth's standard social token flow expectation.

The module under test (apps.accounts.apple_auth) does not yet exist — every test
fails RED when the import is attempted inside the test body.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Test JWT helper — produces structurally valid RS256 JWTs for tests that
# need a valid-format token (e.g. "wrong audience" test where we want to
# get past structural validation to hit the audience check).
# ---------------------------------------------------------------------------


def generate_test_apple_jwt(
    payload: dict[str, Any],
    key_id: str = "test-kid",
    private_key: bytes | None = None,
) -> str:
    """Generate a signed RS256 JWT with the given payload.

    Uses a freshly generated RSA key pair when private_key is None.
    The corresponding public key is NOT registered anywhere — these tokens
    will fail real JWKS verification and are only useful for tests that mock
    the JWKS endpoint.
    """
    import jwt as pyjwt
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    if private_key is None:
        rsa_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_key = rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

    headers = {"kid": key_id}
    return pyjwt.encode(payload, private_key, algorithm="RS256", headers=headers)


def _make_apple_jwks_mock(private_key_pem: bytes) -> MagicMock:
    """Build a mock for requests.get that returns a JWKS response matching private_key_pem."""
    import base64

    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    key = load_pem_private_key(private_key_pem, password=None)
    pub = key.public_key()
    pub_numbers = pub.public_numbers()

    def _int_to_base64url(n: int) -> str:
        length = (n.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": _int_to_base64url(pub_numbers.n),
                "e": _int_to_base64url(pub_numbers.e),
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = jwks
    mock_response.raise_for_status.return_value = None
    mock_get = MagicMock(return_value=mock_response)
    return mock_get


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestVerifyAppleIdentityToken:
    """SOCIAL-03: Unit tests for Apple identity token JWT verification."""

    def test_verify_identity_token_rejects_invalid(self) -> None:
        """verify_apple_identity_token raises an error on a structurally invalid token."""
        try:
            from apps.accounts.apple_auth import verify_apple_identity_token
        except ImportError:
            pytest.fail(
                "verify_apple_identity_token not yet implemented — "
                "create apps/accounts/apple_auth.py with "
                "verify_apple_identity_token(token, audience)"
            )

        import jwt

        with pytest.raises((jwt.PyJWTError, ValueError)):
            verify_apple_identity_token("bad.token.value", "com.test.app")

    def test_verify_identity_token_rejects_wrong_audience(self) -> None:
        """verify_apple_identity_token raises InvalidAudienceError when aud doesn't match."""
        try:
            from apps.accounts.apple_auth import verify_apple_identity_token
        except ImportError:
            pytest.fail(
                "verify_apple_identity_token not yet implemented — "
                "create apps/accounts/apple_auth.py"
            )

        import jwt
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        # Generate fresh RSA key pair for this test
        rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_key_pem = rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        payload = {
            "iss": "https://appleid.apple.com",
            "aud": "com.wrong.app",  # Wrong audience
            "sub": "test-user-id",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = generate_test_apple_jwt(payload, private_key=private_key_pem)
        mock_get = _make_apple_jwks_mock(private_key_pem)

        with patch("apps.accounts.apple_auth.requests.get", mock_get):
            with pytest.raises(jwt.exceptions.InvalidAudienceError):
                verify_apple_identity_token(token, "com.correct.app")

    def test_verify_identity_token_accepts_valid_token(self) -> None:
        """verify_apple_identity_token returns decoded payload for a valid token."""
        try:
            from apps.accounts.apple_auth import verify_apple_identity_token
        except ImportError:
            pytest.fail(
                "verify_apple_identity_token not yet implemented — "
                "create apps/accounts/apple_auth.py"
            )

        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_key_pem = rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        bundle_id = "com.example.myapp"
        payload = {
            "iss": "https://appleid.apple.com",
            "aud": bundle_id,
            "sub": "apple-user-001",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = generate_test_apple_jwt(payload, private_key=private_key_pem)
        mock_get = _make_apple_jwks_mock(private_key_pem)

        with patch("apps.accounts.apple_auth.requests.get", mock_get):
            decoded = verify_apple_identity_token(token, bundle_id)

        assert decoded["sub"] == "apple-user-001"
        assert decoded["aud"] == bundle_id


class TestAppleNamePersistence:
    """SOCIAL-03: Apple name is persisted on first login and never overwritten on return login."""

    def test_name_persisted_first_login(self, db: Any) -> None:
        """User's name from Apple is saved to first_name on first sign-in."""
        try:
            from apps.accounts.apple_auth import handle_apple_login
        except ImportError:
            pytest.fail(
                "handle_apple_login not yet implemented in apps/accounts/apple_auth.py — "
                "create a function that accepts (identity_payload, full_name) and creates/updates "
                "the user, persisting first_name only when it is currently blank"
            )

        identity_payload = {
            "sub": "apple-user-unique-001",
            "email": "user@example.com",
            "aud": "com.example.app",
        }
        user = handle_apple_login(identity_payload=identity_payload, full_name="Alice Smith")
        assert user.first_name == "Alice", (
            "first_name should be 'Alice' after first Apple Sign In with full_name='Alice Smith'"
        )

    def test_name_not_overwritten_on_return_login(self, db: Any) -> None:
        """User's name is NOT overwritten on subsequent Apple Sign In (Apple sends no name)."""
        try:
            from apps.accounts.apple_auth import handle_apple_login
        except ImportError:
            pytest.fail(
                "handle_apple_login not yet implemented — "
                "needed for return-login name persistence test"
            )

        apple_sub = "apple-user-unique-002"
        identity_payload = {
            "sub": apple_sub,
            "email": "returning@example.com",
            "aud": "com.example.app",
        }

        # First login — name provided
        handle_apple_login(identity_payload=identity_payload, full_name="Bob Jones")

        # Second login — Apple sends no name (full_name=None)
        user = handle_apple_login(identity_payload=identity_payload, full_name=None)

        assert user.first_name == "Bob", (
            "first_name must not be overwritten on return Apple login when full_name is None"
        )
