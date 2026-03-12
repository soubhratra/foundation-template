import json
from datetime import UTC, datetime

from allauth.headless.contrib.ninja.security import jwt_token_auth
from django.http import HttpResponse
from ninja import Schema
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

from .schemas import UserOut, UserUpdateIn
from .services import AccountExportService, UserService
from .tasks import delete_user_account


class DeleteAccountIn(Schema):
    password: str


class MessageOut(Schema):
    message: str


@api_controller(
    "/users",
    tags=["Users"],
    permissions=[IsAuthenticated],
    auth=[SessionAuth(), jwt_token_auth],
)
class UserController(ControllerBase):
    def __init__(self):
        self.service = UserService()

    @route.get("/me", response=UserOut, url_name="user-me")
    def get_current_user(self, request):
        """Get the authenticated user's profile."""
        return self.service.get_user(user_id=request.user.id)

    @route.patch("/me", response=UserOut, url_name="user-me-update")
    def update_current_user(self, request, payload: UserUpdateIn):
        """Update the authenticated user's profile."""
        return self.service.update_user(user_id=request.user.id, data=payload)


@api_controller(
    "/account",
    tags=["Account"],
    permissions=[IsAuthenticated],
    auth=[SessionAuth(), jwt_token_auth],
)
class AccountController(ControllerBase):
    """GDPR endpoints for account self-service deletion and data export."""

    @route.delete(
        "/",
        response={202: MessageOut, 400: dict},
        url_name="account-delete",
    )
    def delete_account(self, request, payload: DeleteAccountIn):
        """Initiate account deletion (GDPR Article 17 — right to erasure).

        Verifies the user's password, invalidates all sessions, and enqueues
        an asynchronous Celery task to perform the full deletion cascade.

        Returns 202 Accepted immediately — the actual deletion happens asynchronously.
        Returns 400 if the provided password is incorrect.
        """
        from .services import invalidate_user_sessions

        if not request.user.check_password(payload.password):
            return 400, {"detail": "Incorrect password."}

        invalidate_user_sessions(request.user.id)
        delete_user_account.delay(request.user.id)
        return 202, {"message": "Account deletion initiated."}

    @route.get(
        "/export",
        url_name="account-export",
    )
    def export_account(self, request):
        """Export user data package (GDPR Article 20 — right to data portability).

        Returns a JSON file download containing profile, connected social accounts,
        and billing history. Stripe IDs are excluded from the export payload.
        """
        data = AccountExportService().export(request.user)
        data["exported_at"] = datetime.now(UTC).isoformat()

        response = HttpResponse(
            json.dumps(data, default=str),
            content_type="application/json",
        )
        response["Content-Disposition"] = 'attachment; filename="my-data.json"'
        return response


# ---------------------------------------------------------------------------
# SOCIAL AUTH MODULE — remove this controller to exclude Apple Sign In
# ---------------------------------------------------------------------------


class AppleSignInRequest(Schema):
    identity_token: str
    full_name: str | None = None  # only present on first login


class AppleSignInResponse(Schema):
    access: str
    refresh: str


@api_controller(
    "/auth",
    tags=["Auth"],
    auth=None,  # Public endpoint — no auth required for sign in
)
class AppleSignInController(ControllerBase):  # SOCIAL AUTH MODULE
    @route.post(
        "/apple/",
        response={200: AppleSignInResponse, 400: dict},
        url_name="apple-sign-in",
    )
    def apple_sign_in(self, request, payload: AppleSignInRequest):
        """
        iOS Apple Sign In endpoint for Expo's expo-apple-authentication.

        Accepts an identityToken from AppleAuthentication.signInAsync(), verifies
        it against Apple's JWKS, and returns JWT access + refresh tokens.

        The standard allauth /provider/token endpoint cannot be used because
        expo-apple-authentication issues JWTs with aud = Bundle ID, while
        allauth expects aud = Services ID (web OAuth flow).
        """
        import jwt as pyjwt
        from allauth.headless.tokens.strategies.jwt.strategy import JWTTokenStrategy
        from django.conf import settings

        from .apple_auth import handle_apple_login, verify_apple_identity_token

        bundle_id = getattr(settings, "APPLE_CLIENT_ID", "")

        try:
            identity_payload = verify_apple_identity_token(payload.identity_token, bundle_id)
        except (pyjwt.PyJWTError, ValueError) as exc:
            return 400, {"error": "invalid_token", "detail": str(exc)}

        user = handle_apple_login(
            identity_payload=identity_payload,
            full_name=payload.full_name,
        )

        # Log the user into the Django session so the JWT strategy can create tokens.
        # Django's login() attaches the user to request.user and ensures
        # request.session has a session_key (required by allauth's JWT strategy).
        from django.contrib.auth import login as django_login

        django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        # Issue JWT tokens using allauth's built-in JWT strategy.
        # create_access_token_payload returns {"access_token": "...", "refresh_token": "..."}
        strategy = JWTTokenStrategy()
        token_payload = strategy.create_access_token_payload(request)
        if token_payload is None:
            # Fallback: strategy returned None (e.g., SessionAwareJWTTokenStrategy without
            # Authorization header) — call internal directly with the live session.
            from allauth.headless.tokens.strategies.jwt import internal as jwt_internal

            if not request.session.session_key:
                request.session.save()
            access_token = jwt_internal.create_access_token(user, request.session, {})
            refresh_token = jwt_internal.create_refresh_token(user, request.session)
        else:
            access_token = token_payload.get("access_token", "")
            refresh_token = token_payload.get("refresh_token", "")

        return 200, {"access": access_token, "refresh": refresh_token}


# ---------------------------------------------------------------------------
# END SOCIAL AUTH MODULE
# ---------------------------------------------------------------------------
