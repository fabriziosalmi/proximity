# Proximity Codebase Analysis: Catalog Feature Structure & Failing Tests

## Executive Summary

This document provides a comprehensive analysis of the **Catalog feature** in the Proximity 2.0 application and identifies issues with the failing E2E tests. The analysis covers the catalog structure, API endpoints, data flow, and test failures.

---

## 1. CATALOG FEATURE STRUCTURE

### 1.1 Overview
The catalog system is a **JSON-file-based application registry** that allows users to browse and deploy pre-configured applications from a centralized store. It does NOT use Django ORM models.

**Key Components:**
- **Models:** No Django models (intentionally simple, file-based)
- **Schemas:** Pydantic-based validation using `CatalogAppSchema`
- **Services:** `CatalogService` singleton that loads and manages catalog data
- **API Endpoints:** REST endpoints via Django Ninja
- **Data Source:** JSON files in `/Users/fab/GitHub/proximity/catalog_data/`

---

### 1.2 File Structure

```
/Users/fab/GitHub/proximity/
├── backend/
│   └── apps/
│       └── catalog/
│           ├── __init__.py
│           ├── api.py              # REST API endpoints
│           ├── services.py          # CatalogService (singleton)
│           ├── schemas.py           # Pydantic schemas
│           ├── models.py            # Empty (file-based, no DB models)
│           ├── tests.py             # Unit tests
│           └── test_api.py          # API tests
└── catalog_data/
    └── adminer.json                 # Sample app definition
```

---

### 1.3 Database Models

**File:** `/Users/fab/GitHub/proximity/backend/apps/catalog/models.py`

**Status:** EMPTY - Contains only a docstring explaining that the catalog uses JSON files, not Django models.

```python
"""
Catalog models.

Note: This app does not use Django models, as the catalog
is loaded from JSON files on disk. This file is kept for
Django app structure compliance.
"""
```

---

### 1.4 Pydantic Schemas

**File:** `/Users/fab/GitHub/proximity/backend/apps/catalog/schemas.py`

**Core Schema: `CatalogAppSchema`**

A Pydantic model that validates application definitions with the following fields:

```python
class CatalogAppSchema(BaseModel):
    # Core identification
    id: str                           # Unique identifier
    name: str                         # Display name
    version: str                      # App version
    description: str                  # Short description

    # Visual and categorization
    icon: Optional[str]               # Icon URL
    category: str                     # Category for grouping

    # Docker configuration
    docker_compose: Dict[str, Any]    # Full docker-compose config

    # Resource requirements
    ports: List[int]                  # Exposed ports
    volumes: List[Any]                # Volume definitions
    environment: Dict[str, str]       # Default env vars

    # System requirements
    min_memory: int                   # Minimum memory in MB (≥ 0)
    min_cpu: int                      # Minimum CPU cores (≥ 1)

    # Metadata
    tags: List[str]                   # Search/filter tags
    author: Optional[str]             # App author
    website: Optional[str]            # Official website
```

**Related Schemas:**
- `DockerComposeServiceSchema`: Single service definition
- `DockerComposeSchema`: Full docker-compose structure
- `CatalogListResponse`: Response for list endpoints
- `CatalogCategoriesResponse`: Response for category endpoints

---

### 1.5 Service Layer

**File:** `/Users/fab/GitHub/proximity/backend/apps/catalog/services.py`

**Class: `CatalogService` (Singleton Pattern)**

Responsibilities:
1. **Load catalog:** Reads all JSON files from disk on initialization
2. **Validate:** Uses Pydantic to validate each app against `CatalogAppSchema`
3. **Query:** Provides methods to search, filter, and retrieve apps
4. **Reload:** Supports reloading catalog without restart

**Key Methods:**

```python
class CatalogService:
    _instance: Optional['CatalogService'] = None
    _initialized: bool = False

    def __init__(self):
        """Initialize singleton, load catalog from disk."""

    def get_all_apps() -> List[CatalogAppSchema]
        """Get all apps, sorted by name."""

    def get_app_by_id(app_id: str) -> Optional[CatalogAppSchema]
        """Get single app by ID."""

    def get_categories() -> List[str]
        """Get unique categories, sorted."""

    def search_apps(query: str) -> List[CatalogAppSchema]
        """Search apps by name, description, or tags (case-insensitive)."""

    def filter_by_category(category: str) -> List[CatalogAppSchema]
        """Filter by category (case-insensitive)."""

    def get_stats() -> Dict[str, int]
        """Get catalog statistics (total_apps, total_categories)."""

    def reload() -> None
        """Reload catalog from disk."""
```

**Initialization Flow:**
1. Service is a singleton - instantiated once globally via `catalog_service = CatalogService()`
2. On first `__init__()`: loads all JSON files from `CATALOG_DATA_PATH`
3. Validates each file against `CatalogAppSchema`
4. Invalid files are logged and skipped
5. Apps stored in-memory in `self._apps` dict (keyed by app ID)

**Configuration:**
```python
# In Django settings.py
CATALOG_DATA_PATH = BASE_DIR.parent / 'catalog_data'
```

---

### 1.6 API Endpoints

**File:** `/Users/fab/GitHub/proximity/backend/apps/catalog/api.py`

**Router Setup:**
```python
router = Router(tags=["Catalog"])
```

**Mounted at:** `/api/catalog/` (via Django Ninja in urls.py)

**Endpoints:**

| Method | Path | Summary | Response |
|--------|------|---------|----------|
| GET | `/` | List all applications | `CatalogListResponse` |
| GET | `/categories` | List all categories | `CatalogCategoriesResponse` |
| GET | `/search?q=query` | Search applications | `CatalogListResponse` |
| GET | `/category/{category}` | Filter by category | `CatalogListResponse` |
| GET | `/stats` | Get statistics | Dict with counts |
| GET | `/{app_id}` | Get app by ID | `CatalogAppSchema` or 404 |
| POST | `/reload` | Reload catalog (admin only) | Dict with message + stats |

**Example Response: `GET /api/catalog/`**
```json
{
  "total": 1,
  "applications": [
    {
      "id": "adminer",
      "name": "Adminer",
      "version": "latest",
      "description": "Full-featured database management tool in a single file",
      "icon": "https://cdn.simpleicons.org/adminer/34567C",
      "category": "Database",
      "docker_compose": { ... },
      "ports": [8080],
      "volumes": [],
      "environment": {},
      "min_memory": 128,
      "min_cpu": 1,
      "tags": ["database", "management", "mysql", "postgresql"],
      "author": "Adminer",
      "website": "https://www.adminer.org"
    }
  ]
}
```

---

### 1.7 Data Files

**Location:** `/Users/fab/GitHub/proximity/catalog_data/`

**Current Files:**
- `adminer.json` - Database management tool (742 bytes)

**Example: adminer.json**
```json
{
  "id": "adminer",
  "name": "Adminer",
  "version": "latest",
  "description": "Full-featured database management tool in a single file",
  "icon": "https://cdn.simpleicons.org/adminer/34567C",
  "category": "Database",
  "docker_compose": {
    "version": "3.8",
    "services": {
      "adminer": {
        "image": "adminer:latest",
        "environment": {
          "ADMINER_DEFAULT_SERVER": "db"
        },
        "restart": "always",
        "network_mode": "host"
      }
    }
  },
  "ports": [8080],
  "volumes": [],
  "environment": {},
  "min_memory": 128,
  "min_cpu": 1,
  "tags": ["database", "management", "mysql", "postgresql"],
  "author": "Adminer",
  "website": "https://www.adminer.org"
}
```

---

### 1.8 Integration in URL Router

**File:** `/Users/fab/GitHub/proximity/backend/proximity/urls.py`

```python
from apps.catalog.api import router as catalog_router

api = NinjaAPI(
    title="Proximity 2.0 API",
    version="2.0.0",
    auth=JWTCookieAuthenticator(),
)

api.add_router("/catalog/", catalog_router, tags=["Catalog"])

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    # ...
]
```

**Protection:** All catalog endpoints are protected by `JWTCookieAuthenticator` - requires valid session cookie or JWT token.

---

## 2. FAILING E2E TESTS

### 2.1 Overview

Four E2E tests are failing:
1. `test_clone_feature.py::test_clone_application_lifecycle`
2. `test_debug_store.py::test_debug_store_page`
3. `test_golden_path.py::test_full_app_lifecycle`
4. `test_login_console.py::test_login_with_console_logs`

**Common Failure Pattern:** Timeout waiting for `/api/apps` response (15000ms exceeded)

**Root Cause:** Tests expect `/api/catalog/` endpoint to be called, but the actual URL being requested is `/api/apps/` (different API endpoint).

---

### 2.2 Test File Details

#### **File 1: test_clone_feature.py**

**Location:** `/Users/fab/GitHub/proximity/e2e_tests/test_clone_feature.py`

**Tests:**
1. `test_clone_application_lifecycle()` - Fast test using deployed_app fixture
2. `test_clone_application_workflow()` - Full UI-driven test

**What They Do:**
- Deploy an application (Adminer)
- Clone the application with a new hostname
- Monitor clone progress until "running" status
- Verify both apps are running
- Test 3D flip animation (Living Interface)

**Failure Point:** Line 93 in `test_clone_application_lifecycle`
```python
apps_page.navigate()  # Tries to intercept /api/apps, but times out after 15s
```

**Root Cause:** `AppsPage.navigate()` waits for `/api/apps` response, but this endpoint doesn't exist in the catalog service.

---

#### **File 2: test_debug_store.py**

**Location:** `/Users/fab/GitHub/proximity/e2e_tests/test_debug_store.py`

**Test:** `test_debug_store_page()`

**What It Does:**
- Login
- Navigate to /store
- Wait for apps to load using `wait_for_apps_loaded()`
- Screenshot and inspect app cards

**Failure Point:** Line 35
```python
store_page.wait_for_apps_loaded(min_count=1, timeout=30000)
```

**Root Cause:** Test expects catalog cards with `data-testid^="catalog-card-"` but the frontend is likely not rendering them due to API issues.

---

#### **File 3: test_golden_path.py**

**Location:** `/Users/fab/GitHub/proximity/e2e_tests/test_golden_path.py`

**Tests:**
1. `test_full_app_lifecycle()` - Complete user journey
2. `test_login_only()` - Smoke test for login
3. `test_catalog_loads()` - Smoke test for catalog

**What They Do:**
- Login with unique user
- Navigate to store
- Deploy Adminer
- Monitor deployment
- Stop and start app
- Delete app

**Failure Point:** Line 120 in `test_full_app_lifecycle`
```python
store_page.wait_for_apps_loaded(min_count=1, timeout=30000)
```

**Root Cause:** Same as test_debug_store - catalog not loading properly.

---

#### **File 4: test_login_console.py**

**Location:** `/Users/fab/GitHub/proximity/e2e_tests/test_login_console.py`

**Test:** `test_login_with_console_logs()`

**What It Does:**
- Capture browser console logs
- Capture API requests/responses
- Test login form submission
- Check for error messages

**Failure Point:** Test doesn't explicitly fail on catalog, but likely affected by the same authentication/API issues.

---

### 2.3 Test Infrastructure

**Key Fixtures:**

```python
@pytest.fixture(scope="session")
def api_client() -> Generator[httpx.Client, None, None]:
    """HTTP client with cookie management and CSRF handling."""
    # Creates httpx client with self-signed cert support
    # Gets CSRF token from /api/auth/login/

@pytest.fixture
def unique_user(api_client: httpx.Client) -> Generator[Dict[str, str], None, None]:
    """Create unique test user via registration API."""
    # POST /api/auth/registration/
    # POST /api/auth/login/
    # Returns: {"username": "...", "password": "...", "user_id": ..., "access_token": ...}

@pytest.fixture
def deployed_app(api_client: httpx.Client, unique_user: dict) -> dict:
    """Deploy an app (Adminer) for testing."""
    # POST /api/apps/ to deploy an application
    # Returns: deployed app with hostname, ID, auth token, etc.

@pytest.fixture
def proxmox_host(api_client: httpx.Client) -> dict:
    """Ensure a Proxmox host exists."""
    # Interacts with /api/proxmox/ endpoints

@pytest.fixture
def base_url() -> str:
    """Base frontend URL: https://localhost:5173"""

@pytest.fixture
def test_page(page: Page, base_url: str) -> Page:
    """Playwright page with storage initialized."""
```

---

## 3. DATA FLOW ANALYSIS

### 3.1 Catalog Loading Flow (Happy Path)

```
Frontend (/store)
    ↓
1. User navigates to /store page
    ↓
2. Page loads, triggers API call
    ↓
3. Frontend calls: GET /api/catalog/
    ↓
Backend (apps/catalog/api.py)
    ↓
4. @api.get("/") handler calls catalog_service.get_all_apps()
    ↓
5. CatalogService loads from JSON files (singleton)
    ↓
6. Returns List[CatalogAppSchema]
    ↓
7. Router serializes to JSON response: {"total": N, "applications": [...]}
    ↓
8. Frontend receives response, renders catalog cards
    ↓
9. User sees apps and can click "Deploy"
```

### 3.2 Catalog vs Applications Endpoints

**IMPORTANT DISTINCTION:**

The codebase has TWO separate app-related endpoints:

| Endpoint | Purpose | File | Returns |
|----------|---------|------|---------|
| `/api/catalog/` | Browse AVAILABLE apps (store) | `apps/catalog/api.py` | `CatalogAppSchema` objects from JSON files |
| `/api/apps/` | Manage DEPLOYED apps (my apps) | `apps/applications/api.py` | User's deployed application instances |

**Test Expectation Mismatch:**
- `AppsPage.navigate()` expects `/api/apps` → deployed applications list
- `StorePage` expects `/api/catalog/` → available applications in store
- Tests are confusing which endpoint to call

---

## 4. OBVIOUS ISSUES IDENTIFIED

### Issue #1: Insufficient Catalog Data
**Severity:** MEDIUM
**Location:** `/Users/fab/GitHub/proximity/catalog_data/`

Only ONE app (adminer.json) is in the catalog. Tests expect multiple apps to be visible.

**Fix:** Add more catalog JSON files for variety.

---

### Issue #2: Test Endpoint Confusion
**Severity:** HIGH
**Location:** `e2e_tests/pages/apps_page.py` line 72

The `AppsPage.navigate()` method expects `/api/apps` response (deployed apps), but this is the wrong context. When navigating to /apps after deployment, the page should load the user's deployed apps.

**Current Code:**
```python
def navigate(self) -> 'AppsPage':
    with self.page.expect_response(
        lambda res: "/api/apps" in res.url and res.status == 200,
        timeout=15000
    ) as response_info:
        self.page.goto(f"{self.base_url}/apps")
```

**Issue:** This is correct (waiting for deployed apps list), but the backend may not be returning this response properly.

---

### Issue #3: Missing Catalog Reload Endpoint Authorization
**Severity:** LOW
**Location:** `/Users/fab/GitHub/proximity/backend/apps/catalog/api.py` line 97

The `/reload` endpoint has a TODO for admin permission check:

```python
@router.post("/reload", summary="Reload catalog from disk")
def reload_catalog(request):
    """
    Reload the catalog from disk.
    ...
    Requires admin authentication.
    """
    # TODO: Add permission check for admin users
    catalog_service.reload()
    ...
```

**Fix:** Add actual permission checking.

---

### Issue #4: Catalog Service Singleton Not Thread-Safe
**Severity:** LOW
**Location:** `/Users/fab/GitHub/proximity/backend/apps/catalog/services.py` line 30-45

The singleton implementation uses class variables but no locking:

```python
class CatalogService:
    _instance: Optional['CatalogService'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if CatalogService._initialized:
            return
        # ... load catalog ...
        CatalogService._initialized = True
```

**Issue:** If two threads initialize simultaneously, race condition possible.

**Fix:** Use `threading.Lock()` or Django's `@cached_property`.

---

### Issue #5: Tests Don't Handle Minimal Catalog Gracefully
**Severity:** MEDIUM
**Location:** Multiple test files

Tests assume at least 1-2 apps are visible in the catalog, but with only Adminer, tests checking for "Adminer" by name may fail.

---

## 5. RECENT CHANGES TO CATALOG

### Recent Commits:
1. **84fe678** - "Database migration automation, Playwright fixes, and StorePage selector corrections"
   - Likely fixed selector issues in StorePage

2. **00d896e / 0dd791b** - "Add high-star self-hosted apps"
   - Added catalog apps (but not in current catalog_data/ directory?)

3. **fa2c85f / c7ec270** - "Update app catalog to version 2.8.0 and add new applications"
   - Major catalog update

4. **a7edb35** - "Improve login flow and error handling in E2E tests"
   - Fixed HttpOnly cookie handling

5. **5cabccb** - "Implement atomic state management in AuthStore"
   - Authentication improvements

---

## 6. SUMMARY & RECOMMENDATIONS

### What Works:
✅ Catalog service is well-structured and properly integrated
✅ Pydantic validation ensures data integrity
✅ API endpoints are properly defined
✅ Singleton pattern avoids multiple loads
✅ Tests have proper fixtures and setup

### What's Broken:
❌ Only 1 catalog app available (adminer.json)
❌ Tests timeout waiting for API responses (network/timing issues)
❌ `/api/apps` endpoint may not be properly wired in applications API
❌ Frontend might not be calling the correct endpoints

### Recommended Fixes (Priority Order):

1. **Verify Backend API Responses**
   - Check that `/api/apps/` endpoint exists and returns proper JSON
   - Check that `/api/catalog/` endpoint returns proper JSON
   - Run backend tests: `pytest backend/apps/catalog/tests.py`

2. **Add More Catalog Apps**
   - Create 3-5 more JSON files in `/catalog_data/` for tests
   - Ensure they follow the `CatalogAppSchema` format

3. **Fix Test Timeout Issues**
   - Increase timeout in tests (15s → 30s) for slower CI environments
   - Add better error logging to see what response (if any) is received

4. **Fix Thread Safety**
   - Use `@cached_property` or `threading.Lock()` in `CatalogService`

5. **Add Authorization to `/reload`**
   - Implement proper admin permission check

6. **Verify Frontend Integration**
   - Check that frontend components are calling `/api/catalog/` correctly
   - Check that components are properly rendering catalog cards

---

## 7. FILE LOCATIONS REFERENCE

| Component | File Path | Status |
|-----------|-----------|--------|
| Catalog Service | `/Users/fab/GitHub/proximity/backend/apps/catalog/services.py` | ✅ Complete |
| Catalog API | `/Users/fab/GitHub/proximity/backend/apps/catalog/api.py` | ✅ Complete |
| Schemas | `/Users/fab/GitHub/proximity/backend/apps/catalog/schemas.py` | ✅ Complete |
| Models | `/Users/fab/GitHub/proximity/backend/apps/catalog/models.py` | ✅ Empty (intentional) |
| Unit Tests | `/Users/fab/GitHub/proximity/backend/apps/catalog/tests.py` | ✅ Comprehensive |
| API Tests | `/Users/fab/GitHub/proximity/backend/apps/catalog/test_api.py` | ✅ Present |
| Catalog Data | `/Users/fab/GitHub/proximity/catalog_data/` | ⚠️ Only 1 file |
| E2E Tests | `/Users/fab/GitHub/proximity/e2e_tests/` | ⚠️ 4 failing |
| Page Objects | `/Users/fab/GitHub/proximity/e2e_tests/pages/` | ✅ Present |
| Test Fixtures | `/Users/fab/GitHub/proximity/e2e_tests/conftest.py` | ✅ Well-structured |

---

**Analysis Date:** October 25, 2025
**Codebase:** Proximity 2.0
**Analysis Depth:** Full structure + recent commits + test execution
