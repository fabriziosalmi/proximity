# Bugfix: Caddy Service Not Starting in Network Appliance

## Problem

The network appliance was configured to install Caddy via `apk add caddy`, but Caddy was not starting properly. The Alpine Linux `caddy` package does not include an OpenRC init script by default, causing service management commands to fail.

**Symptoms:**
- `rc-service caddy start` fails or shows warnings
- Caddy reverse proxy not accessible
- Network appliance services showing Caddy as "not running"
- Applications not accessible through the reverse proxy

## Root Cause

Alpine Linux's `caddy` package provides only the binary (`/usr/sbin/caddy`) but doesn't include:
- OpenRC init script (`/etc/init.d/caddy`)
- Service management integration
- Automatic startup configuration

Without the init script, commands like `rc-service caddy start` and `rc-update add caddy default` fail silently or with errors.

## Solution

Created a proper OpenRC init script for Caddy that:

1. **Manages Caddy as a background service**
   - Uses OpenRC's process supervision
   - Proper PID file management
   - Log file management

2. **Handles dependencies**
   - Waits for network to be available
   - Runs after firewall configuration

3. **Creates necessary directories**
   - `/var/log/caddy` for logs
   - `/var/lib/caddy` for state files
   - Proper permissions

## Changes Made

### 1. Network Appliance Orchestrator (`backend/services/network_appliance_orchestrator.py`)

Enhanced `_configure_caddy()` method to:
- Create all necessary directories (`/etc/caddy/sites-enabled`, `/var/log/caddy`, `/var/lib/caddy`)
- Generate OpenRC init script at `/etc/init.d/caddy`
- Make init script executable
- Enable and start Caddy service properly

### 2. Caddy Service (`backend/services/caddy_service.py`)

Enhanced `_install_caddy()` method to:
- Install Caddy package
- Create OpenRC init script
- Set up initial configuration
- Start service with proper supervision

## Init Script Details

The OpenRC init script (`/etc/init.d/caddy`) includes:

```sh
#!/sbin/openrc-run

description="Caddy web server"
command="/usr/sbin/caddy"
command_args="run --config /etc/caddy/Caddyfile --adapter caddyfile"
command_background="yes"
pidfile="/run/caddy.pid"
output_log="/var/log/caddy/caddy.log"
error_log="/var/log/caddy/caddy.err"

depend() {
    need net
    after firewall
}

start_pre() {
    checkpath --directory --owner root:root --mode 0755 /var/log/caddy
    checkpath --directory --owner root:root --mode 0755 /var/lib/caddy
}
```

## Verification

### 1. Check Service Status

```bash
# SSH into the appliance
ssh root@<appliance-ip>

# Check Caddy service status
rc-service caddy status

# Should show: "caddy [started]"
```

### 2. Verify Init Script

```bash
# Check init script exists and is executable
ls -la /etc/init.d/caddy

# Should show: -rwxr-xr-x 1 root root ... /etc/init.d/caddy
```

### 3. Test Service Commands

```bash
# Stop Caddy
rc-service caddy stop

# Start Caddy
rc-service caddy start

# Restart Caddy
rc-service caddy restart

# Check if enabled at boot
rc-update show default | grep caddy

# Should show: caddy | default
```

### 4. Check Caddy Process

```bash
# Check if Caddy is running
ps aux | grep caddy

# Should show: /usr/sbin/caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
```

### 5. Check Logs

```bash
# View Caddy logs
tail -f /var/log/caddy/caddy.log

# View error logs (if any)
tail -f /var/log/caddy/caddy.err
```

### 6. Test HTTP Response

```bash
# From within the appliance
curl http://localhost

# Or from Proxmox host
curl http://<appliance-ip>
```

## API Verification

Use the Proximity API to check appliance status:

```bash
# Get infrastructure status
curl http://localhost:8765/api/v1/system/infrastructure/status

# Response should show:
{
  "appliance": {
    "status": "running",
    ...
  },
  "services": {
    "caddy": "started",
    "dnsmasq": "started"
  }
}
```

## Migration for Existing Appliances

If you have an existing network appliance without the Caddy service:

### Option 1: Recreate Appliance (Recommended)

```bash
# Delete existing appliance via Proximity UI
# Recreate appliance - it will include the fix
```

### Option 2: Manual Fix (Advanced)

```bash
# SSH into existing appliance
ssh root@<appliance-ip>

# Create init script
cat > /etc/init.d/caddy << 'EOF'
#!/sbin/openrc-run

description="Caddy web server"
command="/usr/sbin/caddy"
command_args="run --config /etc/caddy/Caddyfile --adapter caddyfile"
command_background="yes"
pidfile="/run/caddy.pid"
output_log="/var/log/caddy/caddy.log"
error_log="/var/log/caddy/caddy.err"

depend() {
    need net
    after firewall
}

start_pre() {
    checkpath --directory --owner root:root --mode 0755 /var/log/caddy
    checkpath --directory --owner root:root --mode 0755 /var/lib/caddy
}
EOF

# Make executable
chmod +x /etc/init.d/caddy

# Create necessary directories
mkdir -p /var/log/caddy /var/lib/caddy

# Enable and start service
rc-update add caddy default
rc-service caddy start

# Verify
rc-service caddy status
```

## Troubleshooting

### Caddy Won't Start

```bash
# Check configuration syntax
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

# Try running Caddy manually
/usr/sbin/caddy run --config /etc/caddy/Caddyfile --adapter caddyfile

# Check for port conflicts
netstat -tulpn | grep :80
netstat -tulpn | grep :443
```

### Permission Issues

```bash
# Ensure directories exist with proper permissions
mkdir -p /var/log/caddy /var/lib/caddy
chmod 755 /var/log/caddy /var/lib/caddy
```

### Init Script Not Found

```bash
# Verify init script exists
ls -la /etc/init.d/caddy

# If missing, recreate using commands above
```

## Impact

- **Existing Deployments**: Newly provisioned network appliances will have Caddy working correctly
- **In-Progress Deployments**: If Caddy failed during appliance setup, reprovisioning will fix it
- **Application Access**: Applications will be accessible through the Caddy reverse proxy
- **Service Management**: Standard OpenRC commands (`rc-service caddy start|stop|restart`) now work properly

## Related Files

- `backend/services/network_appliance_orchestrator.py` - Network appliance provisioning
- `backend/services/caddy_service.py` - Caddy service management (legacy/separate instances)
- `docs/architecture.md` - Network architecture documentation
- `docs/deployment.md` - Deployment and operations guide

## Testing

To test the fix:

1. **Provision new appliance:**
   ```bash
   # Via Proximity UI: Navigate to Infrastructure → Create Appliance
   ```

2. **Check service status:**
   ```bash
   # SSH to appliance
   rc-service caddy status
   ```

3. **Deploy an application:**
   ```bash
   # Deploy any web application via Proximity UI
   # Verify it's accessible through Caddy
   ```

4. **Check logs:**
   ```bash
   tail -f /var/log/caddy/caddy.log
   ```

## References

- [Caddy Documentation](https://caddyserver.com/docs/)
- [OpenRC Service Scripts](https://wiki.gentoo.org/wiki/OpenRC)
- [Alpine Linux Init System](https://wiki.alpinelinux.org/wiki/OpenRC)
