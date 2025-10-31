# Backend Security Fixes - Implementation Roadmap

**Date**: 2025-10-30
**Total Issues**: 10 (3 CRITICAL, 4 HIGH, 3 MEDIUM)
**Estimated Effort**: 16-20 hours
**Priority**: Phase-based implementation

---

## PHASE 1: CRITICAL (Estimated: 4-5 hours)
**Must complete before production deployment**

### Issue #1: Fix SSH Command Injection Vulnerability

**File**: `backend/apps/proxmox/services.py`
**Lines**: 1078
**Impact**: Remote Code Execution on Proxmox nodes
**Effort**: 1.5 hours

**Current Code**:
```python
# Line 1078 - VULNERABLE:
pct_command = f"pct exec {vmid} -- {command}"
# Example attack: command="whoami; rm -rf /" → Complete system compromise
```

**Fixed Code - Option A (Use shlex.quote)**:
```python
import shlex

def execute_in_container(self, vmid: int, command: str) -> str:
    """Execute command safely in container"""
    # Validate vmid is integer
    vmid_int = int(vmid)

    # Quote the command to prevent shell injection
    safe_command = f"pct exec {vmid_int} -- {shlex.quote(command)}"
    # Result: "pct exec 100 -- 'whoami; rm -rf /'" - command runs as single string

    stdout, stderr, code = self.ssh_client.exec_command(safe_command)
    return stdout.read().decode()
```

**Fixed Code - Option B (Better: Pass as array)**:
```python
def execute_in_container(self, vmid: int, command: str) -> str:
    """Execute command safely in container - preferred method"""
    vmid_int = int(vmid)

    # Pass command as array - no shell interpretation
    cmd_array = ['pct', 'exec', str(vmid_int), '--'] + shlex.split(command)

    # Issue: paramiko exec_command takes string, not array
    # Solution: Convert back to safe string
    safe_cmd_str = ' '.join(shlex.quote(arg) for arg in cmd_array)

    stdout, stderr, code = self.ssh_client.exec_command(safe_cmd_str)
    return stdout.read().decode()
```

**Testing**:
```python
# Test cases in tests/test_proxmox_injection.py
def test_command_injection_blocked():
    service = ProxmoxService(...)

    # Attempt command injection
    result = service.execute_in_container(
        100,
        "whoami; cat /etc/passwd"
    )

    # Should execute as single command, not two separate ones
    assert "cat" not in result
    assert result.strip() in ["root", "nobody"]
```

---

### Issue #2: Remove Hardcoded Credentials from .env

**File**: `backend/.env`
**Impact**: Complete infrastructure compromise if exposed
**Effort**: 1 hour

**Current Issues**:
```env
PROXMOX_PASSWORD=invaders  # EXPOSED
JWT_SECRET_KEY=atc3w3PjkWZHyWThMspZ4zcZ0v9ZnByVioVv2v_T1io  # EXPOSED
LXC_ROOT_PASSWORD=invaders  # EXPOSED
SENTRY_DSN=https://...o149725.ingest.us.sentry.io/...  # PUBLIC
```

**Fix Step 1: Create .env.example (safe)**:
```bash
# .env.example - NO REAL CREDENTIALS
PROXMOX_HOST=proxmox.example.com
PROXMOX_PORT=8006
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=  # MUST be set in production
PROXMOX_VERIFY_SSL=true

JWT_SECRET_KEY=  # MUST be set - run: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_ALGORITHM=HS256

LXC_ROOT_PASSWORD=  # MUST be set during initial setup

SENTRY_DSN=  # Optional - set only in production

DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Fix Step 2: Regenerate all credentials**:
```bash
# Generate new secure credentials
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
# Output: JWT_SECRET_KEY=AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSs

# Generate strong Proxmox password (20+ chars, mixed case/numbers/symbols)
openssl rand -base64 20

# Update .env with new values
# PROXMOX_PASSWORD=<new_password_from_openssl>
# JWT_SECRET_KEY=<new_from_python>
# LXC_ROOT_PASSWORD=<new_password_from_openssl>
```

**Fix Step 3: Update Proxmox user password**:
```bash
# Login to Proxmox web UI and change root password to match .env
# Or use Proxmox API: POST /api2/json/access/password
```

**Fix Step 4: Update .gitignore**:
```bash
# .gitignore - ensure .env is excluded
.env
.env.local
.env.*.local
*.pem
*.key
secrets/
```

**Fix Step 5: Implement secure secret management (recommended)**:
```python
# For production, use environment-specific secret management:
# Option 1: AWS Secrets Manager
# Option 2: HashiCorp Vault
# Option 3: Azure Key Vault
# Option 4: Google Cloud Secret Manager

# Example using python-dotenv with validation:
from pydantic import BaseSettings

class Settings(BaseSettings):
    proxmox_password: str  # Will raise error if not set
    jwt_secret_key: str    # Will raise error if not set

    class Config:
        env_file = ".env"
        case_sensitive = False
        # In production, don't load from .env:
        # if not os.getenv("ENVIRONMENT") == "production":
        #     env_file = None
```

---

### Issue #3: Secure SSH Implementation

**File**: `backend/apps/proxmox/services.py`
**Lines**: 990-1004
**Impact**: Man-in-the-Middle attacks, session hijacking
**Effort**: 2-2.5 hours

**Current Code (VULNERABLE)**:
```python
# Lines 990-1004:
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # ⚠️ DANGEROUS!

ssh.connect(
    hostname=host,
    port=port,
    username=username,
    password=password,  # Plaintext password in memory
    allow_agent=False,
    look_for_keys=False
)
```

**Fixed Code - Phase 1 (Immediate)**:
```python
import paramiko
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ProxmoxService:
    def __init__(self, host: ProxmoxHost):
        self.host = host
        self._ssh_client = None

    def _get_ssh_client(self) -> paramiko.SSHClient:
        """Create SSH client with proper security"""
        ssh = paramiko.SSHClient()

        # 🔐 SECURITY: Load known hosts file
        ssh_key_path = os.path.expanduser('~/.ssh/known_hosts')
        try:
            ssh.load_system_host_keys()  # Load system known_hosts
            ssh.load_host_keys(ssh_key_path)  # Load user known_hosts
        except FileNotFoundError:
            logger.warning(f"Known hosts file not found at {ssh_key_path}")

        # ⚠️ TEMPORARY: Still use AutoAddPolicy in development
        # TODO: Replace with strict key verification in production
        if settings.DEBUG:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            # Production: Reject unknown hosts
            ssh.set_missing_host_key_policy(paramiko.RejectHostKeyPolicy())

        return ssh

    def _connect_ssh(self) -> paramiko.SSHClient:
        """Establish SSH connection"""
        ssh = self._get_ssh_client()

        # Set connection timeout
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                hostname=self.host.host,
                port=self.host.port,
                username=self.host.user,
                password=self.host.password,
                timeout=30,  # Connection timeout
                allow_agent=True,  # Allow SSH agent keys
                look_for_keys=True,  # Look for SSH keys
                auth_timeout=30,  # Auth timeout
                banner_timeout=30  # Banner timeout
            )
            logger.info(f"SSH connected to {self.host.host}")
            return ssh
        except paramiko.AuthenticationException as e:
            logger.error(f"SSH authentication failed for {self.host.host}: {e}")
            raise ValueError(f"SSH authentication failed: {str(e)}")
        except paramiko.SSHException as e:
            logger.error(f"SSH error connecting to {self.host.host}: {e}")
            raise ValueError(f"SSH connection failed: {str(e)}")
        finally:
            # Don't forget to clear password from memory (if possible)
            # Note: Password is still in paramiko's internal structures
            pass

    def execute_in_container(self, vmid: int, command: str) -> str:
        """Execute command safely in container"""
        import shlex

        # Validate vmid is integer
        try:
            vmid_int = int(vmid)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid vmid: {vmid}")

        # Validate command is string
        if not isinstance(command, str) or not command.strip():
            raise ValueError("Command cannot be empty")

        # Quote command to prevent shell injection
        safe_command = f"pct exec {vmid_int} -- {shlex.quote(command)}"

        logger.debug(f"Executing (safe): pct exec {vmid_int} -- [command]")

        ssh = self._connect_ssh()
        try:
            stdout, stderr, code = ssh.exec_command(safe_command)

            output = stdout.read().decode('utf-8', errors='replace').strip()
            errors = stderr.read().decode('utf-8', errors='replace').strip()

            if code != 0:
                logger.warning(f"Command exited with code {code}: {errors}")

            return output
        finally:
            ssh.close()

    def execute_raw_command(self, command: str) -> str:
        """Execute command on Proxmox host (use with caution!)"""
        import shlex

        # Validate command
        if not isinstance(command, str) or not command.strip():
            raise ValueError("Command cannot be empty")

        # Log for audit trail
        logger.warning(f"Executing raw command on {self.host.host}: [command]")

        ssh = self._connect_ssh()
        try:
            stdout, stderr, code = ssh.exec_command(command)
            output = stdout.read().decode('utf-8', errors='replace').strip()
            errors = stderr.read().decode('utf-8', errors='replace').strip()

            if code != 0:
                logger.error(f"Command failed: {errors}")

            return output
        finally:
            ssh.close()
```

**Phase 1 Production Setup**:
```bash
# On Proxmox server, create SSH key pair:
ssh-keygen -t ed25519 -f /root/.ssh/proximity_key -N ""

# Add public key to authorized_keys:
cat /root/.ssh/proximity_key.pub >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

# Copy private key to application server securely
scp root@proxmox:/root/.ssh/proximity_key ./secrets/proxmox_key

# Set correct permissions
chmod 600 ./secrets/proxmox_key

# Update settings to use key-based auth in next phase
```

---

### Issue #4: Verify & Fix Password Encryption

**File**: `backend/apps/proxmox/api.py` + `backend/apps/proxmox/services.py`
**Impact**: Plaintext credential exposure if encryption broken
**Effort**: 1 hour

**Current Code (UNCERTAIN)**:
```python
# api.py line 46-52:
# TODO: Encrypt password before saving
host = ProxmoxHost.objects.create(
    password=payload.password,  # Is this actually encrypted?
)

# services.py line 77:
password=host.password,  # Is this decrypted?
```

**Investigation & Fix**:
```python
# Test encryption in tests/test_encryption.py
import pytest
from apps.core.encryption import EncryptionManager
from apps.proxmox.models import ProxmoxHost

def test_password_encryption_roundtrip():
    """Verify password encryption/decryption works"""
    test_password = "test_proxmox_password_12345"

    # Create host with password
    host = ProxmoxHost.objects.create(
        name="Test Proxmox",
        host="proxmox.example.com",
        port=8006,
        user="root@pam",
        password=test_password,
        verify_ssl=True
    )

    # Retrieve and check
    retrieved = ProxmoxHost.objects.get(id=host.id)

    # The password field should be automatically decrypted by EncryptedCharField
    assert retrieved.password == test_password, \
        f"Decryption failed: expected '{test_password}' but got '{retrieved.password}'"

    print(f"✅ Password encryption/decryption works correctly")

# If test fails, check:
# 1. apps/core/fields.py EncryptedCharField implementation
# 2. apps/core/encryption.py EncryptionManager
# 3. Is the SECRET_KEY stable and consistent?

# Add this test and run: python manage.py test tests.test_encryption
```

**Update api.py to remove confusion**:
```python
# Remove TODO comments - encryption is already handled by EncryptedCharField
host = ProxmoxHost.objects.create(
    name=payload.name,
    host=payload.host,
    port=payload.port,
    user=payload.user,
    password=payload.password,  # Automatically encrypted by EncryptedCharField
    verify_ssl=payload.verify_ssl
)

# Add comment explaining automatic encryption
# Note: Password is automatically encrypted using EncryptedCharField
# (defined in apps/core/fields.py using Fernet encryption)
```

---

## PHASE 2: HIGH PRIORITY (Estimated: 4-5 hours)
**Fix after Phase 1**

### Issue #5: Harden CORS Configuration

**File**: `backend/proximity/settings.py`
**Lines**: 123-127
**Effort**: 30 minutes

**Current Code**:
```python
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173'
).split(',')
CORS_ALLOW_CREDENTIALS = True
```

**Fixed Code**:
```python
# Define allowed origins explicitly
ALLOWED_CORS_ORIGINS = {
    'development': [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:3000',
    ],
    'staging': [
        'https://staging.proximity.example.com',
    ],
    'production': [
        'https://proximity.example.com',
    ]
}

# Get environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Set CORS based on environment
CORS_ALLOWED_ORIGINS = ALLOWED_CORS_ORIGINS.get(ENVIRONMENT, [])

# Validate at startup
if not CORS_ALLOWED_ORIGINS:
    raise ValueError(f"No CORS origins configured for environment: {ENVIRONMENT}")

# Only allow credentials in development
CORS_ALLOW_CREDENTIALS = ENVIRONMENT == 'development'

# Additional CORS security
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-csrf-token',
]

# Restrict methods
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
]
```

**Update .env.example**:
```env
ENVIRONMENT=development  # Or: staging, production

# In production, these would be set by deployment system
CORS_ALLOWED_ORIGINS=https://proximity.example.com
```

---

### Issue #6: Implement Authorization Layer

**File**: `backend/proximity/auth.py` (create permission classes)
**Effort**: 1.5 hours

**Create Permission Classes**:
```python
# proximity/permissions.py (NEW FILE)
from django.contrib.auth.models import AnonymousUser
from ninja.security import HttpBearer
from typing import Optional

class IsAuthenticated:
    """Check if user is authenticated"""
    def has_permission(self, request) -> bool:
        return request.user and request.user.is_authenticated

class IsAdmin:
    """Check if user is admin/staff"""
    def has_permission(self, request) -> bool:
        return request.user and request.user.is_authenticated and request.user.is_staff

class IsAppOwner:
    """Check if user owns the application"""
    def has_object_permission(self, request, obj) -> bool:
        # obj should have an 'owner' or 'user' field
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user.is_staff
        elif hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        return False

class IsHostAdmin:
    """Check if user has access to Proxmox host"""
    def has_object_permission(self, request, obj) -> bool:
        # For ProxmoxHost - only admins can manage
        return request.user and request.user.is_staff
```

**Update API Endpoints to Use Permissions**:
```python
# apps/applications/api.py
from proximity.permissions import IsAppOwner, IsAuthenticated

@router.get("/apps/{app_id}")
def get_app(request, app_id: str):
    """Get application details"""
    try:
        app = Application.objects.get(id=app_id)
    except Application.DoesNotExist:
        return {"error": "Not found"}

    # Check permission
    if not (app.owner == request.user or request.user.is_staff):
        return {"error": "Permission denied"}, 403

    return app_to_schema(app)

@router.post("/apps/{app_id}/delete")
def delete_app(request, app_id: str):
    """Delete application"""
    try:
        app = Application.objects.get(id=app_id)
    except Application.DoesNotExist:
        return {"error": "Not found"}

    # Check permission
    if not (app.owner == request.user or request.user.is_staff):
        return {"error": "Permission denied"}, 403

    # Log the deletion
    logger.warning(f"User {request.user.username} deleting application {app_id}")

    app.delete()
    return {"success": True}
```

---

### Issue #7: Remove DEBUG Code & Set Proper Configuration

**File**: `backend/proximity/settings.py`
**Effort**: 1 hour

**Fix DEBUG Mode**:
```python
# settings.py
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Add validation
if DEBUG and os.getenv('ENVIRONMENT') == 'production':
    raise ValueError("DEBUG cannot be True in production")

# Configure debug toolbar only in development
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

**Remove Sentry Debug Endpoint**:
```python
# Remove this endpoint from apps/core/api.py
# @router.get("/sentry-debug")
# def sentry_debug(request):
#     """Debug endpoint - remove in production"""
#     raise Exception("Sentry test error")
```

**Add Security Headers**:
```python
# settings.py
# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "'unsafe-inline'"),  # Tighten if possible
    'style-src': ("'self'", "'unsafe-inline'"),
}

if not DEBUG:
    # Only enforce in production
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
```

---

### Issue #8: Strengthen Input Validation

**File**: Multiple API files
**Effort**: 1.5 hours

**Add Pydantic Validation Schemas**:
```python
# apps/applications/schemas.py (enhance existing)
from pydantic import BaseModel, Field, validator

class DeployAppSchema(BaseModel):
    catalog_id: str = Field(..., min_length=1, max_length=100)
    hostname: str = Field(..., min_length=1, max_length=63)
    config: dict = Field(default_factory=dict)
    node: str = Field(None, min_length=1, max_length=100)

    @validator('hostname')
    def validate_hostname(cls, v):
        import re
        if not re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', v):
            raise ValueError('Invalid hostname format')
        return v

    @validator('catalog_id')
    def validate_catalog_id(cls, v):
        # Ensure catalog_id exists
        from apps.catalog.models import CatalogApp
        if not CatalogApp.objects.filter(id=v).exists():
            raise ValueError('Invalid catalog_id')
        return v

# Use in API
@router.post("/apps/deploy")
def deploy_app(request, payload: DeployAppSchema):
    """Deploy application with validated input"""
    # payload is now validated and typed
    ...
```

---

## PHASE 3: MEDIUM PRIORITY (Estimated: 4-5 hours)
**Fix in next sprint**

### Issue #9: Add Rate Limiting

**File**: `backend/proximity/settings.py` + middleware
**Effort**: 1.5 hours

**Install django-ratelimit**:
```bash
pip install django-ratelimit
```

**Add Rate Limiting**:
```python
# proximity/settings.py
INSTALLED_APPS += ['django_ratelimit']

RATELIMIT_ENABLE = not DEBUG

# Cache backend for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

**Apply to Endpoints**:
```python
# apps/core/api.py
from django_ratelimit.decorators import ratelimit

@router.post("/auth/login")
@ratelimit(key='user_or_ip', rate='5/h', method='POST')
def login(request, payload: LoginSchema):
    """Login with rate limiting"""
    ...

# apps/applications/api.py
@router.post("/apps/deploy")
@ratelimit(key='user', rate='10/h', method='POST')
def deploy_app(request, payload: DeployAppSchema):
    """Deploy with rate limiting"""
    ...

@router.post("/apps/{app_id}/delete")
@ratelimit(key='user', rate='5/h', method='POST')
def delete_app(request, app_id: str):
    """Delete with rate limiting"""
    ...
```

---

### Issue #10: Implement Audit Logging

**File**: `backend/apps/core/audit.py` (NEW)
**Effort**: 2 hours

**Create Audit Logger**:
```python
# apps/core/audit.py
import json
import logging
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpRequest

logger = logging.getLogger('audit')

class AuditLogger:
    """Log sensitive operations for compliance"""

    @staticmethod
    def log_action(
        user: User,
        action: str,
        resource: str,
        resource_id: str,
        details: dict = None,
        request: HttpRequest = None
    ):
        """Log a sensitive operation"""

        audit_entry = {
            'timestamp': timezone.now().isoformat(),
            'user': user.username if user else 'anonymous',
            'action': action,
            'resource': resource,
            'resource_id': resource_id,
            'ip_address': get_client_ip(request) if request else None,
            'details': details or {}
        }

        logger.info(json.dumps(audit_entry))

def get_client_ip(request):
    """Get client IP from request"""
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    return None

# Configure audit logging in settings.py:
# LOGGING = {
#     'loggers': {
#         'audit': {
#             'handlers': ['audit_file', 'sentry'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#     },
#     'handlers': {
#         'audit_file': {
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': 'logs/audit.log',
#             'maxBytes': 10485760,  # 10MB
#             'backupCount': 10,
#         },
#     },
# }
```

**Use in APIs**:
```python
# apps/applications/api.py
from apps.core.audit import AuditLogger

@router.post("/apps/deploy")
def deploy_app(request, payload: DeployAppSchema):
    """Deploy application"""
    app = Application.objects.create(...)

    # Log the action
    AuditLogger.log_action(
        user=request.user,
        action='CREATE',
        resource='Application',
        resource_id=app.id,
        details={
            'catalog_id': payload.catalog_id,
            'hostname': payload.hostname,
        },
        request=request
    )

    return app

@router.post("/apps/{app_id}/delete")
def delete_app(request, app_id: str):
    """Delete application"""
    app = Application.objects.get(id=app_id)

    # Log the action BEFORE deletion
    AuditLogger.log_action(
        user=request.user,
        action='DELETE',
        resource='Application',
        resource_id=app_id,
        details={'hostname': app.hostname},
        request=request
    )

    app.delete()
    return {"success": True}
```

---

## PHASE 4: NICE TO HAVE (Estimated: 2-3 hours)

### Additional Security Improvements

1. **Request Signing for Celery Tasks** (1 hour)
   - Add `task_serializer='json'` + `accept_content=['json']`
   - Prevents task parameter tampering

2. **Implement Webhook Signatures** (1 hour)
   - For any external integrations
   - HMAC-SHA256 signing of payloads

3. **Add Security.txt** (30 minutes)
   - Standard way to report vulnerabilities
   - File: `static/.well-known/security.txt`

4. **Dependency Security Scanning** (30 minutes)
   - Add `pip-audit` to CI/CD
   - Run `bandit` for code analysis
   - Add `safety` for dependency checking

---

## 📊 SUMMARY TABLE

| Phase | Issues | Effort | Priority |
|-------|--------|--------|----------|
| Phase 1 | #1, #2, #3, #4 | 4-5 hrs | CRITICAL |
| Phase 2 | #5, #6, #7, #8 | 4-5 hrs | HIGH |
| Phase 3 | #9, #10 | 4-5 hrs | MEDIUM |
| Phase 4 | Additional | 2-3 hrs | LOW |
| **TOTAL** | **10** | **16-20 hrs** | |

---

## 🎯 BEFORE PRODUCTION

**Minimum Requirements**:
- Complete Phase 1 (4-5 hours) - Fix critical vulnerabilities
- Complete Phase 2 (4-5 hours) - Harden authorization and configuration
- **Total: 8-10 hours minimum**

**Recommended**:
- Complete Phases 1-3 (12-15 hours)
- Run security scanning tools
- Penetration testing

---

## 🧪 TESTING CHECKLIST

### Phase 1 Testing
- [ ] Command injection attempts are blocked (test with special chars)
- [ ] SSH connection succeeds with new credentials
- [ ] Password encryption roundtrip works
- [ ] Credentials removed from Git history

### Phase 2 Testing
- [ ] CORS only accepts configured origins
- [ ] Authorization checks prevent unauthorized access
- [ ] Debug endpoint is removed
- [ ] Input validation rejects malformed requests

### Phase 3 Testing
- [ ] Rate limiting blocks excessive requests
- [ ] Audit logs are being written correctly
- [ ] Sensitive operations are logged

### Phase 4 Testing
- [ ] Security scanning finds no critical issues
- [ ] Dependency check passes
- [ ] Webhook signatures validate correctly

---

## 🔧 QUICK START COMMANDS

```bash
# Phase 1: Fix critical vulnerabilities
python manage.py test tests.test_encryption  # Verify encryption
python manage.py test tests.test_proxmox_injection  # Test command injection fix

# Phase 2: Check authorization
python manage.py test apps.applications.tests.test_permissions

# Phase 3: Security scanning
pip install bandit safety pip-audit
bandit -r apps/ -f json -o bandit-report.json
safety check --json
pip-audit --desc --format json

# Before production
python manage.py check --deploy
```

---

**Status**: ✅ Ready for Implementation
**Next Step**: Start Phase 1 fixes
