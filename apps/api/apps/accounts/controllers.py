from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

from allauth.headless.contrib.ninja.security import jwt_token_auth

from .schemas import UserOut, UserUpdateIn
from .services import UserService


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
