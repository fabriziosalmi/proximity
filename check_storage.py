#!/usr/bin/env python3
"""
Quick script to list available storage on Proxmox
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.proxmox_service import proxmox_service


async def list_storage():
    """List available storage"""
    
    print("🗄️  Available Storage:")
    print("=" * 70)
    
    try:
        nodes = await proxmox_service.get_nodes()
        node = nodes[0].node
        
        # Get storage list
        client = await proxmox_service._get_client()
        storages = await asyncio.to_thread(
            client.nodes(node).storage.get
        )
        
        for storage in storages:
            name = storage.get('storage', 'N/A')
            storage_type = storage.get('type', 'N/A')
            content = storage.get('content', 'N/A')
            enabled = storage.get('enabled', 0)
            active = storage.get('active', 0)
            
            print(f"\n📦 {name}")
            print(f"   Type: {storage_type}")
            print(f"   Content: {content}")
            print(f"   Enabled: {'✅' if enabled else '❌'}")
            print(f"   Active: {'✅' if active else '❌'}")
            
            # Check if suitable for containers
            if 'rootdir' in content:
                print(f"   ✅ Suitable for LXC containers")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(list_storage())
