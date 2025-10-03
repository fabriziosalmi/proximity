# Proximity Network Architecture

## Overview

Proximity now provides a **fully isolated, managed network environment** for all application containers. This architecture provides better security, management, and DNS/DHCP services compared to the previous approach of directly attaching containers to the host bridge (vmbr0).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Proxmox Host                             │
│                                                                   │
│  ┌─────────────┐                                                │
│  │   vmbr0     │ ◄──── External Network (e.g., 192.168.1.0/24)  │
│  │ (Physical)  │                                                 │
│  └──────┬──────┘                                                 │
│         │                                                         │
│         │ NAT (iptables MASQUERADE)                             │
│         │                                                         │
│  ┌──────▼──────────────────────────────────────────────┐        │
│  │          prox-net (Linux Bridge)                     │        │
│  │          IP: 10.10.0.1/24                           │        │
│  │          DHCP: 10.10.0.100-250                      │        │
│  │          Domain: prox.local                         │        │
│  └──────┬───────────────────────────────────────┬──────┘        │
│         │                                        │                │
│         │                                        │                │
│  ┌──────▼──────────┐                   ┌────────▼─────────┐     │
│  │  dnsmasq        │                   │   Application    │     │
│  │  (DNS/DHCP)     │                   │   Containers     │     │
│  │  Service        │                   │   (LXC)          │     │
│  │                 │                   │                  │     │
│  │  - Assigns IPs  │                   │  nginx-01        │     │
│  │  - DNS records  │                   │  10.10.0.101     │     │
│  │  - hostname     │                   │  nginx-01.prox..│     │
│  │    resolution   │                   │                  │     │
│  └─────────────────┘                   │  wordpress-02    │     │
│                                         │  10.10.0.102     │     │
│                                         │  wordpress-02... │     │
│                                         └──────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## Network Components

### 1. prox-net Bridge

**Purpose**: Isolated virtual network for all application containers

**Configuration**:
- **IP Address**: 10.10.0.1/24 (host gateway)
- **Bridge Type**: Linux bridge (software-based)
- **No Physical Ports**: Pure virtual bridge
- **STP**: Disabled (not needed for virtual bridge)

**Location**: `/etc/network/interfaces`

```ini
auto prox-net
iface prox-net inet static
        address 10.10.0.1/24
        bridge-ports none
        bridge-stp off
        bridge-fd 0
        post-up echo 1 > /proc/sys/net/ipv4/ip_forward
        post-up iptables -t nat -A POSTROUTING -s '10.10.0.0/24' -o vmbr0 -j MASQUERADE
        post-down iptables -t nat -D POSTROUTING -s '10.10.0.0/24' -o vmbr0 -j MASQUERADE
```

### 2. NAT Routing

**Purpose**: Allow containers to access external networks

**Implementation**: iptables MASQUERADE rule

**Traffic Flow**:
```
Container (10.10.0.x) → prox-net → NAT → vmbr0/eth0 → Internet
```

**Benefits**:
- Containers can reach external resources (apt, docker pull, etc.)
- External network cannot directly reach containers (security)
- All outbound traffic appears to come from host IP

### 3. DHCP Service (dnsmasq)

**Purpose**: Automatic IP assignment and DNS resolution

**Configuration**: `/etc/proximity/dnsmasq.conf`

**Key Features**:
- **IP Range**: 10.10.0.100 - 10.10.0.250 (150 addresses)
- **Lease Time**: 12 hours
- **DNS Domain**: prox.local
- **Upstream DNS**: 1.1.1.1, 8.8.8.8

**Benefits**:
- No manual IP management
- Automatic hostname-to-IP mapping
- Containers can resolve each other by name (e.g., `nginx-01.prox.local`)

**Service Management**:
```bash
# Systemd service: proximity-dns.service
systemctl status proximity-dns
systemctl restart proximity-dns
journalctl -u proximity-dns -f
```

### 4. Container Network Configuration

**Old Approach** (deprecated):
```
net0: name=eth0,bridge=vmbr0,ip=192.168.1.100/24,gw=192.168.1.1
```

**New Approach**:
```
net0: name=eth0,bridge=prox-net,ip=dhcp,firewall=1
```

**Container Gets**:
- IP address via DHCP (e.g., 10.10.0.105)
- DNS server: 10.10.0.1 (dnsmasq)
- Default gateway: 10.10.0.1
- Hostname registered in DNS

## Network Manager Service

### Architecture

The `NetworkManager` class in `backend/services/network_manager.py` orchestrates all network infrastructure setup:

```python
network_manager = NetworkManager()
await network_manager.initialize()
```

### Initialization Sequence

```
1. configure_host_bridge()
   ├─ Detect default outgoing interface (vmbr0, eth0, etc.)
   ├─ Check if prox-net already configured
   ├─ Backup /etc/network/interfaces
   ├─ Append bridge configuration
   └─ Apply with ifreload -a

2. verify_host_network_state()
   ├─ Check bridge is UP
   ├─ Check IP assigned
   ├─ Verify NAT rule exists
   └─ Check IP forwarding enabled

3. setup_dhcp_service()
   ├─ Generate dnsmasq.conf
   ├─ Create systemd service file
   ├─ Reload systemd
   └─ Start/restart service
```

### Idempotency

All operations are idempotent:
- Configuration blocks checked before adding
- Existing services not restarted if unchanged
- Safe to run multiple times
- Automatic recovery from partial failures

### Error Handling

```python
try:
    await network_manager.configure_host_bridge()
except RuntimeError as e:
    # Automatic backup restoration
    # Detailed error logging
    # Graceful degradation
```

## Integration Points

### 1. Proxmox Service Integration

```python
# proxmox_service.py
async def create_lxc(self, node: str, vmid: int, config: Dict[str, Any]):
    hostname = config.get('hostname', f"ct{vmid}")
    
    # Get managed network configuration
    net_config = await self.network_manager.get_container_network_config(hostname)
    
    lxc_config = {
        'vmid': vmid,
        'hostname': hostname,  # For DNS registration
        'net0': net_config,    # DHCP on prox-net
        ...
    }
```

### 2. Application Startup

```python
# main.py
@app.on_event("startup")
async def startup():
    # Network infrastructure must be ready first
    network_manager = NetworkManager()
    await network_manager.initialize()
    
    # Then initialize other services
    proxmox_service.network_manager = network_manager
    ...
```

### 3. API Endpoint

```http
GET /api/v1/system/network/status

Response:
{
  "message": "Network infrastructure operational",
  "data": {
    "bridge_name": "prox-net",
    "bridge_ip": "10.10.0.1",
    "subnet": "10.10.0.0/24",
    "dhcp_range": "10.10.0.100-10.10.0.250",
    "dns_domain": "prox.local",
    "bridge_up": true,
    "nat_configured": true,
    "dhcp_service_running": true,
    "health_status": "healthy"
  }
}
```

## DNS Resolution

### How It Works

1. **Container Hostname**: Set during LXC creation (e.g., `nginx-01`)
2. **DHCP Registration**: dnsmasq registers hostname when assigning IP
3. **DNS Query**: Container queries 10.10.0.1 for `nginx-01.prox.local`
4. **Resolution**: dnsmasq returns the assigned IP address

### Usage in Containers

```bash
# Inside a container
ping nginx-01.prox.local
curl http://wordpress-02.prox.local
```

### Benefits

- Service discovery without external DNS
- No hardcoded IPs in configurations
- Automatic updates if DHCP renews different IP

## Security Considerations

### Network Isolation

✅ **Containers cannot be accessed directly from external network**
- No exposure of container IPs outside Proxmox host
- NAT provides one-way connectivity (outbound only)

✅ **Container-to-container communication allowed**
- Required for microservices architectures
- Controlled via firewall rules if needed

### Firewall Integration

Current: `firewall=1` in net0 configuration

Future enhancements:
- Per-container firewall rules
- Network policies
- Traffic inspection

## Operational Tasks

### View DHCP Leases

```bash
cat /var/lib/proximity/dnsmasq.leases
```

Output format:
```
1727890123 10.10.0.105 nginx-01 *
1727890456 10.10.0.102 wordpress-02 *
```

### Monitor DNS Queries

```bash
journalctl -u proximity-dns -f | grep query
```

### Check Bridge Status

```bash
ip addr show prox-net
bridge link show
```

### Verify NAT Rule

```bash
iptables-save | grep MASQUERADE
```

### Restart Network Services

```bash
# Restart dnsmasq
systemctl restart proximity-dns

# Restart bridge (if needed)
ifreload -a
```

## Troubleshooting

### Container Cannot Reach Internet

**Check**: NAT rule exists
```bash
iptables-save | grep -E '10\.10\.0\.0/24.*MASQUERADE'
```

**Check**: IP forwarding enabled
```bash
cat /proc/sys/net/ipv4/ip_forward  # Should be 1
```

**Fix**: Re-run network initialization
```python
await network_manager.initialize()
```

### Container Not Getting IP

**Check**: dnsmasq service running
```bash
systemctl status proximity-dns
```

**Check**: Container network configuration
```bash
pct config <vmid> | grep net0
# Should show: bridge=prox-net,ip=dhcp
```

**Check**: DHCP leases
```bash
cat /var/lib/proximity/dnsmasq.leases
journalctl -u proximity-dns | grep DHCP
```

### DNS Not Resolving

**Check**: Container DNS configuration
```bash
pct exec <vmid> -- cat /etc/resolv.conf
# Should have: nameserver 10.10.0.1
```

**Check**: dnsmasq logs
```bash
journalctl -u proximity-dns -f
```

**Test**: Direct query
```bash
dig @10.10.0.1 nginx-01.prox.local
```

## Migration from Old Architecture

### Backward Compatibility

✅ **Existing containers are not affected**
- Old containers on vmbr0 continue working
- Only new deployments use prox-net

### Migration Path (Future)

For migrating existing containers:

1. **Create snapshot** of container
2. **Shut down** container
3. **Modify network configuration**:
   ```bash
   pct set <vmid> -net0 name=eth0,bridge=prox-net,ip=dhcp,firewall=1
   ```
4. **Start** container
5. **Verify** DHCP assignment and DNS resolution

## Performance Considerations

### Overhead

- **Network Bridge**: Minimal (<1% CPU)
- **NAT/iptables**: Very low overhead
- **dnsmasq**: Extremely lightweight (1-2 MB RAM)

### Scalability

- **DHCP Pool**: 150 addresses (expandable)
- **DNS Queries**: dnsmasq handles thousands/sec
- **Bridge Performance**: Near line-rate for virtual networks

### Optimization

- Bridge STP disabled (not needed)
- dnsmasq caching enabled
- Direct kernel routing (no userspace bridging)

## Future Enhancements

### Planned Features

1. **Multiple Network Zones**
   - Production network: prox-net-prod
   - Development network: prox-net-dev
   - Network isolation between zones

2. **IPv6 Support**
   - Dual-stack configuration
   - IPv6 DHCP (DHCPv6)

3. **Advanced Firewall Rules**
   - Per-app network policies
   - Traffic shaping
   - DDoS protection

4. **Load Balancing**
   - Integrated L4/L7 load balancer
   - Automatic service discovery
   - Health checking

5. **Network Monitoring**
   - Bandwidth usage per container
   - Connection tracking
   - Traffic analysis

## References

- [Linux Bridge Documentation](https://wiki.linuxfoundation.org/networking/bridge)
- [dnsmasq Manual](https://thekelleys.org.uk/dnsmasq/docs/dnsmasq-man.html)
- [iptables NAT Guide](https://www.netfilter.org/documentation/HOWTO/NAT-HOWTO.html)
- [Proxmox Network Configuration](https://pve.proxmox.com/wiki/Network_Configuration)

## Support

For issues related to network configuration:

1. Check logs: `journalctl -u proximity-dns -f`
2. Verify API status: `GET /api/v1/system/network/status`
3. Review configuration: `/etc/network/interfaces`, `/etc/proximity/dnsmasq.conf`
4. Open GitHub issue with diagnostic output
