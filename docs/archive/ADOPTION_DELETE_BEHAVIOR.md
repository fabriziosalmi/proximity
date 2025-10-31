# Container Adoption - Delete Behavior

## Overview
Proximity distinguishes between **deployed containers** (created by Proximity) and **adopted containers** (existing containers imported into management). The delete operation behaves differently based on the container type.

## Delete Behavior

### 🚀 Deployed Containers (Normal Apps)
**Behavior:** Full destruction

When you delete a deployed container:
1. ✅ Container is stopped on Proxmox
2. ✅ Container is **destroyed** from Proxmox (VMID released)
3. ✅ Application record removed from Proximity database
4. ✅ Allocated ports released back to the pool
5. ✅ All resources cleaned up

**Result:** Container is completely removed from both Proximity and Proxmox.

---

### 🔖 Adopted Containers (Imported Apps)
**Behavior:** Management removal only

When you delete an adopted container:
1. ✅ Application record removed from Proximity database
2. ✅ Allocated ports released back to the pool
3. ❌ Container is **NOT touched** on Proxmox
4. ❌ Container continues running with original configuration
5. ✅ Container can be re-adopted later if needed

**Result:** Container is removed from Proximity management but **remains intact on Proxmox**.

---

## How It Works

### Detection
The system identifies adopted containers using the `config.adopted` flag:

```python
# Application.config
{
    "adopted": true,  # ← Flag indicating this is an adopted container
    "original_vmid": 201,
    "original_name": "existing-nginx-lxc-port80",
    "adoption_date": "2025-10-21T12:10:48",
    ...
}
```

### Delete Task Logic

```python
# Simplified logic from delete_app_task
is_adopted = app.config.get('adopted', False)

if is_adopted:
    # ONLY remove from Proximity - leave container on Proxmox
    release_ports()
    app.delete()  # Delete DB record only
    
else:
    # FULL deletion - destroy container
    stop_container()
    delete_container_from_proxmox()
    release_ports()
    app.delete()
```

---

## Safety Features

### 🛡️ Protection Against Accidental Deletion
- Adopted containers are **NEVER destroyed** from Proxmox
- Original VMID and configuration preserved
- Container continues running with no interruption
- Can be re-discovered and re-adopted if needed

### 🔄 Re-Adoption Flow
If you "delete" an adopted container from Proximity:

1. Container remains on Proxmox (running/stopped state unchanged)
2. Navigate to `/adopt` in Proximity
3. Click "Refresh Discovery"
4. Container appears in unmanaged containers list
5. You can adopt it again with fresh configuration

---

## Use Cases

### When to "Delete" an Adopted Container

✅ **Stop managing the container in Proximity**
- You want to manage it manually via Proxmox
- Temporary removal for troubleshooting
- Migrating management to another system

✅ **Clean up Proximity database**
- Remove test adoptions
- Clean up after experimentation
- Free up allocated port numbers

❌ **DON'T use delete if you want to:**
- Destroy the container completely → Use Proxmox directly
- Stop the container → Use the "Stop" action instead
- Restart the container → Use the "Restart" action

---

## Frontend Indicators

### Visual Cues for Adopted Containers
In the Proximity UI, adopted containers can be identified by:

1. **Config badge:** Shows "adopted" type in app details
2. **Metadata:** `config.adopted: true` in JSON
3. **Original info:** Displays original VMID and container name

### Delete Button Behavior
When you click delete on an adopted container:

```
Action: Delete "existing-nginx-lxc-port80"
Message: "Remove from Proximity management (container will be preserved on Proxmox)"
```

vs. normal container:

```
Action: Delete "adminer-test"
Message: "Container will be destroyed from Proxmox"
```

---

## API Responses

### Adopted Container Deletion
```json
{
  "success": true,
  "message": "Adopted container existing-nginx-lxc-port80 removed from Proximity (container preserved on Proxmox)",
  "adopted": true,
  "vmid_preserved": 201
}
```

### Normal Container Deletion
```json
{
  "success": true,
  "message": "Application adminer-test deleted",
  "adopted": false
}
```

---

## Database Impact

### Before Delete (Adopted Container)
```sql
-- Application record
id: nginx-6e0c331e
lxc_id: 201
hostname: existing-nginx-lxc-port80
config: {"adopted": true, "original_vmid": 201}
```

### After Delete
```sql
-- Application record: REMOVED from database
-- Proxmox container VMID 201: STILL EXISTS, STILL RUNNING
```

---

## Logs & Monitoring

### Adopted Container Delete Logs
```
[existing-nginx-lxc-port80] 🔖 ADOPTED CONTAINER - Removing Proximity management only (container will remain on Proxmox)
[existing-nginx-lxc-port80] Releasing allocated ports...
[existing-nginx-lxc-port80] ✅ Adopted container un-managed successfully (VMID 201 preserved on Proxmox)
```

### Normal Container Delete Logs
```
[adminer-test] 🗑️ DEPLOYED CONTAINER - Full deletion (destroying container)
[adminer-test] STEP 1/4: Issuing STOP command for LXC 100...
[adminer-test] STEP 2/4: Verifying LXC 100 is STOPPED...
[adminer-test] STEP 3/4: Deleting LXC 100...
[adminer-test] STEP 4/4: Releasing ports and cleaning up...
[adminer-test] ✅ Application deleted successfully (all 4 steps complete)
```

---

## Best Practices

### ✅ DO
- Use Proximity delete for adopted containers when you want to stop managing them
- Re-adopt containers after deletion if you want to manage them again
- Keep track of original VMIDs for reference
- Use the adoption wizard to rediscover containers

### ❌ DON'T
- Expect adopted containers to be destroyed from Proxmox on delete
- Delete adopted containers if you want to destroy them (use Proxmox instead)
- Worry about losing data when deleting adopted containers
- Forget that the container is still running on Proxmox

---

## Security Considerations

### Why This Design?
1. **Data Safety:** Prevents accidental destruction of important containers
2. **Non-Invasive:** Proximity never destroys what it didn't create
3. **Reversible:** Deletion can be undone by re-adopting
4. **Clear Intent:** Users must explicitly destroy containers in Proxmox

### Alternative: Manual Proxmox Deletion
If you want to **completely destroy** an adopted container:

1. Delete from Proximity (removes management)
2. Log into Proxmox directly
3. Stop the container if needed
4. Delete the container from Proxmox UI/CLI

This two-step process ensures intentional destruction.

---

## Summary

| Feature | Deployed Container | Adopted Container |
|---------|-------------------|-------------------|
| **Delete in Proximity** | Destroys container | Removes management only |
| **Container survives?** | ❌ No | ✅ Yes |
| **Can re-adopt?** | ❌ No (destroyed) | ✅ Yes |
| **Ports released?** | ✅ Yes | ✅ Yes |
| **DB record removed?** | ✅ Yes | ✅ Yes |
| **Proxmox VMID freed?** | ✅ Yes | ❌ No (still in use) |

**Key Takeaway:** Proximity respects the origin of containers. What Proximity creates, Proximity can destroy. What Proximity adopts, Proximity only manages.
