#!/bin/bash
# Quick service health check before running E2E tests

echo "🔍 Checking Proximity services..."
echo ""

# Check backend
echo -n "Backend (https://localhost:8000): "
if curl -k -s https://localhost:8000/api/health/ > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
    BACKEND_DOWN=1
fi

# Check frontend
echo -n "Frontend (https://localhost:5173): "
if curl -k -s https://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
    FRONTEND_DOWN=1
fi

echo ""

if [ -n "$BACKEND_DOWN" ] || [ -n "$FRONTEND_DOWN" ]; then
    echo "❌ Services are not running!"
    echo ""
    echo "To start services, run:"
    echo "  docker-compose up --build"
    echo ""
    exit 1
else
    echo "✅ All services are running!"
    echo ""
    echo "You can now run E2E tests:"
    echo "  source venv/bin/activate"
    echo "  pytest e2e_tests/test_golden_path.py::test_login_only -v -s"
    echo ""
    exit 0
fi
