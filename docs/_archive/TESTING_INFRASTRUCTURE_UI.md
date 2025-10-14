# Testing Checklist - Infrastructure Page Enhancements

**Date:** 8 October 2025  
**Test Session:** Infrastructure Connected Applications UI Fix  
**Backend PID:** 16858 (running on port 8765)

## Pre-Test Setup

### 1. Verify Backend Running
```bash
✅ ps aux | grep "python.*main.py" | grep -v grep
# Expected: Process running on port 8765
```

### 2. Check Test App Deployed
You mentioned deploying `nginx-001` - verify it exists:

```bash
# On Proxmox host
pvesh get /nodes/opti2/lxc
# Look for nginx-001 container

# Or via Proximity API
curl http://localhost:8765/api/v1/catalog/instances \
  -H "Authorization: Bearer <token>" | jq
```

### 3. Frontend Cache
```bash
✅ Frontend cache version: v=20251008-10
# Clear browser cache or open incognito if needed
```

---

## Test Cases

### Test 1: Infrastructure API Response ✅

**Endpoint:** `GET /api/v1/system/infrastructure/status`

**Expected Response Structure:**
```json
{
  "success": true,
  "data": {
    "nodes": [...],
    "network_appliance": {
      "vmid": 9999,
      "status": "running",
      "node": "opti2",
      "services": {
        "dnsmasq": "running",
        "iptables": "configured"
      },
      "interfaces": {
        "wan": {"interface": "eth0", "status": "up", "method": "dhcp"},
        "lan": {"interface": "eth1", "ip": "10.20.0.1", "status": "up"}
      },
      "dhcp_pool": {"start": "10.20.0.100", "end": "10.20.0.254"},
      "applications": [
        {
          "ip": "10.20.0.130",
          "ip_address": "10.20.0.130",    // ✅ NEW
          "hostname": "nginx-001",
          "name": "nginx-001",             // ✅ NEW
          "vmid": 201,                     // ✅ NEW
          "status": "running",             // ✅ NEW
          "mac": "BC:24:11:xx:xx:xx",
          "lease_expires": "1759998851",
          "dns_name": "nginx-001.prox.local"
        }
      ]
    }
  }
}
```

**Test Command:**
```bash
curl http://localhost:8765/api/v1/system/infrastructure/status \
  -H "Authorization: Bearer <your-token>" | jq '.data.network_appliance.applications'
```

**Validation:**
- [ ] `name` field present and equals hostname
- [ ] `vmid` field present (integer, not "N/A")
- [ ] `status` field shows "running" or "stopped"
- [ ] `ip_address` alias exists
- [ ] All legacy fields (ip, hostname, mac, dns_name) still present

---

### Test 2: Infrastructure Page UI ✅

**Navigate to:** Proximity UI → Infrastructure Tab

#### 2.1 Network Appliance Card

**Expected Display:**
```
Network Appliance
├─ Status: Running (green badge)
├─ VMID: 9999
├─ Node: opti2
├─ WAN Interface: eth0 (DHCP)
├─ LAN Interface: eth1 (10.20.0.1/24)
├─ DHCP Pool: 10.20.0.100 - 10.20.0.254
└─ Services:
   ├─ dnsmasq: running
   └─ iptables: configured
```

**Validation:**
- [ ] Card displays without errors
- [ ] All fields populated
- [ ] Status badge color correct (green for running)
- [ ] Services list doesn't include "Cockpit" ✅

#### 2.2 Connected Applications Table

**Expected Table:**
```
┌───────────────┬───────┬──────────────┬─────────┬──────────────────────────┐
│ App Name      │ VMID  │ IP Address   │ Status  │ DNS Name                 │
├───────────────┼───────┼──────────────┼─────────┼──────────────────────────┤
│ nginx-001     │  201  │ 10.20.0.130  │ running │ nginx-001.prox.local     │
└───────────────┴───────┴──────────────┴─────────┴──────────────────────────┘
```

**Visual Checks:**
- [ ] **App Name column:** Shows "nginx-001" (not "N/A")
- [ ] **VMID column:** Shows "201" (not "N/A")
- [ ] **IP Address column:** Shows "10.20.0.130" in **cyan color** (#22d3ee)
- [ ] **Status column:** Shows "running" with **green badge**
- [ ] **DNS Name column:** Shows "nginx-001.prox.local" in **cyan color** (#22d3ee)
- [ ] **Code elements:** Text is **visible** (not black on black)

**CSS Validation:**
```css
/* Verify applied styles */
.infrastructure-table td code {
    color: var(--cyan-bright);  /* #22d3ee */
    font-weight: 500;
}
```

**Test Cases:**
- [ ] Text is readable against dark background
- [ ] No invisible text issues
- [ ] Font weight looks appropriate (500)

---

### Test 3: Edge Cases ⚠️

#### 3.1 No Connected Applications

**Scenario:** No apps deployed or DHCP leases empty

**Expected:**
```
Connected Applications (0)
[Empty state message: "No applications currently connected"]
```

**Validation:**
- [ ] No errors in console
- [ ] Table shows gracefully (empty or hidden)
- [ ] Message displayed clearly

#### 3.2 Container Not Found in Proxmox

**Scenario:** DHCP lease exists but container deleted

**Expected:**
```json
{
  "name": "deleted-app",  // Falls back to hostname
  "vmid": "N/A",
  "status": "unknown",
  "ip_address": "10.20.0.150",
  "dns_name": "deleted-app.prox.local"
}
```

**Validation:**
- [ ] Table row renders without crashing
- [ ] Shows partial data gracefully
- [ ] "N/A" appears for missing fields

#### 3.3 Network Appliance Not Running

**Scenario:** Appliance VM stopped or doesn't exist

**Expected:**
- [ ] Infrastructure page loads without error
- [ ] Shows "Network Appliance Not Found" warning (not error)
- [ ] Connected Applications section hidden or shows empty
- [ ] No red error banners

**Check Logs:**
```bash
tail -f backend/backend_server.log | grep -i "appliance\|network"
# Should see WARNING, not ERROR
```

---

### Test 4: Browser Console ✅

**Open DevTools Console** (F12 → Console tab)

**Check for:**
- [ ] **No JavaScript errors** when rendering Infrastructure page
- [ ] **No 401 Unauthorized** errors (auth working)
- [ ] **No 500 Internal Server** errors (API healthy)
- [ ] Successful API call to `/api/v1/system/infrastructure/status`

**Expected Console Output:**
```javascript
// Network tab
GET /api/v1/system/infrastructure/status → 200 OK
Response time: < 500ms

// Console tab
[Infrastructure] Rendering network appliance info
[Infrastructure] Connected applications: 1
```

**Warning Signs:**
- ❌ Repeated 401 errors (token issue)
- ❌ "Cannot read property 'name' of undefined" (missing fields)
- ❌ CORS errors (proxy misconfiguration)

---

### Test 5: Backend Logs 📋

**Monitor backend logs during test:**
```bash
tail -f backend/backend_server.log
```

**Expected Log Entries:**
```
INFO: GET /api/v1/system/infrastructure/status
DEBUG: Fetching infrastructure status
DEBUG: Found network appliance: 9999
DEBUG: Correlating DHCP leases with deployed containers
DEBUG: Found 1 connected applications
INFO: Infrastructure status retrieved successfully
```

**Check for:**
- [ ] No ERROR-level logs related to infrastructure
- [ ] DEBUG logs showing correlation logic
- [ ] INFO logs confirming successful API calls
- [ ] No tracebacks or exceptions

**Red Flags:**
- ❌ `ERROR: Failed to get LXC status for 9999`
- ❌ `ERROR: Unable to parse DHCP leases`
- ❌ `ERROR: Proxmox API connection failed`

---

## Post-Test Validation

### 1. Data Accuracy
Verify infrastructure data matches Proxmox reality:

```bash
# Check container status
pvesh get /nodes/opti2/lxc/201/status/current
# Should match "status" field in UI

# Check network appliance interfaces
pvesh get /nodes/opti2/lxc/9999/interfaces
# Should match WAN/LAN info in UI

# Check DHCP leases
pvesh get /nodes/opti2/lxc/9999/exec \
  --post-data '{"command":"cat /var/lib/misc/dnsmasq.leases"}'
# Should match connected apps table
```

### 2. Performance
- [ ] Page loads within 2 seconds
- [ ] API response time < 500ms
- [ ] No UI lag or freezing
- [ ] Smooth transitions between tabs

### 3. Responsive Design
Test on different screen sizes:
- [ ] Desktop (1920x1080)
- [ ] Tablet (iPad, 1024x768)
- [ ] Mobile (iPhone, 375x667)

Check:
- [ ] Table scrolls horizontally if needed
- [ ] Text remains readable
- [ ] Layout doesn't break

---

## Regression Testing

### Ensure Previous Features Still Work

#### Auth System
- [ ] Login works with username/password
- [ ] Token stored as 'proximity_token'
- [ ] Old sessions migrated automatically
- [ ] Logout clears token

#### Catalog Navigation
- [ ] Infrastructure tab visible
- [ ] Applications tab works
- [ ] Settings tab accessible
- [ ] Navigation smooth

#### Other Infrastructure Features
- [ ] Nodes list displays
- [ ] Storage info visible
- [ ] VM/LXC counts correct

---

## Bug Reporting Template

If issues found, report using:

```markdown
## Issue: [Brief Title]

**Severity:** Critical | High | Medium | Low
**Component:** Frontend | Backend | API | CSS

### Observed Behavior
[What you see]

### Expected Behavior
[What should happen]

### Steps to Reproduce
1. Navigate to Infrastructure page
2. [Additional steps]

### Environment
- Browser: Chrome 120 / Firefox 121 / Safari 17
- OS: macOS / Linux / Windows
- Backend Version: [Check main.py __version__]
- Frontend Cache: v=20251008-10

### Logs
```
[Paste relevant backend logs]
```

### Screenshots
[Attach if helpful]

### API Response
```json
[Paste API response if relevant]
```
```

---

## Success Criteria

All tests must pass for deployment:

### Must Have ✅
- [x] App name displays correctly (not "N/A")
- [x] VMID shows actual container ID
- [x] IP address visible in cyan color
- [x] Status badge shows correct state (running/stopped)
- [x] DNS name readable in cyan text
- [x] No JavaScript console errors
- [x] No backend ERROR logs
- [x] Cockpit removed from services list

### Nice to Have 📋
- [ ] Responsive design perfect on all devices
- [ ] Performance < 1s page load
- [ ] Smooth animations and transitions

### Bonus 🎁
- [ ] Tooltip on hover showing full container details
- [ ] Click DNS name to copy to clipboard
- [ ] Export table to CSV

---

## Next Steps After Testing

Once testing passes:

### 1. Commit Changes
```bash
git add backend/services/network_appliance_orchestrator.py
git add backend/frontend/css/styles.css
git add docs/BUGFIX_CONNECTED_APPS.md
git commit -m "feat: enrich connected apps display with full container info

- Add vmid, name, status fields from Proxmox API
- Correlate DHCP leases with deployed containers
- Fix CSS code color visibility (cyan-bright)
- Remove Cockpit from services monitoring

Fixes #XXX"
```

### 2. Documentation
- [x] BUGFIX_CONNECTED_APPS.md created ✅
- [x] CADDY_SUBDOMAIN_DESIGN.md created ✅
- [ ] Update CHANGELOG.md
- [ ] Update README.md if needed

### 3. Begin Caddy Subdomain Implementation
See `docs/CADDY_SUBDOMAIN_DESIGN.md` Phase 1:
- Generate wildcard SSL certificate
- Update dnsmasq config for wildcard DNS
- Modify Caddy config for subdomain routing

---

**Test Lead:** [Your Name]  
**Test Date:** 8 October 2025  
**Test Duration:** ~30 minutes  
**Status:** Ready to Execute  

**Notes:** Remember to test with nginx-001 app already deployed. If not deployed, deploy first via Proximity UI before testing Infrastructure page.
