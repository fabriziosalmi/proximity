from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from models.schemas import (
    App, AppCreate, AppUpdate, AppAction, AppList, 
    CatalogResponse, DeploymentStatus, APIResponse, ErrorResponse, SafeCommand
)
from models.database import AuditLog, get_db
from services.app_service import AppService, AppServiceError, get_app_service
from services.command_service import SafeCommandService, SafeCommandError, get_command_service
from services.monitoring_service import get_monitoring_service
from api.middleware.auth import get_current_user
from core.exceptions import (
    ProximityError,
    AppError,
    AppNotFoundError,
    AppAlreadyExistsError,
    AppDeploymentError,
    AppOperationError,
    AppUpdateError,
    CatalogError
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/catalog", response_model=CatalogResponse)
async def get_catalog(
    category: Optional[str] = Query(None, description="Filter by category"),
    service: AppService = Depends(get_app_service)
):
    """Get application catalog"""
    try:
        catalog = await service.get_catalog()
        
        if category:
            filtered_items = [item for item in catalog.items if item.category.lower() == category.lower()]
            catalog.items = filtered_items
            catalog.total = len(filtered_items)
        
        return catalog
    except CatalogError as e:
        logger.error(f"Catalog error: {e}", extra={"category": category})
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error getting catalog: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalog/{catalog_id}")
async def get_catalog_item(
    catalog_id: str,
    service: AppService = Depends(get_app_service)
):
    """Get specific catalog item"""
    try:
        return await service.get_catalog_item(catalog_id)
    except (AppServiceError, CatalogError, AppNotFoundError) as e:
        logger.warning(f"Catalog item not found: {catalog_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting catalog item {catalog_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[App])
@router.get("", response_model=List[App])
async def list_apps(
    status: Optional[str] = Query(None, description="Filter by status"),
    node: Optional[str] = Query(None, description="Filter by node"),
    service: AppService = Depends(get_app_service)
):
    """List all deployed applications"""
    try:
        apps = await service.get_all_apps()
        
        # Apply filters
        if status:
            apps = [app for app in apps if app.status.value == status]
        
        if node:
            apps = [app for app in apps if app.node == node]
        
        return apps
    except Exception as e:
        logger.error(f"Failed to list apps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{app_id}", response_model=App)
async def get_app(
    app_id: str,
    service: AppService = Depends(get_app_service)
):
    """Get specific application"""
    try:
        return await service.get_app(app_id)
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"App not found: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting app {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy", response_model=App)
async def deploy_app(
    app_data: AppCreate,
    background_tasks: BackgroundTasks,
    service: AppService = Depends(get_app_service)
):
    """Deploy a new application"""
    try:
        return await service.deploy_app(app_data)
    except AppAlreadyExistsError as e:
        logger.warning(f"App already exists: {app_data.catalog_id}-{app_data.hostname}")
        raise HTTPException(status_code=409, detail=str(e))
    except (AppDeploymentError, AppServiceError) as e:
        logger.error(f"Deployment failed: {e}", extra={"catalog_id": app_data.catalog_id, "hostname": app_data.hostname})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deploying app: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{app_id}/status", response_model=DeploymentStatus)
async def get_app_status(
    app_id: str,
    service: AppService = Depends(get_app_service)
):
    """
    Get unified application status.
    
    Returns intelligent status based on app state:
    - For running/stopped apps: Simple status response
    - For deploying/updating apps: Rich status with progress and current step
    
    This is the single source of truth for application state.
    """
    try:
        # First try to get detailed deployment status (for apps in transition)
        status = await service.get_deployment_status(app_id)
        return status
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"App status not found: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting app status for {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{app_id}", response_model=App)
async def update_app(
    app_id: str,
    app_update: AppUpdate,
    service: AppService = Depends(get_app_service)
):
    """Update an existing application"""
    try:
        return await service.update_app(app_id, app_update)
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"App not found for update: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating app {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{app_id}/actions", response_model=App)
async def perform_app_action(
    app_id: str,
    action: AppAction,
    service: AppService = Depends(get_app_service)
):
    """Perform action on application (start, stop, restart, rebuild)"""
    try:
        if action.action == "start":
            return await service.start_app(app_id)
        elif action.action == "stop":
            return await service.stop_app(app_id)
        elif action.action == "restart":
            return await service.restart_app(app_id)
        elif action.action == "rebuild":
            # Stop, redeploy with same config
            app = await service.get_app(app_id)
            await service.stop_app(app_id)
            # This would need more sophisticated rebuild logic
            return await service.start_app(app_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action.action}")
            
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"App not found for action: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AppOperationError as e:
        logger.error(f"Operation failed: {action.action} on {app_id}", extra={"app_id": app_id, "action": action.action})
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error performing action {action.action} on {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{app_id}")
async def delete_app(
    app_id: str,
    service: AppService = Depends(get_app_service)
):
    """Delete an application and its container"""
    try:
        await service.delete_app(app_id)
        return APIResponse(message=f"App {app_id} deleted successfully")
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"App not found for deletion: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AppOperationError as e:
        logger.error(f"Failed to delete app {app_id}: {e}", extra={"app_id": app_id})
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting app {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{app_id}/logs")
async def get_app_logs(
    app_id: str,
    lines: int = Query(100, description="Number of log lines to retrieve"),
    service: AppService = Depends(get_app_service)
):
    """Get application logs (from container)"""
    try:
        app = await service.get_app(app_id)
        
        # Get logs from the container using docker compose logs
        from services.proxmox_service import proxmox_service
        
        result = await proxmox_service.execute_in_container(
            app.node, 
            app.lxc_id, 
            f"cd /root && docker compose logs --tail={lines}"
        )
        
        return {"logs": result}
        
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"App not found for logs: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting logs for {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{app_id}/stats")
async def get_app_stats(
    app_id: str,
    service: AppService = Depends(get_app_service)
):
    """Get application resource usage statistics"""
    try:
        app = await service.get_app(app_id)
        
        from services.proxmox_service import proxmox_service
        
        # Get container stats
        lxc_status = await proxmox_service.get_lxc_status(app.node, app.lxc_id)
        
        return {
            "cpu_usage": lxc_status.cpu,
            "memory_usage": lxc_status.mem,
            "memory_max": lxc_status.maxmem,
            "disk_usage": lxc_status.disk,
            "disk_max": lxc_status.maxdisk,
            "network_in": lxc_status.netin,
            "network_out": lxc_status.netout,
            "uptime": lxc_status.uptime
        }
        
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"App not found for stats: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting stats for {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{app_id}/exec")
async def execute_command(
    app_id: str,
    command_data: dict,
    service: AppService = Depends(get_app_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Execute arbitrary command inside the application container.
    
    WARNING: This endpoint allows execution of any command and should be used with caution.
    It is intended for terminal/console functionality.
    """
    try:
        # Get app info
        app = await service.get_app(app_id)
        
        # Extract command from request
        command = command_data.get("command", "").strip()
        if not command:
            raise HTTPException(status_code=400, detail="Command is required")
        
        # Import proxmox service
        from services.proxmox_service import proxmox_service
        
        # Execute command in the container
        # cd to /root where docker-compose.yml typically is
        full_command = f"cd /root && {command}"
        
        try:
            result = await proxmox_service.execute_in_container(
                app.node, 
                app.lxc_id, 
                full_command,
                timeout=30,
                allow_nonzero_exit=True
            )
            
            return {
                "success": True,
                "output": result
            }
        except Exception as cmd_error:
            # Return error as output for display in terminal
            return {
                "success": False,
                "output": str(cmd_error),
                "error": str(cmd_error)
            }
        
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"App not found for exec: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error executing command in {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{app_id}/command/{command_name}")
async def execute_safe_command(
    app_id: str,
    command_name: SafeCommand,
    tail: Optional[int] = Query(100, ge=1, le=1000, description="Number of log lines for 'logs' command"),
    service_name: Optional[str] = Query(None, description="Service name for 'logs' command"),
    app_service: AppService = Depends(get_app_service),
    command_service: SafeCommandService = Depends(get_command_service),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a predefined safe command inside the application container.
    
    This endpoint replaces the dangerous /exec endpoint with secure,
    auditable command execution. Only predefined, read-only commands
    are allowed.
    
    Available commands:
    - logs: Get Docker Compose logs (supports 'tail' and 'service_name' params)
    - status: Get Docker Compose container status
    - disk: Get disk usage information
    - processes: Get list of running processes
    - memory: Get memory usage information
    - network: Get network interface information
    - images: Get list of Docker images
    - volumes: Get list of Docker volumes
    - config: Get Docker Compose configuration
    - system: Get system information
    """
    try:
        # Get app info
        app = await app_service.get_app(app_id)
        
        # Map command enum to service method
        command_map = {
            SafeCommand.LOGS: lambda: command_service.get_docker_logs(
                app.node, app.lxc_id, tail=tail, service=service_name
            ),
            SafeCommand.STATUS: lambda: command_service.get_container_status(
                app.node, app.lxc_id
            ),
            SafeCommand.DISK: lambda: command_service.get_disk_usage(
                app.node, app.lxc_id
            ),
            SafeCommand.PROCESSES: lambda: command_service.get_running_processes(
                app.node, app.lxc_id
            ),
            SafeCommand.MEMORY: lambda: command_service.get_memory_usage(
                app.node, app.lxc_id
            ),
            SafeCommand.NETWORK: lambda: command_service.get_network_info(
                app.node, app.lxc_id
            ),
            SafeCommand.IMAGES: lambda: command_service.get_docker_images(
                app.node, app.lxc_id
            ),
            SafeCommand.VOLUMES: lambda: command_service.get_docker_volumes(
                app.node, app.lxc_id
            ),
            SafeCommand.CONFIG: lambda: command_service.get_compose_config(
                app.node, app.lxc_id
            ),
            SafeCommand.SYSTEM: lambda: command_service.get_system_info(
                app.node, app.lxc_id
            )
        }
        
        # Execute the safe command
        command_func = command_map.get(command_name)
        if not command_func:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown command: {command_name}"
            )
        
        output = await command_func()
        
        # Audit log the command execution
        try:
            audit_entry = AuditLog(
                user_id=current_user.get("id"),
                username=current_user.get("username", "unknown"),
                action="execute_safe_command",
                resource_type="app",
                resource_id=app_id,
                details={
                    "command": command_name.value,
                    "app_name": app.name,
                    "lxc_id": app.lxc_id,
                    "node": app.node,
                    "parameters": {
                        "tail": tail if command_name == SafeCommand.LOGS else None,
                        "service": service_name if command_name == SafeCommand.LOGS else None
                    }
                },
                ip_address=None  # Could be extracted from request if needed
            )
            db.add(audit_entry)
            db.commit()
            logger.info(
                f"User '{current_user.get('username')}' executed command '{command_name.value}' "
                f"on app '{app_id}' (LXC {app.lxc_id})"
            )
        except Exception as audit_error:
            logger.error(f"Failed to create audit log entry: {audit_error}")
            # Don't fail the request if audit logging fails
        
        return {
            "success": True,
            "command": command_name.value,
            "app_id": app_id,
            "app_name": app.name,
            "output": output,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"App not found for command execution: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except SafeCommandError as e:
        logger.error(f"Safe command error: {e}", extra={"app_id": app_id, "command": command_name})
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error executing command '{command_name}' on {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")


@router.get("/{app_id}/commands")
async def list_available_commands(
    app_id: str,
    command_service: SafeCommandService = Depends(get_command_service),
    current_user: dict = Depends(get_current_user)
):
    """
    List all available safe commands that can be executed on this app.
    
    Returns a dictionary mapping command names to their descriptions.
    """
    return {
        "app_id": app_id,
        "available_commands": command_service.get_available_commands(),
        "note": "These commands are safe, read-only operations that do not modify the container."
    }


@router.post("/{app_id}/update", status_code=202)
async def update_app(
    app_id: str,
    service: AppService = Depends(get_app_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an application with fearless workflow:
    1. Create pre-update backup (safety net)
    2. Pull latest images
    3. Recreate containers
    4. Health check
    5. Auto-rollback on failure (future)

    Returns 202 Accepted as update is asynchronous.
    """
    try:
        logger.info(f"User {current_user.get('username')} initiated update for app {app_id}")

        # Call the update_app method (which is async and comprehensive)
        updated_app = await service.update_app(app_id, current_user.get("id"))

        return {
            "message": "Update completed successfully",
            "app_id": app_id,
            "status": updated_app.status,
            "updated_at": updated_app.updated_at
        }

    except AppNotFoundError as e:
        logger.error(f"App not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))

    except AppUpdateError as e:
        logger.error(f"Update failed for app {app_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error updating app {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get("/{app_id}/stats/current")
async def get_app_current_stats(
    app_id: str,
    service: AppService = Depends(get_app_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get current resource usage statistics for an application.

    This endpoint provides real-time CPU, RAM, and disk usage metrics
    with intelligent caching to ensure scalability.

    Performance Characteristics:
    - Cache-first design: Sub-millisecond response on cache hit
    - 10-second TTL prevents API abuse
    - Zero overhead when not actively monitored

    Args:
        app_id: Application ID
        service: Injected AppService
        current_user: Authenticated user from token

    Returns:
        Dict with current metrics:
        {
            "cpu_percent": 15.2,
            "mem_used_gb": 1.2,
            "mem_total_gb": 4.0,
            "mem_percent": 30.0,
            "disk_used_gb": 5.5,
            "disk_total_gb": 20.0,
            "disk_percent": 27.5,
            "uptime_seconds": 3600,
            "status": "running",
            "cached": true,
            "timestamp": "2025-10-04T12:34:56Z"
        }

    Raises:
        404: App not found
        500: Proxmox API error
    """
    try:
        # Get app from database
        app = await service.get_app(app_id)

        # Get monitoring service
        monitoring_service = get_monitoring_service(service.proxmox_service)

        # Fetch current stats (with caching)
        stats = await monitoring_service.get_current_app_stats(app)

        return stats

    except AppNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get stats for app {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.post("/{app_id}/clone", response_model=App, status_code=202)
async def clone_app(
    app_id: str,
    new_hostname: str = Query(..., description="Hostname for the cloned app"),
    service: AppService = Depends(get_app_service)
):
    """
    Clone an existing application.

    Creates a new LXC container with the same configuration as the source app
    and copies all persistent volumes to the new container.

    Args:
        app_id: Source application ID to clone
        new_hostname: Hostname for the new cloned application

    Returns:
        App: The newly cloned application

    Raises:
        404: Source app not found
        409: App with new_hostname already exists
        400: Clone operation failed
        500: Unexpected error

    Example:
        POST /apps/nginx-01/clone?new_hostname=nginx-02
    """
    try:
        logger.info(f"Cloning app {app_id} to {new_hostname}")
        cloned_app = await service.clone_app(app_id, new_hostname)
        return cloned_app
    except AppNotFoundError as e:
        logger.warning(f"Source app not found for cloning: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AppAlreadyExistsError as e:
        logger.warning(f"Target app already exists: {new_hostname}")
        raise HTTPException(status_code=409, detail=str(e))
    except AppOperationError as e:
        logger.error(f"Clone operation failed: {e}", extra={"source_app_id": app_id, "new_hostname": new_hostname})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error cloning app {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Clone failed: {str(e)}")


@router.put("/{app_id}/config", response_model=App)
async def update_app_config(
    app_id: str,
    cpu_cores: Optional[int] = Query(None, ge=1, le=16, description="Number of CPU cores"),
    memory_mb: Optional[int] = Query(None, ge=512, le=32768, description="Memory in MB"),
    disk_gb: Optional[int] = Query(None, ge=1, le=500, description="Disk size in GB"),
    service: AppService = Depends(get_app_service)
):
    """
    Update application resource configuration.

    Modifies CPU, memory, or disk allocation for a running application.
    The container will be restarted to apply changes.

    Args:
        app_id: Application ID to update
        cpu_cores: New CPU cores allocation (1-16)
        memory_mb: New memory allocation in MB (512-32768)
        disk_gb: New disk size in GB (1-500)

    Returns:
        App: Updated application

    Raises:
        404: App not found
        400: Invalid configuration or update failed
        500: Unexpected error

    Example:
        PUT /apps/nginx-01/config?cpu_cores=2&memory_mb=2048
    """
    try:
        logger.info(f"Updating config for app {app_id}: cpu={cpu_cores}, mem={memory_mb}, disk={disk_gb}")
        updated_app = await service.update_app_config(app_id, cpu_cores, memory_mb, disk_gb)
        return updated_app
    except AppNotFoundError as e:
        logger.warning(f"App not found for config update: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AppOperationError as e:
        logger.error(f"Config update failed: {e}", extra={"app_id": app_id})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating config for {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Config update failed: {str(e)}")