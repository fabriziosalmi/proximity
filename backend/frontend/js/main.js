/**
 * Proximity Application - Main Entry Point
 *
 * This is the main entry point for the Proximity application.
 * It bootstraps the application and initializes all components.
 */

// Import new modular components
import * as AppState from './state/appState.js';
import * as API from './services/api.js';
import * as DOM from './utils/dom.js';
import * as Notifications from './utils/notifications.js';
import * as Auth from './utils/auth.js';
import * as UI from './utils/ui.js';
import { SoundService } from './services/soundService.js';
import { handleOnboarding } from './onboarding.js';
import { initTooltips, refreshTooltips } from './utils/tooltips.js';

// Make modules available globally for transition period
// This allows the legacy code to work while we migrate
window.AppState = AppState;
window.API = API;
window.DOM = DOM;
window.Notifications = Notifications;
window.Auth = Auth;
window.UI = UI;
window.SoundService = SoundService;
window.initTooltips = initTooltips;
window.refreshTooltips = refreshTooltips;

// Initialize sound system
SoundService.init();

console.log('✅ Proximity modular system loaded');
console.log('📦 Available modules:', {
    AppState: 'State management',
    API: 'API service layer',
    DOM: 'DOM utilities',
    Notifications: 'Toast notifications',
    Auth: 'Authentication',
    UI: 'UI utilities and mode control'
});

/**
 * Enhanced initialization that includes onboarding flow.
 * This wraps the legacy init() function from app.js and adds
 * the first-run onboarding experience before it.
 */
async function initializeProximity() {
    console.log('🚀 Starting Proximity initialization...');

    // STEP 1: Handle onboarding (first run check)
    // This will either show the Power On screen (first run) or return immediately
    await handleOnboarding();

    // STEP 2: Continue with normal app initialization
    // The init() function from app.js handles authentication and UI setup
    if (typeof window.init === 'function') {
        console.log('✅ Onboarding complete - proceeding to app initialization');
        await window.init();

        // STEP 3: Initialize custom tooltip system after UI is rendered
        initTooltips();
    } else {
        console.error('❌ Legacy init() function not found in app.js');
    }
}

// Wait for DOM to be ready, then start initialization
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        UI.initUIMode();
        console.log(`🎯 Current mode: ${AppState.getProximityMode()}`);
        // Start the enhanced initialization
        initializeProximity();
    });
} else {
    UI.initUIMode();
    console.log(`🎯 Current mode: ${AppState.getProximityMode()}`);
    // Start the enhanced initialization
    initializeProximity();
}
