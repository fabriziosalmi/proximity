# Quick Test After SSH Fix

## Restart Backend and Watch for Success

```bash
cd /Users/fab/GitHub/proximity/backend
python3 main.py
```

## Expected Successful Output

```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
2025-10-03 XX:XX:XX - main - INFO - Starting Proximity API...
2025-10-03 XX:XX:XX - main - INFO - STEP 1: Connecting to Proxmox
2025-10-03 XX:XX:XX - services.proxmox_service - INFO - Connected to Proxmox at 192.168.100.102
2025-10-03 XX:XX:XX - main - INFO - ✓ Proxmox connection successful

2025-10-03 XX:XX:XX - main - INFO - STEP 2: Initializing Network Appliance (Platinum Edition)
2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - 🚀 Initializing Proximity Network Appliance...
2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - Step 1/4: Provisioning host bridge...
2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - Checking for proximity-lan bridge on Proxmox host...
2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - Creating proximity-lan bridge...
✅ 2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - ✓ Created proximity-lan bridge successfully

2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - Step 2/4: Provisioning appliance LXC...
✅ 2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - ✓ Appliance LXC ready: VMID 100, WAN IP: 192.168.100.X

2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - Step 3/4: Configuring appliance services...
✅ 2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - ✓ Services configured successfully

2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - Step 4/4: Verifying appliance health...
✅ 2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - ✅ Proximity Network Appliance initialized successfully
2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO -    Management UI: http://192.168.100.X:9090
2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO -    LAN Gateway: 10.20.0.1
2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO -    DNS Domain: .prox.local

✅ 2025-10-03 XX:XX:XX - main - INFO - ✓ Network orchestrator injected into ProxmoxService
✅ 2025-10-03 XX:XX:XX - main - INFO -   → New containers will use proximity-lan network

2025-10-03 XX:XX:XX - main - INFO - STEP 3: Loading Application Catalog
2025-10-03 XX:XX:XX - main - INFO - ✓ Loaded catalog with 11 applications

2025-10-03 XX:XX:XX - main - INFO - STEP 4: Initializing Reverse Proxy Manager
✅ 2025-10-03 XX:XX:XX - main - INFO - ✓ Reverse Proxy Manager initialized
2025-10-03 XX:XX:XX - main - INFO - 🚀 Proximity API started on 0.0.0.0:8765
```

## Key Success Indicators

Look for these specific lines (marked with ✅):

1. **Bridge Created**: `✓ Created proximity-lan bridge successfully`
2. **Appliance Ready**: `✓ Appliance LXC ready: VMID 100`
3. **Services Configured**: `✓ Services configured successfully`
4. **Orchestrator Injected**: `✓ Network orchestrator injected into ProxmoxService`
5. **Correct Network**: `→ New containers will use proximity-lan network`

## What Changed (Old vs New)

### ❌ BEFORE (Failed with local subprocess)
```
2025-10-03 22:58:34,316 - services.network_appliance_orchestrator - ERROR - Failed to execute: ip link add name proximity-lan type bridge
2025-10-03 22:58:34,316 - services.network_appliance_orchestrator - ERROR - Failed to setup host bridge
2025-10-03 22:58:34,316 - main - WARNING - ⚠️  Network appliance initialization failed
2025-10-03 22:58:34,316 - main - WARNING - ⚠ No network orchestrator available
2025-10-03 22:58:34,316 - main - INFO -   → New containers will use default vmbr0 network
```

### ✅ AFTER (Success with SSH execution)
```
2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - ✓ Created proximity-lan bridge successfully
2025-10-03 XX:XX:XX - services.network_appliance_orchestrator - INFO - ✅ Proximity Network Appliance initialized successfully
2025-10-03 XX:XX:XX - main - INFO - ✓ Network orchestrator injected into ProxmoxService
2025-10-03 XX:XX:XX - main - INFO -   → New containers will use proximity-lan network
```

## Test App Deployment

After successful startup, deploy a test app:

```bash
# Deploy nginx
curl -X POST http://localhost:8765/api/v1/apps/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "nginx",
    "instance_name": "test-nginx",
    "resources": {
      "cpu_cores": 1,
      "memory_mb": 512,
      "disk_size_gb": 8
    }
  }'
```

### Expected Deployment Log

```
2025-10-03 XX:XX:XX - services.app_service - INFO - [nginx-test-nginx] Creating LXC container XXX on node opti2
✅ 2025-10-03 XX:XX:XX - services.proxmox_service - INFO - Using managed network config: name=eth0,bridge=proximity-lan,ip=dhcp,firewall=1
2025-10-03 XX:XX:XX - services.proxmox_service - INFO - LXC creation started: node=opti2, vmid=XXX...
```

**Key line**: `Using managed network config: name=eth0,bridge=proximity-lan,ip=dhcp,firewall=1`

### ❌ OLD (Wrong - would show)
```
2025-10-03 22:58:43,021 - services.proxmox_service - WARNING - NetworkManager not available - using default bridge (vmbr0) with DHCP
```

## Verify on Proxmox

SSH to your Proxmox host and check:

```bash
# 1. Bridge exists
ip link show proximity-lan
# Expected: proximity-lan: <BROADCAST,MULTICAST,UP,LOWER_UP>

# 2. Appliance LXC exists and running
pct list | grep 100
# Expected: 100  running  prox-appliance

# 3. Appliance has dual interfaces
pct config 100 | grep net
# Expected:
#   net0: name=eth0,bridge=vmbr0,ip=dhcp,firewall=1  (WAN - management)
#   net1: name=eth1,bridge=proximity-lan,ip=10.20.0.1/24,firewall=1  (LAN - gateway)

# 4. New app containers use proximity-lan
pct config <new_vmid> | grep net0
# Expected: net0: name=eth0,bridge=proximity-lan,ip=dhcp,firewall=1
```

## Troubleshooting

### If initialization still fails:

1. **Check SSH connectivity**:
```bash
ssh root@192.168.100.102 "ip link show"
```

2. **Check SSH settings in config**:
```bash
grep -E 'PROXMOX_(HOST|PASSWORD|SSH)' backend/core/config.py
```

3. **Check for paramiko**:
```bash
python3 -c "import paramiko; print('OK')"
```

4. **Review full logs**: Look for SSH connection errors

5. **Manual bridge creation** (temporary workaround):
```bash
ssh root@192.168.100.102
ip link add name proximity-lan type bridge
ip link set proximity-lan up
```

## Success Checklist

- [ ] Backend starts without errors
- [ ] "✓ Created proximity-lan bridge successfully" appears in logs
- [ ] "✓ Appliance LXC ready: VMID 100" appears in logs
- [ ] "✓ Network orchestrator injected" appears in logs
- [ ] "→ New containers will use proximity-lan network" (not vmbr0)
- [ ] Deployed app shows "Using managed network config: name=eth0,bridge=proximity-lan"
- [ ] App accessible via clean URL (http://app-name.prox.local or http://192.168.100.20)
- [ ] `ip link show proximity-lan` works on Proxmox
- [ ] `pct list | grep 100` shows prox-appliance running

## Complete!

Once all checkboxes are ✅, your **Platinum Edition Network Appliance** is fully operational! 🎉

All new apps will:
- Deploy to isolated 10.20.0.0/24 network
- Get DHCP from appliance (10.20.0.100-250)
- Have DNS names (app-name.prox.local)
- Route through NAT gateway (10.20.0.1)
- Be accessible via reverse proxy
