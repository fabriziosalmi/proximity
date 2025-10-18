"""
Application API endpoints - Full CRUD and lifecycle management
"""
from typing import List
from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from django.db.models import Q
import uuid

from .models import Application, DeploymentLog
from .schemas import (
    ApplicationCreate, ApplicationResponse, ApplicationListResponse,
    ApplicationAction, ApplicationLogsResponse, DeploymentLogResponse
)
from .tasks import deploy_app_task, start_app_task, stop_app_task, restart_app_task, delete_app_task
from .port_manager import PortManagerService
from apps.proxmox.models import ProxmoxHost, ProxmoxNode

router = Router()


@router.get("/", response=ApplicationListResponse)
def list_applications(
    request,
    page: int = 1,
    per_page: int = 20,
    status: str = None,
    search: str = None
):
    """
    List all applications with optional filtering.
    
    Query params:
        page: Page number (default: 1)
        per_page: Items per page (default: 20)
        status: Filter by status
        search: Search by name or hostname
    """
    queryset = Application.objects.all()
    
    # Apply filters
    if status:
        queryset = queryset.filter(status=status)
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(hostname__icontains=search)
        )
    
    # Filter by user (non-admin users see only their apps)
    if request.user.is_authenticated and not request.user.is_staff:
        queryset = queryset.filter(owner=request.user)
    
    # Pagination
    total = queryset.count()
    start = (page - 1) * per_page
    end = start + per_page
    apps = queryset[start:end]
    
    return {
        "apps": [{
            "id": app.id,
            "catalog_id": app.catalog_id,
            "name": app.name,
            "hostname": app.hostname,
            "status": app.status,
            "url": app.url,
            "iframe_url": app.iframe_url,
            "public_port": app.public_port,
            "internal_port": app.internal_port,
            "lxc_id": app.lxc_id,
            "node": app.node,
            "host_id": app.host_id,
            "created_at": app.created_at.isoformat(),
            "updated_at": app.updated_at.isoformat(),
            "config": app.config,
            "environment": app.environment,
        } for app in apps],
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.post("/", response=ApplicationResponse)
def create_application(request, payload: ApplicationCreate):
    """
    Create and deploy a new application.
    
    This triggers a Celery task for the actual deployment.
    """
    # Validate hostname is unique
    if Application.objects.filter(hostname=payload.hostname).exists():
        raise HttpError(400, f"Hostname '{payload.hostname}' already exists")
    
    # Get or select Proxmox host
    if payload.node:
        # Find host that has this node
        node_obj = ProxmoxNode.objects.filter(name=payload.node).first()
        if not node_obj:
            raise HttpError(400, f"Node '{payload.node}' not found")
        host = node_obj.host
        node = payload.node
    else:
        # Select default host
        host = ProxmoxHost.objects.filter(is_default=True, is_active=True).first()
        if not host:
            host = ProxmoxHost.objects.filter(is_active=True).first()
        if not host:
            raise HttpError(400, "No active Proxmox host configured")
        
        # Select first available node
        node_obj = ProxmoxNode.objects.filter(host=host).first()
        if not node_obj:
            raise HttpError(400, "No nodes available on selected host")
        node = node_obj.name
    
    # Allocate ports
    port_manager = PortManagerService()
    try:
        public_port, internal_port = port_manager.allocate_ports()
    except ValueError as e:
        raise HttpError(500, str(e))
    
    # Generate unique app ID
    app_id = f"{payload.catalog_id}-{uuid.uuid4().hex[:8]}"
    
    # Create application record
    app = Application.objects.create(
        id=app_id,
        catalog_id=payload.catalog_id,
        name=payload.catalog_id,  # TODO: Get actual name from catalog
        hostname=payload.hostname,
        status='deploying',
        public_port=public_port,
        internal_port=internal_port,
        lxc_id=0,  # Will be set by deploy task
        node=node,
        host=host,
        config=payload.config,
        environment=payload.environment,
        owner=request.user if request.user.is_authenticated else None
    )
    
    # Trigger deployment task
    deploy_app_task.delay(
        app_id=app.id,
        catalog_id=app.catalog_id,
        hostname=app.hostname,
        host_id=host.id,
        node=node,
        config=payload.config,
        environment=payload.environment,
        owner_id=request.user.id if request.user.is_authenticated else None
    )
    
    return {
        "id": app.id,
        "catalog_id": app.catalog_id,
        "name": app.name,
        "hostname": app.hostname,
        "status": app.status,
        "url": app.url,
        "iframe_url": app.iframe_url,
        "public_port": app.public_port,
        "internal_port": app.internal_port,
        "lxc_id": app.lxc_id,
        "node": app.node,
        "host_id": app.host_id,
        "created_at": app.created_at.isoformat(),
        "updated_at": app.updated_at.isoformat(),
        "config": app.config,
        "environment": app.environment,
    }


@router.get("/{app_id}", response=ApplicationResponse)
def get_application(request, app_id: str):
    """Get application details."""
    app = get_object_or_404(Application, id=app_id)
    
    return {
        "id": app.id,
        "catalog_id": app.catalog_id,
        "name": app.name,
        "hostname": app.hostname,
        "status": app.status,
        "url": app.url,
        "iframe_url": app.iframe_url,
        "public_port": app.public_port,
        "internal_port": app.internal_port,
        "lxc_id": app.lxc_id,
        "node": app.node,
        "host_id": app.host_id,
        "created_at": app.created_at.isoformat(),
        "updated_at": app.updated_at.isoformat(),
        "config": app.config,
        "environment": app.environment,
    }


@router.post("/{app_id}/action")
def app_action(request, app_id: str, payload: ApplicationAction):
    """
    Perform an action on an application.
    
    Actions: start, stop, restart, delete
    """
    app = get_object_or_404(Application, id=app_id)
    
    action = payload.action.lower()
    
    if action == 'start':
        start_app_task.delay(app_id)
        return {"success": True, "message": f"Starting {app.name}"}
    
    elif action == 'stop':
        stop_app_task.delay(app_id)
        return {"success": True, "message": f"Stopping {app.name}"}
    
    elif action == 'restart':
        restart_app_task.delay(app_id)
        return {"success": True, "message": f"Restarting {app.name}"}
    
    elif action == 'delete':
        delete_app_task.delay(app_id)
        return {"success": True, "message": f"Deleting {app.name}"}
    
    else:
        return 400, {"error": f"Invalid action: {action}"}


@router.get("/{app_id}/logs", response=ApplicationLogsResponse)
def get_application_logs(request, app_id: str, limit: int = 50):
    """
    Get deployment logs for an application.
    
    Query params:
        limit: Maximum number of log entries (default: 50)
    """
    app = get_object_or_404(Application, id=app_id)
    
    logs = DeploymentLog.objects.filter(application=app).order_by('-timestamp')[:limit]
    
    return {
        "app_id": app.id,
        "logs": [{
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "level": log.level,
            "message": log.message,
            "step": log.step,
        } for log in logs],
        "total": logs.count()
    }
