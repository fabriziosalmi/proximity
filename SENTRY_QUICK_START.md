# Sentry Integration Quick Reference

## 🚀 Quick Start

### Enable Sentry in Production

1. Add to `backend/.env`:
```bash
SENTRY_DSN=https://dbee00d4782d131ab54ffe60b16d969b@o149725.ingest.us.sentry.io/4510189390266368
```

2. Restart backend:
```bash
cd backend
python main.py
```

3. Verify in logs:
```
✓ Sentry initialized (environment=production, release=0.1.0)
```

## 🧪 Testing

### Backend Test (Server Must Be Running)
```bash
# Check Sentry status
curl http://localhost:8765/api/v1/test/sentry-info

# Trigger test error
curl http://localhost:8765/api/v1/test/sentry-backend
# Expected: 500 error + event in Sentry dashboard
```

### Frontend Test (Browser Console)
```javascript
// Check initialization
// Should see: ✅ Sentry initialized - Error tracking enabled

// Trigger test error
window.testSentry()
// Check Sentry dashboard in ~30 seconds
```

### Automated Test Suite
```bash
# Test frontend configuration only
python test_sentry_integration.py --frontend-only

# Test full integration (requires running server)
python test_sentry_integration.py
```

## 📝 What Gets Tracked

### Backend Errors
- ✅ Unhandled exceptions (500 errors)
- ✅ Logger.error() and above
- ✅ User context (from JWT)
- ✅ Request breadcrumbs

### Frontend Errors
- ✅ Uncaught JavaScript errors
- ✅ Unhandled promise rejections
- ✅ Login/logout events
- ✅ Deployment start/success/failure
- ✅ App deletion events
- ✅ Navigation breadcrumbs

## 🔍 User Context

### What's Captured
```json
{
  "id": "user-123",
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin"
}
```

### When It's Set
- **Backend:** Automatically on authenticated requests (via middleware)
- **Frontend:** Automatically on login, cleared on logout

## 🥖 Breadcrumb Trail Example

```
1. [user_action] Login attempt (username: admin)
2. [request] POST /api/v1/auth/login
3. [user_action] Login successful (role: admin)
4. [navigation] Navigated to #apps
5. [user_action] App deployment started (catalog: wordpress, hostname: myblog)
6. [request] POST /api/v1/apps/deploy
7. [user_action] App deployment succeeded (vmid: 102)
```

## 🛠 Manual Error Reporting

### Backend
```python
import sentry_sdk

# Add breadcrumb
sentry_sdk.add_breadcrumb(
    category="custom",
    message="Important operation started",
    level="info"
)

# Report error with context
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
```

### Frontend
```javascript
// Add breadcrumb
window.addDebugBreadcrumb('User clicked important button', {
    button_id: 'deploy-btn',
    timestamp: Date.now()
});

// Report error with context
try {
    riskyOperation();
} catch (error) {
    window.reportToSentry(error, {
        context: 'important_operation',
        user_action: 'button_click'
    });
}
```

## 🔕 Development Mode

### Disable Sentry in Development
Backend: Remove `SENTRY_DSN` from `.env` or leave empty

Frontend: Events are filtered by default. To enable:
```javascript
localStorage.setItem('sentry_debug_enabled', 'true')
```

## 📊 Sentry Dashboard

**URL:** https://sentry.io/organizations/proximity/issues/

### Key Metrics to Monitor
- Error rate trends
- User impact (affected users count)
- Resolution time
- Deployment success rate

## 🚨 Common Issues

### "Sentry not capturing errors"
1. Check `SENTRY_DSN` is set in `backend/.env`
2. Verify logs show: `✓ Sentry initialized`
3. Test with `/api/v1/test/sentry-backend` endpoint
4. Frontend: Check for `sentry_debug_enabled` blocking dev events

### "User context missing"
1. Verify user is authenticated (check for JWT token)
2. Backend: Check auth middleware is running
3. Frontend: Check console for `✓ Sentry user context set`

### "Too many events"
1. Enable development mode filtering
2. Add to frontend ignoreErrors in `sentry-config.js`
3. Adjust backend traces_sample_rate (default 10% in prod)

## 📚 Documentation

- **Full Audit Report:** `SENTRY_AUDIT_REPORT.md`
- **Sentry SDK Docs:** https://docs.sentry.io/platforms/python/guides/fastapi/
- **Frontend Config:** `backend/frontend/js/sentry-config.js`
- **Backend Init:** `backend/main.py` (lines 22-66)
- **Test Endpoints:** `backend/api/endpoints/test.py`

## ✅ Production Checklist

Before going live:
- [ ] `SENTRY_DSN` configured in production `.env`
- [ ] Test error capture with `/test/sentry-backend`
- [ ] Test frontend with `window.testSentry()`
- [ ] Configure Sentry alerts (email/Slack)
- [ ] Set up error assignment rules
- [ ] Document incident response process
- [ ] Train team on Sentry dashboard

---

**Need Help?** See `SENTRY_AUDIT_REPORT.md` for complete documentation.
