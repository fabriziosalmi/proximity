# Cache Clearing Guide

This guide explains how to clear various caches in the Proximity application.

## 🌐 Browser Cache (Frontend)

### Quick Hard Refresh

**macOS:**
- **Chrome/Edge:** `Cmd + Shift + R` or `Cmd + Option + R`
- **Firefox:** `Cmd + Shift + R`
- **Safari:** `Cmd + Option + E` (clear cache), then `Cmd + R` (reload)

**Windows/Linux:**
- **Chrome/Edge/Firefox:** `Ctrl + Shift + R` or `Ctrl + F5`

### Clear Cache via DevTools

1. Open DevTools: `F12` or `Right-click → Inspect`
2. Go to **Network** tab
3. Check **"Disable cache"** checkbox
4. Keep DevTools open and reload the page

### Complete Browser Cache Clear

**Chrome/Edge:**
1. Open Settings: `chrome://settings/clearBrowserData`
2. Select "Cached images and files"
3. Click "Clear data"

**Firefox:**
1. Open Settings: `about:preferences#privacy`
2. Scroll to "Cookies and Site Data"
3. Click "Clear Data"

**Safari:**
1. Menu: Safari → Settings → Advanced
2. Check "Show Develop menu"
3. Menu: Develop → Empty Caches

---

## 🔄 Force Frontend Update (Cache Busting)

The frontend uses versioned assets to prevent caching issues. To force all browsers to reload:

### Update Version Numbers

**File:** `backend/frontend/index.html`

Current version is set in two places:
```html
<!-- Line 15 -->
<script src="app.js?v=20251008-5"></script>

<!-- Line 18 -->
<script src="js/main.js?v=20251008-5" type="module"></script>

<!-- Line 258 -->
<script src="app.js?v=20251008-5"></script>

<!-- Line 261 -->
<script src="js/main.js?v=20251008-5" type="module"></script>
```

**To update:** Increment the version number (e.g., `20251008-5` → `20251008-6`)

### Automated Version Update Script

Create this script to auto-update versions:

```bash
#!/bin/bash
# update_cache_version.sh

DATE=$(date +%Y%m%d)
VERSION="${DATE}-$(($(date +%s) % 100))"

sed -i '' "s/\?v=[0-9]*-[0-9]*/\?v=${VERSION}/g" backend/frontend/index.html

echo "✅ Updated cache version to: v=${VERSION}"
```

Make it executable and run:
```bash
chmod +x update_cache_version.sh
./update_cache_version.sh
```

---

## 🐍 Backend/Python Cache

### Clear Python Cache

```bash
cd /Users/fab/GitHub/proximity

# Remove __pycache__ directories
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Remove .pyc files
find . -type f -name "*.pyc" -delete

# Remove .pyo files
find . -type f -name "*.pyo" -delete

# Alternative: Use pyclean (if available)
pyclean .
```

### Clear Pytest Cache

```bash
# Remove pytest cache
rm -rf .pytest_cache
rm -rf tests/.pytest_cache
rm -rf e2e_tests/.pytest_cache
```

---

## 🗄️ Database Cache

### SQLite Cache

The database doesn't use a traditional cache, but you can:

```bash
# CAUTION: This clears all data!
# Backup first:
cp backend/proximity.db backend/proximity_backup_$(date +%Y%m%d_%H%M%S).db

# If you really want to start fresh:
rm backend/proximity.db
# Database will be recreated on next start
```

### Query Cache (if implemented)

If using any query caching:
```python
# In Python code or console
from backend.core.database import db
db.clear_cache()  # If implemented
```

---

## 🌐 Proxmox API Cache

Proximity caches some Proxmox API responses. To clear:

### Restart Backend Server

```bash
# Stop backend
pkill -f "uvicorn backend.main:app" || pkill -f "python.*backend/main.py"

# Or if running with specific port
lsof -ti:8765 | xargs kill -9

# Start backend
cd backend
python main.py
```

### Clear Session Cache (if applicable)

```bash
# If using Redis or memcached
redis-cli FLUSHALL  # Redis
# or
echo 'flush_all' | nc localhost 11211  # Memcached
```

---

## 🌍 Reverse Proxy Cache (Caddy)

If Caddy has caching enabled:

```bash
# SSH into the network appliance
ssh root@<appliance-ip>

# Restart Caddy
rc-service caddy restart

# Or reload configuration
caddy reload --config /etc/caddy/Caddyfile
```

---

## 📦 NPM/Node.js Cache (if applicable)

If you're using any Node.js tools:

```bash
# Clear npm cache
npm cache clean --force

# Clear node_modules (if present)
rm -rf node_modules
npm install
```

---

## 🔧 Complete System Clear

To clear **everything** at once:

```bash
#!/bin/bash
# complete_cache_clear.sh

echo "🧹 Clearing all caches..."

# Python caches
echo "Clearing Python caches..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
rm -rf .pytest_cache

# Backup database
echo "Backing up database..."
cp backend/proximity.db backend/proximity_backup_$(date +%Y%m%d_%H%M%S).db 2>/dev/null

# Update frontend cache version
echo "Updating frontend cache version..."
DATE=$(date +%Y%m%d)
VERSION="${DATE}-$(($(date +%s) % 100))"
sed -i '' "s/\?v=[0-9]*-[0-9]*/\?v=${VERSION}/g" backend/frontend/index.html

# Restart backend
echo "Restarting backend..."
pkill -f "uvicorn backend.main:app" || pkill -f "python.*backend/main.py"
sleep 2
cd backend && python main.py &

echo "✅ All caches cleared!"
echo "🌐 Hard refresh your browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)"
```

---

## 🧪 Testing Cache Clearance

### Verify Frontend Cache Cleared

1. Open DevTools (F12)
2. Go to **Network** tab
3. Enable "Disable cache"
4. Reload page
5. Look for `app.js?v=XXXXXX-X` in network requests
6. Verify version number is updated

### Verify Backend Restart

```bash
# Check if backend is running
ps aux | grep "python.*backend/main.py"

# Check backend logs
tail -f backend/backend.log

# Test API endpoint
curl http://localhost:8765/api/v1/health
```

### Verify Browser Cache

1. Open DevTools → Network tab
2. Look at "Size" column
3. Should show actual file sizes, not "(from disk cache)"
4. Status should be `200 OK`, not `304 Not Modified`

---

## 🚨 Troubleshooting

### Browser Still Using Old Cache

**Solution:**
1. Close all browser tabs/windows completely
2. Clear browser cache manually (see above)
3. Try in Incognito/Private mode
4. Try a different browser

### Backend Changes Not Reflecting

**Solution:**
```bash
# Force kill and restart
pkill -9 -f "python.*backend"
cd backend
python main.py
```

### Database Issues After Clearing

**Solution:**
```bash
# Restore from backup
cp backend/proximity_backup_YYYYMMDD_HHMMSS.db backend/proximity.db
```

### Permission Denied When Clearing Cache

**Solution:**
```bash
# Use sudo for system-wide caches
sudo find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## 📝 Best Practices

1. **Always backup before clearing database**
   ```bash
   cp backend/proximity.db backend/proximity_backup_$(date +%Y%m%d_%H%M%S).db
   ```

2. **Use version numbers for cache busting** (already implemented)
   - Automatic with every significant change
   - No need for users to clear cache manually

3. **Enable DevTools cache disabling during development**
   - Prevents frustration during active coding

4. **Document cache-dependent features**
   - Know what needs clearing when things break

5. **Automate cache clearing in deployment**
   - Include version bumps in deployment scripts

---

## 🔗 Related Documentation

- [Development Guide](development.md) - Local development setup
- [Deployment Guide](deployment.md) - Production deployment
- [Troubleshooting](troubleshooting.md) - Common issues and fixes

---

## 📊 Cache Locations Reference

| Cache Type | Location | Command to Clear |
|------------|----------|------------------|
| Browser | Browser-specific | `Cmd/Ctrl + Shift + R` |
| Python | `__pycache__/` | `find . -name __pycache__ -exec rm -rf {} +` |
| Pytest | `.pytest_cache/` | `rm -rf .pytest_cache` |
| Frontend Assets | Browser memory | Update `?v=` version in HTML |
| SQLite DB | `backend/proximity.db` | Backup and restart |
| Proxmox API | Memory (backend) | Restart backend server |
| Caddy | Memory (appliance) | `rc-service caddy restart` |

---

## ✅ Quick Reference

**Most Common: Hard Browser Refresh**
```
Mac: Cmd + Shift + R
Windows/Linux: Ctrl + Shift + R
```

**Force All Users to Update: Bump Version**
```
Edit: backend/frontend/index.html
Change: ?v=20251008-5 → ?v=20251008-6
```

**Clear Backend: Restart Server**
```bash
pkill -f "python.*backend/main.py"
cd backend && python main.py
```

**Clear Everything: Nuclear Option**
```bash
# Run complete_cache_clear.sh script above
```
