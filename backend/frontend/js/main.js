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

// Make modules available globally for transition period
// This allows the legacy code to work while we migrate
window.AppState = AppState;
window.API = API;
window.DOM = DOM;
window.Notifications = Notifications;
window.Auth = Auth;
window.UI = UI;

console.log('✅ Proximity modular system loaded');
console.log('📦 Available modules:', {
    AppState: 'State management',
    API: 'API service layer',
    DOM: 'DOM utilities',
    Notifications: 'Toast notifications',
    Auth: 'Authentication',
    UI: 'UI utilities and mode control'
});

// Wait for DOM to be ready, then initialize UI mode
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        UI.initUIMode();
        console.log(`🎯 Current mode: ${AppState.getProximityMode()}`);
    });
} else {
    UI.initUIMode();
    console.log(`🎯 Current mode: ${AppState.getProximityMode()}`);
}
