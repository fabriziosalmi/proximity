# Lifecycle & Consistency Doctrine - Testing Checklist

## Pre-Deployment Verification

### 🔍 Code Review Checklist

- [x] DOCTRINE #1: `delete_app_task` checks `is_adopted` flag
- [x] DOCTRINE #1: Soft delete path implemented for adopted apps
- [x] DOCTRINE #1: Hard delete path preserved for native apps
- [x] DOCTRINE #2: Reconciliation classifies orphans (expected vs anomalous)
- [x] DOCTRINE #2: Sentry alerts for anomalous orphans
- [x] DOCTRINE #2: Soft cleanup for all orphans
- [x] DOCTRINE #3: Janitor only marks as error (no container deletion)
- [x] DOCTRINE #3: Explicit handoff to reconciliation service
- [x] DOCTRINE #4: Adoption captures full Proxmox config
- [x] DOCTRINE #4: Adoption stores actual container status
- [x] DOCTRINE #4: Resource metadata captured at adoption

---

## 🧪 Testing Scenarios

### Scenario 1: Adopted App Deletion (Soft Delete)

**Setup:**
1. Adopt an existing container
2. Verify it shows in Proximity UI
3. Note the VMID on Proxmox

**Test:**
1. Delete the app from Proximity UI
2. Check logs for: `"SOFT DELETE"` message
3. Verify container still exists on Proxmox
4. Verify app removed from Proximity DB

**Expected Result:**
- ✅ Container remains on Proxmox
- ✅ Ports released in Proximity
- ✅ DB record removed
- ✅ Log shows: `"Container VMID X preserved on node 'Y'"`

---

### Scenario 2: Native App Deletion (Hard Delete)

**Setup:**
1. Deploy a new app via Proximity
2. Wait for it to reach `running` state
3. Note the VMID on Proxmox

**Test:**
1. Delete the app from Proximity UI
2. Check logs for: `"HARD DELETE"` message
3. Verify container destroyed on Proxmox
4. Verify app removed from Proximity DB

**Expected Result:**
- ✅ Container destroyed on Proxmox
- ✅ Ports released in Proximity
- ✅ DB record removed
- ✅ Log shows: `"Container VMID X destroyed on Proxmox"`

---

### Scenario 3: Expected Orphan (Removing State)

**Setup:**
1. Deploy an app
2. Start deletion process
3. Manually delete container from Proxmox *during* deletion

**Test:**
1. Wait for reconciliation service to run
2. Check logs for orphan detection
3. Verify classification as "EXPECTED ORPHAN"

**Expected Result:**
- ✅ Log level: INFO (not WARNING)
- ✅ Message: `"EXPECTED ORPHAN: Container removal expected"`
- ✅ No Sentry alert
- ✅ DB record cleaned silently

---

### Scenario 4: Anomalous Orphan (Running State)

**Setup:**
1. Deploy an app and wait for `running` state
2. Manually delete container from Proxmox UI
3. Leave Proximity DB record intact

**Test:**
1. Trigger reconciliation service
2. Check logs for orphan detection
3. Verify Sentry alert sent

**Expected Result:**
- ✅ Log level: CRITICAL
- ✅ Message: `"🚨 ANOMALOUS ORPHAN DETECTED: Container was MANUALLY DELETED"`
- ✅ Sentry alert with level='error'
- ✅ DB record still cleaned (soft cleanup)

---

### Scenario 5: Stuck App (Janitor Service)

**Setup:**
1. Deploy an app
2. Force it into `deploying` state for >1 hour (or modify timeout for testing)

**Test:**
1. Run janitor cleanup service
2. Check logs for diagnosis
3. Verify status change to `error`
4. Verify container NOT deleted

**Expected Result:**
- ✅ App status changed to `error`
- ✅ Log: `"🩺 DIAGNOSING: ... Stuck for Xh Ym"`
- ✅ Log: `"→ Container (if any) will be handled by ReconciliationService"`
- ✅ Container remains on Proxmox (if it exists)
- ✅ DeploymentLog entry created

---

### Scenario 6: Informed Adoption

**Setup:**
1. Create a container manually on Proxmox
2. Configure it with specific resources (e.g., 4 CPUs, 8GB RAM)
3. Start the container

**Test:**
1. Adopt the container via Proximity UI
2. Check the Application record in DB
3. Inspect `config` field

**Expected Result:**
- ✅ Status matches actual Proxmox state (`running`)
- ✅ `config.proxmox_config_snapshot` contains full config
- ✅ `config.resources_at_adoption` has CPU/memory/disk values
- ✅ `config.status_at_adoption` matches actual status
- ✅ Log shows: `"Config snapshot: X keys captured"`

---

## 🔧 Manual Verification Commands

### Check Adoption Metadata
```python
from apps.applications.models import Application

# Find adopted app
app = Application.objects.filter(config__adopted=True).first()

# Verify metadata
print("Adopted:", app.config.get('adopted'))
print("Config snapshot keys:", len(app.config.get('proxmox_config_snapshot', {})))
print("Resources at adoption:", app.config.get('resources_at_adoption'))
print("Status at adoption:", app.config.get('status_at_adoption'))
```

### Trigger Services Manually
```bash
# From Django shell
python manage.py shell

# Reconciliation
from apps.applications.services import ApplicationService
result = ApplicationService.reconcile_applications()
print(result)

# Janitor
result = ApplicationService.cleanup_stuck_applications()
print(result)
```

### Check Logs
```bash
# Celery worker logs
tail -f celery_worker.log | grep -E "(SOFT DELETE|HARD DELETE|ORPHAN|JANITOR)"

# Application logs
tail -f app.log | grep -E "(ADOPT|RECONCILIATION)"
```

---

## 🚨 Regression Tests

### Test 1: Normal Deployment Still Works
- Deploy a new app
- Verify it reaches `running` state
- Verify it's NOT marked as adopted
- Delete it and verify hard delete

### Test 2: Port Allocation Unchanged
- Deploy multiple apps
- Verify unique ports allocated
- Delete apps and verify ports released
- Deploy again and verify ports reused

### Test 3: Existing Adoption Feature
- Existing adoption endpoint still works
- Port detection/allocation still works
- Adopted apps show in UI

---

## 📊 Monitoring Metrics to Track

After deployment, monitor:

1. **Deletion Operations:**
   - Count of soft deletes vs hard deletes
   - Success rate of both paths

2. **Reconciliation Results:**
   - Orphans found per run
   - Expected vs anomalous ratio
   - Sentry alert frequency

3. **Janitor Activity:**
   - Apps marked as error per run
   - Distribution of stuck states

4. **Adoption Success:**
   - Adoption success rate
   - Config snapshot capture success rate

---

## ✅ Success Criteria

All scenarios pass AND:
- ✅ No regressions in existing functionality
- ✅ Clear log differentiation between doctrine paths
- ✅ Sentry alerts only for true anomalies
- ✅ No accidental container deletions

---

## 🎯 QA Sign-off

- [ ] All test scenarios executed
- [ ] Manual verification commands run
- [ ] Logs reviewed for correct classification
- [ ] Sentry integration verified
- [ ] No regressions found
- [ ] Documentation reviewed

**QA Engineer:** _________________  
**Date:** _________________  
**Approved for Production:** [ ] YES [ ] NO

---

## 📝 Notes

_Add any observations, edge cases, or issues found during testing:_

```
[Space for tester notes]
```
