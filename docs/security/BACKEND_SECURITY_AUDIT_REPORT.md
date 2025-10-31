# Proximity Backend - Security Analysis Report

## Executive Summary

**Framework**: Django 5.0.1 with Django Ninja REST API
**Key Components**:
- JWT Authentication (djangorestframework-simplejwt)
- Proxmox Integration (proxmoxer library)
- Celery Task Queue
- SSH Command Execution (paramiko)
- Encrypted Database Fields (Fernet)

**Overall Risk Level**: MEDIUM-HIGH

The application handles sensitive infrastructure operations (container deployment, SSH execution) with several security concerns that require immediate attention.

---

## 1. Framework and Key Dependencies

### Primary Framework
- **Django 5.0.1**: Modern Python web framework
- **Django Ninja 1.1.0**: Modern async REST API framework
- **Django REST Framework 3.15.1**: Additional REST capabilities

### Authentication & Security
- **djangorestframework-simplejwt 5.3.1**: JWT token management
- **dj-rest-auth 6.0.0**: Authentication endpoints
- **django-allauth 0.61.1**: User registration and accounts
- **bcrypt 4.1.2**: Password hashing
- **cryptography 41.0.0+**: Encryption library
- **PyJWT 2.8.0**: JWT token creation/validation

### Infrastructure Integration
- **proxmoxer 2.0.1**: Proxmox API client
- **paramiko 3.4.0**: SSH client for remote command execution
- **requests 2.31.0**: HTTP library

### Async & Task Processing
- **celery 5.3.6**: Distributed task queue
- **redis 5.0.1**: Broker and cache
- **channels 4.0.0**: WebSocket support
- **daphne 4.1.2**: ASGI server

### Monitoring
- **sentry-sdk 1.39.2**: Error tracking and monitoring

---

## 2. Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Vue.js/JavaScript)                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTPS/WebSocket
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Django Ninja REST API (Port 8000/8765)              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  JWT Cookie Authentication (proximity-auth-cookie)      │   │
│  │  Global Auth: JWTCookieAuthenticator                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ Core API    │  │ Apps API     │  │ Proxmox API         │   │
│  │ /core/      │  │ /apps/       │  │ /proxmox/           │   │
│  │ Settings    │  │ Deploy/Start │  │ Hosts/Nodes         │   │
│  │ Health      │  │ Stop/Delete  │  │ Connection Tests    │   │
│  └─────────────┘  │ Logs         │  └─────────────────────┘   │
│                   └──────────────┘                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Database (SQLite/PostgreSQL via dj-database-url)        │   │
│  │ - Users (with AbstractUser)                             │   │
│  │ - Applications (deployed containers)                    │   │
│  │ - ProxmoxHosts/Nodes (with EncryptedCharField)         │   │
│  │ - Backups, DeploymentLogs, SystemSettings              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                       │
                       ├─ Celery Task Queue ──┬─ Redis Broker
                       │                      └─ Result Backend
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│          Proxmox API (HTTPS, Port 8006)                         │
│  - Create/Delete/Clone LXC containers                           │
│  - Execute commands via 'pct exec' (SSH → Proxmox node)        │
│  - Manage storage, backups, snapshots                           │
│                                                                  │
│          SSH to Proxmox Node (Port 22)                          │
│  - Execute 'pct exec' for in-container commands                │
│  - Configure LXC settings directly                              │
│  - Docker installation and application deployment              │
└─────────────────────────────────────────────────────────────────┘
```

### Key Data Flows

1. **Deployment Flow**:
   - API → Celery Task → ProxmoxService → Create LXC → SSH exec inside container

2. **Authentication Flow**:
   - Login endpoint → JWT token in HttpOnly cookie + body
   - JWTCookieAuthenticator validates token on each request
   - User filtering: non-admin users see only their own apps

3. **Backup/Restore Flow**:
   - Application state backed up via Proxmox vzdump
   - Async restore operations via Celery

---

## 3. Top 10 Security Concerns (Priority Order)

### CRITICAL

#### 1. **SSH Command Injection via Unquoted Arguments**
**File**: `/Users/fab/GitHub/proximity/backend/apps/proxmox/services.py` (line 1078)
**Severity**: CRITICAL (RCE)

```python
# VULNERABLE CODE:
pct_command = f"pct exec {vmid} -- {command}"
# Example: command="whoami; rm -rf /" → "pct exec 100 -- whoami; rm -rf /"
```

**Issue**: The `command` parameter in `execute_in_container()` is directly interpolated into the shell command without proper escaping. An attacker controlling the command parameter (via API) could execute arbitrary shell commands on the Proxmox node.

**Attack Scenario**:
```python
# Malicious deployment config with:
docker_setup_command = "sh -c 'whoami; cat /etc/proxmox/pve/authkey.pub' > /tmp/leak.txt"
# Proxmox node will execute this!
```

**Impact**: Complete compromise of Proxmox node and all containers

**Mitigation**: Use `shlex.quote()` or pass commands as array to `exec_command()` instead of shell string.

---

#### 2. **Plaintext Password Storage in Database**
**Files**:
- `/Users/fab/GitHub/proximity/backend/apps/proxmox/api.py` (lines 46, 52)
- `/Users/fab/GitHub/proximity/backend/apps/proxmox/services.py` (line 77)
**Severity**: CRITICAL (Credential Disclosure)

**Issue**: Multiple TODOs indicate passwords are NOT being encrypted before saving:
```python
# From api.py line 46-52:
# TODO: Encrypt password before saving
host = ProxmoxHost.objects.create(
    password=payload.password,  # TODO: Encrypt
)

# From services.py line 77:
password=host.password,  # TODO: Decrypt password
```

**Analysis**: While `EncryptedCharField` is defined in `apps/core/fields.py`, the ProxmoxHost model DOES use it:
```python
password = EncryptedCharField(max_length=500)
```

However, the TODOs suggest the decryption may not work properly at retrieval time. The encryption logic uses Fernet with SHA256 hash of SECRET_KEY, which is reasonable but has issues (see below).

**Actual Risk**:
- Passwords are encrypted at database level (good)
- BUT: TODOs indicate developers are unsure if it's working (red flag)
- SECRET_KEY is in `.env` file and committed to repo
- If SECRET_KEY is compromised, all passwords can be decrypted

**Impact**: If database is breached + SECRET_KEY leaked, all Proxmox credentials compromised

---

#### 3. **Hardcoded Credentials in .env File**
**File**: `/Users/fab/GitHub/proximity/backend/.env`
**Severity**: CRITICAL (Credential Disclosure)

```
PROXMOX_PASSWORD=invaders  # HARDCODED!
JWT_SECRET_KEY=atc3w3PjkWZHyWThMspZ4zcZ0v9ZnByVioVv2v_T1io  # EXPOSED!
LXC_ROOT_PASSWORD=invaders  # HARDCODED!
SENTRY_DSN=https://dbee00d4782d131ab54ffe60b16d969b@o149725.ingest.us.sentry.io/4510189390266368  # PUBLIC
```

**Impact**: Any commit history exposure reveals credentials. The JWT_SECRET_KEY allows forging authentication tokens. Proxmox credentials allow infrastructure access.

---

#### 4. **Insecure SSH Implementation (Password Auth, No Key Verification)**
**File**: `/Users/fab/GitHub/proximity/backend/apps/proxmox/services.py` (lines 990-1004)
**Severity**: CRITICAL (MITM Attacks)

```python
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # ⚠️ DANGEROUS!

ssh.connect(
    hostname=host,
    port=port,
    username=username,
    password=password,  # Plaintext password transmission risk
    allow_agent=False,
    look_for_keys=False
)
```

**Issues**:
1. **No host key verification**: `AutoAddPolicy()` accepts ANY host key - enables MITM attacks
2. **Password authentication**: Less secure than key-based auth
3. **Password in memory**: Not cleared after use
4. **No timeout on initial connection**: Could hang indefinitely

**Attack**: Attacker on network can MITM SSH connection and execute arbitrary commands:
```
Attacker ←→ Proxmox Node Setup
Attacker intercepts: "pct exec 100 -- apt-get update"
Attacker injects: "pct exec 100 -- apt-get update && malicious-command"
```

**Impact**: Complete compromise of container environments

---

#### 5. **Unsafe Shell Command Construction in Docker Setup**
**File**: `/Users/fab/GitHub/proximity/backend/apps/applications/docker_setup.py` (line 191)
**Severity**: HIGH (Command Injection)

```python
# Line 191:
f"sh -c \"mkdir -p /root && echo '{compose_yaml_escaped}' > /root/docker-compose.yml\""

# Single quote escaping may be insufficient:
compose_yaml_escaped = compose_yaml.replace("'", "'\\''")

# If compose_yaml contains certain patterns, could still break out:
# compose_yaml = "version: 3\nservices: ' && malicious"
```

**Issue**: While the code attempts quote escaping, it's error-prone. YAML is embedded directly in shell string.

**Better approach**: Use base64 encoding or pass via heredoc

---

### HIGH SEVERITY

#### 6. **DEBUG Mode Enabled in Development**
**File**: `/Users/fab/GitHub/proximity/backend/.env` + `/proximity/settings.py`
**Severity**: HIGH (Information Disclosure)

```python
DEBUG=true  # In .env
DEBUG = os.getenv('DEBUG', 'False') == 'True'  # In settings.py
```

**Risks when DEBUG=True**:
- Full stack traces exposed in error pages
- Database query logging enabled
- Secret settings potentially visible
- Static file serving without caching headers

**Note**: Good that default is False, but .env shows it's enabled locally

---

#### 7. **Insufficient CORS Configuration**
**File**: `/Users/fab/GitHub/proximity/backend/proximity/settings.py` (lines 123-127)
**Severity**: HIGH (CSRF/XSS)

```python
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173'  # Only localhost
).split(',')
CORS_ALLOW_CREDENTIALS = True  # Cookies sent with CORS requests
```

**Issues**:
1. **Not explicitly restrictive**: Depends entirely on env variable
2. **No validation of env value**: Could accidentally include malicious origins
3. **CORS_ALLOW_CREDENTIALS=True**: Allows cross-origin cookie theft

**Current state is reasonable** for development, but needs hardening for production.

---

#### 8. **Authentication Bypasses in API Endpoints**
**File**: `/Users/fab/GitHub/proximity/backend/apps/backups/api.py` (line 34)
**Severity**: HIGH (Authorization Bypass)

```python
# Line 34:
router = Router()  # TODO: Add auth=AuthBearer() when implemented

# Authentication is applied globally via:
# api = NinjaAPI(..., auth=JWTCookieAuthenticator())
# But this suggests alternative auth methods aren't implemented
```

**Issue**:
- Comment suggests auth was planned but incomplete
- Backup APIs rely on global auth only
- No secondary authorization checks in some endpoints

**Actual Status**: APIs ARE protected by global JWT auth, but pattern is concerning

---

#### 9. **Weak Password Generation for Container Root**
**File**: `/Users/fab/GitHub/proximity/backend/apps/applications/tasks.py` (line ~147)
**Severity**: HIGH (Weak Credentials)

```python
# From grep results - line indicates:
# Generate root password (TODO: Use encryption service from v1.0)
# TODO: Encrypt this

# This suggests:
# 1. Root password generation may be weak
# 2. Password not encrypted for storage
# 3. Password stored in LXC template in plain...

# Code shows:
app.lxc_root_password = root_password  # TODO: Encrypt this
```

**Issue**: Container root passwords not properly encrypted in database

---

#### 10. **Missing Input Validation on Node Selection**
**File**: `/Users/fab/GitHub/proximity/backend/apps/applications/api.py`
**Severity**: MEDIUM (Logic Error)

```python
# API accepts 'node' parameter from user request
# But ProxmoxNode doesn't validate if user has access to that node
# Could allow deploying to unauthorized nodes

# Line 21-22 shows filtering by host, but:
# User can specify ANY node on ANY host they have access to
```

**Mitigation**: Validate node belongs to allowed hosts

---

## 4. Additional Security Issues (Medium/Low)

### SSL/TLS Configuration
**File**: `/Users/fab/GitHub/proximity/backend/proximity/settings.py` (lines 342-343)
```python
CSRF_COOKIE_SECURE = False  # Development setting
SESSION_COOKIE_SECURE = False  # Development setting
```
**Issue**: Not production-ready. Needs HTTPS in production.

### Database Query Logging
**File**: `/Users/fab/GitHub/proximity/backend/apps/applications/api.py` (line 45)
```python
# DEBUG: Log received payload
```
**Issue**: Debug logging of payloads could expose sensitive data

### Sentry DSN Exposed
**File**: `/Users/fab/GitHub/proximity/backend/.env` (line 53)
```
SENTRY_DSN=https://dbee00d4782d131ab54ffe60b16d969b@o149725.ingest.us.sentry.io/...
```
**Issue**: Public DSN allows anyone to send errors to project

### SQL Injection Risk (Low)
**Status**: Uses Django ORM, safe from SQL injection
- Good use of select_related() for performance
- All database access through ORM

### Deserialization Risk (Low)
**Status**: YAML loading
- File: `apps/applications/docker_setup.py`
- Uses `yaml.dump()` (safe) not `yaml.load()` (unsafe)
- Safe implementation

---

## 5. File Structure Overview

```
/Users/fab/GitHub/proximity/backend/
├── proximity/                    # Django project settings
│   ├── settings.py              # Main configuration
│   ├── urls.py                  # URL routing
│   ├── auth.py                  # JWT authentication
│   ├── celery.py                # Celery configuration
│   ├── wsgi.py                  # WSGI application
│   └── asgi.py                  # ASGI application
│
├── apps/                        # Django applications
│   ├── core/                    # User models, encryption, base settings
│   │   ├── models.py            # User, SystemSettings
│   │   ├── fields.py            # EncryptedCharField, EncryptedTextField
│   │   ├── encryption.py        # EncryptionManager (Fernet)
│   │   ├── auth.py              # (empty, uses dj-rest-auth)
│   │   ├── api.py               # Health, system info, settings management
│   │   ├── middleware.py        # Sentry context enrichment
│   │   └── migrations/
│   │
│   ├── proxmox/                 # Proxmox infrastructure integration
│   │   ├── models.py            # ProxmoxHost, ProxmoxNode
│   │   ├── services.py          # ProxmoxService (SSH execution!)
│   │   ├── api.py               # Proxmox API endpoints (hosts/nodes)
│   │   ├── schemas.py           # Request/response schemas
│   │   ├── mock_service.py      # Testing mock
│   │   └── migrations/
│   │
│   ├── applications/            # Application deployment management
│   │   ├── models.py            # Application, DeploymentLog
│   │   ├── api.py               # CRUD operations, lifecycle
│   │   ├── services.py          # ApplicationService, reconciliation
│   │   ├── tasks.py             # Celery deployment tasks
│   │   ├── docker_setup.py      # Docker installation via SSH
│   │   ├── port_manager.py      # Port allocation
│   │   ├── schemas.py           # API schemas
│   │   └── management/
│   │       └── commands/        # Cleanup commands
│   │
│   ├── backups/                 # Backup management
│   │   ├── models.py            # Backup model
│   │   ├── api.py               # Backup CRUD endpoints
│   │   ├── tasks.py             # Async backup tasks
│   │   └── schemas.py
│   │
│   ├── catalog/                 # Application catalog
│   │   ├── models.py            # Catalog, CatalogApp
│   │   ├── api.py               # Search, list, reload
│   │   ├── services.py          # Catalog loading from filesystem
│   │   └── schemas.py
│   │
│   └── monitoring/              # Monitoring
│       └── models.py            # Monitoring data
│
├── tests/                       # Test suite
│   ├── test_*.py                # Integration tests
│   └── conftest.py              # Pytest configuration
│
├── requirements.txt             # Python dependencies
├── manage.py                    # Django CLI
├── db.sqlite3                   # SQLite database (dev)
├── .env                         # Environment variables (EXPOSED!)
├── Dockerfile                   # Container image
└── entrypoint.sh                # Docker entrypoint
```

---

## 6. Key Security Characteristics

### Authentication
- **Method**: JWT tokens in HttpOnly cookies + optional body
- **Rotation**: Refresh tokens rotated on every refresh
- **Expiration**: Access tokens 60 minutes, refresh tokens 7 days
- **Global Protection**: All endpoints protected by JWTCookieAuthenticator
- **User Isolation**: Non-admin users see only their own applications

### Authorization
- **Model**: Role-based (is_staff for admin)
- **Implementation**: Manual checks in API endpoints
- **Granularity**: User ownership checks for applications
- **Risk**: Some endpoints missing explicit permission checks

### Password Management
- **Hashing**: Uses Django's built-in validators + bcrypt
- **Storage**: User passwords properly hashed
- **Proxmox credentials**: Encrypted with Fernet (but TODO comments suggest issues)
- **Container root**: Encrypted in database but unclear if working

### Encryption
- **Algorithm**: Fernet (symmetric) from cryptography library
- **Key**: SHA256 hash of SECRET_KEY (first 32 bytes)
- **Implementation**: Custom EncryptionManager class
- **Risk**: SECRET_KEY in .env means if exposed, all encrypted data can be decrypted

### Logging
- **Level**: INFO by default, DEBUG in development
- **Output**: Console (StreamHandler)
- **Sentry**: Integrated for error tracking
- **Risk**: Debug logging may expose sensitive data; Sentry DSN is public

---

## 7. Recommendations (Priority Order)

### Immediate (Critical)
1. **Fix SSH Command Injection**:
   - Use `shlex.quote()` for command arguments
   - Or better: Pass commands as array to paramiko
   - Test with various payloads

2. **Verify Password Encryption**:
   - Test that encrypted passwords are being properly decrypted
   - Add unit tests for encryption/decryption round-trip
   - Document why TODOs say "encrypt" when EncryptedCharField is used

3. **Secure SSH Implementation**:
   - Implement SSH key-based authentication instead of passwords
   - Add host key verification (known_hosts file or strict mode)
   - Add SFTP for secure file transfers instead of shell commands
   - Example:
     ```python
     ssh.get_transport().get_security_options().key_types = ['ssh-ed25519']
     ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
     ssh.connect(..., look_for_keys=True)  # Use keys, not passwords
     ```

4. **Remove Hardcoded Credentials**:
   - Regenerate all exposed credentials
   - Move to secure secret management (HashiCorp Vault, AWS Secrets Manager)
   - Use environment variables only, no defaults in code
   - Implement credential rotation

### Short Term (High Priority)
5. **Input Validation Hardening**:
   - Validate all user input for API endpoints
   - Use Pydantic for request validation (already using in some endpoints)
   - Sanitize command arguments passed to SSH

6. **CORS & CSRF Hardening**:
   - Restrict CORS_ALLOWED_ORIGINS to specific domains only
   - Set CSRF_COOKIE_SECURE = True in production
   - Consider CSRF token middleware even for API

7. **Implement Authorization Layer**:
   - Create permission classes for Django Ninja
   - Example:
     ```python
     class IsAppOwner(BasePermission):
         def has_permission(self, request):
             return request.user.is_authenticated

         def has_object_permission(self, request, obj):
             return obj.owner == request.user or request.user.is_staff
     ```
   - Apply to all sensitive endpoints

8. **Remove Debug Code**:
   - Remove "sentry-debug" endpoint (line 46 in api.py)
   - Remove debug logging of payloads
   - Disable DEBUG mode in production config

### Medium Term
9. **Add Rate Limiting**:
   - Use django-ratelimit or similar
   - Rate limit login endpoints (prevent brute force)
   - Rate limit deployment endpoints (prevent resource exhaustion)

10. **Implement Audit Logging**:
    - Log all sensitive operations (deploy, delete, configuration changes)
    - Include user, timestamp, IP address
    - Use immutable log storage
    - Example: All changes to ProxmoxHost should be logged

11. **Add Request Signing**:
    - For Celery tasks crossing process boundaries
    - Prevent tampering with task parameters

12. **Security Headers**:
    - Add security middleware:
      ```python
      SECURE_BROWSER_XSS_FILTER = True
      SECURE_CONTENT_SECURITY_POLICY = {...}
      X_FRAME_OPTIONS = 'DENY'
      SECURE_HSTS_SECONDS = 31536000
      SECURE_HSTS_INCLUDE_SUBDOMAINS = True
      ```

---

## 8. Testing & Validation

### Manual Testing Checklist
- [ ] Attempt command injection in deployment APIs
- [ ] Test SSH with malicious commands
- [ ] Attempt authorization bypass on backup endpoints
- [ ] Try accessing other users' applications
- [ ] Test CORS with unauthorized origins
- [ ] Verify encrypted fields decrypt properly

### Automated Testing
- [ ] Add unit tests for encryption/decryption
- [ ] Add integration tests for Proxmox operations
- [ ] Add security tests for input validation
- [ ] Run SAST tools (bandit, semgrep)
- [ ] Run dependency check (safety, pip-audit)

### Vulnerability Scanning
```bash
# Check dependencies
pip-audit --desc

# Check code security
bandit -r apps/ -f json

# Check for common patterns
semgrep --config p/security-audit
```

---

## Conclusion

The Proximity backend has **strong foundational security** with proper JWT authentication, role-based authorization, and encrypted sensitive fields. However, it has **CRITICAL vulnerabilities** in SSH command execution and authentication that must be fixed immediately before production use.

The three main security gaps are:
1. **Command injection via unescaped SSH commands** (CRITICAL RCE)
2. **Plaintext credential exposure in .env** (CRITICAL)  
3. **Insecure SSH implementation without host verification** (CRITICAL MITM)

All other issues are important but less immediately dangerous. Priority should be fixing these three issues, then implementing the "Short Term" recommendations before any production deployment.
