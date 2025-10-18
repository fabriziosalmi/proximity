"""
URL configuration for Proximity 2.0 project.

This module routes requests to Django Ninja API and Django admin.
"""
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from apps.core.api import router as core_router
from apps.applications.api import router as apps_router
from apps.proxmox.api import router as proxmox_router
from apps.backups.api import router as backups_router
from apps.catalog.api import router as catalog_router

# Create Django Ninja API instance
api = NinjaAPI(
    title="Proximity 2.0 API",
    version="2.0.0",
    description="Modern, application-centric delivery platform for Proxmox",
    docs_url="/docs",
)

# Register API routers
api.add_router("/core/", core_router, tags=["Core"])
api.add_router("/apps/", apps_router, tags=["Applications"])
api.add_router("/proxmox/", proxmox_router, tags=["Proxmox"])
api.add_router("/backups/", backups_router, tags=["Backups"])
api.add_router("/catalog/", catalog_router, tags=["Catalog"])

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]
