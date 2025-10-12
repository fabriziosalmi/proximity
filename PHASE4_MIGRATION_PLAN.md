# Phase 4 Migration Plan - App Operations Extraction

**Date**: October 12, 2025  
**Status**: Planning Complete, Ready to Execute  
**Estimated Time**: 2-3 hours  
**Target Lines**: ~1,500 lines

---

## 🎯 Objectives

Extract app control and management operations from `app.js` into dedicated service modules, continuing the modular architecture established in Phases 1-3.

### Primary Goals:
1. Create `js/services/appOperations.js` for app control logic
2. Extract search/filter functionality
3. Consolidate data loading functions
4. Reduce app.js by ~1,500 lines
5. Maintain backward compatibility during transition

---

## 🔍 Current State Analysis

### Functions to Extract from app.js:

#### 1. **App Control Operations** (~400 lines)
Located around lines 1800-2200 in app.js:
- `controlApp(appId, action)` - Start/stop/restart apps
- `confirmDeleteApp(appId, appName)` - Delete confirmation
- `deleteApp(appId)` - App deletion logic
- `showUpdateModal(appId)` - Update workflow
- `performUpdate(appId, appName)` - Update execution
- `pollAppStatus(appId, targetStatus, timeout)` - Status polling

#### 2. **Search & Filter Operations** (~200 lines)
Located around lines 780-980:
- `searchCatalog(query)` - Catalog search
- `clearCatalogSearch()` - Clear search
- `filterApps(filters)` - App filtering
- `applyFilters()` - Filter application
- Search state management

#### 3. **Data Loading Operations** (~300 lines)
Located around lines 1100-1400:
- `loadApps()` - Load deployed apps
- `loadCatalog()` - Load catalog data
- `refreshAppList()` - Refresh apps
- `loadAppDetails(appId)` - Get app details
- Data caching logic

#### 4. **Backup Operations** (~350 lines)
Located around lines 5200-5550:
- `showBackupModal(appId)` - Backup modal
- `loadBackups(appId)` - List backups
- `createBackup(appId)` - Create backup
- `restoreBackup(appId, backupId)` - Restore backup
- `deleteBackup(appId, backupId)` - Delete backup
- Backup polling logic

#### 5. **Clone & Config Operations** (~250 lines)
Located around lines 4800-5050:
- `showCloneModal(appId, appName)` - Clone modal
- `cloneApp(appId, newName)` - Clone logic
- `showEditConfigModal(appId, appName)` - Config editor
- `saveConfig(appId, config)` - Save configuration
- Config validation

---

## 📋 Phase 4 Execution Plan

### Step 1: Create `js/services/appOperations.js` (60 min)

**Purpose**: Core app control operations

**Functions to Extract**:
```javascript
export async function controlApp(appId, action) {
    // Start/stop/restart logic
}

export async function deleteApp(appId, appName) {
    // Deletion logic with confirmation
}

export async function updateApp(appId, appName) {
    // Update workflow
}

export async function pollAppStatus(appId, targetStatus, timeout) {
    // Status polling with timeout
}

export function confirmDeleteApp(appId, appName) {
    // Delete confirmation modal
}
```

**Dependencies to Import**:
- `authFetch` from `../utils/auth.js`
- `showNotification` from `../utils/notifications.js`
- `showLoading`, `hideLoading` from `../utils/loading.js`
- `API_BASE` constant

**Test**:
```javascript
import { controlApp } from './js/services/appOperations.js';
await controlApp('app-123', 'restart');
```

---

### Step 2: Create `js/services/searchService.js` (30 min)

**Purpose**: Search and filter functionality

**Functions to Extract**:
```javascript
export function searchCatalog(query, items) {
    // Search logic
    return filteredItems;
}

export function filterApps(apps, filters) {
    // Filter logic
    return filteredApps;
}

export function clearSearch() {
    // Clear search state
}
```

**State Management**:
- Use local state within service
- Expose getters for search state
- No direct DOM manipulation

**Test**:
```javascript
import { searchCatalog } from './js/services/searchService.js';
const results = searchCatalog('wordpress', catalogItems);
```

---

### Step 3: Create `js/services/dataService.js` (45 min)

**Purpose**: Data loading and caching

**Functions to Extract**:
```javascript
export async function loadApps() {
    // Load deployed apps
    return apps;
}

export async function loadCatalog() {
    // Load catalog with caching
    return catalog;
}

export async function refreshAppList() {
    // Refresh apps
}

export async function loadAppDetails(appId) {
    // Get specific app details
    return app;
}
```

**Caching Strategy**:
- Cache catalog data (5 min TTL)
- Always fetch fresh app data
- Expose cache invalidation

**Test**:
```javascript
import { loadApps, loadCatalog } from './js/services/dataService.js';
const apps = await loadApps();
const catalog = await loadCatalog();
```

---

### Step 4: Create `js/services/backupService.js` (45 min)

**Purpose**: Backup management operations

**Functions to Extract**:
```javascript
export async function listBackups(appId) {
    // List all backups
    return backups;
}

export async function createBackup(appId) {
    // Create backup
    return backupId;
}

export async function restoreBackup(appId, backupId) {
    // Restore from backup
}

export async function deleteBackup(appId, backupId) {
    // Delete backup
}

export function startBackupPolling(appId, callback) {
    // Poll backup status
    return intervalId;
}
```

**Features**:
- Status polling for async operations
- Progress callbacks
- Error handling

**Test**:
```javascript
import { listBackups, createBackup } from './js/services/backupService.js';
const backups = await listBackups('app-123');
await createBackup('app-123');
```

---

### Step 5: Create `js/services/configService.js` (30 min)

**Purpose**: App configuration management

**Functions to Extract**:
```javascript
export async function loadConfig(appId) {
    // Load app config
    return config;
}

export async function saveConfig(appId, config) {
    // Save config
}

export function validateConfig(config) {
    // Validate configuration
    return { valid: true, errors: [] };
}

export async function cloneApp(appId, newName, config) {
    // Clone app with config
    return newAppId;
}
```

**Validation**:
- Schema validation
- Type checking
- Required fields

**Test**:
```javascript
import { loadConfig, saveConfig } from './js/services/configService.js';
const config = await loadConfig('app-123');
await saveConfig('app-123', updatedConfig);
```

---

## 🔄 Update Strategy for Existing Code

### Update Views to Use New Services

#### AppsView.js:
```javascript
// Add imports
import { controlApp, deleteApp } from '../services/appOperations.js';
import { loadApps, refreshAppList } from '../services/dataService.js';

// Replace window.* calls
// OLD: window.controlApp(appId, 'restart')
// NEW: await controlApp(appId, 'restart')
```

#### CatalogView.js:
```javascript
// Add imports
import { searchCatalog } from '../services/searchService.js';
import { loadCatalog } from '../services/dataService.js';

// Replace window.* calls
```

#### Modals:
Update existing modals to use new services:
- BackupModal.js → use backupService
- CloneModal.js → use configService
- EditConfigModal.js → use configService

---

## ⏱️ Time Estimates

| Task | Time | Cumulative |
|------|------|------------|
| 4.1: appOperations.js | 60 min | 60 min |
| 4.2: searchService.js | 30 min | 90 min |
| 4.3: dataService.js | 45 min | 135 min |
| 4.4: backupService.js | 45 min | 180 min |
| 4.5: configService.js | 30 min | 210 min |
| Update views | 20 min | 230 min |
| Update modals | 20 min | 250 min |
| Testing | 30 min | 280 min |

**Total**: ~4.5 hours (rounded to 2-3 hours with optimizations)

---

## 🧪 Testing Strategy

### After Each Service Creation:
1. ✅ Import service in browser console
2. ✅ Test each exported function
3. ✅ Verify no console errors
4. ✅ Check API calls work correctly

### Integration Testing:
1. ✅ Test app start/stop/restart
2. ✅ Test app deletion
3. ✅ Test search functionality
4. ✅ Test backup creation/restore
5. ✅ Test app cloning
6. ✅ Verify all views still work

### E2E Testing:
```bash
pytest e2e_tests/test_app_lifecycle.py -v
pytest e2e_tests/test_catalog_navigation.py -v
pytest e2e_tests/ -v
```

---

## 📊 Expected Outcome

### Before Phase 4:
```
app.js: 6,304 lines
services/: Limited functionality
```

### After Phase 4:
```
app.js: ~4,800 lines (-1,500 lines, -24%)
services/appOperations.js: 400 lines (NEW)
services/searchService.js: 200 lines (NEW)
services/dataService.js: 300 lines (NEW)
services/backupService.js: 350 lines (NEW)
services/configService.js: 250 lines (NEW)
```

**Total Migration**: 5,291 / 7,090 lines (75% complete)

---

## 🚨 Potential Issues & Solutions

### Issue 1: Circular Dependencies
**Problem**: Services import each other
**Solution**: Use dependency injection or event emitters

### Issue 2: State Management
**Problem**: Services need shared state
**Solution**: Pass state as parameters or use AppState

### Issue 3: Modal Integration
**Problem**: Services need to show modals
**Solution**: Return promises, let caller handle UI

### Issue 4: Error Handling
**Problem**: Inconsistent error handling
**Solution**: Standardize error format across services

---

## 📝 Commit Strategy

### After Each Service:
```bash
git add js/services/serviceName.js
git commit -m "refactor: Phase 4.X - Create serviceName service

- Extracted [functions] from app.js
- ~[X] lines migrated
- Service tested and working
- Ready for integration"
```

### After All Services:
```bash
git add js/services/ js/views/ js/modals/ app.js PHASE4_PROGRESS.md
git commit -m "refactor: Phase 4 COMPLETE - App Operations Extraction

- Created 5 new service modules
- ~1,500 lines migrated from app.js
- app.js reduced to ~4,800 lines (-24%)
- All services tested and integrated
- E2E tests passing
- Overall refactoring 75% complete"
```

---

## 🎯 Success Criteria

Phase 4 will be complete when:
- ✅ All 5 service modules created
- ✅ ~1,500 lines extracted from app.js
- ✅ All views updated to use services
- ✅ All modals updated to use services
- ✅ No regressions in functionality
- ✅ All E2E tests passing
- ✅ app.js under 5,000 lines

---

## 📚 Reference: Function Locations in app.js

Quick reference for extraction (approximate line numbers):

```
App Control:
- controlApp(): ~1850
- deleteApp(): ~1920
- confirmDeleteApp(): ~1900
- updateApp(): ~5400
- pollAppStatus(): ~1950

Search/Filter:
- searchCatalog(): ~780
- clearCatalogSearch(): ~820
- filterApps(): ~850

Data Loading:
- loadApps(): ~1200
- loadCatalog(): ~1280
- refreshAppList(): ~1350
- loadAppDetails(): ~1380

Backups:
- showBackupModal(): ~5200
- loadBackups(): ~5250
- createBackup(): ~5300
- restoreBackup(): ~5350
- deleteBackup(): ~5400

Config/Clone:
- showCloneModal(): ~4800
- cloneApp(): ~4850
- showEditConfigModal(): ~4900
- saveConfig(): ~4950
```

Use `grep -n "function name" app.js` to find exact locations.

---

## 🚀 Next Session Checklist

**Before Starting**:
1. ✅ Phase 3 committed
2. ✅ Read this plan
3. ✅ Verify app.js is working
4. ✅ Run baseline tests

**Start With**:
1. Create `js/services/appOperations.js`
2. Extract `controlApp()` first (most critical)
3. Test in isolation
4. Extract remaining operations
5. Update views incrementally

**Then**:
1. Create other services one by one
2. Test after each creation
3. Update dependent code
4. Verify no regressions

---

**Phase 4 Status**: 📋 **PLANNED**  
**Next Action**: Create appOperations.js 🚀  
**Ready to Execute**: ✅ Yes
