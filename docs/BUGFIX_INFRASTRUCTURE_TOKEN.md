# Bugfix: Infrastructure Page - Token Key Mismatch

**Date:** 8 October 2025  
**Issue:** Infrastructure page showing "Network Appliance Not Found" despite appliance being available  
**Severity:** High - Blocks visibility of infrastructure status

## Problem Description

The Infrastructure page was not displaying network appliance information even though:
- The appliance exists and is running (VMID 9999 on node opti2)
- The backend API returns correct data
- All services are operational

### Root Cause

**Token Key Mismatch** between different parts of the frontend code:

1. **app.js legacy code** used: `localStorage.getItem('authToken')`
2. **Auth object in app.js** defined: `TOKEN_KEY: 'proximity_token'`
3. **auth.js module** used: `'authToken'`
4. **api.js service** used: `'authToken'`

This caused authenticated requests to fail because the token was stored with one key but retrieved with another.

## Solution Applied

### 1. Standardized Token Key

All code now uses the same token key: `'proximity_token'`

**Files Modified:**
- `backend/frontend/app.js` - Updated all token retrievals to use `Auth.getToken()`
- `backend/frontend/js/utils/auth.js` - Changed from `'authToken'` to `'proximity_token'`
- `backend/frontend/js/services/api.js` - Changed from `'authToken'` to `TOKEN_KEY` constant

### 2. Added Token Migration

Added automatic migration for existing users who have tokens stored with the old key:

```javascript
// In app.js Auth object
migrateOldToken() {
    const oldToken = localStorage.getItem('authToken');
    const newToken = localStorage.getItem(this.TOKEN_KEY);
    
    if (oldToken && !newToken) {
        console.log('🔄 Migrating auth token to new key...');
        localStorage.setItem(this.TOKEN_KEY, oldToken);
        localStorage.removeItem('authToken');
    }
}
```

### 3. Updated Cache Version

Updated cache busting version in `index.html`:
- `app.js?v=20251008-9`
- `main.js?v=20251008-9`

## Changes Summary

| File | Lines Changed | Change Description |
|------|--------------|-------------------|
| `backend/frontend/app.js` | 672, 1059, 2683, 2761, 2825, 2902, 2985, 3058, 3124 | Changed `localStorage.getItem('authToken')` to `Auth.getToken()` |
| `backend/frontend/app.js` | 35-50 | Added `migrateOldToken()` method |
| `backend/frontend/js/utils/auth.js` | 8, 14, 22, 30 | Changed `'authToken'` to `TOKEN_KEY = 'proximity_token'` |
| `backend/frontend/js/services/api.js` | 9, 16, 53, 114 | Changed `'authToken'` to `TOKEN_KEY = 'proximity_token'` |
| `backend/frontend/index.html` | 15, 18 | Updated cache version to `v=20251008-9` |

## Verification Steps

### 1. Clear Browser Cache
```bash
# Chrome/Edge
Cmd + Shift + Delete → Clear cached images and files

# Safari
Cmd + Option + E
```

### 2. Hard Refresh
```bash
Cmd + Shift + R
```

### 3. Check Browser Console

After refreshing, you should see:
```
[Infrastructure] Fetching status...
[Infrastructure] Response status: 200
[Infrastructure] Result: {success: true, data: {...}}
[Infrastructure] Infrastructure data: {appliance: {...}, ...}
[Infrastructure] Appliance: {vmid: 9999, hostname: 'prox-appliance', ...}
```

### 4. Verify Infrastructure Page

The Infrastructure page should now display:

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
   - dnsmasq (DHCP/DNS)
   - caddy (Reverse Proxy)
   - iptables (NAT Firewall)

✅ **Network Configuration** details

✅ **Connected Applications** (if any)

✅ **Proxmox Nodes** cards

## Testing

### Manual Test
1. Open browser DevTools (F12)
2. Go to Application → Local Storage
3. Clear all entries (optional)
4. Login to Proximity
5. Navigate to Infrastructure page
6. Verify appliance information is displayed

### API Test
```bash
# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8765/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# Test infrastructure endpoint
curl -s http://localhost:8765/api/v1/system/infrastructure/status \
  -H "Authorization: Bearer $TOKEN" | jq '.data.appliance'
```

Expected output:
```json
{
  "vmid": 9999,
  "hostname": "prox-appliance",
  "status": "running",
  "node": "opti2",
  "wan_ip": "192.168.100.2",
  "lan_ip": "10.20.0.1",
  ...
}
```

## Migration Impact

### Backward Compatibility
✅ **Automatic migration** - Users with old tokens will be automatically migrated
✅ **No re-login required** - Existing sessions continue to work
✅ **Transparent upgrade** - No user action needed

### Future-Proofing
- Single source of truth for token key name
- Consistent authentication across all modules
- Easier to maintain and debug

## Related Issues

This fix resolves:
- Infrastructure page showing "Network Appliance Not Found"
- Authentication inconsistencies between modules
- Token storage/retrieval mismatches

## Next Steps

1. Monitor for any authentication issues
2. Consider removing migration code after 1-2 weeks (when all users have migrated)
3. Add integration tests for authentication flow

## Files to Review

- `backend/frontend/app.js`
- `backend/frontend/js/utils/auth.js`
- `backend/frontend/js/services/api.js`
- `backend/frontend/index.html`

---

**Status:** ✅ Fixed and ready for testing  
**Priority:** High  
**Type:** Bug Fix  
**Component:** Frontend Authentication + Infrastructure UI
