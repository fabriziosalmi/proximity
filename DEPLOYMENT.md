# Deployment Guide

## Proxmox API Limitations

### The `/exec` Endpoint Issue

The Proxmox VE API has a known limitation: the `/nodes/{node}/lxc/{vmid}/exec` endpoint for executing commands inside LXC containers is **not implemented** in most Proxmox versions. This affects Proximity's ability to automatically install Docker inside newly created containers.

#### What This Means

When deploying an application:
1. ✅ Proximity **can** create an LXC container with proper Docker settings
2. ✅ Proximity **can** configure the container with required features (nesting=1, keyctl=1)
3. ❌ Proximity **cannot** automatically install Docker via the API
4. ❌ Proximity **cannot** run setup scripts inside the container via the API

## Solutions & Workarounds

### Option 1: Use Pre-built Docker Templates (Recommended)

The best solution is to use LXC templates that already have Docker pre-installed.

#### Create a Custom Docker Template

1. **Create a base container manually:**
   ```bash
   # On your Proxmox host
   pct create 999 local:vztmpl/alpine-3.22-default_20250617_amd64.tar.xz \
     --hostname docker-template \
     --memory 2048 \
     --cores 2 \
     --net0 name=eth0,bridge=vmbr0,firewall=1,gw=192.168.1.1,ip=192.168.1.50/24 \
     --features nesting=1,keyctl=1 \
     --unprivileged 1 \
     --rootfs local-lvm:8
   ```

2. **Start the container and install Docker:**
   ```bash
   pct start 999
   
   # Wait a few seconds, then exec into it
   pct exec 999 -- sh -c '
     apk update && \
     apk add docker docker-compose && \
     rc-update add docker default && \
     service docker start && \
     docker info
   '
   ```

3. **Create a template from this container:**
   ```bash
   # Stop the container
   pct stop 999
   
   # Convert to template (this makes it read-only)
   vzdump 999 --dumpdir /var/lib/vz/template/cache --compress gzip
   
   # The resulting file will be something like:
   # /var/lib/vz/template/cache/vzdump-lxc-999-YYYY_MM_DD-HH_MM_SS.tar.gz
   
   # Rename it for easier use:
   mv /var/lib/vz/template/cache/vzdump-lxc-999-*.tar.gz \
      /var/lib/vz/template/cache/alpine-docker-template.tar.gz
   
   # Remove the temporary container
   pct destroy 999
   ```

4. **Use your template in Proximity:**
   - Update the template reference in your deployment code
   - Or manually specify it when creating containers

### Option 2: Manual Docker Installation (Per Container)

For each container that Proximity creates, you need to manually install Docker.

#### Via Proxmox Web Console

1. Go to Proxmox web interface
2. Select the container (e.g., 103)
3. Click "Console"
4. Run these commands:
   ```sh
   apk update
   apk add docker docker-compose
   rc-update add docker default
   service docker start
   docker info  # Verify it's working
   ```

#### Via SSH from Proxmox Host

```bash
# SSH into your Proxmox host, then:
pct exec <VMID> -- sh -c '
  apk update && \
  apk add docker docker-compose && \
  rc-update add docker default && \
  service docker start
'

# Example for container 103:
pct exec 103 -- sh -c 'apk update && apk add docker docker-compose && rc-update add docker default && service docker start'
```

### Option 3: Automate via SSH (Advanced)

If you want to automate this process, you can extend Proximity to use SSH:

1. Configure SSH access to your Proxmox host
2. Use Python's `paramiko` or `asyncssh` library
3. Execute `pct exec` commands via SSH

**Example Python code:**

```python
import asyncssh

async def install_docker_via_ssh(host, username, password, vmid):
    async with asyncssh.connect(host, username=username, password=password) as conn:
        result = await conn.run(
            f"pct exec {vmid} -- sh -c '"
            f"apk update && "
            f"apk add docker docker-compose && "
            f"rc-update add docker default && "
            f"service docker start"
            f"'"
        )
        return result.stdout
```

## Current Behavior

When you attempt to deploy an application, Proximity will:

1. ✅ Create an LXC container with proper configuration
2. ✅ Start the container
3. ❌ **Fail** at the "Setting up Docker" step with a detailed error message
4. ✅ Automatically clean up (stop and destroy) the failed container

**Error Message Example:**
```
Cannot automatically setup Docker in LXC 103. The Proxmox API does not support /exec endpoint for running commands inside containers. 

The container 103 has been created on node opti2 with proper Docker settings (nesting=1, keyctl=1).

To complete the setup, please choose one of these options:

1. **Use a pre-built template with Docker** (Recommended):
   - Download a template with Docker pre-installed
   - Or create your own template after manual Docker installation

2. **Manually install Docker via Console**:
   - Access the container via Proxmox web console
   - Run: apk update && apk add docker docker-compose
   - Run: rc-update add docker default && service docker start

3. **Use SSH** (if configured):
   - SSH into Proxmox host
   - Run: pct exec 103 -- sh -c 'apk update && apk add docker docker-compose && rc-update add docker default && service docker start'

After Docker is installed, you can continue with your application deployment.
```

## Future Improvements

We're exploring these options for better automation:

1. **Cloud-init Support**: Use cloud-init to bootstrap containers on first boot
2. **Hookscripts**: Use Proxmox hookscripts to run commands at container startup
3. **SSH Integration**: Add optional SSH-based command execution
4. **Template Repository**: Provide pre-built templates with Docker included

## FAQ

### Q: Why doesn't Proximity just use SSH?

**A:** We want Proximity to work out-of-the-box without requiring additional SSH configuration, keys, or security considerations. The API-based approach is cleaner and more secure when available.

### Q: Will this be fixed in future Proxmox versions?

**A:** The `/exec` endpoint has been unimplemented for years. It's unclear if/when it will be added. That's why we recommend using pre-built templates.

### Q: Can I use Ubuntu/Debian instead of Alpine?

**A:** Yes! You can modify the deployment code to use different base images. Just make sure Docker is pre-installed in your template, or manually install it using the appropriate package manager (`apt` for Ubuntu/Debian).

### Q: Does this affect VMs?

**A:** No, this only affects LXC containers. VMs have different API endpoints available.

## Related Documentation

- [Proxmox VE API Documentation](https://pve.proxmox.com/pve-docs/api-viewer/)
- [LXC Container Documentation](https://pve.proxmox.com/wiki/Linux_Container)
- [Docker in LXC](https://www.reddit.com/r/Proxmox/comments/qje9gq/running_docker_in_lxc_containers/)

## Contributing

If you've found a better solution or workaround, please contribute to this documentation or open an issue on GitHub!
