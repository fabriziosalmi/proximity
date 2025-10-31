from ninja.security import APIKeyCookie
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()

class JWTCookieAuthenticator(APIKeyCookie):
    param_name = "proximity-auth-cookie"  # As defined in settings.py REST_AUTH

    def authenticate(self, request, key):
        """
        Authenticates a user based on a JWT stored in an HttpOnly cookie.

        Args:
            request: The incoming HTTP request.
            key: The value of the cookie specified by `param_name`.

        Returns:
            The authenticated user object if the token is valid, otherwise None.
        """
        if key:
            try:
                # The key is the access token. We use simple-jwt's AccessToken
                # class to validate it and get the payload.
                token = AccessToken(key)
                
                # The payload contains the user_id claim we configured in settings.py.
                user_id = token.get('user_id')
                
                if user_id:
                    # Retrieve the user from the database.
                    user = User.objects.get(id=user_id)
                    return user
            except (InvalidToken, TokenError, User.DoesNotExist):
                # This handles cases where the token is expired, malformed,
                # or the user it refers to no longer exists.
                return None
        
        # If no key is provided, authentication fails.
        return None
