"""
Backup API endpoints - Placeholder for EPIC 2 implementation
"""
from ninja import Router

router = Router()


@router.get("/")
def list_backups(request):
    """List all backups (placeholder)."""
    return {"backups": [], "total": 0}
