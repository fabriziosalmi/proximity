# 🎉 FASE 2: SPRINT MVP PRO - KICKOFF

**Start Date**: After Phase 1 completion
**Duration**: 2-3 weeks
**Goal**: Transform Proximity from secure prototype → production-ready platform

---

## 🎯 WHAT WE'RE BUILDING

### **The Vision**:
A **complete, self-service platform** where users can:
1. **Configure** their Proxmox connection via UI (no more .env files!)
2. **Monitor** network infrastructure in real-time
3. **Manage** app lifecycle: backup, restore, update
4. **Observe** all systems with integrated monitoring

### **The Reality Check**:
- Phase 1 made it **secure** ✅
- Phase 2 makes it **usable** 🚀
- Phase 3 makes it **scalable** (future)

---

## 📦 DELIVERABLES OVERVIEW

### **Week 3: Core Features**

#### **P1-1: Settings Page** (Days 1-3)
**What**: Configuration management UI with encrypted credential storage

**Key Features**:
- **Proxmox Tab**: Host, user, password (🔐 encrypted), SSL settings
- **Network Tab**: proximity-lan ranges, DHCP, DNS domain
- **Resources Tab**: Default LXC memory/CPU/disk
- **System Tab**: Logging level, auto-updates, cache settings

**Security**:
- Fernet encryption for passwords
- Admin-only access
- Audit trail for all changes

**Files to Create**:
- `services/encryption_service.py` ✅ (Already created!)
- `services/settings_service.py`
- `api/endpoints/settings.py`
- `models/database.py` (add `Setting` model)
- Frontend: Settings page UI

---

#### **P1-2: Infrastructure Page** (Days 4-5)
**What**: Network appliance dashboard with diagnostics

**Key Features**:
- **Appliance Status**: VMID, IPs, resource usage
- **Service Grid**: dnsmasq, Caddy, iptables health
- **Connected Apps**: Table of all apps with IPs/DNS
- **Diagnostic Tools**:
  - Restart appliance
  - View service logs (dnsmasq, Caddy)
  - Test NAT/DNS resolution
  - Rebuild bridge

**API**: Already 80% exists! (`/api/v1/system/infrastructure/status`)

**Files to Create**:
- `api/endpoints/system.py` (add diagnostic endpoints)
- Frontend: Infrastructure page UI
- Service health checks

---

#### **P1-3: Backup/Restore** (Days 6-7)
**What**: App lifecycle management with Proxmox vzdump

**Key Features**:
- **Backup**: Create LXC snapshot via vzdump
- **Restore**: Restore from backup (same or different node)
- **Schedule**: Automatic daily/weekly backups
- **Storage**: Metadata in DB, files in Proxmox storage

**Implementation**:
```bash
# Backup
vzdump <vmid> --mode snapshot --storage local

# Restore
pct restore <vmid> <backup-file>
```

**Files to Create**:
- `services/backup_service.py`
- `models/database.py` (add `Backup` model)
- `api/endpoints/backups.py`
- Frontend: Backup management UI

---

### **Week 4: Advanced & Polish**

#### **P1-3: Update/Rollback** (Days 1-2)
**What**: App update with Docker image pull

**Key Features**:
- **Update**: Pull latest images, recreate containers
- **Rollback**: Restore from previous backup if update fails
- **Atomic**: Create backup before update, auto-rollback on error

**Implementation**:
```bash
# In container
cd /root
docker-compose pull
docker-compose up -d --force-recreate
```

---

#### **P2-1: Monitoring Integration** (Days 3-4)
**What**: Integrate Netdata or Prometheus/Grafana

**Strategy**: Don't build, integrate!

**Approach**:
1. Deploy monitoring tool as system app
2. Auto-configure agents for all containers
3. Deep-link from Proximity UI

**Options**:
- **Netdata** (recommended): Lightweight, auto-discovery
- **Prometheus + Grafana**: More powerful, heavier

**UI**:
```html
<div class="monitoring-page">
  <h2>System Monitoring</h2>
  <div class="quick-stats">...</div>
  <iframe src="http://netdata-ip:19999"></iframe>
</div>
```

---

## 📊 PROGRESS TRACKING

### **Week 3 Checklist**:
- [ ] Day 1: Encryption service + Settings DB model
- [ ] Day 2: Settings API endpoints
- [ ] Day 3: Settings UI + testing
- [ ] Day 4: Infrastructure diagnostics API
- [ ] Day 5: Infrastructure UI + testing
- [ ] Day 6: Backup service implementation
- [ ] Day 7: Backup UI + testing

### **Week 4 Checklist**:
- [ ] Day 1: Update/rollback logic
- [ ] Day 2: Update UI + testing
- [ ] Day 3: Deploy monitoring stack
- [ ] Day 4: Monitoring UI integration
- [ ] Day 5: Bug fixes, edge cases
- [ ] Day 6: Documentation (USER_GUIDE, ADMIN_GUIDE)
- [ ] Day 7: Final polish, beta prep

---

## 🔧 TECHNICAL ARCHITECTURE

### **Settings Storage (Encrypted)**:
```
┌─────────────────────────────────┐
│ Settings Table                  │
├─────────────────────────────────┤
│ key          | value            │
├─────────────────────────────────┤
│ proxmox_host | 192.168.100.102  │
│ proxmox_user | root@pam         │
│ proxmox_pass | gAAAAA... 🔐     │  ← Encrypted!
│ lan_subnet   | 10.20.0.0/24     │
│ dhcp_start   | 10.20.0.100      │
└─────────────────────────────────┘
```

### **Encryption Flow**:
```
User Input → EncryptionService → Fernet (AES) → Base64 → Database
Database → Base64 Decode → Fernet Decrypt → PlainText → API Response (masked)
```

### **Backup Workflow**:
```
1. User clicks "Backup"
2. Create backup: vzdump <vmid> --mode snapshot
3. Store metadata in DB:
   - backup_id, app_id, filename, size, created_at
4. Show in UI with restore button
5. Restore: pct restore <vmid> <backup-file>
```

---

## 🎨 UI MOCKUPS

### **Settings Page**:
```
┌────────────────────────────────────────────┐
│ ⚙️  Settings                               │
├────────────────────────────────────────────┤
│ [Proxmox] [Network] [Resources] [System]   │
├────────────────────────────────────────────┤
│                                            │
│  Proxmox Connection                        │
│  ┌────────────────────────────────────┐   │
│  │ Host:     [192.168.100.102     ]   │   │
│  │ Port:     [8006                ]   │   │
│  │ User:     [root@pam            ]   │   │
│  │ Password: [••••••••            ]   │   │
│  │ □ Verify SSL                       │   │
│  │                                    │   │
│  │ [Test Connection] [Save]           │   │
│  └────────────────────────────────────┘   │
│                                            │
│  ✅ Connected to Proxmox VE 8.1           │
└────────────────────────────────────────────┘
```

### **Infrastructure Page**:
```
┌────────────────────────────────────────────┐
│ 🏗️  Infrastructure                         │
├────────────────────────────────────────────┤
│ Network Appliance (VMID 9999)              │
│ Status: ● Running                          │
│ WAN IP: 192.168.100.45                     │
│ LAN IP: 10.20.0.1                          │
│ [Restart] [View Logs] [Diagnostics]        │
├────────────────────────────────────────────┤
│ Services:                                  │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│ │ DHCP/DNS │ │ Reverse  │ │   NAT    │    │
│ │   ● OK   │ │  Proxy   │ │   ● OK   │    │
│ │          │ │   ● OK   │ │          │    │
│ │ [Logs]   │ │ [Logs]   │ │ [Test]   │    │
│ └──────────┘ └──────────┘ └──────────┘    │
├────────────────────────────────────────────┤
│ Connected Apps:                            │
│ ┌────────────────────────────────────────┐ │
│ │ Hostname    │ IP         │ DNS Name   │ │
│ │ nginx-01    │ 10.20.0.100│ ✓ Resolves│ │
│ │ wordpress-1 │ 10.20.0.101│ ✓ Resolves│ │
│ └────────────────────────────────────────┘ │
└────────────────────────────────────────────┘
```

---

## 🧪 TESTING STRATEGY

### **P1-1 Settings Tests**:
```bash
# 1. Encrypt/Decrypt
- Set Proxmox password
- Verify encrypted in DB (SQLite query)
- Get settings (should show ******)
- Test connection (should work)

# 2. Network settings
- Update LAN subnet
- Verify new apps get new range
- Old apps unchanged

# 3. Admin-only
- Regular user can't change settings
- Returns 403 Forbidden
```

### **P1-2 Infrastructure Tests**:
```bash
# 1. Status endpoint
- Returns appliance info
- Shows all services
- Lists connected apps

# 2. Diagnostics
- Restart appliance (verify comes back up)
- View logs (contains recent entries)
- Test NAT (ping from container to internet)
```

### **P1-3 Backup Tests**:
```bash
# 1. Backup creation
- Create backup
- Verify file exists in Proxmox storage
- Metadata saved in DB

# 2. Restore
- Delete app
- Restore from backup
- Verify app works

# 3. Update
- Update app (pull new images)
- Verify containers recreated
- Auto-rollback if fails
```

---

## 📚 DOCUMENTATION PLAN

### **USER_GUIDE.md** (End-user):
- Installing Proximity
- First-time setup wizard
- Deploying your first app
- Managing apps (start/stop/backup)
- Accessing apps (DNS, path-based)
- Troubleshooting

### **ADMIN_GUIDE.md** (Admin/Ops):
- Production deployment
- Security hardening
- Backup strategies
- Scaling considerations
- Monitoring setup
- Network architecture

### **API.md** (Developers):
- Complete API reference
- Authentication flow
- Examples for all endpoints
- Error codes
- Rate limiting

---

## 🚀 LAUNCH CHECKLIST

**Before Public Beta**:
- [ ] All P1 features complete and tested
- [ ] Security audit passed
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Demo video created
- [ ] GitHub repository cleaned up
- [ ] LICENSE file added (MIT/Apache)
- [ ] Contributing guidelines (CONTRIBUTING.md)
- [ ] Code of conduct

**Launch Targets**:
- [ ] Reddit: r/selfhosted, r/homelab, r/Proxmox
- [ ] Hacker News
- [ ] Product Hunt
- [ ] Awesome-Selfhosted list
- [ ] Proxmox forum

---

## 💪 YOU'RE READY!

**Phase 1 Status**: ✅ Complete
**Phase 2 Status**: 📝 Planned
**Your Mission**: Build the MVP in 3 weeks

**Start with**:
1. Install encryption dependencies: `pip install cryptography`
2. Create `Setting` model in `database.py`
3. Build `settings_service.py`
4. Create Settings API endpoints
5. Build Settings UI

**Resources**:
- `PHASE2_IMPLEMENTATION_GUIDE.md` - Complete technical guide
- `encryption_service.py` - Already created! ✅
- Phase 1 codebase - Solid foundation

---

## 🎯 FINAL WORDS

**You've already built**:
- 🔐 Secure authentication system
- 🛡️ Hardened API
- 💾 Database infrastructure
- 📝 Complete documentation

**Now you're building**:
- ⚙️ Self-service configuration
- 🏗️ Infrastructure monitoring
- 💾 Backup/restore
- 📊 Integrated monitoring

**In 3 weeks, you'll have**:
- 🚀 Production-ready platform
- 🌟 Open-source project ready for launch
- 💎 Portfolio piece
- 🎓 Deep knowledge of Proxmox, LXC, networking

---

**LET'S BUILD! 🚀**

*Start with Day 1: Settings Service → Settings API → Settings UI*
*Follow PHASE2_IMPLEMENTATION_GUIDE.md step-by-step*
*Test thoroughly, document everything*

**See you at the finish line with a world-class platform!** 🏆
