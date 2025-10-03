#!/usr/bin/env python3
"""
Network Diagnostic Tool for Proximity
Tests connectivity and network configuration for deployed apps
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.proxmox_service import ProxmoxService
from services.caddy_service import get_caddy_service
from services.app_service import AppService, get_app_service


async def test_lxc_network(proxmox: ProxmoxService, node: str, vmid: int, app_name: str):
    """Test network connectivity for an LXC container"""
    print(f"\n{'='*60}")
    print(f"Testing: {app_name} (LXC {vmid} on {node})")
    print(f"{'='*60}")
    
    try:
        # Check LXC status
        status = await proxmox.get_lxc_status(node, vmid)
        print(f"✓ LXC Status: {status.status.value}")
        
        if status.status.value != "running":
            print(f"⚠️  LXC is not running!")
            return False
        
        # Get LXC IP
        ip = await proxmox.get_lxc_ip(node, vmid)
        if ip:
            print(f"✓ LXC IP: {ip}")
        else:
            print(f"❌ Could not get LXC IP")
            return False
        
        # Check network interface
        try:
            net_info = await proxmox.execute_in_container(node, vmid, "ip -4 addr show eth0")
            print(f"\n📡 Network Interface (eth0):")
            print(net_info)
        except Exception as e:
            print(f"⚠️  Could not get network info: {e}")
        
        # Check Docker status
        try:
            docker_status = await proxmox.execute_in_container(node, vmid, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
            print(f"\n🐳 Docker Containers:")
            print(docker_status)
        except Exception as e:
            print(f"⚠️  Docker not available: {e}")
        
        # Test port 80 listening
        try:
            port_check = await proxmox.execute_in_container(
                node, vmid, 
                "netstat -tlnp 2>/dev/null | grep ':80 ' || ss -tlnp 2>/dev/null | grep ':80 '",
                allow_nonzero_exit=True
            )
            if port_check and "LISTEN" in port_check:
                print(f"\n✓ Port 80 is listening:")
                print(port_check)
            else:
                print(f"\n⚠️  Port 80 does not appear to be listening")
        except Exception as e:
            print(f"⚠️  Could not check port: {e}")
        
        # Test HTTP response from localhost inside LXC
        try:
            http_test = await proxmox.execute_in_container(
                node, vmid,
                "wget -qO- --timeout=5 http://localhost:80 2>&1 | head -20",
                allow_nonzero_exit=True
            )
            if http_test and len(http_test.strip()) > 0:
                print(f"\n✓ HTTP test from localhost successful (first 20 lines):")
                print(http_test[:500])  # Limit output
            else:
                print(f"\n⚠️  HTTP test returned empty response")
        except Exception as e:
            print(f"⚠️  HTTP test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing {app_name}: {e}")
        return False


async def test_caddy_proxy(caddy_service):
    """Test Caddy reverse proxy status"""
    print(f"\n{'='*60}")
    print(f"Testing: Caddy Reverse Proxy")
    print(f"{'='*60}")
    
    if not caddy_service.is_deployed:
        print("⚠️  Caddy is not deployed yet")
        return False
    
    print(f"✓ Caddy is deployed (Node: {caddy_service.caddy_node}, LXC: {caddy_service.caddy_lxc_id})")
    
    # Check if running
    is_running = await caddy_service.is_caddy_running()
    print(f"{'✓' if is_running else '⚠️ '} Caddy Status: {'running' if is_running else 'stopped'}")
    
    # Get IP
    caddy_ip = await caddy_service.get_caddy_ip()
    if caddy_ip:
        print(f"✓ Caddy IP: {caddy_ip}")
        print(f"✓ Access URL: http://{caddy_ip}:8080/")
    else:
        print(f"❌ Could not get Caddy IP")
    
    # Get registered apps
    config = caddy_service.config
    print(f"\n📋 Registered Apps: {len(config.apps)}")
    for app_id, app_config in config.apps.items():
        print(f"  • {app_id}: {app_config['path']} → {app_config['backend']}")
    
    # Check Caddy config
    if is_running:
        try:
            caddyfile = await caddy_service.proxmox.execute_in_container(
                caddy_service.caddy_node,
                caddy_service.caddy_lxc_id,
                "cat /etc/caddy/Caddyfile"
            )
            print(f"\n📄 Caddyfile:")
            print(caddyfile)
        except Exception as e:
            print(f"⚠️  Could not read Caddyfile: {e}")
    
    return is_running


async def main():
    """Run network diagnostics"""
    print("\n" + "="*60)
    print("🔍 PROXIMITY NETWORK DIAGNOSTICS")
    print("="*60)
    
    try:
        # Initialize services
        app_service = get_app_service()
        
        # Load apps
        await app_service._load_apps()
        await app_service._load_catalog()
        
        if not app_service._apps_db:
            print("\n⚠️  No apps deployed yet")
            return
        
        print(f"\n📦 Found {len(app_service._apps_db)} deployed app(s)")
        
        # Test each app
        for app_id, app in app_service._apps_db.items():
            await test_lxc_network(
                app_service.proxmox_service,
                app.node,
                app.lxc_id,
                app.name
            )
            print(f"\nCurrent URL in database: {app.url or 'Not set'}")
        
        # Test Caddy
        if app_service._caddy_service:
            await test_caddy_proxy(app_service._caddy_service)
        else:
            print("\n⚠️  Caddy service not initialized")
        
        print("\n" + "="*60)
        print("✓ Diagnostics complete")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
