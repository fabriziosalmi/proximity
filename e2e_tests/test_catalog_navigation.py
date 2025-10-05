"""Quick test to verify catalog navigation works after setupEventListeners fix."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.smoke
def test_catalog_navigation(authenticated_page: Page):
    """
    Test that we can navigate to the catalog view.

    This is a simple smoke test to verify the navigation fix works.
    """
    page = authenticated_page

    print("\n🧪 Testing catalog navigation")

    # Enable console log capture
    page.on("console", lambda msg: print(f"  [BROWSER] {msg.text}"))

    # Step 1: Verify we're on dashboard
    print("  → Verifying dashboard is visible")
    expect(page.locator("#dashboardView")).to_be_visible(timeout=5000)
    print("  ✓ Dashboard visible")

    # Step 2: Click catalog navigation
    print("  → Clicking catalog navigation")
    catalog_nav = page.locator("[data-view='catalog']")

    # Debug: Check if event listeners are attached
    has_listeners = page.evaluate("""
        () => {
            const navItems = document.querySelectorAll('.nav-item');
            console.log('Found nav items:', navItems.length);
            navItems.forEach((item, i) => {
                console.log(`  Nav item ${i}:`, item.dataset.view, item.classList.toString());
            });
            return navItems.length > 0;
        }
    """)
    print(f"  → Nav items found: {has_listeners}")

    catalog_nav.click()
    page.wait_for_timeout(500)

    # Debug: Check view states after click
    view_states = page.evaluate("""
        () => {
            const views = document.querySelectorAll('.view');
            const states = {};
            views.forEach(v => {
                states[v.id] = v.classList.contains('hidden') ? 'hidden' : 'visible';
            });
            return states;
        }
    """)
    print(f"  → View states after click: {view_states}")

    # Step 3: Wait for catalog view to appear
    print("  → Waiting for catalog view")
    expect(page.locator("#catalogView")).to_be_visible(timeout=10000)
    print("  ✓ Catalog view visible")

    # Step 4: Verify catalog view has content
    print("  → Checking for catalog content")
    page.wait_for_timeout(2000)  # Give catalog time to render

    # Check that catalog view is not empty (has some content)
    catalog_content = page.locator("#catalogView").inner_html()
    assert len(catalog_content) > 100, "Catalog view should have content"
    print("  ✓ Catalog has content")

    print("\n✅ Catalog navigation works!")
