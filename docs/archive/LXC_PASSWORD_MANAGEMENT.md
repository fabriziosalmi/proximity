# LXC Container Password Management

## Overview

Proximity now supports configurable and secure password management for LXC containers. Instead of using hardcoded passwords, you can:

- Set a custom default password via environment variables
- Enable automatic random password generation for each container
- Store passwords securely using encryption
- Retrieve passwords when needed for container access

## Configuration

Add these settings to your `.env` file:

```bash
# Default root password for LXC containers
LXC_ROOT_PASSWORD=invaders

# Enable random password generation (recommended for production)
LXC_PASSWORD_RANDOM=false

# Length of randomly generated passwords
LXC_PASSWORD_LENGTH=16
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `LXC_ROOT_PASSWORD` | `invaders` | Default password for container root user |
| `LXC_PASSWORD_RANDOM` | `false` | Generate a unique random password for each container |
| `LXC_PASSWORD_LENGTH` | `16` | Length of randomly generated passwords |

## Security Features

### Password Generation

When `LXC_PASSWORD_RANDOM=true`:
- Uses Python's `secrets` module for cryptographically secure random generation
- Passwords include: uppercase, lowercase, digits, and safe special characters
- Special characters are shell-safe: `!@#$%^&*-_=+`
- Each container gets a unique password

### Password Encryption

All passwords are encrypted before storage:
- Uses Fernet encryption (symmetric encryption from `cryptography` library)
- Encryption key derived from `JWT_SECRET_KEY`
- Each encryption includes a timestamp and nonce for uniqueness
- Stored in database in encrypted form only

### Password Storage

Passwords are stored in the `apps` table:
```sql
lxc_root_password VARCHAR(500) NULL
```

The column is nullable to maintain backward compatibility with existing deployments.

## Usage Examples

### Example 1: Using Default Password

```bash
# .env
LXC_ROOT_PASSWORD=my-secure-password-123
LXC_PASSWORD_RANDOM=false
```

All containers will use `my-secure-password-123` as the root password.

### Example 2: Random Passwords (Recommended)

```bash
# .env
LXC_PASSWORD_RANDOM=true
LXC_PASSWORD_LENGTH=24
```

Each container gets a unique 24-character random password.

### Example 3: Development Setup

```bash
# .env
LXC_ROOT_PASSWORD=devpass
LXC_PASSWORD_RANDOM=false
```

Simple password for easy access during development.

## Retrieving Passwords

### Via Database Query

```python
from models.database import App as DBApp
from core.security import decrypt_password

# Get app from database
app = db.query(DBApp).filter(DBApp.id == app_id).first()

# Decrypt password
if app.lxc_root_password:
    password = decrypt_password(app.lxc_root_password)
    print(f"Container root password: {password}")
```

### Via API (Future Enhancement)

A dedicated API endpoint could be added to retrieve passwords securely:
```
GET /api/v1/apps/{app_id}/credentials
```

## Migration

The database migration adds the `lxc_root_password` column:

```bash
# Run migration
python backend/migrations/add_lxc_password_column.py

# Verify migration
sqlite3 backend/proximity.db "PRAGMA table_info(apps);" | grep lxc_root_password
```

### Migration Details

- **Created**: 2025-10-09
- **File**: `backend/migrations/add_lxc_password_column.py`
- **Changes**: Adds `lxc_root_password VARCHAR(500)` column to `apps` table
- **Backward Compatible**: Column is nullable, existing deployments not affected

## Implementation Details

### Files Modified

1. **backend/core/config.py**
   - Added `LXC_ROOT_PASSWORD`, `LXC_PASSWORD_RANDOM`, `LXC_PASSWORD_LENGTH` settings

2. **backend/core/security.py** (NEW)
   - `generate_secure_password()` - General password generation
   - `generate_lxc_password()` - LXC-safe password generation
   - `encrypt_password()` - Encrypt passwords for storage
   - `decrypt_password()` - Decrypt passwords from storage
   - `get_encryption_key()` - Key derivation from JWT_SECRET_KEY

3. **backend/models/database.py**
   - Added `lxc_root_password` column to `App` model

4. **backend/services/proxmox_service.py**
   - Updated `create_lxc()` to accept optional `root_password` parameter
   - Implements password selection logic (provided → random → default)
   - Returns password in result dict for storage

5. **backend/services/app_service.py**
   - Imports `encrypt_password` from `core.security`
   - Encrypts password from `create_lxc()` result
   - Stores encrypted password in database

### Password Flow

```
1. User triggers deployment
   ↓
2. app_service.deploy_app()
   ↓
3. proxmox_service.create_lxc()
   ├─ No password provided?
   │  ├─ LXC_PASSWORD_RANDOM = true? → Generate random
   │  └─ LXC_PASSWORD_RANDOM = false? → Use LXC_ROOT_PASSWORD
   └─ Returns: {task_id, vmid, node, hostname, root_password}
   ↓
4. app_service encrypts password
   ↓
5. Stores in database (apps.lxc_root_password)
   ↓
6. Password available for retrieval when needed
```

## Testing

Comprehensive test suites verify functionality:

### Password Security Tests
```bash
python backend/tests/test_password_security.py
```

Tests:
- Password generation with various lengths
- Character set validation
- Encryption/decryption round-trip
- Configuration loading

### Integration Tests
```bash
python backend/tests/test_password_integration.py
```

Tests:
- Default password flow
- Custom password flow
- Random password generation flow
- Multiple containers with unique passwords
- Configuration settings

## Backward Compatibility

This feature maintains full backward compatibility:

1. **Existing Deployments**: Not affected (column is nullable)
2. **Default Behavior**: Uses `invaders` password if not configured
3. **Opt-In Random**: Must explicitly enable `LXC_PASSWORD_RANDOM=true`
4. **Migration Safe**: Can run migration on existing databases without data loss

## Security Recommendations

### Development
```bash
LXC_ROOT_PASSWORD=devpass
LXC_PASSWORD_RANDOM=false
```

### Production
```bash
LXC_PASSWORD_RANDOM=true
LXC_PASSWORD_LENGTH=24
```

### High Security
```bash
LXC_PASSWORD_RANDOM=true
LXC_PASSWORD_LENGTH=32
# Ensure JWT_SECRET_KEY is strong and unique
```

## Troubleshooting

### Migration Error: "no such column: apps.lxc_root_password"

**Problem**: Database hasn't been migrated.

**Solution**:
```bash
cd /Users/fab/GitHub/proximity/backend
python migrations/add_lxc_password_column.py
```

### Can't Decrypt Password

**Problem**: Encryption key changed.

**Cause**: `JWT_SECRET_KEY` in `.env` was modified after passwords were encrypted.

**Solution**: 
- Restore original `JWT_SECRET_KEY`, OR
- Redeploy affected containers (new passwords will be generated)

### Random Passwords Not Working

**Check**:
```bash
grep LXC_PASSWORD_RANDOM .env
# Should show: LXC_PASSWORD_RANDOM=true
```

**Verify**:
```python
from core.config import settings
print(settings.LXC_PASSWORD_RANDOM)  # Should be True
```

## Future Enhancements

Potential improvements:

1. **Password Rotation**: Ability to change container passwords
2. **Password History**: Track password changes over time
3. **API Endpoint**: Retrieve passwords via authenticated API
4. **SSH Key Support**: Use SSH keys instead of passwords
5. **Password Strength**: Configurable complexity requirements
6. **Audit Logging**: Log when passwords are accessed
7. **External Secrets**: Integration with HashiCorp Vault or AWS Secrets Manager

## References

- [Cryptography Library](https://cryptography.io/en/latest/)
- [Python Secrets Module](https://docs.python.org/3/library/secrets.html)
- [Proxmox LXC Security](https://pve.proxmox.com/wiki/Linux_Container)
- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
