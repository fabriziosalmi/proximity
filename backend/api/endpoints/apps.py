from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional
import logging

from models.schemas import (
    App, AppCreate, AppUpdate, AppAction, AppList, 
    CatalogResponse, DeploymentStatus, APIResponse, ErrorResponse
)
from services.app_service import AppService, AppServiceError, get_app_service

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
    except Exception as e:
        logger.error(f"Failed to get catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalog/{catalog_id}")
async def get_catalog_item(
    catalog_id: str,
    service: AppService = Depends(get_app_service)
):
    """Get specific catalog item"""
    try:
        return await service.get_catalog_item(catalog_id)
    except AppServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get catalog item {catalog_id}: {e}")
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
    except AppServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get app {app_id}: {e}")
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
    except AppServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to deploy app: {e}")
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
    except AppServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get deployment status for {app_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{app_id}/deployment-status", response_model=DeploymentStatus)
async def get_deployment_status(
    app_id: str,
    service: AppService = Depends(get_app_service)
):
    """Get deployment status for an app"""
    try:
        return await service.get_deployment_status(app_id)
    except AppServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get deployment status for {app_id}: {e}")
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
    except AppServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update app {app_id}: {e}")
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
            
    except AppServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to perform action {action.action} on app {app_id}: {e}")
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
    except AppServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete app {app_id}: {e}")
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
        
    except AppServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get logs for app {app_id}: {e}")
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
        
    except AppServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get stats for app {app_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{app_id}/exec")
async def execute_command_in_app(
    app_id: str,
    command_data: dict,
    service: AppService = Depends(get_app_service)
):
    """Execute a command inside the application container"""
    try:
        app = await service.get_app(app_id)
        command = command_data.get("command", "").strip()
        
        if not command:
            raise HTTPException(status_code=400, detail="Command is required")
        
        # Security: Command validation (HARDENED)
        dangerous_patterns = [';', '&&', '||', '|', '>', '>>', '<', '`', '$(', 'rm ', 'wget', 'curl', 'nc ', 'bash', 'sh ', '/bin/']
        if any(pattern in command for pattern in dangerous_patterns):
            raise HTTPException(
                status_code=400,
                detail=f"Command contains dangerous pattern. Use predefined safe actions instead."
            )
        
        from services.proxmox_service import proxmox_service
        
        # Execute command in container
        result = await proxmox_service.execute_in_container(
            app.node,
            app.lxc_id,
            command
        )
        
        return {
            "success": True,
            "output": result,
            "command": command
        }
        
    except AppServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute command in app {app_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": command_data.get("command", "")
        }