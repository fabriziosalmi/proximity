#!/bin/bash

# Restart Frontend Dev Server
# This script helps restart the Vite dev server to pick up TypeScript changes

echo "🔄 Restarting Frontend Dev Server..."
echo "========================================"
echo ""

# Check if dev server is running
if lsof -ti:5173 > /dev/null 2>&1; then
    echo "📍 Found process on port 5173"
    echo "🛑 Killing existing dev server..."
    lsof -ti:5173 | xargs kill -9
    sleep 2
    echo "✅ Server stopped"
else
    echo "ℹ️  No dev server running on port 5173"
fi

echo ""
echo "🚀 Starting new dev server..."
echo "📝 Logs will appear below. Press Ctrl+C to stop."
echo ""
echo "========================================"
echo ""

cd frontend && npm run dev
