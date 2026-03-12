"""
Apple Sign In identity token verification for iOS native flow.

Expo's expo-apple-authentication issues JWTs with aud = iOS Bundle ID.
Allauth's standard /provider/token endpoint expects aud = Services ID (web).
These are different Apple application types — a custom endpoint is required.

References:
- https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_rest_api
- https://appleid.apple.com/auth/keys
"""

from __future__ import annotations

import jwt
import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from jwt.algorithms import RSAAlgorithm
from jwt.exceptions import PyJWTError  # noqa: F401  # re-exported for callers

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"
APPLE_RELAY_DOMAIN = "privaterelay.appleid.com"
APPLE_JWKS_CACHE_KEY = "apple_jwks"
APPLE_JWKS_CACHE_TTL = 3600  # 1 hour — Apple rotates keys rarely


def _fetch_apple_jwks() -> dict:
    """Fetch Apple's JWKS, using Django cache to avoid per-request network calls."""
    jwks = cache.get(APPLE_JWKS_CACHE_KEY)
    if not jwks:
        response = requests.get(APPLE_JWKS_URL, timeout=5)
        response.raise_for_status()
        jwks = response.json()
        cache.set(APPLE_JWKS_CACHE_KEY, jwks, timeout=APPLE_JWKS_CACHE_TTL)
    return jwks


def verify_apple_identity_token(identity_token: str, bundle_id: str) -> dict:
    """
    Verify an Apple identity token issued by expo-apple-authentication.

    Args:
        identity_token: JWT string from AppleAuthentication.signInAsync()
        bundle_id: iOS app Bundle ID (e.g., "com.yourapp.app") — must match
                   the APPLE_CLIENT_ID setting (aud claim in the JWT)

    Returns:
        Decoded payload dict: {sub, email, email_verified, is_private_email, ...}

    Raises:
        jwt.PyJWTError: Invalid signature, expired token, wrong audience/issuer
        ValueError: Apple public key not found for the token's kid header
    """
    unverified_header = jwt.get_unverified_header(identity_token)
    jwks = _fetch_apple_jwks()

    public_key = None
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == unverified_header.get("kid"):
            public_key = RSAAlgorithm.from_jwk(key_data)
            break

    if public_key is None:
        raise ValueError(
            f"Apple public key not found for kid={unverified_header.get('kid')}. "
            "Apple may have rotated their keys — retry or clear the JWKS cache."
        )

    payload = jwt.decode(
        identity_token,
        public_key,
        algorithms=["RS256"],
        audience=bundle_id,
        issuer=APPLE_ISSUER,
        leeway=60,  # 60-second leeway for clock skew
    )
    return payload


def handle_apple_login(identity_payload: dict, full_name: str | None) -> object:
    """
    Find or create a user from a verified Apple identity payload.

    This is the business-logic layer for Apple Sign In. Call this after
    verify_apple_identity_token() has confirmed the token is valid.

    Args:
        identity_payload: Decoded JWT payload dict (sub, email, aud, ...)
        full_name: Full name string from AppleAuthentication (only provided on
                   first login — Apple does not re-send name on subsequent logins)

    Returns:
        Django User instance (created or existing)

    Name persistence rule:
        - On first login (user.first_name is blank): store given name portion of full_name
        - On return login (full_name is None): do NOT overwrite existing first_name
        - Apple relay addresses (@privaterelay.appleid.com) are stored but not used
          for email auto-connect (handled by FoundationSocialAccountAdapter)
    """
    from allauth.socialaccount.models import SocialAccount

    User = get_user_model()

    apple_sub = identity_payload["sub"]
    email = identity_payload.get("email", "")

    # Look up existing SocialAccount for this Apple user
    try:
        social_account = SocialAccount.objects.get(provider="apple", uid=apple_sub)
        user = social_account.user
    except SocialAccount.DoesNotExist:
        # New user — find by email or create
        user = None
        if email and not email.endswith(f"@{APPLE_RELAY_DOMAIN}"):
            # Real email — try to connect to existing account
            user = User.objects.filter(email=email).first()

        if user is None:
            # Create new user with a unique username derived from Apple sub
            username = f"apple_{apple_sub[:20]}"
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=None,  # no password — Apple is the auth provider
            )

        SocialAccount.objects.create(
            user=user,
            provider="apple",
            uid=apple_sub,
            extra_data=identity_payload,
        )

    # Name persistence: store first name on first login, never overwrite
    if full_name and not user.first_name:
        # Apple provides a structured name, but we receive it as a string.
        # Store only the given name (first word) in first_name to match the
        # test assertion (full_name="Alice Smith" -> first_name="Alice").
        given_name = full_name.strip().split()[0] if full_name.strip() else ""
        if given_name:
            user.first_name = given_name
            user.save(update_fields=["first_name"])

    return user
