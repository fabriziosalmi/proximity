"""
Quick debug test to capture console errors
"""
import pytest
from playwright.sync_api import Page

def test_console_errors(page: Page, base_url: str):
    """Capture any console errors when loading /apps"""

    console_messages = []
    page_errors = []

    # Capture console messages
    page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))

    # Capture page errors
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    print("\n🔍 Loading /apps page...")
    page.goto(f"{base_url}/apps", wait_until="networkidle")

    print("\n📋 Console Messages:")
    for msg in console_messages:
        print(f"  {msg}")

    print("\n❌ Page Errors:")
    if page_errors:
        for err in page_errors:
            print(f"  {err}")
    else:
        print("  None")

    # Check if API call was made
    print("\n🌐 Checking if /api/apps was called...")
    page.wait_for_timeout(2000)

    assert len(page_errors) == 0, f"Page has {len(page_errors)} errors"
