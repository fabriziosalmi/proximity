# First Steps with Proximity

## Welcome!

This guide walks you through your first deployment with Proximity. We'll deploy a simple web server and explore the basic features.

## Prerequisites

- Proximity installed and running (see [Installation Guide](./INSTALLATION.md))
- Access to a Proxmox host with available resources
- Administrator account created

## Step 1: Login

### Web UI Login

1. Navigate to your Proximity instance (default: `http://localhost:3000`)
2. Enter your username and password
3. Click **Sign In**

You should see the **Dashboard** with system information.

### API Authentication

To use the API, you'll need a token:

```bash
# Get your JWT token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'

# Response
{
  "key": "your-jwt-token-here"
}

# Save token for later use
TOKEN="your-jwt-token-here"
```

## Step 2: Configure Proxmox Host

### Via Web UI

1. Go to **Settings** → **Proxmox Hosts**
2. Click **Add New Host**
3. Fill in the details:
   - **Name:** pve (or your node name)
   - **Hostname/IP:** 192.168.1.100
   - **Port:** 8006
   - **Username:** root@pam
   - **Password:** your-proxmox-password
4. Click **Test Connection**
5. Click **Save**

### Via API

```bash
curl -X POST http://localhost:8000/api/proxmox/hosts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pve",
    "host": "192.168.1.100",
    "port": 8006,
    "user": "root@pam",
    "password": "your-password",
    "is_active": true
  }'
```

## Step 3: Browse the Catalog

The application catalog contains pre-configured applications ready to deploy.

### Via Web UI

1. Go to **Catalog**
2. Browse available applications
3. Click on an app to see details:
   - Description
   - Resource requirements
   - Configuration options
   - Available versions

### Via API

```bash
# List all applications
curl http://localhost:8000/api/catalog/ \
  -H "Authorization: Bearer $TOKEN"

# Get specific app details
curl http://localhost:8000/api/catalog/nginx/ \
  -H "Authorization: Bearer $TOKEN"

# Browse by category
curl http://localhost:8000/api/catalog/categories/ \
  -H "Authorization: Bearer $TOKEN"

# Search apps
curl "http://localhost:8000/api/catalog/search?q=web" \
  -H "Authorization: Bearer $TOKEN"
```

## Step 4: Deploy Your First Application

Let's deploy **Nginx** web server.

### Via Web UI

1. Go to **Applications** → **New Application**
2. Select **Nginx** from the catalog
3. Configure deployment:
   - **Hostname:** my-webserver
   - **Port:** 8080 (web port)
   - **Configuration:** (leave defaults)
4. Click **Deploy**
5. Wait for deployment to complete (2-3 minutes)

### Via API

```bash
# Deploy Nginx
curl -X POST http://localhost:8000/api/apps/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "catalog_id": "nginx",
    "hostname": "my-webserver",
    "config": {
      "port": 8080
    }
  }'

# Response (202 Accepted)
{
  "id": "app-001",
  "status": "deploying",
  "message": "Application deployment started for nginx"
}

# Check deployment status
APP_ID="app-001"
curl http://localhost:8000/api/apps/$APP_ID/ \
  -H "Authorization: Bearer $TOKEN"
```

### Monitor Deployment

```bash
# Poll status (every 5 seconds)
while true; do
  curl http://localhost:8000/api/apps/$APP_ID/ \
    -H "Authorization: Bearer $TOKEN" | jq '.status'
  sleep 5
done

# Stop when status changes to "running"
```

## Step 5: Access Your Application

Once deployment is complete:

1. Go to **Applications**
2. Click on **my-webserver**
3. Click **Open Application**
4. You should see the Nginx welcome page!

Or directly in a browser:
```
http://my-webserver.local:8080/
```

## Step 6: Create a Backup

Let's back up your application.

### Via Web UI

1. Go to **Applications** → **my-webserver**
2. Click **Backups** tab
3. Click **Create Backup**
4. Select backup type: "Snapshot"
5. Click **Create**
6. Wait for backup to complete

### Via API

```bash
# Create backup
curl -X POST http://localhost:8000/api/apps/$APP_ID/backups/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "backup_type": "snapshot",
    "compression": "zstd"
  }'

# Response (202 Accepted)
{
  "id": 1,
  "status": "creating",
  "message": "Backup creation started"
}

# Check backup status
curl http://localhost:8000/api/apps/$APP_ID/backups/ \
  -H "Authorization: Bearer $TOKEN"
```

## Step 7: Restore from Backup

Let's simulate a failure and restore from backup.

### Via Web UI

1. Go to **Applications** → **my-webserver** → **Backups**
2. Find your backup in the list
3. Click the **...** menu → **Restore**
4. Confirm restoration
5. Wait for restore to complete

### Via API

```bash
# Restore from backup
BACKUP_ID=1

curl -X POST http://localhost:8000/api/apps/$APP_ID/backups/$BACKUP_ID/restore/ \
  -H "Authorization: Bearer $TOKEN"

# Response (202 Accepted)
{
  "status": "restoring",
  "message": "Restore operation started"
}
```

## Step 8: Delete Application

When you're done testing:

### Via Web UI

1. Go to **Applications** → **my-webserver**
2. Click **Delete Application**
3. Confirm deletion
4. Wait for deletion to complete

### Via API

```bash
curl -X DELETE http://localhost:8000/api/apps/$APP_ID/ \
  -H "Authorization: Bearer $TOKEN"

# Response (202 Accepted)
{
  "status": "removing",
  "message": "Application deletion started"
}
```

## Next: Try More Applications

Now that you've deployed your first app, try:

1. **PostgreSQL** - Database server
2. **Redis** - Cache server
3. **Adminer** - Database management UI
4. **Minecraft Server** - Game server

## Troubleshooting

### Deployment Failed

1. Check **Activity Log** for error messages
2. Verify Proxmox host is online and configured
3. Ensure sufficient resources (CPU, RAM, disk)
4. Check application logs in **Applications** → **Logs**

### Cannot Access Application

1. Verify application status is **running**
2. Check network connectivity
3. Verify port is not blocked by firewall
4. Check DNS resolution for hostname

### Backup Failed

1. Verify sufficient disk space for backup
2. Check Proxmox storage is accessible
3. Ensure backup storage is configured
4. Check application logs

## Common Commands

```bash
# List all applications
curl http://localhost:8000/api/apps/ -H "Authorization: Bearer $TOKEN"

# Get application status
curl http://localhost:8000/api/apps/$APP_ID/ -H "Authorization: Bearer $TOKEN"

# List all backups
curl http://localhost:8000/api/apps/$APP_ID/backups/ \
  -H "Authorization: Bearer $TOKEN"

# Check system health
curl http://localhost:8000/api/health/ -H "Authorization: Bearer $TOKEN"
```

## Learning Resources

- **[API Reference](./API.md)** - Complete API documentation
- **[Architecture Guide](./ARCHITECTURE.md)** - System design
- **[Troubleshooting](./TROUBLESHOOTING.md)** - Common issues
- **[Development Guide](./DEVELOPMENT.md)** - Contributing code

## Next Steps

1. Deploy different applications
2. Explore **Settings** and configuration options
3. Read the [Development Guide](./DEVELOPMENT.md) to contribute
4. Check out [Advanced Deployment](./DEPLOYMENT.md) options

---

**First Steps Version:** 1.0
**Last Updated:** October 31, 2025
**Status:** ✅ Ready to Deploy
