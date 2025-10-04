# Quick Start: Database Migration Guide

## 🎯 For Users Upgrading from JSON-based Version

If you have an existing Proximity installation using `data/apps.json`, follow these steps:

### Step 1: Backup Everything
```bash
cd backend

# Backup current database (if exists)
cp proximity.db proximity_backup_$(date +%Y%m%d).db

# Backup JSON file
cp data/apps.json data/apps.json.backup
```

### Step 2: Create Admin User (if needed)
```bash
# Check if you have an admin user
sqlite3 proximity.db "SELECT username, role FROM users WHERE role='admin';"

# If no admin exists, register one through the UI first:
# http://localhost:8000 → Register → Use admin credentials
```

### Step 3: Run Migration
```bash
python scripts/migrate_json_to_sqlite.py
```

**Expected Output:**
```
============================================================
PROXIMITY: JSON to SQLite Migration
============================================================
Found 5 apps in JSON file
Found admin user: admin (ID: 1)
All migrated apps will be assigned to this user

  ✓ Created: WordPress (ID: wordpress-prod) (Owner: admin)
  ✓ Created: Nextcloud (ID: nextcloud-storage) (Owner: admin)
  ...
------------------------------------------------------------
✅ Migration completed successfully!
📦 JSON file backed up to: data/apps.json.backup
```

### Step 4: Verify Migration
```bash
# Check apps in database
sqlite3 proximity.db "SELECT id, name, status, hostname FROM apps;"

# Check ownership
sqlite3 proximity.db "
  SELECT a.name, a.status, u.username as owner
  FROM apps a
  LEFT JOIN users u ON a.owner_id = u.id;
"
```

### Step 5: Restart Application
```bash
# Stop backend (Ctrl+C)
# Start again
python main.py

# Apps should load from database now
```

### Step 6: Cleanup (Optional)
```bash
# After confirming everything works
mv data/apps.json data/apps.json.archive
```

---

## 🆕 For Fresh Installations

If you're installing Proximity for the first time:

```bash
cd backend

# 1. Database is automatically created on first run
# 2. Register your admin user through the UI
# 3. Start deploying apps!
```

**That's it!** No migration needed for fresh installs.

---

## 🔍 Troubleshooting

### "No admin user found" during migration
**Problem:** Migration script can't find an admin user to assign apps to.

**Solution:**
```bash
# Option 1: Register admin through UI first
# http://localhost:8000 → Register with admin credentials

# Option 2: Create admin via SQL
sqlite3 proximity.db
> INSERT INTO users (username, email, hashed_password, role, is_active)
  VALUES ('admin', 'admin@example.com', '$2b$12$...', 'admin', 1);
> .quit
```

### Apps show "error" status after migration
**Problem:** LXC containers exist but status is wrong.

**Solution:**
```bash
# The sync function will fix this automatically
# Just access the app list in the UI or:
curl http://localhost:8000/api/v1/apps \
  -H "Authorization: Bearer $YOUR_TOKEN"

# Status will sync with actual Proxmox state
```

### Migration script fails with "Permission denied"
**Problem:** Script not executable.

**Solution:**
```bash
chmod +x scripts/migrate_json_to_sqlite.py
python scripts/migrate_json_to_sqlite.py
```

---

## 📊 Database Schema Overview

```
users
├── id (PK)
├── username (unique)
├── email (unique, nullable)
├── hashed_password
├── role (admin/user)
└── is_active

apps
├── id (PK)
├── catalog_id
├── name
├── hostname (unique)
├── status (running/stopped/error)
├── url
├── lxc_id (unique)
├── node
├── owner_id (FK → users.id)
├── config (JSON)
├── ports (JSON)
├── volumes (JSON)
├── environment (JSON)
├── created_at
└── updated_at

deployment_logs
├── id (PK)
├── app_id (FK → apps.id)
├── timestamp
├── level (info/warning/error)
├── message
└── step
```

---

## 🔧 Common Database Operations

### View all apps
```bash
sqlite3 proximity.db "
  SELECT id, name, status, url
  FROM apps
  ORDER BY created_at DESC;
"
```

### View apps by owner
```bash
sqlite3 proximity.db "
  SELECT a.name, a.status, u.username
  FROM apps a
  JOIN users u ON a.owner_id = u.id
  WHERE u.username = 'admin';
"
```

### View deployment logs for an app
```bash
sqlite3 proximity.db "
  SELECT timestamp, level, message
  FROM deployment_logs
  WHERE app_id = 'nginx-myapp'
  ORDER BY timestamp DESC
  LIMIT 20;
"
```

### Backup database
```bash
# SQLite backup
sqlite3 proximity.db ".backup proximity_backup.db"

# Or simple copy
cp proximity.db proximity_backup_$(date +%Y%m%d_%H%M%S).db
```

### Restore database
```bash
# Stop backend first!
cp proximity_backup.db proximity.db
# Restart backend
```

---

## ✅ Migration Verification Checklist

After migration, verify:

- [ ] All apps show in UI at `http://localhost:8000`
- [ ] App statuses are correct (running/stopped)
- [ ] URLs are accessible
- [ ] Can start/stop apps
- [ ] Can deploy new apps
- [ ] Can delete apps
- [ ] Server restart preserves all apps
- [ ] Deployment logs are visible

---

## 🆘 Need Help?

1. Check logs: `backend/logs/proximity.log`
2. Check migration output for errors
3. Verify database exists: `ls -lh backend/proximity.db`
4. Check app state: `sqlite3 proximity.db "SELECT * FROM apps;"`

---

## 📝 Key Changes from JSON Version

| Feature | JSON Version | Database Version |
|---------|-------------|------------------|
| Data file | `data/apps.json` | `proximity.db` |
| Reads | Parse entire file | Indexed queries |
| Writes | Overwrite file | Atomic transactions |
| Concurrent access | File locks | Row-level locks |
| User ownership | Not supported | Fully supported |
| Deployment logs | In-memory only | Persisted in DB |
| Backup | Copy JSON file | SQL dump |
| Recovery | Restore file | Point-in-time restore |

---

**You're all set!** 🚀 Your Proximity installation is now using a robust database backend.
