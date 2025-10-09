"""
E2E tests for UI feedback sound system

Tests the professional sound feedback system including:
- Sound playback on notifications
- Mute/unmute functionality
- LocalStorage persistence
- Audio API integration

Requires mocking window.Audio since Playwright doesn't play actual audio
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="function")
def page_with_audio_mock(page: Page):
    """
    Set up a page with Audio API mocking
    Tracks all played sounds in window.playedSounds array
    """
    # Navigate to the app
    page.goto("http://localhost:8765")
    
    # Wait for app to load
    page.wait_for_selector(".top-nav-rack", state="visible", timeout=10000)
    
    # Inject Audio API mock before any sounds can play
    page.evaluate("""
        // Track all played sounds
        window.playedSounds = [];
        
        // Mock Audio constructor
        window.OriginalAudio = window.Audio;
        window.Audio = class MockAudio {
            constructor(src) {
                this.src = src;
                this.preload = 'auto';
                this.volume = 1.0;
                this.currentTime = 0;
                this.paused = true;
                this._onended = null;
            }
            
            play() {
                // Track that this sound was played
                window.playedSounds.push({
                    src: this.src,
                    volume: this.volume,
                    timestamp: Date.now()
                });
                this.paused = false;
                
                // Return a resolved promise (Audio.play() returns Promise<void>)
                return Promise.resolve();
            }
            
            pause() {
                this.paused = true;
            }
            
            load() {
                // No-op for preloading
            }
            
            set onended(handler) {
                this._onended = handler;
            }
            
            get onended() {
                return this._onended;
            }
        };
        
        console.log('✅ Audio API mocked - sounds will be tracked in window.playedSounds');
    """)
    
    # Re-initialize SoundService with mocked Audio
    page.evaluate("""
        if (window.SoundService) {
            window.SoundService.isInitialized = false;
            window.SoundService.init();
            console.log('🔄 SoundService re-initialized with mocked Audio');
        }
    """)
    
    yield page


def test_sound_service_initialization(page_with_audio_mock: Page):
    """Test that SoundService initializes correctly"""
    is_initialized = page_with_audio_mock.evaluate("window.SoundService.isInitialized")
    assert is_initialized, "SoundService should be initialized"
    
    sound_count = page_with_audio_mock.evaluate("Object.keys(window.SoundService.sounds).length")
    assert sound_count == 5, f"Expected 5 sounds loaded, got {sound_count}"
    
    print("✅ SoundService initialized with 5 sounds")


def test_success_notification_plays_sound(page_with_audio_mock: Page):
    """Test that success notifications play the success sound"""
    # Clear previous sounds
    page_with_audio_mock.evaluate("window.playedSounds = []")
    
    # Trigger a success notification
    page_with_audio_mock.evaluate("""
        window.Notifications.showSuccess('Test success message');
    """)
    
    # Wait for notification to appear
    page_with_audio_mock.wait_for_selector(".toast-notification.toast-success", timeout=2000)
    
    # Check that success sound was played
    played_sounds = page_with_audio_mock.evaluate("window.playedSounds")
    assert len(played_sounds) > 0, "No sounds were played"
    assert any('/assets/sounds/success.wav' in sound['src'] for sound in played_sounds), \
        "Success sound was not played"
    
    print("✅ Success notification triggered success.wav")


def test_error_notification_plays_sound(page_with_audio_mock: Page):
    """Test that error notifications play the error sound"""
    # Clear previous sounds
    page_with_audio_mock.evaluate("window.playedSounds = []")
    
    # Trigger an error notification
    page_with_audio_mock.evaluate("""
        window.Notifications.showError('Test error message');
    """)
    
    # Wait for notification to appear
    page_with_audio_mock.wait_for_selector(".toast-notification.toast-error", timeout=2000)
    
    # Check that error sound was played
    played_sounds = page_with_audio_mock.evaluate("window.playedSounds")
    assert len(played_sounds) > 0, "No sounds were played"
    assert any('/assets/sounds/error.wav' in sound['src'] for sound in played_sounds), \
        "Error sound was not played"
    
    print("✅ Error notification triggered error.wav")


def test_info_notification_plays_notification_sound(page_with_audio_mock: Page):
    """Test that info notifications play the notification sound"""
    # Clear previous sounds
    page_with_audio_mock.evaluate("window.playedSounds = []")
    
    # Trigger an info notification
    page_with_audio_mock.evaluate("""
        window.Notifications.showNotification('Test info message', 'info');
    """)
    
    # Wait for notification to appear
    page_with_audio_mock.wait_for_selector(".toast-notification.toast-info", timeout=2000)
    
    # Check that notification sound was played
    played_sounds = page_with_audio_mock.evaluate("window.playedSounds")
    assert len(played_sounds) > 0, "No sounds were played"
    assert any('/assets/sounds/notification.wav' in sound['src'] for sound in played_sounds), \
        "Notification sound was not played"
    
    print("✅ Info notification triggered notification.wav")


def test_mute_button_toggles_state(page_with_audio_mock: Page):
    """Test that the mute button toggles sound on/off"""
    # Get initial mute state
    initial_mute = page_with_audio_mock.evaluate("window.SoundService.getMute()")
    
    # Click the mute button
    mute_button = page_with_audio_mock.locator("#soundToggleBtn")
    mute_button.click()
    
    # Check that state changed
    new_mute = page_with_audio_mock.evaluate("window.SoundService.getMute()")
    assert new_mute != initial_mute, "Mute state should toggle"
    
    # Click again
    mute_button.click()
    
    # Should be back to initial state
    final_mute = page_with_audio_mock.evaluate("window.SoundService.getMute()")
    assert final_mute == initial_mute, "Mute state should toggle back"
    
    print("✅ Mute button toggles correctly")


def test_mute_persists_in_localstorage(page_with_audio_mock: Page):
    """Test that mute state persists in localStorage"""
    # Set to muted
    page_with_audio_mock.evaluate("""
        window.SoundService.setMute(true);
    """)
    
    # Check localStorage
    stored_value = page_with_audio_mock.evaluate("""
        localStorage.getItem('proximity_sound_muted')
    """)
    assert stored_value == "true", "Mute state should be stored as 'true'"
    
    # Set to unmuted
    page_with_audio_mock.evaluate("""
        window.SoundService.setMute(false);
    """)
    
    # Check localStorage again
    stored_value = page_with_audio_mock.evaluate("""
        localStorage.getItem('proximity_sound_muted')
    """)
    assert stored_value == "false", "Mute state should be stored as 'false'"
    
    print("✅ Mute state persists in localStorage")


def test_mute_state_restored_on_reload(page_with_audio_mock: Page):
    """Test that mute state is restored from localStorage on page reload"""
    # Set to muted
    page_with_audio_mock.evaluate("""
        window.SoundService.setMute(true);
    """)
    
    # Reload the page
    page_with_audio_mock.reload()
    
    # Wait for app to load again
    page_with_audio_mock.wait_for_selector(".top-nav-rack", state="visible", timeout=10000)
    
    # Re-inject mock (after reload)
    page_with_audio_mock.evaluate("""
        window.playedSounds = [];
        window.OriginalAudio = window.Audio;
        window.Audio = class MockAudio {
            constructor(src) {
                this.src = src;
                this.preload = 'auto';
                this.volume = 1.0;
                this.currentTime = 0;
                this.paused = true;
            }
            play() {
                window.playedSounds.push({src: this.src, timestamp: Date.now()});
                this.paused = false;
                return Promise.resolve();
            }
            pause() { this.paused = true; }
            load() {}
        };
    """)
    
    # Wait a bit for SoundService to initialize
    page_with_audio_mock.wait_for_timeout(500)
    
    # Check that mute state was restored
    is_muted = page_with_audio_mock.evaluate("window.SoundService.getMute()")
    assert is_muted, "Mute state should be restored from localStorage"
    
    # Verify button has muted class
    mute_button = page_with_audio_mock.locator("#soundToggleBtn")
    expect(mute_button).to_have_class("sound-toggle-btn muted")
    
    print("✅ Mute state restored after page reload")


def test_muted_sounds_dont_play(page_with_audio_mock: Page):
    """Test that sounds don't play when muted"""
    # Set to muted
    page_with_audio_mock.evaluate("""
        window.SoundService.setMute(true);
    """)
    
    # Clear played sounds
    page_with_audio_mock.evaluate("window.playedSounds = []")
    
    # Trigger a success notification
    page_with_audio_mock.evaluate("""
        window.Notifications.showSuccess('Test message');
    """)
    
    # Wait for notification to appear
    page_with_audio_mock.wait_for_selector(".toast-notification.toast-success", timeout=2000)
    
    # Check that NO sounds were played
    played_sounds = page_with_audio_mock.evaluate("window.playedSounds")
    assert len(played_sounds) == 0, "Sounds should not play when muted"
    
    print("✅ Sounds correctly muted")


def test_sound_button_icon_changes_on_toggle(page_with_audio_mock: Page):
    """Test that the sound button icon changes between volume-2 and volume-x"""
    mute_button = page_with_audio_mock.locator("#soundToggleBtn")
    sound_icon = page_with_audio_mock.locator("#soundIcon")
    
    # Get initial icon state
    initial_icon = sound_icon.get_attribute("data-lucide")
    
    # Click to toggle
    mute_button.click()
    page_with_audio_mock.wait_for_timeout(300)  # Wait for icon update
    
    # Check icon changed
    new_icon = sound_icon.get_attribute("data-lucide")
    assert new_icon != initial_icon, "Icon should change on toggle"
    assert new_icon in ["volume-2", "volume-x"], f"Icon should be volume-2 or volume-x, got {new_icon}"
    
    # Click again to toggle back
    mute_button.click()
    page_with_audio_mock.wait_for_timeout(300)
    
    # Should be back to initial
    final_icon = sound_icon.get_attribute("data-lucide")
    assert final_icon == initial_icon, "Icon should toggle back"
    
    print("✅ Sound button icon changes correctly")


def test_deploy_button_plays_deploy_start_sound(page_with_audio_mock: Page):
    """Test that clicking Deploy plays the deploy_start sound"""
    # Go to App Store
    page_with_audio_mock.evaluate("showView('appStore')")
    page_with_audio_mock.wait_for_timeout(500)
    
    # Wait for app cards to load
    page_with_audio_mock.wait_for_selector(".app-card", timeout=5000)
    
    # Clear played sounds
    page_with_audio_mock.evaluate("window.playedSounds = []")
    
    # Click first "Deploy" button to open modal
    deploy_btn = page_with_audio_mock.locator(".app-card .btn-primary").first
    deploy_btn.click()
    
    # Wait for modal to appear
    page_with_audio_mock.wait_for_selector("#deployModal", state="visible", timeout=3000)
    
    # Fill in hostname
    hostname_input = page_with_audio_mock.locator("#hostname")
    hostname_input.fill("test-app-sound")
    
    # Clear sounds again (modal open might have played click)
    page_with_audio_mock.evaluate("window.playedSounds = []")
    
    # Click Deploy in modal
    modal_deploy_btn = page_with_audio_mock.locator("#deployModal .btn-primary")
    modal_deploy_btn.click()
    
    # Wait a bit for sound to be triggered
    page_with_audio_mock.wait_for_timeout(500)
    
    # Check that deploy_start sound was played
    played_sounds = page_with_audio_mock.evaluate("window.playedSounds")
    
    # Debug: print what was played
    print(f"Played sounds: {played_sounds}")
    
    assert any('/assets/sounds/deploy_start.wav' in sound['src'] for sound in played_sounds), \
        "Deploy start sound was not played"
    
    print("✅ Deploy button triggered deploy_start.wav")
