# 🏗️ FASE 2: SPRINT MVP PRO - COMPLETE IMPLEMENTATION GUIDE

**Duration**: 2-3 weeks
**Goal**: Production-ready, feature-complete Proximity platform
**Prerequisites**: Phase 1 completed (authentication, security hardening)

---

## 📅 TIMELINE OVERVIEW

### **Week 3: Core Features**
- **Days 1-3**: P1-1 Settings Page
- **Days 4-5**: P1-2 Infrastructure Page
- **Days 6-7**: P1-3 Backup/Restore (Part 1)

### **Week 4: Advanced & Polish**
- **Days 1-2**: P1-3 Update/Rollback (Part 2)
- **Days 3-4**: P2-1 Monitoring Integration
- **Days 5**: Testing & Bug Fixes
- **Days 6-7**: Documentation & Final Polish

---

## 🔧 TASK P1-1: SETTINGS PAGE

### **Objective**: Secure configuration management UI

### **What Users Can Configure**:
1. **Proxmox Connection** (encrypted credentials)
2. **Network Settings** (proximity-lan ranges, domain)
3. **Default Resources** (LXC memory/CPU/disk)
4. **System Preferences** (logging, auto-updates)

---

### **Day 1: Backend Infrastructure**

#### **Step 1.1: Create Settings Database Model**

Add to `models/database.py`:

```python
class Setting(Base):
    """System settings with encryption support"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(1000))  # Encrypted if sensitive
    is_encrypted = Column(Boolean, default=False)
    category = Column(String(50), index=True)  # 'proxmox', 'network', 'system', etc.
    description = Column(String(500))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"))
```

Run migration:
```bash
# Add to database init
from models.database import init_db
init_db()  # Creates settings table
```

---

#### **Step 1.2: Create Settings Service**

File: `services/settings_service.py`

```python
"""
Settings Service for Proximity

Manages system configuration with encryption for sensitive values.
"""

from sqlalchemy.orm import Session
from models.database import Setting
from services.encryption_service import get_encryption_service
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SettingsService:
    """Manage system settings with encryption"""

    # Define which settings should be encrypted
    ENCRYPTED_KEYS = {
        'proxmox_password',
        'proxmox_api_token',
        'smtp_password',
        # Add more as needed
    }

    def __init__(self):
        self.encryption = get_encryption_service()

    def get(self, db: Session, key: str, default: Any = None) -> Any:
        """Get setting value (auto-decrypts if encrypted)"""
        setting = db.query(Setting).filter(Setting.key == key).first()

        if not setting:
            return default

        value = setting.value

        if setting.is_encrypted:
            try:
                value = self.encryption.decrypt(value)
            except ValueError:
                logger.error(f"Failed to decrypt setting: {key}")
                return default

        return value

    def set(self, db: Session, key: str, value: str,
            category: str = 'system', user_id: int = None) -> Setting:
        """Set setting value (auto-encrypts if sensitive)"""

        # Check if should encrypt
        is_encrypted = key in self.ENCRYPTED_KEYS
        stored_value = value

        if is_encrypted and value:
            stored_value = self.encryption.encrypt(value)

        # Update or create
        setting = db.query(Setting).filter(Setting.key == key).first()

        if setting:
            setting.value = stored_value
            setting.is_encrypted = is_encrypted
            setting.updated_by = user_id
        else:
            setting = Setting(
                key=key,
                value=stored_value,
                is_encrypted=is_encrypted,
                category=category,
                updated_by=user_id
            )
            db.add(setting)

        db.commit()
        db.refresh(setting)
        return setting

    def get_category(self, db: Session, category: str) -> Dict[str, Any]:
        """Get all settings in a category (decrypted)"""
        settings = db.query(Setting).filter(Setting.category == category).all()

        result = {}
        for setting in settings:
            value = setting.value
            if setting.is_encrypted:
                try:
                    value = self.encryption.decrypt(value)
                except ValueError:
                    logger.warning(f"Could not decrypt {setting.key}")
                    value = None
            result[setting.key] = value

        return result

    def set_proxmox_credentials(self, db: Session, host: str, user: str,
                                password: str, user_id: int = None):
        """Convenience method to set Proxmox credentials"""
        self.set(db, 'proxmox_host', host, 'proxmox', user_id)
        self.set(db, 'proxmox_user', user, 'proxmox', user_id)
        self.set(db, 'proxmox_password', password, 'proxmox', user_id)  # Auto-encrypted

        logger.info(f"Proxmox credentials updated by user {user_id}")

    def get_proxmox_credentials(self, db: Session) -> Dict[str, str]:
        """Get Proxmox credentials (decrypted)"""
        return {
            'host': self.get(db, 'proxmox_host'),
            'user': self.get(db, 'proxmox_user'),
            'password': self.get(db, 'proxmox_password'),  # Auto-decrypted
        }

# Singleton
settings_service = SettingsService()
```

---

#### **Step 1.3: Create Settings API Endpoints**

File: `api/endpoints/settings.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db
from api.middleware.auth import get_current_user, require_admin, TokenData
from services.settings_service import settings_service
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Schemas
class ProxmoxCredentials(BaseModel):
    host: str
    user: str
    password: str
    port: int = 8006
    verify_ssl: bool = False

class NetworkSettings(BaseModel):
    lan_subnet: str = "10.20.0.0/24"
    lan_gateway: str = "10.20.0.1"
    dhcp_start: str = "10.20.0.100"
    dhcp_end: str = "10.20.0.250"
    dns_domain: str = "prox.local"

class DefaultResources(BaseModel):
    lxc_memory: int = 2048
    lxc_cores: int = 2
    lxc_disk: int = 8
    lxc_storage: str = "local-lvm"

# Endpoints

@router.get("/proxmox")
async def get_proxmox_settings(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin)
):
    """Get Proxmox connection settings (admin only)"""
    creds = settings_service.get_proxmox_credentials(db)

    # Don't return password in response (use placeholder)
    return {
        "host": creds.get('host', ''),
        "user": creds.get('user', ''),
        "password": "******" if creds.get('password') else "",
        "port": settings_service.get(db, 'proxmox_port', 8006),
        "verify_ssl": settings_service.get(db, 'proxmox_verify_ssl', False)
    }

@router.post("/proxmox")
async def update_proxmox_settings(
    creds: ProxmoxCredentials,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin)
):
    """Update Proxmox credentials (admin only, encrypted storage)"""

    # Only update password if not placeholder
    if creds.password != "******":
        settings_service.set_proxmox_credentials(
            db, creds.host, creds.user, creds.password, current_user.user_id
        )
    else:
        # Update host/user only
        settings_service.set(db, 'proxmox_host', creds.host, 'proxmox', current_user.user_id)
        settings_service.set(db, 'proxmox_user', creds.user, 'proxmox', current_user.user_id)

    settings_service.set(db, 'proxmox_port', str(creds.port), 'proxmox', current_user.user_id)
    settings_service.set(db, 'proxmox_verify_ssl', str(creds.verify_ssl), 'proxmox', current_user.user_id)

    # Test connection
    from services.proxmox_service import proxmox_service
    try:
        # Update proxmox_service with new credentials
        # (This would require modifying proxmox_service to reload credentials)
        is_connected = await proxmox_service.test_connection()

        return {
            "success": True,
            "message": "Proxmox settings updated",
            "connection_test": "success" if is_connected else "failed"
        }
    except Exception as e:
        logger.error(f"Proxmox connection test failed: {e}")
        return {
            "success": True,
            "message": "Settings saved but connection test failed",
            "connection_test": "failed",
            "error": str(e)
        }

@router.get("/network")
async def get_network_settings(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get network configuration"""
    return {
        "lan_subnet": settings_service.get(db, 'lan_subnet', '10.20.0.0/24'),
        "lan_gateway": settings_service.get(db, 'lan_gateway', '10.20.0.1'),
        "dhcp_start": settings_service.get(db, 'dhcp_start', '10.20.0.100'),
        "dhcp_end": settings_service.get(db, 'dhcp_end', '10.20.0.250'),
        "dns_domain": settings_service.get(db, 'dns_domain', 'prox.local')
    }

@router.post("/network")
async def update_network_settings(
    network: NetworkSettings,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin)
):
    """Update network settings (admin only)"""

    settings_service.set(db, 'lan_subnet', network.lan_subnet, 'network', current_user.user_id)
    settings_service.set(db, 'lan_gateway', network.lan_gateway, 'network', current_user.user_id)
    settings_service.set(db, 'dhcp_start', network.dhcp_start, 'network', current_user.user_id)
    settings_service.set(db, 'dhcp_end', network.dhcp_end, 'network', current_user.user_id)
    settings_service.set(db, 'dns_domain', network.dns_domain, 'network', current_user.user_id)

    return {
        "success": True,
        "message": "Network settings updated",
        "warning": "Changes will apply to newly created apps. Existing apps not affected."
    }

@router.get("/resources")
async def get_default_resources(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get default resource allocations"""
    return {
        "lxc_memory": int(settings_service.get(db, 'lxc_memory', 2048)),
        "lxc_cores": int(settings_service.get(db, 'lxc_cores', 2)),
        "lxc_disk": int(settings_service.get(db, 'lxc_disk', 8)),
        "lxc_storage": settings_service.get(db, 'lxc_storage', 'local-lvm')
    }

@router.post("/resources")
async def update_default_resources(
    resources: DefaultResources,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin)
):
    """Update default resource allocations (admin only)"""

    settings_service.set(db, 'lxc_memory', str(resources.lxc_memory), 'resources', current_user.user_id)
    settings_service.set(db, 'lxc_cores', str(resources.lxc_cores), 'resources', current_user.user_id)
    settings_service.set(db, 'lxc_disk', str(resources.lxc_disk), 'resources', current_user.user_id)
    settings_service.set(db, 'lxc_storage', resources.lxc_storage, 'resources', current_user.user_id)

    return {
        "success": True,
        "message": "Default resources updated"
    }

@router.get("/all")
async def get_all_settings(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin)
):
    """Get all settings grouped by category (admin only)"""
    return {
        "proxmox": await get_proxmox_settings(db, current_user),
        "network": await get_network_settings(db, current_user),
        "resources": await get_default_resources(db, current_user)
    }
```

---

### **Day 2-3: Frontend UI**

#### **Settings Page Structure**

Create `frontend/settings.html` (or integrate into existing UI):

```html
<div class="settings-container">
  <!-- Tabs -->
  <div class="settings-tabs">
    <button class="tab active" data-tab="proxmox">Proxmox</button>
    <button class="tab" data-tab="network">Network</button>
    <button class="tab" data-tab="resources">Resources</button>
    <button class="tab" data-tab="system">System</button>
  </div>

  <!-- Proxmox Tab -->
  <div id="proxmox-tab" class="tab-content active">
    <h2>Proxmox Connection</h2>
    <form id="proxmox-form">
      <label>Host:
        <input type="text" name="host" required />
      </label>
      <label>Port:
        <input type="number" name="port" value="8006" />
      </label>
      <label>User:
        <input type="text" name="user" required />
      </label>
      <label>Password:
        <input type="password" name="password" placeholder="******" />
      </label>
      <label>
        <input type="checkbox" name="verify_ssl" />
        Verify SSL
      </label>
      <button type="submit">Test & Save</button>
    </form>
    <div id="connection-status"></div>
  </div>

  <!-- Network Tab -->
  <div id="network-tab" class="tab-content">
    <h2>Network Configuration</h2>
    <form id="network-form">
      <label>LAN Subnet:
        <input type="text" name="lan_subnet" value="10.20.0.0/24" />
      </label>
      <label>Gateway:
        <input type="text" name="lan_gateway" value="10.20.0.1" />
      </label>
      <label>DHCP Start:
        <input type="text" name="dhcp_start" value="10.20.0.100" />
      </label>
      <label>DHCP End:
        <input type="text" name="dhcp_end" value="10.20.0.250" />
      </label>
      <label>DNS Domain:
        <input type="text" name="dns_domain" value="prox.local" />
      </label>
      <button type="submit">Save</button>
    </form>
  </div>

  <!-- Resources Tab -->
  <div id="resources-tab" class="tab-content">
    <h2>Default Resources</h2>
    <form id="resources-form">
      <label>Memory (MB):
        <input type="number" name="lxc_memory" value="2048" />
      </label>
      <label>CPU Cores:
        <input type="number" name="lxc_cores" value="2" />
      </label>
      <label>Disk (GB):
        <input type="number" name="lxc_disk" value="8" />
      </label>
      <label>Storage:
        <input type="text" name="lxc_storage" value="local-lvm" />
      </label>
      <button type="submit">Save</button>
    </form>
  </div>
</div>

<script>
// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(content => {
      content.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(t => {
      t.classList.remove('active');
    });

    // Show selected tab
    const tabName = tab.dataset.tab;
    document.getElementById(`${tabName}-tab`).classList.add('active');
    tab.classList.add('active');
  });
});

// Load settings on page load
async function loadSettings() {
  const token = localStorage.getItem('auth_token');

  // Load Proxmox settings
  const proxmoxRes = await fetch('/api/v1/settings/proxmox', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const proxmox = await proxmoxRes.json();
  document.querySelector('[name="host"]').value = proxmox.host || '';
  document.querySelector('[name="user"]').value = proxmox.user || '';
  // ... populate other fields
}

// Save Proxmox settings
document.getElementById('proxmox-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const token = localStorage.getItem('auth_token');
  const formData = new FormData(e.target);

  const res = await fetch('/api/v1/settings/proxmox', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      host: formData.get('host'),
      user: formData.get('user'),
      password: formData.get('password'),
      port: parseInt(formData.get('port')),
      verify_ssl: formData.get('verify_ssl') === 'on'
    })
  });

  const result = await res.json();
  document.getElementById('connection-status').innerHTML =
    result.connection_test === 'success'
      ? '<p class="success">✓ Connected to Proxmox</p>'
      : `<p class="error">✗ Connection failed: ${result.error}</p>`;
});

// Initialize
loadSettings();
</script>
```

---

### **Integration Steps**:

1. **Add to `main.py`**:
```python
from api.endpoints import settings

app.include_router(
    settings.router,
    prefix=f"/api/{settings.API_VERSION}/settings",
    tags=["Settings"],
    dependencies=[Depends(get_current_user)]  # Protected
)
```

2. **Update `requirements.txt`**:
```txt
cryptography==41.0.7  # For encryption
```

3. **Update `.env`**:
```bash
# Encryption (generated automatically)
ENCRYPTION_KEY=<auto-generated-from-JWT-secret>
```

4. **Run migration**:
```bash
python3 -c "from models.database import init_db; init_db()"
```

---

### **Testing P1-1**:

```bash
# 1. Set Proxmox credentials
curl -X POST http://localhost:8765/api/v1/settings/proxmox \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "host": "192.168.100.102",
    "user": "root@pam",
    "password": "yourpassword",
    "port": 8006,
    "verify_ssl": false
  }'

# 2. Get settings (password encrypted in DB)
curl http://localhost:8765/api/v1/settings/proxmox \
  -H "Authorization: Bearer $TOKEN"
# → Returns: { "host": "...", "password": "******" }

# 3. Verify encryption in DB
sqlite3 proximity.db "SELECT key, value, is_encrypted FROM settings WHERE key='proxmox_password';"
# → Shows encrypted value, is_encrypted=1
```

---

## 🏗️ TASK P1-2: INFRASTRUCTURE PAGE

### **Objective**: Network Appliance monitoring & diagnostics

**API already exists** (`/api/v1/system/infrastructure/status`)
**Task**: Build comprehensive UI + add diagnostic tools

### **Implementation** (Days 4-5):

#### **Diagnostic Endpoints** (`api/endpoints/system.py` - ADD):

```python
@router.post("/infrastructure/appliance/restart")
async def restart_appliance(
    current_user: TokenData = Depends(require_admin)
):
    """Restart network appliance (admin only)"""
    from main import app
    orchestrator = app.state.orchestrator

    if not orchestrator or not orchestrator.appliance_info:
        raise HTTPException(404, "Network appliance not found")

    # Restart LXC
    from services.proxmox_service import proxmox_service
    await proxmox_service.stop_lxc(
        orchestrator.appliance_info.node,
        orchestrator.appliance_info.vmid
    )
    await asyncio.sleep(2)
    await proxmox_service.start_lxc(
        orchestrator.appliance_info.node,
        orchestrator.appliance_info.vmid
    )

    return {"success": True, "message": "Appliance restarting"}

@router.get("/infrastructure/appliance/logs")
async def get_appliance_logs(
    service: str = "dnsmasq",  # or "caddy", "iptables"
    lines: int = 100,
    current_user: TokenData = Depends(get_current_user)
):
    """Get appliance service logs"""
    # Implementation: pct exec to get logs
    pass
```

#### **Frontend** (Infrastructure Page):

```html
<div class="infrastructure-dashboard">
  <div class="appliance-status">
    <h2>Network Appliance</h2>
    <div class="status-indicator"></div>
    <p>VMID: <span id="vmid"></span></p>
    <p>WAN IP: <span id="wan-ip"></span></p>
    <p>LAN IP: <span id="lan-ip"></span></p>

    <button onclick="restartAppliance()">Restart Appliance</button>
  </div>

  <div class="services-grid">
    <div class="service">
      <h3>DHCP/DNS (dnsmasq)</h3>
      <span class="status">●</span>
      <button onclick="viewLogs('dnsmasq')">View Logs</button>
    </div>
    <div class="service">
      <h3>Reverse Proxy (Caddy)</h3>
      <span class="status">●</span>
      <button onclick="viewLogs('caddy')">View Logs</button>
    </div>
    <div class="service">
      <h3>NAT (iptables)</h3>
      <span class="status">●</span>
      <button onclick="checkNAT()">Test NAT</button>
    </div>
  </div>

  <div class="connected-apps">
    <h3>Connected Applications</h3>
    <table id="apps-table">
      <thead>
        <tr>
          <th>Hostname</th>
          <th>IP</th>
          <th>DNS Name</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</div>
```

---

## 💾 TASK P1-3: BACKUP/RESTORE

### **Objective**: App lifecycle management with Proxmox vzdump

### **Implementation** (Days 6-7 + Week 4 Days 1-2):

#### **Backup Service** (`services/backup_service.py`):

```python
class BackupService:

    async def backup_app(self, app_id: str, db: Session) -> str:
        """Create backup using Proxmox vzdump"""
        app = await app_service.get_app(app_id, db)

        # Use Proxmox vzdump
        backup_cmd = f"vzdump {app.lxc_id} --mode snapshot --storage local"
        result = await proxmox_service.execute_command_via_ssh(backup_cmd)

        # Parse backup filename from output
        # Store backup metadata in DB

        return backup_path

    async def restore_app(self, backup_id: str, target_node: str = None):
        """Restore from backup"""
        # pct restore <vmid> <backup-file>
        pass

    async def update_app(self, app_id: str):
        """Update app (pull latest images)"""
        app = await app_service.get_app(app_id)

        # docker-compose pull && docker-compose up -d
        await proxmox_service.execute_in_container(
            app.node, app.lxc_id,
            "cd /root && docker-compose pull && docker-compose up -d --force-recreate"
        )
```

---

## 📊 MONITORING INTEGRATION (P2-1)

### **Strategy**: Don't reinvent - integrate existing tools

#### **Option A: Netdata (Recommended)**
```bash
# Deploy Netdata as system app
# Auto-configure agents in all containers
# Deep-link from Proximity UI
```

#### **Option B: Prometheus + Grafana**
```bash
# Deploy stack via catalog
# Pre-configured dashboards
# Embed Grafana in UI via iframe
```

**UI Integration**:
```html
<div class="monitoring-page">
  <iframe src="http://netdata-ip:19999" />
</div>
```

---

## ✅ PHASE 2 SUCCESS CRITERIA

**By end of Week 4, verify**:
- [ ] Settings page: Can configure Proxmox, network, resources
- [ ] Credentials encrypted in database
- [ ] Infrastructure page: Shows appliance status + diagnostics
- [ ] Can restart appliance, view logs
- [ ] Backup/restore working with vzdump
- [ ] App updates working (pull latest images)
- [ ] Monitoring integrated (Netdata/Grafana)
- [ ] Full documentation updated

---

## 📚 Documentation to Create

1. **USER_GUIDE.md** - End-user documentation
2. **ADMIN_GUIDE.md** - Admin/installation guide
3. **API.md** - Complete API reference
4. **TROUBLESHOOTING.md** - Common issues & solutions

---

## 🚀 FINAL DELIVERABLE

**At end of Phase 2**:
- ✅ Production-ready platform
- ✅ Feature-complete MVP
- ✅ Encrypted credential storage
- ✅ Full app lifecycle (deploy → backup → restore → update)
- ✅ Network infrastructure monitoring
- ✅ Comprehensive documentation

**Ready for**: Public beta launch, open source release

---

*This is your complete implementation guide for Phase 2. Follow day-by-day, test thoroughly, and you'll have a world-class platform in 3 weeks!*
