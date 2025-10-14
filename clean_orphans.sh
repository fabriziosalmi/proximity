#!/bin/bash
# Clean Orphan Containers Script

echo "=================================================="
echo "PROXIMITY - ORPHAN CONTAINER CLEANUP"
echo "=================================================="
echo ""
echo "This script will delete LXC containers 101 and 102"
echo "which are not tracked by Proximity database."
echo ""
echo "Container 101: test-nginx (ORPHAN)"
echo "Container 102: test-nginx (ORPHAN)"
echo ""
echo "⚠️  WARNING: This action cannot be undone!"
echo ""
read -p "Do you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted by user"
    exit 1
fi

echo ""
echo "🧹 Cleaning up orphan containers..."
echo ""

# Stop and destroy container 101
echo "📦 Stopping LXC 101..."
ssh root@192.168.100.102 "pct stop 101"
if [ $? -eq 0 ]; then
    echo "✓ LXC 101 stopped"
    echo "🗑️  Destroying LXC 101..."
    ssh root@192.168.100.102 "pct destroy 101"
    if [ $? -eq 0 ]; then
        echo "✓ LXC 101 destroyed"
    else
        echo "❌ Failed to destroy LXC 101"
    fi
else
    echo "❌ Failed to stop LXC 101"
fi

echo ""

# Stop and destroy container 102
echo "📦 Stopping LXC 102..."
ssh root@192.168.100.102 "pct stop 102"
if [ $? -eq 0 ]; then
    echo "✓ LXC 102 stopped"
    echo "🗑️  Destroying LXC 102..."
    ssh root@192.168.100.102 "pct destroy 102"
    if [ $? -eq 0 ]; then
        echo "✓ LXC 102 destroyed"
    else
        echo "❌ Failed to destroy LXC 102"
    fi
else
    echo "❌ Failed to stop LXC 102"
fi

echo ""
echo "=================================================="
echo "✅ CLEANUP COMPLETE"
echo "=================================================="
echo ""
echo "Run diagnose_containers.py to verify:"
echo "  python3 diagnose_containers.py"
echo ""
