"""
Core middleware for Proximity 2.0
"""
import sentry_sdk
from django.utils.deprecation import MiddlewareMixin


class SentryUserContextMiddleware(MiddlewareMixin):
    """
    Middleware to enrich Sentry error reports with user context.
    
    This middleware sets the user information in Sentry whenever a request
    is made by an authenticated user, providing better context for debugging.
    """
    
    def process_request(self, request):
        """
        Process incoming request and set Sentry user context.
        
        Args:
            request: Django HttpRequest object
        """
        if request.user.is_authenticated:
            sentry_sdk.set_user({
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
            })
        else:
            # Clear user context for anonymous requests
            sentry_sdk.set_user(None)
        
        return None
