# Sentry Integration Guide for Proximity 2.0

## Overview

Proximity 2.0 is now fully integrated with Sentry for comprehensive error and performance monitoring across both the Django backend and SvelteKit frontend. This follows our "Tranquillità by Default" pillar, ensuring we have full visibility into the application's health.

## 🎯 What's Integrated

### Backend (Django)
- ✅ Full Django integration with `sentry-sdk[django]`
- ✅ Celery task monitoring
- ✅ Redis operation tracking
- ✅ User context enrichment via middleware
- ✅ Debug endpoint `/api/core/sentry-debug/` for verification

### Frontend (SvelteKit)
- ✅ SvelteKit SDK with full observability
- ✅ Performance tracing
- ✅ Session replay (optional)
- ✅ Log shipping to Sentry
- ✅ User context enrichment on login/logout
- ✅ Test button on home page

## 📋 Configuration

### Environment Variables

**Backend & Frontend:**
```bash
SENTRY_DSN=https://your-dsn@sentry.io/project
SENTRY_ENVIRONMENT=development|staging|production
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% in dev, lower in prod
```

**Frontend Only:**
```bash
VITE_SENTRY_DSN=https://your-dsn@sentry.io/project
VITE_SENTRY_ENVIRONMENT=development
VITE_SENTRY_TRACES_SAMPLE_RATE=1.0
VITE_SENTRY_DEBUG=false  # Set to true to send errors in dev mode
```

**Optional (for source maps & releases):**
```bash
SENTRY_ORG=your-org
SENTRY_PROJECT=your-project
SENTRY_AUTH_TOKEN=your-auth-token
```

### Docker Compose

The `docker-compose.yml` is pre-configured with Sentry environment variables for:
- `backend` service
- `celery_worker` service
- `celery_beat` service
- `frontend` service

## 🔍 Features

### 1. Automatic Error Capture

**Backend:**
- All unhandled exceptions in Django views
- Celery task failures
- Redis connection errors
- Database query errors

**Frontend:**
- JavaScript runtime errors
- Promise rejections
- Component errors
- Network failures

### 2. Performance Monitoring

**Backend:**
- Database query performance
- Celery task duration
- Redis operation timing
- HTTP request/response times

**Frontend:**
- Page load times
- Component render duration
- API call performance
- Navigation timing

### 3. User Context Enrichment

**Backend Middleware:**
```python
# apps/core/middleware.py - SentryUserContextMiddleware
# Automatically sets user context on every authenticated request
{
    "id": user.id,
    "username": user.username,
    "email": user.email
}
```

**Frontend API Client:**
```typescript
// src/lib/api.ts - login() method
// Sets user context on successful login
Sentry.setUser({
    id: user.id,
    username: user.username,
    email: user.email
});
```

### 4. Development Mode Behavior

**By default, Sentry does NOT send events in development mode** to reduce noise. This is controlled by the `beforeSend` hook.

**To enable Sentry in dev mode:**
- Backend: Set `SENTRY_DEBUG=True`
- Frontend: Set `VITE_SENTRY_DEBUG=true`

Errors will be logged to console regardless of sending.

## 🧪 Testing the Integration

### Backend Test

1. **Start the application:**
   ```bash
   docker-compose up
   ```

2. **Hit the debug endpoint:**
   ```bash
   curl http://localhost:8000/api/core/sentry-debug/
   ```

3. **Expected result:**
   - Console shows: `🔴 [Sentry Server] Error captured`
   - Sentry dashboard shows: `ZeroDivisionError: Sentry test error from backend.`

### Frontend Test

1. **Navigate to:** `http://localhost:5173`

2. **Click the "🐛 Test Sentry" button**

3. **Expected result:**
   - Console shows: `🔴 [Sentry Client] Error captured`
   - Sentry dashboard shows: `Error: Sentry test error from frontend.`

## 📊 What Gets Tracked

### Context Information
- **User:** ID, username, email (when authenticated)
- **Environment:** development/staging/production
- **Device:** Browser, OS, screen resolution (frontend)
- **Request:** URL, method, headers, body
- **Performance:** Response times, query counts

### Breadcrumbs
- HTTP requests
- Database queries
- Console logs
- User interactions (clicks, navigation)
- Cache operations

## 🚀 Production Recommendations

1. **Lower Sample Rates:**
   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
   ```

2. **Enable Session Replay only for errors:**
   ```typescript
   replaysSessionSampleRate: 0.1,  // 10% of all sessions
   replaysOnErrorSampleRate: 1.0,  // 100% of sessions with errors
   ```

3. **Set Up Alerts:**
   - Configure Sentry alerts for critical errors
   - Set up Slack/email notifications
   - Define SLA thresholds

4. **Source Maps:**
   - Use `.env.sentry-build-plugin` for automatic upload
   - Configure `SENTRY_AUTH_TOKEN` for CI/CD

5. **Data Scrubbing:**
   - Review `send_default_pii` setting
   - Configure data scrubbing rules in Sentry dashboard
   - Be mindful of GDPR compliance

## 📚 Files Modified/Created

### Backend
- `backend/requirements.txt` - Added `sentry-sdk[django]==1.39.2`
- `backend/proximity/settings.py` - Sentry initialization
- `backend/apps/core/middleware.py` - **NEW** User context middleware
- `backend/apps/core/api.py` - Debug endpoint

### Frontend
- `frontend/src/hooks.server.ts` - Server-side Sentry init
- `frontend/src/hooks.client.ts` - Client-side Sentry init
- `frontend/src/instrumentation.server.ts` - **NEW** Server instrumentation
- `frontend/src/lib/api.ts` - User context on login/logout
- `frontend/src/routes/+page.svelte` - Test button

### Configuration
- `.env.example` - Sentry environment variables
- `docker-compose.yml` - Sentry env vars for all services

## 🔗 Resources

- [Sentry Django Documentation](https://docs.sentry.io/platforms/python/guides/django/)
- [Sentry SvelteKit Documentation](https://docs.sentry.io/platforms/javascript/guides/sveltekit/)
- [Proximity 2.0 Sentry Dashboard](https://sentry.io/organizations/fabriziosalmi/projects/proximity/)

## 🎉 Benefits

1. **Immediate Issue Detection:** Know about errors before users report them
2. **Performance Insights:** Identify slow queries and bottlenecks
3. **User Impact Analysis:** See how many users are affected by each issue
4. **Release Tracking:** Monitor error rates across deployments
5. **Peace of Mind:** "Tranquillità by Default" ✅

---

**Last Updated:** October 19, 2025  
**Sentry Version:** SDK 1.39.2 (Backend) | @sentry/sveltekit 10.20.0 (Frontend)
