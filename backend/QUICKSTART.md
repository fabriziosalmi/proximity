# 🚀 PROXIMITY - PHASE 1 QUICK START

**Last Updated**: October 4, 2025
**Status**: Phase 1 Security Hardening Complete ✅

---

## ⚡ Quick Setup (5 Minutes)

### Step 1: Install Dependencies
```bash
cd /Users/fab/GitHub/proximity/backend
pip install -r requirements.txt
```

### Step 2: Initialize Database & Create Admin User
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from models.database import init_db, SessionLocal, User

# Initialize database
init_db()
print("✅ Database initialized")

# Create admin user
db = SessionLocal()
admin = User(
    username="admin",
    email="admin@proximity.local",
    hashed_password=User.hash_password("proximity"),  # Change this!
    role="admin"
)
db.add(admin)
db.commit()
print("✅ Admin user created (username: admin, password: proximity)")
print("⚠️  IMPORTANT: Change password after first login!")
db.close()
EOF
```

### Step 3: Start Server
```bash
uvicorn main:app --reload --port 8765
```

### Step 4: Login & Get Token
```bash
# Login
curl -X POST http://localhost:8765/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"proximity"}'

# Copy the "access_token" from response
export TOKEN="<paste-token-here>"
```

### Step 5: Test Protected Endpoint
```bash
# This should work WITH token
curl http://localhost:8765/api/v1/apps/ \
  -H "Authorization: Bearer $TOKEN"

# This should FAIL without token
curl http://localhost:8765/api/v1/apps/
# → 401 Unauthorized ✅
```

---

## 🔐 Change Default Password (CRITICAL!)

```bash
curl -X POST http://localhost:8765/api/v1/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "old_password": "proximity",
    "new_password": "YourSecurePassword123!"
  }'
```

---

## ✅ Verify Security

### Test 1: Authentication Required
```bash
# Should fail without token
curl http://localhost:8765/api/v1/apps/
# Expected: {"success":false,"error":"Authentication required"}
```

### Test 2: Command Injection Blocked
```bash
# Should reject dangerous commands
curl -X POST http://localhost:8765/api/v1/apps/test/exec \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"command":"ls && rm -rf /"}'
# Expected: 400 Bad Request - "Command contains dangerous pattern"
```

### Test 3: Password Security
```bash
# Check passwords are hashed
sqlite3 proximity.db "SELECT username, substr(hashed_password,1,10) FROM users;"
# Expected: admin|$2b$12$... (bcrypt hash, not plaintext)
```

---

## 📊 What's Protected Now

| Endpoint | Method | Protected | Description |
|----------|--------|-----------|-------------|
| `/api/v1/auth/login` | POST | ❌ No | Login (public) |
| `/api/v1/auth/register` | POST | ❌ No | Register (public) |
| `/api/v1/apps/*` | ALL | ✅ Yes | All app operations |
| `/api/v1/system/*` | ALL | ✅ Yes | System info |
| `/health` | GET | ❌ No | Health check |
| `/` | GET | ❌ No | UI |

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install python-jose[cryptography] passlib[bcrypt] email-validator sqlalchemy
```

### Server won't start
```bash
# Check if port 8765 is already in use
lsof -i :8765
# If yes, kill it or use different port
uvicorn main:app --reload --port 8766
```

### "Database is locked"
```bash
rm proximity.db
# Re-run Step 2 to recreate database
```

---

## 📚 Next Steps

1. **Run Full Tests**: See `PHASE1_TESTING.md`
2. **Review Summary**: See `PHASE1_SUMMARY.md`
3. **Continue Phase 1**:
   - Day 4: Implement SafeCommandService
   - Day 5: Migrate to SQLite
   - Week 2: Integration testing

---

## 🎯 Current Status

**✅ Completed**:
- JWT authentication on all routes
- Command injection vulnerability fixed
- Password hashing with bcrypt
- Audit logging system
- Database schema created

**⏳ Remaining (Phase 1)**:
- Safe command service (replaces /exec)
- Full SQLite migration (apps.json → database)
- Integration testing

**🚀 Ready for**: Controlled beta testing with trusted users

---

**Need help?** Check the full testing guide in `PHASE1_TESTING.md`
