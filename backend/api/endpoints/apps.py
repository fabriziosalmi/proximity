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
from api.middleware.auth import get_current_user
from core.exceptions import (
    ProximityError,
    AppError,
    AppNotFoundError,
    AppAlreadyExistsError,
    AppDeploymentError,
    AppOperationError,
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


@router.get("/deploy/{app_id}/status", response_model=DeploymentStatus)
async def get_deployment_status(
    app_id: str,
    service: AppService = Depends(get_app_service)
):
    """Get real-time deployment status for an application"""
    try:
        status = await service.get_deployment_status(app_id)
        return status
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"Deployment status not found: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting deployment status for {app_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{app_id}/deployment-status", response_model=DeploymentStatus)
async def get_deployment_status(
    app_id: str,
    service: AppService = Depends(get_app_service)
):
    """Get deployment status for an app"""
    try:
        return await service.get_deployment_status(app_id)
    except (AppServiceError, AppNotFoundError) as e:
        logger.warning(f"Deployment status not found: {app_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting deployment status for {app_id}: {e}", exc_info=True)
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
            "timestamp": datetime.utcnow().isoformat()
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