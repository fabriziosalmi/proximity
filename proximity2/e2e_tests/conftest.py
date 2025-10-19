"""
Pytest Fixtures for E2E Tests - "Indestructible Test Pattern"

This module implements self-contained, self-cleaning test fixtures that ensure
complete test isolation. Each test gets a unique user and all resources are
automatically cleaned up after the test completes.
"""
import os
import time
import httpx
import pytest
from typing import Dict, Generator
from playwright.sync_api import Page, Browser


# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:5173")
API_URL = os.getenv("API_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def api_client() -> Generator[httpx.Client, None, None]:
    """
    Provides an HTTP client for direct backend API interactions.
    
    This client is used for programmatic setup and teardown operations,
    bypassing the UI layer for speed and reliability.
    """
    with httpx.Client(base_url=API_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def unique_user(api_client: httpx.Client) -> Generator[Dict[str, str], None, None]:
    """
    Creates a unique user for the test and ensures complete cleanup.
    
    This is the CORE of the "Indestructible Test Pattern":
    1. Creates a new user with timestamp-based unique credentials
    2. Yields the credentials to the test
    3. In teardown: Deletes all apps created by the user
    4. In teardown: Deletes the user account
    
    Returns:
        dict: {
            'email': str,
            'password': str,
            'username': str,
            'auth_token': str (after successful registration/login)
        }
    """
    # Generate unique credentials
    timestamp = int(time.time() * 1000)
    user_data = {
        "email": f"testuser_{timestamp}@example.com",
        "username": f"testuser_{timestamp}",
        "password": "E2ETest123!Secure",
        "first_name": "E2E",
        "last_name": f"Test_{timestamp}"
    }
    
    print(f"\n🔧 Setting up unique user: {user_data['username']}")
    
    # Create user via API
    try:
        register_response = api_client.post(
            "/api/core/auth/register",
            json={
                "email": user_data["email"],
                "username": user_data["username"],
                "password": user_data["password"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"]
            }
        )
        
        if register_response.status_code not in [200, 201]:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(f"Response: {register_response.text}")
            pytest.fail(f"Failed to create test user: {register_response.text}")
        
        registration_data = register_response.json()
        user_data["user_id"] = registration_data.get("id")
        
        print(f"✅ User created successfully: {user_data['username']}")
        
        # Login to get auth token (registration doesn't return token)
        login_response = api_client.post(
            "/api/core/auth/login",
            json={
                "username": user_data["username"],
                "password": user_data["password"]
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            pytest.fail(f"Failed to login test user: {login_response.text}")
        
        login_data = login_response.json()
        user_data["auth_token"] = login_data.get("access_token", "")
        
        print(f"✅ User logged in successfully, token obtained")
        
    except Exception as e:
        pytest.fail(f"Failed to create test user: {str(e)}")
    
    # Yield control to the test
    yield user_data
    
    # TEARDOWN: Clean up all resources
    print(f"\n🧹 Cleaning up user: {user_data['username']}")
    
    try:
        # Step 1: Delete all applications created by this user
        # First, get auth token if we need to log in
        if not user_data.get("auth_token"):
            login_response = api_client.post(
                "/api/core/auth/login",
                json={
                    "username": user_data["username"],
                    "password": user_data["password"]
                }
            )
            if login_response.status_code == 200:
                user_data["auth_token"] = login_response.json().get("token", "")
        
        # Get list of user's applications
        headers = {}
        if user_data.get("auth_token"):
            headers["Authorization"] = f"Bearer {user_data['auth_token']}"
        
        apps_response = api_client.get("/api/apps/", headers=headers)
        
        if apps_response.status_code == 200:
            apps_data = apps_response.json()
            applications = apps_data.get("applications", [])
            
            print(f"Found {len(applications)} applications to clean up")
            
            for app in applications:
                app_id = app.get("id")
                hostname = app.get("hostname", "unknown")
                print(f"  🗑️  Deleting application: {hostname} (ID: {app_id})")
                
                try:
                    delete_response = api_client.delete(
                        f"/api/apps/{app_id}",
                        headers=headers
                    )
                    if delete_response.status_code in [200, 202, 204]:
                        print(f"    ✅ App {hostname} deleted")
                    else:
                        print(f"    ⚠️  Failed to delete app {hostname}: {delete_response.status_code}")
                except Exception as app_error:
                    print(f"    ⚠️  Error deleting app {hostname}: {str(app_error)}")
        
        # Step 2: Delete the user account
        # Note: This requires a user deletion endpoint. If not available, we'll skip.
        # In production, you'd implement DELETE /api/core/auth/user endpoint
        try:
            user_delete_response = api_client.delete(
                f"/api/core/auth/user/{user_data.get('user_id')}",
                headers=headers
            )
            if user_delete_response.status_code in [200, 204]:
                print(f"✅ User {user_data['username']} deleted")
            else:
                print(f"⚠️  User deletion endpoint returned: {user_delete_response.status_code}")
                print(f"   (This is acceptable if the endpoint doesn't exist yet)")
        except Exception as user_error:
            print(f"⚠️  Could not delete user account: {str(user_error)}")
            print(f"   (This is acceptable if the endpoint doesn't exist yet)")
        
        print(f"✅ Cleanup completed for {user_data['username']}")
        
    except Exception as cleanup_error:
        print(f"⚠️  Cleanup encountered an error: {str(cleanup_error)}")
        # Don't fail the test on cleanup errors
        pass


@pytest.fixture(scope="session")
def base_url() -> str:
    """Provides the frontend base URL."""
    return BASE_URL


@pytest.fixture(scope="session")
def api_url() -> str:
    """Provides the backend API URL."""
    return API_URL


@pytest.fixture
def context_with_storage(browser: Browser):
    """
    Creates a browser context with persistent storage and increased timeouts.

    This allows cookies and localStorage to persist across page navigations,
    which is crucial for maintaining authentication state.
    """
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="America/New_York",
        permissions=["clipboard-read", "clipboard-write"],
        # Record videos for debugging failed tests
        record_video_dir="./test-results/videos" if os.getenv("RECORD_VIDEO") else None
    )
    
    # Increase default timeouts for slower CI environments
    context.set_default_timeout(60000)  # 60 seconds
    context.set_default_navigation_timeout(60000)
    
    yield context
    
    # Safe cleanup: check if context is still open before closing
    try:
        context.close()
    except Exception as e:
        # Context may already be closed, ignore
        pass


@pytest.fixture
def test_page(context_with_storage):
    """
    Creates a page from context_with_storage and ensures proper cleanup.
    """
    page = context_with_storage.new_page()
    yield page
    try:
        page.close()
    except Exception:
        pass  # Page might already be closed


@pytest.fixture(scope="function")
def proxmox_host():
    """
    Creates a test Proxmox host and node via Django shell command in Docker.
    
    This fixture ensures that at least one Proxmox host with nodes exists
    for deployment tests.
    
    Returns:
        Dict containing host details
    """
    import subprocess
    
    # Create host and node via Django shell in Docker container
    create_command = """
from apps.proxmox.models import ProxmoxHost, ProxmoxNode
host, created = ProxmoxHost.objects.get_or_create(
    name='e2e-test-host',
    defaults={
        'host': '192.168.100.102',
        'port': 8006,
        'user': 'root@pam',
        'password': 'invaders',
        'verify_ssl': False,
        'is_active': True,
        'is_default': True
    }
)

# Create test node
node, node_created = ProxmoxNode.objects.get_or_create(
    name='pve',
    host=host,
    defaults={
        'status': 'online',
        'cpu_count': 8,
        'cpu_usage': 10.5,
        'memory_total': 32 * 1024 * 1024 * 1024,  # 32GB in bytes
        'memory_used': 8 * 1024 * 1024 * 1024,    # 8GB in bytes
        'storage_total': 500 * 1024 * 1024 * 1024,   # 500GB in bytes
        'storage_used': 100 * 1024 * 1024 * 1024,    # 100GB in bytes
        'uptime': 86400
    }
)
print(f'{host.id},{host.name},{host.host},{host.port},{node.name}')
"""
    
    try:
        # Get the correct path to docker-compose.yml
        import os
        test_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(test_dir)
        docker_compose_path = os.path.join(project_root, 'docker-compose.yml')
        
        result = subprocess.run(
            ['docker-compose', '-f', docker_compose_path, 'exec', '-T', 'backend', 
             'python', 'manage.py', 'shell', '-c', create_command],
            capture_output=True,
            text=True,
            timeout=30,  # Increased timeout for Sentry overhead
            env={**os.environ, 'SENTRY_DEBUG': 'False'}  # Disable Sentry debug output
        )
        
        if result.returncode == 0:
            # Parse output: id,name,host,port,node_name
            output_line = result.stdout.strip().split('\n')[-1]
            host_id, name, host, port, node_name = output_line.split(',')
            
            host_data = {
                "id": int(host_id),
                "name": name,
                "host": host,
                "port": int(port),
                "url": f"{host}:{port}",
                "node": node_name
            }
            
            print(f"\n✅ Proxmox host ready: {name} (ID: {host_id})")
            print(f"✅ Proxmox node ready: {node_name}")
            return host_data
        else:
            pytest.fail(f"Failed to create Proxmox host: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        pytest.fail("Timeout creating Proxmox host")
    except Exception as e:
        pytest.fail(f"Error creating Proxmox host: {str(e)}")


@pytest.fixture
def deployed_app(
    api_client: httpx.Client,
    unique_user: Dict[str, str],
    proxmox_host: Dict[str, str]
) -> Generator[Dict[str, any], None, None]:
    """
    Provides a deployed application ready for cloning tests.
    
    This fixture:
    1. Creates a unique app via API (bypassing UI for speed)
    2. Waits for the app to reach 'running' status
    3. Yields app details and auth token
    4. In teardown: Deletes the app and any clones
    
    Returns:
        dict: {
            'id': int,
            'hostname': str,
            'auth_token': str,
            'user': dict (user details)
        }
    """
    timestamp = int(time.time() * 1000)
    app_hostname = f"e2e-clone-source-{timestamp}"
    
    print(f"\n🚀 Deploying source app for clone test: {app_hostname}")
    
    headers = {"Authorization": f"Bearer {unique_user['auth_token']}"}
    
    # Ensure catalog is loaded
    print(f"  ⏳ Reloading catalog...")
    try:
        reload_response = api_client.post("/api/catalog/reload", headers=headers)
        if reload_response.status_code in [200, 201]:
            print(f"  ✓ Catalog reloaded successfully")
        else:
            print(f"  ⚠️  Catalog reload returned {reload_response.status_code}, continuing anyway...")
    except Exception as reload_error:
        print(f"  ⚠️  Could not reload catalog: {str(reload_error)}, continuing anyway...")
    
    # Get available catalog apps
    catalog_response = api_client.get("/api/catalog/")
    
    if catalog_response.status_code != 200:
        pytest.fail(f"Failed to fetch catalog: {catalog_response.status_code}")
    
    catalog_data = catalog_response.json()
    apps_list = catalog_data.get("applications", [])  # Fixed: API returns "applications", not "apps"
    
    if not apps_list:
        pytest.fail("No catalog apps available for deployment. Please ensure catalog JSON files exist.")
    
    # Use the first catalog app
    first_app = apps_list[0]
    catalog_id = first_app.get("id")
    catalog_name = first_app.get("name", "unknown")
    
    print(f"  ✓ Using catalog app: {catalog_name} (ID: {catalog_id})")
    
    # Deploy application via API
    deploy_payload = {
        "catalog_id": catalog_id,
        "hostname": app_hostname,
        "node": proxmox_host["node"],
        "config": {},
        "environment": {}
    }
    
    try:
        deploy_response = api_client.post(
            "/api/apps/",
            json=deploy_payload,
            headers=headers
        )
        
        if deploy_response.status_code not in [200, 201, 202]:
            pytest.fail(f"Failed to deploy source app: {deploy_response.status_code} - {deploy_response.text}")
        
        app_data = deploy_response.json()
        app_id = app_data.get("id")
        
        print(f"✅ Source app created: {app_hostname} (ID: {app_id})")
        print(f"⏳ Waiting for app to reach 'running' status (timeout: 3 minutes)...")
        
        # Poll for app status to reach 'running'
        max_wait = 180  # 3 minutes
        poll_interval = 3  # 3 seconds
        elapsed = 0
        
        while elapsed < max_wait:
            status_response = api_client.get(
                f"/api/apps/{app_id}",
                headers=headers
            )
            
            if status_response.status_code == 200:
                current_app = status_response.json()
                current_status = current_app.get("status")
                
                print(f"  Status: {current_status} (elapsed: {elapsed}s)")
                
                if current_status == "running":
                    print(f"✅ Source app is now running!")
                    app_details = {
                        "id": app_id,
                        "hostname": app_hostname,
                        "auth_token": unique_user["auth_token"],
                        "user": unique_user,
                        "status": current_status,
                        "vmid": current_app.get("vmid"),
                        "node": current_app.get("node")
                    }
                    break
                elif current_status == "error":
                    pytest.fail(f"Source app deployment failed with error status")
                
            time.sleep(poll_interval)
            elapsed += poll_interval
        else:
            pytest.fail(f"Source app did not reach 'running' status within {max_wait} seconds")
        
    except Exception as e:
        pytest.fail(f"Failed to deploy source app: {str(e)}")
    
    # Yield to test
    yield app_details
    
    # TEARDOWN: Clean up source app (cloned apps will be cleaned by unique_user fixture)
    print(f"\n🧹 Cleaning up source app: {app_hostname}")
    
    try:
        delete_response = api_client.delete(
            f"/api/apps/{app_id}",
            headers=headers
        )
        
        if delete_response.status_code in [200, 202, 204]:
            print(f"✅ Source app {app_hostname} deleted")
        else:
            print(f"⚠️  Failed to delete source app: {delete_response.status_code}")
    except Exception as cleanup_error:
        print(f"⚠️  Error during source app cleanup: {str(cleanup_error)}")


@pytest.fixture
def authenticated_page(
    context_with_storage, 
    base_url: str, 
    unique_user: Dict[str, str]
) -> Generator[Page, None, None]:
    """
    Provides a Page object that's already authenticated.
    
    This fixture bypasses the UI login flow by directly injecting the auth token
    into localStorage. This is faster and more reliable than UI-based login.
    """
    page = context_with_storage.new_page()
    
    # Navigate to a page to establish the domain context
    page.goto(base_url)
    
    # Inject auth token into localStorage
    # This simulates a successful login without going through the UI
    # Note: The frontend uses 'access_token' key (see frontend/src/lib/api.ts)
    page.evaluate(f"""
        localStorage.setItem('access_token', '{unique_user["auth_token"]}');
    """)
    
    print(f"✅ Authenticated page ready for user: {unique_user['username']}")
    
    yield page
    
    page.close()


# Playwright configuration hooks
def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "golden_path: The critical user journey test"
    )
    config.addinivalue_line(
        "markers", "smoke: Quick smoke tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than 60 seconds"
    )
