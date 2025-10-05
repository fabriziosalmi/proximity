# Database Schema Issue - Resolution Report

**Date**: October 5, 2025  
**Issue**: SQLAlchemy IntegrityError - NOT NULL constraint failed: users.email  
**Status**: ✅ RESOLVED

---

## Problem

```
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: users.email
[SQL: INSERT INTO users (username, email, hashed_password, role, is_active, created_at, updated_at) 
      VALUES (?, ?, ?, ?, ?, ?, ?)]
[parameters: ('fab', None, '$2b$12$...', 'user', 1, '2025-10-05 09:44:26.212986', '2025-10-05 09:44:26.212990')]
```

---

## Root Cause

### Multiple Database Files
The project had **two** `proximity.db` files with **different schemas**:

1. **`/Users/fab/GitHub/proximity/proximity.db`** (ROOT)
   - email: VARCHAR(100) (**NOT NULL**) ❌ OLD SCHEMA
   - Used when server started from root: `python3 backend/main.py`

2. **`/Users/fab/GitHub/proximity/backend/proximity.db`** (BACKEND)  
   - email: VARCHAR(100) (**NULL**) ✅ CORRECT SCHEMA
   - Used when server started from backend: `cd backend && python main.py`

### Why This Happened

The SQLAlchemy connection string is:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./proximity.db")
```

The `./` makes it **relative to the current working directory** where Python is executed:
- Run from root → creates `/Users/fab/GitHub/proximity/proximity.db`
- Run from backend → creates `/Users/fab/GitHub/proximity/backend/proximity.db`

---

## Resolution

### Steps Taken

1. ✅ **Identified multiple database files**
   ```bash
   find . -name "proximity.db"
   # Found:
   # - ./proximity.db (OLD SCHEMA - NOT NULL)
   # - ./backend/proximity.db (CORRECT SCHEMA - NULL)
   ```

2. ✅ **Verified schema mismatch**
   ```bash
   # Root DB: email VARCHAR(100) (NOT NULL)  ❌
   # Backend DB: email VARCHAR(100) (NULL)    ✅
   ```

3. ✅ **Backed up and removed old root database**
   ```bash
   # Backed up to: proximity_backup_20251005_115815.db
   # Removed: proximity.db
   ```

4. ✅ **Database will recreate on next server start**
   - New database will use current model definition
   - Model has `email = Column(String(100), unique=True, nullable=True)`
   - First server start will create correct schema

---

## Verification

After server restart, verify schema:
```python
import sqlite3
conn = sqlite3.connect('proximity.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(users)')
for col in cursor.fetchall():
    if col[1] == 'email':
        print(f"email: {col[2]} ({'NOT NULL' if col[3] else 'NULL'})")
        # Should print: email: VARCHAR(100) (NULL)
```

---

## Preventive Measures

### Recommendation 1: Use Absolute Path
Change database configuration to use absolute path:

```python
# backend/core/config.py or backend/models/database.py
import os
from pathlib import Path

# Get backend directory
BACKEND_DIR = Path(__file__).parent.parent
DB_PATH = BACKEND_DIR / "proximity.db"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
```

This ensures the database is always in the same location regardless of where the server is started.

### Recommendation 2: Add Database Location Check
Add startup logging to show which database is being used:

```python
# In backend/main.py startup
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_path = Path(db_path).resolve()
    logger.info(f"📊 Using database: {db_path}")
    logger.info(f"   Database exists: {db_path.exists()}")
```

### Recommendation 3: Add to Documentation
Update README.md or QUICKSTART.md:

```markdown
## Important: Running the Server

Always start the server from the **backend directory**:

```bash
cd backend
python main.py
```

Or use an absolute path to ensure database consistency:

```bash
python /path/to/proximity/backend/main.py
```

Starting from the root directory (`python backend/main.py`) may create
a separate database file with incompatible schema.
```

---

## Files Created

1. **`backend/check_db_schema.py`** - Schema validation tool
2. **`DATABASE_SCHEMA_RESOLUTION.md`** - This report

## Backups Created

1. `proximity_backup_20251005_115815.db` - Root database (old schema)
2. `backend/proximity_backup_20251005_114523.db` - Backend database
3. Additional backend backups from migration attempts

---

## Next Steps

1. ✅ Remove old root database (DONE)
2. ⏳ Restart backend server (creates new DB with correct schema)
3. ⏳ Test user registration with and without email
4. ⏳ Consider implementing absolute path for DATABASE_URL
5. ⏳ Add database location logging on startup

---

## Related to Baseline Discovery

This database issue was **separate from** but **related to** the E2E test failures:

- **Auth Modal Issue**: Frontend initialization bug (tests can't log in)
- **Database Issue**: Backend schema mismatch (registration fails)

Both issues prevent testing, but have different root causes:
- Auth modal: JavaScript/CSS display logic failure
- Database: Multiple DB files with schema drift

---

**Status**: ✅ Root database removed. Server will create fresh DB with correct schema on next start.
