# Smart Infrastructure Cleanup - Integration Guide

## Overview

This guide explains how to integrate smart cleanup of the network infrastructure when deleting applications. The infrastructure (proximity-lan bridge and network appliance) should only be removed when the last application is deleted.

---

## Behavior

### When Deleting an App

**If there are other apps running:**
```
1. Delete app LXC container
2. Remove reverse proxy vhost
3. Keep infrastructure running
4. Return success
```

**If this is the last app:**
```
1. Delete app LXC container
2. Remove reverse proxy vhost
3. Stop and delete network appliance (VMID 100)
4. Remove proximity-lan bridge
5. Clean up configuration files
6. Return success
```

---

## Implementation

### 1. Modified App Deletion Flow

```python
# In app_service.py or app lifecycle handler

async def delete_app(self, app_name: str, vmid: int) -> dict:
    """
    Delete an application and clean up infrastructure if needed.
    
    Args:
        app_name: Name of the application
        vmid: VMID of the LXC container
        
    Returns:
        dict: Deletion result with cleanup info
    """
    try:
        logger.info(f"Deleting application: {app_name}")
        
        # Step 1: Remove reverse proxy vhost
        if hasattr(self, 'proxy_manager'):
            logger.info(f"Removing vhost for {app_name}...")
            await self.proxy_manager.delete_vhost(app_name)
        
        # Step 2: Delete LXC container
        logger.info(f"Deleting LXC container {vmid}...")
        await self.proxmox.delete_lxc(vmid)
        
        # Step 3: Check if infrastructure cleanup is needed
        cleanup_performed = False
        if hasattr(self, 'orchestrator'):
            logger.info("Checking if infrastructure cleanup needed...")
            cleanup_performed = await self.orchestrator.cleanup_if_empty()
        
        result = {
            'app_name': app_name,
            'vmid': vmid,
            'deleted': True,
            'infrastructure_cleaned': cleanup_performed
        }
        
        if cleanup_performed:
            logger.info("✓ Last application removed - infrastructure cleaned up")
            result['message'] = "Application deleted and infrastructure cleaned up (was last app)"
        else:
            logger.info("✓ Application deleted - infrastructure still in use")
            result['message'] = "Application deleted successfully"
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to delete app {app_name}: {e}")
        raise
```

### 2. Orchestrator Cleanup Method

The `NetworkApplianceOrchestrator` already includes the cleanup logic:

```python
async def cleanup_if_empty(self) -> bool:
    """
    Clean up network infrastructure if no applications are connected.
    
    Steps:
    1. Count remaining applications (via DHCP leases)
    2. If > 0: do nothing, return False
    3. If = 0: clean up appliance and bridge, return True
    
    Returns:
        bool: True if cleanup was performed, False if infrastructure still in use
    """
    try:
        # Count remaining apps
        app_count = await self.count_connected_apps()
        
        if app_count > 0:
            logger.info(f"Infrastructure still in use ({app_count} apps remaining)")
            return False
        
        logger.info("Last application removed, cleaning up infrastructure...")
        
        # Stop and delete appliance LXC
        if self.appliance_info:
            await self._cleanup_appliance(self.appliance_info.vmid)
        
        # Remove bridge
        await self._cleanup_bridge()
        
        # Reset state
        self.appliance_info = None
        
        logger.info("✓ Infrastructure cleanup complete")
        return True
        
    except Exception as e:
        logger.error(f"Failed to cleanup infrastructure: {e}")
        return False
```

### 3. Counting Connected Apps

The orchestrator determines if cleanup is needed by checking DHCP leases:

```python
async def count_connected_apps(self) -> int:
    """
    Count applications by reading DHCP leases from dnsmasq.
    
    Returns:
        int: Number of active DHCP leases
    """
    try:
        apps = await self._get_connected_applications()
        return len(apps)
    except Exception as e:
        logger.error(f"Failed to count connected apps: {e}")
        return 0

async def _get_connected_applications(self) -> List[Dict[str, Any]]:
    """Read dnsmasq leases file to get active applications."""
    try:
        if not self.appliance_info:
            return []
        
        # Read DHCP leases file
        leases_cmd = "cat /var/lib/misc/dnsmasq.leases 2>/dev/null || echo ''"
        result = await self._exec_in_lxc(self.appliance_info.vmid, leases_cmd)
        
        if result.get('exitcode') != 0:
            return []
        
        apps = []
        leases = result.get('output', '').strip().split('\n')
        
        for lease in leases:
            if not lease:
                continue
            
            # Parse lease: timestamp mac ip hostname client-id
            parts = lease.split()
            if len(parts) >= 4:
                apps.append({
                    'ip': parts[2],
                    'hostname': parts[3],
                    'mac': parts[1],
                    'lease_expires': parts[0],
                    'dns_name': f"{parts[3]}.prox.local"
                })
        
        return apps
        
    except Exception as e:
        logger.debug(f"Could not get connected applications: {e}")
        return []
```

---

## API Endpoint Modification

### Delete App Endpoint

```python
# In api/endpoints/apps.py

@router.delete("/{app_name}")
async def delete_app(
    app_name: str,
    app_service: AppService = Depends(get_app_service)
):
    """
    Delete an application.
    
    Automatically cleans up network infrastructure if this is the last app.
    """
    try:
        # Get app details
        app = await app_service.get_app(app_name)
        if not app:
            raise HTTPException(status_code=404, detail=f"App {app_name} not found")
        
        # Delete app with smart cleanup
        result = await app_service.delete_app(app_name, app.vmid)
        
        return APIResponse(
            message=result.get('message', 'Application deleted'),
            data={
                'app_name': app_name,
                'infrastructure_cleaned': result.get('infrastructure_cleaned', False)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to delete app: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Infrastructure Status Page

### API Endpoint

```python
@router.get("/infrastructure/status")
async def get_infrastructure_status():
    """
    Get comprehensive infrastructure status.
    
    Returns:
    - Appliance information (status, IPs, resources)
    - Bridge configuration
    - Network settings
    - Service status (DHCP, DNS, NAT, Caddy, Cockpit)
    - Connected applications with IPs
    - Network statistics
    """
    try:
        from main import app
        orchestrator = app.state.orchestrator
        
        # Get comprehensive status
        infrastructure = await orchestrator.get_infrastructure_status()
        
        return APIResponse(
            message="Infrastructure status retrieved",
            data=infrastructure
        )
        
    except Exception as e:
        logger.error(f"Failed to get infrastructure status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Response Format

```json
{
  "message": "Infrastructure status retrieved",
  "data": {
    "appliance": {
      "vmid": 100,
      "hostname": "prox-appliance",
      "status": "running",
      "wan_ip": "192.168.1.150",
      "wan_interface": "eth0",
      "lan_ip": "10.20.0.1",
      "lan_interface": "eth1",
      "management_url": "http://192.168.1.150:9090",
      "resources": {
        "cpu_cores": 2,
        "memory_mb": 1024,
        "storage_gb": 8,
        "status": "running"
      }
    },
    "bridge": {
      "name": "proximity-lan",
      "exists": true,
      "status": "UP",
      "type": "bridge"
    },
    "network": {
      "bridge_name": "proximity-lan",
      "network": "10.20.0.0/24",
      "gateway": "10.20.0.1",
      "netmask": "255.255.255.0",
      "dhcp_range": "10.20.0.100 - 10.20.0.250",
      "dns_domain": "prox.local"
    },
    "services": {
      "dnsmasq": {
        "name": "DHCP/DNS Server",
        "status": "running",
        "healthy": true
      },
      "iptables": {
        "name": "NAT Firewall",
        "status": "running",
        "healthy": true
      },
      "caddy": {
        "name": "Reverse Proxy",
        "status": "running",
        "healthy": true
      },
      "cockpit": {
        "name": "Management UI",
        "status": "stopped",
        "healthy": false
      }
    },
    "applications": [
      {
        "ip": "10.20.0.101",
        "hostname": "nginx-01",
        "mac": "BC:24:11:XX:XX:XX",
        "lease_expires": "1696348800",
        "dns_name": "nginx-01.prox.local"
      },
      {
        "ip": "10.20.0.102",
        "hostname": "wordpress",
        "mac": "BC:24:11:YY:YY:YY",
        "lease_expires": "1696348900",
        "dns_name": "wordpress.prox.local"
      }
    ],
    "statistics": {
      "interface": "eth1",
      "network": "10.20.0.0/24",
      "gateway": "10.20.0.1",
      "active_leases": 2,
      "available_ips": 151
    },
    "health_status": "healthy"
  }
}
```

---

## Frontend Infrastructure Page

### Component Structure

```typescript
// InfrastructurePage.tsx

interface InfrastructureStatus {
  appliance: ApplianceInfo;
  bridge: BridgeInfo;
  network: NetworkConfig;
  services: ServiceStatus;
  applications: Application[];
  statistics: NetworkStats;
  health_status: 'healthy' | 'degraded' | 'not_initialized';
}

function InfrastructurePage() {
  const [status, setStatus] = useState<InfrastructureStatus | null>(null);
  
  useEffect(() => {
    fetchInfrastructureStatus();
    
    // Refresh every 10 seconds
    const interval = setInterval(fetchInfrastructureStatus, 10000);
    return () => clearInterval(interval);
  }, []);
  
  async function fetchInfrastructureStatus() {
    const response = await fetch('/api/v1/system/infrastructure/status');
    const data = await response.json();
    setStatus(data.data);
  }
  
  return (
    <div className="infrastructure-page">
      <h1>Network Infrastructure</h1>
      
      {/* Overall Health */}
      <HealthBadge status={status?.health_status} />
      
      {/* Network Appliance Card */}
      <ApplianceCard appliance={status?.appliance} />
      
      {/* Network Configuration Card */}
      <NetworkCard network={status?.network} bridge={status?.bridge} />
      
      {/* Services Grid */}
      <ServicesGrid services={status?.services} />
      
      {/* Connected Applications Table */}
      <ApplicationsTable apps={status?.applications} />
      
      {/* Network Statistics */}
      <StatisticsCard stats={status?.statistics} />
    </div>
  );
}
```

### Sample UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Network Infrastructure                          [●] Healthy  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Network Appliance (prox-appliance)                    │   │
│ │                                                       │   │
│ │ Status: ● Running           VMID: 100                │   │
│ │ Management IP: 192.168.1.150                         │   │
│ │ LAN Gateway: 10.20.0.1                               │   │
│ │ Resources: 2 CPU | 1GB RAM | 8GB Storage             │   │
│ │                                                       │   │
│ │ [Open Management UI :9090]                           │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Network Configuration                                 │   │
│ │                                                       │   │
│ │ Bridge: proximity-lan (UP)                           │   │
│ │ Network: 10.20.0.0/24                                │   │
│ │ Gateway: 10.20.0.1                                   │   │
│ │ DHCP Range: 10.20.0.100 - 10.20.0.250               │   │
│ │ DNS Domain: .prox.local                              │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Services                                              │   │
│ │                                                       │   │
│ │ DHCP/DNS Server      ● Running                       │   │
│ │ NAT Firewall         ● Running                       │   │
│ │ Reverse Proxy        ● Running                       │   │
│ │ Management UI        ○ Stopped                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Connected Applications (2)                            │   │
│ │                                                       │   │
│ │ ┌────────────┬──────────────┬────────────────────┐   │   │
│ │ │ Hostname   │ IP Address   │ DNS Name          │   │   │
│ │ ├────────────┼──────────────┼────────────────────┤   │   │
│ │ │ nginx-01   │ 10.20.0.101 │ nginx-01.prox.local│   │   │
│ │ │ wordpress  │ 10.20.0.102 │ wordpress.prox.local│  │   │
│ │ └────────────┴──────────────┴────────────────────┘   │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Network Statistics                                    │   │
│ │                                                       │   │
│ │ Active DHCP Leases: 2                                │   │
│ │ Available IPs: 151                                   │   │
│ │ Utilization: 1.3%                                    │   │
│ └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Testing Scenarios

### Scenario 1: Delete Non-Last App

```bash
# Initial state: 3 apps running
curl http://localhost:8765/api/v1/system/infrastructure/status
# Response: applications: [app1, app2, app3]

# Delete app1
curl -X DELETE http://localhost:8765/api/v1/apps/app1
# Response: { "infrastructure_cleaned": false }

# Check infrastructure
curl http://localhost:8765/api/v1/system/infrastructure/status
# Response: applications: [app2, app3] (infrastructure still up)
```

### Scenario 2: Delete Last App

```bash
# Initial state: 1 app running
curl http://localhost:8765/api/v1/system/infrastructure/status
# Response: applications: [app1]

# Delete app1 (last app)
curl -X DELETE http://localhost:8765/api/v1/apps/app1
# Response: { "infrastructure_cleaned": true }

# Check infrastructure
curl http://localhost:8765/api/v1/system/infrastructure/status
# Response: { "health_status": "not_initialized", "appliance": null }

# Check bridge
ssh root@proxmox "ip link show proximity-lan"
# Result: "Device does not exist" (bridge removed)
```

### Scenario 3: Deploy After Cleanup

```bash
# Deploy new app after cleanup
curl -X POST http://localhost:8765/api/v1/apps/deploy \
  -d '{"name": "nginx", "template": "nginx"}'

# Infrastructure auto-initializes
# - proximity-lan bridge created
# - Network appliance deployed
# - Services configured
# - App deployed and accessible
```

---

## Benefits

### 1. Resource Efficiency
- No idle infrastructure when no apps are running
- Automatic cleanup saves resources (1GB RAM, 2 CPU cores)
- Bridge removed when not needed

### 2. Clean State
- Fresh infrastructure for each deployment cycle
- No stale configurations
- Predictable behavior

### 3. User Experience
- Automatic - no manual intervention needed
- Transparent - user just deletes apps
- Informative - UI shows when cleanup occurs

### 4. Cost Optimization
- Infrastructure only runs when needed
- Reduces resource usage on Proxmox host
- Perfect for development/testing environments

---

## Configuration Options

### Disable Auto-Cleanup (Optional)

If you want to keep infrastructure running even with 0 apps:

```python
# In network_appliance_orchestrator.py

class NetworkApplianceOrchestrator:
    def __init__(self, proxmox_service, auto_cleanup=True):
        self.proxmox = proxmox_service
        self.auto_cleanup_enabled = auto_cleanup
        # ...
    
    async def cleanup_if_empty(self) -> bool:
        if not self.auto_cleanup_enabled:
            logger.info("Auto-cleanup disabled, keeping infrastructure")
            return False
        
        # ... rest of cleanup logic ...
```

### Grace Period (Optional)

Add a grace period before cleanup:

```python
async def cleanup_if_empty(self, grace_period_seconds: int = 300) -> bool:
    """
    Clean up with optional grace period.
    
    Args:
        grace_period_seconds: Wait this long before cleanup (default: 5 minutes)
    """
    app_count = await self.count_connected_apps()
    
    if app_count > 0:
        return False
    
    # Wait grace period
    logger.info(f"No apps remaining, waiting {grace_period_seconds}s before cleanup...")
    await asyncio.sleep(grace_period_seconds)
    
    # Re-check after grace period
    app_count = await self.count_connected_apps()
    if app_count > 0:
        logger.info("Apps deployed during grace period, keeping infrastructure")
        return False
    
    # Proceed with cleanup
    # ...
```

---

## Summary

The smart cleanup system ensures that:

1. **Infrastructure persists** while apps are running
2. **Automatic cleanup** when last app is deleted
3. **Resource efficiency** by removing idle infrastructure
4. **Automatic re-initialization** when next app is deployed
5. **Complete visibility** via Infrastructure status page

This provides the best balance between convenience, resource efficiency, and user experience.

---

**Status: ✅ Implementation Complete**

All code for smart cleanup and infrastructure status is implemented and ready for integration.
