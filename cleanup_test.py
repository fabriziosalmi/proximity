#!/usr/bin/env python3
"""Quick cleanup script for test container"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.proxmox_service import proxmox_service


async def cleanup():
    try:
        nodes = await proxmox_service.get_nodes()
        node = nodes[0].node
        vmid = 9998
        
        print(f'🧹 Cleaning up test container {vmid}...')
        
        # Check if exists
        try:
            status = await proxmox_service.get_lxc_status(node, vmid)
            print(f'   Found container with status: {status.status}')
            
            # Stop if running
            if status.status == 'running':
                print(f'   Stopping container...')
                await proxmox_service.stop_lxc(node, vmid, force=True)
                await asyncio.sleep(3)
            
            # Delete
            print(f'   Deleting container...')
            await proxmox_service.destroy_lxc(node, vmid, force=True)
            await asyncio.sleep(2)
            print(f'✅ Container {vmid} deleted successfully')
            
        except Exception as e:
            print(f'⚠️  Container {vmid} not found or already deleted: {e}')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(cleanup())
