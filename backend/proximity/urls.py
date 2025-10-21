"""
URL configuration for Proximity 2.0 project.

This module routes requests to Django Ninja API and Django admin.
"""
from django.contrib import admin
from django.urls import path, include
from ninja import NinjaAPI

from apps.core.api import router as core_router
from apps.applications.api import router as apps_router
from apps.proxmox.api import router as proxmox_router
from apps.backups.api import router as backups_router
from apps.catalog.api import router as catalog_router

from .auth import JWTCookieAuthenticator

# Create Django Ninja API instance with global authentication
api = NinjaAPI(
    title="Proximity 2.0 API",
    version="2.0.0",
    description="Modern, application-centric delivery platform for Proxmox",
    docs_url="/docs",
    auth=JWTCookieAuthenticator(),
)


# Health check endpoint (public)
@api.get("/health", tags=["Health"], auth=None, summary="Health Check")
def health_check(request):
    """
    Health check endpoint for monitoring and container orchestration.
    Returns 200 OK if the service is running.
    """
    from django.db import connection
    from django.core.cache import cache
    
    health_status = {
        "status": "healthy",
        "service": "proximity-backend",
        "version": "2.0.0"
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis/cache
    try:
        cache.set("health_check", "ok", 10)
        cache.get("health_check")
        health_status["cache"] = "connected"
    except Exception as e:
        health_status["cache"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


# Register API routers (will be protected by global auth)
api.add_router("/core/", core_router, tags=["Core"])
api.add_router("/apps/", apps_router, tags=["Applications"])
api.add_router("/proxmox/", proxmox_router, tags=["Proxmox"])
api.add_router("/backups/", backups_router, tags=["Backups"])
api.add_router("/catalog/", catalog_router, tags=["Catalog"])

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Mount the Ninja API (now globally protected by JWT cookie auth)
    path('api/', api.urls),

    # Add dj-rest-auth endpoints for login, logout, token refresh, etc.
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
]