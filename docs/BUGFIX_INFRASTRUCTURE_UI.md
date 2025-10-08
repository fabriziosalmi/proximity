# Bugfix: Infrastructure Page UI Issues

## Problem

The Infrastructure page was showing incorrect status with the following issues:

1. **"Infrastructure Status: Unknown"** - Health status not properly determined
2. **"Network Appliance Not Found"** - Appliance section not rendering even when appliance exists
3. **Field mismatch** - Frontend looking for `connected_apps` but backend returning `applications`
4. **Insufficient error handling** - No detailed logging to diagnose issues
5. **Silent failures** - Errors not being properly reported

**Symptoms:**
- Infrastructure page shows "Unknown" status
- Network Appliance section shows "Not Found" warning
- No appliance details displayed (VMID, IP addresses, services)
- Proxmox Nodes shown but appliance information missing

## Root Causes

### 1. Field Name Mismatch
**Location:** `backend/frontend/app.js` line 695

```javascript
// WRONG - Backend doesn't return this field
const connected_apps = infrastructure?.connected_apps || [];

// Backend actually returns:
status['applications'] = apps  // from network_appliance_orchestrator.py
```

### 2. Insufficient Logging
The frontend had minimal logging, making it hard to diagnose issues:
- No console logs for API responses
- No status tracking of data flow
- Silent failures on API errors

### 3. Missing Error State Handling
No error variable to track and display API failures to help with debugging.

## Solution

### 1. Fixed Field Name Mismatch

**File:** `backend/frontend/app.js`

Changed line 695 from:
```javascript
const connected_apps = infrastructure?.connected_apps || [];
```

To:
```javascript
// Support both field names for backwards compatibility
const connected_apps = infrastructure?.applications || infrastructure?.connected_apps || [];
```

This ensures compatibility if either field name is used.

### 2. Added Comprehensive Logging

Added detailed console logging throughout the render function:

```javascript
console.log('[Infrastructure] Fetching status...');
console.log('[Infrastructure] Response status:', response.status);
console.log('[Infrastructure] Result:', result);
console.log('[Infrastructure] Infrastructure data:', infrastructure);
console.log('[Infrastructure] Appliance:', infrastructure?.appliance);
console.log('[Infrastructure] Health status:', infrastructure?.health_status);
console.log('[Infrastructure] Final state:', {
    appliance: !!appliance,
    services: Object.keys(services).length,
    connected_apps: connected_apps.length,
    health_status,
    error
});
```

### 3. Added Error Tracking

```javascript
let infrastructure = null;
let error = null;  // NEW: Track errors

try {
    // ... API call ...
    if (response.ok) {
        // Success path
    } else {
        error = `Failed to load infrastructure status (${response.status})`;
        console.error('[Infrastructure] Error:', error);
    }
} catch (err) {
    error = err.message || 'Failed to load infrastructure';
    console.error('[Infrastructure] Exception:', err);
}
```

### 4. Updated Cache Version

**File:** `backend/frontend/index.html`

Updated from `v=20251008-5` to `v=20251008-6` to force browser cache refresh.

## Verification

### 1. Check Browser Console

After refreshing the page (Cmd+Shift+R), you should see detailed logs:

```
[Infrastructure] Fetching status...
[Infrastructure] Response status: 200
[Infrastructure] Result: {success: true, data: {...}}
[Infrastructure] Infrastructure data: {appliance: {...}, services: {...}, ...}
[Infrastructure] Appliance: {vmid: 9999, hostname: 'prox-appliance', ...}
[Infrastructure] Health status: healthy
[Infrastructure] Final state: {appliance: true, services: 4, connected_apps: 0, health_status: 'healthy', error: null}
```

### 2. Infrastructure Page Should Show

✅ **Infrastructure Status: Healthy** (or appropriate status)
✅ **Network Appliance section** with:
   - Hostname
   - Status badge (running/stopped)
   - VMID number
   - Node name
   - WAN IP address
   - LAN IP address
   - Resource usage (memory, cores, disk, uptime)
   - Management buttons (Restart, View Logs, Test NAT)

✅ **Services Health grid** showing:
   - dnsmasq
   - caddy  
   - NAT firewall
   - (other services)

✅ **Network Configuration** details
✅ **Connected Applications** list (if any apps deployed)
✅ **Proxmox Nodes** cards

### 3. If Still Showing "Unknown" or "Not Found"

Check the console logs to identify the actual issue:

**If "Not authenticated":**
```
[Infrastructure] No auth token
```
**Solution:** Log in again

**If API error (404, 500, etc):**
```
[Infrastructure] Error: Failed to load infrastructure status (500)
```
**Solution:** Check backend is running and appliance exists

**If no appliance:**
```
[Infrastructure] Appliance: null
```
**Solution:** Deploy your first application to trigger appliance creation

## Testing Steps

### 1. Hard Refresh Browser
```
Mac: Cmd + Shift + R
Windows/Linux: Ctrl + Shift + R
```

### 2. Open Developer Tools
```
Press F12 or Right-click → Inspect
Go to Console tab
```

### 3. Navigate to Infrastructure Page
Click "Infrastructure" in sidebar

### 4. Check Console Output
Should see all the `[Infrastructure]` log messages

### 5. Verify Display
- Status should be "Healthy", "Degraded", or "Unknown" (with reason)
- If appliance exists, its card should display with all details
- Services should show their health status
- No JavaScript errors in console

## Troubleshooting

### Still Showing "Unknown"

**Check 1: Is backend running?**
```bash
lsof -ti:8765
# Should return a PID
```

**Check 2: API endpoint accessible?**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8765/api/v1/system/infrastructure/status
```

**Check 3: Console errors?**
Look for red errors in browser console

### Still Showing "Not Found"

**Check 1: Does appliance exist?**
```bash
# SSH to Proxmox
pvesh get /nodes/NODENAME/lxc/9999/status/current
```

**Check 2: Backend logs**
```bash
tail -f backend/backend.log
```

Look for:
```
Using Proxmox node: NODE_NAME
Found existing appliance VMID 9999 on node 'NODE_NAME'
```

### Network Appliance Creation

If no appliance exists:
1. Deploy any application from App Store
2. Appliance will be automatically created
3. Wait 2-3 minutes for provisioning
4. Refresh Infrastructure page

## Backend Field Names Reference

For future development, the backend returns these fields in `infrastructure.data`:

```python
{
    'appliance': {
        'vmid': int,
        'hostname': str,
        'status': str,
        'node': str,
        'wan_ip': str,
        'wan_interface': str,
        'lan_ip': str,
        'lan_interface': str,
        'ssh_access': str,
        'resources': {...},
        'memory': str,
        'cores': str,
        'disk': str,
        'uptime': str
    },
    'bridge': {...},
    'network': {...},
    'services': {...},
    'applications': [],  # <-- NOTE: Not 'connected_apps'
    'statistics': {...},
    'health_status': str  # 'healthy', 'degraded', or 'unknown'
}
```

## Related Files

- `backend/frontend/app.js` - Frontend rendering and API calls
- `backend/services/network_appliance_orchestrator.py` - Backend infrastructure status
- `backend/api/endpoints/system.py` - API endpoint `/system/infrastructure/status`
- `backend/frontend/index.html` - Cache version numbers

## Changes Summary

| File | Lines | Change |
|------|-------|--------|
| `backend/frontend/app.js` | 670-720 | Added logging, error handling, fixed field name |
| `backend/frontend/index.html` | 15, 18, 258, 261 | Updated cache version to v=20251008-6 |

## Impact

- **User Experience:** Infrastructure page now displays correctly with accurate status
- **Debugging:** Detailed console logs help diagnose issues quickly
- **Reliability:** Error handling prevents silent failures
- **Compatibility:** Supports both `applications` and `connected_apps` field names

## Prevention

To prevent similar issues in the future:

1. **API Contract Documentation** - Document exact field names returned by backend
2. **Type Checking** - Consider TypeScript for frontend to catch field mismatches
3. **Integration Tests** - Test full API → Frontend data flow
4. **Console Logging** - Always log API responses during development
5. **Error Boundaries** - Display user-friendly errors when APIs fail

## Next Steps

1. ✅ Hard refresh browser (Cmd+Shift+R)
2. ✅ Navigate to Infrastructure page
3. ✅ Check console for detailed logs
4. ✅ Verify appliance and services display correctly
5. ✅ If issues persist, check troubleshooting section above

---

**Status:** ✅ Fixed and deployed
**Cache Version:** v=20251008-6
**Date:** October 8, 2025
