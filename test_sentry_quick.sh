#!/bin/bash
# Quick test script to verify Sentry is capturing events

echo "🔍 Testing Sentry Integration..."
echo ""
echo "1. Checking environment variables..."
docker exec proximity2_backend env | grep SENTRY

echo ""
echo "2. Sending test error to Sentry..."
docker exec proximity2_backend python /app/scripts/test_sentry_integration.py

echo ""
echo "✅ Test sent! Check your Sentry dashboard at:"
echo "   https://o149725.ingest.us.sentry.io/issues/"
echo ""
echo "You should see:"
echo "  - An error event with full context"
echo "  - Breadcrumbs trail"
echo "  - User information"
echo "  - Custom tags"
echo "  - Performance transaction"
