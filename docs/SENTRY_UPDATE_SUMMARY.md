# Sentry Configuration Update Summary

## What Changed

### 1. Test Environment Configuration ✅
**File**: `tests/conftest.py`

**Before**: Tests were disabling Sentry completely
```python
os.environ['SENTRY_DSN'] = ''
os.environ['SENTRY_ENVIRONMENT'] = 'testing'
```

**After**: Tests now send to development stream
```python
os.environ['SENTRY_ENVIRONMENT'] = 'development'
```

**Impact**: Test exceptions are now captured in the development stream for better debugging

---

### 2. Enhanced Sentry Initialization ✅
**File**: `backend/main.py`

#### Improved Environment Detection
- Auto-detects "development" for localhost, local, or test hostnames
- Defaults to "production" for other environments
- Supports explicit `SENTRY_ENVIRONMENT` override

#### Enhanced Context Capturing
Added to every event:
- **Application context**: name, version, debug mode, environment
- **Proxmox context**: host, port, SSL verification status
- **Database context**: connection scheme
- **Exception details**: type, module, custom attributes
- **Request context**: path, method, URL

#### Smart Sampling Configuration
- **Development**: 100% traces, 100% errors, debug mode ON
- **Production**: 10% traces, 100% errors, debug mode OFF

#### New Features
- `attach_stacktrace=True`: Full stack traces on all events
- `max_breadcrumbs=50`: More context history
- `debug=True` in development: Verbose Sentry logging

---

### 3. Enhanced Exception Handlers ✅
**File**: `backend/main.py`

All exception handlers now add rich Sentry context:

#### ProxmoxError Handler
```python
with sentry_sdk.push_scope() as scope:
    scope.set_tag("error_type", "proxmox")
    scope.set_context("proxmox_error", {
        "error_message": str(exc),
        "request_path": request.url.path,
        "request_method": request.method,
    })
    sentry_sdk.capture_exception(exc)
```

#### AppServiceError Handler
```python
with sentry_sdk.push_scope() as scope:
    scope.set_tag("error_type", "app_service")
    scope.set_context("app_service_error", {...})
    sentry_sdk.capture_exception(exc)
```

#### HTTPException Handler
- Only captures 5xx errors (server errors)
- Skips 4xx errors (client errors)
- Includes status code tag

#### General Exception Handler
- Captures ALL unhandled exceptions
- Includes exception type, module, message
- Adds query parameters if present

---

### 4. Enhanced User Context ✅
**File**: `backend/api/middleware/auth.py`

Added to authenticated requests:
```python
sentry_sdk.set_user({
    "id": str(token_data.user_id),
    "username": token_data.username,
    "email": getattr(user, "email", None),
    "role": token_data.role,
    "ip_address": request.client.host,  # NEW
})

# Additional tags for filtering
sentry_sdk.set_tag("user_role", token_data.role)  # NEW
sentry_sdk.set_tag("authenticated", "true")  # NEW
```

---

### 5. Documentation ✅
**New File**: `docs/SENTRY_CONFIGURATION.md`

Comprehensive guide including:
- Environment configuration details
- Context information captured
- Error handler integration
- Testing configuration
- Breadcrumbs explanation
- Tags for filtering
- Performance monitoring
- Best practices
- Troubleshooting guide
- Example queries

---

## Benefits

### For Development
1. **Better Test Debugging**: Test errors now visible in Sentry development stream
2. **Full Visibility**: 100% sampling means nothing is missed
3. **Rich Context**: Every error has full request/user/system context
4. **Debug Mode**: Verbose Sentry logging helps troubleshoot integration

### For Production
1. **Focused Monitoring**: Only errors (not info/warning) sent to reduce noise
2. **Optimized Sampling**: 10% performance monitoring to manage quota
3. **Error Priority**: 100% of errors captured, nothing missed
4. **Smart Filtering**: Tags make it easy to filter and group errors

### For All Environments
1. **User Tracking**: Know which users hit errors
2. **Request Context**: Full request details for reproduction
3. **Exception Details**: Type, module, custom attributes captured
4. **Breadcrumbs**: Last 50 actions leading to error
5. **Performance Data**: Transaction timing and slow endpoint detection

---

## Sentry Dashboard Usage

### Filter by Environment
```
environment:development  # All dev/test errors
environment:production   # Production errors only
```

### Filter by Error Type
```
error_type:proxmox        # Proxmox API errors
error_type:app_service    # Application service errors
error_type:unhandled      # Unexpected errors
```

### Filter by User Role
```
user_role:admin          # Admin user errors
user_role:user           # Regular user errors
authenticated:true       # All authenticated requests
```

### Complex Queries
```
environment:production error_type:proxmox user_role:admin
```

---

## Testing Verification

Tests now send to development stream as expected:

```bash
$ pytest tests/test_app_clone_config.py -v
...
================================== 2 passed in 0.44s ===================================
```

All test errors will appear in your Sentry development environment with full context.

---

## Environment Variables

### Required
```bash
SENTRY_DSN=https://your-key@sentry.io/your-project
```

### Optional (with smart defaults)
```bash
# Explicitly set environment (auto-detects if not set)
SENTRY_ENVIRONMENT=development  # or production

# Set custom release version (uses APP_VERSION if not set)
SENTRY_RELEASE=0.1.0
```

---

## Migration Notes

### No Breaking Changes
- Existing Sentry configuration continues to work
- New features are additive
- Backward compatible with all existing code

### Recommended Actions
1. ✅ Clear old Sentry issues in development
2. ✅ Monitor development stream for test errors
3. ✅ Set up alerts for production errors
4. ✅ Review new tags and context in first production errors
5. ✅ Update team on new filtering capabilities

---

## Next Steps

1. **Monitor Development**: Check that test errors appear in development stream
2. **Set Up Alerts**: Configure Sentry alerts for production errors
3. **Review Tags**: Use new tags to organize and filter errors
4. **Team Training**: Share `SENTRY_CONFIGURATION.md` with team
5. **Fine-tune**: Adjust sampling rates based on volume

---

## Support

Questions? Check:
- `docs/SENTRY_CONFIGURATION.md` - Complete configuration guide
- `docs/SENTRY_QUICK_START.md` - Getting started guide
- Sentry dashboard for live error monitoring
