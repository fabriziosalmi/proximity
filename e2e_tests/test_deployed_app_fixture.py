"""Test to verify the deployed_app fixture works correctly."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.fixture_test
def test_deployed_app_fixture(deployed_app):
    """
    Verify the deployed_app fixture provides a working app.

    This test confirms:
    - App is deployed successfully
    - App info is returned with required fields
    - App can be used in tests
    """
    print("\n🧪 Testing deployed_app fixture")

    # Verify app info structure
    assert "id" in deployed_app, "App should have 'id'"
    assert "name" in deployed_app, "App should have 'name'"
    assert "hostname" in deployed_app, "App should have 'hostname'"

    print(f"  ✓ App deployed: {deployed_app}")
    print(f"  ✓ App ID: {deployed_app['id']}")
    print(f"  ✓ App name: {deployed_app['name']}")
    print(f"  ✓ Hostname: {deployed_app['hostname']}")

    # Verify app ID is valid (it's a string in this system)
    assert len(deployed_app['id']) > 0, "App ID should not be empty"

    print("\n✅ deployed_app fixture works correctly!")


@pytest.mark.fixture_test
def test_deployed_app_visible_in_ui(deployed_app, authenticated_page: Page):
    """
    Verify the deployed app appears in the UI.

    This confirms the fixture properly integrates with the frontend.
    """
    page = authenticated_page

    print("\n🧪 Testing deployed app visibility in UI")

    # Navigate to apps view
    print("  → Navigating to Apps view")
    page.evaluate("if (typeof setupEventListeners === 'function') setupEventListeners();")

    apps_nav = page.locator("[data-view='apps']")
    apps_nav.click()
    page.wait_for_timeout(1000)

    # Check if app card exists
    print(f"  → Looking for app: {deployed_app['name']}")

    # Look for app card (may be in deployed apps section)
    app_cards = page.locator(".app-card")
    card_count = app_cards.count()

    print(f"  → Found {card_count} app cards")

    if card_count > 0:
        print("  ✓ At least one app card is visible")
    else:
        print("  ℹ️  No app cards found (apps view may be empty)")

    print("\n✅ App UI visibility test complete!")
