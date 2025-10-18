# Proximity 2.0 - EPIC 2 Quick Test Guide

## Prerequisites

1. **Proxmox Host Configured**:
   ```bash
   # Start the stack
   cd /Users/fab/GitHub/proximity/proximity2
   docker-compose up -d
   
   # Check services are running
   docker-compose ps
   ```

2. **Database Initialized**:
   ```bash
   # Run migrations
   docker-compose exec backend python manage.py migrate
   
   # Create superuser
   docker-compose exec backend python manage.py createsuperuser
   ```

3. **Add Proxmox Host via API**:
   - Go to: http://localhost:8000/api/docs
   - Authenticate (use superuser credentials)
   - POST `/api/proxmox/hosts` with your Proxmox details

## Test Scenarios

### Scenario 1: Deploy Your First App

#### Step 1: Create Application

**Request**:
```bash
curl -X POST http://localhost:8000/api/apps/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "catalog_id": "nginx",
    "hostname": "my-nginx-test",
    "config": {
      "memory": 2048,
      "cores": 2,
      "disk_size": "8",
      "ostemplate": "local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
    },
    "environment": {}
  }'
```

**Expected Response**:
```json
{
  "id": "nginx-abc123",
  "status": "deploying",
  "hostname": "my-nginx-test",
  "public_port": 8100,
  "internal_port": 9100,
  ...
}
```

#### Step 2: Monitor Deployment

**Watch Logs**:
```bash
curl http://localhost:8000/api/apps/nginx-abc123/logs
```

**Expected Log Progression**:
1. "Starting deployment of my-nginx-test"
2. "Allocating VMID..."
3. "Allocated VMID: 100"
4. "Creating LXC container..."
5. "LXC container created"
6. "Starting LXC container..."
7. "Container started, configuring application..."
8. "Deployment complete"

#### Step 3: Check Application Status

```bash
curl http://localhost:8000/api/apps/nginx-abc123
```

**Expected**: `"status": "running"`

#### Step 4: Check Celery Worker Logs

```bash
docker-compose logs -f celery_worker
```

You should see detailed task execution logs.

### Scenario 2: Application Lifecycle Management

#### Stop the Application

```bash
curl -X POST http://localhost:8000/api/apps/nginx-abc123/action \
  -H "Content-Type: application/json" \
  -d '{"action": "stop"}'
```

**Expected**: Container stops, status → "stopped"

#### Start the Application

```bash
curl -X POST http://localhost:8000/api/apps/nginx-abc123/action \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'
```

**Expected**: Container starts, status → "running"

#### Restart the Application

```bash
curl -X POST http://localhost:8000/api/apps/nginx-abc123/action \
  -H "Content-Type: application/json" \
  -d '{"action": "restart"}'
```

**Expected**: Stop → Start sequence

#### Delete the Application

```bash
curl -X POST http://localhost:8000/api/apps/nginx-abc123/action \
  -H "Content-Type: application/json" \
  -d '{"action": "delete"}'
```

**Expected**: 
- LXC container deleted from Proxmox
- Ports released
- Application record removed

### Scenario 3: Port Management

#### Check Port Usage

```python
# In Django shell
docker-compose exec backend python manage.py shell

from apps.applications.port_manager import PortManagerService

pm = PortManagerService()
print(pm.get_port_range_usage())
```

**Expected Output**:
```python
{
    'public': {
        'used': 3,
        'available': 897,
        'total': 900,
        'range': '8100-8999'
    },
    'internal': {
        'used': 3,
        'available': 897,
        'total': 900,
        'range': '9100-9999'
    }
}
```

### Scenario 4: List Applications

#### Get All Applications

```bash
curl http://localhost:8000/api/apps/
```

#### Filter by Status

```bash
curl "http://localhost:8000/api/apps/?status=running"
curl "http://localhost:8000/api/apps/?status=deploying"
```

#### Search Applications

```bash
curl "http://localhost:8000/api/apps/?search=nginx"
```

#### Pagination

```bash
curl "http://localhost:8000/api/apps/?page=1&per_page=10"
```

## Monitoring

### Check Celery Worker Health

```bash
# View worker logs
docker-compose logs -f celery_worker

# Check active tasks
docker-compose exec backend celery -A proximity inspect active

# Check scheduled tasks
docker-compose exec backend celery -A proximity inspect scheduled
```

### Check Database

```bash
# PostgreSQL
docker-compose exec db psql -U proximity -d proximity

# List applications
SELECT id, name, hostname, status FROM applications;

# List deployment logs
SELECT app_id, level, message, step, timestamp 
FROM deployment_logs 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Check Redis

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check task queue
KEYS celery*

# Monitor commands in real-time
MONITOR
```

## Troubleshooting

### Problem: Task Not Starting

**Check**:
```bash
# Is Celery worker running?
docker-compose ps celery_worker

# Are there errors in logs?
docker-compose logs celery_worker

# Is Redis accessible?
docker-compose exec backend python -c "import redis; r=redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

### Problem: LXC Creation Fails

**Check**:
```bash
# Proxmox connectivity
curl -k https://your-proxmox-host:8006/api2/json/version

# OS template exists
pvesh get /nodes/{node}/storage/local/content --content vztmpl

# Sufficient storage
pvesh get /nodes/{node}/storage
```

### Problem: Port Conflicts

**Check**:
```python
from apps.applications.models import Application

# Find duplicate ports
from django.db.models import Count
Application.objects.values('public_port').annotate(count=Count('id')).filter(count__gt=1)
```

## Interactive API Testing

Visit **http://localhost:8000/api/docs** for interactive Swagger documentation.

You can:
- 🔐 Authenticate with JWT
- 📝 Try all endpoints
- 📖 See request/response schemas
- 🧪 Test directly in browser

## Expected Performance

**Deployment Times** (approximate):
- LXC Creation: 10-30 seconds
- Container Start: 5-10 seconds
- Total First Deploy: 30-60 seconds

**API Response Times**:
- List Apps: < 100ms
- Create App (trigger): < 200ms
- Get Logs: < 100ms
- Actions (trigger): < 100ms

## Success Criteria

✅ **Deployment Flow Works**:
- Application record created
- Ports allocated
- LXC container created in Proxmox
- Container started
- Status updated to "running"

✅ **Lifecycle Management Works**:
- Start/stop/restart commands execute
- Status updates correctly
- Logs are recorded

✅ **Port Management Works**:
- No duplicate ports
- Ports released on deletion
- Statistics accurate

✅ **Error Handling Works**:
- Failed deployments mark status as "error"
- Retries attempted automatically
- Errors logged properly

## Next: Adding App Catalog

Once this is working, we'll add:
1. Catalog service (load from JSON)
2. Frontend dashboard
3. App Store UI
4. Deployment wizard

---

**Current Status**: Core deployment flow ready for testing ✅
