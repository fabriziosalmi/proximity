"""
Pytest Fixtures for E2E Tests - "Indestructible Test Pattern" (Refactored)

This module implements self-contained, self-cleaning test fixtures that ensure
complete test isolation. It now uses a UI-based login for realism and supports
the new cookie-based authentication scheme.
"""
import os
import time
import httpx
import pytest
from typing import Dict, Generator
from playwright.sync_api import Page, Browser


# --- Configuration ---
BASE_URL = os.getenv("BASE_URL", "http://localhost:5173")
API_URL = os.getenv("API_URL", "http://localhost:8000")


# --- Core Fixtures ---

@pytest.fixture(scope="session")
def api_client() -> Generator[httpx.Client, None, None]:
    """
    Provides a stateful HTTP client that manages cookies across requests,
    essential for interacting with the cookie-based auth system.
    """
    with httpx.Client(base_url=API_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def unique_user(api_client: httpx.Client) -> Generator[Dict[str, str], None, None]:
    """
    Creates a unique user via API for the test and ensures complete cleanup.
    This fixture now uses cookie-based authentication via dj-rest-auth.
    """
    timestamp = int(time.time() * 1000)
    user_data = {
        "email": f"testuser_{timestamp}@example.com",
        "username": f"testuser_{timestamp}",
        "password": "E2ETest123!Secure",
    }
    
    print(f"\n🔧 Setting up unique user: {user_data['username']}")
    
    try:
        # Create user
        register_response = api_client.post(
            "/api/auth/registration/",
            json={
                "username": user_data["username"],
                "email": user_data["email"],
                "password": user_data["password"],
                "password2": user_data["password"],
            }
        )
        if register_response.status_code not in [200, 201]:
            pytest.fail(f"Failed to create test user: {register_response.status_code} - {register_response.text}")
        
        print(f"✅ User created successfully: {user_data['username']}")
        
        # Log in to establish a session via cookies in the client
        login_response = api_client.post(
            "/api/auth/login/",
            json={"username": user_data["username"], "password": user_data["password"]}
        )
        if login_response.status_code != 200:
            pytest.fail(f"Failed to login test user: {login_response.status_code} - {login_response.text}")
        
        login_data = login_response.json()
        user_data["user_id"] = login_data.get("user", {}).get("pk")
        
        print(f"✅ User logged in successfully, session cookie set in api_client.")
        
    except Exception as e:
        pytest.fail(f"Failed to create and log in test user: {str(e)}")
    
    yield user_data
    
    # --- TEARDOWN ---
    print(f"\n🧹 Cleaning up user and resources: {user_data['username']}")
    try:
        # The api_client is already authenticated with a session cookie
        apps_response = api_client.get("/api/apps/")
        if apps_response.status_code == 200:
            apps_data = apps_response.json()
            # Adjust based on actual API response structure
            applications = apps_data.get("apps", [])
            
            print(f"Found {len(applications)} applications to clean up.")
            for app in applications:
                app_id = app.get("id")
                hostname = app.get("hostname", "unknown")
                print(f"  ♲️  Deleting application: {hostname} (ID: {app_id})")
                try:
                    # Use the correct action endpoint
                    delete_response = api_client.post(f"/api/apps/{app_id}/action", json={"action": "delete"})
                    if delete_response.status_code in [200, 202, 204]:
                        print(f"    ✅ App {hostname} deletion initiated")
                    else:
                        print(f"    ⚠️  Failed to delete app {hostname}: {delete_response.status_code} - {delete_response.text}")
                except Exception as app_error:
                    print(f"    ⚠️  Error deleting app {hostname}: {str(app_error)}")
        else:
            print(f"Could not fetch apps for cleanup, status: {apps_response.status_code}")

        print(f"✅ Cleanup completed for {user_data['username']}")
    except Exception as cleanup_error:
        print(f"⚠️  Cleanup encountered an error: {str(cleanup_error)}")
        pass


# --- Playwright Fixtures ---

@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL

@pytest.fixture
def context_with_storage(browser: Browser):
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        record_video_dir="./test-results/videos" if os.getenv("RECORD_VIDEO") else None
    )
    context.set_default_timeout(60000)
    yield context
    try:
        context.close()
    except Exception:
        pass

@pytest.fixture
def test_page(context_with_storage):
    page = context_with_storage.new_page()
    yield page
    try:
        page.close()
    except Exception:
        pass

@pytest.fixture
def logged_in_page(test_page: Page, unique_user: Dict[str, str], base_url: str) -> Page:
    """
    Provides a Page object that has been authenticated via the UI.
    This is the SOTA standard for E2E tests, as it follows the real user path.
    """
    page = test_page
    print(f"\n☺️ Performing UI login for user: {unique_user['username']}")
    
    page.goto(f"{base_url}/login")
    page.locator('input[name="username"]').fill(unique_user["username"])
    page.locator('input[name="password"]').fill(unique_user["password"])
    page.locator('button[type="submit"]').click()
    
    # Wait for successful authentication by checking for the main rack element
    page.wait_for_selector('#master-control-rack', state='visible', timeout=30000)
    print(f"✅ UI Login successful.")
    
    return page


# --- Application-Specific Fixtures ---

@pytest.fixture
def deployed_app(api_client: httpx.Client, unique_user: Dict[str, str]) -> Generator[Dict[str, any], None, None]:
    """
    Provides a deployed application by calling the API directly.
    This now relies on the cookie-authenticated api_client.
    """
    timestamp = int(time.time() * 1000)
    app_hostname = f"e2e-deployed-app-{timestamp}"
    print(f"\n🌆 Deploying app for test: {app_hostname}")

    # api_client is already logged in by the unique_user fixture
    catalog_response = api_client.get("/api/catalog/")
    if catalog_response.status_code != 200:
        pytest.fail(f"Failed to fetch catalog: {catalog_response.status_code}")
    
    catalog_id = catalog_response.json()["applications"][0]["id"]
    
    deploy_payload = {"catalog_id": catalog_id, "hostname": app_hostname}
    deploy_response = api_client.post("/api/apps/", json=deploy_payload)
    if deploy_response.status_code not in [200, 201, 202]:
        pytest.fail(f"Failed to deploy app: {deploy_response.status_code} - {deploy_response.text}")
    
    app_data = deploy_response.json()
    app_id = app_data.get("id")
    print(f"✅ App created: {app_hostname} (ID: {app_id})")
    
    # Poll for 'running' status
    max_wait = 180
    poll_interval = 5
    elapsed = 0
    app_details = {}
    while elapsed < max_wait:
        status_response = api_client.get(f"/api/apps/{app_id}")
        if status_response.status_code == 200:
            current_app = status_response.json()
            if current_app.get("status") == "running":
                print(f"✅ App is running!")
                app_details = current_app
                break
        time.sleep(poll_interval)
        elapsed += poll_interval
    else:
        pytest.fail(f"App did not reach 'running' status within {max_wait} seconds")

    yield app_details
    # Cleanup is handled by the unique_user fixture's teardown
