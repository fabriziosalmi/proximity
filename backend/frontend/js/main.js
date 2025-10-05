/**
 * Proximity Application - Main Entry Point
 *
 * This is the main entry point for the Proximity application.
 * It bootstraps the application and initializes all components.
 */

// Import legacy app.js as a module (temporary bridge)
// We'll gradually replace this with proper ES6 modules
import '../app.js';

// Import new modular components
import * as AppState from './state/appState.js';
import * as API from './services/api.js';
import * as DOM from './utils/dom.js';
import * as Notifications from './utils/notifications.js';
import * as Auth from './utils/auth.js';

// Make modules available globally for transition period
// This allows the legacy code to work while we migrate
window.AppState = AppState;
window.API = API;
window.DOM = DOM;
window.Notifications = Notifications;
window.Auth = Auth;

console.log('✅ Proximity modular system loaded');
console.log('📦 Available modules:', {
    AppState: 'State management',
    API: 'API service layer',
    DOM: 'DOM utilities',
    Notifications: 'Toast notifications',
    Auth: 'Authentication'
});
