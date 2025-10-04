# Backup & Restore Feature - Implementation Plan

**Status:** ⏳ IN PROGRESS - Database Models Complete
**Date Started:** October 4, 2025

---

## ✅ Completed Steps

### Step 1.1: Database Models ✅ DONE

**Files Modified:**
- `backend/models/database.py` - Added `Backup` model
- `backend/models/schemas.py` - Added `Backup`, `BackupStatus`, `BackupCreate`, `BackupList` schemas

**Backup Database Model:**
```python
class Backup(Base):
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(String(255), ForeignKey("apps.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    storage_name = Column(String(100), nullable=False, default="local")
    size_bytes = Column(Integer, nullable=True)
    backup_type = Column(String(50), nullable=False, default="vzdump")
    status = Column(String(50), nullable=False, index=True)
    error_message = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationship
    app = relationship("App", back_populates="backups")
```

**Relationships:**
- ✅ App.backups (one-to-many, cascade delete)
- ✅ Backup.app (many-to-one)

---

## 📋 Remaining Steps

### Step 1.2: Database Model Tests (NEXT)

**Create:** `tests/test_backup_model.py`

**Required Tests:**
```python
class TestBackupModel:
    def test_create_backup(self, db_session, test_app):
        """Test creating a backup"""
        backup = Backup(
            app_id=test_app.id,
            filename="vzdump-lxc-100-2025_10_04-12_00_00.tar.zst",
            storage_name="local",
            backup_type="vzdump",
            status="creating"
        )
        db_session.add(backup)
        db_session.commit()

        assert backup.id is not None
        assert backup.status == "creating"

    def test_backup_app_relationship(self, db_session, test_app):
        """Test backup-app relationship"""
        # Test cascade, foreign keys, etc.

    def test_backup_status_transitions(self, db_session, test_app):
        """Test status changes: creating → available → restoring"""
```

---

### Step 1.3: BackupService Implementation (TDD Approach)

**Create:** `backend/services/backup_service.py`

**Service Methods to Implement:**

1. **`async def create_backup(app_id, backup_type, storage, compress, mode)`**
   - Get app from database
   - Validate app exists and is running
   - Call Proxmox `vzdump` API
   - Create Backup record with status='creating'
   - Start background task to poll for completion
   - Return Backup object

2. **`async def list_backups_for_app(app_id)`**
   - Query all backups for app_id
   - Return list of Backup objects

3. **`async def get_backup(backup_id, app_id)`**
   - Get specific backup
   - Verify belongs to app
   - Return Backup object

4. **`async def restore_from_backup(backup_id, app_id)`**
   - Get backup and app
   - Validate backup status is 'available'
   - Stop the app
   - Call Proxmox restore (pct restore)
   - Start the app
   - Update app status

5. **`async def delete_backup(backup_id, app_id)`**
   - Get backup
   - Call Proxmox to delete backup file
   - Delete from database

6. **`async def _poll_backup_completion(backup_id, task_id)`** (Background)
   - Poll Proxmox task status
   - Update backup record when complete
   - Set size_bytes, completed_at, status

**Required Proxmox Methods (add to ProxmoxService):**
```python
async def create_vzdump(node, vmid, storage, compress, mode):
    """Create LXC backup using vzdump"""
    # POST /nodes/{node}/vzdump

async def get_backup_list(node, vmid):
    """List backups for a container"""
    # GET /nodes/{node}/storage/{storage}/content?vmid={vmid}

async def restore_backup(node, vmid, backup_file, storage):
    """Restore from backup"""
    # POST /nodes/{node}/lxc
    # with restore=1 and archive parameter

async def delete_backup(node, storage, backup_file):
    """Delete a backup file"""
    # DELETE /nodes/{node}/storage/{storage}/content/{backup_file}
```

---

### Step 1.4: BackupService Tests

**Create:** `tests/test_backup_service.py`

**Test Structure:**
```python
class TestBackupService:
    @pytest.mark.asyncio
    async def test_create_backup_success(self, app_service, db_session, test_app):
        """Test successful backup creation"""
        # Mock proxmox_service.create_vzdump
        # Call backup_service.create_backup
        # Assert backup record created with status='creating'
        # Assert vzdump was called with correct params

    @pytest.mark.asyncio
    async def test_create_backup_app_not_found(self):
        """Test backup creation for nonexistent app"""
        # Should raise AppNotFoundError

    @pytest.mark.asyncio
    async def test_list_backups_for_app(self):
        """Test listing backups"""
        # Create multiple backups in DB
        # Call list_backups_for_app
        # Assert correct backups returned

    @pytest.mark.asyncio
    async def test_restore_from_backup_success(self):
        """Test successful restore"""
        # Mock stop, restore, start
        # Verify called in correct order
        # Assert app status updated

    @pytest.mark.asyncio
    async def test_restore_from_backup_not_available(self):
        """Test restore when backup is still creating"""
        # Should raise error

    @pytest.mark.asyncio
    async def test_delete_backup_success(self):
        """Test backup deletion"""
        # Mock proxmox delete
        # Verify DB record deleted
```

---

### Step 1.5: API Endpoints

**Create:** `backend/api/endpoints/backups.py`

**Endpoints:**

```python
router = APIRouter()

@router.post("/apps/{app_id}/backups", status_code=202)
async def create_backup(
    app_id: str,
    backup_data: BackupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Backup:
    """Create a new backup for an application"""
    # Verify app belongs to user
    # Call backup_service.create_backup
    # Return backup object

@router.get("/apps/{app_id}/backups")
async def list_backups(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> BackupList:
    """List all backups for an application"""

@router.get("/apps/{app_id}/backups/{backup_id}")
async def get_backup(
    app_id: str,
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Backup:
    """Get a specific backup"""

@router.post("/apps/{app_id}/backups/{backup_id}/restore")
async def restore_backup(
    app_id: str,
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """Restore an application from a backup"""

@router.delete("/apps/{app_id}/backups/{backup_id}")
async def delete_backup(
    app_id: str,
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """Delete a backup"""
```

**Register in main.py:**
```python
from api.endpoints import backups

app.include_router(backups.router, prefix="/api/v1", tags=["backups"])
```

---

### Step 1.6: API Endpoint Tests

**Add to:** `tests/test_api_endpoints.py`

```python
class TestBackupEndpoints:
    def test_create_backup_success(self, client, auth_headers, test_app):
        response = client.post(
            f"/api/v1/apps/{test_app.id}/backups",
            headers=auth_headers,
            json={"backup_type": "vzdump", "compress": "zstd"}
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "creating"

    def test_create_backup_unauthorized(self, client):
        response = client.post("/api/v1/apps/test-app/backups")
        assert response.status_code == 401

    def test_list_backups(self, client, auth_headers, test_app):
        # Create backups first
        # Then list and verify

    def test_restore_backup(self, client, auth_headers, test_app, test_backup):
        response = client.post(
            f"/api/v1/apps/{test_app.id}/backups/{test_backup.id}/restore",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_delete_backup(self, client, auth_headers, test_app, test_backup):
        response = client.delete(
            f"/api/v1/apps/{test_app.id}/backups/{test_backup.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
```

---

## Step 2: Frontend Implementation

### Step 2.1: Backup Modal HTML

**Add to:** `backend/index.html`

```html
<!-- Backup Management Modal -->
<div id="backup-modal" class="modal">
    <div class="modal-content">
        <span class="close" onclick="hideBackupModal()">&times;</span>
        <h2>Backups for <span id="backup-app-name"></span></h2>

        <button class="btn btn-primary" onclick="createBackup()">
            <i data-lucide="plus"></i> Create New Backup
        </button>

        <div id="backup-list" class="backup-list">
            <!-- Backups will be loaded here -->
        </div>
    </div>
</div>
```

### Step 2.2: Backup JavaScript

**Add to:** `backend/app.js`

```javascript
// Global state
let currentBackupAppId = null;

async function showBackupModal(appId) {
    currentBackupAppId = appId;

    // Get app details
    const app = await authFetch(`${API_BASE}/apps/${appId}`);
    document.getElementById('backup-app-name').textContent = app.name;

    // Load backups
    await loadBackups(appId);

    // Show modal
    document.getElementById('backup-modal').style.display = 'block';
}

function hideBackupModal() {
    document.getElementById('backup-modal').style.display = 'none';
    currentBackupAppId = null;
}

async function loadBackups(appId) {
    try {
        const response = await authFetch(`${API_BASE}/apps/${appId}/backups`);
        const { backups } = response;

        const listEl = document.getElementById('backup-list');

        if (backups.length === 0) {
            listEl.innerHTML = '<p class="empty-state">No backups yet</p>';
            return;
        }

        listEl.innerHTML = backups.map(backup => `
            <div class="backup-item" data-backup-id="${backup.id}">
                <div class="backup-info">
                    <div class="backup-filename">${backup.filename}</div>
                    <div class="backup-meta">
                        <span class="backup-date">${formatDate(backup.created_at)}</span>
                        <span class="backup-size">${formatSize(backup.size_bytes)}</span>
                        <span class="backup-status status-${backup.status}">${backup.status}</span>
                    </div>
                </div>
                <div class="backup-actions">
                    ${backup.status === 'available' ? `
                        <button class="btn btn-sm btn-secondary" onclick="restoreBackup('${appId}', ${backup.id})">
                            <i data-lucide="rotate-ccw"></i> Restore
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-danger" onclick="deleteBackup('${appId}', ${backup.id})">
                        <i data-lucide="trash-2"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');

        // Refresh icons
        lucide.createIcons();

        // Start polling for creating backups
        startBackupPolling(appId, backups);

    } catch (error) {
        showNotification('Failed to load backups', 'error');
        console.error('Error loading backups:', error);
    }
}

async function createBackup() {
    if (!currentBackupAppId) return;

    try {
        showNotification('Creating backup...', 'info');

        await authFetch(`${API_BASE}/apps/${currentBackupAppId}/backups`, {
            method: 'POST',
            body: JSON.stringify({
                backup_type: 'vzdump',
                compress: 'zstd',
                mode: 'snapshot'
            })
        });

        showNotification('Backup started', 'success');

        // Reload backups
        await loadBackups(currentBackupAppId);

    } catch (error) {
        showNotification('Failed to create backup', 'error');
        console.error('Error creating backup:', error);
    }
}

async function restoreBackup(appId, backupId) {
    if (!confirm('Are you sure you want to restore from this backup? This will replace the current application state.')) {
        return;
    }

    try {
        showNotification('Restoring from backup...', 'info');

        await authFetch(`${API_BASE}/apps/${appId}/backups/${backupId}/restore`, {
            method: 'POST'
        });

        showNotification('Restore successful', 'success');
        hideBackupModal();

        // Refresh app list
        await loadApps();

    } catch (error) {
        showNotification('Failed to restore backup', 'error');
        console.error('Error restoring backup:', error);
    }
}

async function deleteBackup(appId, backupId) {
    if (!confirm('Are you sure you want to delete this backup?')) {
        return;
    }

    try {
        await authFetch(`${API_BASE}/apps/${appId}/backups/${backupId}`, {
            method: 'DELETE'
        });

        showNotification('Backup deleted', 'success');

        // Reload backups
        await loadBackups(appId);

    } catch (error) {
        showNotification('Failed to delete backup', 'error');
        console.error('Error deleting backup:', error);
    }
}

function startBackupPolling(appId, backups) {
    const creatingBackups = backups.filter(b => b.status === 'creating');

    if (creatingBackups.length > 0) {
        // Poll every 5 seconds
        setTimeout(() => loadBackups(appId), 5000);
    }
}

function formatSize(bytes) {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}
```

### Step 2.3: Backup CSS

**Add to:** `backend/styles.css`

```css
/* Backup Modal */
.backup-list {
    margin-top: 1.5rem;
    max-height: 500px;
    overflow-y: auto;
}

.backup-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: var(--card-bg);
    border-radius: 8px;
    margin-bottom: 0.75rem;
    border: 1px solid var(--border);
}

.backup-info {
    flex: 1;
}

.backup-filename {
    font-weight: 600;
    margin-bottom: 0.5rem;
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 0.9rem;
}

.backup-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.85rem;
    color: var(--text-secondary);
}

.backup-status {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-weight: 600;
}

.backup-status.status-available {
    background: var(--success-bg);
    color: var(--success);
}

.backup-status.status-creating {
    background: var(--warning-bg);
    color: var(--warning);
}

.backup-status.status-failed {
    background: var(--error-bg);
    color: var(--error);
}

.backup-actions {
    display: flex;
    gap: 0.5rem;
}

.empty-state {
    text-align: center;
    padding: 3rem;
    color: var(--text-secondary);
}
```

### Step 2.4: Add to App Card Menu

**Modify:** App card action menu in `backend/app.js`

```javascript
// In the app card HTML generation, add:
<button class="menu-item" onclick="showBackupModal('${app.id}')">
    <i data-lucide="database"></i>
    <span>Backups</span>
</button>
```

---

## Step 3: E2E Tests

**Create:** `e2e_tests/tests/test_backup_restore_flow.py`

```python
import pytest
from playwright.sync_api import Page, expect

def test_full_backup_and_restore_workflow(
    authenticated_page: Page,
    deployed_app_fixture
):
    """Test complete backup and restore workflow"""
    page = authenticated_page
    app_id = deployed_app_fixture

    # Navigate to dashboard
    page.goto("http://localhost:8000")

    # Open app menu
    page.locator(f"[data-app-id='{app_id}'] .app-menu-button").click()

    # Click Backups
    page.locator("text=Backups").click()

    # Wait for modal
    expect(page.locator("#backup-modal")).to_be_visible()

    # Verify empty state
    expect(page.locator(".empty-state")).to_be_visible()

    # Create backup
    page.locator("text=Create New Backup").click()

    # Wait for backup to appear in list
    expect(page.locator(".backup-item")).to_be_visible(timeout=10000)

    # Wait for status to change from creating to available
    expect(
        page.locator(".backup-status.status-available")
    ).to_be_visible(timeout=180000)  # 3 minutes

    # Restore backup
    page.locator("text=Restore").click()

    # Confirm dialog
    page.on("dialog", lambda dialog: dialog.accept())

    # Wait for success notification
    expect(page.locator(".notification.success")).to_be_visible(timeout=60000)

    # Verify app still running
    expect(page.locator(f"[data-app-id='{app_id}'] .status-running")).to_be_visible()

    # Delete backup
    page.locator("text=Backups").click()
    page.locator(".backup-item button:has-text('Delete')").click()
    page.on("dialog", lambda dialog: dialog.accept())

    # Verify backup removed
    expect(page.locator(".backup-item")).to_have_count(0)
```

---

## 📊 Implementation Checklist

### Backend
- [x] Database model (Backup)
- [x] Pydantic schemas (Backup, BackupCreate, BackupList, BackupStatus)
- [ ] Database model tests
- [ ] BackupService implementation
- [ ] BackupService tests
- [ ] Proxmox backup methods
- [ ] API endpoints
- [ ] API endpoint tests
- [ ] Database migration

### Frontend
- [ ] Backup modal HTML
- [ ] Backup JavaScript functions
- [ ] Backup CSS styles
- [ ] Add to app menu
- [ ] Polling for backup status

### E2E Tests
- [ ] Backup creation test
- [ ] Backup restore test
- [ ] Backup deletion test
- [ ] Full workflow test

### Documentation
- [ ] API documentation (Swagger)
- [ ] User guide
- [ ] Architecture documentation

---

## 🚀 Next Steps

1. **Database Migration:**
   ```bash
   cd backend
   python migrate_db.py  # Or use Alembic
   ```

2. **Run Tests:**
   ```bash
   pytest tests/test_backup_model.py -v
   pytest tests/test_backup_service.py -v
   pytest tests/test_api_endpoints.py::TestBackupEndpoints -v
   ```

3. **Test Frontend:**
   - Start backend: `python main.py`
   - Navigate to http://localhost:8000
   - Deploy test app
   - Test backup creation, restore, delete

4. **Run E2E Tests:**
   ```bash
   cd e2e_tests
   pytest tests/test_backup_restore_flow.py -v
   ```

---

## 📝 Notes

- Backups are automatically deleted when app is deleted (cascade)
- Background polling updates backup status from Proxmox
- Restore operation stops app, restores, then starts
- All operations require authentication
- Size calculation happens asynchronously during backup creation

---

**Implementation Started:** October 4, 2025
**Current Phase:** Database Models Complete
**Next Phase:** Database Model Tests
