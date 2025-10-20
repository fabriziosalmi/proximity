# Settings Architecture - Visual Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    PROXIMITY 2.0 - SETTINGS ARCHITECTURE                  │
│                         (After API Refactoring)                           │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  FRONTEND LAYER                                                          │
└─────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────┐        ┌────────────────────────┐
    │ ResourceSettings.svelte │        │ NetworkSettings.svelte  │
    │                         │        │                         │
    │ ┌─────────────────────┐│        │ ┌─────────────────────┐│
    │ │ onMount()           ││        │ │ onMount()           ││
    │ │ - loadSettings()    ││        │ │ - loadSettings()    ││
    │ │                     ││        │ │                     ││
    │ │ Form Fields:        ││        │ │ Form Fields:        ││
    │ │ • CPU Cores         ││        │ │ • Subnet (CIDR)     ││
    │ │ • Memory (MB)       ││        │ │ • Gateway IP        ││
    │ │ • Disk (GB)         ││        │ │ • DNS Servers       ││
    │ │ • Swap (MB)         ││        │ │ • Bridge Name       ││
    │ │                     ││        │ │                     ││
    │ │ Actions:            ││        │ │ Actions:            ││
    │ │ • validateForm()    ││        │ │ • validateForm()    ││
    │ │ • handleSave()      ││        │ │ • handleSave()      ││
    │ └─────────────────────┘│        │ └─────────────────────┘│
    └────────┬───────────────┘        └────────┬───────────────┘
             │                                  │
             │                                  │
             └──────────────┬───────────────────┘
                            │
                            ↓
              ┌─────────────────────────────┐
              │      src/lib/api.ts         │
              │  ┌───────────────────────┐  │
              │  │ ApiClient Class       │  │
              │  │                       │  │
              │  │ Methods:              │  │
              │  │ • getResourceSettings │  │
              │  │ • saveResourceSettings│  │
              │  │ • getNetworkSettings  │  │
              │  │ • saveNetworkSettings │  │
              │  │                       │  │
              │  │ Auth:                 │  │
              │  │ • Bearer Token        │  │
              │  │ • Auto-inject headers │  │
              │  └───────────────────────┘  │
              └─────────────┬───────────────┘
                            │
                            │ HTTP Requests
                            │ (JSON + JWT)
                            ↓

┌─────────────────────────────────────────────────────────────────────────┐
│  API LAYER                                                               │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────┐
                    │  API Gateway          │
                    │  (Django + Ninja)     │
                    └───────────┬───────────┘
                                │
                ┌───────────────┴────────────────┐
                │                                │
                ↓                                ↓
    ┌───────────────────────┐      ┌───────────────────────┐
    │ GET /api/core/        │      │ GET /api/core/        │
    │     settings/resources│      │     settings/network  │
    │                       │      │                       │
    │ • No auth required    │      │ • No auth required    │
    │ • Returns defaults if │      │ • Returns defaults if │
    │   not configured      │      │   not configured      │
    └───────────────────────┘      └───────────────────────┘
                │                                │
                ↓                                ↓
    ┌───────────────────────┐      ┌───────────────────────┐
    │ POST /api/core/       │      │ POST /api/core/       │
    │      settings/resources│      │      settings/network │
    │                       │      │                       │
    │ Middleware:           │      │ Middleware:           │
    │ ✓ JWTAuth()          │      │ ✓ JWTAuth()          │
    │ ✓ @require_admin     │      │ ✓ @require_admin     │
    │                       │      │                       │
    │ Validation:           │      │ Validation:           │
    │ • CPU: 1-64 cores    │      │ • CIDR format         │
    │ • Memory: 512MB-128GB│      │ • Valid IPs           │
    │ • Disk: 8GB-2TB      │      │ • Gateway in subnet   │
    │ • Swap: 0-64GB       │      │ • Bridge name         │
    └───────────┬───────────┘      └───────────┬───────────┘
                │                                │
                └────────────┬───────────────────┘
                             │
                             ↓

┌─────────────────────────────────────────────────────────────────────────┐
│  BUSINESS LOGIC LAYER                                                    │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────┐
                    │ settings_service.py   │
                    │                       │
                    │ Functions:            │
                    │ • get_settings()      │
                    │ • save_settings()     │
                    │ • validate_resource_  │
                    │   settings()          │
                    │ • validate_network_   │
                    │   settings()          │
                    └───────────┬───────────┘
                                │
                                ↓

┌─────────────────────────────────────────────────────────────────────────┐
│  DATA LAYER                                                              │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────┐
                    │   PostgreSQL DB       │
                    │                       │
                    │  SystemSettings Table │
                    │  ┌─────────────────┐ │
                    │  │ id (PK)         │ │
                    │  │ setting_key     │ │
                    │  │ setting_value   │ │
                    │  │ created_at      │ │
                    │  │ updated_at      │ │
                    │  └─────────────────┘ │
                    │                       │
                    │  Resource Keys:       │
                    │  • default_cpu_cores  │
                    │  • default_memory_mb  │
                    │  • default_disk_gb    │
                    │  • default_swap_mb    │
                    │                       │
                    │  Network Keys:        │
                    │  • default_subnet     │
                    │  • default_gateway    │
                    │  • default_dns_primary│
                    │  • default_dns_       │
                    │    secondary          │
                    │  • default_bridge     │
                    └───────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  AUTHENTICATION FLOW                                                     │
└─────────────────────────────────────────────────────────────────────────┘

    User Login
        ↓
    POST /api/core/auth/login
        ↓
    Backend validates credentials
        ↓
    Returns JWT access_token
        ↓
    Frontend stores in localStorage
        ↓
    ApiClient.setToken(token)
        ↓
    ALL subsequent API calls include:
    Header: "Authorization: Bearer <token>"
        ↓
    Backend JWTAuth() middleware validates
        ↓
    Backend @require_admin checks role
        ↓
    Request processed or 403 Forbidden

┌─────────────────────────────────────────────────────────────────────────┐
│  DATA FLOW EXAMPLE: Saving Resource Settings                            │
└─────────────────────────────────────────────────────────────────────────┘

1. User changes CPU cores from 2 → 4 in UI
2. User clicks "Save Settings" button
3. Frontend validates: 1 ≤ 4 ≤ 64 ✓
4. Frontend calls:
   api.saveResourceSettings({
     default_cpu_cores: 4,
     default_memory_mb: 2048,
     default_disk_gb: 20,
     default_swap_mb: 512
   })
5. ApiClient adds headers:
   {
     "Content-Type": "application/json",
     "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
   }
6. POST /api/core/settings/resources
7. Backend JWTAuth extracts and validates JWT
8. Backend checks user.is_admin === true
9. Backend validates ranges:
   - CPU: 4 cores ✓ (1-64)
   - Memory: 2048 MB ✓ (512-131072)
   - Disk: 20 GB ✓ (8-2000)
   - Swap: 512 MB ✓ (0-65536)
10. Backend calls settings_service.save_settings()
11. Database UPDATE/INSERT SystemSettings rows
12. Response: { "success": true, "data": {...} }
13. Frontend shows toast: "✅ Resource settings saved successfully"
14. Settings persist across page reloads

┌─────────────────────────────────────────────────────────────────────────┐
│  ERROR HANDLING FLOW                                                     │
└─────────────────────────────────────────────────────────────────────────┘

Frontend Validation Error:
    validateForm() fails
        ↓
    Toast: "Please fix validation errors"
        ↓
    Highlights invalid fields in red
        ↓
    Does NOT call API

Backend Validation Error:
    API call made with invalid data
        ↓
    Backend validation fails
        ↓
    Returns 400 Bad Request
    { "error": "Invalid CIDR notation" }
        ↓
    Frontend catches error
        ↓
    Toast: "❌ Invalid CIDR notation"

Authentication Error:
    No token or expired token
        ↓
    Backend returns 401 Unauthorized
        ↓
    Frontend catches error
        ↓
    Redirects to /login

Authorization Error:
    Valid token but not admin
        ↓
    Backend returns 403 Forbidden
        ↓
    Frontend catches error
        ↓
    Toast: "❌ Admin access required"

Network Error:
    Backend unreachable
        ↓
    fetch() throws exception
        ↓
    Frontend catches in try-catch
        ↓
    Toast: "❌ Network error"

┌─────────────────────────────────────────────────────────────────────────┐
│  REMOVED: Old localStorage Implementation                                │
└─────────────────────────────────────────────────────────────────────────┘

    ❌ localStorage.setItem('resource_settings', JSON.stringify(settings))
    ❌ localStorage.getItem('resource_settings')
    ❌ localStorage.setItem('network_settings', JSON.stringify(settings))
    ❌ localStorage.getItem('network_settings')

    Problems with localStorage:
    ✗ Not persistent across devices
    ✗ Not shared between users
    ✗ No validation
    ✗ No authentication
    ✗ Browser-specific
    ✗ Easy to tamper with

┌─────────────────────────────────────────────────────────────────────────┐
│  BENEFITS: New API-Driven Implementation                                 │
└─────────────────────────────────────────────────────────────────────────┘

    ✅ Database persistence (PostgreSQL)
    ✅ Multi-user support
    ✅ Centralized configuration
    ✅ Authentication required
    ✅ Admin-only access control
    ✅ Backend validation
    ✅ Audit trail (created_at, updated_at)
    ✅ Consistent across all clients
    ✅ Backup-able with database
    ✅ Production-ready

┌─────────────────────────────────────────────────────────────────────────┐
│  TESTING COMMANDS                                                        │
└─────────────────────────────────────────────────────────────────────────┘

# Start backend
cd proximity2/backend
python manage.py runserver

# Start frontend
cd proximity2/frontend
npm run dev

# Manual test
Open: http://localhost:5173/settings
Login: admin / password
Test: Change values, save, refresh → values persist ✅

# E2E test
cd proximity2/e2e_tests
pytest test_settings.py -v

# Check no localStorage references
grep -r "localStorage" proximity2/frontend/src/lib/components/settings/
# Expected: No matches found ✅

┌─────────────────────────────────────────────────────────────────────────┐
│  PRODUCTION DEPLOYMENT CHECKLIST                                         │
└─────────────────────────────────────────────────────────────────────────┘

    ✅ API endpoints implemented and tested
    ✅ JWT authentication working
    ✅ Admin authorization enforced
    ✅ Input validation on frontend and backend
    ✅ Database migrations applied
    ✅ Error handling comprehensive
    ✅ Logging in place (console.log for debugging)
    ✅ Sentry integration active
    ✅ CORS configured for production
    ✅ Environment variables set
    ✅ SSL/TLS enabled (HTTPS)
    ✅ Database backups configured

┌─────────────────────────────────────────────────────────────────────────┐
│  STATUS: PRODUCTION READY ✅                                             │
└─────────────────────────────────────────────────────────────────────────┘
```
