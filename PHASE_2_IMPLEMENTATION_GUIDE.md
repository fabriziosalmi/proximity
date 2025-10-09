# 🚀 Phase 2 Implementation Guide

## Fearless Updates Feature

### Overview
The "Fearless Updates" feature allows users to update their applications without worry, by automatically creating a backup before the update and providing an easy rollback option.

### Backend Implementation

#### 1. Add Version Tracking

**File**: `backend/models/schemas.py`

Add version field to App model:
```python
class App(BaseModel):
    # ... existing fields ...
    catalog_version: Optional[str] = Field(None, description="Version of catalog item when deployed")
    available_version: Optional[str] = Field(None, description="Latest available version from catalog")
    update_available: bool = Field(False, description="Whether an update is available")
```

**File**: `backend/catalog/*.json`

Add version to catalog items:
```json
{
  "id": "nginx",
  "name": "Nginx",
  "version": "1.25.3",
  "changelog_url": "https://nginx.org/en/CHANGES",
  ...
}
```

#### 2. Add Update Endpoint

**File**: `backend/api/endpoints/apps.py`

```python
@router.post("/{app_id}/update")
async def update_app(
    app_id: str,
    update_data: dict,
    service: AppService = Depends(get_app_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an application to the latest catalog version.
    
    Process:
    1. Create automatic backup
    2. Update app configuration
    3. Rebuild container with new version
    4. Verify app is running
    5. Return backup ID for potential rollback
    """
    try:
        # Get app
        app = await service.get_app(app_id)
        
        # Create automatic backup first
        backup_id = await service.create_automatic_backup(
            app_id, 
            note="Pre-update backup"
        )
        
        # Perform update
        updated_app = await service.update_app_version(app_id)
        
        return {
            "success": True,
            "app": updated_app,
            "backup_id": backup_id,
            "message": "Update completed successfully"
        }
    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 3. Add Update Check Service

**File**: `backend/services/app_service.py`

```python
async def check_for_updates(self, app_id: str) -> dict:
    """
    Check if an update is available for an app.
    
    Returns:
        dict with update_available, current_version, latest_version
    """
    app = await self.get_app(app_id)
    
    # Load catalog item
    catalog_item = await self.catalog_service.get_item(app.catalog_id)
    
    current_version = app.catalog_version or "unknown"
    latest_version = catalog_item.version or "unknown"
    
    # Simple version comparison (can be enhanced)
    update_available = (
        latest_version != "unknown" and
        current_version != latest_version
    )
    
    return {
        "update_available": update_available,
        "current_version": current_version,
        "latest_version": latest_version,
        "changelog_url": catalog_item.changelog_url
    }

async def update_app_version(self, app_id: str) -> App:
    """
    Update app to latest catalog version.
    """
    app = await self.get_app(app_id)
    catalog_item = await self.catalog_service.get_item(app.catalog_id)
    
    # Stop app
    await self.proxmox_service.stop_lxc(app.node, app.lxc_id)
    
    # Execute update commands in container
    update_commands = [
        "cd /root",
        "docker-compose pull",  # Pull latest images
        "docker-compose up -d"  # Restart with new images
    ]
    
    for cmd in update_commands:
        await self.proxmox_service.execute_in_container(
            app.node, 
            app.lxc_id, 
            cmd
        )
    
    # Update version in database
    app.catalog_version = catalog_item.version
    app.updated_at = datetime.now()
    self.db.commit()
    
    return app
```

### Frontend Implementation

#### 1. Update Badge Component

**File**: `backend/frontend/app.js`

Add to app card rendering:
```javascript
function renderAppCard(app) {
    // ... existing code ...
    
    // Check for updates
    const updateBadge = app.update_available ? `
        <div class="update-badge" title="Update available: ${app.available_version}">
            <i data-lucide="arrow-up-circle"></i>
            Update Available
        </div>
    ` : '';
    
    return `
        <div class="app-card deployed" data-app-id="${app.id}">
            ${updateBadge}
            <!-- rest of card -->
        </div>
    `;
}
```

#### 2. Update Modal

**File**: `backend/frontend/index.html`

Add update modal:
```html
<!-- Update Modal -->
<div id="updateModal" class="modal">
    <div class="modal-content" style="max-width: 500px;">
        <div class="modal-header">
            <h2 class="modal-title">
                <i data-lucide="arrow-up-circle"></i>
                Update <span id="update-app-name"></span>
            </h2>
            <button class="modal-close" onclick="hideUpdateModal()">✕</button>
        </div>
        <div class="modal-body">
            <div class="update-info">
                <div class="version-info">
                    <div class="version-current">
                        <label>Current Version</label>
                        <span id="update-current-version">1.0.0</span>
                    </div>
                    <i data-lucide="arrow-right"></i>
                    <div class="version-new">
                        <label>New Version</label>
                        <span id="update-new-version">2.0.0</span>
                    </div>
                </div>
                
                <div class="update-benefits">
                    <h4>✓ Safe Update Process</h4>
                    <ul>
                        <li><strong>Automatic Backup</strong> - A backup is created before updating</li>
                        <li><strong>Easy Rollback</strong> - Restore previous version if needed</li>
                        <li><strong>Zero Config</strong> - Your settings are preserved</li>
                    </ul>
                </div>
                
                <div id="update-changelog" class="update-changelog">
                    <!-- Changelog will be loaded here -->
                </div>
            </div>
            
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="hideUpdateModal()">
                    Cancel
                </button>
                <button class="btn btn-primary" onclick="confirmUpdate()">
                    <i data-lucide="check"></i>
                    Update Now
                </button>
            </div>
        </div>
    </div>
</div>
```

#### 3. Update Functions

**File**: `backend/frontend/app.js`

```javascript
let currentUpdateApp = null;

/**
 * Show update modal for an app
 */
async function showUpdateModal(appId) {
    try {
        // Get app details
        const app = await authFetch(`${API_BASE}/apps/${appId}`);
        
        // Check for updates
        const updateInfo = await authFetch(`${API_BASE}/apps/${appId}/update-check`);
        
        if (!updateInfo.update_available) {
            showNotification('App is already up to date', 'info');
            return;
        }
        
        currentUpdateApp = appId;
        
        // Populate modal
        document.getElementById('update-app-name').textContent = app.name;
        document.getElementById('update-current-version').textContent = 
            updateInfo.current_version;
        document.getElementById('update-new-version').textContent = 
            updateInfo.latest_version;
        
        // Load changelog if available
        if (updateInfo.changelog_url) {
            document.getElementById('update-changelog').innerHTML = `
                <a href="${updateInfo.changelog_url}" target="_blank" class="btn btn-link">
                    View Changelog
                </a>
            `;
        }
        
        // Show modal
        document.getElementById('updateModal').style.display = 'flex';
        
        // Refresh icons
        setTimeout(() => lucide.createIcons(), 100);
        
    } catch (error) {
        showNotification('Failed to check for updates', 'error');
        console.error('Update check error:', error);
    }
}

/**
 * Hide update modal
 */
function hideUpdateModal() {
    document.getElementById('updateModal').style.display = 'none';
    currentUpdateApp = null;
}

/**
 * Confirm and execute update
 */
async function confirmUpdate() {
    if (!currentUpdateApp) return;
    
    try {
        hideUpdateModal();
        showNotification('Starting update... (this may take a few minutes)', 'info');
        
        // Execute update
        const result = await authFetch(`${API_BASE}/apps/${currentUpdateApp}/update`, {
            method: 'POST',
            body: JSON.stringify({})
        });
        
        if (result.success) {
            showNotification(
                `Update completed successfully! Backup created: ${result.backup_id}`, 
                'success'
            );
            
            // Refresh app list
            await loadApps();
        } else {
            throw new Error(result.message || 'Update failed');
        }
        
    } catch (error) {
        showNotification('Update failed: ' + error.message, 'error');
        console.error('Update error:', error);
    }
}

/**
 * Check for updates for all apps (background task)
 */
async function checkAllAppsForUpdates() {
    try {
        const response = await authFetch(`${API_BASE}/apps`);
        const apps = response.apps || response || [];
        
        for (const app of apps) {
            try {
                const updateInfo = await authFetch(
                    `${API_BASE}/apps/${app.id}/update-check`
                );
                
                // Update app object with update info
                app.update_available = updateInfo.update_available;
                app.available_version = updateInfo.latest_version;
                
            } catch (error) {
                console.error(`Update check failed for ${app.id}:`, error);
            }
        }
        
        return apps;
    } catch (error) {
        console.error('Failed to check updates:', error);
        return [];
    }
}
```

### CSS Styling

**File**: `backend/frontend/css/styles.css`

```css
/* Update Badge */
.update-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    color: #000;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.25rem;
    z-index: 10;
    box-shadow: 0 2px 8px rgba(251, 191, 36, 0.3);
    animation: pulse 2s ease-in-out infinite;
}

.update-badge i {
    width: 14px;
    height: 14px;
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.7;
    }
}

/* Update Modal */
.update-info {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.version-info {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    padding: 1.5rem;
    background: var(--surface);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border);
}

.version-current,
.version-new {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
}

.version-current label,
.version-new label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.05em;
}

.version-current span {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-secondary);
}

.version-new span {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary);
}

.update-benefits {
    padding: 1.5rem;
    background: linear-gradient(135deg, rgba(74, 222, 128, 0.1) 0%, rgba(34, 211, 238, 0.1) 100%);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(74, 222, 128, 0.2);
}

.update-benefits h4 {
    margin: 0 0 1rem 0;
    color: var(--success);
    font-size: 1rem;
}

.update-benefits ul {
    margin: 0;
    padding-left: 1.5rem;
    list-style: none;
}

.update-benefits li {
    margin: 0.5rem 0;
    color: var(--text-secondary);
    position: relative;
}

.update-benefits li::before {
    content: "✓";
    position: absolute;
    left: -1.5rem;
    color: var(--success);
    font-weight: 700;
}

.update-benefits li strong {
    color: var(--text-primary);
}

.update-changelog {
    text-align: center;
}
```

---

## PRO Mode Feature

### Overview
PRO Mode unlocks advanced features (Clone, Config Edit) for power users while keeping the basic UX simple.

### Backend Implementation

**File**: `backend/models/schemas.py`

```python
class UserSettings(BaseModel):
    """User settings"""
    user_id: str
    pro_mode_enabled: bool = False
    theme: str = "dark"
    notifications_enabled: bool = True
    
class UserSettingsUpdate(BaseModel):
    """Update user settings"""
    pro_mode_enabled: Optional[bool] = None
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None
```

**File**: `backend/api/endpoints/users.py`

```python
@router.get("/me/settings")
async def get_user_settings(
    current_user: dict = Depends(get_current_user)
):
    """Get user settings"""
    # Implementation
    pass

@router.patch("/me/settings")
async def update_user_settings(
    settings: UserSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user settings"""
    # Implementation
    pass
```

### Frontend Implementation

**File**: `backend/frontend/app.js`

```javascript
// Global state for PRO mode
let proModeEnabled = false;

/**
 * Load user settings
 */
async function loadUserSettings() {
    try {
        const settings = await authFetch(`${API_BASE}/users/me/settings`);
        proModeEnabled = settings.pro_mode_enabled || false;
        
        // Update UI based on PRO mode
        updateProModeUI();
        
    } catch (error) {
        console.error('Failed to load user settings:', error);
    }
}

/**
 * Toggle PRO mode
 */
async function toggleProMode(enabled) {
    try {
        await authFetch(`${API_BASE}/users/me/settings`, {
            method: 'PATCH',
            body: JSON.stringify({
                pro_mode_enabled: enabled
            })
        });
        
        proModeEnabled = enabled;
        updateProModeUI();
        
        showNotification(
            enabled ? 'PRO Mode enabled' : 'PRO Mode disabled',
            'success'
        );
        
        // Refresh app list to show/hide PRO features
        await loadApps();
        
    } catch (error) {
        showNotification('Failed to update PRO mode', 'error');
        console.error('PRO mode toggle error:', error);
    }
}

/**
 * Update UI based on PRO mode
 */
function updateProModeUI() {
    const proFeatures = document.querySelectorAll('.pro-feature');
    
    proFeatures.forEach(element => {
        if (proModeEnabled) {
            element.classList.remove('hidden');
        } else {
            element.classList.add('hidden');
        }
    });
}
```

**Add PRO buttons to app cards**:

```javascript
// In renderAppCard function
const proButtons = proModeEnabled ? `
    <button class="action-icon pro-feature" title="Clone App" 
            onclick="event.stopPropagation(); cloneAppModal('${app.id}')">
        <i data-lucide="copy"></i>
    </button>
    <button class="action-icon pro-feature" title="Edit Config" 
            onclick="event.stopPropagation(); editConfigModal('${app.id}')">
        <i data-lucide="edit"></i>
    </button>
` : '';
```

---

## Testing

### Update Feature Tests

```python
# e2e_tests/test_update_feature.py

@pytest.mark.e2e
def test_update_flow(authenticated_page: Page):
    """Test complete update flow with automatic backup"""
    # Deploy app
    # Wait for update badge to appear
    # Click update button
    # Verify backup created
    # Verify update completed
    # Verify app still works
    pass
```

### PRO Mode Tests

```python
# e2e_tests/test_pro_mode.py

@pytest.mark.e2e
def test_pro_mode_toggle(authenticated_page: Page):
    """Test PRO mode enables/disables advanced features"""
    # Open settings
    # Enable PRO mode
    # Verify Clone/Edit buttons appear
    # Disable PRO mode
    # Verify buttons hidden
    pass
```

---

## Deployment Checklist

### Fearless Updates
- [ ] Add version field to catalog items
- [ ] Implement update check endpoint
- [ ] Implement update execution endpoint
- [ ] Create update modal UI
- [ ] Add update badge to app cards
- [ ] Test update flow end-to-end
- [ ] Document update process

### PRO Mode
- [ ] Create user settings model
- [ ] Implement settings endpoints
- [ ] Add PRO mode toggle to settings
- [ ] Hide/show advanced features based on mode
- [ ] Create Clone modal
- [ ] Create Config Edit modal
- [ ] Test PRO mode toggle
- [ ] Document PRO features

---

## Estimated Time

- **Fearless Updates**: 8-12 hours
  - Backend: 4-6 hours
  - Frontend: 3-4 hours
  - Testing: 1-2 hours

- **PRO Mode**: 6-10 hours
  - Backend: 2-3 hours
  - Frontend: 3-5 hours
  - Testing: 1-2 hours

**Total**: 14-22 hours for complete Phase 2 implementation.
