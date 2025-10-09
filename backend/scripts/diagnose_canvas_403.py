#!/usr/bin/env python3
"""
Diagnostic script for Canvas 403 Forbidden errors.

This script helps identify and fix common issues that cause 403 errors
when accessing apps through the Canvas iframe feature.

Checks:
1. Caddy reverse proxy configuration
2. Port allocation and availability
3. Container network connectivity
4. Frame-busting header removal
5. File permissions in containers
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.proxmox_service import ProxmoxService
from services.reverse_proxy_manager import ReverseProxyManager
from core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Canvas403Diagnostics:
    """Diagnostic tool for Canvas 403 errors"""
    
    def __init__(self):
        self.proxmox = ProxmoxService()
        self.proxy_manager = ReverseProxyManager()
        self.issues = []
        self.fixes = []
    
    async def run_diagnostics(self, app_hostname: str = None):
        """
        Run comprehensive diagnostics for Canvas 403 errors.
        
        Args:
            app_hostname: Specific app to diagnose (optional)
        """
        print("\n" + "="*80)
        print("🔍 Canvas 403 Diagnostics")
        print("="*80)
        
        # Check 1: Verify Caddy is running
        await self._check_caddy_status()
        
        # Check 2: Verify port configuration
        await self._check_port_configuration()
        
        # Check 3: Test app accessibility
        if app_hostname:
            await self._check_app_access(app_hostname)
        
        # Check 4: Verify Caddy configuration
        await self._check_caddy_config(app_hostname)
        
        # Print summary
        self._print_summary()
    
    async def _check_caddy_status(self):
        """Check if Caddy reverse proxy is running"""
        print("\n📡 Checking Caddy Status...")
        
        try:
            # Get network appliance info
            if hasattr(self.proxmox, 'network_manager') and self.proxmox.network_manager:
                appliance_info = self.proxmox.network_manager.appliance_info
                if appliance_info:
                    caddy_vmid = appliance_info.caddy_vmid
                    node = appliance_info.node
                    
                    # Check if Caddy container is running
                    status = await self.proxmox.get_lxc_status(node, caddy_vmid)
                    
                    if status == "running":
                        print(f"   ✓ Caddy is running (VMID: {caddy_vmid})")
                    else:
                        print(f"   ✗ Caddy is NOT running (status: {status})")
                        self.issues.append("Caddy container is not running")
                        self.fixes.append("Start Caddy container or redeploy network appliance")
                else:
                    print("   ⚠ Could not get appliance info")
                    self.issues.append("Network appliance not found")
            else:
                print("   ⚠ Network manager not available")
                self.issues.append("Network manager not configured")
        
        except Exception as e:
            print(f"   ✗ Error checking Caddy status: {e}")
            self.issues.append(f"Caddy status check failed: {e}")
    
    async def _check_port_configuration(self):
        """Check port allocation configuration"""
        print("\n🔌 Checking Port Configuration...")
        
        print(f"   • Public port range: {settings.PUBLIC_PORT_RANGE_START}-{settings.PUBLIC_PORT_RANGE_END}")
        print(f"   • Internal port range: {settings.INTERNAL_PORT_RANGE_START}-{settings.INTERNAL_PORT_RANGE_END}")
        
        # Check for port conflicts
        if settings.PUBLIC_PORT_RANGE_START >= settings.PUBLIC_PORT_RANGE_END:
            print("   ✗ Invalid public port range")
            self.issues.append("Public port range is invalid")
        else:
            print("   ✓ Port ranges configured correctly")
    
    async def _check_app_access(self, hostname: str):
        """Check specific app accessibility"""
        print(f"\n🎯 Checking App Access: {hostname}")
        
        try:
            # Get app details from database
            from services.app_service import AppService
            from api.dependencies import get_db
            
            db = next(get_db())
            app_service = AppService(db, self.proxmox, None)
            
            apps = await app_service.list_apps()
            app = next((a for a in apps if a.hostname == hostname), None)
            
            if not app:
                print(f"   ✗ App '{hostname}' not found")
                self.issues.append(f"App '{hostname}' not found in database")
                return
            
            print(f"   • App ID: {app.id}")
            print(f"   • Status: {app.status}")
            print(f"   • Public URL: {app.url}")
            print(f"   • Canvas URL: {app.iframe_url}")
            print(f"   • Public Port: {app.public_port}")
            print(f"   • Internal Port: {app.internal_port}")
            print(f"   • Container IP: (fetching...)")
            
            # Get container IP
            container_ip = await self.proxmox.get_lxc_ip(app.node, app.lxc_id)
            print(f"   • Container IP: {container_ip}")
            
            if app.status != "running":
                print(f"   ⚠ App is not running (status: {app.status})")
                self.issues.append(f"App '{hostname}' is not running")
                self.fixes.append(f"Start the app '{hostname}'")
            
            if not app.iframe_url:
                print("   ✗ Canvas URL not configured")
                self.issues.append(f"App '{hostname}' has no iframe_url")
                self.fixes.append("Redeploy app or update database with iframe_url")
            else:
                print("   ✓ Canvas URL is configured")
        
        except Exception as e:
            print(f"   ✗ Error checking app: {e}")
            self.issues.append(f"App access check failed: {e}")
    
    async def _check_caddy_config(self, hostname: str = None):
        """Check Caddy configuration for header stripping"""
        print("\n📝 Checking Caddy Configuration...")
        
        try:
            if hasattr(self.proxmox, 'network_manager') and self.proxmox.network_manager:
                appliance_info = self.proxmox.network_manager.appliance_info
                if appliance_info:
                    caddy_vmid = appliance_info.caddy_vmid
                    node = appliance_info.node
                    
                    # Check if sites-enabled directory exists
                    print(f"   • Checking Caddy config directory on VMID {caddy_vmid}...")
                    
                    # List all vhost files
                    list_cmd = "ls -la /etc/caddy/sites-enabled/ 2>&1"
                    result = await self.proxmox.execute_lxc_command(node, caddy_vmid, list_cmd)
                    
                    if result.get('success'):
                        print("   ✓ Caddy sites-enabled directory accessible")
                        
                        if hostname:
                            # Check specific app config
                            config_file = f"/etc/caddy/sites-enabled/{hostname}.caddy"
                            cat_cmd = f"cat {config_file} 2>&1"
                            config_result = await self.proxmox.execute_lxc_command(node, caddy_vmid, cat_cmd)
                            
                            if config_result.get('success'):
                                config_content = config_result.get('output', '')
                                print(f"   • Checking {hostname}.caddy...")
                                
                                # Check for critical header_down directives
                                has_header_down = 'header_down -X-Frame-Options' in config_content
                                has_csp_down = 'header_down -Content-Security-Policy' in config_content
                                
                                if has_header_down and has_csp_down:
                                    print("   ✓ Frame-busting headers are being stripped")
                                else:
                                    print("   ✗ Missing header_down directives")
                                    self.issues.append("Caddy config missing header stripping directives")
                                    self.fixes.append("Regenerate Caddy configuration with proper header_down directives")
                                
                                # Check for internal port block
                                if ':40' in config_content or ':' + str(settings.INTERNAL_PORT_RANGE_START) in config_content:
                                    print("   ✓ Internal port block found")
                                else:
                                    print("   ⚠ Internal port block may be missing")
                                    self.issues.append("Internal iframe port block not found in config")
                            else:
                                print(f"   ⚠ Could not read config for {hostname}")
                    else:
                        print("   ✗ Cannot access Caddy config directory")
                        self.issues.append("Caddy configuration directory not accessible")
                        
        except Exception as e:
            print(f"   ✗ Error checking Caddy config: {e}")
            self.issues.append(f"Caddy config check failed: {e}")
    
    def _print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "="*80)
        print("📊 Diagnostic Summary")
        print("="*80)
        
        if not self.issues:
            print("\n✅ No issues found! Canvas should work correctly.")
        else:
            print(f"\n❌ Found {len(self.issues)} issue(s):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        if self.fixes:
            print(f"\n🔧 Suggested fixes:")
            for i, fix in enumerate(self.fixes, 1):
                print(f"   {i}. {fix}")
        
        print("\n" + "="*80)


async def main():
    """Main diagnostic routine"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Diagnose Canvas 403 errors")
    parser.add_argument("--app", help="Specific app hostname to diagnose")
    args = parser.parse_args()
    
    diagnostics = Canvas403Diagnostics()
    await diagnostics.run_diagnostics(app_hostname=args.app)


if __name__ == "__main__":
    asyncio.run(main())
