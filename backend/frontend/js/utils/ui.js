/**
 * UI Utilities
 *
 * Centralized UI control functions including dual-mode visibility.
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
