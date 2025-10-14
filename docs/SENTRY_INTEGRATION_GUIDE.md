# Sentry Integration Guide - Proximity Platform

## Overview

Sentry is now integrated into the Proximity platform frontend to provide real-time error tracking, performance monitoring, and session replay capabilities.

## 📊 What Sentry Tracks

### 1. **JavaScript Errors**
- Uncaught exceptions
- Unhandled promise rejections
- Component mounting errors
- Router navigation failures
- API request failures

### 2. **Performance Metrics**
- Page load times
- View transition performance
- API call latency
- Resource loading times

### 3. **Session Replay** (10% of normal sessions, 100% of error sessions)
- User interactions leading to errors
- Network requests
- Console logs
- DOM mutations

### 4. **Breadcrumbs**
- Navigation history
- User actions (clicks, form submissions)
- API calls
- Custom application events

## 🔧 Configuration

### Environment Detection
Sentry automatically detects the environment:
- `localhost` or `127.0.0.1` → `development`
- Other domains → `production`

### Development Mode
By default, Sentry **does not send events** from localhost to avoid cluttering production data.

To enable Sentry in development:
```javascript
localStorage.setItem('sentry_debug_enabled', 'true');
```

To disable again:
```javascript
localStorage.removeItem('sentry_debug_enabled');
```

## 📝 Manual Error Reporting

### Basic Error Capture
```javascript
try {
    // Your code
} catch (error) {
    window.reportToSentry(error, {
        context: 'app_deployment',
        app_name: 'wordpress',
        user_action: 'deploy_button_clicked',
    });
}
```

### Custom Events
```javascript
// Track important application events
window.captureAppEvent('deployment_failed', {
    app_name: 'wordpress',
    error_code: 'TIMEOUT',
    duration_seconds: 120,
});
```

### Debug Breadcrumbs
```javascript
// Add custom breadcrumbs for debugging
window.addDebugBreadcrumb('User clicked deploy button', {
    app_id: 123,
    app_name: 'wordpress',
    node_id: 'pve1',
});
```

## 🎯 Integration Points

### 1. Router (Already Integrated)
- Navigation breadcrumbs automatically added
- View mounting errors captured
- Component registration errors tracked

### 2. API Calls
Add to your API utility:
```javascript
async function apiCall(endpoint, options) {
    try {
        const response = await fetch(endpoint, options);
        if (!response.ok) {
            const error = new Error(`API Error: ${response.status}`);
            window.reportToSentry(error, {
                context: 'api_call',
                endpoint,
                status: response.status,
                method: options.method,
            });
        }
        return response;
    } catch (error) {
        window.reportToSentry(error, {
            context: 'api_call',
            endpoint,
            network_error: true,
        });
        throw error;
    }
}
```

### 3. Deployment Flow
```javascript
async function deployApp(appData) {
    window.addDebugBreadcrumb('Starting deployment', {
        app: appData.name,
        node: appData.node_id,
    });

    try {
        const result = await api.post('/api/v1/apps', appData);
        
        window.captureAppEvent('deployment_success', {
            app_name: appData.name,
            duration: result.duration,
        });
        
        return result;
    } catch (error) {
        window.reportToSentry(error, {
            context: 'deployment',
            app_data: appData,
            error_type: error.constructor.name,
        });
        throw error;
    }
}
```

### 4. View Components
In your view mount functions:
```javascript
export function mount(container, state) {
    window.addDebugBreadcrumb(`Mounting ${viewName} view`, {
        has_data: !!state.apps,
        app_count: state.apps?.length || 0,
    });

    try {
        // Your mount logic
        renderView(container, state);
        
        return () => {
            // Cleanup
            container.innerHTML = '';
        };
    } catch (error) {
        window.reportToSentry(error, {
            context: 'view_mount',
            view: viewName,
            state_keys: Object.keys(state),
        });
        throw error;
    }
}
```

## 🔍 Accessing Sentry Dashboard

### URL
https://proximity.sentry.io

### What to Look For

#### 1. **Issues Tab**
- See all captured errors grouped by type
- View error frequency and affected users
- Access full stack traces
- Watch session replays of errors

#### 2. **Performance Tab**
- Transaction overview (page loads, navigation)
- Slowest operations
- Performance trends over time

#### 3. **Replays Tab**
- Watch user sessions that encountered errors
- See exactly what the user did before the error
- Review network calls and console logs

## 🎮 Testing Sentry Integration

### Test Error Capture
Open browser console and run:
```javascript
// Enable Sentry in development
localStorage.setItem('sentry_debug_enabled', 'true');

// Test basic error
throw new Error('Test Sentry integration');

// Test custom event
window.captureAppEvent('test_event', { test: true });

// Test breadcrumb
window.addDebugBreadcrumb('Test breadcrumb', { action: 'test' });
```

### Test Router Integration
```javascript
// Navigate to trigger breadcrumbs
router.navigateTo('apps');
router.navigateTo('catalog');

// Force a navigation error (view doesn't exist)
router.navigateTo('nonexistent_view');
```

## 📊 Monitoring Best Practices

### 1. **Error Grouping**
Use consistent context keys:
```javascript
window.reportToSentry(error, {
    context: 'deployment',  // Group by context
    app_name: 'wordpress',  // Group by app
    error_type: 'timeout',  // Group by error type
});
```

### 2. **Breadcrumbs for User Flow**
Add breadcrumbs at key interaction points:
```javascript
// Before critical operations
window.addDebugBreadcrumb('User opened app configuration', { app_id: 123 });
window.addDebugBreadcrumb('User clicked save', { fields_changed: ['cpu', 'memory'] });
```

### 3. **Performance Tags**
Tag slow operations:
```javascript
const startTime = performance.now();
try {
    await loadCatalog();
} finally {
    const duration = performance.now() - startTime;
    if (duration > 5000) {
        window.captureAppEvent('slow_catalog_load', {
            duration_ms: duration,
            item_count: items.length,
        });
    }
}
```

## 🚫 What NOT to Log

### 1. **Sensitive Data**
```javascript
// ❌ DON'T
window.reportToSentry(error, {
    password: user.password,        // Never!
    api_key: settings.api_key,      // Never!
    token: localStorage.token,      // Never!
});

// ✅ DO
window.reportToSentry(error, {
    user_id: user.id,               // OK
    has_password: !!user.password,  // OK
    has_api_key: !!settings.api_key,// OK
});
```

### 2. **PII (Personally Identifiable Information)**
Sentry config already masks:
- All text in session replays
- All media in session replays

But be cautious in custom contexts:
```javascript
// ❌ DON'T
window.reportToSentry(error, {
    email: user.email,           // Masked automatically, but avoid
    full_name: user.full_name,   // Avoid
});

// ✅ DO
window.reportToSentry(error, {
    user_id: user.id,            // OK - non-identifiable
    role: user.role,             // OK
});
```

## 🔔 Alert Configuration

### Recommended Alerts (Configure in Sentry)

1. **High Error Rate**
   - Trigger: >10 errors/minute
   - Notify: Slack, Email

2. **New Error Type**
   - Trigger: First occurrence of new error
   - Notify: Slack

3. **Performance Degradation**
   - Trigger: P95 response time >3s
   - Notify: Email

4. **Critical Errors**
   - Trigger: Any error in deployment flow
   - Notify: Slack, Email (immediate)

## 📈 Success Metrics

Track these in Sentry:

1. **Error Rate Trend** (target: <0.1% of sessions)
2. **Mean Time to Resolution** (target: <24h)
3. **Error-Free Session Rate** (target: >99.5%)
4. **Performance Score** (target: >80/100)

## 🛠️ Troubleshooting

### Sentry Not Capturing Errors

1. **Check SDK loaded:**
   ```javascript
   console.log(typeof Sentry); // Should be 'object'
   ```

2. **Check development mode:**
   ```javascript
   console.log(localStorage.getItem('sentry_debug_enabled'));
   ```

3. **Check environment:**
   ```javascript
   console.log(window.location.hostname);
   ```

### Events Not Appearing in Dashboard

1. **Check allowUrls filter** in `sentry-config.js`
2. **Check beforeSend filter** for blocked events
3. **Verify DSN is correct**

## 🔗 Resources

- **Sentry Dashboard:** https://proximity.sentry.io
- **Sentry Docs:** https://docs.sentry.io/platforms/javascript/
- **JavaScript SDK:** https://docs.sentry.io/platforms/javascript/guides/browser/

---

**Last Updated:** 2025-10-14  
**Sentry Version:** Browser SDK 7.x  
**Integration Status:** ✅ Active
