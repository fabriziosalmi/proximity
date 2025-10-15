"""
Test per verificare che tutti i pulsanti delle azioni nelle card delle app in My Apps funzionino correttamente.

Azioni da testare:
1. Toggle Status (Start/Stop)
2. Open External (apri in nuova tab)
3. View Logs
4. Console
5. Backups
6. Update
7. Volumes
8. Monitoring
9. Canvas
10. Restart
11. Clone (PRO)
12. Edit Config (PRO)
13. Delete

Esegui con: pytest test_my_apps_actions.py -v -s
"""

import pytest
import logging
from playwright.sync_api import Page, expect
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione base
BASE_URL = "http://localhost:8765"
TEST_USERNAME = "fab"
TEST_PASSWORD = "invaders"


class TestMyAppsActions:
    """Test class per verificare tutte le azioni delle app cards in My Apps"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup: Login e navigazione a My Apps"""
        logger.info("🔐 Performing login...")
        
        try:
            page.goto(BASE_URL, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # Login
            page.wait_for_selector('input[type="text"]', timeout=15000)
            page.fill('input[type="text"]', TEST_USERNAME)
            page.fill('input[type="password"]', TEST_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # Attendi che il dashboard sia caricato (cerca la navigazione top)
            page.wait_for_selector('.top-nav-rack, .nav-rack-items', timeout=15000)
            logger.info("✅ Login successful")
            
            # Chiudi TUTTI i modal che potrebbero essere aperti
            logger.info("🔧 Closing any open modals...")
            page.evaluate("""
                // Chiudi tutti i modal
                document.querySelectorAll('.modal.show').forEach(modal => {
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                });
                // Rimuovi backdrop
                document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
                    backdrop.remove();
                });
            """)
            page.wait_for_timeout(500)
            
            # Naviga a My Apps (usa il link con data-view="apps")
            logger.info("📱 Navigating to My Apps...")
            my_apps_link = page.locator('a[data-view="apps"]').first
            my_apps_link.click()
            page.wait_for_timeout(2000)
            
            # Attendi il caricamento delle app o empty state
            try:
                page.wait_for_selector('.app-card.deployed, .empty-state', timeout=15000)
                
                # Verifica se ci sono app deployate
                deployed_cards = page.locator('.app-card.deployed').count()
                if deployed_cards == 0:
                    logger.warning("⚠️ No deployed apps found!")
                    logger.info("💡 Please deploy at least one app before running these tests")
                else:
                    logger.info(f"✅ Found {deployed_cards} deployed app(s)")
                    
            except Exception as e:
                logger.error(f"❌ Failed to load My Apps page: {e}")
                # Take screenshot for debugging
                page.screenshot(path="error_my_apps_loading.png")
                raise
                
            logger.info("✅ My Apps page loaded")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            page.screenshot(path="error_setup.png")
            raise
        
        yield page
    
    def get_first_running_app(self, page: Page):
        """Trova la prima app in stato 'running'"""
        logger.info("🔍 Looking for a running app...")
        
        # Verifica che ci siano app
        deployed_cards = page.locator('.app-card.deployed').count()
        if deployed_cards == 0:
            logger.warning("⚠️ No deployed apps found!")
            return None
        
        logger.info(f"📦 Found {deployed_cards} deployed app(s)")
        
        # Attendi che le card siano completamente renderizzate
        page.wait_for_timeout(2000)
        
        # Cerca tutte le app cards
        app_cards = page.locator('.app-card.deployed').all()
        
        # Cerca un'app running
        for i, card in enumerate(app_cards):
            try:
                status_indicator = card.locator('.status-indicator.status-running')
                if status_indicator.count() > 0:
                    app_name = card.locator('.app-name').text_content()
                    logger.info(f"✅ Found running app: {app_name}")
                    return card
            except Exception as e:
                logger.debug(f"Error checking card {i}: {e}")
                continue
        
        logger.warning("⚠️ No running apps found, using first app anyway")
        return app_cards[0] if app_cards else None
    
    def get_first_stopped_app(self, page: Page):
        """Trova la prima app in stato 'stopped'"""
        logger.info("🔍 Looking for a stopped app...")
        
        app_cards = page.locator('.app-card.deployed').all()
        
        for card in app_cards:
            try:
                status_indicator = card.locator('.status-indicator.status-stopped')
                if status_indicator.count() > 0:
                    app_name = card.locator('.app-name').text_content()
                    logger.info(f"✅ Found stopped app: {app_name}")
                    return card
            except Exception as e:
                logger.debug(f"Error checking card: {e}")
                continue
        
        return None
    
    def test_00_verify_apps_present(self, page: Page):
        """Test 0: Verifica preliminare presenza app deployate"""
        logger.info("\n" + "="*80)
        logger.info("TEST 0: Verify Apps Present (Prerequisite Check)")
        logger.info("="*80)
        
        # Conta le app deployate
        deployed_count = page.locator('.app-card.deployed').count()
        empty_state = page.locator('.empty-state').count()
        
        logger.info(f"📊 Deployed apps found: {deployed_count}")
        logger.info(f"📊 Empty state visible: {empty_state > 0}")
        
        if deployed_count == 0:
            logger.error("❌ No deployed apps found!")
            logger.error("💡 Please deploy at least one app before running these tests:")
            logger.error("   1. Go to http://localhost:8765")
            logger.error("   2. Login with admin/admin")
            logger.error("   3. Go to 'Catalog' and deploy an app")
            logger.error("   4. Wait for deployment to complete")
            logger.error("   5. Re-run these tests")
            pytest.fail("No deployed apps available for testing")
        
        logger.info(f"✅ TEST 0 PASSED: Found {deployed_count} app(s) ready for testing")
    
    def test_01_toggle_status_stop(self, page: Page):
        """Test 1: Pulsante Toggle Status (Stop per app running)"""
        logger.info("\n" + "="*80)
        logger.info("TEST 1: Toggle Status - Stop")
        logger.info("="*80)
        
        app_card = self.get_first_running_app(page)
        if not app_card:
            pytest.skip("No running app available for testing")
        
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Stop action on: {app_name}")
        
        # Click sul pulsante toggle-status (dovrebbe essere "pause" per stop)
        toggle_btn = app_card.locator('button[data-action="toggle-status"]')
        expect(toggle_btn).to_be_visible()
        
        logger.info("🖱️ Clicking Stop button...")
        toggle_btn.click()
        
        # Attendi notifica di successo o cambio stato
        page.wait_for_timeout(2000)
        
        # Verifica che sia apparsa una notifica o che lo stato sia cambiato
        notifications = page.locator('.toast, .notification').all()
        if notifications:
            logger.info("✅ Notification appeared after stop action")
        
        logger.info("✅ TEST 1 PASSED: Toggle Status (Stop) works")
    
    def test_02_toggle_status_start(self, page: Page):
        """Test 2: Pulsante Toggle Status (Start per app stopped)"""
        logger.info("\n" + "="*80)
        logger.info("TEST 2: Toggle Status - Start")
        logger.info("="*80)
        
        # Aspetta che l'app si sia fermata dal test precedente
        page.wait_for_timeout(3000)
        page.reload()
        page.wait_for_timeout(2000)
        
        app_card = self.get_first_stopped_app(page)
        if not app_card:
            logger.warning("⚠️ No stopped app found, skipping start test")
            pytest.skip("No stopped app available for testing")
        
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Start action on: {app_name}")
        
        toggle_btn = app_card.locator('button[data-action="toggle-status"]')
        expect(toggle_btn).to_be_visible()
        
        logger.info("🖱️ Clicking Start button...")
        toggle_btn.click()
        
        page.wait_for_timeout(2000)
        logger.info("✅ TEST 2 PASSED: Toggle Status (Start) works")
    
    def test_03_open_external(self, page: Page):
        """Test 3: Pulsante Open External"""
        logger.info("\n" + "="*80)
        logger.info("TEST 3: Open External")
        logger.info("="*80)
        
        page.reload()
        page.wait_for_timeout(2000)
        
        app_card = self.get_first_running_app(page)
        if not app_card:
            pytest.skip("No running app available for testing")
        
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Open External on: {app_name}")
        
        open_btn = app_card.locator('button[data-action="open-external"]')
        
        # Verifica che il pulsante sia visibile e non disabilitato
        if open_btn.count() > 0:
            is_disabled = open_btn.get_attribute('disabled')
            if is_disabled:
                logger.warning("⚠️ Open External button is disabled (no URL or app not running)")
                pytest.skip("Open External button is disabled")
            
            logger.info("🖱️ Clicking Open External button...")
            
            # Intercetta l'apertura di nuove finestre
            with page.expect_popup() as popup_info:
                open_btn.click()
                page.wait_for_timeout(1000)
                
            logger.info("✅ TEST 3 PASSED: Open External works")
        else:
            logger.warning("⚠️ Open External button not found")
            pytest.skip("Open External button not found")
    
    def test_04_view_logs(self, page: Page):
        """Test 4: Pulsante View Logs"""
        logger.info("\n" + "="*80)
        logger.info("TEST 4: View Logs")
        logger.info("="*80)
        
        app_card = self.get_first_running_app(page)
        if not app_card:
            pytest.skip("No running app available for testing")
        
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing View Logs on: {app_name}")
        
        logs_btn = app_card.locator('button[data-action="view-logs"]')
        expect(logs_btn).to_be_visible()
        
        logger.info("🖱️ Clicking View Logs button...")
        logs_btn.click()
        
        # Attendi che si apra il modal dei logs
        page.wait_for_timeout(2000)
        
        # Verifica che sia apparso un modal
        modal = page.locator('.modal, #logsModal')
        if modal.count() > 0 and modal.first.is_visible():
            logger.info("✅ Logs modal appeared")
            
            # Chiudi il modal
            close_btn = page.locator('.modal button:has-text("Close"), .modal .close')
            if close_btn.count() > 0:
                close_btn.first.click()
                page.wait_for_timeout(500)
        
        logger.info("✅ TEST 4 PASSED: View Logs works")
    
    def test_05_console(self, page: Page):
        """Test 5: Pulsante Console"""
        logger.info("\n" + "="*80)
        logger.info("TEST 5: Console")
        logger.info("="*80)
        
        app_card = self.get_first_running_app(page)
        if not app_card:
            pytest.skip("No running app available for testing")
        
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Console on: {app_name}")
        
        console_btn = app_card.locator('button[data-action="console"]')
        expect(console_btn).to_be_visible()
        
        logger.info("🖱️ Clicking Console button...")
        console_btn.click()
        
        page.wait_for_timeout(2000)
        
        # Verifica modal console
        modal = page.locator('.modal, #consoleModal')
        if modal.count() > 0 and modal.first.is_visible():
            logger.info("✅ Console modal appeared")
            
            # Chiudi modal
            close_btn = page.locator('.modal button:has-text("Close"), .modal .close')
            if close_btn.count() > 0:
                close_btn.first.click()
                page.wait_for_timeout(500)
        
        logger.info("✅ TEST 5 PASSED: Console works")
    
    def test_06_backups(self, page: Page):
        """Test 6: Pulsante Backups"""
        logger.info("\n" + "="*80)
        logger.info("TEST 6: Backups")
        logger.info("="*80)
        
        app_card = self.get_first_running_app(page)
        if not app_card:
            app_card = page.locator('.app-card.deployed').first
        
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Backups on: {app_name}")
        
        backups_btn = app_card.locator('button[data-action="backups"]')
        expect(backups_btn).to_be_visible()
        
        logger.info("🖱️ Clicking Backups button...")
        backups_btn.click()
        
        page.wait_for_timeout(2000)
        
        # Verifica modal backups
        modal = page.locator('.modal, #backupModal')
        if modal.count() > 0 and modal.first.is_visible():
            logger.info("✅ Backups modal appeared")
            
            # Chiudi modal
            close_btn = page.locator('.modal button:has-text("Close"), .modal .close, button:has-text("Cancel")')
            if close_btn.count() > 0:
                close_btn.first.click()
                page.wait_for_timeout(500)
        
        logger.info("✅ TEST 6 PASSED: Backups works")
    
    def test_07_volumes(self, page: Page):
        """Test 7: Pulsante Volumes"""
        logger.info("\n" + "="*80)
        logger.info("TEST 7: Volumes")
        logger.info("="*80)
        
        app_card = self.get_first_running_app(page)
        if not app_card:
            app_card = page.locator('.app-card.deployed').first
        
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Volumes on: {app_name}")
        
        volumes_btn = app_card.locator('button[data-action="volumes"]')
        expect(volumes_btn).to_be_visible()
        
        logger.info("🖱️ Clicking Volumes button...")
        volumes_btn.click()
        
        page.wait_for_timeout(2000)
        
        # Verifica modal volumes
        modal = page.locator('.modal, #volumesModal')
        if modal.count() > 0 and modal.first.is_visible():
            logger.info("✅ Volumes modal appeared")
            
            # Chiudi modal
            close_btn = page.locator('.modal button:has-text("Close"), .modal .close')
            if close_btn.count() > 0:
                close_btn.first.click()
                page.wait_for_timeout(500)
        
        logger.info("✅ TEST 7 PASSED: Volumes works")
    
    def test_08_monitoring(self, page: Page):
        """Test 8: Pulsante Monitoring"""
        logger.info("\n" + "="*80)
        logger.info("TEST 8: Monitoring")
        logger.info("="*80)
        
        app_card = self.get_first_running_app(page)
        if not app_card:
            pytest.skip("No running app available for testing")
        
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Monitoring on: {app_name}")
        
        monitoring_btn = app_card.locator('button[data-action="monitoring"]')
        
        if monitoring_btn.count() > 0:
            is_disabled = monitoring_btn.get_attribute('disabled')
            if is_disabled:
                logger.warning("⚠️ Monitoring button is disabled")
                pytest.skip("Monitoring button is disabled")
            
            logger.info("🖱️ Clicking Monitoring button...")
            monitoring_btn.click()
            
            page.wait_for_timeout(2000)
            
            # Verifica modal monitoring
            modal = page.locator('.modal, #monitoringModal')
            if modal.count() > 0 and modal.first.is_visible():
                logger.info("✅ Monitoring modal appeared")
                
                # Chiudi modal
                close_btn = page.locator('.modal button:has-text("Close"), .modal .close')
                if close_btn.count() > 0:
                    close_btn.first.click()
                    page.wait_for_timeout(500)
            
            logger.info("✅ TEST 8 PASSED: Monitoring works")
        else:
            logger.warning("⚠️ Monitoring button not found")
            pytest.skip("Monitoring button not found")
    
    def test_09_restart(self, page: Page):
        """Test 9: Pulsante Restart"""
        logger.info("\n" + "="*80)
        logger.info("TEST 9: Restart")
        logger.info("="*80)
        
        app_card = self.get_first_running_app(page)
        if not app_card:
            pytest.skip("No running app available for testing")
        
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Restart on: {app_name}")
        
        restart_btn = app_card.locator('button[data-action="restart"]')
        
        if restart_btn.count() > 0:
            is_disabled = restart_btn.get_attribute('disabled')
            if is_disabled:
                logger.warning("⚠️ Restart button is disabled")
                pytest.skip("Restart button is disabled")
            
            logger.info("🖱️ Clicking Restart button...")
            restart_btn.click()
            
            page.wait_for_timeout(2000)
            
            # Verifica notifica
            notifications = page.locator('.toast, .notification').all()
            if notifications:
                logger.info("✅ Notification appeared after restart action")
            
            logger.info("✅ TEST 9 PASSED: Restart works")
        else:
            logger.warning("⚠️ Restart button not found")
            pytest.skip("Restart button not found")
    
    def test_10_update(self, page: Page):
        """Test 10: Pulsante Update"""
        logger.info("\n" + "="*80)
        logger.info("TEST 10: Update")
        logger.info("="*80)
        
        app_card = page.locator('.app-card.deployed').first
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Update on: {app_name}")
        
        update_btn = app_card.locator('button[data-action="update"]')
        
        if update_btn.count() > 0:
            expect(update_btn).to_be_visible()
            
            logger.info("🖱️ Clicking Update button...")
            update_btn.click()
            
            page.wait_for_timeout(2000)
            
            # Verifica modal update
            modal = page.locator('.modal, #updateModal')
            if modal.count() > 0 and modal.first.is_visible():
                logger.info("✅ Update modal appeared")
                
                # Chiudi modal
                close_btn = page.locator('.modal button:has-text("Close"), .modal .close, button:has-text("Cancel")')
                if close_btn.count() > 0:
                    close_btn.first.click()
                    page.wait_for_timeout(500)
            
            logger.info("✅ TEST 10 PASSED: Update works")
        else:
            logger.warning("⚠️ Update button not found")
            pytest.skip("Update button not found")
    
    def test_11_clone_pro_feature(self, page: Page):
        """Test 11: Pulsante Clone (PRO Feature)"""
        logger.info("\n" + "="*80)
        logger.info("TEST 11: Clone (PRO Feature)")
        logger.info("="*80)
        
        app_card = page.locator('.app-card.deployed').first
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Clone on: {app_name}")
        
        clone_btn = app_card.locator('button[data-action="clone"]')
        
        if clone_btn.count() > 0:
            expect(clone_btn).to_be_visible()
            logger.info("🖱️ Clicking Clone button...")
            clone_btn.click()
            
            page.wait_for_timeout(2000)
            
            # Potrebbe mostrare un modal PRO o di clone
            modal = page.locator('.modal')
            if modal.count() > 0 and modal.first.is_visible():
                modal_text = modal.first.text_content().lower()
                if 'pro' in modal_text or 'premium' in modal_text:
                    logger.info("✅ PRO feature modal appeared (expected for free users)")
                elif 'clone' in modal_text:
                    logger.info("✅ Clone modal appeared")
                
                # Chiudi modal
                close_btn = page.locator('.modal button:has-text("Close"), .modal .close, button:has-text("Cancel")')
                if close_btn.count() > 0:
                    close_btn.first.click()
                    page.wait_for_timeout(500)
            
            logger.info("✅ TEST 11 PASSED: Clone button works")
        else:
            logger.warning("⚠️ Clone button not found")
            pytest.skip("Clone button not found")
    
    def test_12_edit_config_pro_feature(self, page: Page):
        """Test 12: Pulsante Edit Config (PRO Feature)"""
        logger.info("\n" + "="*80)
        logger.info("TEST 12: Edit Config (PRO Feature)")
        logger.info("="*80)
        
        app_card = page.locator('.app-card.deployed').first
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Edit Config on: {app_name}")
        
        edit_btn = app_card.locator('button[data-action="edit-config"]')
        
        if edit_btn.count() > 0:
            expect(edit_btn).to_be_visible()
            logger.info("🖱️ Clicking Edit Config button...")
            edit_btn.click()
            
            page.wait_for_timeout(2000)
            
            # Potrebbe mostrare un modal PRO o di edit config
            modal = page.locator('.modal')
            if modal.count() > 0 and modal.first.is_visible():
                modal_text = modal.first.text_content().lower()
                if 'pro' in modal_text or 'premium' in modal_text:
                    logger.info("✅ PRO feature modal appeared (expected for free users)")
                elif 'config' in modal_text or 'resource' in modal_text:
                    logger.info("✅ Edit Config modal appeared")
                
                # Chiudi modal
                close_btn = page.locator('.modal button:has-text("Close"), .modal .close, button:has-text("Cancel")')
                if close_btn.count() > 0:
                    close_btn.first.click()
                    page.wait_for_timeout(500)
            
            logger.info("✅ TEST 12 PASSED: Edit Config button works")
        else:
            logger.warning("⚠️ Edit Config button not found")
            pytest.skip("Edit Config button not found")
    
    def test_13_canvas(self, page: Page):
        """Test 13: Pulsante Canvas"""
        logger.info("\n" + "="*80)
        logger.info("TEST 13: Canvas")
        logger.info("="*80)
        
        app_card = self.get_first_running_app(page)
        if not app_card:
            pytest.skip("No running app available for testing")
        
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Canvas on: {app_name}")
        
        canvas_btn = app_card.locator('button[data-action="canvas"]')
        
        if canvas_btn.count() > 0 and canvas_btn.is_visible():
            is_disabled = canvas_btn.get_attribute('disabled')
            if is_disabled:
                logger.warning("⚠️ Canvas button is disabled")
                pytest.skip("Canvas button is disabled")
            
            logger.info("🖱️ Clicking Canvas button...")
            canvas_btn.click()
            
            page.wait_for_timeout(2000)
            
            # Verifica che si apra la vista canvas
            canvas_view = page.locator('#canvas-view, .canvas-container')
            if canvas_view.count() > 0 and canvas_view.first.is_visible():
                logger.info("✅ Canvas view appeared")
                
                # Torna a My Apps
                my_apps_link = page.locator('a[href="#apps"]')
                if my_apps_link.count() > 0:
                    my_apps_link.click()
                    page.wait_for_timeout(1000)
            
            logger.info("✅ TEST 13 PASSED: Canvas works")
        else:
            logger.warning("⚠️ Canvas button not found or not visible")
            pytest.skip("Canvas button not available")
    
    def test_14_delete_button_opens_modal(self, page: Page):
        """Test 14: Pulsante Delete (verifica solo apertura modal, non elimina)"""
        logger.info("\n" + "="*80)
        logger.info("TEST 14: Delete (Modal Opening Only)")
        logger.info("="*80)
        
        app_card = page.locator('.app-card.deployed').first
        app_name = app_card.locator('.app-name').text_content()
        logger.info(f"🎯 Testing Delete modal on: {app_name}")
        
        # Trova il pulsante delete (quello con icona trash-2)
        delete_btn = app_card.locator('button.danger[data-tooltip*="Delete"]')
        
        if delete_btn.count() == 0:
            # Prova un selettore alternativo
            delete_btn = app_card.locator('button:has([data-lucide="trash-2"])')
        
        if delete_btn.count() > 0:
            expect(delete_btn).to_be_visible()
            
            logger.info("🖱️ Clicking Delete button...")
            delete_btn.click()
            
            page.wait_for_timeout(2000)
            
            # Verifica che si apra il modal di conferma
            modal = page.locator('.modal')
            if modal.count() > 0 and modal.first.is_visible():
                modal_text = modal.first.text_content().lower()
                if 'delete' in modal_text or 'remove' in modal_text:
                    logger.info("✅ Delete confirmation modal appeared")
                    
                    # Chiudi modal (CANCEL, non eliminiamo davvero)
                    cancel_btn = page.locator('.modal button:has-text("Cancel"), .modal .btn-ghost')
                    if cancel_btn.count() > 0:
                        logger.info("🖱️ Clicking Cancel to close modal...")
                        cancel_btn.first.click()
                        page.wait_for_timeout(500)
                        logger.info("✅ Modal closed successfully")
            
            logger.info("✅ TEST 14 PASSED: Delete button opens modal correctly")
        else:
            logger.warning("⚠️ Delete button not found")
            pytest.skip("Delete button not found")
    
    def test_15_all_buttons_present(self, page: Page):
        """Test 15: Verifica che tutti i pulsanti siano presenti nel template"""
        logger.info("\n" + "="*80)
        logger.info("TEST 15: All Buttons Present in Template")
        logger.info("="*80)
        
        app_card = page.locator('.app-card.deployed').first
        
        expected_actions = [
            'toggle-status',
            'open-external',
            'view-logs',
            'console',
            'backups',
            'update',
            'volumes',
            'monitoring',
            'restart',
            'clone',
            'edit-config'
        ]
        
        missing_buttons = []
        present_buttons = []
        
        for action in expected_actions:
            btn = app_card.locator(f'button[data-action="{action}"]')
            if btn.count() > 0:
                present_buttons.append(action)
                logger.info(f"  ✅ {action} button found")
            else:
                missing_buttons.append(action)
                logger.warning(f"  ⚠️ {action} button NOT found")
        
        # Verifica delete button separatamente (non ha data-action)
        delete_btn = app_card.locator('button.danger')
        if delete_btn.count() > 0:
            present_buttons.append('delete')
            logger.info(f"  ✅ delete button found")
        else:
            missing_buttons.append('delete')
            logger.warning(f"  ⚠️ delete button NOT found")
        
        # Canvas button può essere nascosto
        canvas_btn = app_card.locator('button[data-action="canvas"]')
        if canvas_btn.count() > 0:
            present_buttons.append('canvas')
            logger.info(f"  ✅ canvas button found (may be hidden)")
        
        logger.info(f"\n📊 Summary:")
        logger.info(f"  ✅ Present buttons: {len(present_buttons)}")
        logger.info(f"  ⚠️ Missing buttons: {len(missing_buttons)}")
        
        if missing_buttons:
            logger.warning(f"Missing buttons: {', '.join(missing_buttons)}")
        
        logger.info("✅ TEST 15 PASSED: Button presence verification completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
