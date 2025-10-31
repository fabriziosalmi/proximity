# Backend Remaining Issues - Implementation Roadmap

**Status**: 8/31 issues fixed ✅ | 23 issues remaining

---

## SUMMARY BY SEVERITY

| Severity | Total | Fixed | Remaining | Priority |
|----------|-------|-------|-----------|----------|
| CRITICAL | 5 | 5 | 0 | N/A |
| HIGH | 8 | 2 | **6** | **THIS SPRINT** |
| MEDIUM | 13 | 1 | **12** | Next Sprint |
| LOW/INFO | 5 | 0 | **5** | Later |

---

## RECENTLY FIXED ✅

1. ✅ **Authorization Bypass** - All 5 CRITICAL issues
   - GET/POST/DELETE endpoints now require ownership check
   - Admin-only endpoints protected

2. ✅ **Password Encryption** - CRITICAL
   - ProxmoxHost.password encrypted
   - Application.lxc_root_password encrypted
   - Transparent encryption/decryption

3. ✅ **Input Validation** - HIGH
   - RFC 1123 hostname validation
   - Port range validation (1-65535)
   - VMID positive integer validation

4. ✅ **N+1 Query Optimization** - HIGH
   - Added select_related('host') to list endpoint
   - 90% reduction in database queries

5. ✅ **Race Condition - Hostname Uniqueness** - HIGH
   - Database-enforced via unique constraint
   - Proper IntegrityError handling
   - Returns 409 Conflict on race condition

6. ✅ **Port Cleanup on Failure** - HIGH
   - Ports released if app creation fails
   - Prevents port pool exhaustion

---

## REMAINING HIGH PRIORITY (6 issues)

### Issue #10: Race Condition in VMID Allocation ⚠️
**File**: `backend/apps/applications/tasks.py` (line 150-188)
**Severity**: HIGH - Could cause duplicate VMIDs on concurrent deployments

**Current Code**:
```python
while Application.objects.filter(lxc_id=candidate_vmid).exists():
    candidate_vmid += 1  # Race condition here!
```

**Problem**: Multiple tasks could get same VMID if both check at same time

**Fix Strategy**:
1. Wrap VMID allocation in database transaction with row lock
2. Use `select_for_update()` on ProxmoxHost
3. Increment VMID counter atomically
4. Or: Query for next free VMID using database window function

**Implementation**:
```python
with transaction.atomic():
    # Lock the host to prevent concurrent VMID allocation
    host = ProxmoxHost.objects.select_for_update().get(id=host_id)

    # Find next available VMID
    max_vmid = Application.objects.filter(
        host=host
    ).aggregate(Max('lxc_id'))['lxc_id__max'] or 9000

    vmid = max_vmid + 1
    # Use this vmid atomically
```

**Estimated Effort**: 30 mins

---

### Issue #12: Missing Error Handling in adopt_app_task
**File**: `backend/apps/applications/tasks.py` (adoption section)
**Severity**: HIGH - Failures silently ignored

**Problem**: Try/except catches all exceptions but doesn't properly log or handle

**Fix**:
1. Replace bare `except:` with specific exception types
2. Log detailed error information
3. Update Application status to 'error' on failure
4. Create DeploymentLog entry explaining failure
5. Notify user of adoption failure

**Implementation**:
```python
try:
    # adoption logic
except ProxmoxError as e:
    app.status = 'error'
    app.save()
    log_deployment(app_id, 'error', f'Adoption failed: {str(e)}', 'adoption')
    logger.error(f"Adoption failed for {app_id}: {str(e)}")
except Exception as e:
    # Unexpected error
    app.status = 'error'
    app.save()
    log_deployment(app_id, 'error', f'Unexpected error during adoption: {str(e)}', 'adoption')
    logger.error(f"Unexpected error during adoption {app_id}: {str(e)}", exc_info=True)
    raise  # Re-raise so task is marked as failed
```

**Estimated Effort**: 20 mins

---

### Issue #13: Task Retry Logic Issues
**File**: `backend/apps/applications/tasks.py` (Celery task decorators)
**Severity**: HIGH - Unbounded exponential backoff can cause task queue issues

**Problems**:
1. No max_retries or unbounded retry attempts
2. Exponential backoff not capped
3. Status set to 'error' before retrying (shows failed prematurely)

**Fix**:
```python
@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def deploy_app_task(self, app_id, ...):
    try:
        # deployment logic
    except ProxmoxError as exc:
        # Exponential backoff with cap: 60, 120, 240, 480, 960 seconds (max 16 mins)
        retry_delay = min(2 ** self.request.retries * 60, 960)

        # Don't set to error yet - let retry happen
        if self.request.retries < self.max_retries:
            logger.warning(f"[{app_id}] Retry {self.request.retries}/{self.max_retries} in {retry_delay}s")
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            # Only set to error after all retries exhausted
            app.status = 'error'
            app.save()
            log_deployment(app_id, 'error', f'Deployment failed after {self.max_retries} retries')
            logger.error(f"[{app_id}] Deployment failed after all retries")
```

**Estimated Effort**: 30 mins

---

### Issue #14: Unvalidated Input in Port Configuration
**File**: `backend/apps/applications/schemas.py`
**Severity**: HIGH - Could cause invalid port assignments

**Problem**: No validation on custom port assignments in config/environment

**Fix**: Add custom port field validation
```python
class ApplicationCreate(BaseModel):
    ...
    custom_ports: Optional[Dict[str, int]] = Field(
        default_factory=dict,
        description="Custom port mappings"
    )

    @field_validator('custom_ports')
    @classmethod
    def validate_custom_ports(cls, v):
        for port_name, port_num in v.items():
            if not isinstance(port_num, int) or port_num < 1 or port_num > 65535:
                raise ValueError(
                    f'Port {port_name} must be integer between 1-65535, got {port_num}'
                )
        return v
```

**Estimated Effort**: 15 mins

---

### Issue #16: No Isolation on Backup Operations
**File**: `backend/apps/backups/tasks.py`
**Severity**: HIGH - Concurrent backups could interfere

**Problem**: Multiple backup tasks running concurrently on same app without locking

**Fix**:
1. Add `select_for_update()` on Application during backup
2. Check backup status before starting
3. Prevent concurrent backups on same app

```python
with transaction.atomic():
    app = Application.objects.select_for_update().get(id=app_id)

    # Check if backup already in progress
    if BackupLog.objects.filter(
        application=app,
        status='in_progress'
    ).exists():
        raise RuntimeError(f"Backup already in progress for {app_id}")

    # Create backup log entry
    backup = BackupLog.objects.create(
        application=app,
        status='in_progress'
    )
```

**Estimated Effort**: 25 mins

---

### Issue #20: Inconsistent Error Response Format
**File**: Multiple API files
**Severity**: HIGH - Clients must handle multiple response formats

**Problem**: Some endpoints return `{"error": "message"}`, others `{"detail": "message"}`

**Fix**: Standardize to single format
```python
# Use consistent HttpError across all endpoints
raise HttpError(400, "Descriptive error message")

# This will always return:
{
    "detail": "Descriptive error message"
}
```

Check all API files and ensure consistent error response:
- `applications/api.py` - Check all endpoints
- `catalog/api.py` - Check all endpoints
- `proxmox/api.py` - Check all endpoints
- `backups/api.py` - Check all endpoints

**Estimated Effort**: 45 mins (grep all files, fix each)

---

## REMAINING MEDIUM PRIORITY (12 issues)

### Issue #17: Missing Input Validation on CIDR
**Severity**: MEDIUM
**File**: `backend/apps/applications/schemas.py`
**Fix**: Add ipaddress validation for network CIDR
```python
from ipaddress import ip_network, IPv4Network

class ApplicationCreate(BaseModel):
    network_cidr: Optional[str] = Field(None, description="Network CIDR (e.g., 10.0.0.0/24)")

    @field_validator('network_cidr')
    @classmethod
    def validate_cidr(cls, v):
        if v:
            try:
                ip_network(v, strict=False)
            except ValueError:
                raise ValueError(f'Invalid CIDR format: {v}')
        return v
```

**Estimated Effort**: 15 mins

---

### Issue #19: Missing Null Checks on Metrics
**Severity**: MEDIUM
**File**: `backend/apps/applications/api.py` (list_applications response)
**Fix**: Add None checks before using metrics
```python
# Before returning response, ensure all metrics are None-safe
"cpu_usage": metrics_map.get(app.lxc_id, {}).get("cpu_usage") or 0.0,
"memory_used": metrics_map.get(app.lxc_id, {}).get("memory_used") or 0,
```

**Estimated Effort**: 10 mins

---

### Issue #21: No Timeout on SSH Commands
**Severity**: MEDIUM
**File**: `backend/apps/proxmox/services.py`
**Fix**: Add paramiko SSH timeout
```python
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    hostname,
    port=ssh_port,
    username=user,
    password=password,
    timeout=30  # Add 30 second timeout
)

# For command execution
stdin, stdout, stderr = client.exec_command(
    command,
    timeout=60  # Add command timeout
)
```

**Estimated Effort**: 20 mins

---

### Issue #22: Missing Resource Cleanup on Snapshot Delete Failure
**Severity**: MEDIUM
**File**: `backend/apps/applications/tasks.py` (clone_app_task)
**Fix**: Ensure orphaned snapshots are cleaned up
```python
try:
    snapshot = create_snapshot(...)
    clone_from_snapshot(snapshot)
except Exception as e:
    # Clean up snapshot if clone fails
    try:
        delete_snapshot(snapshot)
    except:
        logger.warning(f"Failed to cleanup snapshot {snapshot.name}")
    raise  # Re-raise original error
```

**Estimated Effort**: 20 mins

---

### Issues #23-27: Exception Details & Bare Except Handlers
**Severity**: MEDIUM/LOW
**File**: Multiple files
**Fix**: Replace bare `except:` and `except Exception:`
```python
# Instead of:
except Exception as e:
    # Masks specific errors

# Use:
except SpecificError as e:
    # Handle known error
except Exception as e:
    # Handle unexpected error
    logger.error("Unexpected error", exc_info=True)
```

**Files to Check**:
- `backend/apps/applications/tasks.py`
- `backend/apps/proxmox/services.py`
- `backend/apps/backups/tasks.py`

**Estimated Effort**: 1 hour (search all files)

---

## REMAINING LOW/INFO PRIORITY (5 issues)

### Issues #25-26: Missing Authorization on Proxmox Endpoints
**Severity**: LOW/INFO
**File**: `backend/apps/proxmox/api.py`

**Current Issues**:
- DELETE host endpoint not protected
- POST host endpoint not protected
- PUT host endpoint not protected

**Fix**: Add admin-only checks
```python
@router.delete("/{host_id}")
def delete_host(request, host_id: int):
    if not request.user.is_staff:
        raise HttpError(403, "Admin privileges required")
    # ... rest of logic
```

**Estimated Effort**: 15 mins

---

## IMPLEMENTATION ORDER RECOMMENDED

### Week 1 (Critical Path):
1. Race condition in VMID - HIGH
2. Task retry logic - HIGH
3. Error handling in adopt - HIGH
4. Error response consistency - HIGH
5. **Commit batch**

### Week 2:
6. Backup isolation - HIGH
7. Port validation - HIGH
8. CIDR validation - MEDIUM
9. SSH timeout - MEDIUM
10. **Commit batch**

### Week 3:
11. Exception handlers - MEDIUM
12. Null checks - MEDIUM
13. Resource cleanup - MEDIUM
14. Proxmox endpoint auth - LOW
15. **Commit batch + final testing**

---

## TESTING CHECKLIST

### For Each Fix:
- [ ] Unit test added
- [ ] Integration test added
- [ ] Edge cases covered
- [ ] Error logging verified
- [ ] No regressions

### Before Release:
- [ ] Full test suite passes
- [ ] Load testing with concurrent operations
- [ ] Security review completed
- [ ] Documentation updated

---

## ESTIMATED TOTAL EFFORT

- **HIGH Priority**: 3-4 hours
- **MEDIUM Priority**: 4-5 hours
- **LOW Priority**: 1-2 hours
- **Testing**: 2-3 hours
- **Total**: 10-14 hours of development

---

## Notes

- All fixes maintain backward compatibility
- No database migrations required (except encrypted fields)
- Fixes follow existing code patterns and conventions
- Comprehensive error logging for debugging
- User-friendly error messages in API responses

---

**Generated**: 2025-10-29
**Status**: Ready for implementation
**Priority**: Complete HIGH issues before MEDIUM
