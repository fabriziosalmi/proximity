# Proximity Automated Deployment - Implementation Summary

## Overview

Successfully implemented **fully automated, unattended deployment** for applications via SSH-based command execution. The system now creates LXC containers, installs Docker, and deploys applications completely automatically.

## Architecture Changes

### 1. SSH-Based Command Execution

**New Methods in `proxmox_service.py`:**

- `execute_command_via_ssh()` - Execute commands on Proxmox host via SSH
- `execute_in_container()` - Execute commands inside LXC containers using `pct exec`
- Updated `setup_docker_in_alpine()` - Fully automated Docker installation via SSH

**How It Works:**
1. Connects to Proxmox host via SSH (using paramiko library)
2. Uses `pct exec <vmid> -- sh -c 'command'` to run commands inside containers
3. Supports long-running operations with configurable timeouts
4. Provides proper error handling and logging

### 2. Automated Docker Installation Process

When deploying an application, the system now:

1. **Creates LXC Container** with proper Docker settings:
   - `nesting=1` - Required for Docker containers
   - `keyctl=1` - Required for systemd/Docker
   - `unprivileged=1` - Security best practice

2. **Starts Container** and waits for it to be ready

3. **Installs Docker** (fully automated via SSH):
   ```bash
   apk update
   apk add --no-cache docker docker-cli-compose
   rc-update add docker default
   service docker start
   docker info  # Verification
   ```

4. **Deploys Application** using Docker Compose:
   - Writes `docker-compose.yml` to container
   - Pulls required Docker images
   - Starts services with `docker compose up -d`
   - Verifies services are running

## Configuration Changes

### `core/config.py` - New SSH Settings

```python
# SSH Settings (for executing commands in containers via pct exec)
PROXMOX_SSH_HOST: Optional[str] = None  # Defaults to PROXMOX_HOST
PROXMOX_SSH_PORT: int = 22
PROXMOX_SSH_USER: str = "root"
PROXMOX_SSH_PASSWORD: Optional[str] = None  # Defaults to PROXMOX_PASSWORD
```

### `.env.example` - Updated Template

Added SSH configuration section with sensible defaults.

### `requirements.txt` - New Dependency

Added `paramiko>=3.3.1` for SSH support.

## Service Updates

### `proxmox_service.py`

**Removed:**
- Old `execute_command_in_lxc()` (API-based, non-functional)
- `write_file_to_lxc()` (filesystem API, not widely supported)

**Added:**
- `execute_command_via_ssh()` - SSH command execution
- `execute_in_container()` - Container command wrapper

**Updated:**
- `setup_docker_in_alpine()` - Now fully automated via SSH
- Error handling and logging throughout

### `app_service.py`

**Updated:**
- `_setup_docker_compose()` - Complete rewrite using SSH execution
  - Properly escapes YAML content for shell
  - Uses `docker compose` (modern v2 syntax) instead of `docker-compose`
  - Adds verification step after deployment
  - Extended timeouts for image pulling (10 min) and service start (5 min)

- `start_app()` - Updated to use `execute_in_container()`
- `stop_app()` - Updated to use `execute_in_container()`

### `api/endpoints/apps.py`

**Updated:**
- `get_app_logs()` - Uses new `execute_in_container()` method

## Deployment Flow

### Complete Automated Workflow

```
1. User clicks "Deploy" in UI
   ↓
2. Proximity selects best node
   ↓
3. Gets next available VMID
   ↓
4. Creates LXC container with Docker settings
   ↓
5. Starts container
   ↓
6. SSH → Install Docker (apk add docker docker-cli-compose)
   ↓
7. SSH → Write docker-compose.yml to /root/
   ↓
8. SSH → Pull Docker images (docker compose pull)
   ↓
9. SSH → Start services (docker compose up -d)
   ↓
10. SSH → Verify services running (docker compose ps)
   ↓
11. Create app record in database
   ↓
12. Return success with app details
```

### Error Handling

If any step fails:
1. Logs detailed error information
2. Initiates cleanup process
3. Force-stops container if running
4. Destroys container
5. Returns descriptive error to user

## Requirements

### SSH Access

The system requires SSH access to the Proxmox host:

- **Default:** Uses same credentials as Proxmox API
- **Custom:** Can specify different SSH credentials via environment variables
- **Port:** Default 22, configurable
- **User:** Default `root`, required for `pct exec` command

### Network Access

- Proxmox API: Port 8006 (HTTPS)
- SSH: Port 22 (configurable)
- Container networking: DHCP or static (configurable)

## Security Considerations

### SSH Security

1. **Password Authentication:** Currently uses password-based SSH
   - Simple setup, no key management
   - Passwords stored in environment variables (not ideal but acceptable for private networks)

2. **Recommendations for Production:**
   - Use SSH keys instead of passwords (future enhancement)
   - Restrict SSH access via firewall
   - Use dedicated service account with limited sudo permissions
   - Enable SSH connection logging

### Container Security

1. **Unprivileged Containers:** All containers run unprivileged
2. **Isolation:** Each app in separate container
3. **Docker in LXC:** Properly configured with nesting and keyctl

## Testing

### Manual Test Steps

1. Start Proximity API
2. Open web UI (http://proxmox-host:8765)
3. Select WordPress from catalog
4. Click "Deploy"
5. Monitor logs for progress
6. Verify container created in Proxmox
7. Verify Docker installed inside container
8. Verify WordPress accessible

### Expected Output

```
INFO - Creating LXC container 106 on node opti2
INFO - LXC creation started...
INFO - Starting container
INFO - Setting up Docker in Alpine LXC 106...
INFO - Updating Alpine packages...
INFO - Installing Docker and Docker Compose...
INFO - Enabling Docker service...
INFO - Starting Docker service...
INFO - Verifying Docker installation...
INFO - ✓ Docker successfully installed and running
INFO - Writing docker-compose.yml to LXC 106...
INFO - Pulling Docker images...
INFO - Starting Docker services...
INFO - Verifying Docker services...
INFO - ✓ Deployment successful
```

## Troubleshooting

### SSH Connection Fails

**Error:** `Failed to execute command via SSH: Authentication failed`

**Solutions:**
1. Verify PROXMOX_SSH_PASSWORD in .env
2. Check SSH is enabled on Proxmox host
3. Verify firewall allows port 22
4. Test manual SSH: `ssh root@proxmox-host`

### Docker Installation Fails

**Error:** `apk: command not found`

**Solution:** Wrong base template, ensure using Alpine Linux template

**Error:** `service docker start: failed`

**Solutions:**
1. Check container has `nesting=1` feature
2. Check container has `keyctl=1` feature
3. Verify unprivileged container
4. Check Proxmox kernel version supports nested containers

### Docker Compose Fails

**Error:** `docker: command not found`

**Solution:** Docker installation step failed, check previous logs

**Error:** `image pull failed`

**Solutions:**
1. Check container has internet access
2. Verify DNS working inside container
3. Check for Docker Hub rate limiting
4. Try pulling image manually

## Performance Considerations

### Timeouts

- **Docker Install:** 180 seconds (3 minutes)
- **Image Pull:** 600 seconds (10 minutes) - Large images need time
- **Service Start:** 300 seconds (5 minutes)
- **SSH Connection:** 30 seconds

### Optimization Opportunities

1. **Template Caching:** Create templates with Docker pre-installed
2. **Image Caching:** Pre-pull common images to shared storage
3. **Parallel Deployment:** Deploy to multiple nodes simultaneously
4. **Connection Pooling:** Reuse SSH connections for multiple commands

## Future Enhancements

### Planned Features

1. **SSH Key Authentication:** More secure than passwords
2. **Progress Streaming:** Real-time deployment progress via WebSocket
3. **Rollback Support:** Automatic rollback on deployment failure
4. **Health Checks:** Verify application is responsive after deployment
5. **Multi-Node Deployment:** Distribute apps across cluster
6. **Docker Image Registry:** Private registry for custom images

### Optimization Ideas

1. **Pre-built Templates:** Docker pre-installed, instant deployment
2. **Image Cache:** Shared storage for Docker images
3. **Connection Pooling:** Persistent SSH connections
4. **Batch Operations:** Deploy multiple apps simultaneously

## Migration from Old System

### Breaking Changes

None! The system is backward compatible.

### New Capabilities

- ✅ Fully automated deployment (no manual steps)
- ✅ Complete error handling and cleanup
- ✅ Detailed logging at every step
- ✅ Works out-of-the-box with default SSH configuration

## Support

### Common Issues

See `DEPLOYMENT.md` for detailed troubleshooting guide.

### Getting Help

1. Check application logs
2. Review deployment status in UI
3. SSH into Proxmox and check container manually
4. Review this documentation

## Files Modified

### Core Files

- `backend/core/config.py` - Added SSH configuration
- `backend/requirements.txt` - Added paramiko dependency
- `.env.example` - Added SSH settings example

### Service Layer

- `backend/services/proxmox_service.py` - SSH execution, automated Docker setup
- `backend/services/app_service.py` - Docker Compose deployment, app lifecycle

### API Layer

- `backend/api/endpoints/apps.py` - Updated log retrieval

### Documentation

- `DEPLOYMENT.md` - Comprehensive deployment guide (existing, explains limitations)
- `AUTOMATED_DEPLOYMENT.md` - This file, explains new automated solution

## Conclusion

The Proximity platform now provides **fully automated, unattended application deployment** via SSH-based command execution. Users can deploy applications with a single click, and the system handles all the complexity:

- Container creation ✅
- Docker installation ✅  
- Application deployment ✅
- Error handling ✅
- Cleanup on failure ✅

No manual intervention required! 🎉
