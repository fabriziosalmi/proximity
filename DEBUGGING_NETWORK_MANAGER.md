# Debugging: Network Manager Not Available

## Issue

Seeing this warning in logs:
```
WARNING - NetworkManager not available - using default bridge (vmbr0) with DHCP
```

This means `proxmox_service.network_manager` is `None` when deploying app containers.

---

## Root Cause Analysis

### Possible Reasons:

1. **Network Appliance Initialization Failed**
   - proximity-lan bridge creation failed
   - Network appliance LXC (VMID 100) creation failed
   - Service configuration failed
   - Health check failed

2. **Orchestrator Not Properly Injected**
   - Injection happened before orchestrator was created
   - Module import issues
   - Timing problems

3. **Development Environment**
   - Running on macOS/Windows (can't create Linux bridges)
   - No access to Proxmox host
   - Testing with mocked services

---

## Diagnosis Steps

### Step 1: Check Startup Logs

Look for these log messages in order:

```
STEP 1: Connecting to Proxmox
✓ Proxmox connection successful
```

```
STEP 2: Initializing Network Appliance (Platinum Edition)
🌐 Deploying proximity-lan bridge and network appliance...
```

**Success Path:**
```
✅ Network Appliance ready:
   • Bridge: proximity-lan (10.20.0.0/24)
   • Appliance: prox-appliance (VMID 100)
   • Gateway: 10.20.0.1
   • DHCP Range: 10.20.0.100-250
   • DNS Domain: .prox.local
   • Management UI: http://192.168.1.x:9090

✓ Network orchestrator injected into ProxmoxService
  → New containers will use proximity-lan network
```

**Failure Path:**
```
⚠️  Network appliance initialization failed
ℹ️  Containers will use default Proxmox networking (vmbr0)

⚠ No network orchestrator available
  → New containers will use default vmbr0 network
```

### Step 2: Check Proxmox Host

SSH into Proxmox and verify:

```bash
# Check if bridge exists
ip link show proximity-lan
# Expected: Device exists and is UP

# Check if appliance exists
pct list | grep 100
# Expected: Shows prox-appliance VMID 100

# Check appliance status
pct status 100
# Expected: status: running

# Check appliance services
pct exec 100 -- rc-status
# Expected: dnsmasq, iptables, caddy running
```

### Step 3: Check for Error Messages

Search logs for these errors:

```bash
# Bridge creation errors
grep -i "failed to create bridge" /var/log/...

# LXC creation errors
grep -i "failed to provision appliance" /var/log/...

# Service configuration errors
grep -i "failed to configure" /var/log/...

# Permission errors
grep -i "permission denied" /var/log/...
```

---

## Common Issues & Fixes

### Issue 1: Permission Denied (Bridge Creation)

**Symptom:**
```
Failed to create bridge: Permission denied
```

**Cause:** Backend doesn't have permission to run ip commands on Proxmox host

**Fix:**
1. Check SSH connection to Proxmox
2. Verify root access via SSH
3. Check SSH key authentication

```bash
# Test SSH connection
ssh root@<proxmox-host> "ip link show"
```

### Issue 2: Alpine Template Not Found

**Symptom:**
```
Template not found: alpine-3.18-default_20230607_amd64.tar.xz
```

**Cause:** Alpine template not downloaded on Proxmox

**Fix:**
```bash
# SSH to Proxmox
pveam update
pveam download local alpine-3.18-default_20230607_amd64.tar.xz
```

### Issue 3: VMID 100 Already in Use

**Symptom:**
```
Failed to create LXC: CT 100 already exists
```

**Cause:** VMID 100 is already used by another container

**Fix Option 1 - Use Existing:**
The orchestrator should detect this and use the existing container if it's the appliance.

**Fix Option 2 - Remove and Recreate:**
```bash
# SSH to Proxmox
pct stop 100
pct destroy 100
# Restart backend - will recreate appliance
```

**Fix Option 3 - Change VMID:**
Edit `network_appliance_orchestrator.py`:
```python
APPLIANCE_VMID = 101  # Change from 100 to 101
```

### Issue 4: Storage Not Available

**Symptom:**
```
Failed to create LXC: storage 'local-lvm' does not exist
```

**Cause:** Storage backend not configured

**Fix:**
Check available storage:
```bash
pvesm status
```

Update orchestrator to use available storage:
```python
# In provision_appliance_lxc():
'rootfs': 'local-zfs:8',  # Change from local-lvm
```

### Issue 5: Network Interface Already Exists

**Symptom:**
```
RTNETLINK answers: File exists
```

**Cause:** proximity-lan bridge already exists

**Fix:**
This should be OK - the orchestrator detects existing bridge. If it's causing issues:

```bash
# Remove existing bridge
ssh root@<proxmox-host>
ip link set proximity-lan down
ip link delete proximity-lan
```

### Issue 6: Running on macOS/Windows

**Symptom:**
```
Cannot SSH to Proxmox host from macOS
```

**Cause:** Development environment can't create Linux bridges

**Expected Behavior:**
- Initialization will fail gracefully
- Falls back to vmbr0 networking
- This is normal for development

**Fix:**
Deploy to actual Proxmox host or use VM.

---

## Debugging Code

### Add Debug Logging to main.py

```python
# After orchestrator initialization
logger.debug(f"Orchestrator object: {orchestrator}")
logger.debug(f"Orchestrator type: {type(orchestrator)}")
if orchestrator:
    logger.debug(f"Has get_container_network_config: {hasattr(orchestrator, 'get_container_network_config')}")
    logger.debug(f"Appliance info: {orchestrator.appliance_info}")

# After injection
logger.debug(f"proxmox_service.network_manager: {proxmox_service.network_manager}")
logger.debug(f"network_manager type: {type(proxmox_service.network_manager)}")
```

### Test Network Config Method

```python
# In Python shell or test script
from services.proxmox_service import proxmox_service
from services.network_appliance_orchestrator import NetworkApplianceOrchestrator

# Check if network_manager is set
print(f"network_manager: {proxmox_service.network_manager}")

# Test method call
if proxmox_service.network_manager:
    import asyncio
    config = asyncio.run(
        proxmox_service.network_manager.get_container_network_config("test-host")
    )
    print(f"Network config: {config}")
```

---

## Verification Commands

### After Startup, Verify Network Manager is Active:

```bash
# Check logs for success messages
tail -f /var/log/proximity.log | grep -E "(Network|orchestrator|injected)"

# Expected output:
# ✓ Network orchestrator injected into ProxmoxService
# → New containers will use proximity-lan network
```

### Deploy Test App:

```bash
curl -X POST http://localhost:8765/api/v1/apps/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "catalog_id": "nginx",
    "hostname": "test-nginx",
    "config": {},
    "environment": {}
  }'

# Watch logs for:
# "Using managed network config: name=eth0,bridge=proximity-lan,ip=dhcp"
# NOT:
# "NetworkManager not available - using default bridge (vmbr0)"
```

### Check Container Network After Deployment:

```bash
# SSH to Proxmox
pct config <vmid> | grep net0

# Expected for Platinum Edition:
# net0: name=eth0,bridge=proximity-lan,ip=dhcp,firewall=1

# Old basic mode would show:
# net0: name=eth0,bridge=vmbr0,ip=dhcp,firewall=1
```

---

## Force Reinitialization

If something is stuck, force clean reinitialization:

```bash
# SSH to Proxmox

# 1. Remove appliance
pct stop 100
pct destroy 100

# 2. Remove bridge
ip link set proximity-lan down
ip link delete proximity-lan

# 3. Clean /etc/network/interfaces
vi /etc/network/interfaces
# Remove proximity-lan entries

# 4. Restart backend
# Backend will recreate everything on next startup
```

---

## Expected vs Actual Behavior

### Expected (Success):

```
[Startup]
STEP 2: Initializing Network Appliance
✓ Bridge created: proximity-lan
✓ Appliance created: VMID 100
✓ Services configured: dnsmasq, iptables, caddy, cockpit
✓ Health check passed
✓ Network orchestrator injected

[App Deployment]
Using managed network config: name=eth0,bridge=proximity-lan,ip=dhcp
✓ Container deployed on proximity-lan
✓ Got IP: 10.20.0.101
✓ DNS name: app.prox.local
```

### Actual (If seeing warning):

```
[Startup]
STEP 2: Initializing Network Appliance
⚠️ Network appliance initialization failed
⚠ No network orchestrator available

[App Deployment]
⚠ NetworkManager not available - using default bridge (vmbr0)
✓ Container deployed on vmbr0
✓ Got IP: 192.168.1.x (from network DHCP)
```

---

## Next Steps

1. **Check startup logs** - Look for initialization failure messages
2. **Verify Proxmox connectivity** - Can backend SSH to Proxmox?
3. **Check bridge creation** - Does proximity-lan exist?
4. **Check appliance status** - Is VMID 100 running?
5. **Test method call** - Can you call `get_container_network_config()`?
6. **Review permissions** - Can backend execute privileged commands?

---

## Configuration to Check

### .env file:
```bash
PROXMOX_HOST=<your-proxmox-ip>
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=<password>
PROXMOX_SSH_HOST=<your-proxmox-ip>
PROXMOX_SSH_USER=root
PROXMOX_SSH_PASSWORD=<password>
```

### Permissions Required:
- SSH access to Proxmox host as root
- Permission to create bridges (ip link add)
- Permission to create LXCs (pct create)
- Permission to execute commands in LXCs (pct exec)
- Permission to configure network interfaces

---

**If you're still seeing the warning after checking all of the above, please share:**

1. Full startup logs (from application start)
2. Output of `pct list | grep 100`
3. Output of `ip link show proximity-lan`
4. Any ERROR messages in logs
