"""
Application API endpoints - Placeholder for EPIC 2 implementation
"""
from ninja import Router

router = Router()


@router.get("/")
def list_applications(request):
    """List all applications (placeholder)."""
    return {"apps": [], "total": 0}
