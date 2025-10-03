from fastapi import APIRouter, Depends, HTTPException
import logging

from models.schemas import SystemInfo, NodeInfo, APIResponse
from services.proxmox_service import ProxmoxService, ProxmoxError, proxmox_service
from services.app_service import AppService, get_app_service
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return APIResponse(message="Proximity API is healthy")


@router.get("/info", response_model=SystemInfo)
async def get_system_info(
    proxmox: ProxmoxService = Depends(lambda: proxmox_service),
    app_service: AppService = Depends(get_app_service)
):
    """Get system information including nodes and app statistics"""
    try:
        # Get Proxmox nodes
        nodes = await proxmox.get_nodes()
        
        # Get app statistics
        apps = await app_service.get_all_apps()
        running_apps = len([app for app in apps if app.status.value == "running"])
        
        # Get LXC container count
        containers = await proxmox.get_lxc_containers()
        
        return SystemInfo(
            nodes=nodes,
            total_apps=len(apps),
            running_apps=running_apps,
            total_lxc=len(containers),
            version=settings.APP_VERSION
        )
        
    except ProxmoxError as e:
        logger.error(f"Proxmox error in system info: {e}")
        raise HTTPException(status_code=502, detail=f"Proxmox error: {e}")
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes", response_model=list[NodeInfo])
async def get_nodes(
    proxmox: ProxmoxService = Depends(lambda: proxmox_service)
):
    """Get list of Proxmox nodes"""
    try:
        return await proxmox.get_nodes()
    except ProxmoxError as e:
        logger.error(f"Failed to get nodes: {e}")
        raise HTTPException(status_code=502, detail=f"Proxmox error: {e}")
    except Exception as e:
        logger.error(f"Failed to get nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_name}")
async def get_node_info(
    node_name: str,
    proxmox: ProxmoxService = Depends(lambda: proxmox_service)
):
    """Get detailed information about a specific node"""
    try:
        return await proxmox.get_node_status(node_name)
    except ProxmoxError as e:
        logger.error(f"Failed to get node {node_name} info: {e}")
        raise HTTPException(status_code=502, detail=f"Proxmox error: {e}")
    except Exception as e:
        logger.error(f"Failed to get node {node_name} info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/containers")
async def get_containers(
    node: str = None,
    proxmox: ProxmoxService = Depends(lambda: proxmox_service)
):
    """Get list of LXC containers, optionally filtered by node"""
    try:
        return await proxmox.get_lxc_containers(node)
    except ProxmoxError as e:
        logger.error(f"Failed to get containers: {e}")
        raise HTTPException(status_code=502, detail=f"Proxmox error: {e}")
    except Exception as e:
        logger.error(f"Failed to get containers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection")
async def test_proxmox_connection(
    proxmox: ProxmoxService = Depends(lambda: proxmox_service)
):
    """Test connection to Proxmox API"""
    try:
        is_connected = await proxmox.test_connection()
        if is_connected:
            version_info = await proxmox.get_version()
            return APIResponse(
                message="Connection successful",
                data={
                    "connected": True,
                    "version": version_info
                }
            )
        else:
            raise HTTPException(status_code=502, detail="Connection failed")
            
    except ProxmoxError as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=502, detail=f"Proxmox error: {e}")
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_configuration():
    """Get current configuration (sanitized)"""
    return {
        "proxmox_host": settings.PROXMOX_HOST,
        "api_port": settings.API_PORT,
        "api_version": settings.API_VERSION,
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "default_lxc_template": settings.DEFAULT_LXC_TEMPLATE,
        "lxc_storage": settings.LXC_STORAGE,
        "lxc_memory": settings.LXC_MEMORY,
        "lxc_cores": settings.LXC_CORES,
        "lxc_disk_size": settings.LXC_DISK_SIZE,
        "lxc_bridge": settings.LXC_BRIDGE
    }


@router.get("/metrics")
async def get_metrics(
    proxmox: ProxmoxService = Depends(lambda: proxmox_service),
    app_service: AppService = Depends(get_app_service)
):
    """Get system metrics for monitoring"""
    try:
        # Get basic stats
        nodes = await proxmox.get_nodes()
        apps = await app_service.get_all_apps()
        containers = await proxmox.get_lxc_containers()
        
        # Calculate aggregated metrics
        total_cpu = sum(node.maxcpu or 0 for node in nodes)
        used_cpu = sum(node.cpu or 0 for node in nodes)
        total_memory = sum(node.maxmem or 0 for node in nodes)
        used_memory = sum(node.mem or 0 for node in nodes)
        
        app_status_counts = {}
        for app in apps:
            status = app.status.value
            app_status_counts[status] = app_status_counts.get(status, 0) + 1
        
        return {
            "timestamp": "now",  # In production, use actual timestamp
            "cluster": {
                "nodes": len(nodes),
                "total_cpu_cores": total_cpu,
                "used_cpu_percent": (used_cpu / total_cpu * 100) if total_cpu > 0 else 0,
                "total_memory_bytes": total_memory,
                "used_memory_bytes": used_memory,
                "used_memory_percent": (used_memory / total_memory * 100) if total_memory > 0 else 0
            },
            "applications": {
                "total": len(apps),
                "by_status": app_status_counts
            },
            "containers": {
                "total": len(containers),
                "running": len([c for c in containers if c.status.value == "running"]),
                "stopped": len([c for c in containers if c.status.value == "stopped"])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proxy/status")
async def get_proxy_status(
    app_service: AppService = Depends(get_app_service)
):
    """Get Caddy reverse proxy status"""
    try:
        # Check if Caddy service is initialized
        if app_service._caddy_service is None:
            return APIResponse(
                message="Reverse proxy not initialized",
                data={
                    "deployed": False,
                    "status": "not_deployed",
                    "message": "Caddy will be deployed automatically with the first app"
                }
            )
        
        # Check if Caddy is deployed
        is_deployed = app_service._caddy_service.is_deployed
        
        if not is_deployed:
            return APIResponse(
                message="Reverse proxy not deployed",
                data={
                    "deployed": False,
                    "status": "not_deployed",
                    "message": "Caddy will be deployed automatically with the first app"
                }
            )
        
        # Get Caddy status
        is_running = await app_service._caddy_service.is_caddy_running()
        caddy_ip = None
        app_count = 0
        
        # Get Caddy details (IP and app count) regardless of running status
        try:
            caddy_ip = await app_service._caddy_service.get_caddy_ip()
            # Count registered apps from config
            config = app_service._caddy_service.config
            app_count = len(config.apps)
        except Exception as e:
            logger.warning(f"Failed to get Caddy details: {e}")
        
        return APIResponse(
            message="Reverse proxy status retrieved",
            data={
                "deployed": True,
                "status": "running" if is_running else "stopped",
                "ip_address": caddy_ip,
                "registered_apps": app_count,
                "access_url": f"http://{caddy_ip}:8080/" if caddy_ip else None,
                "message": "Apps accessible via path-based routing (e.g., /app-name)"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get proxy status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/cache")
async def get_template_cache_status(
    proxmox: ProxmoxService = Depends(lambda: proxmox_service)
):
    """Get status of cached templates on all nodes"""
    try:
        nodes = await proxmox.get_nodes()
        cache_status = []
        
        for node in nodes:
            node_name = node.node
            
            # Get all storages for this node
            try:
                storage_list = await proxmox.get_node_storage(node_name)
                templates_found = []
                
                # Check each storage for templates
                for storage_info in storage_list:
                    storage_name = storage_info['storage']
                    try:
                        templates = await proxmox.get_available_templates(node_name, storage_name)
                        
                        # Filter for Alpine templates
                        alpine_templates = [
                            {
                                "volid": t,
                                "storage": storage_name,
                                "filename": t.split('/')[-1] if '/' in t else t
                            }
                            for t in templates 
                            if 'alpine' in t.lower()
                        ]
                        
                        templates_found.extend(alpine_templates)
                    except Exception as e:
                        logger.debug(f"Could not check storage {storage_name}: {e}")
                        continue
                
                cache_status.append({
                    "node": node_name,
                    "cached_templates": templates_found,
                    "template_count": len(templates_found),
                    "cache_hit_available": len(templates_found) > 0
                })
            except Exception as e:
                logger.warning(f"Could not check node {node_name}: {e}")
                cache_status.append({
                    "node": node_name,
                    "cached_templates": [],
                    "template_count": 0,
                    "cache_hit_available": False,
                    "error": str(e)
                })
        
        total_cached = sum(item['template_count'] for item in cache_status)
        
        return APIResponse(
            message=f"Template cache status: {total_cached} Alpine template(s) cached",
            data={
                "nodes": cache_status,
                "total_cached_templates": total_cached,
                "cache_enabled": True,
                "info": "Templates are automatically cached after first download and reused for all deployments"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get template cache status: {e}")
        raise HTTPException(status_code=500, detail=str(e))