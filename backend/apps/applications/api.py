"""
Application API endpoints - Full CRUD and lifecycle management
"""
from typing import List
from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
import uuid

from .models import Application, DeploymentLog
from .schemas import (
    ApplicationCreate, ApplicationResponse, ApplicationListResponse,
    ApplicationAction, ApplicationLogsResponse, DeploymentLogResponse,
    ApplicationClone, ApplicationAdopt
)
from .tasks import deploy_app_task, start_app_task, stop_app_task, restart_app_task, delete_app_task, clone_app_task, adopt_app_task
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
    import logging
    from apps.proxmox.services import ProxmoxService
    
    logger = logging.getLogger(__name__)
    
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
    
    # Build metrics map: {lxc_id: metrics_dict}
    # Performance optimization: Fetch all metrics per node in batch
    metrics_map = {}
    
    try:
        # Group apps by node and host for efficient batch fetching
        nodes_apps = {}
        for app in apps:
            if app.status == 'running' and app.lxc_id:
                key = (app.host_id, app.node)
                if key not in nodes_apps:
                    nodes_apps[key] = []
                nodes_apps[key].append(app)
        
        # Fetch metrics for all running containers on each node
        for (host_id, node_name), node_apps in nodes_apps.items():
            try:
                proxmox_service = ProxmoxService(host_id=host_id)
                for app in node_apps:
                    try:
                        metrics = proxmox_service.get_lxc_metrics(node_name, app.lxc_id)
                        if metrics:
                            metrics_map[app.lxc_id] = metrics
                    except Exception as metrics_error:
                        logger.debug(f"Could not fetch metrics for container {app.lxc_id}: {metrics_error}")
                        # Continue with other containers even if one fails
            except Exception as node_error:
                logger.warning(f"Could not connect to Proxmox host {host_id}: {node_error}")
        
        logger.debug(f"Fetched metrics for {len(metrics_map)} running containers")
    
    except Exception as e:
        logger.warning(f"Error fetching metrics: {e}")
        # Continue without metrics if there's an error
    
    # Build response with metrics
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
            # Add metrics from our pre-built map (no additional API call per app!)
            "cpu_usage": metrics_map.get(app.lxc_id, {}).get("cpu_usage"),
            "memory_used": metrics_map.get(app.lxc_id, {}).get("memory_used"),
            "memory_total": metrics_map.get(app.lxc_id, {}).get("memory_total"),
            "disk_used": metrics_map.get(app.lxc_id, {}).get("disk_used"),
            "disk_total": metrics_map.get(app.lxc_id, {}).get("disk_total"),
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
    # DEBUG: Log received payload
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[API] Received deployment request:")
    logger.info(f"[API] catalog_id: {payload.catalog_id}")
    logger.info(f"[API] hostname: {payload.hostname}")
    logger.info(f"[API] Full payload: {json.dumps(payload.dict(), indent=2)}")
    
    # Validate hostname is unique
    if Application.objects.filter(hostname=payload.hostname).exists():
        raise HttpError(400, f"Hostname '{payload.hostname}' already exists")
    
    # Get or select Proxmox host and node with intelligent selection
    if payload.node:
        # Explicit node specified - verify it's online
        node_obj = ProxmoxNode.objects.filter(name=payload.node, status='online').first()
        if not node_obj:
            # Check if node exists but is offline
            offline_node = ProxmoxNode.objects.filter(name=payload.node).first()
            if offline_node:
                raise HttpError(400, f"The specified node '{payload.node}' is not online (status: {offline_node.status})")
            else:
                raise HttpError(400, f"The specified node '{payload.node}' does not exist")
        
        host = node_obj.host
        node = payload.node
    else:
        # No node specified - intelligent selection
        # Strategy: Select the online node with most available memory
        
        logger.info("🔍 Starting smart node selection...")
        
        # Get all online nodes across all active hosts
        online_nodes = ProxmoxNode.objects.filter(
            status='online',
            host__is_active=True
        ).select_related('host')
        
        logger.info(f"📊 Found {online_nodes.count()} online nodes across active hosts")
        
        # Log details of each candidate node
        for node_obj in online_nodes:
            if node_obj.memory_total and node_obj.memory_used is not None:
                free_gb = (node_obj.memory_total - node_obj.memory_used) / (1024**3)
                logger.info(
                    f"   - Node '{node_obj.name}': "
                    f"status={node_obj.status}, "
                    f"host={node_obj.host.name}, "
                    f"host_active={node_obj.host.is_active}, "
                    f"free_memory={free_gb:.2f}GB"
                )
            else:
                logger.info(
                    f"   - Node '{node_obj.name}': "
                    f"status={node_obj.status}, "
                    f"host={node_obj.host.name}, "
                    f"host_active={node_obj.host.is_active}, "
                    f"free_memory=UNKNOWN"
                )
        
        if not online_nodes.exists():
            logger.error("❌ No online Proxmox nodes available for deployment")
            raise HttpError(503, "No online Proxmox nodes available for deployment")
        
        # Select node with most available memory (best for load balancing)
        best_node = None
        max_available_memory = -1
        
        for node_obj in online_nodes:
            # Calculate available memory (total - used)
            if node_obj.memory_total and node_obj.memory_used is not None:
                available = node_obj.memory_total - node_obj.memory_used
                if available > max_available_memory:
                    max_available_memory = available
                    best_node = node_obj
        
        # Fallback: if no memory info, just pick first online node
        if not best_node:
            logger.warning("⚠️  No memory info available, using first online node")
            best_node = online_nodes.first()
        else:
            free_gb = max_available_memory / (1024**3)
            logger.info(
                f"✅ Selected node '{best_node.name}' with {free_gb:.2f}GB free memory "
                f"(host: {best_node.host.name})"
            )
        
        host = best_node.host
        node = best_node.name
        
        print(f"[API] Smart node selection: {node} on host {host.name} (available memory: {max_available_memory / (1024**3):.2f} GB)")
    
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
        lxc_id=None,  # Will be set by deploy task
        node=node,
        host=host,
        config=payload.config,
        environment=payload.environment,
        owner=request.user if request.user.is_authenticated else None
    )
    
    # Trigger deployment task AFTER transaction commits to avoid race condition
    # This ensures the Application record is available in the database before the task runs
    transaction.on_commit(
        lambda: deploy_app_task.delay(
            app_id=app.id,
            catalog_id=app.catalog_id,
            hostname=app.hostname,
            host_id=host.id,
            node=node,
            config=payload.config,
            environment=payload.environment,
            owner_id=request.user.id if request.user.is_authenticated else None
        )
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


@router.get("/discover", response=List[dict])
def discover_unmanaged_containers(request, host_id: int = None):
    """
    Discover LXC containers that exist on Proxmox but are not managed by Proximity.
    
    This endpoint scans all Proxmox nodes and returns containers that could be adopted.
    
    Query params:
        host_id: Optional Proxmox host ID (uses default if not specified)
    
    Returns:
        List of unmanaged containers with their basic information
    """
    import logging
    from apps.proxmox.services import ProxmoxService, ProxmoxError
    
    logger = logging.getLogger(__name__)
    
    try:
        service = ProxmoxService(host_id=host_id)
        unmanaged_containers = service.discover_unmanaged_lxc()
        
        logger.info(f"Discovery API: Found {len(unmanaged_containers)} unmanaged containers")
        return unmanaged_containers
        
    except ProxmoxError as e:
        logger.error(f"Discovery failed: {e}")
        raise HttpError(500, f"Discovery failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during discovery: {e}")
        raise HttpError(500, f"Unexpected error: {str(e)}")


@router.post("/adopt", response={202: dict})
def adopt_existing_container(request, payload: ApplicationAdopt):
    """
    Adopt an existing LXC container into Proximity management.
    
    This endpoint validates the request and triggers an asynchronous adoption process.
    The actual adoption happens in a background Celery task.
    
    Args:
        payload: ApplicationAdopt schema containing:
            - vmid: Container VMID to adopt
            - node_name: Node where container is running
            - catalog_id: Catalog app ID that matches this container
            - hostname: Optional custom hostname (defaults to container name)
            - container_port_to_expose: Internal port the container listens on
    
    Returns:
        202 Accepted with adoption task information
    """
    import logging
    from apps.catalog.services import CatalogService
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"[ADOPT API] Received adoption request for VMID {payload.vmid} on node {payload.node_name}")
    
    try:
        # Quick validation: Check if container is already managed
        existing = Application.objects.filter(lxc_id=payload.vmid).first()
        if existing:
            logger.warning(f"[ADOPT API] Container {payload.vmid} already managed by Proximity as '{existing.hostname}'")
            raise HttpError(409, f"Container {payload.vmid} is already managed by Proximity")
        
        # Quick validation: Verify catalog app exists
        catalog_service = CatalogService()
        catalog_app = catalog_service.get_app_by_id(payload.catalog_id)
        
        if not catalog_app:
            logger.warning(f"[ADOPT API] Catalog app '{payload.catalog_id}' not found")
            raise HttpError(404, f"Catalog app '{payload.catalog_id}' not found")
        
        # Quick validation: Verify node exists
        node = get_object_or_404(ProxmoxNode, name=payload.node_name)
        
        logger.info(f"[ADOPT API] Validations passed. Starting adoption task...")
        
        # Start adoption task in background
        adopt_app_task.delay(payload.dict())
        
        logger.info(f"[ADOPT API] Adoption task started successfully for VMID {payload.vmid}")
        
        # Return 202 Accepted - operation is async
        return 202, {
            "success": True,
            "message": f"Adoption of container {payload.vmid} started. This will take a few moments.",
            "vmid": payload.vmid,
            "node": payload.node_name,
            "catalog_id": payload.catalog_id,
            "hostname": payload.hostname or f"container-{payload.vmid}"
        }
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"[ADOPT API] Unexpected error: {e}", exc_info=True)
        raise HttpError(500, f"Failed to start adoption: {str(e)}")


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


@router.post("/{app_id}/clone", response={202: dict})
def clone_application(request, app_id: str, payload: ApplicationClone):
    """
    Clone an existing application.
    
    Creates a duplicate of the application with a new hostname.
    Returns 202 Accepted immediately - the actual cloning happens in background.
    
    Args:
        app_id: Source application ID to clone
        payload: Contains new_hostname for the clone
        
    Returns:
        202 Accepted with message and task information
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate source application exists
    source_app = get_object_or_404(Application, id=app_id)
    
    # Validate source app is in a stable state for cloning
    if source_app.status not in ['running', 'stopped']:
        raise HttpError(400, f"Cannot clone application in status '{source_app.status}'. Only running or stopped applications can be cloned.")
    
    # Validate new hostname is unique
    if Application.objects.filter(hostname=payload.new_hostname).exists():
        raise HttpError(400, f"Hostname '{payload.new_hostname}' already exists")
    
    # Get owner from request (use authenticated user or source app's owner)
    owner_id = request.user.id if request.user.is_authenticated else source_app.owner_id
    
    logger.info(f"[CLONE API] Initiating clone of {source_app.name} (ID: {app_id}) to new hostname: {payload.new_hostname}")
    
    # Start clone task in background
    clone_app_task.delay(
        source_app_id=app_id,
        new_hostname=payload.new_hostname,
        owner_id=owner_id
    )
    
    logger.info(f"[CLONE API] Clone task started successfully")
    
    # Return 202 Accepted - operation is async
    return 202, {
        "success": True,
        "message": f"Cloning {source_app.name} to {payload.new_hostname}. This will take a few minutes.",
        "source_app_id": app_id,
        "new_hostname": payload.new_hostname
    }


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
