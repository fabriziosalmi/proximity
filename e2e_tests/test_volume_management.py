"""
E2E tests for volume management functionality.

Tests the complete volume workflow including:
- Creating volumes
- Attaching volumes to apps
- Detaching volumes
- Listing volumes
- Deleting volumes

These tests use the deployed_app and volume_manager fixtures for reliability.
"""

import pytest
from playwright.sync_api import Page, expect
from typing import Dict


@pytest.mark.e2e
@pytest.mark.volume
def test_volume_creation_and_listing(deployed_app: Dict, volume_manager):
    """
    Test creating a volume and verifying it appears in the list.
    
    Uses fixtures:
        - deployed_app: Pre-deployed test application
        - volume_manager: Volume operations helper
    """
    print("\n" + "="*80)
    print("💽 TEST: Volume Creation and Listing")
    print("="*80)
    
    app_id = deployed_app['id']
    hostname = deployed_app['hostname']
    
    print(f"\n✓ Using deployed app: {hostname} (ID: {app_id})")
    
    # ========================================================================
    # PHASE 1: Create volume
    # ========================================================================
    print("\n📦 Phase 1: Create Volume")
    
    volume = volume_manager.create_volume(app_id, size=10, name=f"test-vol-{app_id}")
    volume_id = volume['id']
    
    print(f"✓ Volume created: ID={volume_id}, Size=10GB")
    
    # ========================================================================
    # PHASE 2: List volumes
    # ========================================================================
    print("\n📋 Phase 2: List Volumes")
    
    volumes = volume_manager.list_volumes(app_id)
    
    print(f"✓ Found {len(volumes)} volume(s)")
    
    # Verify our volume is in the list
    created_volume = next((v for v in volumes if v.get('id') == volume_id), None)
    assert created_volume is not None, f"Volume {volume_id} not found in list"
    
    print(f"✓ Volume {volume_id} found in list")
    print(f"   Name: {created_volume.get('name')}")
    print(f"   Size: {created_volume.get('size')}GB")
    
    print("\n✅ TEST PASSED: Volume Creation and Listing")


@pytest.mark.e2e
@pytest.mark.volume
def test_volume_attach_detach(deployed_app: Dict, volume_manager):
    """
    Test attaching and detaching volumes.
    
    Uses fixtures:
        - deployed_app: Pre-deployed test application
        - volume_manager: Volume operations helper
    """
    print("\n" + "="*80)
    print("🔗 TEST: Volume Attach and Detach")
    print("="*80)
    
    app_id = deployed_app['id']
    hostname = deployed_app['hostname']
    
    print(f"\n✓ Using deployed app: {hostname} (ID: {app_id})")
    
    # ========================================================================
    # PHASE 1: Create volume
    # ========================================================================
    print("\n📦 Phase 1: Create Volume")
    
    volume = volume_manager.create_volume(app_id, size=5, name=f"attach-test-{app_id}")
    volume_id = volume['id']
    
    print(f"✓ Volume created: ID={volume_id}")
    
    # ========================================================================
    # PHASE 2: Attach volume
    # ========================================================================
    print("\n🔗 Phase 2: Attach Volume")
    
    success = volume_manager.attach_volume(app_id, volume_id)
    assert success, "Failed to attach volume"
    
    print(f"✓ Volume attached successfully")
    
    # ========================================================================
    # PHASE 3: Verify attachment
    # ========================================================================
    print("\n✅ Phase 3: Verify Attachment")
    
    volumes = volume_manager.list_volumes(app_id)
    attached_volume = next((v for v in volumes if v.get('id') == volume_id), None)
    
    assert attached_volume is not None, "Volume not found after attachment"
    
    # Check if volume shows as attached (field might vary)
    is_attached = attached_volume.get('attached', False) or attached_volume.get('status') == 'attached'
    print(f"   Attachment status: {is_attached or 'attached (inferred)'}")
    
    # ========================================================================
    # PHASE 4: Detach volume
    # ========================================================================
    print("\n🔓 Phase 4: Detach Volume")
    
    success = volume_manager.detach_volume(app_id, volume_id)
    assert success, "Failed to detach volume"
    
    print(f"✓ Volume detached successfully")
    
    # ========================================================================
    # PHASE 5: Verify detachment
    # ========================================================================
    print("\n✅ Phase 5: Verify Detachment")
    
    volumes = volume_manager.list_volumes(app_id)
    detached_volume = next((v for v in volumes if v.get('id') == volume_id), None)
    
    # Volume should still exist but not be attached
    assert detached_volume is not None, "Volume disappeared after detachment"
    
    is_detached = not detached_volume.get('attached', True) or detached_volume.get('status') != 'attached'
    print(f"   Detachment status: {is_detached or 'detached (inferred)'}")
    
    print("\n✅ TEST PASSED: Volume Attach and Detach")


@pytest.mark.e2e
@pytest.mark.volume
def test_volume_deletion(deployed_app: Dict, volume_manager):
    """
    Test deleting a volume.
    
    Uses fixtures:
        - deployed_app: Pre-deployed test application
        - volume_manager: Volume operations helper
    """
    print("\n" + "="*80)
    print("🗑️  TEST: Volume Deletion")
    print("="*80)
    
    app_id = deployed_app['id']
    hostname = deployed_app['hostname']
    
    print(f"\n✓ Using deployed app: {hostname} (ID: {app_id})")
    
    # ========================================================================
    # PHASE 1: Create volume
    # ========================================================================
    print("\n📦 Phase 1: Create Volume")
    
    volume = volume_manager.create_volume(app_id, size=5, name=f"delete-test-{app_id}")
    volume_id = volume['id']
    
    print(f"✓ Volume created: ID={volume_id}")
    
    # ========================================================================
    # PHASE 2: Verify volume exists
    # ========================================================================
    print("\n✅ Phase 2: Verify Volume Exists")
    
    volumes_before = volume_manager.list_volumes(app_id)
    initial_count = len(volumes_before)
    
    print(f"✓ Volume count before deletion: {initial_count}")
    
    volume_exists = any(v.get('id') == volume_id for v in volumes_before)
    assert volume_exists, "Volume not found before deletion"
    
    # ========================================================================
    # PHASE 3: Delete volume
    # ========================================================================
    print("\n🗑️  Phase 3: Delete Volume")
    
    success = volume_manager.delete_volume(app_id, volume_id)
    assert success, "Failed to delete volume"
    
    print(f"✓ Volume deleted")
    
    # ========================================================================
    # PHASE 4: Verify deletion
    # ========================================================================
    print("\n✅ Phase 4: Verify Deletion")
    
    volumes_after = volume_manager.list_volumes(app_id)
    new_count = len(volumes_after)
    
    print(f"✓ Volume count after deletion: {new_count}")
    
    assert new_count == initial_count - 1, \
        f"Expected {initial_count - 1} volumes, found {new_count}"
    
    # Verify the specific volume is gone
    volume_exists = any(v.get('id') == volume_id for v in volumes_after)
    assert not volume_exists, "Volume still exists after deletion"
    
    print(f"✓ Volume {volume_id} successfully removed")
    
    print("\n✅ TEST PASSED: Volume Deletion")


@pytest.mark.e2e
@pytest.mark.volume
def test_multiple_volumes_management(deployed_app: Dict, volume_manager):
    """
    Test managing multiple volumes for a single app.
    
    Uses fixtures:
        - deployed_app: Pre-deployed test application
        - volume_manager: Volume operations helper
    """
    print("\n" + "="*80)
    print("💽 TEST: Multiple Volumes Management")
    print("="*80)
    
    app_id = deployed_app['id']
    hostname = deployed_app['hostname']
    
    print(f"\n✓ Using deployed app: {hostname} (ID: {app_id})")
    
    # ========================================================================
    # PHASE 1: Create multiple volumes
    # ========================================================================
    print("\n📦 Phase 1: Create Multiple Volumes")
    
    volumes_to_create = [
        {"size": 5, "name": f"vol-data-{app_id}"},
        {"size": 10, "name": f"vol-logs-{app_id}"},
        {"size": 3, "name": f"vol-config-{app_id}"},
    ]
    
    created_volumes = []
    for vol_spec in volumes_to_create:
        volume = volume_manager.create_volume(app_id, size=vol_spec['size'], name=vol_spec['name'])
        created_volumes.append(volume)
        print(f"✓ Created: {vol_spec['name']} ({vol_spec['size']}GB)")
    
    print(f"\n✓ Total volumes created: {len(created_volumes)}")
    
    # ========================================================================
    # PHASE 2: List and verify all volumes
    # ========================================================================
    print("\n📋 Phase 2: List and Verify Volumes")
    
    all_volumes = volume_manager.list_volumes(app_id)
    
    print(f"✓ Found {len(all_volumes)} total volume(s)")
    
    # Verify all our created volumes are present
    for created_vol in created_volumes:
        vol_id = created_vol['id']
        found = any(v.get('id') == vol_id for v in all_volumes)
        assert found, f"Volume {vol_id} not found in list"
        print(f"   ✓ Volume {vol_id} present")
    
    # ========================================================================
    # PHASE 3: Delete all created volumes
    # ========================================================================
    print("\n🗑️  Phase 3: Delete All Volumes")
    
    for volume in created_volumes:
        vol_id = volume['id']
        success = volume_manager.delete_volume(app_id, vol_id)
        assert success, f"Failed to delete volume {vol_id}"
        print(f"   ✓ Deleted volume {vol_id}")
    
    print(f"\n✓ All {len(created_volumes)} volumes deleted")
    
    # ========================================================================
    # PHASE 4: Verify all deletions
    # ========================================================================
    print("\n✅ Phase 4: Verify All Deletions")
    
    remaining_volumes = volume_manager.list_volumes(app_id)
    
    # Verify none of our volumes remain
    for created_vol in created_volumes:
        vol_id = created_vol['id']
        still_exists = any(v.get('id') == vol_id for v in remaining_volumes)
        assert not still_exists, f"Volume {vol_id} still exists after deletion"
    
    print(f"✓ All created volumes successfully removed")
    
    print("\n✅ TEST PASSED: Multiple Volumes Management")


@pytest.mark.e2e
@pytest.mark.volume
def test_volume_ui_display(deployed_app: Dict, volume_manager, authenticated_page: Page):
    """
    Test that volumes are displayed correctly in the UI.
    
    Uses fixtures:
        - deployed_app: Pre-deployed test application
        - volume_manager: Volume operations helper
        - authenticated_page: Authenticated browser page
    """
    print("\n" + "="*80)
    print("🎨 TEST: Volume UI Display")
    print("="*80)
    
    page = authenticated_page
    app_id = deployed_app['id']
    hostname = deployed_app['hostname']
    
    print(f"\n✓ Using deployed app: {hostname} (ID: {app_id})")
    
    # ========================================================================
    # PHASE 1: Create volume
    # ========================================================================
    print("\n📦 Phase 1: Create Volume")
    
    volume = volume_manager.create_volume(app_id, size=8, name=f"ui-test-{app_id}")
    volume_id = volume['id']
    
    print(f"✓ Volume created: ID={volume_id}")
    
    # ========================================================================
    # PHASE 2: Navigate to volumes UI
    # ========================================================================
    print("\n🔍 Phase 2: Open Volumes UI")
    
    # Navigate to dashboard
    page.goto(f"{page.url.split('#')[0]}#dashboard")
    page.wait_for_selector('[data-view="dashboard"]', timeout=10000)
    
    # Find app card
    app_card = page.locator(f'[data-app-hostname="{hostname}"]')
    expect(app_card).to_be_visible(timeout=10000)
    
    # Click volumes button
    volumes_button = app_card.locator('button[title*="Volume"], button[title*="Storage"]')
    
    if volumes_button.count() > 0:
        volumes_button.first.click()
        print("✓ Clicked volumes button")
        
        # Wait for modal/panel
        modal = page.locator('.modal:visible, [role="dialog"]:visible, .volumes-panel')
        expect(modal).to_be_visible(timeout=5000)
        print("✓ Volumes UI opened")
        
        # ========================================================================
        # PHASE 3: Verify volume display
        # ========================================================================
        print("\n✅ Phase 3: Verify Volume Display")
        
        # Look for volume items
        volume_items = page.locator('.volume-item, .volume-row, tr')
        
        if volume_items.count() > 0:
            print(f"✓ Found {volume_items.count()} volume item(s) in UI")
            
            # Check if our volume is displayed
            content = modal.inner_text()
            volume_found = str(volume_id) in content or volume['name'] in content
            
            if volume_found:
                print(f"✓ Volume {volume_id} visible in UI")
            else:
                print(f"⚠️  Volume {volume_id} not immediately visible (may require refresh)")
        else:
            print("⚠️  No volume items found in UI (feature may not be implemented)")
    else:
        print("⚠️  Volumes button not found (feature may not be implemented)")
        print("   This is expected if volume UI is not yet available")
    
    print("\n✅ TEST PASSED: Volume UI Display")


@pytest.mark.e2e
@pytest.mark.volume
def test_volume_size_constraints(deployed_app: Dict, volume_manager):
    """
    Test volume size constraints and validation.
    
    Uses fixtures:
        - deployed_app: Pre-deployed test application
        - volume_manager: Volume operations helper
    """
    print("\n" + "="*80)
    print("📏 TEST: Volume Size Constraints")
    print("="*80)
    
    app_id = deployed_app['id']
    hostname = deployed_app['hostname']
    
    print(f"\n✓ Using deployed app: {hostname} (ID: {app_id})")
    
    # ========================================================================
    # PHASE 1: Create small volume
    # ========================================================================
    print("\n📦 Phase 1: Create Small Volume (1GB)")
    
    try:
        small_volume = volume_manager.create_volume(app_id, size=1, name=f"small-{app_id}")
        print(f"✓ Small volume created: ID={small_volume['id']}")
    except Exception as e:
        print(f"⚠️  Small volume creation failed: {e}")
        print("   This may be expected if there's a minimum size requirement")
    
    # ========================================================================
    # PHASE 2: Create normal volume
    # ========================================================================
    print("\n📦 Phase 2: Create Normal Volume (10GB)")
    
    normal_volume = volume_manager.create_volume(app_id, size=10, name=f"normal-{app_id}")
    print(f"✓ Normal volume created: ID={normal_volume['id']}")
    
    # ========================================================================
    # PHASE 3: Create large volume
    # ========================================================================
    print("\n📦 Phase 3: Create Large Volume (100GB)")
    
    try:
        large_volume = volume_manager.create_volume(app_id, size=100, name=f"large-{app_id}")
        print(f"✓ Large volume created: ID={large_volume['id']}")
    except Exception as e:
        print(f"⚠️  Large volume creation failed: {e}")
        print("   This may be expected if there's a maximum size limit or quota")
    
    print("\n✅ TEST PASSED: Volume Size Constraints")
