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


@router.get("/network/status")
async def get_network_status():
    """
    Get status of the Proximity managed network infrastructure.
    
    Returns information about:
    - prox-net bridge status
    - NAT configuration
    - DHCP/DNS service status
    - Network configuration details
    """
    try:
        from services.network_manager import NetworkManager
        
        network_manager = NetworkManager()
        network_info = await network_manager.get_network_info()
        
        # Determine overall health status
        is_healthy = (
            network_info.get("bridge_up", False) and
            network_info.get("nat_configured", False) and
            network_info.get("dhcp_service_running", False)
        )
        
        status_msg = "Network infrastructure operational" if is_healthy else "Network infrastructure issues detected"
        
        return APIResponse(
            message=status_msg,
            data={
                **network_info,
                "health_status": "healthy" if is_healthy else "degraded",
                "info": "All application containers are provisioned on the isolated prox-net network"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get network status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INFRASTRUCTURE ENDPOINTS - DISABLED (network appliance removed)
# ============================================================================
# The following endpoints were part of the complex network appliance architecture
# that has been removed in favor of simple vmbr0 + DHCP networking.
# Keeping them commented for reference in case they're needed in the future.
#
# @router.get("/infrastructure/status")
# @router.post("/infrastructure/appliance/restart")  
# @router.get("/infrastructure/appliance/logs")
# @router.post("/infrastructure/test-nat")
# @router.post("/infrastructure/rebuild-bridge")
# ============================================================================


@router.get("/templates/cache")


# ============================================================================
# INFRASTRUCTURE ENDPOINTS - DISABLED (network appliance removed)
# ============================================================================
# The following endpoints were part of the complex network appliance architecture
# that has been removed in favor of simple vmbr0 + DHCP networking.
# ============================================================================



@router.post("/infrastructure/test-nat")
async def test_nat_connectivity():
    """
    Test NAT connectivity from the Network Appliance.

    Attempts to ping external hosts and verify DNS resolution
    to ensure NAT and routing are working correctly.
    """
    try:
        from main import app
        from services.proxmox_service import proxmox_service

        orchestrator = getattr(app.state, 'orchestrator', None)

        if not orchestrator or not orchestrator.appliance_info:
            raise HTTPException(
                status_code=404,
                detail="Network appliance not found"
            )

        vmid = orchestrator.appliance_info.vmid
        node = orchestrator.appliance_info.node

        logger.info(f"Testing NAT connectivity for appliance VMID {vmid}")

        # Test DNS resolution
        dns_test = await proxmox_service.exec_command(
            node, vmid,
            "nslookup google.com 2>&1 || echo 'DNS test failed'"
        )
        dns_working = "Address" in dns_test or "answer" in dns_test.lower()

        # Test internet connectivity
        ping_test = await proxmox_service.exec_command(
            node, vmid,
            "ping -c 3 -W 2 8.8.8.8 2>&1 || echo 'Ping failed'"
        )
        ping_working = "3 packets transmitted, 3 received" in ping_test or "0% packet loss" in ping_test

        # Check default route
        route_test = await proxmox_service.exec_command(
            node, vmid,
            "ip route show default 2>&1"
        )
        route_configured = "default via" in route_test

        # Check NAT rules
        nat_check = await proxmox_service.exec_command(
            node, vmid,
            "iptables -t nat -L POSTROUTING -n 2>&1 | grep -i masquerade || echo 'No NAT rules'"
        )
        nat_configured = "MASQUERADE" in nat_check

        overall_success = dns_working and ping_working and route_configured and nat_configured

        return APIResponse(
            message="NAT connectivity test complete" if overall_success else "NAT connectivity issues detected",
            data={
                "success": overall_success,
                "tests": {
                    "dns_resolution": {
                        "passed": dns_working,
                        "output": dns_test.strip()
                    },
                    "internet_connectivity": {
                        "passed": ping_working,
                        "output": ping_test.strip()
                    },
                    "default_route": {
                        "passed": route_configured,
                        "output": route_test.strip()
                    },
                    "nat_rules": {
                        "passed": nat_configured,
                        "output": nat_check.strip()
                    }
                },
                "timestamp": None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"NAT connectivity test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.post("/infrastructure/rebuild-bridge")
async def rebuild_network_bridge():
    """
    Rebuild the proximity-lan bridge on the Proxmox host.

    WARNING: This will temporarily disconnect all containers on the bridge.
    Use only if bridge configuration is corrupted or missing.
    """
    try:
        from main import app
        from services.proxmox_service import proxmox_service

        orchestrator = getattr(app.state, 'orchestrator', None)

        if not orchestrator or not orchestrator.appliance_info:
            raise HTTPException(
                status_code=404,
                detail="Network appliance not found"
            )

        node = orchestrator.appliance_info.node

        logger.warning(f"Rebuilding proximity-lan bridge on node {node}")

        # Execute bridge rebuild via orchestrator
        success = await orchestrator._ensure_bridge_exists(node)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to rebuild bridge. Check Proxmox host permissions."
            )

        # Restart appliance to apply new bridge configuration
        vmid = orchestrator.appliance_info.vmid
        await proxmox_service.stop_container(node, vmid)

        import asyncio
        await asyncio.sleep(2)

        await proxmox_service.start_container(node, vmid)

        logger.info(f"Bridge rebuilt and appliance restarted on node {node}")

        return APIResponse(
            message="Network bridge rebuilt successfully",
            data={
                "node": node,
                "bridge": "proximity-lan",
                "status": "rebuilt",
                "appliance_restarted": True,
                "note": "All containers on this bridge have been reconnected"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rebuild bridge: {e}")
        raise HTTPException(status_code=500, detail=f"Bridge rebuild failed: {str(e)}")
