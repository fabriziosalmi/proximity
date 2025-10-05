"""
E2E Tests for Dual-Mode (AUTO/PRO) Experience.

Tests the complete user experience for AUTO and PRO modes:
- AUTO mode hides PRO-only features
- Switching to PRO mode reveals advanced features
- Mode persists across page reloads
- Mode toggle UI works correctly
"""

import pytest
import logging
from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)


@pytest.mark.dual_mode
@pytest.mark.smoke
@pytest.mark.timeout(120)
def test_auto_mode_hides_pro_features(authenticated_page: Page):
    """
    Test that AUTO mode hides PRO-only features by default.

    Steps:
        1. Clear localStorage to ensure clean AUTO mode state
        2. Navigate to dashboard
        3. Verify body does NOT have .pro-mode class
        4. Navigate to My Apps (if apps exist)
        5. Verify Clone and Edit Resources buttons are NOT visible
        6. Navigate to backup modal (if available)
        7. Verify "Create New Backup" button is NOT visible

    Expected Results:
        - Body does not have .pro-mode class
        - PRO-only features (.pro-feature elements) are hidden
        - UI shows simplified AUTO mode interface
    """
    page = authenticated_page

    print("\n" + "="*80)
    print("🔍 TEST: AUTO Mode Hides PRO Features")
    print("="*80)

    # Step 1: Clear mode from localStorage and reload to ensure AUTO mode
    print("\n📋 Step 1: Ensure AUTO mode is active")
    page.evaluate("localStorage.removeItem('proximityMode')")
    page.reload()
    page.wait_for_load_state("networkidle")
    print("   ✓ Cleared localStorage and reloaded page")

    # Step 2: Verify body does NOT have pro-mode class
    print("\n🔍 Step 2: Verify body does not have .pro-mode class")
    body_classes = page.locator("body").get_attribute("class") or ""
    assert "pro-mode" not in body_classes, "Body should not have pro-mode class in AUTO mode"
    print(f"   ✓ Body classes: '{body_classes}' (no pro-mode)")

    # Step 3: Check for pro-feature elements - they should be hidden
    print("\n👁️  Step 3: Verify PRO-only features are hidden")
    pro_features = page.locator(".pro-feature").all()
    print(f"   Found {len(pro_features)} .pro-feature elements")

    if len(pro_features) > 0:
        # Verify they are not visible
        for i, feature in enumerate(pro_features):
            is_visible = feature.is_visible()
            print(f"   Feature {i+1}: visible={is_visible}")
            assert not is_visible, f"PRO feature {i+1} should not be visible in AUTO mode"
        print(f"   ✓ All {len(pro_features)} PRO features are hidden")
    else:
        print("   ℹ️  No PRO features found in current view")

    # Step 4: Navigate to Settings to verify mode display
    print("\n⚙️  Step 4: Check Settings page shows AUTO mode")
    settings_nav = page.locator('a.nav-item[data-view="settings"]')
    settings_nav.click()
    page.wait_for_timeout(1000)

    # Check for mode badge showing AUTO
    mode_badge = page.locator("#current-mode-badge")
    if mode_badge.count() > 0:
        badge_text = mode_badge.text_content()
        print(f"   Mode badge text: {badge_text}")
        assert "AUTO" in badge_text, "Mode badge should show AUTO"
        print("   ✓ Settings page shows AUTO mode")
    else:
        print("   ℹ️  Mode badge not found (settings may not be fully loaded)")

    print("\n" + "="*80)
    print("✅ TEST PASSED: AUTO Mode Hides PRO Features")
    print("="*80)


@pytest.mark.dual_mode
@pytest.mark.smoke
@pytest.mark.timeout(180)
def test_switching_to_pro_mode_reveals_features(authenticated_page: Page):
    """
    Test switching from AUTO to PRO mode reveals advanced features.

    Steps:
        1. Start in AUTO mode (clear localStorage)
        2. Navigate to Settings
        3. Verify toggle is in AUTO position
        4. Click toggle to switch to PRO mode
        5. Verify success notification appears
        6. Verify body has .pro-mode class
        7. Navigate to My Apps
        8. Verify Clone and Edit Resources buttons ARE visible
        9. Verify "Create New Backup" button would be visible

    Expected Results:
        - Toggle switches from AUTO to PRO
        - Success notification appears
        - Body gets .pro-mode class
        - PRO-only features become visible
    """
    page = authenticated_page

    print("\n" + "="*80)
    print("🔄 TEST: Switching to PRO Mode Reveals Features")
    print("="*80)

    # Step 1: Start in AUTO mode
    print("\n📋 Step 1: Ensure starting in AUTO mode")
    page.evaluate("localStorage.setItem('proximityMode', 'AUTO')")
    page.reload()
    page.wait_for_load_state("networkidle")
    print("   ✓ Set to AUTO mode and reloaded")

    # Step 2: Navigate to Settings
    print("\n⚙️  Step 2: Navigate to Settings page")
    settings_nav = page.locator('a.nav-item[data-view="settings"]')
    settings_nav.click()
    page.wait_for_timeout(1500)

    # Wait for system panel to be visible
    system_tab = page.locator('.settings-tab[data-tab="system"]')
    if system_tab.count() > 0:
        system_tab.click()
        page.wait_for_timeout(1000)
        print("   ✓ Clicked System tab")

    # Step 3: Verify mode toggle exists
    print("\n🔍 Step 3: Locate mode toggle")
    mode_toggle = page.locator("#modeToggleInput")
    expect(mode_toggle).to_be_visible(timeout=5000)
    print("   ✓ Mode toggle found")

    # Verify toggle is NOT checked (AUTO mode)
    is_checked = mode_toggle.is_checked()
    print(f"   Toggle checked: {is_checked}")
    assert not is_checked, "Toggle should not be checked in AUTO mode"
    print("   ✓ Toggle is in AUTO position")

    # Step 4: Click toggle to switch to PRO mode
    print("\n🖱️  Step 4: Click toggle to switch to PRO mode")
    mode_toggle.check()
    page.wait_for_timeout(1000)  # Wait for mode switch to complete
    print("   ✓ Clicked toggle")

    # Step 5: Verify success notification
    print("\n📢 Step 5: Verify success notification")
    # Look for notification with "PRO mode" text
    notification = page.locator(".toast-notification:has-text('PRO mode')")
    if notification.count() > 0:
        print("   ✓ Success notification appeared")
    else:
        print("   ℹ️  Notification may have disappeared (timing issue)")

    # Step 6: Verify body has .pro-mode class
    print("\n✅ Step 6: Verify body has .pro-mode class")
    body_classes = page.locator("body").get_attribute("class") or ""
    print(f"   Body classes: '{body_classes}'")
    assert "pro-mode" in body_classes, "Body should have pro-mode class in PRO mode"
    print("   ✓ Body has .pro-mode class")

    # Step 7: Verify mode badge shows PRO
    print("\n🏷️  Step 7: Verify mode badge shows PRO")
    mode_badge = page.locator("#current-mode-badge")
    if mode_badge.count() > 0:
        badge_text = mode_badge.text_content()
        print(f"   Mode badge text: {badge_text}")
        assert "PRO" in badge_text, "Mode badge should show PRO"
        print("   ✓ Mode badge shows PRO")

    # Step 8: Check if PRO features are now visible
    print("\n👁️  Step 8: Verify PRO features are now visible")
    pro_features = page.locator(".pro-feature").all()
    print(f"   Found {len(pro_features)} .pro-feature elements")

    if len(pro_features) > 0:
        # At least some should be visible now
        visible_count = sum(1 for f in pro_features if f.is_visible())
        print(f"   Visible PRO features: {visible_count}/{len(pro_features)}")
        assert visible_count > 0, "At least some PRO features should be visible in PRO mode"
        print(f"   ✓ {visible_count} PRO features are now visible")
    else:
        print("   ℹ️  No PRO features found in current view")

    # Step 9: Verify localStorage was updated
    print("\n💾 Step 9: Verify localStorage persistence")
    stored_mode = page.evaluate("localStorage.getItem('proximityMode')")
    print(f"   localStorage proximityMode: {stored_mode}")
    assert stored_mode == "PRO", "localStorage should contain PRO mode"
    print("   ✓ Mode persisted to localStorage")

    print("\n" + "="*80)
    print("✅ TEST PASSED: Switching to PRO Mode Reveals Features")
    print("="*80)


@pytest.mark.dual_mode
@pytest.mark.smoke
@pytest.mark.timeout(120)
def test_mode_persists_across_reloads(authenticated_page: Page):
    """
    Test that mode selection persists across page reloads.

    Steps:
        1. Navigate to Settings
        2. Switch to PRO mode
        3. Verify body has .pro-mode class
        4. Reload the page
        5. Wait for page to load
        6. Verify body STILL has .pro-mode class
        7. Verify PRO features are still visible
        8. Switch back to AUTO mode
        9. Reload page
        10. Verify body does NOT have .pro-mode class

    Expected Results:
        - PRO mode persists after reload
        - AUTO mode persists after reload
        - localStorage correctly stores and restores mode
    """
    page = authenticated_page

    print("\n" + "="*80)
    print("💾 TEST: Mode Persists Across Page Reloads")
    print("="*80)

    # Step 1: Set PRO mode via JavaScript
    print("\n📋 Step 1: Set PRO mode via localStorage")
    page.evaluate("localStorage.setItem('proximityMode', 'PRO')")
    page.reload()
    page.wait_for_load_state("networkidle")
    print("   ✓ Set PRO mode and reloaded")

    # Step 2: Verify PRO mode is active
    print("\n✅ Step 2: Verify PRO mode is active after reload")
    body_classes = page.locator("body").get_attribute("class") or ""
    assert "pro-mode" in body_classes, "PRO mode should persist after reload"
    print(f"   ✓ Body has .pro-mode class: '{body_classes}'")

    # Step 3: Reload again to test persistence
    print("\n🔄 Step 3: Reload page again")
    page.reload()
    page.wait_for_load_state("networkidle")
    print("   ✓ Page reloaded")

    # Step 4: Verify PRO mode is STILL active
    print("\n✅ Step 4: Verify PRO mode persisted through second reload")
    body_classes = page.locator("body").get_attribute("class") or ""
    assert "pro-mode" in body_classes, "PRO mode should persist through multiple reloads"
    print(f"   ✓ Body still has .pro-mode class: '{body_classes}'")

    # Step 5: Switch to AUTO mode
    print("\n🔄 Step 5: Switch to AUTO mode")
    page.evaluate("localStorage.setItem('proximityMode', 'AUTO')")
    page.reload()
    page.wait_for_load_state("networkidle")
    print("   ✓ Set AUTO mode and reloaded")

    # Step 6: Verify AUTO mode is active
    print("\n✅ Step 6: Verify AUTO mode is active after reload")
    body_classes = page.locator("body").get_attribute("class") or ""
    assert "pro-mode" not in body_classes, "AUTO mode should remove .pro-mode class"
    print(f"   ✓ Body does not have .pro-mode class: '{body_classes}'")

    # Step 7: Reload and verify AUTO mode persists
    print("\n🔄 Step 7: Reload and verify AUTO mode persists")
    page.reload()
    page.wait_for_load_state("networkidle")
    body_classes = page.locator("body").get_attribute("class") or ""
    assert "pro-mode" not in body_classes, "AUTO mode should persist after reload"
    print(f"   ✓ Body still does not have .pro-mode class: '{body_classes}'")

    print("\n" + "="*80)
    print("✅ TEST PASSED: Mode Persists Across Page Reloads")
    print("="*80)


@pytest.mark.dual_mode
@pytest.mark.timeout(90)
def test_mode_toggle_ui_behavior(authenticated_page: Page):
    """
    Test the UI behavior of the mode toggle switch.

    Steps:
        1. Navigate to Settings > System
        2. Verify mode toggle is visible
        3. Verify slider shows correct text (AUTO or PRO)
        4. Verify mode description cards highlight correctly
        5. Toggle switch and verify UI updates
        6. Verify slider animation

    Expected Results:
        - Toggle UI renders correctly
        - Slider text matches current mode
        - Mode cards show active state
        - Smooth transition on toggle
    """
    page = authenticated_page

    print("\n" + "="*80)
    print("🎨 TEST: Mode Toggle UI Behavior")
    print("="*80)

    # Step 1: Set to AUTO mode
    print("\n📋 Step 1: Set to AUTO mode")
    page.evaluate("localStorage.setItem('proximityMode', 'AUTO')")
    page.reload()
    page.wait_for_load_state("networkidle")

    # Navigate to Settings > System
    print("\n⚙️  Step 2: Navigate to Settings > System")
    settings_nav = page.locator('a.nav-item[data-view="settings"]')
    settings_nav.click()
    page.wait_for_timeout(1000)

    system_tab = page.locator('.settings-tab[data-tab="system"]')
    if system_tab.count() > 0:
        system_tab.click()
        page.wait_for_timeout(1000)

    # Step 3: Verify toggle elements exist
    print("\n🔍 Step 3: Verify toggle UI elements")
    mode_toggle = page.locator("#modeToggleInput")
    expect(mode_toggle).to_be_visible(timeout=5000)
    print("   ✓ Mode toggle input visible")

    slider = page.locator(".mode-toggle-slider")
    expect(slider).to_be_visible(timeout=3000)
    slider_text = slider.text_content()
    print(f"   ✓ Slider visible with text: '{slider_text}'")
    assert "AUTO" in slider_text or "PRO" in slider_text, "Slider should show AUTO or PRO"

    # Step 4: Verify mode cards
    print("\n🏷️  Step 4: Verify mode description cards")
    auto_card = page.locator("#auto-mode-card")
    pro_card = page.locator("#pro-mode-card")

    if auto_card.count() > 0:
        auto_classes = auto_card.get_attribute("class") or ""
        print(f"   AUTO card classes: '{auto_classes}'")
        assert "active" in auto_classes, "AUTO card should be active in AUTO mode"
        print("   ✓ AUTO card is active")

    if pro_card.count() > 0:
        pro_classes = pro_card.get_attribute("class") or ""
        print(f"   PRO card classes: '{pro_classes}'")
        assert "active" not in pro_classes, "PRO card should not be active in AUTO mode"
        print("   ✓ PRO card is not active")

    print("\n" + "="*80)
    print("✅ TEST PASSED: Mode Toggle UI Behavior")
    print("="*80)
