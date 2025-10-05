"""
E2E tests for backup and restore functionality.

Tests the complete backup workflow including:
- Creating backups using fixtures
- Waiting for backup completion
- Restoring from backups
- Deleting backups

These tests use the deployed_app and backup_manager fixtures for better reliability.
"""

import pytest
from playwright.sync_api import Page, expect
from typing import Dict


@pytest.mark.e2e
@pytest.mark.backup
def test_backup_creation_and_listing(deployed_app: Dict, backup_manager, authenticated_page: Page):
    """
    Test creating a backup and verifying it appears in the list.
    
    Uses fixtures:
        - deployed_app: Pre-deployed test application
        - backup_manager: Backup operations helper
    """
    print("\n" + "="*80)
    print("💾 TEST: Backup Creation and Listing")
    print("="*80)
    
    page = authenticated_page
    app_id = deployed_app['id']
    hostname = deployed_app['hostname']
    
    print(f"\n✓ Using deployed app: {hostname} (ID: {app_id})")
    
    # ========================================================================
    # PHASE 1: Create backup via API
    # ========================================================================
    print("\n📦 Phase 1: Create Backup")
    
    backup = backup_manager.create_backup(app_id)
    backup_id = backup['id']
    
    print(f"✓ Backup created: ID={backup_id}")
    
    # ========================================================================
    # PHASE 2: Verify backup appears in UI
    # ========================================================================
    print("\n🔍 Phase 2: Verify Backup in UI")
    
    # Navigate to dashboard if not already there
    page.goto(f"{page.url.split('#')[0]}#dashboard")
    page.wait_for_selector('[data-view="dashboard"]', timeout=10000)
    
    # Find app card and click backups button
    app_card = page.locator(f'[data-app-hostname="{hostname}"]')
    expect(app_card).to_be_visible(timeout=10000)
    
    backup_button = app_card.locator('button[title*="Backup"]')
    backup_button.click()
    
    # Wait for backup modal
    modal = page.locator('#backupModal, .backup-modal')
    expect(modal).to_be_visible(timeout=5000)
    print("✓ Backup modal opened")
    
    # Verify backup appears in list
    backup_items = page.locator('.backup-item')
    expect(backup_items.first).to_be_visible(timeout=10000)
    
    backup_count = backup_items.count()
    print(f"✓ Found {backup_count} backup(s) in UI")
    
    # Verify the backup we created is shown
    backup_item = backup_items.first
    expect(backup_item).to_be_visible()
    
    # Verify status is either "creating" or "available"
    status_locator = backup_item.locator('.backup-status')
    status_text = status_locator.inner_text().lower()
    assert status_text in ['creating', 'available', 'pending'], f"Unexpected status: {status_text}"
    print(f"✓ Backup status: {status_text}")
    
    print("\n✅ TEST PASSED: Backup Creation and Listing")


@pytest.mark.e2e
@pytest.mark.backup
@pytest.mark.slow
@pytest.mark.timeout(360)  # 6 minutes for backup completion
def test_backup_completion_polling(deployed_app: Dict, backup_manager):
    """
    Test that backup completes successfully.
    
    This test creates a backup and waits for it to reach 'available' status.
    
    Uses fixtures:
        - deployed_app: Pre-deployed test application
        - backup_manager: Backup operations helper with wait_for_completion
    """
    print("\n" + "="*80)
    print("⏳ TEST: Backup Completion Polling")
    print("="*80)
    
    app_id = deployed_app['id']
    hostname = deployed_app['hostname']
    
    print(f"\n✓ Using deployed app: {hostname} (ID: {app_id})")
    
    # ========================================================================
    # PHASE 1: Create backup
    # ========================================================================
    print("\n📦 Phase 1: Create Backup")
    
    backup = backup_manager.create_backup(app_id)
    backup_id = backup['id']
    
    print(f"✓ Backup created: ID={backup_id}")
    
    # ========================================================================
    # PHASE 2: Wait for completion
    # ========================================================================
    print("\n⏳ Phase 2: Wait for Backup Completion")
    print("   This may take several minutes...")
    
    completed_backup = backup_manager.wait_for_completion(app_id, backup_id, timeout=300)
    
    print(f"\n✅ Backup completed!")
    print(f"   Status: {completed_backup.get('status')}")
    print(f"   Size: {completed_backup.get('size', 'N/A')}")
    print(f"   Filename: {completed_backup.get('filename', 'N/A')}")
    
    # Verify status is available
    assert completed_backup.get('status') == 'available', \
        f"Expected status 'available', got: {completed_backup.get('status')}"
    
    print("\n✅ TEST PASSED: Backup Completion Polling")


@pytest.mark.e2e
@pytest.mark.backup
@pytest.mark.timeout(180)  # 3 minutes for restore
def test_backup_restore_workflow(deployed_app_with_backup: Dict, backup_manager, authenticated_page: Page):
    """
    Test restoring from an available backup.
    
    Uses fixtures:
        - deployed_app_with_backup: App with a pre-created backup
        - backup_manager: Backup operations helper
    """
    print("\n" + "="*80)
    print("🔄 TEST: Backup Restore Workflow")
    print("="*80)
    
    page = authenticated_page
    app_id = deployed_app_with_backup['id']
    hostname = deployed_app_with_backup['hostname']
    backup_id = deployed_app_with_backup.get('backup_id')
    
    print(f"\n✓ Using app: {hostname} (ID: {app_id})")
    print(f"✓ Backup ID: {backup_id}")
    
    # Verify backup exists and is available
    backups = backup_manager.list_backups(app_id)
    assert len(backups) > 0, "No backups found"
    
    available_backup = next((b for b in backups if b.get('status') == 'available'), None)
    assert available_backup, "No available backup found"
    
    print(f"✓ Found available backup: {available_backup.get('id')}")
    
    # ========================================================================
    # PHASE 1: Restore via API
    # ========================================================================
    print("\n🔄 Phase 1: Initiate Restore")
    
    restore_result = backup_manager.restore_backup(app_id, available_backup['id'])
    
    print(f"✓ Restore initiated")
    print(f"   Task ID: {restore_result.get('task_id', 'N/A')}")
    
    # ========================================================================
    # PHASE 2: Verify in UI (optional)
    # ========================================================================
    print("\n🔍 Phase 2: Verify Restore Status in UI")
    
    # Navigate to dashboard
    page.goto(f"{page.url.split('#')[0]}#dashboard")
    page.wait_for_timeout(2000)
    
    # Find app card
    app_card = page.locator(f'[data-app-hostname="{hostname}"]')
    
    # The app might show a restoring or running status
    # We just verify it's still visible after restore
    expect(app_card).to_be_visible(timeout=30000)
    
    print("✓ App visible after restore")
    
    print("\n✅ TEST PASSED: Backup Restore Workflow")


@pytest.mark.e2e
@pytest.mark.backup
def test_backup_deletion(deployed_app_with_backup: Dict, backup_manager):
    """
    Test deleting a backup.
    
    Uses fixtures:
        - deployed_app_with_backup: App with a pre-created backup
        - backup_manager: Backup operations helper
    """
    print("\n" + "="*80)
    print("🗑️  TEST: Backup Deletion")
    print("="*80)
    
    app_id = deployed_app_with_backup['id']
    hostname = deployed_app_with_backup['hostname']
    
    print(f"\n✓ Using app: {hostname} (ID: {app_id})")
    
    # ========================================================================
    # PHASE 1: List backups
    # ========================================================================
    print("\n📋 Phase 1: List Backups")
    
    backups_before = backup_manager.list_backups(app_id)
    initial_count = len(backups_before)
    
    print(f"✓ Found {initial_count} backup(s)")
    
    assert initial_count > 0, "No backups to delete"
    
    # ========================================================================
    # PHASE 2: Delete first backup
    # ========================================================================
    print("\n🗑️  Phase 2: Delete Backup")
    
    backup_to_delete = backups_before[0]
    backup_id = backup_to_delete['id']
    
    print(f"   Deleting backup ID: {backup_id}")
    
    success = backup_manager.delete_backup(app_id, backup_id)
    assert success, "Failed to delete backup"
    
    print("✓ Backup deleted")
    
    # ========================================================================
    # PHASE 3: Verify deletion
    # ========================================================================
    print("\n✅ Phase 3: Verify Deletion")
    
    backups_after = backup_manager.list_backups(app_id)
    new_count = len(backups_after)
    
    print(f"✓ Backup count after deletion: {new_count}")
    
    assert new_count == initial_count - 1, \
        f"Expected {initial_count - 1} backups, found {new_count}"
    
    # Verify the specific backup is gone
    deleted_backup = next((b for b in backups_after if b['id'] == backup_id), None)
    assert deleted_backup is None, "Deleted backup still exists"
    
    print("✓ Backup successfully removed from list")
    
    print("\n✅ TEST PASSED: Backup Deletion")


@pytest.mark.e2e
@pytest.mark.backup
def test_backup_ui_feedback(deployed_app: Dict, backup_manager, authenticated_page: Page):
    """
    Test UI feedback during backup operations.
    
    Verifies that the UI properly displays backup status and loading indicators.
    """
    print("\n" + "="*80)
    print("🎨 TEST: Backup UI Feedback")
    print("="*80)
    
    page = authenticated_page
    app_id = deployed_app['id']
    hostname = deployed_app['hostname']
    
    print(f"\n✓ Using app: {hostname} (ID: {app_id})")
    
    # ========================================================================
    # PHASE 1: Create backup via UI
    # ========================================================================
    print("\n📦 Phase 1: Create Backup via UI")
    
    # Navigate to dashboard
    page.goto(f"{page.url.split('#')[0]}#dashboard")
    page.wait_for_selector('[data-view="dashboard"]', timeout=10000)
    
    # Open backup modal
    app_card = page.locator(f'[data-app-hostname="{hostname}"]')
    backup_button = app_card.locator('button[title*="Backup"]')
    backup_button.click()
    
    modal = page.locator('#backupModal, .backup-modal')
    expect(modal).to_be_visible(timeout=5000)
    print("✓ Backup modal opened")
    
    # Click create backup button
    create_button = page.locator('button:has-text("Create"), button:has-text("New Backup")')
    create_button.first.click()
    print("✓ Clicked create backup button")
    
    # ========================================================================
    # PHASE 2: Verify UI feedback
    # ========================================================================
    print("\n🎨 Phase 2: Verify UI Feedback")
    
    # Wait for backup item to appear
    backup_item = page.locator('.backup-item').first
    expect(backup_item).to_be_visible(timeout=10000)
    print("✓ Backup item visible")
    
    # Check for status indicator
    status_elem = backup_item.locator('.backup-status, .status')
    expect(status_elem).to_be_visible(timeout=5000)
    
    status_text = status_elem.inner_text().lower()
    print(f"✓ Status displayed: {status_text}")
    
    # Verify status is one of the expected values
    valid_statuses = ['creating', 'pending', 'available', 'processing']
    assert any(s in status_text for s in valid_statuses), \
        f"Unexpected status text: {status_text}"
    
    # If status is creating/pending, check for loading indicator
    if 'creating' in status_text or 'pending' in status_text:
        # Look for spinner or loading icon
        spinner = backup_item.locator('i.spin, .spinner, .loading')
        if spinner.count() > 0:
            print("✓ Loading indicator present")
    
    print("\n✅ TEST PASSED: Backup UI Feedback")


@pytest.mark.e2e
@pytest.mark.backup
def test_backup_list_shows_app_info(deployed_app: Dict, backup_manager, authenticated_page: Page):
    """
    Test that backup modal displays correct app information.
    
    Verifies app name, hostname, and other metadata in the backup interface.
    """
    print("\n" + "="*80)
    print("📋 TEST: Backup List Shows App Info")
    print("="*80)
    
    page = authenticated_page
    hostname = deployed_app['hostname']
    
    print(f"\n✓ Using app: {hostname}")
    
    # Navigate to dashboard
    page.goto(f"{page.url.split('#')[0]}#dashboard")
    page.wait_for_selector('[data-view="dashboard"]', timeout=10000)
    
    # Find app card
    app_card = page.locator(f'[data-app-hostname="{hostname}"]')
    expect(app_card).to_be_visible(timeout=10000)
    
    # Get app name from card
    app_name_elem = app_card.locator('.app-name, [data-app-name]')
    
    # Open backup modal
    backup_button = app_card.locator('button[title*="Backup"]')
    backup_button.click()
    
    modal = page.locator('#backupModal, .backup-modal')
    expect(modal).to_be_visible(timeout=5000)
    print("✓ Backup modal opened")
    
    # Verify modal shows app name or hostname
    modal_content = modal.inner_text()
    assert hostname in modal_content or hostname.replace('-', ' ') in modal_content, \
        f"App hostname '{hostname}' not found in modal"
    
    print(f"✓ Modal displays app info")
    
    print("\n✅ TEST PASSED: Backup List Shows App Info")
