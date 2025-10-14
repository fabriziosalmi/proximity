/* ============================================================================
   TOP NAVIGATION RACK - JavaScript
   Handles the new horizontal navigation system
   ============================================================================ */

// Initialize Top Navigation Rack
function initTopNavRack() {
    console.log('🎯 Initializing Top Navigation Rack...');

    
    // Sound toggle button - Now opens advanced panel
    const soundToggleBtn = document.getElementById('soundToggleBtn');
    const soundIcon = document.getElementById('soundIcon');
    let soundPanelOpen = false;

    if (soundToggleBtn && soundIcon && window.SoundService) {
        // Set initial state from SoundService
        updateSoundButton(soundToggleBtn, soundIcon);

        soundToggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            if (soundPanelOpen) {
                closeSoundPanel();
                soundPanelOpen = false;
            } else {
                showSoundPanel(soundToggleBtn);
                soundPanelOpen = true;
            }
        });
    }

    // Close sound panel when clicking outside
    document.addEventListener('click', (e) => {
        if (soundPanelOpen && !e.target.closest('.sound-panel') && !e.target.closest('#soundToggleBtn')) {
            closeSoundPanel();
            soundPanelOpen = false;
        }
    });
    
    // Fullscreen toggle button
    const fullscreenToggleBtn = document.getElementById('fullscreenToggleBtn');
    const fullscreenIcon = document.getElementById('fullscreenIcon');

    if (fullscreenToggleBtn && fullscreenIcon) {
        // Set initial icon
        updateFullscreenIcon(fullscreenIcon);

        fullscreenToggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            toggleFullscreen();
        });

        // Listen for fullscreen changes (user pressing ESC, F11, etc.)
        document.addEventListener('fullscreenchange', () => {
            updateFullscreenIcon(fullscreenIcon);
        });
        document.addEventListener('webkitfullscreenchange', () => {
            updateFullscreenIcon(fullscreenIcon);
        });
        document.addEventListener('mozfullscreenchange', () => {
            updateFullscreenIcon(fullscreenIcon);
        });
        document.addEventListener('MSFullscreenChange', () => {
            updateFullscreenIcon(fullscreenIcon);
        });
    }
    
    // User profile button toggle
    const userProfileBtn = document.getElementById('userProfileBtn');
    const userMenu = document.getElementById('userMenu');
    
    if (userProfileBtn && userMenu) {
        userProfileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenu.classList.toggle('show');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!userProfileBtn.contains(e.target) && !userMenu.contains(e.target)) {
                userMenu.classList.remove('show');
            }
        });
    }
    
    // Initialize Lucide icons in the navigation bar
    if (window.lucide) {
        window.lucide.createIcons();
        console.log('✓ Top Navigation Rack icons initialized');
    }
    
    console.log('✓ Top Navigation Rack initialized');
}

// Update sound button appearance based on mute state
function updateSoundButton(button, icon) {
    if (window.SoundService) {
        const isMuted = window.SoundService.getMute();
        
        if (isMuted) {
            button.classList.add('muted');
            button.title = 'Unmute Sound';
            icon.setAttribute('data-lucide', 'volume-x');
        } else {
            button.classList.remove('muted');
            button.title = 'Mute Sound';
            icon.setAttribute('data-lucide', 'volume-2');
        }
        
        // Re-render Lucide icon
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }
}

// Update active navigation item
function updateActiveNav(viewName) {
    const navItems = document.querySelectorAll('.nav-rack-item');
    navItems.forEach(item => {
        if (item.dataset.view === viewName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// Update user info in navigation
function updateUserInfoNav() {
    const user = Auth.getUserInfo();
    if (user) {
        // Update legacy user info elements (if they exist)
        const userNameEl = document.querySelector('.nav-rack-user .user-name');
        const userRoleEl = document.querySelector('.nav-rack-user .user-role');
        const userAvatarEl = document.querySelector('.nav-rack-user .user-avatar');
        
        if (userNameEl) {
            userNameEl.textContent = user.username || 'User';
        }
        if (userRoleEl) {
            userRoleEl.textContent = user.role === 'admin' ? 'Admin' : 'User';
        }
        if (userAvatarEl) {
            const initials = (user.username || 'U').substring(0, 2).toUpperCase();
            userAvatarEl.textContent = initials;
        }
        
        // Update new user-info element
        const userInfoEl = document.getElementById('userInfo');
        const usernameDisplayEl = document.getElementById('usernameDisplay');
        
        if (userInfoEl && usernameDisplayEl) {
            usernameDisplayEl.textContent = user.username || 'User';
            // Keep user info hidden for now - reserved for future user profile features
            // userInfoEl.style.display = ''; // Uncomment when implementing user profile
            
            // Initialize icon if lucide is available
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
    }
}

// Update apps count badge
function updateAppsCountBadge(count) {
    const badge = document.getElementById('appsCount');
    if (badge) {
        badge.textContent = count || '0';
        // Add pulse animation if count > 0
        if (count > 0) {
            badge.style.animation = 'pulse 2s ease-in-out infinite';
        } else {
            badge.style.animation = 'none';
        }
    }
}

// Show advanced sound control panel
function showSoundPanel(button) {
    // Remove existing panel
    closeSoundPanel();

    const panel = document.createElement('div');
    panel.className = 'sound-panel';
    panel.innerHTML = `
        <div class="sound-panel-header">
            <span>Audio Settings</span>
        </div>
        <div class="sound-panel-body">
            <!-- Quick Mute Toggle -->
            <button class="sound-quick-mute" id="quickMute">
                <i data-lucide="${window.SoundService.getMute() ? 'volume-x' : 'volume-2'}"></i>
                <span>${window.SoundService.getMute() ? 'Unmute' : 'Mute'}</span>
            </button>

            <!-- Volume Slider -->
            <div class="sound-control-group">
                <label>Volume</label>
                <div class="volume-slider-wrapper">
                    <i data-lucide="volume-1"></i>
                    <input type="range" min="0" max="100" value="${Math.round(window.SoundService.getVolume() * 100)}"
                           class="volume-slider" id="volumeSlider">
                    <span class="volume-value">${Math.round(window.SoundService.getVolume() * 100)}%</span>
                </div>
            </div>

            <!-- Presets -->
            <div class="sound-control-group">
                <label>Preset</label>
                <div class="preset-buttons">
                    <button class="preset-btn ${window.SoundService.getPreset() === 'minimal' ? 'active' : ''}" data-preset="minimal">
                        <i data-lucide="volume-1"></i>
                        <span>Minimal</span>
                    </button>
                    <button class="preset-btn ${window.SoundService.getPreset() === 'standard' ? 'active' : ''}" data-preset="standard">
                        <i data-lucide="volume-2"></i>
                        <span>Standard</span>
                    </button>
                    <button class="preset-btn ${window.SoundService.getPreset() === 'immersive' ? 'active' : ''}" data-preset="immersive">
                        <i data-lucide="volume"></i>
                        <span>Immersive</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(panel);

    // Position panel
    const rect = button.getBoundingClientRect();
    panel.style.top = `${rect.bottom + 8}px`;
    panel.style.right = `${window.innerWidth - rect.right}px`;

    // Initialize Lucide icons
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // Setup event listeners
    setupSoundPanelListeners(panel);
}

// Close sound panel
function closeSoundPanel() {
    const panel = document.querySelector('.sound-panel');
    if (panel) {
        panel.remove();
    }
}

// Setup sound panel event listeners
function setupSoundPanelListeners(panel) {
    // Quick mute
    const quickMute = panel.querySelector('#quickMute');
    if (quickMute) {
        quickMute.addEventListener('click', () => {
            const isMuted = window.SoundService.toggleMute();
            quickMute.querySelector('i').setAttribute('data-lucide', isMuted ? 'volume-x' : 'volume-2');
            quickMute.querySelector('span').textContent = isMuted ? 'Unmute' : 'Mute';
            updateSoundButton(document.getElementById('soundToggleBtn'), document.getElementById('soundIcon'));
            if (window.lucide) window.lucide.createIcons();
        });
    }

    // Volume slider
    const slider = panel.querySelector('#volumeSlider');
    const valueDisplay = panel.querySelector('.volume-value');
    if (slider && valueDisplay) {
        slider.addEventListener('input', (e) => {
            const volume = parseInt(e.target.value) / 100;
            window.SoundService.setVolume(volume);
            valueDisplay.textContent = `${e.target.value}%`;
        });

        // Test sound on release
        slider.addEventListener('change', () => {
            if (!window.SoundService.getMute()) {
                window.SoundService.play('click');
            }
        });
    }

    // Preset buttons
    const presetButtons = panel.querySelectorAll('.preset-btn');
    presetButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const preset = btn.dataset.preset;
            window.SoundService.applyPreset(preset);

            // Update active state
            presetButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update slider
            if (slider && valueDisplay) {
                const newVolume = Math.round(window.SoundService.getVolume() * 100);
                slider.value = newVolume;
                valueDisplay.textContent = `${newVolume}%`;
            }

            // Test sound
            if (!window.SoundService.getMute()) {
                window.SoundService.play('notification');
            }
        });
    });
}

// ============================================================================
// FULLSCREEN FUNCTIONS
// ============================================================================

/**
 * Toggle fullscreen mode
 */
function toggleFullscreen() {
    if (!document.fullscreenElement &&
        !document.webkitFullscreenElement &&
        !document.mozFullScreenElement &&
        !document.msFullscreenElement) {
        // Enter fullscreen
        enterFullscreen();
    } else {
        // Exit fullscreen
        exitFullscreen();
    }
}

/**
 * Enter fullscreen mode
 */
function enterFullscreen() {
    const elem = document.documentElement;
    
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) { // Safari
        elem.webkitRequestFullscreen();
    } else if (elem.mozRequestFullScreen) { // Firefox
        elem.mozRequestFullScreen();
    } else if (elem.msRequestFullscreen) { // IE/Edge
        elem.msRequestFullscreen();
    }
}

/**
 * Exit fullscreen mode
 */
function exitFullscreen() {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.webkitExitFullscreen) { // Safari
        document.webkitExitFullscreen();
    } else if (document.mozCancelFullScreen) { // Firefox
        document.mozCancelFullScreen();
    } else if (document.msExitFullscreen) { // IE/Edge
        document.msExitFullscreen();
    }
}

/**
 * Check if currently in fullscreen
 */
function isFullscreen() {
    return !!(document.fullscreenElement ||
              document.webkitFullscreenElement ||
              document.mozFullScreenElement ||
              document.msFullscreenElement);
}

/**
 * Update fullscreen icon based on current state
 */
function updateFullscreenIcon(icon) {
    if (isFullscreen()) {
        icon.setAttribute('data-lucide', 'minimize');
        icon.parentElement.title = 'Exit Fullscreen';
    } else {
        icon.setAttribute('data-lucide', 'maximize');
        icon.parentElement.title = 'Enter Fullscreen';
    }
    
    // Re-render Lucide icon
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

// Export functions for use in main app.js
if (typeof window !== 'undefined') {
    window.initTopNavRack = initTopNavRack;
    window.updateActiveNav = updateActiveNav;
    window.updateUserInfoNav = updateUserInfoNav;
    window.updateAppsCountBadge = updateAppsCountBadge;
    window.showSoundPanel = showSoundPanel;
    window.closeSoundPanel = closeSoundPanel;
}
