# LXC Container Adoption Feature

## 🎯 Overview

The **Adoption Feature** allows Proximity to discover and take over management of pre-existing LXC containers on Proxmox. This is critical for onboarding users with existing Proxmox infrastructures.

## 🏗️ Architecture

### Backend Components

#### 1. Discovery Engine (`ProxmoxService.discover_unmanaged_lxc()`)

**Location**: `backend/apps/proxmox/services.py`

Discovers containers that exist on Proxmox but are not managed by Proximity.

**Algorithm**:
1. Query database for all managed container VMIDs
2. Query all Proxmox nodes for all LXC containers
3. Return the difference (unmanaged containers)

**Returns**:
```python
[
    {
        'vmid': 105,
        'name': 'adguard-existing',
        'status': 'running',
        'node': 'opti2',
        'memory': 268435456,
        'disk': 1073741824,
        'uptime': 3600,
        'cpus': 1
    },
    ...
]
```

#### 2. API Endpoints

**Location**: `backend/apps/applications/api.py`

##### GET `/api/apps/discover`

Discovers unmanaged containers.

**Query Parameters**:
- `host_id` (optional): Proxmox host ID

**Response**:
```json
[
    {
        "vmid": 201,
        "name": "existing-nginx",
        "status": "running",
        "node": "opti2",
        "memory": 536870912,
        "disk": 8350298112,
        "uptime": 282,
        "cpus": 1
    }
]
```

##### POST `/api/apps/adopt`

Adopts an existing container into Proximity management.

**Payload**:
```json
{
    "vmid": 201,
    "node": "opti2",
    "catalog_id": "adminer",
    "hostname": "my-adminer",
    "internal_port": 8080
}
```

**Required Fields**:
- `vmid`: Container VMID to adopt
- `node`: Node name where container is running
- `catalog_id`: Catalog app ID that matches this container

**Optional Fields**:
- `hostname`: Custom hostname (defaults to container name)
- `internal_port`: Internal port the app listens on (defaults to catalog port)

**Response**: Standard `ApplicationResponse` object

**Process**:
1. Validate container is not already managed
2. Fetch container info from Proxmox
3. Match with catalog app
4. Allocate public/internal ports
5. Create Application record with `adopted: true` flag
6. Create adoption log entry

### Frontend Components

#### 1. Adoption Wizard (TODO)

**Location**: `frontend/src/lib/components/adoption/AdoptionWizard.svelte`

**Flow**:
1. **Discovery Step**: Call `/api/apps/discover` and show list
2. **Matching Step**: User selects container(s) and matches with catalog apps
3. **Configuration Step**: Confirm/adjust internal ports
4. **Confirmation Step**: Review and confirm adoption
5. **Execution**: Call `/api/apps/adopt` for each selected container

#### 2. UI Triggers

- `/apps` page: "Adopt Existing Containers" button in empty state
- Operational Rack: "Adopt" button

## 📋 Usage Example

### Step 1: Discover Unmanaged Containers

```bash
curl -s http://localhost:8000/api/apps/discover | jq
```

### Step 2: Adopt a Container

```bash
curl -X POST http://localhost:8000/api/apps/adopt \
  -H "Content-Type: application/json" \
  -d '{
    "vmid": 201,
    "node": "opti2",
    "catalog_id": "adminer",
    "hostname": "my-existing-adminer",
    "internal_port": 8080
  }' | jq
```

### Step 3: Verify Adoption

```bash
curl -s http://localhost:8000/api/apps/ | jq
```

The adopted container will appear with:
- `config.adopted: true`
- `config.original_vmid: 201`
- `config.adoption_date: "2025-10-21T11:00:00Z"`

## 🎨 Frontend Implementation Plan

### Phase 1: Basic UI (MVP)

1. Add "Adopt" button to `/apps` page
2. Create simple modal with:
   - Discovery step (show list)
   - Selection + catalog matching
   - Confirm button

### Phase 2: Full Wizard

1. Multi-step wizard component
2. Port configuration UI
3. Batch adoption support
4. Progress indicators
5. Error handling with retry

### Phase 3: Advanced Features

1. Auto-detection of app type (analyze container)
2. Port scanning to detect internal ports
3. Import existing app configurations
4. Adoption history and audit logs

## 🔒 Security Considerations

- Adopted containers inherit Proximity's port mapping
- Original container configuration is preserved in `config.container_internal_port`
- Adoption is logged in deployment logs
- Users cannot adopt already-managed containers (409 Conflict)

## 🧪 Testing

### Backend Tests

```bash
# Test discovery
curl http://localhost:8000/api/apps/discover

# Test adoption with invalid VMID
curl -X POST http://localhost:8000/api/apps/adopt \
  -d '{"vmid": 999, "node": "opti2", "catalog_id": "adminer"}'
# Expected: 404 Not Found

# Test adoption of already-managed container
curl -X POST http://localhost:8000/api/apps/adopt \
  -d '{"vmid": 100, "node": "opti2", "catalog_id": "adminer"}'
# Expected: 409 Conflict
```

### Frontend Tests (TODO)

- E2E test for adoption wizard flow
- Unit tests for adoption modal components
- Integration tests for API calls

## 📈 Success Metrics

- Users can discover existing containers ✅
- Users can adopt containers into Proximity ✅
- Adopted containers work with all Proximity features (Stop/Start/Backup) 🔄
- Adoption wizard is intuitive and error-resistant 🔄

## 🚀 Next Steps

1. ✅ Backend discovery logic implemented
2. ✅ Backend adoption API implemented
3. ⏳ Frontend adoption wizard
4. ⏳ UI triggers and buttons
5. ⏳ Testing and validation
6. ⏳ Documentation and user guide

---

**Status**: Backend Complete, Frontend In Progress
**Last Updated**: 2025-10-21
