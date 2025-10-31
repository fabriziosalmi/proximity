# Proximity Backend Security & Quality Audit Report

## Executive Summary

This is a comprehensive audit of the Proximity backend codebase examining critical issues across security, error handling, race conditions, type safety, resource management, and API design. **31 significant issues were identified** ranging from CRITICAL to INFO severity.

---

## CRITICAL SEVERITY ISSUES

### Issue #1: Missing Authorization Check on Application Access
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 365-386)
**Method:** `get_application(request, app_id: str)`
**Severity:** CRITICAL - Authorization Bypass

**Code:**
```python
@router.get("/{app_id}", response=ApplicationResponse)
def get_application(request, app_id: str):
    """Get application details."""
    app = get_object_or_404(Application, id=app_id)
    
    return {
        "id": app.id,
        # ... returns full app details
    }
```

**Issue:** The endpoint does NOT check if `request.user` or `request.auth` owns the application. Any authenticated user can access ANY application in the system.

**Root Cause:** Missing ownership validation after `get_object_or_404()`.

**Security Impact:** High - Information Disclosure. Users can enumerate and view all applications, their ports, configurations, and owner information.

**Fix:**
```python
@router.get("/{app_id}", response=ApplicationResponse)
def get_application(request, app_id: str):
    """Get application details."""
    queryset = Application.objects.all()
    
    # Authorization: non-admins see only their own apps
    if request.user.is_authenticated and not request.user.is_staff:
        queryset = queryset.filter(owner=request.user)
    
    app = get_object_or_404(queryset, id=app_id)
    
    return {
        "id": app.id,
        # ... rest of response
    }
```

---

### Issue #2: Missing Authorization on Application Actions (Start/Stop/Restart/Delete)
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 389-417)
**Method:** `app_action(request, app_id: str, payload: ApplicationAction)`
**Severity:** CRITICAL - Authorization Bypass

**Code:**
```python
@router.post("/{app_id}/action")
def app_action(request, app_id: str, payload: ApplicationAction):
    """Perform an action on an application."""
    app = get_object_or_404(Application, id=app_id)
    
    action = payload.action.lower()
    
    if action == 'start':
        start_app_task.delay(app_id)
        return {"success": True, "message": f"Starting {app.name}"}
    elif action == 'delete':
        delete_app_task.delay(app_id)
        return {"success": True, "message": f"Deleting {app.name}"}
    # ... etc
```

**Issue:** No ownership check. Any authenticated user can start, stop, restart, or DELETE any application.

**Security Impact:** CRITICAL - Resource Hijacking. Users can destroy other users' applications, stop critical services, etc.

**Fix:** Add ownership check before executing any action:
```python
@router.post("/{app_id}/action")
def app_action(request, app_id: str, payload: ApplicationAction):
    """Perform an action on an application."""
    queryset = Application.objects.all()
    
    if request.user.is_authenticated and not request.user.is_staff:
        queryset = queryset.filter(owner=request.user)
    
    app = get_object_or_404(queryset, id=app_id)
    
    action = payload.action.lower()
    # ... rest of logic
```

---

### Issue #3: Missing Authorization on Clone Endpoint
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 420-469)
**Method:** `clone_application(request, app_id: str, payload: ApplicationClone)`
**Severity:** CRITICAL - Authorization Bypass

**Code:**
```python
@router.post("/{app_id}/clone", response={202: dict})
def clone_application(request, app_id: str, payload: ApplicationClone):
    """Clone an existing application."""
    source_app = get_object_or_404(Application, id=app_id)
    
    # ... no ownership validation ...
    
    clone_app_task.delay(...)
```

**Issue:** Missing authorization check. Any user can clone any application in the system.

**Security Impact:** CRITICAL - Unauthorized Resource Creation. Enables resource exhaustion attacks and privilege escalation.

**Fix:** Add the same ownership check pattern before cloning.

---

### Issue #4: Missing Authorization on Logs Endpoint
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 472-494)
**Method:** `get_application_logs(request, app_id: str, limit: int = 50)`
**Severity:** HIGH - Information Disclosure

**Code:**
```python
@router.get("/{app_id}/logs", response=ApplicationLogsResponse)
def get_application_logs(request, app_id: str, limit: int = 50):
    """Get deployment logs for an application."""
    app = get_object_or_404(Application, id=app_id)
    
    logs = DeploymentLog.objects.filter(application=app).order_by('-timestamp')[:limit]
    # ... returns logs without ownership check
```

**Issue:** No authorization check on logs endpoint. Logs may contain sensitive information.

**Security Impact:** HIGH - Information Disclosure. Deployment logs may reveal infrastructure details, API keys, or configuration secrets.

**Fix:** Add ownership validation before returning logs.

---

### Issue #5: Missing Admin Permission Check on Catalog Reload
**File:** `/Users/fab/GitHub/proximity/backend/apps/catalog/api.py` (Lines 97-113)
**Method:** `reload_catalog(request)`
**Severity:** CRITICAL - Missing Access Control

**Code:**
```python
@router.post("/reload", summary="Reload catalog from disk")
def reload_catalog(request):
    """Reload the catalog from disk."""
    # TODO: Add permission check for admin users
    catalog_service.reload()
    stats = catalog_service.get_stats()
    return {
        "message": "Catalog reloaded successfully",
        "stats": stats
    }
```

**Issue:** TODO comment indicates missing permission check. Any authenticated user can reload the catalog.

**Security Impact:** CRITICAL - Administrative function exposed. Could cause service disruption, resource exhaustion, or be used in DOS attacks.

**Fix:**
```python
@router.post("/reload", summary="Reload catalog from disk")
def reload_catalog(request):
    """Reload the catalog from disk. Requires admin privileges."""
    if not request.auth or not request.auth.is_staff:
        raise HttpError(403, "Admin privileges required")
    
    catalog_service.reload()
    stats = catalog_service.get_stats()
    return {
        "message": "Catalog reloaded successfully",
        "stats": stats
    }
```

---

### Issue #6: Missing Authorization on Backup Operations
**File:** `/Users/fab/GitHub/proximity/backend/apps/backups/api.py` (Lines 42-66)
**Severity:** HIGH - Authorization Issues

**Code:**
```python
def list_app_backups(request, app_id: str):
    """List all backups for an application."""
    app = get_object_or_404(
        Application.objects.filter(owner=request.auth),
        id=app_id
    )
```

**Issue:** Filter uses `request.auth` but this may be `None` if user is unauthenticated. No explicit null check, will just silently return no apps instead of raising 403.

**Security Impact:** MEDIUM - Silent Failure. If auth system fails, users silently get "no backups" instead of an error, masking issues.

**Fix:**
```python
def list_app_backups(request, app_id: str):
    """List all backups for an application."""
    if not request.auth:
        raise HttpError(401, "Authentication required")
    
    app = get_object_or_404(
        Application.objects.filter(owner=request.auth),
        id=app_id
    )
```

---

### Issue #7: Unencrypted Password Storage in Database
**File:** `/Users/fab/GitHub/proximity/backend/apps/proxmox/models.py` (Lines 38-41)
**Model:** `ProxmoxHost`
**Severity:** CRITICAL - Credential Exposure

**Code:**
```python
password = models.CharField(
    max_length=500,
    help_text='Encrypted password for Proxmox API'
)
```

**Issue:** Despite the comment saying "Encrypted", passwords are stored in PLAINTEXT in the database. Multiple TODOs confirm this:
- `/Users/fab/GitHub/proximity/backend/apps/proxmox/services.py:77` - `password=host.password,  # TODO: Decrypt password`
- `/Users/fab/GitHub/proximity/backend/apps/proxmox/api.py:37` - `# TODO: Encrypt password before saving`

**Root Cause:** No encryption implemented before database storage.

**Security Impact:** CRITICAL - Credential Exposure. If database is compromised, all Proxmox credentials are exposed in plaintext, giving attackers full access to infrastructure.

**Evidence from Code:**
```python
# In tasks.py line 195-197
import secrets
root_password = secrets.token_urlsafe(16)
logger.info(f"[{app_id}] 🔐 Generated root password (length: {len(root_password)})")
```
Also stored unencrypted:
```python
# Line 319
app.lxc_root_password = root_password  # TODO: Encrypt this
```

**Fix:** Implement field-level encryption:
```python
from django.contrib.auth.hashers import make_password, check_password
from cryptography.fernet import Fernet

class ProxmoxHost(models.Model):
    _password = models.CharField(max_length=500)
    
    @property
    def password(self):
        # Decrypt before return
        cipher = Fernet(settings.PASSWORD_CIPHER_KEY)
        return cipher.decrypt(self._password).decode()
    
    @password.setter
    def password(self, value):
        # Encrypt before storage
        cipher = Fernet(settings.PASSWORD_CIPHER_KEY)
        self._password = cipher.encrypt(value.encode())
```

---

### Issue #8: Plaintext Password in Logs
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/tasks.py` (Lines 195-198)
**Severity:** HIGH - Credential Exposure in Logs

**Code:**
```python
root_password = secrets.token_urlsafe(16)
logger.info(f"[{app_id}] 🔐 Generated root password (length: {len(root_password)})")
```

**Issue:** While the immediate log doesn't print the password, it's later passed to Proxmox service and logged at line 320 and stored unencrypted.

**Security Impact:** HIGH - Credentials in logs. Even though length is logged not the password itself, other logs may expose it. Root passwords should NEVER be logged.

**Root Passwords stored unencrypted:**
```python
# Line 319-321
app.lxc_root_password = root_password  # TODO: Encrypt this
app.updated_at = timezone.now()
app.save(update_fields=['status', 'lxc_root_password', 'updated_at'])
```

**Fix:** Implement encryption for stored passwords and never log passwords:
```python
import secrets
from cryptography.fernet import Fernet

root_password = secrets.token_urlsafe(16)
logger.info(f"[{app_id}] Root password generated")

# Encrypt before storing
cipher = Fernet(settings.PASSWORD_CIPHER_KEY)
encrypted_password = cipher.encrypt(root_password.encode())

app.lxc_root_password = encrypted_password
```

---

## HIGH SEVERITY ISSUES

### Issue #9: Race Condition in Application Creation - Hostname Uniqueness
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 128-129)
**Severity:** HIGH - Race Condition

**Code:**
```python
# Validate hostname is unique
if Application.objects.filter(hostname=payload.hostname).exists():
    raise HttpError(400, f"Hostname '{payload.hostname}' already exists")

# ... 10 lines of code ...

# Create application record
app = Application.objects.create(
    id=app_id,
    hostname=payload.hostname,  # NOT guaranteed to be unique!
    # ...
)
```

**Issue:** Check-then-act pattern without transaction protection. Between the `exists()` check and the `create()` call, another request could create an app with the same hostname.

**Root Cause:** No database-level transaction or constraint enforcement. Race condition window = 10+ lines of code.

**Concurrency Impact:** HIGH - Under load, duplicate hostnames could be created despite the check.

**Fix:** Use database constraint + exception handling:
```python
from django.db import IntegrityError

# At model level (models.py):
class Application(models.Model):
    hostname = models.CharField(max_length=255, unique=True, db_index=True)
    # ... This creates DB constraint

# In API:
try:
    with transaction.atomic():
        app = Application.objects.create(
            id=app_id,
            hostname=payload.hostname,
            # ... other fields
        )
except IntegrityError:
    raise HttpError(400, f"Hostname '{payload.hostname}' already exists")
```

---

### Issue #10: Race Condition in VMID Allocation
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/tasks.py` (Lines 154-185)
**Severity:** HIGH - Race Condition with Incomplete Fix

**Code:**
```python
for attempt in range(max_attempts):
    candidate_vmid = proxmox_service.get_next_vmid()

    # Check if this VMID is already in use in our database
    existing_app = Application.objects.filter(lxc_id=candidate_vmid).first()

    if not existing_app:
        # VMID is unique, use it
        vmid = candidate_vmid
        logger.info(f"[{app_id}] ✓ Allocated unique VMID: {vmid}")
        break
```

**Issue:** While the code does attempt conflict resolution, there's still a race condition:
1. Check: `existing_app = Application.objects.filter(lxc_id=candidate_vmid).first()`
2. Time gap
3. Another task allocates same VMID
4. Create: `app.lxc_id = vmid; app.save()`

The assignment at line 190-191 is AFTER the check but NOT in a transaction.

**Concurrency Impact:** HIGH - Two apps could get the same VMID in parallel deployments.

**Fix:** Use database unique constraint + atomic transaction:
```python
from django.db import IntegrityError

for attempt in range(max_attempts):
    candidate_vmid = proxmox_service.get_next_vmid()
    
    try:
        with transaction.atomic():
            # First, verify it's not already in DB under lock
            existing = Application.objects.select_for_update().filter(
                lxc_id=candidate_vmid
            ).first()
            
            if existing:
                continue  # Already used, try next
            
            # Assign now - this entire operation is atomic
            app.lxc_id = candidate_vmid
            app.save(update_fields=['lxc_id'])
            vmid = candidate_vmid
            break
    except IntegrityError:
        # Unique constraint violated - another process got this VMID
        continue
```

---

### Issue #11: Missing Port Release on Deployment Failure
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 211-250)
**Severity:** HIGH - Resource Leak

**Code:**
```python
# Allocate ports
port_manager = PortManagerService()
try:
    public_port, internal_port = port_manager.allocate_ports()
except ValueError as e:
    raise HttpError(500, str(e))

# Create application record
app = Application.objects.create(
    id=app_id,
    # ...
    public_port=public_port,
    internal_port=internal_port,
    # ...
)

# Trigger deployment task AFTER transaction commits
transaction.on_commit(
    lambda: deploy_app_task.delay(...)
)
```

**Issue:** If `deploy_app_task.delay()` fails to queue (Redis connection lost), ports are allocated but never released. If task later fails, no rollback releases the ports.

**Root Cause:** No try-finally block to release ports on error. No explicit error handling for task queueing.

**Resource Impact:** HIGH - Port exhaustion. Allocated ports leak on deployment failures.

**Fix:**
```python
port_manager = PortManagerService()
public_port = None
internal_port = None

try:
    public_port, internal_port = port_manager.allocate_ports()
    
    # Create application record
    app = Application.objects.create(
        id=app_id,
        public_port=public_port,
        internal_port=internal_port,
        # ...
    )
    
    # Trigger deployment task
    try:
        transaction.on_commit(
            lambda: deploy_app_task.delay(...)
        )
    except Exception as e:
        logger.error(f"Failed to queue deployment task: {e}")
        # Ports will be released by app deletion below
        raise
        
except Exception:
    # Release allocated ports on any error
    if public_port and internal_port:
        try:
            port_manager.release_ports(public_port, internal_port)
        except Exception as e:
            logger.error(f"Failed to release ports: {e}")
    raise
```

---

### Issue #12: Missing Error Handling in adopt_app_task
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/tasks.py` (Lines 1018-1039)
**Severity:** HIGH - Unhandled Exception

**Code:**
```python
container_config_snapshot = {}
try:
    # Get detailed configuration
    config_response = proxmox_service.proxmox.nodes(node_name).lxc(vmid).config.get()
    container_config_snapshot = dict(config_response)
    # ...
except Exception as config_error:
    logger.warning(f"[ADOPT {vmid}] ⚠️  Could not capture full config snapshot: {config_error}")
    # Continue with adoption even if config capture fails
    container_config_snapshot = {'error': str(config_error)}
```

**Issue:** The error is logged but silently ignored. If config capture fails, adoption continues with incomplete data. No way to know if important configuration was missed.

**Error Handling Impact:** HIGH - Silent failures. Task appears successful but with corrupted metadata.

**Fix:**
```python
try:
    config_response = proxmox_service.proxmox.nodes(node_name).lxc(vmid).config.get()
    container_config_snapshot = dict(config_response)
except Exception as config_error:
    logger.warning(f"[ADOPT {vmid}] Could not capture full config snapshot: {config_error}")
    logger.warning(f"[ADOPT {vmid}] This is non-critical but reduces adoption metadata completeness")
    container_config_snapshot = {'error': str(config_error), 'attempted': True}
    # Optionally: Track this in metrics for monitoring
```

---

### Issue #13: Task Retry Logic Issues
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/tasks.py` (Lines 345-373)
**Severity:** HIGH - Unreliable Error Recovery

**Code:**
```python
except Exception as e:
    logger.error(f"[TASK FAILED] Exception Type: {type(e).__name__}")
    # ...
    
    # Retry with exponential backoff
    retry_countdown = 60 * (2 ** self.request.retries)
    logger.error(f"[{app_id}] Scheduling retry in {retry_countdown} seconds...")
    raise self.retry(exc=e, countdown=retry_countdown)
```

**Issues:**
1. **Line 352:** `self.request.retries` might not exist if Celery isn't properly bound
2. **No max retries enforced** in try-except despite `max_retries=3` decorator. If error persists, it will retry forever if exception keeps being raised.
3. **Exponential backoff grows unbounded** - After 3 retries: 120s, 240s, 480s, then keeps doubling
4. **Status set to 'error' before retry** - May confuse users thinking app failed when it's retrying

**Retry Impact:** HIGH - Tasks could fail to recover gracefully or get stuck in retry loops.

**Fix:**
```python
@shared_task(bind=True, max_retries=3)
def deploy_app_task(self, app_id: str, ...):
    try:
        # ... main logic ...
    except Exception as e:
        logger.error(f"[TASK FAILED] Exception: {str(e)}")
        
        # Check if we've exhausted retries
        if self.request.retries >= self.max_retries:
            logger.error(f"[{app_id}] Max retries ({self.max_retries}) exhausted, marking as error")
            try:
                app = Application.objects.get(id=app_id)
                app.status = 'error'
                app.save(update_fields=['status'])
            except:
                pass
            # Don't retry - re-raise to let Celery log final failure
            raise
        
        # Still have retries remaining
        retry_countdown = 60 * (2 ** self.request.retries)
        logger.warning(f"[{app_id}] Retrying in {retry_countdown}s (attempt {self.request.retries + 1}/{self.max_retries})")
        
        # Status should be 'deploying' not 'error' during retries
        raise self.retry(exc=e, countdown=retry_countdown)
```

---

### Issue #14: Unvalidated Input in Port Configuration
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 214-216)
**Severity:** MEDIUM - Input Validation

**Code:**
```python
# Allocate ports
port_manager = PortManagerService()
try:
    public_port, internal_port = port_manager.allocate_ports()
except ValueError as e:
    raise HttpError(500, str(e))
```

**Issue:** `ApplicationCreate` payload never defines what values are valid for `internal_port`. If passed in config, no validation occurs.

**Validation Impact:** MEDIUM - Could allocate invalid ports (e.g., > 65535, < 1).

**Fix:** Add explicit validation in schema:
```python
from pydantic import BaseModel, validator

class ApplicationCreate(BaseModel):
    catalog_id: str
    hostname: str
    internal_port: Optional[int] = None
    
    @validator('internal_port')
    def validate_port(cls, v):
        if v is not None and (v < 1 or v > 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v
```

---

### Issue #15: No N+1 Query Prevention in List Endpoint
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 50-106)
**Severity:** MEDIUM - Query Optimization

**Code:**
```python
queryset = Application.objects.all()

if status:
    queryset = queryset.filter(status=status)

if search:
    queryset = queryset.filter(
        Q(name__icontains=search) | Q(hostname__icontains=search)
    )

# ...
apps = queryset[start:end]

# Build response with metrics
return {
    "apps": [{
        "host_id": app.host_id,  # May trigger query if not selected_related
        # ...
    } for app in apps],
```

**Issue:** No `select_related('host')` on the queryset. Each app iteration loads the host separately (N+1).

**Database Impact:** MEDIUM - For 20 apps per page, makes 21 queries instead of 1.

**Fix:**
```python
queryset = Application.objects.select_related('host', 'owner').all()
```

---

### Issue #16: No Isolation on Backup Operations
**File:** `/Users/fab/GitHub/proximity/backend/apps/backups/tasks.py` (Lines 171-177)
**Severity:** MEDIUM - Inconsistent State

**Code:**
```python
# Update statuses
with transaction.atomic():
    backup.status = 'restoring'
    backup.save()
    
    app.status = 'updating'
    app.save()
```

**Issue:** Two separate model saves in same transaction but no locking. Another request could load and modify app.status between these two saves.

**Concurrency Impact:** MEDIUM - State inconsistency possible if multiple restores attempted.

**Fix:**
```python
with transaction.atomic():
    backup = Backup.objects.select_for_update().get(id=backup_id)
    app = Application.objects.select_for_update().get(id=backup.application_id)
    
    backup.status = 'restoring'
    backup.save()
    
    app.status = 'updating'
    app.save()
```

---

## MEDIUM SEVERITY ISSUES

### Issue #17: Missing Input Validation on Hostname
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 128-129)
**Severity:** MEDIUM - Input Validation

**Issue:** `ApplicationCreate.hostname` has no validation for valid hostname format.

**Impact:** MEDIUM - Invalid hostnames could be stored, causing issues with DNS and container configuration.

**Fix:** Add hostname validator:
```python
import re

class ApplicationCreate(BaseModel):
    hostname: str
    
    @validator('hostname')
    def validate_hostname(cls, v):
        # RFC 1123 hostname validation
        if len(v) > 253:
            raise ValueError('Hostname too long (max 253 characters)')
        
        pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.?$'
        if not re.match(pattern, v):
            raise ValueError('Invalid hostname format')
        
        return v
```

---

### Issue #18: Missing Validation on Adoption Port
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/tasks.py` (Lines 1057-1065)
**Severity:** MEDIUM - Input Validation

**Code:**
```python
# Determine which port to expose
if port_to_expose:
    container_port = port_to_expose
    logger.info(f"[ADOPT {vmid}] 📌 Using user-specified port: {container_port}")
elif detected_ports:
    container_port = detected_ports[0]
else:
    # Default fallback - common HTTP port
    container_port = 80
```

**Issue:** `port_to_expose` parameter is never validated. Could be negative, > 65535, or invalid.

**Impact:** MEDIUM - Invalid port configurations created.

**Fix:** Validate port before use:
```python
if port_to_expose:
    if not (1 <= port_to_expose <= 65535):
        raise ValueError(f"Invalid port: {port_to_expose}. Must be 1-65535")
    container_port = port_to_expose
```

---

### Issue #19: Missing Validation on CIDR Input
**File:** `/Users/fab/GitHub/proximity/backend/apps/core/api.py` (Lines 129-144)
**Severity:** MEDIUM - Input Validation Already Exists But Incomplete

**Code:**
```python
try:
    # Validate subnet CIDR
    ipaddress.IPv4Network(payload.default_subnet, strict=False)
    
    # Validate gateway IP
    ipaddress.IPv4Address(payload.default_gateway)
    
    # Validate DNS servers
    ipaddress.ip_address(payload.default_dns_primary)
    if payload.default_dns_secondary:
        ipaddress.ip_address(payload.default_dns_secondary)
        
except ValueError as e:
    return 400, {"error": f"Invalid IP address or CIDR notation: {str(e)}"}
```

**Issue:** While validation exists, no check that gateway is actually in the subnet.

**Impact:** MEDIUM - Invalid network configurations possible (gateway not in subnet).

**Fix:**
```python
try:
    subnet = ipaddress.IPv4Network(payload.default_subnet, strict=False)
    gateway = ipaddress.IPv4Address(payload.default_gateway)
    
    # Validate gateway is in subnet
    if gateway not in subnet:
        return 400, {"error": f"Gateway {gateway} is not in subnet {subnet}"}
    
    ipaddress.ip_address(payload.default_dns_primary)
    if payload.default_dns_secondary:
        ipaddress.ip_address(payload.default_dns_secondary)
        
except ValueError as e:
    return 400, {"error": f"Invalid IP address or CIDR notation: {str(e)}"}
```

---

### Issue #20: Inconsistent Error Response Format
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 416-417)
**Severity:** MEDIUM - API Design

**Code:**
```python
else:
    return 400, {"error": f"Invalid action: {action}"}
```

**Issue:** Most errors use `HttpError()` but this one returns a tuple. Inconsistent with rest of API.

**API Impact:** MEDIUM - Clients must handle multiple error response formats.

**Fix:**
```python
else:
    raise HttpError(400, f"Invalid action: {action}")
```

---

### Issue #21: Missing Exception Details in API Responses
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 298-303)
**Severity:** MEDIUM - Error Handling

**Code:**
```python
except ProxmoxError as e:
    logger.error(f"Discovery failed: {e}")
    raise HttpError(500, f"Discovery failed: {str(e)}")
except Exception as e:
    logger.error(f"Unexpected error during discovery: {e}")
    raise HttpError(500, f"Unexpected error: {str(e)}")
```

**Issue:** In production, returning raw exception messages to clients leaks implementation details.

**Security Impact:** MEDIUM - Information disclosure.

**Fix:**
```python
except ProxmoxError as e:
    logger.error(f"Discovery failed: {e}", exc_info=True)
    raise HttpError(500, "Discovery failed. Contact administrator.")
except Exception as e:
    logger.exception(f"Unexpected error during discovery: {e}")
    raise HttpError(500, "An unexpected error occurred. Contact administrator.")
```

---

### Issue #22: Missing Null Check on Metrics
**File:** `/Users/fab/GitHub/proximity/backend/apps/proxmox/services.py` (Lines 574-579)
**Severity:** MEDIUM - Type Safety

**Code:**
```python
cpu_raw = status.get("cpu", 0.0)
cpus = status.get("cpus", 1)  # Number of CPU cores allocated
cpu_usage = (cpu_raw / cpus) if cpus > 0 else 0.0
```

**Issue:** `status.get("cpus")` could return None if key exists but value is None. Division by None would raise TypeError.

**Impact:** MEDIUM - Metrics calculation fails silently in edge cases.

**Fix:**
```python
cpu_raw = status.get("cpu", 0.0) or 0.0
cpus = status.get("cpus") or 1
cpu_usage = (cpu_raw / cpus) if cpus > 0 else 0.0
```

---

### Issue #23: No Timeout on SSH Commands
**File:** `/Users/fab/GitHub/proximity/backend/apps/proxmox/services.py` (Lines 293-300)
**Severity:** MEDIUM - Resource Management

**Code:**
```python
for cmd in commands:
    stdout, stderr, exit_code = self._execute_ssh_command(
        host=host.host,
        port=host.ssh_port,
        username=ssh_username,
        password=host.password,
        command=cmd,
        timeout=10
    )
```

**Issue:** Timeout of 10 seconds for SSH config modification. If SSH hangs, thread blocks for 10s. No retry logic on timeout.

**Resource Impact:** MEDIUM - Potential thread exhaustion under slow network conditions.

**Fix:** Implement proper timeout handling:
```python
try:
    stdout, stderr, exit_code = self._execute_ssh_command(
        host=host.host,
        port=host.ssh_port,
        username=ssh_username,
        password=host.password,
        command=cmd,
        timeout=10
    )
except socket.timeout:
    logger.warning(f"SSH command timed out on {host.host}")
    raise ProxmoxError(f"SSH timeout configuring LXC {vmid}")
```

---

### Issue #24: Missing Resource Cleanup on Snapshot Delete Failure
**File:** `/Users/fab/GitHub/proximity/backend/apps/proxmox/services.py` (Lines 518-530)
**Severity:** MEDIUM - Resource Cleanup

**Code:**
```python
finally:
    # Step 4/4: Guaranteed cleanup - delete temporary snapshot
    if snapshot_created:
        try:
            logger.info(f"[Step 4/4] Cleaning up temporary snapshot '{snapshot_name}'...")
            delete_task = self.delete_snapshot(node_name, source_vmid, snapshot_name)
            self.wait_for_task(node_name, delete_task, timeout=60)
        except Exception as cleanup_error:
            logger.critical(
                f"[Step 4/4] ✗ FAILED to delete temporary snapshot '{snapshot_name}': {cleanup_error}. "
                f"Manual cleanup required: 'pct delsnapshot {source_vmid} {snapshot_name}'"
            )
```

**Issue:** When snapshot cleanup fails, exception is logged but not raised. Cloning appears successful but leaves orphaned snapshot.

**Impact:** MEDIUM - Storage leaks. Orphaned snapshots consume disk space.

**Fix:** Consider failing the clone operation if snapshot cleanup fails (since it indicates serious problems):
```python
finally:
    if snapshot_created:
        try:
            logger.info(f"[Step 4/4] Cleaning up temporary snapshot '{snapshot_name}'...")
            delete_task = self.delete_snapshot(node_name, source_vmid, snapshot_name)
            self.wait_for_task(node_name, delete_task, timeout=60)
            logger.info(f"[Step 4/4] ✓ Snapshot cleaned up successfully")
        except Exception as cleanup_error:
            logger.error(f"[Step 4/4] FAILED to clean up snapshot '{snapshot_name}': {cleanup_error}")
            # Log critical alert for operations team
            logger.critical(f"MANUAL CLEANUP REQUIRED: pct delsnapshot {source_vmid} {snapshot_name}")
```

---

## LOW/INFO SEVERITY ISSUES

### Issue #25: Missing DELETE Authorization Check
**File:** `/Users/fab/GitHub/proximity/backend/apps/proxmox/api.py` (Lines 99-104)
**Severity:** MEDIUM - Authorization

**Code:**
```python
@router.delete("/hosts/{host_id}")
def delete_host(request, host_id: int):
    """Delete a Proxmox host configuration."""
    host = get_object_or_404(ProxmoxHost, id=host_id)
    host.delete()
    return {"success": True, "message": f"Host {host.name} deleted"}
```

**Issue:** No permission check. Any user can delete Proxmox host configurations.

**Impact:** MEDIUM - Administrative resource modification.

**Fix:**
```python
@router.delete("/hosts/{host_id}")
def delete_host(request, host_id: int):
    """Delete a Proxmox host configuration. Requires admin privileges."""
    if not request.auth or not request.auth.is_staff:
        raise HttpError(403, "Admin privileges required")
    
    host = get_object_or_404(ProxmoxHost, id=host_id)
    host.delete()
    return {"success": True, "message": f"Host {host.name} deleted"}
```

---

### Issue #26: Missing Authorization on Proxmox Endpoints
**File:** `/Users/fab/GitHub/proximity/backend/apps/proxmox/api.py` (Lines 34-58)
**Severity:** MEDIUM - Authorization

**Issue:** `create_host`, `update_host`, `sync_nodes`, and `test_host_connection` endpoints have no admin permission checks.

**Fix:** Add admin checks to all administrative endpoints:
```python
@router.post("/hosts", response=ProxmoxHostResponse)
def create_host(request, payload: ProxmoxHostCreate):
    """Create a new Proxmox host configuration. Requires admin privileges."""
    if not request.auth or not request.auth.is_staff:
        raise HttpError(403, "Admin privileges required")
    # ... rest of logic
```

---

### Issue #27: Bare Exception Handler
**File:** `/Users/fab/GitHub/proximity/backend/apps/proxmox/services.py` (Lines 374-375)
**Severity:** LOW - Error Handling

**Code:**
```python
except:
    pass  # Ignore errors if already stopped
```

**Issue:** Bare `except:` catches ALL exceptions including SystemExit, KeyboardInterrupt. Never use bare except.

**Impact:** LOW - Could hide serious errors like memory issues.

**Fix:**
```python
except Exception as e:
    logger.debug(f"Container may already be stopped: {e}")
```

---

### Issue #28: Missing Validation on Limit Parameter
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 473)
**Severity:** LOW - Input Validation

**Code:**
```python
def get_application_logs(request, app_id: str, limit: int = 50):
    """Get deployment logs for an application."""
    # No validation on limit parameter
    logs = DeploymentLog.objects.filter(application=app).order_by('-timestamp')[:limit]
```

**Issue:** `limit` parameter not validated. User could request `limit=999999` causing memory issues.

**Impact:** LOW - Potential DOS through excessive memory usage.

**Fix:**
```python
def get_application_logs(request, app_id: str, limit: int = 50):
    """Get deployment logs for an application."""
    # Validate limit
    if limit < 1 or limit > 1000:
        raise HttpError(400, "limit must be between 1 and 1000")
    
    logs = DeploymentLog.objects.filter(application=app).order_by('-timestamp')[:limit]
```

---

### Issue #29: Missing Validation on Page Parameters
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (Lines 29-31)
**Severity:** LOW - Input Validation

**Code:**
```python
def list_applications(
    request,
    page: int = 1,
    per_page: int = 20,
    # ...
):
    # No validation on page or per_page
    start = (page - 1) * per_page
```

**Issue:** No validation on `page` or `per_page`. User could request page=0 or per_page=99999.

**Impact:** LOW - Potential DOS or incorrect results.

**Fix:**
```python
def list_applications(
    request,
    page: int = 1,
    per_page: int = 20,
):
    if page < 1:
        raise HttpError(400, "page must be >= 1")
    if per_page < 1 or per_page > 100:
        raise HttpError(400, "per_page must be between 1 and 100")
```

---

### Issue #30: Missing API Response Validation
**File:** `/Users/fab/GitHub/proximity/backend/apps/proxmox/services.py` (Lines 183-184)
**Severity:** LOW - Type Safety

**Code:**
```python
containers = client.nodes(node_name).lxc.get()
return containers
```

**Issue:** No validation that returned value is actually a list. ProxmoxAPI could return None or unexpected structure.

**Impact:** LOW - Could cause issues in downstream code expecting a list.

**Fix:**
```python
containers = client.nodes(node_name).lxc.get()
if not isinstance(containers, list):
    logger.warning(f"Unexpected container response type: {type(containers)}")
    return []
return containers
```

---

### Issue #31: Hardcoded Test Password
**File:** `/Users/fab/GitHub/proximity/backend/apps/applications/tasks.py` (Line 120)
**Severity:** INFO - Code Quality

**Code:**
```python
app.lxc_root_password = 'test-password'
```

**Issue:** Hardcoded test password in test mode. Should use proper test data or mock.

**Impact:** INFO - Code quality issue.

**Fix:**
```python
# In test mode, generate realistic password
app.lxc_root_password = secrets.token_urlsafe(16)
```

---

## Summary Table

| # | Issue | File | Severity | Type |
|---|-------|------|----------|------|
| 1 | Missing auth on get_application | applications/api.py:365 | CRITICAL | Authorization |
| 2 | Missing auth on app_action | applications/api.py:389 | CRITICAL | Authorization |
| 3 | Missing auth on clone | applications/api.py:420 | CRITICAL | Authorization |
| 4 | Missing auth on logs | applications/api.py:472 | HIGH | Authorization |
| 5 | Missing admin check on reload_catalog | catalog/api.py:97 | CRITICAL | Authorization |
| 6 | Unvalidated request.auth in backups | backups/api.py:50 | HIGH | Authorization |
| 7 | Plaintext password storage | proxmox/models.py:38 | CRITICAL | Security |
| 8 | Password exposure in logs | applications/tasks.py:195 | HIGH | Security |
| 9 | Hostname race condition | applications/api.py:128 | HIGH | Concurrency |
| 10 | VMID allocation race | applications/tasks.py:154 | HIGH | Concurrency |
| 11 | Port leak on failure | applications/api.py:211 | HIGH | Resource Mgmt |
| 12 | Unhandled config error | applications/tasks.py:1018 | HIGH | Error Handling |
| 13 | Task retry issues | applications/tasks.py:345 | HIGH | Async/Tasks |
| 14 | Port validation missing | applications/api.py:214 | MEDIUM | Validation |
| 15 | N+1 queries | applications/api.py:50 | MEDIUM | Performance |
| 16 | No isolation on backup | backups/tasks.py:171 | MEDIUM | Concurrency |
| 17 | Hostname validation | applications/api.py:128 | MEDIUM | Validation |
| 18 | Port validation in adopt | applications/tasks.py:1057 | MEDIUM | Validation |
| 19 | CIDR validation incomplete | core/api.py:129 | MEDIUM | Validation |
| 20 | Inconsistent error format | applications/api.py:416 | MEDIUM | API Design |
| 21 | Error details leak | applications/api.py:298 | MEDIUM | Security |
| 22 | Null check on metrics | proxmox/services.py:574 | MEDIUM | Type Safety |
| 23 | No SSH timeout handling | proxmox/services.py:293 | MEDIUM | Resource Mgmt |
| 24 | Snapshot cleanup failure | proxmox/services.py:518 | MEDIUM | Resource Mgmt |
| 25 | Missing auth on delete_host | proxmox/api.py:99 | MEDIUM | Authorization |
| 26 | Missing auth on proxmox endpoints | proxmox/api.py:34 | MEDIUM | Authorization |
| 27 | Bare except clause | proxmox/services.py:374 | LOW | Error Handling |
| 28 | Limit parameter validation | applications/api.py:473 | LOW | Validation |
| 29 | Page/per_page validation | applications/api.py:29 | LOW | Validation |
| 30 | API response validation | proxmox/services.py:183 | LOW | Type Safety |
| 31 | Hardcoded test password | applications/tasks.py:120 | INFO | Code Quality |

---

## Recommended Fix Priority

### Phase 1 - CRITICAL (Immediate)
1. Issue #7 - Implement password encryption
2. Issue #1 - Add authorization to get_application
3. Issue #2 - Add authorization to app_action
4. Issue #3 - Add authorization to clone
5. Issue #5 - Add admin check to reload_catalog

### Phase 2 - HIGH (This Sprint)
6. Issue #9 - Fix hostname race condition with DB constraint
7. Issue #10 - Fix VMID allocation race with atomic transaction
8. Issue #11 - Add port cleanup on failure
9. Issue #8 - Remove password from storage/logs
10. Issue #13 - Fix task retry logic

### Phase 3 - MEDIUM (Next Sprint)
11. Issue #14-19 - Add comprehensive input validation
12. Issue #4, #6, #25, #26 - Add remaining authorization checks
13. Issue #16 - Add transaction isolation to backup ops
14. Issue #21 - Improve error response security

---

## Testing Recommendations

1. **Security Testing:**
   - Test cross-user app access without authorization
   - Test password encryption in database
   - Test admin-only endpoints from non-admin user

2. **Concurrency Testing:**
   - Parallel hostname creation with same value
   - Parallel VMID allocation
   - Race condition testing with load testing tools

3. **Input Validation Testing:**
   - Invalid hostnames, ports, CIDR ranges
   - SQL injection attempts
   - Boundary value testing

4. **Error Handling Testing:**
   - Deployment failures with cleanup verification
   - Task retry exhaustion
   - Resource leak detection

---

## Conclusion

The Proximity backend has **31 significant issues** that require attention:
- **5 CRITICAL** security/authorization issues
- **8 HIGH** concurrency/error handling issues
- **13 MEDIUM** validation/design issues
- **5 LOW/INFO** code quality issues

**Most Critical:** The complete lack of authorization checks on user-owned resources (applications, backups, logs) is a severe security gap that should be addressed immediately. Combined with plaintext password storage, these issues pose significant risks to system security and data protection.

All recommended fixes are provided with code examples and can be implemented incrementally starting with Phase 1 critical issues.
