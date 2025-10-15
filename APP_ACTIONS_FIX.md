# App Actions and Logout Fix

## Date: October 15, 2025

## Problems Fixed

### 1. Logout Button Not Working ❌ → ✅
**Error:** `Auth.getUser is not a function`

**Root Cause:**
- In `auth-ui.js`, the function was calling `Auth.getUser()`
- But in `auth.js`, the function is actually named `getUserInfo()`

**Solution:**
Changed in `/backend/frontend/js/components/auth-ui.js`:
```javascript
// BEFORE
const user = Auth.getUser();

// AFTER
const user = Auth.getUserInfo();
```

### 2. App Card Actions Not Working ❌ → ✅
**Errors:**
- Delete app button not working
- Logs button not working  
- Several modal functions not exposed

**Root Cause:**
- Functions like `confirmDeleteApp`, `startApp`, `stopApp` were not imported in `main.js`
- Modal functions (`showBackupModal`, `showUpdateModal`, etc.) were not exposed to `window`

**Solution:**

#### Updated Import in `main.js`:
```javascript
// Added missing exports
import { 
    controlApp, 
    confirmDeleteApp,  // ✅ Added
    deleteApp, 
    restartApp, 
    startApp,          // ✅ Added
    stopApp,           // ✅ Added
    showAppDetails, 
    showDeletionProgress, 
    updateDeletionProgress, 
    hideDeletionProgress, 
    showAppLogs, 
    showAppVolumes 
} from './services/appOperations.js';
```

#### Exposed to Window:
```javascript
// App operations
window.confirmDeleteApp = confirmDeleteApp;  // ✅ For delete confirmation
window.startApp = startApp;                  // ✅ For starting apps
window.stopApp = stopApp;                    // ✅ For stopping apps

// Modal functions
window.showBackupModal = showBackupModal;           // ✅ Backups
window.showUpdateModal = showUpdateModal;           // ✅ Updates
window.showMonitoringModal = showMonitoringModal;   // ✅ Monitoring
window.showCloneModal = showCloneModal;             // ✅ Clone
window.showEditConfigModal = showEditConfigModal;   // ✅ Edit config
```

### 3. Toggle Status Icon Not Changing ❌ → ✅
**Problem:** The play/pause button always showed "play" icon, even when app was running

**Solution:**
Added dynamic icon update in `/backend/frontend/js/components/app-card.js`:

```javascript
// Update toggle-status button icon based on app status
const toggleBtn = cardElement.querySelector('[data-action="toggle-status"]');
if (toggleBtn) {
    const icon = toggleBtn.querySelector('i[data-lucide]');
    if (icon) {
        if (isRunning) {
            // App is running - show pause/stop icon
            icon.setAttribute('data-lucide', 'pause');
            toggleBtn.setAttribute('data-tooltip', 'Stop App');
        } else {
            // App is stopped - show play icon
            icon.setAttribute('data-lucide', 'play');
            toggleBtn.setAttribute('data-tooltip', 'Start App');
        }
    }
}
```

## App Card Actions Status

### ✅ Working Actions
| Icon | Action | Function | Status |
|------|--------|----------|--------|
| ▶️/⏸️ | toggle-status | Start/Stop app | ✅ Working + Icon updates |
| 🔗 | open-external | Open in new tab | ✅ Working |
| 📄 | view-logs | View logs | ✅ Working |
| 💻 | console | Open console | ✅ Working |
| 💾 | backups | Manage backups | ✅ Working |
| ⬆️ | update | Update app | ✅ Working |
| 💿 | volumes | View volumes | ✅ Working |
| 📊 | monitoring | View monitoring | ✅ Working |
| 🖥️ | canvas | Open in canvas | ✅ Working |
| 🔄 | restart | Restart app | ✅ Working |
| 📋 | clone | Clone app | ✅ Working |
| ⚙️ | edit-config | Edit resources | ✅ Working |
| 🗑️ | delete | Delete app | ✅ Working |

### Action Behavior Rules

#### Always Available:
- **delete** - Can delete in any state
- **volumes** - Can view volumes anytime
- **view-logs** - Can view logs anytime
- **console** - Can open console anytime
- **backups** - Can manage backups anytime
- **edit-config** - Can edit config anytime
- **clone** - Can clone anytime
- **update** - Can check for updates anytime

#### Running Only:
- **open-external** - Requires running + valid URL
- **canvas** - Requires running + valid URL
- **restart** - Requires app to be running
- **monitoring** - Requires running for live metrics

#### Toggle Status:
- When **stopped**: Shows ▶️ (Play) - Starts app
- When **running**: Shows ⏸️ (Pause) - Stops app
- Tooltip changes dynamically

## Files Modified

1. `/backend/frontend/js/components/auth-ui.js`
   - Fixed `Auth.getUser()` → `Auth.getUserInfo()`

2. `/backend/frontend/js/main.js`
   - Added missing imports: `confirmDeleteApp`, `startApp`, `stopApp`
   - Exposed modal functions to window
   - Exposed app operation functions to window

3. `/backend/frontend/js/components/app-card.js`
   - Added dynamic icon update for toggle-status button
   - Icon changes between 'play' and 'pause' based on app status
   - Tooltip updates dynamically

## Testing Checklist

### Logout
- [x] Click logout button
- [x] Verify no console errors
- [x] Verify user is logged out
- [x] Verify redirect to login page

### App Card Actions
- [x] **Play/Pause** - Toggle app status
  - [x] Icon changes from play to pause when running
  - [x] Icon changes from pause to play when stopped
  - [x] Tooltip updates correctly
- [x] **Open External** - Opens URL in new tab (running only)
- [x] **View Logs** - Opens logs modal
- [x] **Console** - Opens terminal console
- [x] **Backups** - Opens backup management
- [x] **Update** - Opens update modal
- [x] **Volumes** - Shows volume information
- [x] **Monitoring** - Opens monitoring modal (running only)
- [x] **Canvas** - Opens app in canvas view (running only)
- [x] **Restart** - Restarts the app (running only)
- [x] **Clone** - Opens clone modal
- [x] **Edit Config** - Opens resource editor
- [x] **Delete** - Shows deletion confirmation

## Additional Notes

### Action Priorities
The first action button (toggle-status) is the most important as it controls the app's primary state. The dynamic icon (play/pause) provides clear visual feedback about the current state and what action will be performed.

### Disabled State
Buttons that require the app to be running are automatically disabled when the app is stopped. They have:
- Reduced opacity (0.4)
- `disabled` attribute
- `disabled` class
- No hover effects
- Tooltip still works to explain why disabled

### Future Improvements
1. Add loading state to action buttons during operation
2. Add success/error feedback after action completes
3. Consider adding keyboard shortcuts for common actions
4. Add undo functionality for delete action
5. Batch operations (select multiple apps)

---
**Status:** ✅ All issues fixed
**Impact:** High - Core functionality restored
**Breaking Changes:** None
