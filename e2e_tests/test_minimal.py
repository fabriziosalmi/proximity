"""
Minimal test to diagnose fixture issue
"""
import pytest
from playwright.sync_api import Page


def test_minimal_without_fixtures(page: Page):
    """Test without custom fixtures to isolate the problem."""
    print("\n✅ Test started - Page fixture works")
    page.goto("https://localhost:5173")
    print(f"✅ Navigated to: {page.url}")
    assert "localhost" in page.url
    print("✅ Test completed successfully")


def test_minimal_with_user(page: Page, unique_user: dict):
    """Test with unique_user fixture to see if it's the blocker."""
    print(f"\n✅ Got unique user: {unique_user['username']}")
    page.goto("https://localhost:5173")
    print(f"✅ Navigated to: {page.url}")
    print("✅ Test completed successfully")
