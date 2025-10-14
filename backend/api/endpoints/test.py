"""
Test endpoints for debugging and monitoring.

These endpoints are useful for:
- Testing Sentry error capture
- Verifying API health
- Debugging deployment issues
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sentry_sdk

router = APIRouter(prefix="/test", tags=["test"])


class TestResponse(BaseModel):
    message: str
    status: str


@router.get("/sentry-backend", response_model=TestResponse)
async def test_sentry_backend():
    """
    Test endpoint to verify backend Sentry integration.
    
    This endpoint deliberately raises an error that should be captured by Sentry.
    Use this to verify that:
    - Sentry is properly initialized
    - Backend errors are being captured
    - User context is being attached (if authenticated)
    - Stack traces are complete
    
    Expected behavior: Returns 500 error and creates a Sentry event.
    """
    # Add breadcrumb for context
    sentry_sdk.add_breadcrumb(
        category="test",
        message="Sentry backend test endpoint called",
        level="info"
    )
    
    # Deliberately raise an error
    raise ValueError("This is a deliberate test error from the Proximity backend. If you see this in Sentry, the integration is working correctly!")


@router.get("/health", response_model=TestResponse)
async def health_check():
    """
    Simple health check endpoint.
    
    Returns: Success message if API is running.
    """
    return TestResponse(
        message="Proximity API is healthy",
        status="ok"
    )


@router.get("/sentry-info", response_model=dict)
async def sentry_info():
    """
    Get information about Sentry configuration.
    
    Returns: Sentry status and configuration details (non-sensitive).
    """
    from core.config import settings
    
    is_enabled = bool(settings.SENTRY_DSN)
    
    return {
        "sentry_enabled": is_enabled,
        "environment": settings.SENTRY_ENVIRONMENT or "auto-detected",
        "release": settings.SENTRY_RELEASE or settings.APP_VERSION,
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
    }
