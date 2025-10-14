/**
 * Apps View Component
 *
 * Displays all deployed applications with real-time CPU/RAM metrics.
 * THIS IS THE TRUE MIGRATION: Code moved from app.js, not recreated.
 *
 * @module views/AppsView
 */

import { Component } from '../core/Component.js';
import { renderAppCard, startCPUPolling } from '../components/app-card.js';
import { authFetch, API_BASE } from '../services/api.js';
import { loadDeployedApps } from '../services/dataService.js';
import { getState } from '../state/appState.js';

export class AppsView extends Component {
    constructor() {
        super();
        this._cpuPollingInterval = null;
        this._state = null;
    }

    /**
     * Mount the apps view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    async mount(container, state) {
        console.time('⏱️ AppsView Total Mount Time');
        console.log('✅ Mounting Apps View');

        // Store state reference
        this._state = state;

        // OPTIMIZATION: Only reload if state.deployedApps is empty or stale
        // This prevents unnecessary API calls on every navigation
        const needsReload = !state.deployedApps || state.deployedApps.length === 0;

        if (needsReload) {
            console.time('⏱️ API loadDeployedApps');
            console.log('🔄 Loading deployed apps from API (first load)...');

            try {
                const deployedApps = await loadDeployedApps(false);  // Don't trigger setState
                console.timeEnd('⏱️ API loadDeployedApps');
                state.deployedApps = deployedApps;
                this._state = state;
            } catch (error) {
                console.timeEnd('⏱️ API loadDeployedApps');
                console.error('❌ Failed to load apps:', error);

                // Show error state
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">⚠️</div>
                        <h2>Cannot Load Applications</h2>
                        <p>Unable to connect to the backend server.</p>
                        <p class="text-muted">Please make sure the backend is running.</p>
                        <button class="btn btn-primary" onclick="window.location.reload()">
                            <i data-lucide="refresh-cw"></i>
                            Retry
                        </button>
                    </div>
                `;

                if (window.lucide) {
                    window.lucide.createIcons();
                }

                console.timeEnd('⏱️ AppsView Total Mount Time');
                return super.mount(container, state);
            }
        } else {
            console.log(`⚡ Using cached apps (${state.deployedApps.length} apps) - no API call needed`);
        }

        // MOVED FROM app.js: renderAppsView() function
        console.time('⏱️ renderAppsView');
        this.renderAppsView(container, state);
        console.timeEnd('⏱️ renderAppsView');

        // MOVED FROM app.js: Start CPU polling using imported function
        this._cpuPollingInterval = startCPUPolling(state);

        console.timeEnd('⏱️ AppsView Total Mount Time');
        console.log('✅ Apps View fully loaded and rendered');

        // Call parent mount
        return super.mount(container, state);
    }

    /**
     * MOVED FROM app.js (line 1192): renderAppsView()
     * Renders the apps view HTML structure and app cards
     * @param {HTMLElement} container - Container element
     * @param {Object} state - Application state
     */
    renderAppsView(container, state) {
        container.classList.remove('has-sub-nav'); // Remove old sub-nav class

        console.log(`📱 renderAppsView() - deployedApps count: ${state.deployedApps?.length || 0}`);
        console.log(`📱 deployedApps:`, state.deployedApps);

        // Search bar is now in the submenu - no need for it here anymore
        const content = `
            <div class="apps-grid deployed" id="allAppsGrid"></div>
        `;

        container.innerHTML = content;

        // Render app cards using template cloning (existing pattern)
        const grid = document.getElementById('allAppsGrid');

        if (!state.deployedApps || state.deployedApps.length === 0) {
            console.log('📱 No apps to display - showing empty state');
            // Show empty state
            grid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📦</div>
                    <h3 class="empty-title">No applications deployed</h3>
                    <p class="empty-message">Start by deploying an application from the catalog.</p>
                    <button class="btn btn-primary" onclick="window.router.navigateTo('catalog')">Browse Catalog</button>
                </div>
            `;
        } else {
            console.log(`📱 Rendering ${state.deployedApps.length} app cards`);
            console.time('⏱️ Render Cards Loop');

            // PERFORMANCE OPTIMIZATION: Batch render all cards using DocumentFragment
            // This reduces reflows from N to 1
            const fragment = document.createDocumentFragment();
            const tempContainer = document.createElement('div');

            for (const app of state.deployedApps) {
                renderAppCard(app, tempContainer, true);
            }
            console.timeEnd('⏱️ Render Cards Loop');

            console.time('⏱️ DOM Fragment Insert');
            // Move all rendered cards to fragment
            while (tempContainer.firstChild) {
                fragment.appendChild(tempContainer.firstChild);
            }

            // Single DOM insertion (much faster!)
            grid.appendChild(fragment);
            console.timeEnd('⏱️ DOM Fragment Insert');
            console.log(`⚡ Batch rendered ${state.deployedApps.length} cards in single operation`);
        }

        // PERFORMANCE OPTIMIZATION: Event delegation at grid level
        // Instead of attaching listeners to each card, we use a single delegated listener
        console.time('⏱️ Setup Event Delegation');
        this._setupEventDelegation(grid, state);
        console.timeEnd('⏱️ Setup Event Delegation');

        // PERFORMANCE CRITICAL: Pass container to scope icon/tooltip initialization
        // This scans ONLY the apps grid instead of the entire document (100x faster!)

        // Initialize Lucide icons ONLY in the grid
        if (typeof window.initLucideIcons === 'function') {
            window.initLucideIcons(grid);  // Scoped to grid only!
        }

        // Refresh tooltips ONLY in the grid
        if (typeof window.refreshTooltips === 'function') {
            window.refreshTooltips(grid);  // Scoped to grid only!
        }
    }

    /**
     * Setup event delegation for all app cards (PERFORMANCE CRITICAL)
     * Single listener handles all cards instead of N listeners
     * @param {HTMLElement} grid - Apps grid container
     * @param {Object} state - Application state
     */
    _setupEventDelegation(grid, state) {
        // Remove any existing delegated listener
        if (this._gridClickHandler) {
            grid.removeEventListener('click', this._gridClickHandler);
        }

        // Create new handler
        this._gridClickHandler = (e) => {
            const target = e.target;

            // Find closest action button or card
            const actionBtn = target.closest('.action-icon');
            const card = target.closest('.app-card');

            if (!card) return;

            // Get app data from card hostname attribute
            const hostname = card.getAttribute('data-hostname');
            if (!hostname) return;

            const app = state.deployedApps.find(a => a.hostname === hostname);
            if (!app) return;

            const isRunning = app.status === 'running';
            const appUrl = (app.url && app.url !== 'None' && app.url !== 'null') ? app.url : null;

            // Handle action button clicks
            if (actionBtn) {
                e.stopPropagation();
                const action = actionBtn.dataset.action;

                // Check if button is disabled
                if (actionBtn.classList.contains('disabled') || actionBtn.hasAttribute('disabled')) {
                    return;
                }

                // Execute action
                switch (action) {
                    case 'toggle-status':
                        window.controlApp(app.id, isRunning ? 'stop' : 'start');
                        break;
                    case 'open-external':
                        if (appUrl) window.open(appUrl, '_blank');
                        break;
                    case 'view-logs':
                        window.showAppLogs(app.id, app.hostname);
                        break;
                    case 'console':
                        window.showAppConsole(app.id, app.hostname);
                        break;
                    case 'backups':
                        window.showBackupModal(app.id);
                        break;
                    case 'update':
                        window.showUpdateModal(app.id);
                        break;
                    case 'volumes':
                        window.showAppVolumes(app.id);
                        break;
                    case 'monitoring':
                        window.showMonitoringModal(app.id, app.name);
                        break;
                    case 'canvas':
                        window.openCanvas({
                            id: app.id,
                            name: app.name,
                            hostname: app.hostname,
                            iframe_url: appUrl || app.url,
                            url: appUrl || app.url,
                            status: app.status
                        });
                        break;
                    case 'restart':
                        window.controlApp(app.id, isRunning ? 'restart' : 'start');
                        break;
                    case 'clone':
                        window.showCloneModal(app.id, app.name);
                        break;
                    case 'edit-config':
                        window.showEditConfigModal(app.id, app.name);
                        break;
                    case 'delete':
                        window.confirmDeleteApp(app.id, app.name);
                        break;
                }
                return;
            }

            // Handle card click (open canvas if running and has URL)
            if (!target.closest('.connection-link') && isRunning && appUrl) {
                window.openCanvas({
                    id: app.id,
                    name: app.name,
                    hostname: app.hostname,
                    iframe_url: appUrl,
                    url: appUrl,
                    status: app.status
                });
            }
        };

        // Attach single delegated listener
        grid.addEventListener('click', this._gridClickHandler);
        console.log('⚡ Event delegation setup complete - single listener handles all cards');
    }

    /**
     * Unmount apps view and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Apps View');

        // Stop CPU polling by clearing the interval
        if (this._cpuPollingInterval) {
            console.log('⏹️ Stopping CPU usage polling...');
            clearInterval(this._cpuPollingInterval);
            this._cpuPollingInterval = null;
        }

        // Remove delegated event listener
        const grid = document.getElementById('allAppsGrid');
        if (grid && this._gridClickHandler) {
            grid.removeEventListener('click', this._gridClickHandler);
            this._gridClickHandler = null;
            console.log('⏹️ Event delegation removed');
        }

        super.unmount();
    }
}

// Create singleton instance
export const appsView = new AppsView();
