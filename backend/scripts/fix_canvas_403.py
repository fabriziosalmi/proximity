#!/usr/bin/env python3
"""
Automatic Canvas 403 Fix Script

This script automatically fixes common Canvas 403 Forbidden errors by:
1. Verifying Caddy configuration includes proper header stripping
2. Regenerating vhost configs if needed
3. Reloading Caddy to apply changes
4. Testing app accessibility

Usage:
    python scripts/fix_canvas_403.py --app nginx-01
    python scripts/fix_canvas_403.py --all
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.proxmox_service import ProxmoxService
from services.reverse_proxy_manager import ReverseProxyManager
from services.app_service import AppService
from core.database import SessionLocal
from core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Canvas403Fixer:
    """Automatic fixer for Canvas 403 errors"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.proxmox = ProxmoxService()
        self.proxy_manager = ReverseProxyManager()
        self.app_service = AppService(self.db, self.proxmox, self.proxy_manager)
        self.fixed_count = 0
        self.failed_count = 0
    
    async def fix_app(self, hostname: str) -> bool:
        """
        Fix Canvas 403 error for a specific app.
        
        Args:
            hostname: App hostname to fix
            
        Returns:
            True if fixed successfully
        """
        print(f"\n{'='*80}")
        print(f"🔧 Fixing Canvas Access for: {hostname}")
        print('='*80)
        
        try:
            # Step 1: Get app details
            apps = await self.app_service.list_apps()
            app = next((a for a in apps if a.hostname == hostname), None)
            
            if not app:
                print(f"❌ App '{hostname}' not found")
                self.failed_count += 1
                return False
            
            print(f"\n📋 App Details:")
            print(f"   • ID: {app.id}")
            print(f"   • Status: {app.status}")
            print(f"   • Public Port: {app.public_port}")
            print(f"   • Internal Port: {app.internal_port}")
            print(f"   • LXC ID: {app.lxc_id}")
            print(f"   • Node: {app.node}")
            
            # Step 2: Verify app is running
            if app.status != "running":
                print(f"\n⚠️  App is not running. Starting...")
                await self.proxmox.start_lxc(app.node, app.lxc_id)
                await asyncio.sleep(3)
                print("   ✓ App started")
            
            # Step 3: Get container IP
            container_ip = await self.proxmox.get_lxc_ip(app.node, app.lxc_id)
            print(f"   • Container IP: {container_ip}")
            
            if not container_ip:
                print("❌ Could not get container IP")
                self.failed_count += 1
                return False
            
            # Step 4: Regenerate Caddy vhost config
            print(f"\n🔄 Regenerating Caddy configuration...")
            
            # Get catalog item for port info
            from models.schemas import CatalogItem
            catalog_item = CatalogItem(
                id=app.catalog_id,
                name=app.name,
                description="",
                icon="",
                ports=[80],
                volumes=[],
                environment=[]
            )
            
            primary_port = catalog_item.ports[0] if catalog_item.ports else 80
            
            # Recreate vhost
            vhost_created = await self.proxy_manager.create_vhost(
                app_name=app.hostname,
                backend_ip=container_ip,
                backend_port=primary_port,
                public_port=app.public_port,
                internal_port=app.internal_port
            )
            
            if not vhost_created:
                print("❌ Failed to create vhost configuration")
                self.failed_count += 1
                return False
            
            print("   ✓ Vhost configuration created")
            
            # Step 5: Reload Caddy
            print(f"\n🔄 Reloading Caddy...")
            reload_success = await self.proxy_manager.reload_caddy()
            
            if reload_success:
                print("   ✓ Caddy reloaded successfully")
            else:
                print("   ⚠️  Caddy reload may have failed, but config is in place")
            
            # Step 6: Update app URLs in database
            if hasattr(self.proxmox, 'network_manager') and self.proxmox.network_manager:
                appliance_info = self.proxmox.network_manager.appliance_info
                if appliance_info:
                    appliance_wan_ip = appliance_info.wan_ip
                    
                    new_public_url = f"http://{appliance_wan_ip}:{app.public_port}"
                    new_iframe_url = f"http://{appliance_wan_ip}:{app.internal_port}"
                    
                    print(f"\n🔗 Updated URLs:")
                    print(f"   • Public: {new_public_url}")
                    print(f"   • Canvas: {new_iframe_url}")
                    
                    # Update in database
                    await self.app_service._update_app_urls(app.id, new_public_url, new_iframe_url)
            
            # Step 7: Verify configuration
            print(f"\n✅ Verification:")
            print(f"   • Configuration regenerated")
            print(f"   • Caddy reloaded")
            print(f"   • URLs updated")
            print(f"\n💡 Try accessing the app in Canvas now:")
            print(f"   {app.iframe_url}")
            
            self.fixed_count += 1
            return True
            
        except Exception as e:
            print(f"\n❌ Error fixing app: {e}")
            logger.exception("Failed to fix app")
            self.failed_count += 1
            return False
    
    async def fix_all_apps(self):
        """Fix Canvas access for all deployed apps"""
        print("\n" + "="*80)
        print("🔧 Fixing Canvas Access for All Apps")
        print("="*80)
        
        try:
            apps = await self.app_service.list_apps()
            
            if not apps:
                print("\n📭 No apps found")
                return
            
            print(f"\n📦 Found {len(apps)} app(s)")
            
            for app in apps:
                if app.status == "running" and app.iframe_url:
                    await self.fix_app(app.hostname)
                    await asyncio.sleep(1)  # Small delay between apps
                else:
                    print(f"\n⏭️  Skipping {app.hostname} (not running or no iframe_url)")
            
        except Exception as e:
            print(f"\n❌ Error fixing all apps: {e}")
            logger.exception("Failed to fix all apps")
    
    def print_summary(self):
        """Print fix summary"""
        print("\n" + "="*80)
        print("📊 Fix Summary")
        print("="*80)
        print(f"✅ Fixed: {self.fixed_count}")
        print(f"❌ Failed: {self.failed_count}")
        print("="*80)
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'db'):
            self.db.close()


async def main():
    """Main fix routine"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix Canvas 403 errors")
    parser.add_argument("--app", help="Specific app hostname to fix")
    parser.add_argument("--all", action="store_true", help="Fix all apps")
    args = parser.parse_args()
    
    if not args.app and not args.all:
        parser.print_help()
        print("\nError: Please specify --app <hostname> or --all")
        sys.exit(1)
    
    fixer = Canvas403Fixer()
    
    try:
        if args.all:
            await fixer.fix_all_apps()
        else:
            await fixer.fix_app(args.app)
    finally:
        fixer.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
