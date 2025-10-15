# Network Errors and Logs Fix

## Date: October 15, 2025

## Problems Fixed

### 1. NetworkActivityMonitor Console Spam ❌ → ✅
**Error:** `NetworkActivityMonitor poll error: TypeError: NetworkError when attempting to fetch resource`

**Root Cause:**
- NetworkActivityMonitor was trying to fetch app stats during page load
- If the stats endpoint was not available or slow, it would spam console with errors
- These are not critical errors and were polluting the console

**Solution:**
Silenced non-critical network errors in `/backend/frontend/js/services/NetworkActivityMonitor.js`:

```javascript
// BEFORE
} catch (error) {
    console.error('NetworkActivityMonitor poll error:', error);
}

// AFTER
} catch (error) {
    // Only log non-network errors
    if (error.message && !error.message.includes('NetworkError') && !error.message.includes('fetch')) {
        console.error('NetworkActivityMonitor poll error:', error);
    }
}
```

Also silenced individual app stat fetch warnings:
```javascript
// BEFORE
} catch (error) {
    console.warn(`Failed to fetch stats for app ${app.id}:`, error);
}

// AFTER
} catch (error) {
    // Silently skip if stats not available
    // console.warn(`Failed to fetch stats for app ${app.id}:`, error);
}
```

### 2. App Logs 404 Error ❌ → 🔍 Debugging Added
**Error:** `GET http://127.0.0.1:8765/api/apps/nginx-nginx-01/logs [HTTP/1.1 404 Not Found]`

**Issue:**
- The endpoint is being called with what looks like a hostname instead of an ID
- URL shows `/api/apps/nginx-nginx-01/logs` but should be `/api/apps/{numeric_id}/logs`

**Solution:**
Added debug logging to track what's being passed in `/backend/frontend/js/services/appOperations.js`:

```javascript
export async function loadAppLogs(appId, logType = 'all') {
    // ... existing code ...
    
    console.log(`📄 Loading logs for app: ${appId}, type: ${logType}`);
    
    const url = `${API_BASE}/apps/${appId}/logs`;
    console.log(`📡 Fetching logs from: ${url}`);
    
    // ... rest of code ...
}
```

**Next Steps to Investigate:**
1. Check what value `app.id` has when calling `showAppLogs(app.id, app.hostname)`
2. Verify that the backend API expects numeric ID vs hostname
3. Check if the app data structure has both `id` (numeric) and `hostname` fields
4. If backend expects hostname, change endpoint; if expects ID, ensure correct value is passed

## Files Modified

1. `/backend/frontend/js/services/NetworkActivityMonitor.js`
   - Silenced non-critical network fetch errors
   - Removed verbose warnings for individual app stat failures

2. `/backend/frontend/js/services/appOperations.js`
   - Added debug logging for logs endpoint calls
   - Helps track what ID is being passed to the API

## Impact

### NetworkActivityMonitor Fix
- ✅ Cleaner console output
- ✅ Only shows actual errors, not expected network issues
- ✅ Reduces noise during debugging
- ⚠️ Stats polling continues to work silently in background

### Logs Debug Enhancement
- ✅ Better visibility into what's being called
- ✅ Easier to diagnose ID vs hostname issue
- 🔍 Needs follow-up to fix actual root cause

## Testing Checklist

### NetworkActivityMonitor
- [x] Console is not spammed with NetworkError messages
- [ ] Network stats still update when available
- [ ] Other errors still show in console

### App Logs
- [ ] Check console for debug messages when clicking "View Logs"
- [ ] Verify what ID value is being passed
- [ ] Confirm backend API expectation (ID vs hostname)
- [ ] Fix endpoint or data mapping as needed

## Follow-up Required

### Logs 404 Issue
The debug logging will help identify the root cause. Possible fixes:

**Option A: Backend expects numeric ID**
```javascript
// Ensure app.id is numeric, not hostname
'view-logs': () => window.showAppLogs(app.id, app.hostname)
```

**Option B: Backend expects hostname**
```javascript
// Change to use hostname instead
'view-logs': () => window.showAppLogs(app.hostname, app.hostname)
```

**Option C: Backend endpoint format is different**
```javascript
// Change API endpoint structure
const response = await authFetch(`${API_BASE}/apps/logs/${appId}`);
```

### Action Items
1. ✅ Check console logs when clicking "View Logs" button
2. ⏳ Identify if app.id contains numeric ID or hostname
3. ⏳ Verify backend API endpoint format
4. ⏳ Apply appropriate fix based on findings

---

**Status:** Partial - Console spam fixed, logs issue needs investigation
**Priority:** Medium - Logs feature not working
**Impact:** Medium - Users can't view app logs
