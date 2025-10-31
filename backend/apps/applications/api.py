"""
Application API endpoints - Full CRUD and lifecycle management
"""

from typing import List
from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import transaction
import uuid

from .models import Application, DeploymentLog
from .schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationAction,
    ApplicationLogsResponse,
    ApplicationClone,
    ApplicationAdopt,
)
from .tasks import (
    deploy_app_task,
    start_app_task,
    stop_app_task,
    restart_app_task,
    delete_app_task,
    clone_app_task,
    adopt_app_task,
)
from .port_manager import PortManagerService
from apps.proxmox.models import ProxmoxNode

router = Router()


@router.get("/", response=ApplicationListResponse)
def list_applications(
    request, page: int = 1, per_page: int = 20, status: str = None, search: str = None
):
    """
    List all applications with optional filtering.

    Requires JWT authentication. Users see only their own apps (unless admin).

    Query params:
        page: Page number (default: 1)
        per_page: Items per page (default: 20)
        status: Filter by status
        search: Search by name or hostname
    """
    # 🔐 AUTHORIZATION: Require authentication
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required to list applications")

    import logging

    logger = logging.getLogger(__name__)

    # 🔧 OPTIMIZATION: Use select_related to avoid N+1 queries
    queryset = Application.objects.select_related("host").order_by("-created_at")

    # Apply filters
    if status:
        queryset = queryset.filter(status=status)

    if search:
        queryset = queryset.filter(Q(name__icontains=search) | Q(hostname__icontains=search))

    # Filter by user (non-admin users see only their apps)
    if request.user.is_authenticated and not request.user.is_staff:
        queryset = queryset.filter(owner=request.user)

    # Pagination
    total = queryset.count()
    start = (page - 1) * per_page
    end = start + per_page
    apps = queryset[start:end]

    # Build metrics map: {lxc_id: metrics_dict}
    # NOTE: Metrics fetching has been moved to separate endpoint for performance
    # The /metrics endpoint can be called separately to get real-time metrics
    # This keeps the list endpoint fast for UI
    metrics_map = {}

    # Build response with metrics
    return {
        "apps": [
            {
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
            }
            for app in apps
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("/", response=ApplicationResponse)
def create_application(request, payload: ApplicationCreate):
    """
    Create and deploy a new application.

    Requires JWT authentication. The app will be owned by the authenticated user.
    This triggers a Celery task for the actual deployment.
    """
    # 🔐 AUTHORIZATION: Require authentication
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required to create applications")

    # DEBUG: Log received payload
    import json
    import logging

    logger = logging.getLogger(__name__)

    logger.info("[API] Received deployment request:")
    logger.info(f"[API] catalog_id: {payload.catalog_id}")
    logger.info(f"[API] hostname: {payload.hostname}")
    logger.info(f"[API] Full payload: {json.dumps(payload.dict(), indent=2)}")

    # NOTE: Hostname uniqueness is enforced by the database unique constraint.
    # We'll catch IntegrityError if a race condition creates a duplicate.
    # This is safer than checking before creation (check-then-act race condition).

    # Get or select Proxmox host and node with intelligent selection
    if payload.node:
        # Explicit node specified - verify it's online
        node_obj = ProxmoxNode.objects.filter(name=payload.node, status="online").first()
        if not node_obj:
            # Check if node exists but is offline
            offline_node = ProxmoxNode.objects.filter(name=payload.node).first()
            if offline_node:
                raise HttpError(
                    400,
                    f"The specified node '{payload.node}' is not online (status: {offline_node.status})",
                )
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
            status="online", host__is_active=True
        ).select_related("host")

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

        print(
            f"[API] Smart node selection: {node} on host {host.name} (available memory: {max_available_memory / (1024**3):.2f} GB)"
        )

    # 🔐 TRANSACTION: Wrap port allocation and app creation with proper cleanup
    port_manager = PortManagerService()
    public_port = None
    internal_port = None
    app = None

    try:
        # Allocate ports
        try:
            public_port, internal_port = port_manager.allocate_ports()
        except ValueError as e:
            raise HttpError(500, str(e))

        # Generate unique app ID
        app_id = f"{payload.catalog_id}-{uuid.uuid4().hex[:8]}"

        # Create application record - wrapped in try/except to handle race conditions
        try:
            with transaction.atomic():
                app = Application.objects.create(
                    id=app_id,
                    catalog_id=payload.catalog_id,
                    name=payload.catalog_id,  # TODO: Get actual name from catalog
                    hostname=payload.hostname,
                    status="deploying",
                    public_port=public_port,
                    internal_port=internal_port,
                    lxc_id=None,  # Will be set by deploy task
                    node=node,
                    host=host,
                    config=payload.config,
                    environment=payload.environment,
                    owner=request.user if request.user.is_authenticated else None,
                )
                logger.info(f"[API] ✓ Application created successfully: {app_id}")

        except Exception as e:
            # Handle IntegrityError (likely hostname duplicate from race condition)
            from django.db import IntegrityError

            if isinstance(e, IntegrityError):
                # Release allocated ports on hostname conflict
                logger.warning(f"[API] ⚠️  IntegrityError (hostname likely duplicate): {str(e)}")
                if public_port and internal_port:
                    port_manager.release_ports(public_port, internal_port)
                    logger.info(
                        f"[API] Released ports {public_port}/{internal_port} due to hostname conflict"
                    )
                raise HttpError(
                    409, f"Hostname '{payload.hostname}' already exists (race condition detected)"
                )
            else:
                # Unknown error - release ports and re-raise
                if public_port and internal_port:
                    port_manager.release_ports(public_port, internal_port)
                raise

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
                owner_id=request.user.id if request.user.is_authenticated else None,
            )
        )

    except HttpError:
        # Already handled, re-raise
        raise
    except Exception as e:
        # Unexpected error - make sure ports are released
        logger.error(
            f"[API] ❌ Unexpected error during deployment creation: {str(e)}", exc_info=True
        )
        if public_port and internal_port:
            port_manager.release_ports(public_port, internal_port)
            logger.info(f"[API] Released ports {public_port}/{internal_port} due to error")
        # 🔐 Don't expose internal exception details to client
        raise HttpError(500, "Failed to create application. Please try again or contact support.")

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
    from apps.proxmox import ProxmoxService, ProxmoxError

    logger = logging.getLogger(__name__)

    try:
        service = ProxmoxService(host_id=host_id)
        unmanaged_containers = service.discover_unmanaged_lxc()

        logger.info(f"Discovery API: Found {len(unmanaged_containers)} unmanaged containers")
        return unmanaged_containers

    except ProxmoxError as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        # 🔐 Don't expose Proxmox connection details
        raise HttpError(503, "Failed to connect to Proxmox. Please check your connection settings.")
    except Exception as e:
        logger.error(f"Unexpected error during discovery: {e}", exc_info=True)
        # 🔐 Don't expose internal error details
        raise HttpError(500, "Discovery operation failed. Please try again or contact support.")


@router.post("/adopt", response={202: dict})
def adopt_existing_container(request, payload: ApplicationAdopt):
    """
    Adopt an existing LXC container into Proximity management.

    This endpoint imports a pre-existing container AS-IS, preserving its original
    configuration and hostname. The container is not forced to match catalog apps.

    Args:
        payload: ApplicationAdopt schema containing:
            - vmid: Container VMID to adopt
            - node_name: Node where container is running
            - suggested_type: Optional type hint for categorization (default: "custom")
            - port_to_expose: Optional port to expose (auto-detected if not provided)

    Returns:
        202 Accepted with adoption task information
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.info(
        f"[ADOPT API] Received adoption request for VMID {payload.vmid} on node {payload.node_name}"
    )

    try:
        # Quick validation: Check if container is already managed
        existing = Application.objects.filter(lxc_id=payload.vmid).first()
        if existing:
            logger.warning(
                f"[ADOPT API] Container {payload.vmid} already managed by Proximity as '{existing.hostname}'"
            )
            raise HttpError(409, f"Container {payload.vmid} is already managed by Proximity")

        # Quick validation: Verify node exists
        node = get_object_or_404(ProxmoxNode, name=payload.node_name)

        logger.info("[ADOPT API] Validations passed. Starting adoption task...")

        # Start adoption task in background
        adopt_app_task.delay(payload.dict())

        logger.info(f"[ADOPT API] Adoption task started successfully for VMID {payload.vmid}")

        # Return 202 Accepted - operation is async
        return 202, {
            "success": True,
            "message": f"Adoption of container {payload.vmid} started. The container will be imported with its original configuration.",
            "vmid": payload.vmid,
            "node": payload.node_name,
            "type": payload.suggested_type or "custom",
            "port_detection": (
                "automatic" if not payload.port_to_expose else f"manual:{payload.port_to_expose}"
            ),
        }

    except HttpError:
        raise
    except Exception as e:
        logger.error(f"[ADOPT API] Unexpected error: {e}", exc_info=True)
        # 🔐 Don't expose internal error details
        raise HttpError(500, "Failed to start adoption. Please try again or contact support.")


@router.get("/{app_id}", response=ApplicationResponse)
def get_application(request, app_id: str):
    """Get application details."""
    # 🔐 AUTHORIZATION: Only owner or admin can view application
    queryset = Application.objects.all()
    if request.user.is_authenticated and not request.user.is_staff:
        # Regular users can only see their own applications
        queryset = queryset.filter(owner=request.user)
    elif not request.user.is_authenticated:
        # Unauthenticated users cannot access any applications
        raise HttpError(401, "Authentication required")

    app = get_object_or_404(queryset, id=app_id)

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
        # 🔐 Metrics are optional and may not be available for all containers
        "cpu_usage": None,
        "memory_used": None,
        "memory_total": None,
        "disk_used": None,
        "disk_total": None,
    }


@router.post("/{app_id}/action")
def app_action(request, app_id: str, payload: ApplicationAction):
    """
    Perform an action on an application.

    Actions: start, stop, restart, delete
    """
    # 🔐 AUTHORIZATION: Only owner or admin can control application
    queryset = Application.objects.all()
    if request.user.is_authenticated and not request.user.is_staff:
        # Regular users can only control their own applications
        queryset = queryset.filter(owner=request.user)
    elif not request.user.is_authenticated:
        # Unauthenticated users cannot control applications
        raise HttpError(401, "Authentication required")

    app = get_object_or_404(queryset, id=app_id)

    action = payload.action.lower()

    if action == "start":
        start_app_task.delay(app_id)
        return {"success": True, "message": f"Starting {app.name}"}

    elif action == "stop":
        stop_app_task.delay(app_id)
        return {"success": True, "message": f"Stopping {app.name}"}

    elif action == "restart":
        restart_app_task.delay(app_id)
        return {"success": True, "message": f"Restarting {app.name}"}

    elif action == "delete":
        delete_app_task.delay(app_id)
        return {"success": True, "message": f"Deleting {app.name}"}

    else:
        # 🔐 CONSISTENCY: Use HttpError for all error responses
        raise HttpError(400, f"Invalid action: {action}")


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

    # 🔐 AUTHORIZATION: Only owner or admin can clone application
    queryset = Application.objects.all()
    if request.user.is_authenticated and not request.user.is_staff:
        # Regular users can only clone their own applications
        queryset = queryset.filter(owner=request.user)
    elif not request.user.is_authenticated:
        # Unauthenticated users cannot clone applications
        raise HttpError(401, "Authentication required")

    # Validate source application exists
    source_app = get_object_or_404(queryset, id=app_id)

    # Validate source app is in a stable state for cloning
    if source_app.status not in ["running", "stopped"]:
        raise HttpError(
            400,
            f"Cannot clone application in status '{source_app.status}'. Only running or stopped applications can be cloned.",
        )

    # NOTE: Hostname uniqueness is enforced by the database unique constraint.
    # The clone task will handle any race condition errors gracefully.

    # Get owner from request (use authenticated user or source app's owner)
    owner_id = request.user.id if request.user.is_authenticated else source_app.owner_id

    logger.info(
        f"[CLONE API] Initiating clone of {source_app.name} (ID: {app_id}) to new hostname: {payload.new_hostname}"
    )

    # Start clone task in background
    clone_app_task.delay(source_app_id=app_id, new_hostname=payload.new_hostname, owner_id=owner_id)

    logger.info("[CLONE API] Clone task started successfully")

    # Return 202 Accepted - operation is async
    return 202, {
        "success": True,
        "message": f"Cloning {source_app.name} to {payload.new_hostname}. This will take a few minutes.",
        "source_app_id": app_id,
        "new_hostname": payload.new_hostname,
    }


@router.get("/{app_id}/logs", response=ApplicationLogsResponse)
def get_application_logs(request, app_id: str, limit: int = 50):
    """
    Get deployment logs for an application.

    Query params:
        limit: Maximum number of log entries (default: 50)
    """
    # 🔐 AUTHORIZATION: Only owner or admin can view application logs
    queryset = Application.objects.all()
    if request.user.is_authenticated and not request.user.is_staff:
        # Regular users can only view their own application logs
        queryset = queryset.filter(owner=request.user)
    elif not request.user.is_authenticated:
        # Unauthenticated users cannot view logs
        raise HttpError(401, "Authentication required")

    app = get_object_or_404(queryset, id=app_id)

    logs = DeploymentLog.objects.filter(application=app).order_by("-timestamp")[:limit]

    return {
        "app_id": app.id,
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "step": log.step,
            }
            for log in logs
        ],
        "total": logs.count(),
    }
