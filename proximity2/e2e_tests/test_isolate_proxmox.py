"""
Test to isolate proxmox_host fixture issue
"""
import pytest
from playwright.sync_api import Page
from pages import LoginPage


def test_login_page_without_proxmox(page: Page, unique_user: dict, base_url: str):
    """Test LoginPage without proxmox_host fixture."""
    print("\n🔍 TEST: LoginPage WITHOUT proxmox_host")
    
    login_page = LoginPage(page, base_url)
    login_page.navigate()
    
    print(f"   Logging in as: {unique_user['username']}")
    login_page.login(
        username=unique_user['username'],
        password=unique_user['password'],
        wait_for_navigation=True
    )
    
    print(f"   ✅ Login successful! URL: {page.url}")
    assert "/login" not in page.url


def test_login_page_with_proxmox(page: Page, unique_user: dict, proxmox_host: dict, base_url: str):
    """Test LoginPage WITH proxmox_host fixture."""
    print("\n🔍 TEST: LoginPage WITH proxmox_host")
    print(f"   Proxmox host: {proxmox_host['name']}")
    
    login_page = LoginPage(page, base_url)
    login_page.navigate()
    
    print(f"   Logging in as: {unique_user['username']}")
    login_page.login(
        username=unique_user['username'],
        password=unique_user['password'],
        wait_for_navigation=True
    )
    
    print(f"   ✅ Login successful! URL: {page.url}")
    assert "/login" not in page.url
