# 🔐 AuthStore Data Flow Diagrams

## 1. Application Startup Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User Opens Browser / Navigates to App                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ +layout.svelte Loads                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ onMount(() => {                                             │ │
│ │   authStore.init();  ← CRITICAL FIRST STEP                 │ │
│ │   ThemeService.init();                                      │ │
│ │ })                                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ authStore.init() Executes                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Read localStorage.getItem('access_token')               │ │
│ │ 2. Read localStorage.getItem('user')                       │ │
│ │ 3. If both exist:                                          │ │
│ │    - Parse user JSON                                       │ │
│ │    - Update store: { token, user, isAuthenticated: true } │ │
│ │    - Set body[data-api-client-ready="true"]               │ │
│ │    - Log: "Initialized with existing session"             │ │
│ │ 4. If either missing:                                      │ │
│ │    - Keep store: { token: null, user: null }              │ │
│ │    - Log: "No existing session found"                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ All Subscribers Notified (Svelte Reactive System)               │
│ ┌───────────────────────────────────────────────────────┐       │
│ │ ApiClient Constructor (runs once)                     │       │
│ │ authStore.subscribe(state => {                        │       │
│ │   this.accessToken = state.token;                     │       │
│ │   console.log("Auth state updated:", state.token);    │       │
│ │ })                                                    │       │
│ └───────────────────────────────────────────────────────┘       │
│ ┌───────────────────────────────────────────────────────┐       │
│ │ UI Components (any that import authStore)             │       │
│ │ $authStore.isAuthenticated → show/hide content        │       │
│ │ $authStore.user.username → display user info          │       │
│ └───────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ App is Ready                                                     │
│ - ApiClient has token (if logged in)                            │
│ - UI reflects auth state                                        │
│ - All API calls will include Authorization header              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Login Flow (User Interactive)

```
┌─────────────────────────────────────────────────────────────────┐
│ User Enters Credentials on /login Page                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ handleLogin() in +page.svelte                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ const response = await api.login(username, password);      │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ ApiClient.login() Method                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ POST /api/core/auth/login { username, password }          │ │
│ │ ← Response: { access_token, user }                         │ │
│ │ return response (does NOT manage state!)                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Back in handleLogin() - Success Branch                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ if (response.success && response.data) {                   │ │
│ │   authStore.login(                                         │ │
│ │     response.data.access_token,                            │ │
│ │     response.data.user                                     │ │
│ │   );                                                       │ │
│ │   goto('/');                                               │ │
│ │ }                                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ authStore.login(token, user) Executes                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Update internal state:                                  │ │
│ │    { token, user, isAuthenticated: true }                 │ │
│ │                                                            │ │
│ │ 2. Sync to localStorage:                                   │ │
│ │    localStorage.setItem('access_token', token)            │ │
│ │    localStorage.setItem('user', JSON.stringify(user))     │ │
│ │                                                            │ │
│ │ 3. Set ready signal:                                       │ │
│ │    body[data-api-client-ready="true"]                     │ │
│ │                                                            │ │
│ │ 4. Notify all subscribers (triggers set())                │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ All Subscribers React Immediately                                │
│ ┌───────────────────────────────────────────────────────┐       │
│ │ ApiClient subscription callback fires:                │       │
│ │ this.accessToken = state.token;                       │       │
│ │ → All future API calls now authenticated!             │       │
│ └───────────────────────────────────────────────────────┘       │
│ ┌───────────────────────────────────────────────────────┐       │
│ │ UI Components update:                                 │       │
│ │ - Show authenticated nav                              │       │
│ │ - Display user profile                                │       │
│ │ - Enable protected features                           │       │
│ └───────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Navigate to Home Page (/) - Fully Authenticated                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Logout Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User Clicks Logout Button                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ handleLogout() in Navigation Component                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ authStore.logout();  ← Single source of truth              │ │
│ │ api.logout();        ← Just clears Sentry context          │ │
│ │ goto('/login');                                            │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ authStore.logout() Executes                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Clear localStorage:                                     │ │
│ │    localStorage.removeItem('access_token')                │ │
│ │    localStorage.removeItem('user')                        │ │
│ │    body.removeAttribute('data-api-client-ready')          │ │
│ │                                                            │ │
│ │ 2. Clear internal state:                                   │ │
│ │    { token: null, user: null, isAuthenticated: false }    │ │
│ │                                                            │ │
│ │ 3. Notify all subscribers (triggers set())                │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ All Subscribers React Immediately                                │
│ ┌───────────────────────────────────────────────────────┐       │
│ │ ApiClient subscription callback fires:                │       │
│ │ this.accessToken = null;                              │       │
│ │ → All future API calls are unauthenticated            │       │
│ └───────────────────────────────────────────────────────┘       │
│ ┌───────────────────────────────────────────────────────┐       │
│ │ UI Components update:                                 │       │
│ │ - Hide authenticated nav                              │       │
│ │ - Clear user profile display                          │       │
│ │ - Disable protected features                          │       │
│ └───────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Navigate to Login Page - Fully Logged Out                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. E2E Programmatic Login Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ E2E Test Starts (Playwright)                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ programmatic_login(page, auth_token) Called                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Step 1: Register init script (runs before page loads)     │ │
│ │ page.add_init_script("""                                   │ │
│ │   localStorage.setItem('access_token', 'xxx...');         │ │
│ │   localStorage.setItem('user', '{"id":1,...}');           │ │
│ │ """)                                                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ page.goto('/') - Navigate to App                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Browser Loads Page                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Init script runs FIRST (injects token + user)          │ │
│ │ 2. Page HTML loads                                         │ │
│ │ 3. Svelte app mounts                                       │ │
│ │ 4. +layout.svelte onMount fires                            │ │
│ │ 5. authStore.init() executes                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ authStore.init() Finds Injected Token                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Reads localStorage.getItem('access_token') → FOUND!    │ │
│ │ 2. Reads localStorage.getItem('user') → FOUND!            │ │
│ │ 3. Updates store with token + user                        │ │
│ │ 4. Sets body[data-api-client-ready="true"]                │ │
│ │ 5. Logs: "Initialized with existing session"              │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ ApiClient Subscription Fires                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ this.accessToken = state.token;                            │ │
│ │ console.log("Auth state updated: token=SET");              │ │
│ │ → ApiClient is now ready for authenticated requests!       │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ E2E Test Continues (Wait for Ready Signal)                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ page.wait_for_timeout(1000)                                │ │
│ │ page.wait_for_selector('body[data-api-client-ready]')     │ │
│ │ → Signal detected! ApiClient is ready!                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ E2E Test Makes Authenticated API Call                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ POST /api/apps/ { ... }                                    │ │
│ │ Headers: { Authorization: "Bearer xxx..." }               │ │
│ │ ← Response: 201 Created (SUCCESS!)                         │ │
│ │                                                            │ │
│ │ ✅ NO MORE 401 ERRORS!                                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Race Condition Prevention (Key Insight)

### ❌ OLD WAY (RACE CONDITIONS)
```
Thread 1: ApiClient Constructor
  │
  ├─ Read localStorage.getItem('access_token')
  │  → Returns null (token not injected yet)
  │
  └─ this.accessToken = null
     ❌ RACE LOST

Thread 2: E2E Test
  │
  └─ Injects token into localStorage
     (but ApiClient already read it!)
```

### ✅ NEW WAY (BULLETPROOF)
```
Thread 1: E2E Test
  │
  ├─ Registers init script (injects token BEFORE page loads)
  │
  └─ Navigates to page
     │
     └─ Page loads → authStore.init() runs
        │
        └─ Reads localStorage → Token is there! ✅
           │
           └─ Notifies ApiClient via subscription
              │
              └─ ApiClient receives token ✅
```

**Key Difference:**
- Old: ApiClient reads **once** at construction time
- New: ApiClient **subscribes** to authStore and receives updates

---

## 6. Subscriber Pattern (Technical Deep Dive)

```typescript
// authStore.ts
const { subscribe, set } = writable({ token: null });

return {
  subscribe,  // ← Exposes Svelte store subscription
  login: (token) => {
    set({ token });  // ← This triggers ALL subscribers!
  }
};

// api.ts (in ApiClient constructor)
authStore.subscribe(state => {
  // ⚡ This callback fires EVERY TIME authStore changes
  this.accessToken = state.token;
});
```

**Execution Timeline:**
```
T=0: ApiClient constructed
     └─ Subscribes to authStore
        └─ Receives initial state: { token: null }
           └─ this.accessToken = null

T=100ms: User logs in
         └─ authStore.login(token, user) called
            └─ set({ token, user, ... }) fires
               └─ ALL subscribers notified
                  └─ ApiClient callback fires
                     └─ this.accessToken = token ✅

T=200ms: API call made
         └─ ApiClient.request() runs
            └─ Reads this.accessToken
               └─ Token is present! ✅
                  └─ Adds Authorization header
                     └─ Backend receives authenticated request ✅
```

**This is why it works:** The subscription guarantees ApiClient **always** has the latest token, with **zero** race conditions.

---

**End of Flow Diagrams**
