"""
Catalog API endpoints.

Provides REST API for browsing and searching the application catalog.
"""
from typing import List
from ninja import Router
from ninja.errors import HttpError

from .schemas import (
    CatalogAppSchema,
    CatalogListResponse,
    CatalogCategoriesResponse
)
from .services import catalog_service


router = Router(tags=["Catalog"])


@router.get("/", response=CatalogListResponse, summary="List all applications")
def list_apps(request):
    """
    Get all applications from the catalog.
    
    Returns a list of all available applications that can be deployed.
    """
    apps = catalog_service.get_all_apps()
    return {
        "total": len(apps),
        "applications": apps
    }


@router.get("/categories", response=CatalogCategoriesResponse, summary="List all categories")
def list_categories(request):
    """
    Get all unique categories from the catalog.
    
    Returns a list of category names that can be used for filtering.
    """
    categories = catalog_service.get_categories()
    return {
        "categories": categories
    }


@router.get("/search", response=CatalogListResponse, summary="Search applications")
def search_apps(request, q: str = ""):
    """
    Search for applications matching the query.
    
    Searches in application name, description, and tags.
    
    Args:
        q: Search query string (case-insensitive)
        
    Returns:
        List of matching applications
    """
    apps = catalog_service.search_apps(q)
    return {
        "total": len(apps),
        "applications": apps
    }


@router.get("/category/{category}", response=CatalogListResponse, summary="Filter by category")
def filter_by_category(request, category: str):
    """
    Get all applications in a specific category.
    
    Args:
        category: The category name
        
    Returns:
        List of applications in the category
    """
    apps = catalog_service.filter_by_category(category)
    return {
        "total": len(apps),
        "applications": apps
    }


@router.get("/stats", summary="Get catalog statistics")
def get_stats(request):
    """
    Get statistics about the catalog.
    
    Returns:
        Dictionary with total apps and categories
    """
    return catalog_service.get_stats()


@router.post("/reload", summary="Reload catalog from disk")
def reload_catalog(request):
    """
    Reload the catalog from disk.
    
    This endpoint can be called to refresh the catalog without
    restarting the application.
    
    Requires admin authentication.
    """
    # TODO: Add permission check for admin users
    catalog_service.reload()
    stats = catalog_service.get_stats()
    return {
        "message": "Catalog reloaded successfully",
        "stats": stats
    }


@router.get("/{app_id}", response=CatalogAppSchema, summary="Get application by ID")
def get_app(request, app_id: str):
    """
    Get a single application by its ID.
    
    Args:
        app_id: The application ID (e.g., 'adminer', 'nginx')
        
    Returns:
        The application details
        
    Raises:
        404: If the application is not found
    """
    app = catalog_service.get_app_by_id(app_id)
    
    if app is None:
        raise HttpError(404, f"Application '{app_id}' not found in catalog")
    
    return app
