"""
JWT Authentication for Django Ninja API
"""
import jwt
from typing import Optional
from django.conf import settings
from django.http import HttpRequest
from ninja.security import HttpBearer
from .models import User


class JWTAuth(HttpBearer):
    """
    JWT Bearer token authentication for Django Ninja.

    Usage:
        @router.get("/protected", auth=JWTAuth())
        def protected_endpoint(request):
            # request.auth will contain the authenticated user
            return {"user": request.auth.username}
    """

    def authenticate(self, request: HttpRequest, token: str) -> Optional[User]:
        """
        Authenticate the JWT token and return the user.

        Args:
            request: Django HTTP request
            token: JWT token from Authorization header

        Returns:
            User object if authentication succeeds, None otherwise
        """
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Get user from payload
            user_id = payload.get('user_id')
            if not user_id:
                return None

            # Fetch user from database
            user = User.objects.get(id=user_id)

            # Attach user to request for convenience
            request.user = user

            return user

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            return None
