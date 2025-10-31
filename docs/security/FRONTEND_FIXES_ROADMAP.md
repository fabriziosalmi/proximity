# Frontend Security Fixes - Implementation Roadmap

**Date**: 2025-10-30
**Total Issues**: 18 (4 HIGH, 10 MEDIUM, 4 LOW)
**Estimated Effort**: 10-14 hours
**Priority**: Phase-based implementation

---

## PHASE 1: CRITICAL (Estimated: 2-3 hours)
**Must complete before production deployment**

### Issue #1: Remove Sensitive Information from Console Logs

**File**: `src/lib/api.ts`
**Lines**: 81, 90
**Impact**: Prevents information disclosure via browser console
**Effort**: 30 minutes

**Current Code**:
```typescript
// Line 81
console.error(`❌ API Error ${response.status}:`, data);

// Line 90
console.error(`💥 API Exception for ${endpoint}:`, error);
```

**Fixed Code**:
```typescript
// Line 80-85
if (!response.ok) {
  if (import.meta.env.PROD) {
    Sentry.captureException(new Error(`API Error ${response.status}`));
  } else {
    console.error(`❌ API Error ${response.status}:`, data);
  }
  return {
    success: false,
    error: data.detail || data.error || 'An unknown error occurred'
  };
}

// Line 89-95
if (error instanceof Error) {
  if (import.meta.env.PROD) {
    Sentry.captureException(error);
  } else {
    console.error(`💥 API Exception for ${endpoint}:`, error);
  }
  return {
    success: false,
    error: error.message
  };
}
```

---

### Issue #2: Create Logging Utility & Remove Console Statements

**Files**: Multiple (auth.ts, apps.ts, hooks.client.ts, etc.)
**Effort**: 1-2 hours
**Impact**: Prevents widespread information disclosure

**Step 1: Create logging utility**
```typescript
// src/lib/logger.ts
import * as Sentry from '@sentry/sveltekit';

export const logger = {
  debug: (msg: string, data?: any) => {
    if (import.meta.env.DEV) {
      console.log(`[DEBUG] ${msg}`, data);
    }
  },

  info: (msg: string, data?: any) => {
    if (import.meta.env.DEV) {
      console.info(`[INFO] ${msg}`, data);
    }
  },

  warn: (msg: string, data?: any) => {
    if (import.meta.env.DEV) {
      console.warn(`[WARN] ${msg}`, data);
    }
  },

  error: (msg: string, error?: any) => {
    Sentry.captureException(error || new Error(msg));
    if (import.meta.env.DEV) {
      console.error(`[ERROR] ${msg}`, error);
    }
  }
};
```

**Step 2: Replace all console calls**

Search for and replace:
- `console.log(` → `logger.debug(`
- `console.error(` → `logger.error(`
- `console.warn(` → `logger.warn(`

**Files to update**:
- src/lib/stores/auth.ts (lines 55, 58, 71, 76)
- src/lib/stores/apps.ts (lines 59, 82, 83, 85, 266)
- src/hooks.client.ts (lines 25-31)
- src/hooks.server.ts (lines 27)
- All route files

---

### Issue #3: Validate URL Parameters

**File**: `src/lib/api.ts`
**Lines**: 185, 208, 262, 272
**Effort**: 45 minutes
**Impact**: Prevents URL injection attacks

**Search and Replace Pattern**:

Find all instances of:
```typescript
const params = hostId ? `?host_id=${hostId}` : '';
```

Replace with:
```typescript
const params = hostId ? `?host_id=${Number(hostId)}` : '';
```

Find all instances of:
```typescript
const params = tail ? `?tail=${tail}` : '';
```

Replace with:
```typescript
const params = tail ? `?tail=${Math.max(0, Number(tail))}` : '';
```

**Better approach - use URLSearchParams**:
```typescript
// Create reusable helper
private buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined) {
      // Validate numbers
      if (key.includes('id') || key === 'tail') {
        const numValue = Number(value);
        if (!isNaN(numValue)) {
          searchParams.append(key, String(numValue));
        }
      } else {
        searchParams.append(key, String(value));
      }
    }
  }

  const query = searchParams.toString();
  return query ? `?${query}` : '';
}
```

---

### Issue #4: Fix Hardcoded Sentry DSN

**Files**: `src/hooks.client.ts`, `src/hooks.server.ts`
**Line**: 10
**Effort**: 15 minutes
**Impact**: Prevents hardcoded credentials

**Current Code**:
```typescript
dsn: import.meta.env.VITE_SENTRY_DSN || 'https://example@sentry.io/PROJECT',
```

**Fixed Code**:
```typescript
// Remove fallback entirely
dsn: import.meta.env.VITE_SENTRY_DSN,

// Or validate in production
const dsn = import.meta.env.VITE_SENTRY_DSN;
if (!dsn && import.meta.env.PROD) {
  throw new Error('VITE_SENTRY_DSN is required in production');
}

Sentry.init({
  dsn: dsn || undefined,  // undefined = Sentry disabled in dev
  environment: import.meta.env.MODE,
  // ... rest of config
});
```

**Environment Setup**:
```bash
# .env.production
VITE_SENTRY_DSN=https://YOUR_DSN@sentry.io/PROJECT_ID
```

---

## PHASE 2: HIGH PRIORITY (Estimated: 3-4 hours)
**Fix after Phase 1**

### Issue #5: Enforce CSRF Token Requirement

**File**: `src/lib/api.ts`
**Lines**: 51-61
**Effort**: 20 minutes

**Current Code**:
```typescript
if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
  const csrfToken = this.getCsrfToken();
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
  } else {
    console.warn(`⚠️ [ApiClient] No CSRF token found...`);
  }
}
```

**Fixed Code**:
```typescript
if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
  const csrfToken = this.getCsrfToken();
  if (!csrfToken) {
    throw new Error('CSRF token is required for state-changing requests. This should not happen in normal operation.');
  }
  headers['X-CSRFToken'] = csrfToken;
  logger.debug(`CSRF token added for ${method} ${endpoint}`);
}
```

---

### Issue #6: Add Response Type Validation

**File**: `src/lib/api.ts`
**Lines**: 147, 158, 374
**Effort**: 1.5 hours

**Create TypeScript interfaces**:
```typescript
// src/lib/types/api.ts
export interface Host {
  id: number;
  name: string;
  host: string;
  port: number;
  is_active: boolean;
}

export interface HostsResponse {
  success: boolean;
  data: Host[];
}

export interface ProxmoxSettings {
  host: string;
  port: number;
  user: string;
  verify_ssl: boolean;
}
```

**Update API methods**:
```typescript
async createHost(data: Omit<Host, 'id'>): Promise<Host> {
  const response = await this.request<Host>('/proxmox/hosts', {
    method: 'POST',
    body: JSON.stringify(data)
  });

  if (!response.success || !response.data) {
    throw new Error('Failed to create host');
  }

  return response.data;
}
```

---

### Issue #7: Add Null Checks in State Updates

**File**: `src/lib/stores/apps.ts`
**Lines**: 87, 171-176
**Effort**: 30 minutes

**Current Code**:
```typescript
const appsArray = (response.data as any).apps || response.data || [];
```

**Fixed Code**:
```typescript
const appsArray = Array.isArray(response.data?.apps)
  ? response.data.apps
  : Array.isArray(response.data)
  ? response.data
  : [];

// Type guard function
function isApplicationArray(data: any): data is Application[] {
  return Array.isArray(data) && data.every(app =>
    app && typeof app === 'object' && 'id' in app && 'status' in app
  );
}
```

---

### Issue #10: Fix Hostname Validation

**File**: `src/lib/components/DeploymentModal.svelte`
**Lines**: 91-94
**Effort**: 15 minutes

**Current Code**:
```typescript
if (!/^[a-z0-9-]+$/.test(hostname)) {
  error = 'Hostname must contain only lowercase letters, numbers, and hyphens';
}
```

**Fixed Code**:
```typescript
// RFC 952/1123 compliant hostname validation
const hostnameRegex = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$/;

if (!hostnameRegex.test(hostname)) {
  error = 'Hostname must start and end with alphanumeric, contain only lowercase letters, numbers, and hyphens';
} else if (hostname.length > 63) {
  error = 'Hostname must be 63 characters or less';
}
```

**Also update**: CloneModal.svelte (same validation needed)

---

## PHASE 3: MEDIUM PRIORITY (Estimated: 2-3 hours)
**Fix in next sprint**

### Issue #7: Fix Polling Race Conditions

**File**: `src/lib/stores/apps.ts`
**Lines**: 197-265
**Effort**: 45 minutes

**Add state guard**:
```typescript
let isPolling = false;
let pollingInterval: ReturnType<typeof setInterval> | null = null;

function startPolling(intervalMs: number = 5000) {
  if (isPolling) {
    logger.warn('Polling already started');
    return;
  }

  isPolling = true;
  pollingInterval = setInterval(() => {
    fetchApps();
  }, intervalMs);

  logger.debug(`Polling started with interval ${intervalMs}ms`);
}

function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
  isPolling = false;
  logger.debug('Polling stopped');
}
```

---

### Issue #8: Clear Password After Use

**File**: `src/lib/components/settings/ProxmoxSettings.svelte`
**Lines**: 21, 42, 243
**Effort**: 20 minutes

**Update form handling**:
```typescript
let password = '';

async function saveSettings() {
  try {
    // Make API call
    const result = await api.saveProxmoxSettings({
      host,
      port,
      user,
      password,
      verify_ssl: verifySsl
    });

    // Clear password immediately
    password = '';

    if (result.success) {
      toasts.success('Proxmox settings saved');
    }
  } catch (error) {
    toasts.error('Failed to save settings');
    password = '';  // Clear even on error
  }
}
```

---

### Issue #11: Sanitize Error Messages

**File**: `src/routes/register/+page.svelte`
**Lines**: 69-83
**Effort**: 30 minutes

**Create error sanitizer**:
```typescript
// src/lib/errors.ts
const SAFE_ERROR_MESSAGES: Record<string, string> = {
  'user_already_exists': 'An account with this email already exists',
  'invalid_email': 'Please provide a valid email address',
  'password_too_weak': 'Password must be at least 8 characters',
  'email_required': 'Email is required',
};

export function sanitizeError(error: string): string {
  // If it's a known error code, return safe message
  const knownError = Object.keys(SAFE_ERROR_MESSAGES).find(key =>
    error.toLowerCase().includes(key)
  );

  if (knownError) {
    return SAFE_ERROR_MESSAGES[knownError];
  }

  // For unknown errors, return generic message and log to Sentry
  Sentry.captureMessage(`Unknown error: ${error}`);
  return 'An error occurred. Please try again or contact support.';
}
```

**Update registration**:
```typescript
try {
  const errorData = JSON.parse(response.error);
  if (Array.isArray(errorData.detail)) {
    errorData.detail.forEach((err: any) => {
      const field = err.loc[err.loc.length - 1];
      const safeMessage = sanitizeError(err.msg);
      validationErrors[field] = safeMessage;
    });
  }
} catch {
  errorMessage = sanitizeError(response.error);
}
```

---

### Issue #12: Fix Email Validation

**File**: `src/routes/register/+page.svelte`
**Lines**: 28-29
**Effort**: 10 minutes

**Better email regex**:
```typescript
// More strict email validation (still not RFC 5322 compliant, but better)
const emailRegex = /^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$/;

if (!emailRegex.test(email)) {
  validationErrors.email = 'Please enter a valid email address';
}

// Or use HTML5 validation
<input type="email" bind:value={email} />
```

---

### Issue #16: Add Request Timeouts

**File**: `src/lib/api.ts`
**Lines**: 42-96
**Effort**: 30 minutes

**Wrap fetch with timeout**:
```typescript
private async request<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = 30000
): Promise<ApiResponse<T>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const fetchOptions: RequestInit = {
      ...options,
      headers,
      credentials: 'include',
      signal: controller.signal
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, fetchOptions);
    // ... rest of implementation
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      return {
        success: false,
        error: `Request timeout after ${timeoutMs}ms`
      };
    }
    // ... other error handling
  } finally {
    clearTimeout(timeout);
  }
}
```

---

## PHASE 4: NICE TO HAVE (Estimated: 3-4 hours)
**Future improvements**

### Issue #13: Remove Fallback URLs
**Effort**: 10 minutes
**Simple fix**: Remove `|| 'localhost:8000'` fallback

### Issue #14: Add Error Boundaries
**Effort**: 1 hour
**Create SvelteKit error pages and component error handling**

### Issue #15: Improve Polling Mechanism
**Effort**: 1.5 hours
**Options**:
- Exponential backoff on errors
- WebSocket integration for real-time
- Server-Sent Events (SSE)

### Issue #17: Add CSP Headers
**Effort**: 45 minutes
**Configure in svelte.config.js**

### Issue #18: Remove Debug Logging
**Effort**: 10 minutes
**Remove console.log from Sentry client hook**

---

## 📊 SUMMARY TABLE

| Phase | Issues | Effort | Priority |
|-------|--------|--------|----------|
| Phase 1 | #1, #2, #3, #4 | 2-3 hrs | CRITICAL |
| Phase 2 | #5, #6, #7, #10 | 3-4 hrs | HIGH |
| Phase 3 | #7, #8, #11, #12, #16 | 2-3 hrs | MEDIUM |
| Phase 4 | #13, #14, #15, #17, #18 | 3-4 hrs | LOW |
| **TOTAL** | **18** | **10-14 hrs** | |

---

## 🎯 BEFORE PRODUCTION

**Minimum Requirements**:
- Complete Phase 1 (2-3 hours)
- Complete Phase 2 (3-4 hours)
- **Total: 5-7 hours**

**Recommended**:
- Complete Phases 1-3 (7-10 hours)
- Test all changes thoroughly
- Run security audit again

---

## 🧪 TESTING CHECKLIST

### Phase 1 Testing
- [ ] Console clean in production build (no console.log visible)
- [ ] Sentry capturing errors correctly
- [ ] URL parameters properly validated
- [ ] Sentry DSN loaded from environment

### Phase 2 Testing
- [ ] CSRF token required for POST/PUT/DELETE
- [ ] API response types validated
- [ ] Null safety checks prevent crashes
- [ ] Hostname validation rejects invalid formats

### Phase 3 Testing
- [ ] Polling doesn't create multiple intervals
- [ ] Password cleared after save
- [ ] Error messages are sanitized
- [ ] API requests timeout after 30s

### Phase 4 Testing
- [ ] Error boundaries catch component errors
- [ ] CSP headers enforced
- [ ] Real-time updates work correctly

---

**Generated**: 2025-10-30
**Status**: ✅ Ready for Implementation
**Next Step**: Start Phase 1 fixes
