"""
Diagnostic test to understand deployment verification issues.

This test performs a MOCK deployment verification to understand
why apps don't appear on the dashboard after deployment.
"""

import pytest
import requests
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.diagnostic
def test_dashboard_app_display_diagnostic(authenticated_page: Page, base_url: str):
    """
    Diagnostic test: Verify dashboard correctly displays deployed apps.
    
    This test checks if the dashboard can properly load and display
    existing deployed apps from the backend API.
    """
    page = authenticated_page
    
    print("\n" + "="*80)
    print("🔬 DIAGNOSTIC TEST: Dashboard App Display")
    print("="*80)
    
    # Step 1: Get token
    token = page.evaluate("window.localStorage.getItem('proximity_token')")
    print(f"\n✓ Got auth token (length: {len(token)})")
    
    # Step 2: Query backend API for apps
    print("\n📡 Step 1: Query backend API for deployed apps")
    api_base = base_url.replace(":8765", ":8765/api/v1")
    
    try:
        response = requests.get(
            f"{api_base}/apps",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30  # Increased timeout for slow app listing
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            apps = response.json()
            print(f"   ✅ Backend returned {len(apps)} apps")
            
            for i, app in enumerate(apps):
                print(f"\n   App {i + 1}:")
                print(f"      ID: {app.get('id', 'N/A')}")
                print(f"      Name: {app.get('name', 'N/A')}")
                print(f"      Hostname: {app.get('hostname', 'N/A')}")
                print(f"      Status: {app.get('status', 'N/A')}")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ API request failed: {e}")
        raise
    
    # Step 3: Navigate to dashboard
    print("\n🏠 Step 2: Navigate to dashboard")
    page.click("[data-view='dashboard']")
    page.wait_for_load_state("networkidle")
    print("   ✓ Navigated to dashboard")
    
    # Step 4: Check what the UI shows
    print("\n🔍 Step 3: Inspect dashboard UI")
    
    # Wait for dashboard view
    dashboard = page.locator("#dashboardView")
    expect(dashboard).to_be_visible(timeout=10000)
    print("   ✓ Dashboard view visible")
    
    # Count app cards in UI
    app_cards = page.locator(".app-card.deployed")
    card_count = app_cards.count()
    print(f"   📊 UI shows {card_count} deployed app cards")
    
    # List what cards are visible
    if card_count > 0:
        for i in range(card_count):
            card = app_cards.nth(i)
            card_text = card.inner_text()
            print(f"\n   Card {i + 1}:")
            print(f"      {card_text[:150]}")
    else:
        print("   ⚠️  No deployed app cards visible in UI")
        
        # Check if empty state is shown
        empty_state = page.locator(".empty-state")
        if empty_state.count() > 0:
            empty_text = empty_state.inner_text()
            print(f"   Empty state message: {empty_text}")
    
    # Step 5: Force refresh and check again
    print("\n🔄 Step 4: Force dashboard refresh")
    page.evaluate("if (typeof loadApps === 'function') { loadApps(); }")
    page.wait_for_timeout(3000)
    print("   ✓ Forced refresh")
    
    card_count_after = page.locator(".app-card.deployed").count()
    print(f"   📊 After refresh: {card_count_after} cards visible")
    
    # Step 6: Check if there's a mismatch
    print("\n📊 Step 5: Compare backend vs UI")
    backend_count = len(apps) if response.status_code == 200 else 0
    ui_count = card_count_after
    
    print(f"   Backend reports: {backend_count} apps")
    print(f"   UI displays: {ui_count} cards")
    
    if backend_count != ui_count:
        print(f"   ❌ MISMATCH DETECTED: Backend has {backend_count} but UI shows {ui_count}")
        print(f"   This indicates a dashboard rendering issue!")
    else:
        print(f"   ✅ Counts match!")
    
    print("\n" + "="*80)
    print("🔬 DIAGNOSTIC COMPLETE")
    print("="*80)
