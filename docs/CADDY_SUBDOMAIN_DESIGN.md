# Caddy Subdomain-Based Routing with SSL

**Date:** 8 October 2025  
**Feature:** Automatic subdomain creation with SSL certificates for deployed applications  
**Status:** 🚧 In Design

## Current Architecture

### Path-Based Routing
Currently, deployed apps are accessible via path-based URLs:

```
http://<appliance-wan-ip>:8080/nginx-001/*
http://<appliance-wan-ip>:8080/postgres-001/*
```

**Caddy Configuration (Current):**
```caddyfile
:8080 {
    handle_path /nginx-001/* {
        reverse_proxy 10.20.0.130:80
    }
    
    handle_path /postgres-001/* {
        reverse_proxy 10.20.0.145:5432
    }
}
```

### Limitations
❌ Long URLs with paths  
❌ No HTTPS/SSL support  
❌ Apps must handle path prefixes  
❌ Not user-friendly for external access  

## Proposed Architecture

### Subdomain-Based Routing
Deploy apps with automatic subdomain generation:

```
https://nginx-001.prox.local/
https://postgres-001.prox.local/
```

**Benefits:**
✅ Clean, short URLs  
✅ Automatic SSL certificates  
✅ Apps don't need path rewriting  
✅ Professional appearance  
✅ Easier DNS management  

## Design Components

### 1. DNS Resolution

#### Option A: Wildcard DNS (Recommended)
**dnsmasq configuration** on network appliance:

```conf
# /etc/dnsmasq.conf
domain=prox.local
address=/.prox.local/10.20.0.1
```

This resolves ALL `*.prox.local` to the appliance LAN IP.

**Pros:**
- ✅ Zero configuration per app
- ✅ New apps work immediately
- ✅ Simple to maintain

**Cons:**
- ⚠️ Requires clients to use appliance as DNS server
- ⚠️ Or manual /etc/hosts entries

#### Option B: Individual DNS Records
**dnsmasq configuration:**

```conf
address=/nginx-001.prox.local/10.20.0.1
address=/postgres-001.prox.local/10.20.0.1
```

**Pros:**
- ✅ Explicit control per app

**Cons:**
- ❌ Requires config update per deployment
- ❌ More complex management

**Decision:** Use **Option A (Wildcard DNS)**

---

### 2. SSL Certificate Strategy

#### Option A: Self-Signed Wildcard Certificate (Recommended)
Generate one wildcard cert for `*.prox.local`:

```bash
openssl req -x509 -newkey rsa:4096 \
  -keyout /etc/caddy/certs/wildcard.key \
  -out /etc/caddy/certs/wildcard.crt \
  -days 3650 -nodes \
  -subj "/CN=*.prox.local" \
  -addext "subjectAltName=DNS:*.prox.local,DNS:prox.local"
```

**Caddy Configuration:**
```caddyfile
*.prox.local {
    tls /etc/caddy/certs/wildcard.crt /etc/caddy/certs/wildcard.key
}
```

**Pros:**
- ✅ One certificate for all apps
- ✅ No cert generation per app
- ✅ Faster provisioning
- ✅ Simple management

**Cons:**
- ⚠️ Requires manual trust on client machines
- ⚠️ Browser security warnings (one-time accept)

#### Option B: Individual Self-Signed Certificates
Generate cert per app:

```bash
openssl req -x509 -newkey rsa:2048 \
  -keyout nginx-001.key -out nginx-001.crt \
  -days 365 -nodes -subj "/CN=nginx-001.prox.local"
```

**Pros:**
- ✅ More granular control

**Cons:**
- ❌ Cert generation per deployment
- ❌ More files to manage
- ❌ Still requires manual trust

#### Option C: Internal CA + Signed Certificates
Create internal CA, distribute to clients, sign app certs:

**Pros:**
- ✅ No browser warnings if CA trusted
- ✅ Professional setup

**Cons:**
- ❌ Complex setup
- ❌ CA management overhead
- ❌ Overkill for homelab

**Decision:** Use **Option A (Wildcard Self-Signed)**

---

### 3. Caddy Configuration

#### New Caddyfile Structure

```caddyfile
# Admin API
:2019 {
    bind 127.0.0.1
}

# Health check endpoint
:2020 {
    respond /health "OK" 200
}

# Wildcard subdomain routing with SSL
*.prox.local {
    # Use wildcard certificate
    tls /etc/caddy/certs/wildcard.crt /etc/caddy/certs/wildcard.key
    
    # Dynamic routing based on subdomain
    @nginx-001 host nginx-001.prox.local
    handle @nginx-001 {
        reverse_proxy 10.20.0.130:80
    }
    
    @postgres-001 host postgres-001.prox.local
    handle @postgres-001 {
        reverse_proxy 10.20.0.145:5432
    }
    
    # Fallback for unknown subdomains
    handle {
        respond "Application not found" 404
    }
}

# Main domain - Proximity UI (optional)
prox.local {
    tls /etc/caddy/certs/wildcard.crt /etc/caddy/certs/wildcard.key
    reverse_proxy localhost:8765
}
```

#### Dynamic Generation
The `CaddyConfig` class will generate this structure dynamically:

```python
def generate_caddyfile(self, deployed_apps: list) -> str:
    blocks = []
    
    # Admin API
    blocks.append(self._admin_block())
    
    # Health check
    blocks.append(self._health_block())
    
    # Wildcard subdomain routing
    subdomain_block = self._subdomain_block(deployed_apps)
    blocks.append(subdomain_block)
    
    return "\n\n".join(blocks)

def _subdomain_block(self, apps: list) -> str:
    rules = []
    for app in apps:
        hostname = app['hostname']
        target_ip = app['target_ip']
        target_port = app['target_port']
        
        rule = f"""
    @{hostname} host {hostname}.prox.local
    handle @{hostname} {{
        reverse_proxy {target_ip}:{target_port}
    }}"""
        rules.append(rule)
    
    fallback = """
    handle {
        respond "Application not found" 404
    }"""
    
    return f"""*.prox.local {{
    tls /etc/caddy/certs/wildcard.crt /etc/caddy/certs/wildcard.key
{chr(10).join(rules)}
{fallback}
}}"""
```

---

### 4. Certificate Management

#### Initialization (One-Time)
When network appliance is provisioned:

```python
async def _generate_wildcard_certificate(self):
    """Generate wildcard SSL certificate for *.prox.local"""
    cert_dir = "/etc/caddy/certs"
    cert_file = f"{cert_dir}/wildcard.crt"
    key_file = f"{cert_dir}/wildcard.key"
    
    # Create cert directory
    await self._exec_command(f"mkdir -p {cert_dir}")
    
    # Generate wildcard certificate
    cmd = f"""
    openssl req -x509 -newkey rsa:4096 \
      -keyout {key_file} \
      -out {cert_file} \
      -days 3650 -nodes \
      -subj "/CN=*.prox.local/O=Proximity Homelab" \
      -addext "subjectAltName=DNS:*.prox.local,DNS:prox.local"
    """
    
    result = await self._exec_command(cmd)
    
    if result['exit_code'] == 0:
        logger.info("Wildcard SSL certificate generated successfully")
    else:
        logger.error(f"Failed to generate certificate: {result['stderr']}")
        raise Exception("Certificate generation failed")
    
    # Set permissions
    await self._exec_command(f"chmod 600 {key_file}")
    await self._exec_command(f"chmod 644 {cert_file}")
```

#### Certificate Renewal
Wildcard cert valid for 10 years - no automatic renewal needed for homelab.

For production, implement renewal script (e.g., monthly cron):
```bash
#!/bin/sh
# /etc/periodic/monthly/renew-ssl-cert

openssl req -x509 -newkey rsa:4096 \
  -keyout /etc/caddy/certs/wildcard.key \
  -out /etc/caddy/certs/wildcard.crt \
  -days 3650 -nodes \
  -subj "/CN=*.prox.local/O=Proximity Homelab" \
  -addext "subjectAltName=DNS:*.prox.local,DNS:prox.local"

rc-service caddy reload
```

---

### 5. Client Configuration

#### Automatic DNS (Recommended)
Configure clients to use network appliance as DNS server:

**macOS/Linux:**
```bash
# /etc/resolv.conf
nameserver 10.20.0.1  # Network appliance LAN IP
```

**Windows:**
```powershell
# Network adapter properties
DNS Server: 10.20.0.1
```

#### Manual /etc/hosts (Fallback)
For clients that can't change DNS:

```bash
# /etc/hosts
10.20.0.1  nginx-001.prox.local
10.20.0.1  postgres-001.prox.local
10.20.0.1  prox.local
```

**Script to export:**
```bash
# On appliance, generate hosts entries
cat /var/lib/misc/dnsmasq.leases | awk '{print "10.20.0.1  " $4 ".prox.local"}'
```

#### Trust SSL Certificate
Import wildcard certificate to client trust store:

**macOS:**
```bash
# Download cert from appliance
scp root@<appliance-wan-ip>:/etc/caddy/certs/wildcard.crt ~/Downloads/

# Import to keychain
sudo security add-trusted-cert -d \
  -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/Downloads/wildcard.crt
```

**Linux:**
```bash
sudo cp wildcard.crt /usr/local/share/ca-certificates/proximity.crt
sudo update-ca-certificates
```

**Windows:**
```powershell
# Import to Trusted Root Certification Authorities
Import-Certificate -FilePath wildcard.crt -CertStoreLocation Cert:\LocalMachine\Root
```

---

## Implementation Plan

### Phase 1: Certificate Generation ✅
- [ ] Add `_generate_wildcard_certificate()` method to `NetworkApplianceOrchestrator`
- [ ] Call during appliance provisioning
- [ ] Store cert/key in `/etc/caddy/certs/`
- [ ] Verify permissions (600 for key, 644 for cert)

### Phase 2: DNS Configuration ✅
- [ ] Update dnsmasq config template in `_generate_dnsmasq_config()`
- [ ] Add wildcard domain: `address=/.prox.local/10.20.0.1`
- [ ] Restart dnsmasq service after config change
- [ ] Test DNS resolution from client

### Phase 3: Caddy Reconfiguration 🚧
- [ ] Modify `CaddyConfig.generate_caddyfile()` in `caddy_service.py`
- [ ] Switch from path-based to subdomain-based routing
- [ ] Add wildcard TLS block
- [ ] Generate dynamic `handle @hostname` rules per app
- [ ] Add 404 fallback for unknown subdomains

### Phase 4: Integration Testing 🚧
- [ ] Deploy test app (nginx-001)
- [ ] Verify DNS resolution: `nslookup nginx-001.prox.local 10.20.0.1`
- [ ] Test HTTPS access: `curl -k https://nginx-001.prox.local`
- [ ] Check certificate validity
- [ ] Verify reverse proxy to container

### Phase 5: UI Updates 📋
- [ ] Update Infrastructure page to show subdomain URLs
- [ ] Add "Copy URL" button for easy access
- [ ] Show SSL certificate status
- [ ] Add certificate download link for users

### Phase 6: Documentation 📋
- [ ] User guide: How to configure DNS on client
- [ ] Certificate trust instructions per OS
- [ ] Troubleshooting section
- [ ] Update QUICKSTART.md with subdomain access

---

## Testing Checklist

### DNS Resolution
```bash
# From client machine
nslookup nginx-001.prox.local 10.20.0.1
# Expected: 10.20.0.1

dig @10.20.0.1 postgres-001.prox.local
# Expected: A record pointing to 10.20.0.1
```

### SSL Certificate
```bash
# Check certificate details
openssl s_client -connect nginx-001.prox.local:443 -showcerts
# Expected: CN=*.prox.local, valid dates

# Verify SAN
openssl x509 -in /etc/caddy/certs/wildcard.crt -text -noout | grep DNS
# Expected: DNS:*.prox.local, DNS:prox.local
```

### HTTP/HTTPS Access
```bash
# Test HTTPS (insecure for self-signed)
curl -k https://nginx-001.prox.local
# Expected: nginx welcome page

# Test HTTP redirect (if configured)
curl -I http://nginx-001.prox.local
# Expected: 301/308 redirect to HTTPS

# Test unknown subdomain
curl -k https://nonexistent.prox.local
# Expected: 404 "Application not found"
```

### Reverse Proxy
```bash
# Verify backend is reached
curl -k https://nginx-001.prox.local -H "X-Test-Header: value"
# Check nginx logs on container for header

# Test WebSocket upgrade (for apps like Caddy itself)
curl -k -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  https://app.prox.local
```

---

## Rollback Plan

If subdomain routing causes issues:

### 1. Revert Caddy Config
```bash
# On appliance
cat > /etc/caddy/Caddyfile <<EOF
:8080 {
    handle_path /nginx-001/* {
        reverse_proxy 10.20.0.130:80
    }
}
EOF

rc-service caddy reload
```

### 2. Keep Wildcard DNS
Wildcard DNS doesn't hurt - can stay enabled even with path-based routing.

### 3. Certificate Cleanup (Optional)
```bash
rm /etc/caddy/certs/wildcard.{crt,key}
```

---

## Security Considerations

### Self-Signed Certificate Risks
⚠️ **Browser warnings** - Users must manually accept certificate  
⚠️ **Not trusted by default** - Requires trust store import  
⚠️ **10-year validity** - Long-lived cert, consider shorter for production  

### Mitigation
✅ Document trust process clearly  
✅ Provide one-click certificate download  
✅ Consider internal CA for teams (future enhancement)  

### Network Isolation
✅ LAN-only access by default (10.20.0.0/24)  
✅ Firewall rules prevent external access  
✅ No public DNS records  

---

## Future Enhancements

### 1. Internal Certificate Authority
- Create Proximity CA
- Sign per-app certificates
- Distribute CA cert to clients
- Zero browser warnings

### 2. Let's Encrypt Integration
- For WAN-accessible deployments
- Automatic DNS-01 challenge
- Valid public certificates
- Requires public DNS

### 3. mTLS Client Certificates
- Client authentication via certificates
- Enhanced security for sensitive apps
- Certificate-based access control

### 4. Automatic Client Configuration
- DHCP option 6 (DNS server)
- Automatic trust store injection (MDM)
- Zero manual configuration

---

## Open Questions

1. **Port 443 vs 8080?**
   - Current: Port 8080 (path-based)
   - Proposed: Port 443 (standard HTTPS)
   - Decision: Use 443 for subdomain routing

2. **Main domain behavior?**
   - Should `prox.local` point to Proximity UI?
   - Or serve as landing page with app links?
   - Decision: Proxy to Proximity UI (port 8765)

3. **Subdomain collision?**
   - What if app named "admin" or "api"?
   - Reserve certain names?
   - Decision: Prefix all apps with type (web-, db-, etc.)? Or simple collision check?

4. **Certificate distribution?**
   - Provide download endpoint in UI?
   - Automatically push to clients via DHCP/DNS?
   - Decision: Manual download + documented trust process

---

**Status:** 🚧 Design Complete - Ready for Implementation  
**Next Step:** Phase 1 - Certificate Generation  
**Owner:** Proximity Core Team  
**Priority:** High - Key UX Improvement
