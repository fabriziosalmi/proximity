# Safe Command Quick Reference

## Command Overview

All commands are **read-only** and **predefined**. No arbitrary command execution is allowed.

---

## Command: logs

**Description:** Get Docker Compose logs from the application container

**Parameters:**
- `tail` (optional): Number of log lines to retrieve (1-1000, default: 100)
- `service_name` (optional): Specific service to get logs from

**Examples:**
```bash
# Get last 100 lines of all logs
GET /api/v1/apps/{app_id}/command/logs

# Get last 50 lines
GET /api/v1/apps/{app_id}/command/logs?tail=50

# Get logs from specific service
GET /api/v1/apps/{app_id}/command/logs?tail=100&service_name=web
```

**Use Cases:**
- Debugging application errors
- Monitoring application output
- Checking service health

---

## Command: status

**Description:** Get Docker Compose container status

**Parameters:** None

**Example:**
```bash
GET /api/v1/apps/{app_id}/command/status
```

**Output:**
```
NAME                IMAGE               STATUS      PORTS
nginx-nginx-01-web  nginx:latest       Up 2 hours  0.0.0.0:80->80/tcp
```

**Use Cases:**
- Check if containers are running
- Verify port mappings
- Check container uptime

---

## Command: disk

**Description:** Get disk usage information (df -h)

**Parameters:** None

**Example:**
```bash
GET /api/v1/apps/{app_id}/command/disk
```

**Output:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       20G   5.2G   14G  28% /
tmpfs           2.0G     0  2.0G   0% /dev/shm
```

**Use Cases:**
- Check available disk space
- Diagnose "disk full" errors
- Monitor storage usage

---

## Command: processes

**Description:** Get list of running processes (ps aux)

**Parameters:** None

**Example:**
```bash
GET /api/v1/apps/{app_id}/command/processes
```

**Use Cases:**
- Check if services are running
- Monitor resource usage by process
- Debug hung processes

---

## Command: memory

**Description:** Get memory usage information (free -h)

**Parameters:** None

**Example:**
```bash
GET /api/v1/apps/{app_id}/command/memory
```

**Output:**
```
              total        used        free      shared  buff/cache   available
Mem:          3.8Gi       1.2Gi       1.8Gi        50Mi       800Mi       2.4Gi
Swap:            0B          0B          0B
```

**Use Cases:**
- Check available memory
- Diagnose OOM errors
- Monitor memory usage

---

## Command: network

**Description:** Get network interface information (ip addr show)

**Parameters:** None

**Example:**
```bash
GET /api/v1/apps/{app_id}/command/network
```

**Use Cases:**
- Verify IP address configuration
- Check network connectivity
- Debug network issues

---

## Command: images

**Description:** Get list of Docker images

**Parameters:** None

**Example:**
```bash
GET /api/v1/apps/{app_id}/command/images
```

**Output:**
```
REPOSITORY    TAG       IMAGE ID       CREATED        SIZE
nginx         latest    a6bd71f48f68   2 weeks ago    187MB
redis         7-alpine  3900abf41552   3 weeks ago    32.3MB
```

**Use Cases:**
- Check which images are present
- Verify image versions
- Monitor image disk usage

---

## Command: volumes

**Description:** Get list of Docker volumes

**Parameters:** None

**Example:**
```bash
GET /api/v1/apps/{app_id}/command/volumes
```

**Use Cases:**
- Check persistent data volumes
- Verify volume mounts
- Diagnose data persistence issues

---

## Command: config

**Description:** Get Docker Compose configuration

**Parameters:** None

**Example:**
```bash
GET /api/v1/apps/{app_id}/command/config
```

**Output:** Parsed docker-compose.yml with resolved variables

**Use Cases:**
- Verify configuration is correct
- Check environment variables
- Debug service definitions

---

## Command: system

**Description:** Get system information (uname, uptime, OS version)

**Parameters:** None

**Example:**
```bash
GET /api/v1/apps/{app_id}/command/system
```

**Output:**
```
Linux nginx-01 5.15.0-76-generic #83-Ubuntu SMP x86_64 GNU/Linux
 14:23:45 up 5 days,  3:42,  0 users,  load average: 0.15, 0.10, 0.08
NAME="Alpine Linux"
ID=alpine
VERSION_ID=3.22
```

**Use Cases:**
- Check OS version
- Verify system uptime
- Check kernel version

---

## API Response Format

All commands return a JSON response:

```json
{
  "success": true,
  "command": "logs",
  "app_id": "nginx-nginx-01",
  "app_name": "nginx",
  "output": "... command output ...",
  "timestamp": "2025-10-04T14:23:45.123456"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Command execution failed",
  "detail": "Connection timeout"
}
```

---

## Security Notes

✅ **All commands are read-only** - Cannot modify container state  
✅ **Predefined only** - No arbitrary command execution  
✅ **Audited** - All executions logged to database  
✅ **Authenticated** - Requires valid JWT token  
✅ **Validated** - Parameters sanitized and validated  

⚠️ **Rate Limiting** - Consider implementing rate limits in production  
⚠️ **Timeouts** - All commands timeout after 30 seconds  

---

## Common Workflows

### Debugging a Failed Deployment

1. Check container status: `status`
2. View recent logs: `logs?tail=50`
3. Check disk space: `disk`
4. Verify memory: `memory`

### Monitoring Application Health

1. Check uptime: `status`
2. View recent logs: `logs?tail=100`
3. Check processes: `processes`
4. Monitor resources: `memory` and `disk`

### Investigating Performance Issues

1. Check system info: `system`
2. View running processes: `processes`
3. Check memory usage: `memory`
4. Review application logs: `logs`

---

## Integration Examples

### Python
```python
import requests

def get_app_logs(app_id: str, tail: int = 100):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"http://localhost:8765/api/v1/apps/{app_id}/command/logs",
        headers=headers,
        params={"tail": tail}
    )
    return response.json()
```

### JavaScript
```javascript
async function getAppStatus(appId) {
    const response = await fetch(
        `http://localhost:8765/api/v1/apps/${appId}/command/status`,
        {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );
    return await response.json();
}
```

### cURL
```bash
# Set token
TOKEN="your_jwt_token"

# Get logs with specific parameters
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8765/api/v1/apps/nginx-01/command/logs?tail=50&service_name=web"

# Get container status
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8765/api/v1/apps/nginx-01/command/status"
```

---

## Related Documentation

- [Security Refactoring Documentation](./SECURITY_REFACTORING_SAFE_COMMANDS.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [API Documentation](./api.md) (if exists)

---

**Last Updated:** October 4, 2025
