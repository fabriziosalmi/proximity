"""
Quick test per verificare che il setup sia corretto prima di eseguire la suite completa.

Esegui con: pytest test_quick_check.py -v -s
"""

import pytest
import logging
from playwright.sync_api import Page, expect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8765"
TEST_USERNAME = "fab"
TEST_PASSWORD = "invaders"


def test_server_is_running(page: Page):
    """Test 1: Verifica che il server sia in esecuzione"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Server Health Check")
    logger.info("="*80)
    
    try:
        page.goto(BASE_URL, timeout=10000)
        logger.info(f"✅ Server is responding at {BASE_URL}")
        
        # Verifica che la pagina sia caricata
        expect(page).to_have_title(lambda title: "Proximity" in title or len(title) > 0)
        logger.info("✅ Page loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Server is not responding: {e}")
        logger.error(f"💡 Please start the backend server:")
        logger.error(f"   cd backend && python main.py")
        pytest.fail("Server not running")


def test_login_works(page: Page):
    """Test 2: Verifica che il login funzioni"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Login Functionality")
    logger.info("="*80)
    
    try:
        page.goto(BASE_URL, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Cerca i campi di login
        username_field = page.locator('input[type="text"]')
        password_field = page.locator('input[type="password"]')
        submit_button = page.locator('button[type="submit"]')
        
        expect(username_field).to_be_visible(timeout=5000)
        expect(password_field).to_be_visible(timeout=5000)
        expect(submit_button).to_be_visible(timeout=5000)
        
        logger.info("✅ Login form found")
        
        # Prova il login
        username_field.fill(TEST_USERNAME)
        password_field.fill(TEST_PASSWORD)
        submit_button.click()
        
        page.wait_for_load_state("networkidle", timeout=15000)
        
        # Verifica che il login sia avvenuto (cerca la sidebar)
        page.wait_for_selector('.sidebar', timeout=10000)
        logger.info("✅ Login successful - Dashboard loaded")
        
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        logger.error(f"💡 Check credentials: {TEST_USERNAME} / {TEST_PASSWORD}")
        page.screenshot(path="error_login.png")
        pytest.fail("Login failed")


def test_my_apps_navigation(page: Page):
    """Test 3: Verifica che la navigazione a My Apps funzioni"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: My Apps Navigation")
    logger.info("="*80)
    
    try:
        # Login
        page.goto(BASE_URL, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        page.fill('input[type="text"]', TEST_USERNAME)
        page.fill('input[type="password"]', TEST_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_selector('.sidebar', timeout=10000)
        
        logger.info("✅ Logged in")
        
        # Naviga a My Apps
        my_apps_link = page.locator('a[href="#apps"]')
        expect(my_apps_link).to_be_visible(timeout=5000)
        
        logger.info("✅ My Apps link found")
        my_apps_link.click()
        page.wait_for_timeout(2000)
        
        # Attendi caricamento
        page.wait_for_selector('.app-card.deployed, .empty-state', timeout=15000)
        
        logger.info("✅ My Apps page loaded")
        
    except Exception as e:
        logger.error(f"❌ Navigation failed: {e}")
        page.screenshot(path="error_navigation.png")
        pytest.fail("Navigation to My Apps failed")


def test_apps_are_deployed(page: Page):
    """Test 4: Verifica che ci siano app deployate"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Deployed Apps Check")
    logger.info("="*80)
    
    try:
        # Login e naviga
        page.goto(BASE_URL, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        page.fill('input[type="text"]', TEST_USERNAME)
        page.fill('input[type="password"]', TEST_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_selector('.sidebar', timeout=10000)
        
        my_apps_link = page.locator('a[href="#apps"]')
        my_apps_link.click()
        page.wait_for_timeout(2000)
        page.wait_for_selector('.app-card.deployed, .empty-state', timeout=15000)
        
        # Conta le app
        deployed_count = page.locator('.app-card.deployed').count()
        empty_state_visible = page.locator('.empty-state').count() > 0
        
        logger.info(f"📊 Deployed apps: {deployed_count}")
        logger.info(f"📊 Empty state visible: {empty_state_visible}")
        
        if deployed_count == 0:
            logger.warning("⚠️ No deployed apps found!")
            logger.warning("💡 To test app actions, you need to deploy at least one app:")
            logger.warning("   1. Go to 'Catalog' tab")
            logger.warning("   2. Choose an app (e.g., Nginx)")
            logger.warning("   3. Click 'Deploy'")
            logger.warning("   4. Wait for deployment to complete")
            logger.warning("   5. Return to 'My Apps'")
            logger.warning("")
            logger.warning("⏭️  Tests will skip actions that require deployed apps")
            
            # Non failliamo, ma avvisiamo
            pytest.skip("No deployed apps - some tests will be skipped")
        else:
            logger.info(f"✅ Found {deployed_count} deployed app(s)")
            
            # Verifica almeno una app running
            running_count = page.locator('.status-indicator.status-running').count()
            logger.info(f"📊 Running apps: {running_count}")
            
            if running_count == 0:
                logger.warning("⚠️ No running apps found")
                logger.warning("💡 Some tests may be skipped or fail")
            
    except Exception as e:
        logger.error(f"❌ Check failed: {e}")
        page.screenshot(path="error_apps_check.png")
        pytest.fail("Apps check failed")


def test_app_card_structure(page: Page):
    """Test 5: Verifica la struttura delle app cards"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: App Card Structure Check")
    logger.info("="*80)
    
    try:
        # Login e naviga
        page.goto(BASE_URL, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        page.fill('input[type="text"]', TEST_USERNAME)
        page.fill('input[type="password"]', TEST_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_selector('.sidebar', timeout=10000)
        
        my_apps_link = page.locator('a[href="#apps"]')
        my_apps_link.click()
        page.wait_for_timeout(2000)
        page.wait_for_selector('.app-card.deployed, .empty-state', timeout=15000)
        
        deployed_count = page.locator('.app-card.deployed').count()
        
        if deployed_count == 0:
            pytest.skip("No deployed apps to check structure")
        
        # Prendi la prima card
        first_card = page.locator('.app-card.deployed').first
        
        # Verifica elementi base
        app_name = first_card.locator('.app-name')
        expect(app_name).to_be_visible(timeout=5000)
        logger.info(f"✅ App name found: {app_name.text_content()}")
        
        # Verifica action buttons
        action_buttons = first_card.locator('.action-icon')
        button_count = action_buttons.count()
        logger.info(f"✅ Action buttons found: {button_count}")
        
        if button_count < 10:
            logger.warning(f"⚠️ Expected ~13 buttons, found {button_count}")
        
        # Verifica status indicator
        status = first_card.locator('.status-indicator')
        expect(status).to_be_visible(timeout=5000)
        logger.info("✅ Status indicator found")
        
        logger.info("✅ App card structure looks good")
        
    except Exception as e:
        logger.error(f"❌ Structure check failed: {e}")
        page.screenshot(path="error_structure.png")
        pytest.fail("App card structure check failed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
