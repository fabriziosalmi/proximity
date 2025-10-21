#!/bin/bash

# Run a single E2E test with full console output to debug the auth race condition

echo "🔍 Running debug test with full console logging..."
echo "=================================================="
echo ""

# Run the golden path test (which is failing)
pytest e2e_tests/test_golden_path.py::test_full_app_lifecycle -v -s --tb=short

echo ""
echo "=================================================="
echo "✅ Test complete. Review the numbered console logs above."
echo ""
echo "Expected sequence (if working correctly):"
echo "  🎪 [RootLayout] → 1️⃣ [AuthStore] → 2️⃣-4️⃣ [AuthStore] → 6️⃣-7️⃣ [ApiClient] → 🏁 [AppsPage] → 🎬-1️⃣1️⃣ [myAppsStore] → 8️⃣-🔟 [myAppsStore] → 🚀 [ApiClient]"
echo ""
