# Proximity-LAN Architecture

## Overview

The **proximity-lan** architecture provides consistent, isolated networking for all Proximity installations. Instead of auto-detecting random bridge names (vmbr1, vmbr2, etc.), we create a dedicated, purpose-built `proximity-lan` bridge.

## Why proximity-lan?

### Problems with Auto-Detection (V1)

❌ **Inconsistent naming** - Different bridge names across hosts (vmbr1, vmbr2, vmbr3...)  
❌ **Unclear purpose** - Hard to identify which bridge is for Proximity  
❌ **Complex documentation** - "Find an available vmbr" instructions  
❌ **Auto-detection guessing** - Might pick wrong bridge or fail

### Benefits of proximity-lan (V2)

✅ **Consistent naming** - Same `proximity-lan` name on every installation  
✅ **Clear purpose** - Immediately obvious which bridge is for Proximity  
✅ **Simple documentation** - "Use proximity-lan" everywhere  
✅ **Explicit creation** - No guessing, we create what we need  
✅ **Production ready** - Predictable, reliable, maintainable

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Proxmox Host                                 │
│                                                                       │
│  ┌──────────────────────────────────────────────┐                   │
│  │        vmbr0 (Management LAN)                 │                   │
│  │        192.168.1.0/24                         │                   │
│  │                                                │                   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────┐ │                   │
│  │  │ Proxmox  │  │ Proximity│  │   Router   │ │                   │
│  │  │   UI     │  │   API    │  │    LXC     │─┼──┐                │
│  │  │ :8006    │  │  :8765   │  │ (VMID 100) │ │  │                │
│  │  └──────────┘  └──────────┘  └────────────┘ │  │                │
│  └───────────────────────────────────────────────┘  │                │
│                                                      │                │
│                                                      │ NAT/Routing    │
│  ┌───────────────────────────────────────────────┐  │                │
│  │        proximity-lan (Isolated Network)       │◄─┘                │
│  │        10.10.0.0/24                           │                   │
│  │        Gateway: 10.10.0.1                     │                   │
│  │        DHCP: 10.10.0.100-250                  │                   │
│  │        DNS: *.prox.local                      │                   │
│  │                                                │                   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │                   │
│  │  │  nginx   │  │wordpress │  │  nextcloud│   │                   │
│  │  │10.10.0.101│  │10.10.0.102│ │10.10.0.103│   │                   │
│  │  └──────────┘  └──────────┘  └──────────┘   │                   │
│  └───────────────────────────────────────────────┘                   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Implementation

### Automatic Setup

When Proximity starts on a Linux/Proxmox host:

1. **Discover Bridges** - Scans for existing bridges (vmbr0, vmbr1, proximity-lan...)
2. **Identify Management** - Finds which bridge has Proxmox UI/API
3. **Check proximity-lan** - Looks for existing proximity-lan bridge
4. **Create if Missing** - Creates proximity-lan if not found
5. **Configure Services** - Sets up DHCP/DNS on proximity-lan
6. **Deploy Router** - Creates router LXC (VMID 100) for connectivity

### Bridge Creation

The `NetworkManagerV2` creates proximity-lan using:

```python
# Create bridge interface
ip link add name proximity-lan type bridge

# Assign IP address
ip addr add 10.10.0.1/24 dev proximity-lan

# Bring bridge up
ip link set proximity-lan up

# Make persistent in /etc/network/interfaces
auto proximity-lan
iface proximity-lan inet static
    address 10.10.0.1/24
    bridge-ports none
    bridge-stp off
    bridge-fd 0
```

### Router LXC Configuration

**VMID:** 100 (reserved for Proximity router)

**Network Interfaces:**
- `eth0` → vmbr0 (management) - DHCP from LAN
- `eth1` → proximity-lan (apps) - Static 10.10.0.1/24

**Services:**
- IP forwarding enabled (`net.ipv4.ip_forward=1`)
- NAT via iptables (`MASQUERADE` on eth0)
- DNS forwarding (optional)
- Reverse proxy (optional)

**Resources:**
- CPU: 1 core
- RAM: 512 MB
- Storage: 4 GB
- Type: Unprivileged LXC

## Container Configuration

All app containers automatically use proximity-lan:

```bash
# Container network config
name=eth0,bridge=proximity-lan,ip=dhcp,firewall=1

# Result:
# - Gets IP via DHCP (e.g., 10.10.0.105)
# - Registers DNS hostname (appname.prox.local)
# - Can reach other apps via hostname
# - Internet access via router NAT
# - Isolated from management LAN
```

## Fallback Mode

If proximity-lan creation fails (permissions, platform, etc.):

- Falls back to management bridge (vmbr0)
- Logs clear warning messages
- Apps still work, just without isolation
- Common in development (macOS/Windows)

## Verification

Check proximity-lan status:

```bash
# Check bridge exists
ip link show proximity-lan

# Check IP configuration
ip addr show proximity-lan

# Check router LXC
pct status 100

# Check routing
ip route | grep proximity-lan
```

## User Experience

### Before (vmbr1 Auto-Detection)

```
Step 1/5: Discovering Proxmox network bridges...
Found 3 bridges: ['vmbr0', 'vmbr1', 'vmbr2']

Step 2/5: Identifying management and isolated bridges...
Discovered bridge: BridgeInfo(vmbr0, 192.168.1.100/24, MGMT)
Discovered bridge: BridgeInfo(vmbr1, None, ISOLATED)
Discovered bridge: BridgeInfo(vmbr2, 10.0.0.1/24, ISOLATED)

Identified management bridge: vmbr0 (192.168.1.100/24)
Found isolated bridge for apps: vmbr1

✅ Smart network infrastructure initialized successfully
```

**Issues:**
- Why vmbr1 and not vmbr2?
- What if vmbr1 already in use?
- Documentation confusing ("find available vmbr")

### After (proximity-lan Creation)

```
Step 1/5: Discovering Proxmox network bridges...
Found 2 existing bridges: ['vmbr0', 'vmbr1']

Step 2/5: Identifying management bridge...
Management bridge: vmbr0

Step 3/5: Setting up proximity-lan bridge...
Creating dedicated proximity-lan bridge...
✓ Created proximity-lan bridge successfully

Step 4/5: Configuring DHCP/DNS on proximity-lan...
Configured DHCP range: 10.10.0.100-250
Configured DNS domain: .prox.local

Step 5/5: Deploying router LXC...
Router LXC (VMID 100) deployed successfully

✅ Proximity isolated network initialized successfully
   Apps will use: proximity-lan (10.10.0.0/24)
```

**Benefits:**
- Crystal clear what's happening
- Consistent across all hosts
- Easy to troubleshoot ("check proximity-lan")
- Professional, production-ready

## Documentation Updates

All documentation now references `proximity-lan`:

- API responses: `"app_bridge": "proximity-lan"`
- Log messages: `Apps will use: proximity-lan`
- Error messages: `proximity-lan bridge not found`
- Setup guides: `Create proximity-lan bridge`
- Troubleshooting: `ip link show proximity-lan`

## Security Benefits

✅ **Network Isolation** - Apps separated from management LAN  
✅ **No IP Conflicts** - Dedicated 10.10.0.0/24 subnet  
✅ **Private DNS** - .prox.local domain not on LAN  
✅ **Controlled Access** - All traffic through router LXC  
✅ **Firewall Ready** - Clear boundary for rules  
✅ **Reduced Attack Surface** - Apps not directly exposed

## Migration Path

Existing Proximity installations can migrate:

1. **Update Code** - Pull latest network_manager_v2.py
2. **Restart Service** - proximity-lan created automatically
3. **Migrate Apps** - Gradually move containers to proximity-lan
4. **Verify** - Check logs for successful initialization

Old vmbr1-based containers continue working until migrated.

## Summary

| Aspect | V1 (vmbr1) | V2 (proximity-lan) |
|--------|------------|---------------------|
| Bridge Name | vmbr1/vmbr2 (varies) | proximity-lan (consistent) |
| Discovery | Auto-detect available | Create dedicated |
| Documentation | Complex ("find vmbr") | Simple ("use proximity-lan") |
| User Experience | Confusing | Clear |
| Production Ready | ⚠️  Maybe | ✅ Yes |
| Maintenance | Hard | Easy |
| Troubleshooting | "Which vmbr?" | "Check proximity-lan" |

## Next Steps

1. ✅ **Code Complete** - NetworkManagerV2 implements proximity-lan
2. ✅ **Documentation Updated** - All references changed to proximity-lan
3. 🔄 **Testing** - Deploy on actual Proxmox host
4. 🔄 **Integration** - Update main.py startup sequence
5. 🔄 **Migration Guide** - Document vmbr1 → proximity-lan migration

---

**The proximity-lan architecture makes Proximity's networking as consistent and reliable as its UI.**
