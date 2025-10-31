"""
Proxmox API endpoints - Host and node management
"""
from typing import List
from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404

from .models import ProxmoxHost, ProxmoxNode
from .services import ProxmoxService, ProxmoxError
from .schemas import (
    ProxmoxHostCreate, ProxmoxHostResponse, ProxmoxHostUpdate,
    ProxmoxNodeResponse, ConnectionTestResponse
)

router = Router()


@router.get("/hosts", response=List[ProxmoxHostResponse])
def list_hosts(request):
    """List all Proxmox hosts."""
    # 🔐 Authorization: Only admins can view Proxmox hosts
    if not request.user.is_authenticated or not request.user.is_staff:
        raise HttpError(403, "Admin privileges required to view Proxmox hosts")

    hosts = ProxmoxHost.objects.all()
    return [{
        "id": h.id,
        "name": h.name,
        "host": h.host,
        "port": h.port,
        "user": h.user,
        "is_active": h.is_active,
        "is_default": h.is_default,
        "last_seen": h.last_seen.isoformat() if h.last_seen else None,
    } for h in hosts]


@router.post("/hosts", response=ProxmoxHostResponse)
def create_host(request, payload: ProxmoxHostCreate):
    """Create a new Proxmox host configuration."""
    # 🔐 Authorization: Only admins can create Proxmox hosts
    if not request.user.is_authenticated or not request.user.is_staff:
        raise HttpError(403, "Admin privileges required to create Proxmox hosts")

    # TODO: Encrypt password before saving
    host = ProxmoxHost.objects.create(
        name=payload.name,
        host=payload.host,
        port=payload.port,
        user=payload.user,
        password=payload.password,  # TODO: Encrypt
        verify_ssl=payload.verify_ssl,
        is_default=payload.is_default,
        created_by=request.user if request.user.is_authenticated else None
    )
    
    return {
        "id": host.id,
        "name": host.name,
        "host": host.host,
        "port": host.port,
        "user": host.user,
        "is_active": host.is_active,
        "is_default": host.is_default,
        "last_seen": None,
    }


@router.get("/hosts/{host_id}", response=ProxmoxHostResponse)
def get_host(request, host_id: int):
    """Get a specific Proxmox host."""
    # 🔐 Authorization: Only admins can view Proxmox hosts
    if not request.user.is_authenticated or not request.user.is_staff:
        raise HttpError(403, "Admin privileges required to view Proxmox hosts")

    host = get_object_or_404(ProxmoxHost, id=host_id)
    return {
        "id": host.id,
        "name": host.name,
        "host": host.host,
        "port": host.port,
        "user": host.user,
        "is_active": host.is_active,
        "is_default": host.is_default,
        "last_seen": host.last_seen.isoformat() if host.last_seen else None,
    }


@router.put("/hosts/{host_id}", response=ProxmoxHostResponse)
def update_host(request, host_id: int, payload: ProxmoxHostUpdate):
    """Update a Proxmox host configuration."""
    # 🔐 Authorization: Only admins can update Proxmox hosts
    if not request.user.is_authenticated or not request.user.is_staff:
        raise HttpError(403, "Admin privileges required to update Proxmox hosts")

    host = get_object_or_404(ProxmoxHost, id=host_id)
    
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(host, field, value)
    
    host.save()
    
    return {
        "id": host.id,
        "name": host.name,
        "host": host.host,
        "port": host.port,
        "user": host.user,
        "is_active": host.is_active,
        "is_default": host.is_default,
        "last_seen": host.last_seen.isoformat() if host.last_seen else None,
    }


@router.delete("/hosts/{host_id}")
def delete_host(request, host_id: int):
    """Delete a Proxmox host configuration."""
    # 🔐 Authorization: Only admins can delete Proxmox hosts
    if not request.user.is_authenticated or not request.user.is_staff:
        raise HttpError(403, "Admin privileges required to delete Proxmox hosts")

    host = get_object_or_404(ProxmoxHost, id=host_id)
    host.delete()
    return {"success": True, "message": f"Host {host.name} deleted"}


@router.post("/hosts/{host_id}/test", response=ConnectionTestResponse)
def test_host_connection(request, host_id: int):
    """Test connection to a Proxmox host."""
    # 🔐 Authorization: Only admins can test Proxmox host connections
    if not request.user.is_authenticated or not request.user.is_staff:
        raise HttpError(403, "Admin privileges required to test host connections")

    try:
        service = ProxmoxService(host_id=host_id)
        success = service.test_connection()
        return {
            "success": success,
            "message": "Connection successful" if success else "Connection failed"
        }
    except ProxmoxError as e:
        raise HttpError(503, f"Connection to Proxmox host failed: {str(e)}")


@router.post("/hosts/{host_id}/sync-nodes")
def sync_nodes(request, host_id: int):
    """Sync nodes from Proxmox API to database."""
    # 🔐 Authorization: Only admins can sync nodes
    if not request.user.is_authenticated or not request.user.is_staff:
        raise HttpError(403, "Admin privileges required to sync nodes")

    try:
        service = ProxmoxService(host_id=host_id)
        count = service.sync_nodes()
        return {"success": True, "message": f"Synced {count} nodes"}
    except ProxmoxError as e:
        raise HttpError(503, f"Failed to sync nodes from Proxmox: {str(e)}")


@router.get("/nodes", response=List[ProxmoxNodeResponse])
def list_nodes(request, host_id: int = None):
    """
    List all Proxmox nodes.
    Optionally filter by host_id.
    """
    # 🔐 Authorization: Only admins can view nodes
    if not request.user.is_authenticated or not request.user.is_staff:
        raise HttpError(403, "Admin privileges required to view Proxmox nodes")

    if host_id:
        nodes = ProxmoxNode.objects.filter(host_id=host_id)
    else:
        nodes = ProxmoxNode.objects.all()
    
    return [{
        "id": n.id,
        "host_name": n.host.name,
        "name": n.name,
        "status": n.status,
        "cpu_count": n.cpu_count,
        "cpu_usage": n.cpu_usage,
        "memory_total": n.memory_total,
        "memory_used": n.memory_used,
        "uptime": n.uptime,
    } for n in nodes]
