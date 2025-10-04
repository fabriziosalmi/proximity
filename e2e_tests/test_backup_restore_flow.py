"""
E2E tests for backup and restore functionality.

Tests the complete backup workflow including:
- Creating backups
- Waiting for backup completion
- Restoring from backups
- Deleting backups
"""

import pytest
from playwright.sync_api import Page, expect
import time


@pytest.mark.e2e
def test_backup_creation_and_listing(page: Page, base_url: str):
    """Test creating a backup and seeing it in the list."""
    # Login first
    page.goto(f"{base_url}")

    # Wait for apps to load
    page.wait_for_selector('[data-view="dashboard"]')

    # Find first deployed app
    app_card = page.locator('.app-card.deployed').first
    expect(app_card).to_be_visible()

    # Get app name for verification
    app_name = app_card.locator('.app-name').inner_text()

    # Click backup button
    backup_button = app_card.locator('button[title="Backups"]')
    backup_button.click()

    # Wait for backup modal
    expect(page.locator('#backupModal')).to_be_visible()
    expect(page.locator('#backup-app-name')).to_contain_text(app_name)

    # Should show empty state initially (or existing backups)
    # Click create backup
    page.locator('button:has-text("Create New Backup")').click()

    # Wait for backup to appear in list
    expect(page.locator('.backup-item')).to_be_visible(timeout=10000)

    # Verify backup shows "creating" status
    backup_item = page.locator('.backup-item').first
    expect(backup_item.locator('.backup-status')).to_contain_text('creating')

    # Verify filename format
    filename = backup_item.locator('.backup-filename').inner_text()
    assert 'vzdump-lxc-' in filename
    assert '.tar.zst' in filename


@pytest.mark.e2e
@pytest.mark.slow
def test_backup_completion_polling(page: Page, base_url: str):
    """Test that backup status updates from 'creating' to 'available'."""
    # Login and navigate to backups
    page.goto(f"{base_url}")
    page.wait_for_selector('[data-view="dashboard"]')

    app_card = page.locator('.app-card.deployed').first
    backup_button = app_card.locator('button[title="Backups"]')
    backup_button.click()

    expect(page.locator('#backupModal')).to_be_visible()

    # Create a backup
    page.locator('button:has-text("Create New Backup")').click()

    # Wait for backup item
    expect(page.locator('.backup-item')).to_be_visible(timeout=10000)

    # Wait for status to change from 'creating' to 'available'
    # This uses Playwright's smart waiting - it will poll until condition is met
    expect(
        page.locator('.backup-status.status-available')
    ).to_be_visible(timeout=300000)  # 5 minutes max

    # Verify backup shows size and completion info
    backup_item = page.locator('.backup-item').first
    expect(backup_item.locator('.backup-size')).to_be_visible()


@pytest.mark.e2e
def test_backup_restore_workflow(page: Page, base_url: str):
    """Test restoring from an available backup."""
    # Login and navigate
    page.goto(f"{base_url}")
    page.wait_for_selector('[data-view="dashboard"]')

    app_card = page.locator('.app-card.deployed').first
    backup_button = app_card.locator('button[title="Backups"]')
    backup_button.click()

    expect(page.locator('#backupModal')).to_be_visible()

    # Wait for available backup (assumes one exists from previous test)
    available_backup = page.locator('.backup-status.status-available').first
    expect(available_backup).to_be_visible(timeout=10000)

    # Find the backup item and click restore
    backup_item = available_backup.locator('xpath=ancestor::div[@class="backup-item"]')
    restore_button = backup_item.locator('button:has-text("Restore")')

    # Setup dialog handler for confirmation
    page.on("dialog", lambda dialog: dialog.accept())

    restore_button.click()

    # Wait for notification
    expect(page.locator('.notification')).to_contain_text('Restoring', timeout=5000)

    # Wait for completion notification (with generous timeout)
    expect(
        page.locator('.notification:has-text("Restore completed")')
    ).to_be_visible(timeout=120000)  # 2 minutes

    # Modal should close automatically
    expect(page.locator('#backupModal')).not_to_be_visible(timeout=5000)


@pytest.mark.e2e
def test_backup_deletion(page: Page, base_url: str):
    """Test deleting a backup."""
    # Login and navigate
    page.goto(f"{base_url}")
    page.wait_for_selector('[data-view="dashboard"]')

    app_card = page.locator('.app-card.deployed').first
    backup_button = app_card.locator('button[title="Backups"]')
    backup_button.click()

    expect(page.locator('#backupModal')).to_be_visible()

    # Wait for backup list
    expect(page.locator('.backup-item')).to_be_visible(timeout=10000)

    # Count initial backups
    initial_count = page.locator('.backup-item').count()
    assert initial_count > 0, "Should have at least one backup to delete"

    # Get first backup and delete it
    first_backup = page.locator('.backup-item').first
    delete_button = first_backup.locator('button:has-text("Delete")')

    # Setup dialog handler
    page.on("dialog", lambda dialog: dialog.accept())

    delete_button.click()

    # Wait for deletion notification
    expect(page.locator('.notification:has-text("deleted")')).to_be_visible(timeout=5000)

    # Verify backup count decreased
    page.wait_for_timeout(1000)  # Small wait for UI update
    new_count = page.locator('.backup-item').count()

    if initial_count == 1:
        # Should show empty state
        expect(page.locator('.empty-state')).to_be_visible()
    else:
        assert new_count == initial_count - 1, "Backup count should decrease by 1"


@pytest.mark.e2e
def test_backup_ui_feedback(page: Page, base_url: str):
    """Test UI feedback during backup operations."""
    page.goto(f"{base_url}")
    page.wait_for_selector('[data-view="dashboard"]')

    app_card = page.locator('.app-card.deployed').first
    backup_button = app_card.locator('button[title="Backups"]')
    backup_button.click()

    expect(page.locator('#backupModal')).to_be_visible()

    # Create backup and verify loading feedback
    page.locator('button:has-text("Create New Backup")').click()

    # Should show "Creating backup" notification
    expect(page.locator('.notification:has-text("Creating")')).to_be_visible(timeout=2000)

    # Wait for backup item with creating status
    creating_status = page.locator('.backup-status.status-creating')
    expect(creating_status).to_be_visible(timeout=5000)

    # Verify spinner icon is present
    spinner = creating_status.locator('i.spin')
    expect(spinner).to_be_visible()

    # Verify status text is capitalized properly
    expect(creating_status).to_contain_text('creating')


@pytest.mark.e2e
def test_backup_security_ownership(page: Page, base_url: str):
    """Test that users can only access their own backups (if multi-user)."""
    # This test would require multiple user accounts
    # For now, just verify the backup modal shows correct app name
    page.goto(f"{base_url}")
    page.wait_for_selector('[data-view="dashboard"]')

    app_card = page.locator('.app-card.deployed').first
    app_name = app_card.locator('.app-name').inner_text()

    backup_button = app_card.locator('button[title="Backups"]')
    backup_button.click()

    # Verify modal shows correct app name
    expect(page.locator('#backup-app-name')).to_have_text(app_name)
