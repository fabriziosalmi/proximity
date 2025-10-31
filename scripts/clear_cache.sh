#!/bin/bash
# Complete cache clearing script for Proximity

set -e

echo "🧹 Proximity Cache Clearing Script"
echo "=================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Function to print colored output
print_status() {
    echo -e "\033[1;34m→\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m✓\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m⚠\033[0m $1"
}

# 1. Clear Python caches
print_status "Clearing Python caches..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
rm -rf .pytest_cache tests/.pytest_cache e2e_tests/.pytest_cache 2>/dev/null || true
print_success "Python caches cleared"

# 2. Backup database
if [ -f "backend/proximity.db" ]; then
    BACKUP_NAME="backend/proximity_backup_$(date +%Y%m%d_%H%M%S).db"
    cp backend/proximity.db "$BACKUP_NAME"
    print_success "Database backed up to: $BACKUP_NAME"
fi

# 3. Update frontend cache version
print_status "Updating frontend cache version..."
DATE=$(date +%Y%m%d)
NEW_VERSION="${DATE}-$(($(date +%s) % 100))"

if [ -f "backend/frontend/index.html" ]; then
    # macOS sed syntax
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/\?v=[0-9]*-[0-9]*/\?v=${NEW_VERSION}/g" backend/frontend/index.html
    else
        # Linux sed syntax
        sed -i "s/\?v=[0-9]*-[0-9]*/\?v=${NEW_VERSION}/g" backend/frontend/index.html
    fi
    print_success "Frontend cache version updated to: v=${NEW_VERSION}"
else
    print_warning "backend/frontend/index.html not found"
fi

# 4. Check if backend is running and offer to restart
print_status "Checking backend server..."
BACKEND_PID=$(lsof -ti:8765 2>/dev/null || true)

if [ -n "$BACKEND_PID" ]; then
    echo ""
    echo "Backend server is running (PID: $BACKEND_PID)"
    read -p "Do you want to restart it? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Stopping backend server..."
        kill $BACKEND_PID || kill -9 $BACKEND_PID
        sleep 2
        print_success "Backend server stopped"

        read -p "Start backend server now? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Starting backend server..."
            cd backend
            nohup python main.py > backend.log 2>&1 &
            NEW_PID=$!
            print_success "Backend server started (PID: $NEW_PID)"
            print_status "Logs: tail -f backend/backend.log"
        fi
    fi
else
    print_status "Backend server is not running"
fi

echo ""
echo "=================================="
print_success "Cache clearing complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Hard refresh your browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)"
echo "   2. If using Incognito/Private mode, close and reopen"
echo "   3. Check that version is updated in browser DevTools → Network tab"
echo ""
echo "📖 For more info, see: docs/CACHE_CLEARING_GUIDE.md"
