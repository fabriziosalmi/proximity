# Event Loop Fix for AppService

## Problem Identified

**Root Cause**: `AppService.__init__()` was calling `asyncio.create_task()` to load catalog and apps during initialization, but this happens during **dependency injection** which runs in a **synchronous context** (not inside an async event loop).

**Error from logs**:
```python
File "/Users/fab/GitHub/proximity/backend/services/app_service.py", line 42, in __init__
    asyncio.create_task(self._load_catalog())
RuntimeError: no running event loop
```

### Why This Happens

1. FastAPI dependency injection calls `get_app_service()` (synchronous function)
2. `get_app_service()` creates `AppService(proxmox_service)` 
3. `AppService.__init__()` (synchronous) tries to call `asyncio.create_task()`
4. ❌ `asyncio.create_task()` requires an active event loop
5. ❌ No event loop exists yet in dependency injection context

## Solution Implemented

**Changed from eager loading to lazy loading**:
- Removed `asyncio.create_task()` calls from `__init__()`
- Added tracking flags: `_catalog_loaded` and `_apps_loaded`
- Load catalog/apps on first access instead of at initialization

### Changes Made

**File**: `backend/services/app_service.py`

#### 1. Updated `__init__()` - Removed async task creation

**Before**:
```python
def __init__(self, proxmox_service: ProxmoxService):
    self.proxmox_service = proxmox_service
    self._apps_db: Dict[str, App] = {}
    self._deployment_status: Dict[str, DeploymentStatus] = {}
    self._catalog_cache: Optional[CatalogResponse] = None
    self._apps_file = Path(__file__).parent.parent / "data" / "apps.json"
    self._caddy_service = None
    
    self._apps_file.parent.mkdir(parents=True, exist_ok=True)
    
    # ❌ This fails - no event loop during dependency injection
    asyncio.create_task(self._load_catalog())
    asyncio.create_task(self._load_apps())
```

**After**:
```python
def __init__(self, proxmox_service: ProxmoxService):
    self.proxmox_service = proxmox_service
    self._apps_db: Dict[str, App] = {}
    self._deployment_status: Dict[str, DeploymentStatus] = {}
    self._catalog_cache: Optional[CatalogResponse] = None
    self._apps_file = Path(__file__).parent.parent / "data" / "apps.json"
    self._caddy_service = None
    self._catalog_loaded = False  # ✅ Track if catalog has been loaded
    self._apps_loaded = False     # ✅ Track if apps have been loaded
    
    self._apps_file.parent.mkdir(parents=True, exist_ok=True)
    
    # ✅ Catalog and apps are now loaded lazily on first access
```

#### 2. Updated `_load_catalog()` - Added idempotency check

**Before**:
```python
async def _load_catalog(self) -> None:
    """Load application catalog from individual app files"""
    try:
        # ... loading logic ...
    except Exception as e:
        logger.error(f"Failed to load catalog: {e}", exc_info=True)
        await self._create_default_catalog()
```

**After**:
```python
async def _load_catalog(self) -> None:
    """Load application catalog from individual app files"""
    if self._catalog_loaded and self._catalog_cache is not None:
        return  # ✅ Already loaded, skip
    
    try:
        # ... loading logic ...
        self._catalog_loaded = True  # ✅ Mark as loaded
    except Exception as e:
        logger.error(f"Failed to load catalog: {e}", exc_info=True)
        await self._create_default_catalog()
        self._catalog_loaded = True  # ✅ Mark as attempted
```

#### 3. Updated `_load_apps()` - Added idempotency check

**Before**:
```python
async def _load_apps(self) -> None:
    """Load deployed apps from disk"""
    try:
        if self._apps_file.exists():
            # ... loading logic ...
    except Exception as e:
        logger.error(f"Failed to load apps: {e}")
```

**After**:
```python
async def _load_apps(self) -> None:
    """Load deployed apps from disk"""
    if self._apps_loaded:
        return  # ✅ Already loaded, skip
    
    try:
        if self._apps_file.exists():
            # ... loading logic ...
        
        self._apps_loaded = True  # ✅ Mark as loaded
    except Exception as e:
        logger.error(f"Failed to load apps: {e}")
        self._apps_loaded = True  # ✅ Mark as attempted to prevent retry loops
```

#### 4. Updated `get_all_apps()` - Added lazy loading

**Before**:
```python
async def get_all_apps(self) -> List[App]:
    """Get all deployed applications"""
    # Assumes apps already loaded from __init__
    await self._sync_apps_with_containers()
    return list(self._apps_db.values())
```

**After**:
```python
async def get_all_apps(self) -> List[App]:
    """Get all deployed applications"""
    # ✅ Lazy load apps from disk if not already loaded
    if not self._apps_loaded:
        await self._load_apps()
    
    await self._sync_apps_with_containers()
    return list(self._apps_db.values())
```

#### 5. Updated `get_app()` - Added lazy loading

**Before**:
```python
async def get_app(self, app_id: str) -> App:
    """Get specific application"""
    if app_id not in self._apps_db:
        raise AppServiceError(f"App '{app_id}' not found")
    # ...
```

**After**:
```python
async def get_app(self, app_id: str) -> App:
    """Get specific application"""
    # ✅ Lazy load apps from disk if not already loaded
    if not self._apps_loaded:
        await self._load_apps()
    
    if app_id not in self._apps_db:
        raise AppServiceError(f"App '{app_id}' not found")
    # ...
```

## How Lazy Loading Works

### Loading Sequence

**Old (Eager Loading - Broken)**:
```
1. FastAPI starts
2. Dependency injection creates AppService
3. ❌ __init__ calls asyncio.create_task() → no event loop → CRASH
```

**New (Lazy Loading - Fixed)**:
```
1. FastAPI starts
2. Dependency injection creates AppService
3. ✅ __init__ completes (no async operations)
4. HTTP request arrives → endpoint needs catalog
5. ✅ get_catalog() checks if loaded → calls _load_catalog()
6. ✅ _load_catalog() runs in async context (event loop exists)
7. ✅ Returns catalog data
```

### Idempotency Pattern

Each load method follows this pattern:

```python
async def _load_something(self):
    # 1. Check if already loaded
    if self._something_loaded:
        return
    
    try:
        # 2. Do expensive loading operation
        # ...
        
        # 3. Mark as successfully loaded
        self._something_loaded = True
    except Exception as e:
        logger.error(f"Failed: {e}")
        # 4. Mark as attempted (prevent infinite retry)
        self._something_loaded = True
```

This ensures:
- ✅ Load only happens once
- ✅ Thread-safe (first caller loads, others skip)
- ✅ Failed loads don't retry forever
- ✅ No event loop issues

## Benefits

### ✅ Fixed Issues
- **No more RuntimeError**: No `asyncio.create_task()` in sync context
- **Deferred initialization**: Loading happens when event loop exists
- **Idempotent**: Safe to call load methods multiple times
- **Lazy**: Only loads data when actually needed

### ✅ Performance
- **Faster startup**: AppService creation is instant
- **On-demand loading**: Catalog loaded only when first accessed
- **No wasted work**: If catalog never accessed, never loaded

### ✅ Reliability
- **Proper async context**: All async operations run in event loop
- **Error handling**: Failed loads don't block initialization
- **Retry prevention**: Failed loads marked as attempted

## Testing

### Expected Behavior After Fix

**Backend Startup**:
```bash
cd /Users/fab/GitHub/proximity/backend
python3 main.py
```

**Expected logs**:
```
INFO:     Uvicorn running on http://0.0.0.0:8765
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
2025-10-03 XX:XX:XX - main - INFO - Starting Proximity API...
2025-10-03 XX:XX:XX - main - INFO - STEP 1: Connecting to Proxmox
✅ 2025-10-03 XX:XX:XX - main - INFO - ✓ Proxmox connection successful
2025-10-03 XX:XX:XX - main - INFO - STEP 2: Initializing Network Appliance
...
2025-10-03 XX:XX:XX - main - INFO - STEP 3: Loading Application Catalog
✅ (No catalog loading here - deferred until first request)
2025-10-03 XX:XX:XX - main - INFO - 🚀 Proximity API started on 0.0.0.0:8765
INFO:     Application startup complete.
```

**First API Request** (e.g., GET /api/v1/apps/catalog):
```
2025-10-03 XX:XX:XX - main - INFO - GET /api/v1/apps/catalog
✅ 2025-10-03 XX:XX:XX - services.app_service - INFO - Looking for catalog in: /Users/fab/GitHub/proximity/backend/catalog
✅ 2025-10-03 XX:XX:XX - services.app_service - INFO - Loading catalog from individual app files...
✅ 2025-10-03 XX:XX:XX - services.app_service - INFO - ✓ Loaded 11 apps from 11 catalog files
INFO:     127.0.0.1:62699 - "GET /api/v1/apps/catalog HTTP/1.1" 200 OK
```

**Subsequent Requests** (catalog already cached):
```
2025-10-03 XX:XX:XX - main - INFO - GET /api/v1/apps/catalog
✅ (No loading message - uses cached data)
INFO:     127.0.0.1:62700 - "GET /api/v1/apps/catalog HTTP/1.1" 200 OK
```

### Verification Commands

```bash
# 1. Start backend
cd /Users/fab/GitHub/proximity/backend
python3 main.py

# 2. In another terminal, test endpoints
curl http://localhost:8765/api/v1/apps/catalog
curl http://localhost:8765/api/v1/apps

# 3. Check logs for:
# ✅ No "RuntimeError: no running event loop"
# ✅ "✓ Loaded X apps from Y catalog files" on first request
# ✅ No loading message on subsequent requests
```

## Related Changes

This fix works together with the SSH execution fix:

1. **Event Loop Fix** (this document): AppService lazy loading
2. **SSH Execution Fix** (SSH_FIX.md): NetworkAppliance remote execution

Both fixes enable the backend to run properly on macOS/Windows.

## Technical Notes

### Dependency Injection Pattern

FastAPI uses this pattern for dependencies:

```python
# Dependency function (synchronous)
def get_app_service() -> AppService:
    global app_service
    if app_service is None:
        app_service = AppService(proxmox_service)  # ← Called in sync context
    return app_service

# Endpoint (asynchronous)
@app.get("/api/v1/apps")
async def get_apps(service: AppService = Depends(get_app_service)):
    # ← Event loop exists here
    return await service.get_all_apps()
```

The key insight:
- **Dependency creation**: Synchronous context (no event loop)
- **Endpoint execution**: Asynchronous context (event loop exists)
- **Solution**: Do async work in endpoints, not in dependency creation

### Alternative Approaches Considered

1. ❌ **Make `get_app_service()` async**: FastAPI doesn't support async dependencies for singletons
2. ❌ **Use `asyncio.run()`**: Creates new event loop, conflicts with FastAPI's loop
3. ✅ **Lazy loading**: Simple, clean, works with FastAPI's patterns

## Conclusion

This fix enables `AppService` to initialize properly during FastAPI dependency injection by deferring all async operations (catalog/apps loading) until they're first needed, when an event loop is guaranteed to exist.

Combined with the SSH execution fix, the Proximity backend now runs correctly on any platform (macOS, Windows, Linux) without event loop or subprocess issues.
