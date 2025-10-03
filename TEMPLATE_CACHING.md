# Alpine Template Caching in Proximity

## Overview

Proximity implements **transparent template caching** to avoid re-downloading Alpine Linux templates for every container deployment. Once a template is downloaded, it's stored permanently in Proxmox storage and automatically reused for all future deployments.

## How It Works

### 1. **Cache Check (First)**
When deploying a new application, Proximity:
- Searches ALL storage pools on the target node
- Looks for any existing Alpine Linux template
- If found → **CACHE HIT** ✅ (uses cached template)
- If not found → **CACHE MISS** ⚠️ (downloads template once)

### 2. **Smart Fallback**
The cache search is intelligent:
- First looks for exact version match (e.g., Alpine 3.22)
- Then searches for any Alpine template (version-agnostic)
- Matches architecture automatically (amd64/arm64)

### 3. **One-Time Download**
On cache miss:
- Downloads Alpine template from Proxmox repository
- Stores in node's local storage (typically `local` storage)
- Template becomes **permanently cached** for future use
- Download typically takes 2-5 minutes (one-time only)

### 4. **Automatic Reuse**
After initial download:
- All subsequent deployments use the cached template
- No network downloads required
- Deployment speed significantly faster
- Works across all applications on the same node

## Cache Location

Templates are stored in Proxmox storage:
```
Storage: local (or first available storage with vztmpl support)
Path: /var/lib/vz/template/cache/
Format: alpine-3.22-default_amd64.tar.xz
```

## Checking Cache Status

### Via API
```bash
curl http://localhost:8000/api/system/templates/cache
```

Response shows:
- Nodes with cached templates
- Template count per node
- Cache hit availability

### Via Proxmox UI
1. Navigate to: Node → Storage → local → CT Templates
2. See all cached templates

### Via SSH
```bash
# On Proxmox node
ls -lh /var/lib/vz/template/cache/alpine*
```

## Logs

Cache behavior is logged during deployment:

### Cache Hit (Fast)
```
INFO: Searching for Alpine 3.22 template (amd64) in cache...
INFO: ✓ CACHE HIT: Using cached template from local: local:vztmpl/alpine-3.22-default_amd64.tar.xz
INFO: ✓ Template ready: local:vztmpl/alpine-3.22-default_amd64.tar.xz
```

### Cache Miss (First Deployment Only)
```
INFO: Searching for Alpine 3.22 template (amd64) in cache...
WARN: ⚠️  CACHE MISS: No Alpine template found in cache
INFO: Downloading Alpine 3.22 template (this is a one-time download)...
INFO: 📥 Downloading Alpine 3.22 (amd64) to local on node1...
INFO: ⏳ This may take a few minutes (cached for future deployments)
INFO: Download task started: UPID:node1:00001234...
INFO: ✓ Template downloaded and CACHED successfully: local:vztmpl/alpine-3.22-default_amd64.tar.xz
INFO: 💾 Template is now cached in local for future deployments
```

## Benefits

1. **Faster Deployments**: 2-5 minutes saved per deployment after first
2. **Bandwidth Savings**: No repeated downloads (50-100 MB saved per deployment)
3. **Reliability**: No dependency on external servers after initial download
4. **Transparent**: No configuration needed, works automatically

## Multi-Node Setup

If you have multiple Proxmox nodes:
- Each node maintains its own template cache
- Templates are downloaded once per node (not cluster-wide)
- First deployment on each node triggers download
- Subsequent deployments on that node use cache

### Manual Pre-Caching (Optional)

To pre-download templates on all nodes:

```bash
# On each Proxmox node
pveam update
pveam download local alpine-3.22-default_amd64.tar.xz
```

Or use Proximity API:
```bash
# Deploy and delete a test app on each node
# This will populate the cache automatically
```

## Storage Requirements

- **Alpine Template Size**: ~50-100 MB per template
- **Storage Pool**: Must support `vztmpl` content type
- **Recommended**: Use `local` storage (default)

## Template Versions

Proximity uses:
- **Default**: Alpine 3.22 (latest stable)
- **Architecture**: Auto-detected (amd64 or arm64)
- **Format**: Official Proxmox Alpine templates

### Using Different Versions

Edit in `backend/services/proxmox_service.py`:
```python
template_to_use = await self.ensure_alpine_template(node, version='3.20')
```

## Troubleshooting

### Template Not Found After Download
1. Check storage permissions
2. Verify storage supports `vztmpl` content
3. Check logs for download task completion

### Download Fails
- Check internet connectivity on Proxmox node
- Verify firewall allows HTTP/HTTPS to download.proxmox.com
- Try manual download: `pveam available && pveam download local <template>`

### Cache Not Working
- Check storage is writable
- Verify storage is not full
- Review Proximity logs for cache search details

## Advanced Configuration

### Custom Storage for Templates

To use a different storage pool, templates are automatically searched across all available storages. To force a specific storage:

1. Ensure storage has `vztmpl` content type enabled
2. Templates will be downloaded to first available storage with `vztmpl` support

### Template Cleanup

Templates can be removed via Proxmox UI if needed:
1. Navigate to: Node → Storage → local → CT Templates
2. Select template → Remove

⚠️ **Warning**: Removing templates forces re-download on next deployment

## Performance Metrics

Typical deployment times:

| Scenario | Time |
|----------|------|
| First deployment (cache miss) | 5-8 minutes |
| Subsequent deployments (cache hit) | 2-3 minutes |
| Time saved per deployment | 3-5 minutes |

## Summary

✅ Template caching is **automatic and transparent**  
✅ Works **immediately** after first deployment  
✅ Saves **3-5 minutes per deployment**  
✅ Reduces **bandwidth usage by 50-100 MB per deployment**  
✅ No **configuration required**  

The cache system ensures optimal performance while maintaining reliability and ease of use.
