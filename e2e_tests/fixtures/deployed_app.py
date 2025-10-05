"""
Fixture for providing a deployed application for testing.

This fixture deploys a test application via API and cleans it up after the test.
"""

import pytest
import requests
from typing import Dict, Generator
from playwright.sync_api import Page


@pytest.fixture
def deployed_app(authenticated_page: Page, base_url: str) -> Generator[Dict, None, None]:
    """
    Provides a deployed test application.

    This fixture:
    1. Uses the authenticated_page fixture (user is logged in)
    2. Deploys a lightweight test app (nginx) via API
    3. Waits for deployment to complete
    4. Yields app info to the test
    5. Cleans up (deletes) the app after test completes

    Returns:
        Dict with app info: {'id': int, 'name': str, 'hostname': str, 'status': str}

    Usage:
        def test_something(deployed_app):
            app_id = deployed_app['id']
            # ... test with deployed app ...
    """
    page = authenticated_page

    # DEBUG: Check localStorage contents
    storage = page.evaluate("Object.keys(localStorage)")
    print(f"\n🔍 [deployed_app fixture] localStorage keys: {storage}")

    # Get auth token from page storage
    token = page.evaluate("localStorage.getItem('proximity_token')")
    print(f"🔍 [deployed_app fixture] Token value: {token[:50] if token else 'NOT FOUND'}")

    if not token:
        # More debugging
        all_storage = page.evaluate("""
            () => {
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            }
        """)
        print(f"🔍 [deployed_app fixture] All localStorage: {all_storage}")
        pytest.fail("No auth token found - authentication may have failed")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Deploy a test app (nginx - lightweight and fast)
    deploy_data = {
        "catalog_id": "nginx",  # Standard nginx from catalog
        "hostname": f"test-nginx-{int(__import__('time').time())}",  # Unique hostname
        "template_id": None,  # Use default
        "custom_config": {}
    }

    print(f"\n📦 [deployed_app fixture] Deploying test app: {deploy_data['hostname']}")

    try:
        # Deploy app via API
        api_base = base_url.replace("http://", "http://").replace(":8765", ":8765/api/v1")
        response = requests.post(
            f"{api_base}/apps/deploy",
            headers=headers,
            json=deploy_data,
            timeout=60
        )

        if response.status_code != 200:
            pytest.fail(f"Failed to deploy app: {response.status_code} - {response.text}")

        app_data = response.json()
        app_id = app_data.get("app_id") or app_data.get("id")

        if not app_id:
            pytest.fail(f"No app_id in response: {app_data}")

        print(f"✓ App deployed: ID={app_id}, hostname={deploy_data['hostname']}")

        # Wait for app to be visible in UI
        print("📋 Waiting for app to appear in UI...")
        page.reload()  # Refresh to see new app
        page.wait_for_timeout(2000)  # Give UI time to update

        # Prepare app info for test
        app_info = {
            "id": app_id,
            "name": deploy_data["hostname"],
            "hostname": deploy_data["hostname"],
            "catalog_id": "nginx",
            "status": "running"
        }

        print(f"✓ App ready for testing: {app_info}")

        # Yield to test
        yield app_info

    finally:
        # Cleanup: Delete the app
        print(f"\n🧹 [deployed_app fixture] Cleaning up app ID={app_id}")
        try:
            delete_response = requests.delete(
                f"{api_base}/apps/{app_id}",
                headers=headers,
                timeout=30
            )
            if delete_response.status_code == 200:
                print(f"✓ App deleted successfully")
            else:
                print(f"⚠️  Failed to delete app: {delete_response.status_code}")
        except Exception as e:
            print(f"⚠️  Error deleting app: {e}")


@pytest.fixture
def deployed_app_with_backup(deployed_app: Dict, base_url: str, authenticated_page: Page) -> Generator[Dict, None, None]:
    """
    Provides a deployed app with at least one backup.

    This extends the deployed_app fixture by creating a backup.

    Returns:
        Dict with app info including backup_id
    """
    page = authenticated_page
    app_id = deployed_app["id"]

    # Get auth token
    token = page.evaluate("localStorage.getItem('proximity_token')")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"\n💾 [deployed_app_with_backup fixture] Creating backup for app ID={app_id}")

    try:
        # Create backup via API
        api_base = base_url.replace("http://", "http://").replace(":8765", ":8765/api/v1")
        response = requests.post(
            f"{api_base}/apps/{app_id}/backup",
            headers=headers,
            timeout=120  # Backups can take time
        )

        if response.status_code != 200:
            pytest.fail(f"Failed to create backup: {response.status_code} - {response.text}")

        backup_data = response.json()
        backup_id = backup_data.get("backup_id") or backup_data.get("id")

        print(f"✓ Backup created: ID={backup_id}")

        # Add backup info to app data
        deployed_app["backup_id"] = backup_id
        deployed_app["has_backup"] = True

        yield deployed_app

    except Exception as e:
        print(f"⚠️  Failed to create backup: {e}")
        # Still yield the app without backup
        deployed_app["has_backup"] = False
        yield deployed_app
