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
import * as Formatters from './utils/formatters.js';
import * as Icons from './utils/icons.js';
import * as Clipboard from './utils/clipboard.js';
import { initSidebarToggle } from './utils/sidebar.js';
import { refreshInfrastructure, restartAppliance, viewApplianceLogs, testNAT } from './utils/settingsHelpers.js';
import { SoundService } from './services/soundService.js';
import { handleOnboarding } from './onboarding.js';
import { initTooltips, refreshTooltips } from './utils/tooltips.js';
import { showAuthModal, closeAuthModal, handleLogout, renderAuthTabs, switchAuthTab, renderRegisterForm, renderLoginForm, handleRegisterSubmit, handleLoginSubmit, initializeAuthenticatedSession, toggleUserMenu } from './components/auth-ui.js';
import { showDeployModal } from './modals/DeployModal.js';
import { showBackupModal, hideBackupModal, createBackup, refreshBackups } from './modals/BackupModal.js';
import { openCanvas, closeCanvas, toggleCanvasHeader, refreshCanvas, openInNewTab } from './modals/CanvasModal.js';
import { showAppConsole, cleanupTerminal, closeConsoleModal } from './modals/ConsoleModal.js';
import { showMonitoringModal, startMonitoringPolling, stopMonitoringPolling, formatUptime } from './modals/MonitoringModal.js';
import { showCloneModal } from './modals/CloneModal.js';
import { showPromptModal } from './modals/PromptModal.js';
import { showEditConfigModal, closeEditConfigModal } from './modals/EditConfigModal.js';
import { showUpdateModal } from './modals/UpdateModal.js';
import { controlApp, deleteApp, restartApp, showAppDetails, showDeletionProgress, updateDeletionProgress, hideDeletionProgress, showAppLogs, showAppVolumes } from './services/appOperations.js';

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

    console.log('✅ Router initialized with 6 views');
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
 * Central event delegation handler
 * Handles ALL user interactions via event delegation
 */
function initEventDelegation() {
    console.log('🎯 Initializing event delegation system...');

    // Single click handler for the entire application
    document.body.addEventListener('click', (event) => {
        const target = event.target;
        console.log('🖱️ Click detected on:', target.tagName, target.className);

        // --- 1. NAVIGATION: Handle view navigation ---
        const navLink = target.closest('[data-view]:not([data-action])');
        if (navLink) {
            event.preventDefault();
            event.stopPropagation();
            const viewName = navLink.dataset.view;
            console.log(`📍 Navigation to: ${viewName}`);
            
            // Use router for navigation
            router.navigateTo(viewName);
            return;
        }

        // --- 2. MODALS: Close buttons ---
        const modalClose = target.closest('.modal-close');
        if (modalClose) {
            const modal = modalClose.closest('.modal');
            if (modal) {
                const modalId = modal.id;
                console.log(`❌ Closing modal: ${modalId}`);
                
                if (modalId === 'authModal') {
                    closeAuthModal();
                } else if (modalId === 'backupModal') {
                    hideBackupModal();
                } else if (modalId === 'deployModal') {
                    if (window.closeModal) window.closeModal();
                } else {
                    modal.style.display = 'none';
                }
            }
            return;
        }

        // --- 3. BACKUP ACTIONS ---
        const backupAction = target.closest('[data-action="create-backup"]');
        if (backupAction) {
            console.log('📦 Creating backup...');
            createBackup();
            return;
        }

        const refreshBackupsBtn = target.closest('[data-action="refresh-backups"]');
        if (refreshBackupsBtn) {
            console.log('🔄 Refreshing backups...');
            refreshBackups();
            return;
        }

        // --- 4. CANVAS ACTIONS ---
        const canvasToggle = target.closest('[data-action="toggle-canvas-header"]');
        if (canvasToggle) {
            toggleCanvasHeader();
            return;
        }

        const canvasNewTab = target.closest('[data-action="canvas-new-tab"]');
        if (canvasNewTab) {
            openInNewTab();
            return;
        }

        const canvasRefresh = target.closest('[data-action="canvas-refresh"]');
        if (canvasRefresh) {
            refreshCanvas();
            return;
        }

        const canvasClose = target.closest('[data-action="canvas-close"]');
        if (canvasClose) {
            closeCanvas();
            return;
        }

        // --- 5. LOGOUT ---
        const logoutBtn = target.closest('[data-action="logout"]');
        if (logoutBtn) {
            event.preventDefault();
            handleLogout(event);
            return;
        }

        // --- 6. GENERIC VIEW SWITCH (buttons with data-view) ---
        const viewButton = target.closest('button[data-view]');
        if (viewButton) {
            const viewName = viewButton.dataset.view;
            console.log(`🔘 Button navigation to: ${viewName}`);
            router.navigateTo(viewName);
            return;
        }
    });

    console.log('✅ Event delegation system initialized');
}

/**
 * Wait for Lucide library to be loaded
 * @returns {Promise<void>}
 */
function waitForLucide() {
    return new Promise((resolve) => {
        if (typeof lucide !== 'undefined') {
            resolve();
        } else {
            const checkInterval = setInterval(() => {
                if (typeof lucide !== 'undefined') {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 50);
            
            // Timeout after 5 seconds
            setTimeout(() => {
                clearInterval(checkInterval);
                console.warn('⚠️  Lucide library not loaded after 5 seconds');
                resolve();
            }, 5000);
        }
    });
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

    // STEP 3: Initialize sidebar toggle
    initSidebarToggle();
    console.log('✅ Sidebar initialized');

    // STEP 3.5: Initialize Top Navigation Rack
    if (typeof initTopNavRack !== 'undefined') {
        initTopNavRack();
        console.log('✅ Top Navigation Rack initialized');
    }

    // STEP 4: Initialize router and views
    initRouter();

    // STEP 5: Subscribe render function to state changes
    AppState.subscribe(render);
    console.log('✅ Render function subscribed to state changes');

    // STEP 6: Initialize event delegation (NEW!)
    initEventDelegation();

    // STEP 7: Initialize authentication
    const isAuthenticated = await initAuth();

    // STEP 8: Initialize tooltips
    initTooltips();

    // STEP 9: Initialize Lucide icons (CRITICAL)
    // Wait for Lucide library to be fully loaded before initializing
    await waitForLucide();
    Icons.initLucideIcons();
    console.log('✅ Lucide icons initialized');

    // STEP 10: Initial render
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

// ============================================================================
// BACKWARD COMPATIBILITY: Expose functions to window for legacy code
// ============================================================================
// TODO: Remove these once all legacy onclick attributes are removed from HTML

// Navigation functions
window.showView = (viewName) => router.navigateTo(viewName);
window.navigateToApps = () => router.navigateTo('apps');
window.navigateToCatalog = () => router.navigateTo('catalog');
window.navigateToSettings = () => router.navigateTo('settings');
window.showUILabSubmenu = () => {
    if (window.showSubmenu) window.showSubmenu();
};

// Event delegation
window.setupEventListeners = initEventDelegation; // Alias for backward compatibility

// Modal functions
window.closeModal = () => {
    const modal = document.getElementById('deployModal');
    if (modal) modal.style.display = 'none';
};
window.showAuthModal = showAuthModal;
window.closeAuthModal = closeAuthModal;
window.handleLogout = handleLogout;
window.renderAuthTabs = renderAuthTabs;
window.switchAuthTab = switchAuthTab;
window.renderRegisterForm = renderRegisterForm;
window.renderLoginForm = renderLoginForm;
window.handleRegisterSubmit = handleRegisterSubmit;
window.handleLoginSubmit = handleLoginSubmit;
window.initializeAuthenticatedSession = initializeAuthenticatedSession;
window.toggleUserMenu = toggleUserMenu;
window.showDeployModal = showDeployModal;
window.hideBackupModal = hideBackupModal;
window.createBackup = createBackup;
window.refreshBackups = refreshBackups;

// Canvas functions
window.toggleCanvasHeader = toggleCanvasHeader;
window.openInNewTab = openInNewTab;
window.refreshCanvas = refreshCanvas;
window.closeCanvas = closeCanvas;

// App operations functions
window.controlApp = controlApp;
window.deleteApp = deleteApp;
window.restartApp = restartApp;
window.showAppDetails = showAppDetails;
window.showDeletionProgress = showDeletionProgress;
window.updateDeletionProgress = updateDeletionProgress;
window.hideDeletionProgress = hideDeletionProgress;
window.showAppLogs = showAppLogs;
window.showAppVolumes = showAppVolumes;

// Utility functions (NEW!)
window.initLucideIcons = Icons.initLucideIcons;
window.getAppIcon = Icons.getAppIcon;
window.formatDate = Formatters.formatDate;
window.formatBytes = Formatters.formatBytes;
window.formatSize = Formatters.formatSize;
window.formatUptime = Formatters.formatUptime;
window.showLoading = UI.showLoading;
window.hideLoading = UI.hideLoading;
window.copyToClipboard = Clipboard.copyToClipboard;

// Infrastructure management functions (called from NodesView onclick handlers)
window.refreshInfrastructure = refreshInfrastructure;
window.restartAppliance = restartAppliance;
window.viewApplianceLogs = viewApplianceLogs;
window.testNAT = testNAT;

// Expose modules for advanced usage
window.Formatters = Formatters;
window.Icons = Icons;
window.UI = UI;
window.Clipboard = Clipboard;
window.Auth = Auth; // CRITICAL: Expose Auth for E2E tests and conftest
window.API = API;   // Also expose API for testing

console.log('⚠️  Legacy window functions exposed for backward compatibility');
