#!/usr/bin/env python3
"""
Container Diagnostics Script
Shows all LXC containers in Proxmox and compares with Proximity database
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from services.proxmox_service import ProxmoxService
from models.database import App as DBApp


async def main():
    print("=" * 80)
    print("PROXIMITY CONTAINER DIAGNOSTICS")
    print("=" * 80)
    print()

    # 1. Connect to database
    print("📊 Checking Database...")
    db_path = "proximity.db"  # Default database path
    engine = create_engine(f"sqlite:///{db_path}")
    db = Session(engine)

    db_apps = db.query(DBApp).all()
    print(f"   Found {len(db_apps)} apps in database:")
    for app in db_apps:
        print(
            f"   - {app.hostname} (LXC {app.lxc_id}, status: {app.status}, owner: {app.owner_id or 'None'})"
        )
    print()

    # 2. Connect to Proxmox
    print("🔧 Checking Proxmox...")
    proxmox = ProxmoxService()

    try:
        nodes = await proxmox.get_nodes()
        print(f"   Found {len(nodes)} Proxmox node(s)")

        all_containers = []
        for node in nodes:
            node_name = node.node if hasattr(node, "node") else str(node)
            containers = await proxmox.get_lxc_containers(node_name)
            all_containers.extend([(node_name, c) for c in containers])

        print(f"   Found {len(all_containers)} LXC containers in Proxmox:")
        print()

        # 3. Compare
        print("🔍 Container Analysis:")
        print("=" * 80)

        db_lxc_ids = {app.lxc_id for app in db_apps}

        for node_name, container in all_containers:
            vmid = container["vmid"] if isinstance(container, dict) else container.vmid
            status = container["status"] if isinstance(container, dict) else container.status
            name = (
                container.get("name", "N/A")
                if isinstance(container, dict)
                else getattr(container, "name", "N/A")
            )

            # Get detailed config
            try:
                config = await proxmox.get_container_config(vmid)
                hostname = config.get("hostname", "N/A")
                description = config.get("description", "N/A")

                print(f"\n📦 LXC {vmid} ({node_name})")
                print(f"   Hostname: {hostname}")
                print(f"   Name: {name}")
                print(f"   Status: {status}")
                print(f"   Description: {description}")

                # Check if in database
                if vmid in db_lxc_ids:
                    db_app = next(app for app in db_apps if app.lxc_id == vmid)
                    print(f"   ✅ IN DATABASE as '{db_app.hostname}' (ID: {db_app.id})")
                else:
                    print("   ⚠️  NOT IN DATABASE - Orphan container!")
                    print("   → This container exists in Proxmox but is not tracked by Proximity")
                    print("   → Possible causes:")
                    print("      1. Created manually in Proxmox")
                    print("      2. Failed deployment that didn't save to DB")
                    print("      3. Database was cleared/reset")

            except Exception as e:
                print(f"\n📦 LXC {vmid} ({node_name})")
                print(f"   Status: {status}")
                print(f"   ❌ ERROR getting config: {e}")

        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Database apps: {len(db_apps)}")
        print(f"Proxmox containers: {len(all_containers)}")
        print(f"Orphan containers: {len(all_containers) - len(db_apps)}")
        print()

        # Recommendations
        if len(all_containers) > len(db_apps):
            print("⚠️  RECOMMENDATIONS:")
            print("   1. Check if orphan containers should be imported into Proximity")
            print("   2. If they're old/unused, you can delete them from Proxmox")
            print("   3. To delete: 'pct stop <vmid> && pct destroy <vmid>'")
            print()

    except Exception as e:
        print(f"❌ Error connecting to Proxmox: {e}")
        import traceback

        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
