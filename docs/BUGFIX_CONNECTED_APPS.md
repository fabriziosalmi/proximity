# Bugfix: Infrastructure Page - Connected Applications Display

**Date:** 8 October 2025  
**Issue:** Connected applications not showing complete information  
**Severity:** High - Critical UI functionality broken

## Problems Identified

### 1. Missing Application Data
Connected applications were showing incomplete information:
- ❌ App name not displayed (showed "N/A")
- ❌ VMID not shown (showed "N/A")
- ❌ IP address not visible (showed "N/A")
- ❌ Status not displayed (showed "unknown")
- ❌ DNS name text color invisible (black text on black background)

### 2. Root Cause

The `_get_connected_applications()` method only retrieved DHCP lease information (IP, hostname, MAC) but didn't correlate with actual deployed LXC containers to get:
- Container name
- VMID
- Running status

## Solution Applied

### 1. Enhanced Data Retrieval

**File:** `backend/services/network_appliance_orchestrator.py`

Modified `_get_connected_applications()` to:
1. ✅ Fetch DHCP leases from dnsmasq
2. ✅ Query Proxmox API for all deployed containers
3. ✅ Correlate leases with containers by hostname
4. ✅ Enrich application data with full details

**Changes:**
```python
# Before - Only DHCP lease data
apps.append({
    'ip': parts[2],
    'hostname': parts[3],
    'mac': parts[1],
    'lease_expires': parts[0],
    'dns_name': f"{parts[3]}.{self.DNS_DOMAIN}"
})

# After - Full application data
container_info = deployed_containers.get(hostname, {})
app_data = {
    'ip': parts[2],
    'ip_address': parts[2],  # Alias for frontend
    'hostname': hostname,
    'name': container_info.get('name', hostname),
    'vmid': container_info.get('vmid', 'N/A'),
    'status': container_info.get('status', 'unknown'),
    'mac': parts[1],
    'lease_expires': parts[0],
    'dns_name': f"{hostname}.{self.DNS_DOMAIN}"
}
```

### 2. Fixed CSS Color Issue

**File:** `backend/frontend/css/styles.css`

The DNS name `<code>` elements had black text on black background:

**Before:**
```css
.infrastructure-table td code {
    color: var(--primary);  /* #18181b - black! */
}
```

**After:**
```css
.infrastructure-table td code {
    color: var(--cyan-bright);  /* #22d3ee - visible cyan! */
    font-weight: 500;
}
```

## Infrastructure Page Display

### Before Fix:
```
Connected Applications (1)
┌──────────┬──────┬────────────┬────────┬──────────┐
│ App Name │ VMID │ IP Address │ Status │ DNS Name │
├──────────┼──────┼────────────┼────────┼──────────┤
│ N/A      │ N/A  │ N/A        │ unkno  │ [black]  │
└──────────┴──────┴────────────┴────────┴──────────┘
```

### After Fix:
```
Connected Applications (1)
┌───────────┬──────┬──────────────┬─────────┬───────────────────────┐
│ App Name  │ VMID │ IP Address   │ Status  │ DNS Name              │
├───────────┼──────┼──────────────┼─────────┼───────────────────────┤
│ nginx-001 │ 201  │ 10.20.0.130  │ running │ nginx-001.prox.local  │
└───────────┴──────┴──────────────┴─────────┴───────────────────────┘
```

## API Response Change

### Before:
```json
{
  "applications": [
    {
      "ip": "10.20.0.130",
      "hostname": "nginx-001",
      "mac": "BC:24:11:F6:7A:72",
      "lease_expires": "1759998851",
      "dns_name": "nginx-001.prox.local"
    }
  ]
}
```

### After:
```json
{
  "applications": [
    {
      "ip": "10.20.0.130",
      "ip_address": "10.20.0.130",
      "hostname": "nginx-001",
      "name": "nginx-001",
      "vmid": 201,
      "status": "running",
      "mac": "BC:24:11:F6:7A:72",
      "lease_expires": "1759998851",
      "dns_name": "nginx-001.prox.local"
    }
  ]
}
```

## Testing

### 1. Deploy Test Application

```bash
# Deploy nginx via Proximity UI
# App will be assigned:
# - Name: nginx-001
# - VMID: 201 (or next available)
# - IP: 10.20.0.xxx (DHCP from appliance)
```

### 2. Check Infrastructure Page

Navigate to Infrastructure → Connected Applications:
- ✅ App name shows: "nginx-001"
- ✅ VMID shows: "201"
- ✅ IP Address shows: "10.20.0.130" (in cyan)
- ✅ Status shows: "running" (green badge)
- ✅ DNS name shows: "nginx-001.prox.local" (in cyan, readable)

### 3. Verify API

```bash
curl http://localhost:8765/api/v1/system/infrastructure/status \
  -H "Authorization: Bearer <token>" | jq '.data.applications'
```

Should return full application data with all fields populated.

### 4. Check Correlation Logic

The system correlates DHCP leases with deployed containers by:
1. Reading `/var/lib/misc/dnsmasq.leases` from appliance
2. Querying Proxmox API for all LXC containers
3. Matching by `hostname` field
4. Enriching lease data with container info

## Files Modified

| File | Change | Description |
|------|--------|-------------|
| `backend/services/network_appliance_orchestrator.py` | Lines 1110-1162 | Enhanced `_get_connected_applications()` with container correlation |
| `backend/frontend/css/styles.css` | Line 2896 | Changed code color from black to cyan-bright |
| `docs/BUGFIX_CONNECTED_APPS.md` | New file | This documentation |

## Edge Cases Handled

### 1. Container Not Found
If hostname in DHCP lease doesn't match any deployed container:
- ✅ Falls back to hostname as name
- ✅ Shows "N/A" for VMID
- ✅ Shows "unknown" for status
- ✅ Still displays IP and DNS name

### 2. Multiple Containers with Same Name
- System uses exact hostname match from DHCP
- First match wins if duplicates exist

### 3. Appliance Not Running
- Returns empty array
- Infrastructure page shows "No connected applications"

### 4. API Errors
- Gracefully handled with try/except
- Logs debug message
- Returns partial data or empty array

## Benefits

### User Experience
✅ **Complete visibility** - See all app details at a glance  
✅ **Better readability** - Cyan code elements stand out  
✅ **Real-time status** - Know if apps are running  
✅ **Easy identification** - VMID helps locate containers  

### System Integration
✅ **Data correlation** - Links DHCP with Proxmox  
✅ **Accurate status** - Real container status, not guessed  
✅ **Consistent naming** - Matches deployed app names  

### Debugging
✅ **Quick diagnostics** - See IP assignments immediately  
✅ **Status verification** - Confirm apps are running  
✅ **Network visibility** - Full network topology view  

## Next Steps

### Caddy Subdomain Implementation
Currently apps are accessible via path-based routing:
```
http://<appliance-wan-ip>/nginx-001/
```

**Planned enhancement:**
```
https://nginx-001.prox.local/  (with SSL)
```

This requires:
1. Modify Caddy configuration for subdomain-based vhosts
2. Generate self-signed SSL certificates
3. Update DNS resolution in dnsmasq
4. Document user /etc/hosts configuration

See `docs/CADDY_SUBDOMAIN_DESIGN.md` for implementation plan.

---

**Status:** ✅ Fixed  
**Priority:** High  
**Type:** Bug Fix + Enhancement  
**Component:** Frontend UI + Backend API + CSS
