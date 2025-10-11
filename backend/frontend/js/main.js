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

// Import new lifecycle management system
import { router } from './core/Router.js';
import { dashboardView } from './views/DashboardView.js';
import { appsView } from './views/AppsView.js';
import { catalogView } from './views/CatalogView.js';
import { settingsView } from './views/SettingsView.js';
import { nodesView } from './views/NodesView.js';
import { monitoringView } from './views/MonitoringView.js';

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
 * Initialize the new lifecycle management system
 */
function initLifecycleSystem() {
    console.log('🔄 Initializing Component Lifecycle Management System...');

    // Register all views with the router
    router.registerViews({
        'dashboard': dashboardView,
        'apps': appsView,
        'catalog': catalogView,
        'settings': settingsView,
        'nodes': nodesView,
        'monitoring': monitoringView
    });

    // Expose router globally for navigation
    window.ProximityRouter = router;

    console.log('✅ Lifecycle Management System initialized');
    console.log('📋 Registered views:', ['dashboard', 'apps', 'catalog', 'settings', 'nodes', 'monitoring']);
}

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

    // STEP 2: Initialize the lifecycle management system
    initLifecycleSystem();

    // STEP 3: Continue with normal app initialization
    // The init() function from app.js handles authentication and UI setup
    if (typeof window.init === 'function') {
        console.log('✅ Onboarding complete - proceeding to app initialization');
        await window.init();

        // STEP 4: Initialize custom tooltip system after UI is rendered
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
