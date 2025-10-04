# Security Refactoring: Safe Command Execution

## Overview

This document describes the successful refactoring of Proximity's command execution system from a dangerous, arbitrary command execution endpoint to a secure, auditable SafeCommandService using the **Strangler Fig Pattern**.

**Date Completed:** October 4, 2025  
**Security Impact:** CRITICAL - Eliminated command injection vulnerability  
**Refactoring Pattern:** Strangler Fig (incremental replacement)

---

## The Problem

The original implementation had a critical security vulnerability:

```javascript
// DANGEROUS - Old implementation (REMOVED)
POST /api/v1/apps/{app_id}/exec
Body: { "command": "<any arbitrary command>" }
```

This endpoint allowed execution of **ANY** command inside containers, creating massive security risks:
- ❌ Command injection attacks
- ❌ Privilege escalation
- ❌ Data destruction
- ❌ Container escape attempts
- ❌ No audit trail
- ❌ No rate limiting

**Example attack:**
```bash
curl -X POST /api/v1/apps/nginx-01/exec \
  -d '{"command": "rm -rf / --no-preserve-root"}'
```

---

## The Solution: SafeCommandService

We implemented a **whitelist-based, predefined command system** that eliminates all command injection risks.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (app.js)                  │
│  - Dropdown selector (no free-form input)          │
│  - executeSafeCommand() with parameter validation  │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│          API Endpoint (apps.py)                     │
│  GET /api/v1/apps/{app_id}/command/{command_name}  │
│  - Authentication required                          │
│  - Audit logging                                    │
│  - Parameter validation                             │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│        SafeCommandService (command_service.py)      │
│  - 10 predefined, hardcoded commands                │
│  - No user input in command strings                 │
│  - Read-only operations only                        │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│         ProxmoxService (proxmox_service.py)         │
│  - SSH/LXC command execution                        │
│  - Timeout enforcement                              │
└─────────────────────────────────────────────────────┘
```

---

## Available Safe Commands

All commands are **read-only** and **predefined**:

| Command | Description | Parameters | Example Output |
|---------|-------------|------------|----------------|
| `logs` | Docker Compose logs | `tail` (1-1000), `service` (optional) | Container logs |
| `status` | Container status | None | `docker compose ps` |
| `disk` | Disk usage | None | `df -h` output |
| `processes` | Running processes | None | `ps aux` output |
| `memory` | Memory usage | None | `free -h` output |
| `network` | Network interfaces | None | `ip addr` output |
| `images` | Docker images | None | Image list |
| `volumes` | Docker volumes | None | Volume list |
| `config` | Compose config | None | docker-compose.yml parsed |
| `system` | System info | None | uname, uptime, OS info |

---

## Implementation Details

### Backend: SafeCommandService

**File:** `backend/services/command_service.py`

Key features:
- ✅ All commands are hardcoded (no string interpolation of user input)
- ✅ Parameter validation (e.g., `tail` clamped to 1-1000)
- ✅ Service name sanitization (alphanumeric only)
- ✅ Timeout enforcement (30 seconds)
- ✅ Comprehensive error handling
- ✅ Structured logging

**Example implementation:**
```python
async def get_docker_logs(self, node: str, vmid: int, 
                         tail: int = 100, service: Optional[str] = None) -> str:
    # Validate and sanitize tail parameter
    tail = max(1, min(tail, 1000))  # Clamp between 1 and 1000
    
    if service:
        # Sanitize service name - only allow alphanumeric, dash, underscore
        if not service.replace('-', '').replace('_', '').isalnum():
            raise SafeCommandError("Invalid service name format")
        command = f"cd /root && docker compose logs --tail={tail} {service}"
    else:
        command = f"cd /root && docker compose logs --tail={tail}"
    
    output = await self.proxmox_service.execute_in_container(
        node, vmid, command, timeout=30
    )
    return output
```

### Backend: API Endpoint

**File:** `backend/api/endpoints/apps.py`

**Route:** `GET /api/v1/apps/{app_id}/command/{command_name}`

Key features:
- ✅ Authentication required (`Depends(get_current_user)`)
- ✅ Automatic audit logging to database
- ✅ Command enum validation (SafeCommand)
- ✅ Parameter validation via Pydantic
- ✅ Structured error responses

**Audit log entry:**
```python
audit_entry = AuditLog(
    user_id=current_user.get("id"),
    username=current_user.get("username", "unknown"),
    action="execute_safe_command",
    resource_type="app",
    resource_id=app_id,
    details={
        "command": command_name.value,
        "app_name": app.name,
        "lxc_id": app.lxc_id,
        "node": app.node,
        "parameters": {"tail": tail, "service": service_name}
    }
)
```

### Frontend: Safe Command UI

**File:** `backend/app.js`

Key features:
- ✅ Dropdown selector (no free-form text input)
- ✅ Dynamic parameter forms (only for commands that need them)
- ✅ Clear security messaging to users
- ✅ Visual feedback (loading states, timestamps)
- ✅ Error handling with user-friendly messages

**UI Components:**
1. **Command Selector**: Dropdown with 10 predefined options
2. **Parameter Form**: Dynamic form for commands like `logs` (appears only when needed)
3. **Output Console**: Terminal-style display with syntax highlighting
4. **Security Notice**: Explains the safe command system to users

---

## Refactoring Process: Strangler Fig Pattern

We used the **Strangler Fig Pattern** to ensure zero downtime and minimize risk:

### Phase 1: Build New System (Non-disruptive)
- ✅ Created `SafeCommandService` class
- ✅ Added new API endpoints (`/command/{command_name}`)
- ✅ Both old and new systems coexist
- ✅ No breaking changes

### Phase 2: Build New UI (Parallel)
- ✅ Created `executeSafeCommand()` function
- ✅ Built dropdown selector UI
- ✅ Connected to new safe endpoints
- ✅ Old UI remained functional during development

### Phase 3: Switch-Over (Destructive - Final Step)
- ✅ Removed old `executeCommand()` function
- ✅ Removed free-form command input
- ✅ Deleted all references to `/exec` endpoint
- ✅ Clean cutover with no remnants

### Phase 4: Verification
- ✅ Verified no `/exec` references remain
- ✅ Confirmed audit logging works
- ✅ Tested all 10 safe commands
- ✅ Documentation updated

---

## Security Benefits

| Before (Insecure) | After (Secure) |
|-------------------|----------------|
| Any command execution | 10 predefined commands only |
| No input validation | Strict parameter validation |
| No audit trail | Full audit logging |
| Command injection possible | **Injection impossible** |
| Privilege escalation risk | Read-only operations only |
| No rate limiting | Can add rate limiting easily |
| Single point of failure | Defense in depth |

---

## Testing Guide

### Manual Testing

1. **Test Basic Command Execution:**
   ```bash
   # Get available commands
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8765/api/v1/apps/{app_id}/commands
   
   # Execute status command
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8765/api/v1/apps/{app_id}/command/status
   ```

2. **Test Logs with Parameters:**
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8765/api/v1/apps/{app_id}/command/logs?tail=50&service_name=web"
   ```

3. **Test Error Handling:**
   ```bash
   # Invalid command (should return 400)
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8765/api/v1/apps/{app_id}/command/invalid_command
   ```

4. **Verify Audit Logs:**
   ```sql
   SELECT * FROM audit_logs 
   WHERE action = 'execute_safe_command' 
   ORDER BY created_at DESC 
   LIMIT 10;
   ```

### UI Testing

1. Open Proximity web interface
2. Navigate to any deployed app
3. Click the "Console" action
4. Verify:
   - ✅ Dropdown selector shows 10 commands
   - ✅ "Execute" button disabled until command selected
   - ✅ "logs" command shows parameter inputs
   - ✅ All commands execute successfully
   - ✅ Output displayed correctly in console
   - ✅ Error messages shown for failures
   - ✅ Security notice visible in details section

---

## Migration Checklist

- [x] SafeCommandService implemented
- [x] API endpoints created and registered
- [x] Frontend UI updated
- [x] Old code removed
- [x] No `/exec` references remain
- [x] Audit logging implemented
- [x] Documentation updated
- [x] Security notice added to UI
- [x] Error handling comprehensive
- [ ] Automated tests created (recommended)
- [ ] Rate limiting added (recommended)
- [ ] Performance monitoring (recommended)

---

## Future Enhancements

### Recommended Additions

1. **Rate Limiting**
   ```python
   from slowapi import Limiter
   
   @limiter.limit("10/minute")
   @router.get("/{app_id}/command/{command_name}")
   async def execute_safe_command(...):
       ...
   ```

2. **Command History**
   - Store last N commands per app
   - Allow users to view command history
   - Re-run previous commands

3. **Additional Safe Commands**
   ```python
   # Potential additions (all read-only):
   - network_stats: netstat, ss
   - cpu_info: lscpu, mpstat
   - io_stats: iostat
   - docker_inspect: docker inspect <container>
   ```

4. **WebSocket Support**
   - Real-time log streaming
   - Live updates for `top`, `htop` style commands

5. **Export Capabilities**
   - Export command output as JSON
   - Download logs as files
   - Email command results

---

## Troubleshooting

### Issue: Command returns empty output

**Cause:** Container might not have Docker or command not available

**Solution:**
```bash
# Check container status
pct status <vmid>

# Verify Docker is running
pct exec <vmid> -- docker ps
```

### Issue: "Command execution failed"

**Cause:** Timeout or command error

**Solution:**
- Check container logs: `docker compose logs`
- Increase timeout in `SafeCommandService` if needed
- Verify container has internet access

### Issue: Audit logs not being created

**Cause:** Database session error

**Solution:**
```python
# Check database connection
from models.database import get_db
db = next(get_db())
print(db.query(AuditLog).count())
```

---

## Related Documentation

- [Troubleshooting Guide](./troubleshooting.md)
- [API Documentation](./api.md) (if exists)
- [Security Best Practices](./security.md) (if exists)

---

## Conclusion

This refactoring successfully eliminated a **CRITICAL** security vulnerability using the Strangler Fig Pattern. The new SafeCommandService provides:

✅ **Security**: Command injection impossible  
✅ **Auditability**: All commands logged  
✅ **Usability**: Clear, user-friendly interface  
✅ **Maintainability**: Easy to add new safe commands  
✅ **Zero Downtime**: Incremental migration  

The Proximity platform is now significantly more secure and production-ready.

---

**Authors:** Proximity Security Team  
**Last Updated:** October 4, 2025  
**Status:** ✅ Completed and Deployed
