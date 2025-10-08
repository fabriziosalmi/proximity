#!/usr/bin/env python3
"""
Test script to verify container deployment with vmbr0 + DHCP
This script creates a simple test container to validate the simplified networking
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.proxmox_service import proxmox_service


async def test_vmbr0_deployment():
    """Test creating a container with vmbr0 + DHCP"""
    
    print("=" * 70)
    print("🧪 Testing Container Deployment with vmbr0 + DHCP")
    print("=" * 70)
    
    try:
        # Step 1: Test Proxmox connection
        print("\n[1/5] Testing Proxmox connection...")
        is_connected = await proxmox_service.test_connection()
        if not is_connected:
            print("❌ Failed to connect to Proxmox")
            return False
        print("✅ Connected to Proxmox")
        
        # Step 2: Get available nodes
        print("\n[2/5] Getting available nodes...")
        nodes = await proxmox_service.get_nodes()
        if not nodes:
            print("❌ No nodes available")
            return False
        
        node = nodes[0].node
        print(f"✅ Found node: {node}")
        
        # Step 3: Check for test container (VMID 9998)
        test_vmid = 9998
        print(f"\n[3/5] Checking if test container {test_vmid} already exists...")
        
        try:
            status = await proxmox_service.get_lxc_status(node, test_vmid)
            print(f"⚠️  Container {test_vmid} already exists with status: {status.status}")
            print(f"   Deleting old test container...")
            
            # Stop if running
            if status.status == "running":
                await proxmox_service.stop_lxc(node, test_vmid, force=True)
                await asyncio.sleep(3)
            
            # Delete
            await proxmox_service.destroy_lxc(node, test_vmid, force=True)
            await asyncio.sleep(2)
            print(f"✅ Old container deleted")
            
        except Exception as e:
            print(f"✅ No existing container found (good!)")
        
        # Step 4: Create new test container with vmbr0 + DHCP
        print(f"\n[4/5] Creating test container {test_vmid} with vmbr0 + DHCP...")
        
        config = {
            'hostname': 'test-vmbr0',
            'cores': 1,
            'memory': 512,
            'rootfs': 'local-lvm:8',  # 8GB root filesystem on local-lvm
            'password': 'testpass123',
            'description': 'Test container for vmbr0 DHCP networking'
        }
        
        result = await proxmox_service.create_lxc(node, test_vmid, config)
        print(f"✅ Container creation started: {result}")
        
        # Wait for creation to complete
        print(f"   Waiting for container creation...")
        await asyncio.sleep(10)
        
        # Step 5: Verify container configuration
        print(f"\n[5/5] Verifying container network configuration...")
        
        # Get container config
        lxc_config = await proxmox_service.get_lxc_config(node, test_vmid)
        print(f"\n📋 Container Configuration:")
        print(f"   VMID: {test_vmid}")
        print(f"   Hostname: {lxc_config.get('hostname', 'N/A')}")
        print(f"   Network: {lxc_config.get('net0', 'N/A')}")
        
        # Verify it's using vmbr0 with DHCP
        net0 = lxc_config.get('net0', '')
        if 'bridge=vmbr0' in net0 and 'ip=dhcp' in net0:
            print(f"✅ Network config correct: vmbr0 with DHCP!")
        else:
            print(f"❌ Network config incorrect!")
            print(f"   Expected: bridge=vmbr0 with ip=dhcp")
            print(f"   Got: {net0}")
            return False
        
        # Start container
        print(f"\n🚀 Starting container...")
        await proxmox_service.start_lxc(node, test_vmid)
        await asyncio.sleep(5)
        
        # Check status
        status = await proxmox_service.get_lxc_status(node, test_vmid)
        print(f"   Status: {status.status}")
        
        if status.status == "running":
            print(f"✅ Container is running!")
            
            # Try to get IP address
            print(f"\n🔍 Checking for DHCP-assigned IP...")
            await asyncio.sleep(5)  # Wait for DHCP
            
            try:
                # Get IP from inside container
                ip_result = await proxmox_service.exec_command(
                    node, test_vmid, 
                    "ip -4 addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1"
                )
                
                if ip_result and ip_result.strip():
                    print(f"✅ Container got DHCP IP: {ip_result.strip()}")
                else:
                    print(f"⚠️  Container started but no IP yet (may need more time)")
                    
            except Exception as e:
                print(f"⚠️  Could not check IP (container may still be booting): {e}")
        else:
            print(f"⚠️  Container status: {status.status}")
        
        print("\n" + "=" * 70)
        print("✅ TEST SUCCESSFUL!")
        print("=" * 70)
        print(f"\n📝 Summary:")
        print(f"   • Container VMID: {test_vmid}")
        print(f"   • Network: vmbr0 with DHCP")
        print(f"   • Status: {status.status}")
        print(f"   • Node: {node}")
        print(f"\n💡 To clean up, run:")
        print(f"   pct stop {test_vmid} && pct destroy {test_vmid}")
        print("")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point"""
    success = await test_vmbr0_deployment()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
