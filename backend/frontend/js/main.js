/**
 * Proximity Application - Main Entry Point
 *
 * This is the main entry point for the Proximity application.
 * It bootstraps the application and initializes all components.
 */

// Import modular components
import * as AppState from './state/appState.js';
import * as API from './services/api.js';
import * as DOM from './utils/dom.js';
import * as Notifications from './utils/notifications.js';
import * as Auth from './utils/auth.js';
import * as UI from './utils/ui.js';
import { SoundService } from './services/soundService.js';
import { handleOnboarding } from './onboarding.js';
import { initTooltips, refreshTooltips } from './utils/tooltips.js';
import { showAuthModal, closeAuthModal, handleLogout } from './components/auth-ui.js';
import { showDeployModal } from './modals/DeployModal.js';
import { showBackupModal, hideBackupModal, createBackup, refreshBackups } from './modals/BackupModal.js';
import { openCanvas, closeCanvas, toggleCanvasHeader, refreshCanvas, openInNewTab } from './modals/CanvasModal.js';
import { showAppConsole, cleanupTerminal, closeConsoleModal } from './modals/ConsoleModal.js';
import { showMonitoringModal, startMonitoringPolling, stopMonitoringPolling, formatUptime } from './modals/MonitoringModal.js';
import { showCloneModal } from './modals/CloneModal.js';
import { showPromptModal } from './modals/PromptModal.js';

// Import lifecycle management system
import { router } from './core/Router.js';
import { dashboardView } from './views/DashboardView.js';
import { appsView } from './views/AppsView.js';
import { catalogView } from './views/CatalogView.js';
import { settingsView } from './views/SettingsView.js';
import { nodesView } from './views/NodesView.js';
import { monitoringView } from './views/MonitoringView.js';

// Initialize sound system
SoundService.init();

console.log('✅ Proximity modular system loaded');

/**
 * Initialize the lifecycle management system (Router + Views)
 */
function initRouter() {
    console.log('🔄 Initializing Router...');

    // Register all views with the router
    router.registerViews({
        'dashboard': dashboardView,
        'apps': appsView,
        'catalog': catalogView,
        'settings': settingsView,
        'nodes': nodesView,
        'monitoring': monitoringView
    });

    console.log('✅ Router initialized with views:', Object.keys(router.views));
}

/**
 * Master render function - called on every state change
 * This is the heart of the reactive system
 */
function render(state) {
    console.log('🎨 Render triggered - Current view:', state.currentView);

    // Navigate to the current view via router
    if (state.currentView) {
        router.navigateTo(state.currentView, state);
    }
}

/**
 * Check authentication and initialize user session
 */
async function initAuth() {
    console.log('🔐 Checking authentication...');

    const token = Auth.getToken();
    if (!token) {
        console.log('❌ No token found - user not authenticated');
        AppState.setState({
            isAuthenticated: false,
            currentUser: null
        });
        // Show auth modal
        showAuthModal();
        return false;
    }

    try {
        // Verify token and get user info
        const userInfo = await API.fetchUserInfo();
        console.log('✅ User authenticated:', userInfo.username);

        AppState.setState({
            isAuthenticated: true,
            currentUser: userInfo
        });

        return true;
    } catch (error) {
        console.error('❌ Authentication failed:', error);
        Auth.clearToken();
        AppState.setState({
            isAuthenticated: false,
            currentUser: null
        });

        // Show auth modal
        showAuthModal();

        return false;
    }
}

/**
 * Main application initialization
 * This is the GOD orchestrator that bootstraps everything
 */
async function initializeApp() {
    console.log('🚀 Initializing Proximity Application...');

    // STEP 1: Handle onboarding (first run)
    await handleOnboarding();

    // STEP 2: Initialize UI mode
    UI.initUIMode();
    AppState.initProximityMode();
    console.log(`🎯 Mode: ${AppState.getProximityMode()}`);

    // STEP 3: Initialize router and views
    initRouter();

    // STEP 4: Subscribe render function to state changes
    AppState.subscribe(render);
    console.log('✅ Render function subscribed to state changes');

    // STEP 5: Initialize authentication
    const isAuthenticated = await initAuth();

    // STEP 6: Initialize tooltips
    initTooltips();

    // STEP 7: Initial render
    if (isAuthenticated) {
        // Set initial view to dashboard
        AppState.setState('currentView', 'dashboard');
    }

    console.log('✅ Proximity Application initialized successfully');
}

// Bootstrap the application
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}
