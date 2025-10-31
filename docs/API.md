# REST API Reference

## Overview

Proximity provides a comprehensive REST API for all application management operations. The API is built with Django Ninja and secured with JWT authentication.

## Base URL

```
https://your-proximity-domain.com/api/
```

## Authentication

All API requests require authentication via JWT tokens.

### Login

```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response (200 OK):**
```json
{
  "key": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "your-username",
    "email": "user@example.com"
  }
}
```

### Using Authentication

Include the token in request headers:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

Or the token will be stored in an HTTP-only cookie: `proximity-auth-cookie`

## API Endpoints

### Authentication Endpoints

#### Logout
```http
POST /api/auth/logout/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

#### Get Current User
```http
GET /api/auth/user/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "your-username",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Application Endpoints

#### List Applications
```http
GET /api/apps/
Authorization: Bearer {token}
```

**Query Parameters:**
- `status` - Filter by status (deploying, running, stopping, stopped, error)
- `owner` - Filter by owner ID
- `host_id` - Filter by Proxmox host ID

**Response (200 OK):**
```json
{
  "total": 5,
  "applications": [
    {
      "id": "app-001",
      "catalog_id": "nginx",
      "name": "My Web Server",
      "hostname": "web-01.local",
      "status": "running",
      "lxc_id": 101,
      "url": "http://web-01.local",
      "created_at": "2025-10-31T10:00:00Z",
      "owner_id": 1
    }
  ]
}
```

#### Create Application
```http
POST /api/apps/
Authorization: Bearer {token}
Content-Type: application/json

{
  "catalog_id": "nginx",
  "hostname": "web-02",
  "config": {
    "port": 8080,
    "ssl": true
  },
  "environment": {
    "APP_ENV": "production"
  }
}
```

**Response (202 Accepted):**
```json
{
  "id": "app-002",
  "status": "deploying",
  "message": "Application deployment started for nginx"
}
```

#### Get Application Details
```http
GET /api/apps/{app_id}/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": "app-001",
  "catalog_id": "nginx",
  "name": "My Web Server",
  "hostname": "web-01.local",
  "status": "running",
  "lxc_id": 101,
  "url": "http://web-01.local",
  "iframe_url": "http://web-01.local:8080",
  "public_port": 8080,
  "internal_port": 80,
  "node": "pve",
  "config": { /* ... */ },
  "environment": { /* ... */ },
  "created_at": "2025-10-31T10:00:00Z",
  "updated_at": "2025-10-31T10:30:00Z",
  "owner_id": 1
}
```

#### Update Application
```http
PATCH /api/apps/{app_id}/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Name",
  "config": { /* ... */ }
}
```

**Response (200 OK):**
```json
{
  "id": "app-001",
  "status": "running",
  /* ... full application object ... */
}
```

#### Delete Application
```http
DELETE /api/apps/{app_id}/
Authorization: Bearer {token}
```

**Response (202 Accepted):**
```json
{
  "id": "app-001",
  "status": "removing",
  "message": "Application deletion started"
}
```

### Backup Endpoints

#### List Backups
```http
GET /api/apps/{app_id}/backups/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "total": 3,
  "backups": [
    {
      "id": 1,
      "application_id": "app-001",
      "file_name": "vzdump-lxc-101-2025_10_31-10_00_00.tar.zst",
      "storage_name": "local",
      "size": 524288000,
      "status": "completed",
      "backup_type": "snapshot",
      "compression": "zstd",
      "created_at": "2025-10-31T10:00:00Z"
    }
  ]
}
```

#### Create Backup
```http
POST /api/apps/{app_id}/backups/
Authorization: Bearer {token}
Content-Type: application/json

{
  "backup_type": "snapshot",
  "compression": "zstd"
}
```

**Response (202 Accepted):**
```json
{
  "id": 4,
  "status": "creating",
  "message": "Backup creation started for My Web Server"
}
```

#### Get Backup Details
```http
GET /api/apps/{app_id}/backups/{backup_id}/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "application_id": "app-001",
  "file_name": "vzdump-lxc-101-2025_10_31-10_00_00.tar.zst",
  "size": 524288000,
  "status": "completed",
  "created_at": "2025-10-31T10:00:00Z"
}
```

#### Restore from Backup
```http
POST /api/apps/{app_id}/backups/{backup_id}/restore/
Authorization: Bearer {token}
```

**Response (202 Accepted):**
```json
{
  "backup_id": 1,
  "application_id": "app-001",
  "status": "restoring",
  "message": "Restore operation started"
}
```

#### Delete Backup
```http
DELETE /api/apps/{app_id}/backups/{backup_id}/
Authorization: Bearer {token}
```

**Response (202 Accepted):**
```json
{
  "backup_id": 1,
  "status": "deleting",
  "message": "Backup deletion started"
}
```

#### Get Backup Statistics
```http
GET /api/apps/{app_id}/backups/stats
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "total_backups": 5,
  "completed_backups": 4,
  "failed_backups": 0,
  "in_progress_backups": 1,
  "total_size_gb": 2.5,
  "average_size_mb": 512.0
}
```

### Catalog Endpoints

#### List All Applications
```http
GET /api/catalog/
```

**Response (200 OK):**
```json
{
  "total": 15,
  "applications": [
    {
      "id": "nginx",
      "name": "Nginx Web Server",
      "version": "1.25.0",
      "description": "High-performance web server",
      "category": "Web Servers",
      "min_memory": 256,
      "min_cpu": 1,
      "tags": ["web", "server", "http"]
    }
  ]
}
```

#### Get Catalog Item
```http
GET /api/catalog/{app_id}/
```

**Response (200 OK):**
```json
{
  "id": "nginx",
  "name": "Nginx Web Server",
  "version": "1.25.0",
  "description": "High-performance web server",
  "category": "Web Servers",
  "docker_compose": { /* ... */ },
  "ports": [80, 443],
  "volumes": ["/etc/nginx"],
  "environment": { /* ... */ },
  "min_memory": 256,
  "min_cpu": 1,
  "tags": ["web", "server"]
}
```

#### List Categories
```http
GET /api/catalog/categories/
```

**Response (200 OK):**
```json
{
  "categories": [
    "Web Servers",
    "Databases",
    "Cache",
    "CMS",
    "Development"
  ]
}
```

#### Search Applications
```http
GET /api/catalog/search/?q=web
```

**Response (200 OK):**
```json
{
  "total": 3,
  "applications": [
    /* matching applications */
  ]
}
```

#### Filter by Category
```http
GET /api/catalog/category/Web%20Servers/
```

**Response (200 OK):**
```json
{
  "total": 5,
  "applications": [
    /* web server applications */
  ]
}
```

#### Get Catalog Statistics
```http
GET /api/catalog/stats/
```

**Response (200 OK):**
```json
{
  "total_apps": 15,
  "total_categories": 5,
  "last_updated": "2025-10-31T10:00:00Z"
}
```

## HTTP Status Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful request completed |
| 201 | Created | Resource successfully created |
| 202 | Accepted | Request accepted, processing async |
| 204 | No Content | Successful request with no response |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Operation conflicts with current state |
| 422 | Unprocessable Entity | Request validation failed |
| 500 | Server Error | Unexpected server error |
| 502 | Bad Gateway | Proxmox connection error |

## Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "status": "error"
}
```

## Rate Limiting

Currently no rate limiting is implemented, but it may be added in future versions.

## Pagination

Not currently implemented. All list endpoints return complete results.

## Filtering

Some endpoints support filtering via query parameters:
- `status` - Application status
- `owner` - User ID
- `host_id` - Proxmox host ID

## Sorting

Currently not supported. Results are returned in creation order (newest first).

## WebSockets / Real-time Updates

Currently not implemented. The frontend polls for status updates.

## API Versioning

The current API version is 1.0. The base path `/api/` does not include version information.

## Examples

### Example: Complete Workflow

```bash
# 1. Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Response: {"key": "token123..."}

# 2. List applications
curl http://localhost:8000/api/apps/ \
  -H "Authorization: Bearer token123..."

# 3. Deploy new application
curl -X POST http://localhost:8000/api/apps/ \
  -H "Authorization: Bearer token123..." \
  -H "Content-Type: application/json" \
  -d '{
    "catalog_id":"nginx",
    "hostname":"web-prod",
    "config":{"port":8080}
  }'

# Response: {"id":"app-001","status":"deploying"}

# 4. Wait for deployment
sleep 30

# 5. Get application details
curl http://localhost:8000/api/apps/app-001/ \
  -H "Authorization: Bearer token123..."

# 6. Create backup
curl -X POST http://localhost:8000/api/apps/app-001/backups/ \
  -H "Authorization: Bearer token123..." \
  -H "Content-Type: application/json" \
  -d '{"backup_type":"snapshot"}'
```

## SDK / Client Libraries

No official SDKs are provided yet. The API can be consumed using standard HTTP clients.

---

**API Version:** 1.0
**Last Updated:** October 31, 2025
**Status:** ✅ Complete and Current
