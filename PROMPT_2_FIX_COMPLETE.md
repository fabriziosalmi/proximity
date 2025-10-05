# PROMPT #2 FIX COMPLETE ✅

## Objective
Fix 5 failing clone_app tests by implementing proper cloning logic with exception handling, hostname validation, and data format preservation.

## Test Results
- **Before**: 248/259 tests passing (95.8%)
- **After**: 253/259 tests passing (97.7%)
- **Improvement**: +5 tests fixed (+1.9% pass rate)

## Tests Fixed
All 5 tests in `TestCloneApp` class now passing:

1. ✅ **test_clone_app_success**: Main clone functionality test
2. ✅ **test_clone_app_source_not_found**: Proper AppNotFoundError exception
3. ✅ **test_clone_app_duplicate_hostname**: Proper AppAlreadyExistsError exception
4. ✅ **test_clone_app_proxmox_failure_cleanup**: Rollback and cleanup on failure
5. ✅ **test_clone_app_copies_all_properties**: All app properties copied correctly

## Root Causes Identified

### Issue #1: Exception Handling
**Problem**: `clone_app()` wasn't properly raising `AppNotFoundError` when source app didn't exist
**Root Cause**: Function called `get_app()` without try/except, generic exceptions were propagated
**Impact**: test_clone_app_source_not_found failed

### Issue #2: Hostname Duplicate Check
**Problem**: Clone allowed duplicate hostnames, checked by app_id instead of hostname
**Root Cause**: Database query used `filter(DBApp.id == new_app_id)` instead of `filter(DBApp.hostname == new_hostname)`
**Impact**: test_clone_app_duplicate_hostname failed

### Issue #3: Data Format Preservation
**Problem**: Cloned apps had wrong data formats:
- Volumes: source had dict list `[{'host_path': ..., 'container_path': ...}]` but clone had string list `['/data:/app']`
- Ports: source had string keys `{'80': 80}` but clone had int keys `{80: 80}`

**Root Cause**: Complex multi-step issue:
1. Test fixture creates DBApp with int-key ports and dict volumes
2. SQLite JSON columns convert int dict keys → string keys during database save/load
3. `get_app()` returns App schema, which uses `_db_app_to_schema()` to convert dict volumes → string volumes
4. `clone_app()` used the converted App schema data instead of original DBApp data
5. Pydantic App schema forced types: `Dict[int, int]` for ports, `List[str]` for volumes

**Impact**: test_clone_app_success and test_clone_app_copies_all_properties failed

## Solutions Implemented

### Fix #1: Enhanced Exception Handling (Lines 678-688)
```python
# Get source app from database to preserve original data formats
source_db_app = self.db.query(DBApp).filter(DBApp.id == source_app_id).first()
if not source_db_app:
    raise AppNotFoundError(
        f"Source app '{source_app_id}' not found",
        details={"source_app_id": source_app_id}
    )
```
**Result**: Properly raises AppNotFoundError with details when source app doesn't exist

### Fix #2: Hostname Validation (Lines 691-698)
```python
# Check if target hostname already exists
new_app_id = f"{source_app.catalog_id}-{new_hostname}"
existing = self.db.query(DBApp).filter(DBApp.hostname == new_hostname).first()
if existing:
    raise AppAlreadyExistsError(
        f"Application with hostname '{new_hostname}' already exists",
        details={"hostname": new_hostname, "existing_app_id": existing.id}
    )
```
**Result**: Properly validates hostname uniqueness before cloning

### Fix #3: Data Format Preservation (Multi-step fix)

**Step 3a**: Query source DBApp directly (Lines 678-680)
```python
# Get source app from database to preserve original data formats
source_db_app = self.db.query(DBApp).filter(DBApp.id == source_app_id).first()
```
**Reason**: Get original database formats before schema conversion

**Step 3b**: Preserve original data formats (Lines 768-778)
```python
# Preserve data formats exactly as they are in source database
# Use source_db_app to get original dict/int formats before schema conversion
cloned_ports = source_db_app.ports if source_db_app.ports else {}
cloned_volumes = source_db_app.volumes if source_db_app.volumes else []
cloned_config = source_db_app.config if source_db_app.config else {}
cloned_environment = source_db_app.environment if source_db_app.environment else {}

# Convert volumes to string format for App schema (expects List[str])
volumes_for_schema = cloned_volumes
if cloned_volumes and isinstance(cloned_volumes[0], dict):
    volumes_for_schema = [f"{v.get('host_path', '')}:{v.get('container_path', '')}" for v in cloned_volumes]
```
**Reason**: Preserve database formats for saving, convert only for App schema creation

**Step 3c**: Update App schema to accept both formats (backend/models/schemas.py lines 103-105)
```python
ports: Union[Dict[int, int], Dict[str, int]] = Field(default_factory=dict, description="Port mappings (container:host)")
volumes: Union[List[str], List[Dict[str, str]]] = Field(default_factory=list, description="Mounted volumes")
```
**Reason**: Allow App schema to accept both database formats (string keys, dict volumes) and API formats (int keys, string volumes)

**Step 3d**: Preserve volumes in _db_app_to_schema (Lines 83-86)
```python
def _db_app_to_schema(self, db_app: DBApp) -> App:
    """Convert database App model to Pydantic schema"""
    # Keep volumes in their original format (dict list or string list)
    # The App schema now accepts both Union[List[str], List[Dict[str, str]]]
    volumes = db_app.volumes or []
```
**Reason**: Don't convert volumes to string format, preserve original database format

**Step 3e**: Return database-persisted App (Lines 818-822)
```python
self.db.refresh(db_app)

# Convert to schema with database-persisted formats
result_app = self._db_app_to_schema(db_app)

logger.info(f"✓ Successfully cloned {source_app_id} to {new_app_id}")
return result_app
```
**Reason**: Return App schema created from refreshed database object to match source format

**Result**: Cloned apps now preserve exact data formats from source:
- Dict volumes `[{'host_path': ..., 'container_path': ...}]` ✅
- String-key ports `{'80': 80}` (from SQLite JSON serialization) ✅

## Files Modified

### backend/services/app_service.py
- Lines 678-698: Enhanced exception handling and hostname validation
- Lines 768-778: Data format preservation logic
- Lines 800-822: Database save with preserved formats and schema conversion
- Lines 83-86: Modified _db_app_to_schema to preserve volume formats

### backend/models/schemas.py
- Lines 103-105: Changed App schema to use Union types for ports and volumes

## Database Behavior Understanding
Key insight discovered during implementation:
- SQLite JSON columns **automatically convert int dictionary keys to string keys** during save/load
- Example: `{80: 80}` → stored as → `{'80': 80}` after database refresh
- Dict list volumes `[{dict}]` are preserved as-is
- This behavior required Union types in schema to handle both formats

## Test Execution
```bash
pytest tests/test_app_clone_config.py::TestCloneApp -v
```

**Result**: 5 passed, 0 failed (100% of clone test suite) ✅

## Impact Assessment
- **Tests Fixed**: 5 clone_app tests
- **Pass Rate**: 95.8% → 97.7% (+1.9%)
- **Remaining Failures**: 6 tests (all in TestUpdateAppConfig)
- **Code Quality**: Enhanced exception handling, proper hostname validation, data integrity preserved
- **Schema Flexibility**: App model now accepts both API and database formats

## Next Steps - Prompt #3
Implement `update_app_config` functionality to fix remaining 6 tests:
- test_update_cpu_cores
- test_update_memory
- test_update_disk_size
- test_update_multiple_resources
- test_update_app_not_found
- test_update_failure_attempts_restart

**Target**: 259/259 tests passing (100% pass rate)
