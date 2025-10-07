"""
Fixture for providing a deployed application for testing.

This fixture deploys a test application via API and cleans it up after the test.
Includes additional fixtures for backup management and volume management.
"""

import pytest
import requests
import time
from typing import Dict, Generator, List
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

    # Get auth token from page storage
    token = page.evaluate("localStorage.getItem('proximity_token')")
    if not token:
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

    app_id = None  # Initialize to None for cleanup

    try:
        # Deploy app via API
        api_base = base_url.replace("http://", "http://").replace(":8765", ":8765/api/v1")
        response = requests.post(
            f"{api_base}/apps/deploy",
            headers=headers,
            json=deploy_data,
            timeout=120  # Increased timeout for Docker image pull
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
        page.wait_for_timeout(3000)  # Give UI time to update
        
        # Navigate to apps view
        page.click("[data-view='apps']")
        page.wait_for_timeout(2000)  # Wait for view to load

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
        if app_id:
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
        else:
            print(f"\n🧹 [deployed_app fixture] No app to clean up (deployment may have failed)")


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
            f"{api_base}/apps/{app_id}/backups",
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


@pytest.fixture
def backup_manager(authenticated_page: Page, base_url: str):
    """
    Provides backup management utilities for testing.
    
    This fixture provides helper functions for:
    - Creating backups
    - Waiting for backup completion
    - Listing backups
    - Deleting backups
    
    Usage:
        def test_something(deployed_app, backup_manager):
            backup = backup_manager.create_backup(deployed_app['id'])
            backup_manager.wait_for_completion(backup['id'])
    """
    page = authenticated_page
    
    # Get auth token
    token = page.evaluate("localStorage.getItem('proximity_token')")
    if not token:
        pytest.fail("No auth token found - authentication may have failed")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    api_base = base_url.replace("http://", "http://").replace(":8765", ":8765/api/v1")
    
    class BackupManager:
        """Helper class for backup operations."""
        
        def create_backup(self, app_id: int, compression: str = "zstd", mode: str = "snapshot") -> Dict:
            """
            Create a backup for an app.
            
            Args:
                app_id: Application ID
                compression: Compression type (zstd, lzo, gzip)
                mode: Backup mode (snapshot, stop, suspend)
            
            Returns:
                Dict with backup info including backup_id
            """
            print(f"\n💾 [backup_manager] Creating backup for app ID={app_id}")
            
            response = requests.post(
                f"{api_base}/apps/{app_id}/backups",
                headers=headers,
                json={"compression": compression, "mode": mode},
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to create backup: {response.status_code} - {response.text}")
            
            backup_data = response.json()
            backup_id = backup_data.get("backup_id") or backup_data.get("id")
            
            print(f"✓ Backup created: ID={backup_id}")
            return {"id": backup_id, "app_id": app_id, **backup_data}
        
        def wait_for_completion(self, app_id: int, backup_id: int = None, timeout: int = 300) -> Dict:
            """
            Wait for a backup to complete.
            
            Args:
                app_id: Application ID
                backup_id: Specific backup ID (optional, uses latest if not provided)
                timeout: Maximum seconds to wait
            
            Returns:
                Dict with completed backup info
            """
            print(f"\n⏳ [backup_manager] Waiting for backup completion (timeout={timeout}s)")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Get backups list
                backups = self.list_backups(app_id)
                
                if backup_id:
                    # Find specific backup
                    backup = next((b for b in backups if b.get("id") == backup_id), None)
                else:
                    # Get latest backup
                    backup = backups[0] if backups else None
                
                if backup:
                    status = backup.get("status", "").lower()
                    print(f"  Backup status: {status}")
                    
                    if status == "available":
                        print(f"✓ Backup completed successfully")
                        return backup
                    elif status in ["error", "failed"]:
                        raise Exception(f"Backup failed with status: {status}")
                
                time.sleep(5)  # Poll every 5 seconds
            
            raise TimeoutError(f"Backup did not complete within {timeout} seconds")
        
        def list_backups(self, app_id: int) -> List[Dict]:
            """
            List all backups for an app.
            
            Args:
                app_id: Application ID
            
            Returns:
                List of backup dicts
            """
            response = requests.get(
                f"{api_base}/apps/{app_id}/backups",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                return []
            
            return response.json().get("backups", [])
        
        def delete_backup(self, app_id: int, backup_id: int) -> bool:
            """
            Delete a backup.
            
            Args:
                app_id: Application ID
                backup_id: Backup ID
            
            Returns:
                True if successful
            """
            print(f"\n🗑️  [backup_manager] Deleting backup ID={backup_id}")
            
            response = requests.delete(
                f"{api_base}/apps/{app_id}/backups/{backup_id}",
                headers=headers,
                timeout=30
            )
            
            success = response.status_code == 200
            if success:
                print(f"✓ Backup deleted successfully")
            else:
                print(f"⚠️  Failed to delete backup: {response.status_code}")
            
            return success
        
        def restore_backup(self, app_id: int, backup_id: int) -> Dict:
            """
            Restore from a backup.
            
            Args:
                app_id: Application ID
                backup_id: Backup ID
            
            Returns:
                Dict with restore info
            """
            print(f"\n🔄 [backup_manager] Restoring from backup ID={backup_id}")
            
            response = requests.post(
                f"{api_base}/apps/{app_id}/backups/{backup_id}/restore",
                headers=headers,
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to restore backup: {response.status_code} - {response.text}")
            
            restore_data = response.json()
            print(f"✓ Restore initiated")
            return restore_data
    
    return BackupManager()


@pytest.fixture
def volume_manager(authenticated_page: Page, base_url: str):
    """
    Provides volume management utilities for testing.
    
    This fixture provides helper functions for:
    - Creating volumes
    - Attaching/detaching volumes
    - Listing volumes
    - Deleting volumes
    
    Usage:
        def test_something(deployed_app, volume_manager):
            volume = volume_manager.create_volume(deployed_app['id'], size=10)
            volume_manager.attach_volume(deployed_app['id'], volume['id'])
    """
    page = authenticated_page
    
    # Get auth token
    token = page.evaluate("localStorage.getItem('proximity_token')")
    if not token:
        pytest.fail("No auth token found - authentication may have failed")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    api_base = base_url.replace("http://", "http://").replace(":8765", ":8765/api/v1")
    created_volumes = []  # Track volumes for cleanup
    
    class VolumeManager:
        """Helper class for volume operations."""
        
        def create_volume(self, app_id: int, size: int = 10, name: str = None) -> Dict:
            """
            Create a volume for an app.
            
            Args:
                app_id: Application ID
                size: Volume size in GB
                name: Volume name (auto-generated if not provided)
            
            Returns:
                Dict with volume info
            """
            if not name:
                name = f"test-volume-{int(time.time())}"
            
            print(f"\n💽 [volume_manager] Creating volume: {name} ({size}GB)")
            
            response = requests.post(
                f"{api_base}/apps/{app_id}/volumes",
                headers=headers,
                json={"name": name, "size": size},
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to create volume: {response.status_code} - {response.text}")
            
            volume_data = response.json()
            volume_id = volume_data.get("volume_id") or volume_data.get("id")
            
            # Track for cleanup
            created_volumes.append({"app_id": app_id, "volume_id": volume_id})
            
            print(f"✓ Volume created: ID={volume_id}")
            return {"id": volume_id, "app_id": app_id, "name": name, "size": size, **volume_data}
        
        def list_volumes(self, app_id: int) -> List[Dict]:
            """
            List all volumes for an app.
            
            Args:
                app_id: Application ID
            
            Returns:
                List of volume dicts
            """
            response = requests.get(
                f"{api_base}/apps/{app_id}/volumes",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                return []
            
            return response.json().get("volumes", [])
        
        def attach_volume(self, app_id: int, volume_id: int) -> bool:
            """
            Attach a volume to an app.
            
            Args:
                app_id: Application ID
                volume_id: Volume ID
            
            Returns:
                True if successful
            """
            print(f"\n🔗 [volume_manager] Attaching volume ID={volume_id} to app ID={app_id}")
            
            response = requests.post(
                f"{api_base}/apps/{app_id}/volumes/{volume_id}/attach",
                headers=headers,
                timeout=60
            )
            
            success = response.status_code == 200
            if success:
                print(f"✓ Volume attached successfully")
            else:
                print(f"⚠️  Failed to attach volume: {response.status_code}")
            
            return success
        
        def detach_volume(self, app_id: int, volume_id: int) -> bool:
            """
            Detach a volume from an app.
            
            Args:
                app_id: Application ID
                volume_id: Volume ID
            
            Returns:
                True if successful
            """
            print(f"\n🔓 [volume_manager] Detaching volume ID={volume_id} from app ID={app_id}")
            
            response = requests.post(
                f"{api_base}/apps/{app_id}/volumes/{volume_id}/detach",
                headers=headers,
                timeout=60
            )
            
            success = response.status_code == 200
            if success:
                print(f"✓ Volume detached successfully")
            else:
                print(f"⚠️  Failed to detach volume: {response.status_code}")
            
            return success
        
        def delete_volume(self, app_id: int, volume_id: int) -> bool:
            """
            Delete a volume.
            
            Args:
                app_id: Application ID
                volume_id: Volume ID
            
            Returns:
                True if successful
            """
            print(f"\n🗑️  [volume_manager] Deleting volume ID={volume_id}")
            
            response = requests.delete(
                f"{api_base}/apps/{app_id}/volumes/{volume_id}",
                headers=headers,
                timeout=30
            )
            
            success = response.status_code == 200
            if success:
                print(f"✓ Volume deleted successfully")
            else:
                print(f"⚠️  Failed to delete volume: {response.status_code}")
            
            return success
        
        def cleanup_volumes(self):
            """Clean up all created volumes."""
            print(f"\n🧹 [volume_manager] Cleaning up {len(created_volumes)} volumes")
            
            for vol_info in created_volumes:
                try:
                    self.delete_volume(vol_info["app_id"], vol_info["volume_id"])
                except Exception as e:
                    print(f"⚠️  Error deleting volume {vol_info['volume_id']}: {e}")
    
    manager = VolumeManager()
    yield manager
    
    # Cleanup after test
    manager.cleanup_volumes()
