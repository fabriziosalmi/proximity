# Database Cleanup Service

## Overview

The Cleanup Service automatically maintains database integrity by removing stale records that can cause deployment conflicts. It addresses the "ghost app" problem where database records exist for containers that were never created or have been deleted from Proxmox.

## Problem Statement

### Ghost Apps Issue
When deployments fail or containers are manually deleted, database records can remain with:
- **Unique LXC IDs** that block reuse of those container IDs
- **Unique hostnames** that prevent deploying apps with the same name
- **Unique ports** (public_port, internal_port) that can't be reassigned
- **Error status** that clutters the UI and database

This causes subsequent deployments to fail with constraint violations even though the actual Proxmox containers don't exist.

### Example Scenario
```
1. User deploys nginx-test → Creates DB record (VMID 108, ports 30001/40001)
2. Deployment fails after DB insert but before container creation
3. Database still has record with VMID 108, ports 30001/40001
4. Next deployment tries to use VMID 108 → SQLite UNIQUE constraint error
5. Deployment fails even though VMID 108 doesn't exist in Proxmox
```

## Features

### 1. Ghost App Cleanup
Removes database records for apps whose LXC containers don't exist in Proxmox.

**How it works:**
1. Queries all Proxmox nodes for existing LXC container IDs
2. Compares with app records in database
3. Removes records where `lxc_id` doesn't exist in Proxmox
4. Frees up associated ports for reuse

### 2. Old Error Cleanup
Removes apps with 'error' status after a configurable retention period.

**Use cases:**
- Failed deployments that will never be retried
- Testing/development cleanup
- Preventing database bloat

### 3. Background Operation
Runs automatically in the background at configurable intervals.

## Configuration

All configuration is done via environment variables in `.env`:

### `CLEANUP_ENABLED`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Master switch for cleanup service
- **Values:** `true`, `false`, `1`, `0`, `yes`, `no`

```bash
# Disable cleanup entirely
CLEANUP_ENABLED=false
```

### `ERROR_RETENTION_HOURS`
- **Type:** Integer
- **Default:** `24`
- **Description:** Hours to keep error status apps before cleanup
- **Minimum:** `1`

```bash
# Keep errors for 3 days
ERROR_RETENTION_HOURS=72

# Aggressive cleanup for testing (1 hour)
ERROR_RETENTION_HOURS=1
```

### `GHOST_CLEANUP_ENABLED`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable cleanup of ghost apps (DB records without Proxmox containers)

```bash
# Disable ghost cleanup (e.g., for debugging)
GHOST_CLEANUP_ENABLED=false
```

### `CLEANUP_INTERVAL_MINUTES`
- **Type:** Integer
- **Default:** `60`
- **Description:** How often to run cleanup cycle
- **Minimum:** `5`

```bash
# Run cleanup every 30 minutes
CLEANUP_INTERVAL_MINUTES=30

# Run cleanup every 4 hours
CLEANUP_INTERVAL_MINUTES=240
```

### `CLEANUP_DRY_RUN`
- **Type:** Boolean
- **Default:** `false`
- **Description:** Log what would be deleted without actually deleting

```bash
# Test cleanup behavior without making changes
CLEANUP_DRY_RUN=true
```

## Usage Recommendations

### Homelab with Few Machines (High Activity)
```bash
CLEANUP_ENABLED=true
ERROR_RETENTION_HOURS=4
GHOST_CLEANUP_ENABLED=true
CLEANUP_INTERVAL_MINUTES=30
```
**Rationale:** Quick cleanup to free limited resources, frequent testing creates many errors.

### Homelab with Many Machines (Low Activity)
```bash
CLEANUP_ENABLED=true
ERROR_RETENTION_HOURS=72
GHOST_CLEANUP_ENABLED=true
CLEANUP_INTERVAL_MINUTES=120
```
**Rationale:** More resources available, keep records longer for debugging.

### Production/Team Environment
```bash
CLEANUP_ENABLED=true
ERROR_RETENTION_HOURS=168  # 7 days
GHOST_CLEANUP_ENABLED=true
CLEANUP_INTERVAL_MINUTES=240
```
**Rationale:** Keep records for audit/debugging, cleanup is less critical.

### Development/Testing
```bash
CLEANUP_ENABLED=true
ERROR_RETENTION_HOURS=1
GHOST_CLEANUP_ENABLED=true
CLEANUP_INTERVAL_MINUTES=15
CLEANUP_DRY_RUN=false
```
**Rationale:** Aggressive cleanup during active development.

## API Endpoints

### Get Cleanup Statistics
```bash
GET /api/v1/system/cleanup/stats
```

**Response:**
```json
{
  "enabled": true,
  "last_run": "2025-10-13T22:45:00Z",
  "ghost_apps_removed": 40,
  "old_errors_removed": 5,
  "ports_freed": 90,
  "total_removed": 45,
  "errors": [],
  "config": {
    "error_retention_hours": 24,
    "ghost_cleanup_enabled": true,
    "cleanup_interval_minutes": 60,
    "dry_run": false
  }
}
```

### Trigger Manual Cleanup
```bash
POST /api/v1/system/cleanup/run
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Cleanup complete: removed 40 apps, freed 80 ports",
  "stats": { ... }
}
```

## Monitoring

### Logs
The cleanup service logs all operations:

```
INFO: 🧹 CleanupService initialized: CleanupConfig(enabled=True, error_retention=24h, ghost_cleanup=True, interval=60m, dry_run=False)
INFO: 🧹 Starting cleanup cycle...
INFO: 📦 Found 14 LXC containers in Proxmox: [100, 103, 104, 105, 106, 107, ...]
INFO: 👻 Found 40 ghost apps (DB records without Proxmox containers)
INFO:   - nginx-e2e-202510121506-vnjgdd (LXC 108, status: error)
INFO:   - nginx-e2e-202510121509-pqubva (LXC 109, status: error)
INFO:   ... and 38 more
INFO: ✓ Cleaned up 40 ghost apps
INFO: ✅ Cleanup complete: CleanupStats(ghosts=40, old_errors=0, ports_freed=80, total=40) (freed 80 ports)
```

### Dry Run Mode
Test cleanup behavior without making changes:

```bash
CLEANUP_DRY_RUN=true
```

Logs will show:
```
INFO: [DRY RUN] Would delete: nginx-e2e-202510121506-vnjgdd (LXC 108)
INFO: [DRY RUN] Would delete: nginx-e2e-202510121509-pqubva (LXC 109)
...
INFO: ✅ [DRY RUN] Cleanup complete: CleanupStats(...)
```

## Safety Features

1. **Conservative Proxmox Query:** If Proxmox connection fails, ghost cleanup is skipped
2. **Minimum Retention:** Error retention cannot be set below 1 hour
3. **Minimum Interval:** Cleanup interval cannot be set below 5 minutes
4. **Dry Run Mode:** Test cleanup behavior before enabling
5. **Graceful Degradation:** Cleanup failures don't crash the application
6. **Transaction Safety:** All deletions are committed together or rolled back

## Troubleshooting

### Cleanup Not Running
**Check:** Is cleanup enabled?
```bash
# View current config
curl http://localhost:8765/api/v1/system/cleanup/stats
```

**Fix:** Enable cleanup
```bash
CLEANUP_ENABLED=true
```

### Too Many Records Kept
**Check:** Current retention settings
```bash
curl http://localhost:8765/api/v1/system/cleanup/stats | jq '.config'
```

**Fix:** Lower retention hours
```bash
ERROR_RETENTION_HOURS=4  # More aggressive
```

### Cleanup Runs Too Often
**Check:** Current interval
```bash
curl http://localhost:8765/api/v1/system/cleanup/stats | jq '.config.cleanup_interval_minutes'
```

**Fix:** Increase interval
```bash
CLEANUP_INTERVAL_MINUTES=120  # Every 2 hours
```

### Want to Test Without Deleting
**Fix:** Enable dry run
```bash
CLEANUP_DRY_RUN=true
```

## Integration with Deployment

The cleanup service solves deployment failures caused by:

1. **UNIQUE constraint on lxc_id:** Ghost apps block VMID reuse
2. **UNIQUE constraint on hostname:** Old records prevent name reuse  
3. **UNIQUE constraint on public_port/internal_port:** Ports can't be reassigned

After cleanup runs, these constraints are freed and deployments can succeed.

## Performance Impact

- **Proxmox API Queries:** One query per node per cleanup cycle (cached for 60 seconds)
- **Database Queries:** Two queries per cleanup cycle (ghost apps + old errors)
- **CPU Usage:** Minimal (< 1% for typical cleanup)
- **Memory Usage:** < 50MB for cleanup operations

## Future Enhancements

Potential future features:
- Cleanup of orphaned port assignments
- Cleanup of orphaned backup records
- Metrics export for monitoring systems
- Webhook notifications for cleanup events
- User-specific retention policies
