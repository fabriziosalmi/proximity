/**
 * UI Utilities
 *
 * Centralized UI control functions including dual-mode visibility,
 * loading overlays, and user menu management.
 */

import { getProximityMode, setProximityMode, initProximityMode } from '../state/appState.js';

/**
 * Update UI visibility based on proximity mode
 * This is the master function that controls AUTO/PRO mode visibility
 * @param {string} mode - 'AUTO' or 'PRO' (optional, reads from state if not provided)
 */
export function updateUIVisibility(mode = null) {
    // Get mode from parameter or state
    const currentMode = mode || getProximityMode();

    // Update body class to control CSS visibility
    if (currentMode === 'PRO') {
        document.body.classList.add('pro-mode');
    } else {
        document.body.classList.remove('pro-mode');
    }

    console.log(`🎨 UI Mode: ${currentMode}`);
}

/**
 * Switch proximity mode and update UI
 * @param {string} newMode - 'AUTO' or 'PRO'
 */
export function switchProximityMode(newMode) {
    // Validate mode
    if (newMode !== 'AUTO' && newMode !== 'PRO') {
        console.error('Invalid proximity mode:', newMode);
        return;
    }

    // Update state and localStorage
    setProximityMode(newMode);

    // Update UI visibility
    updateUIVisibility(newMode);

    // Dispatch custom event for other components to react
    window.dispatchEvent(new CustomEvent('proximityModeChanged', {
        detail: { mode: newMode }
    }));

    console.log(`✅ Switched to ${newMode} mode`);
}

/**
 * Show loading overlay with message
 * @param {string} text - Loading message (default: 'Loading...')
 */
export function showLoading(text = 'Loading...') {
    let loadingOverlay = document.getElementById('loadingOverlay');
    
    if (!loadingOverlay) {
        // Create loading overlay if it doesn't exist
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loadingOverlay';
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p class="loading-text">${text}</p>
            </div>
        `;
        document.body.appendChild(loadingOverlay);
    } else {
        // Update text if overlay already exists
        const textElement = loadingOverlay.querySelector('.loading-text');
        if (textElement) {
            textElement.textContent = text;
        }
    }
    
    loadingOverlay.classList.add('show');
}

/**
 * Hide loading overlay
 */
export function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('show');
    }
}

/**
 * Toggle user menu visibility
 */
export function toggleUserMenu() {
    const userMenu = document.querySelector('.user-menu-dropdown');
    if (userMenu) {
        userMenu.classList.toggle('show');
    }
    
    // Close menu when clicking outside
    if (userMenu && userMenu.classList.contains('show')) {
        const closeMenu = (e) => {
            if (!e.target.closest('.user-menu')) {
                userMenu.classList.remove('show');
                document.removeEventListener('click', closeMenu);
            }
        };
        setTimeout(() => document.addEventListener('click', closeMenu), 0);
    }
}

/**
 * Initialize UI mode on page load
 * Should be called during app initialization
 */
export function initUIMode() {
    // Initialize mode from localStorage
    initProximityMode();

    // Apply initial visibility
    updateUIVisibility();
}

/**
 * Check if current mode is PRO
 * @returns {boolean} True if PRO mode
 */
export function isProMode() {
    return getProximityMode() === 'PRO';
}

/**
 * Check if current mode is AUTO
 * @returns {boolean} True if AUTO mode
 */
export function isAutoMode() {
    return getProximityMode() === 'AUTO';
}
