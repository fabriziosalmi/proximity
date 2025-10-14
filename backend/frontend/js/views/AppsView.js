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
    mount(container, state) {
        // Store state reference
        this._state = state;

        // ALWAYS RELOAD: No caching for now to avoid inconsistencies
        // Show loading state immediately
        container.innerHTML = `
            <div class="loading-state">
                <div class="loading-spinner"></div>
                <p>Loading applications...</p>
            </div>
        `;

        // Load async WITHOUT blocking mount
        loadDeployedApps(true).then(() => {
            // loadDeployedApps(true) already updates global state via setState()
            // So we just need to get fresh state
            this._state = getState();

            // NOW render with data
            this.renderAppsView(container, this._state);

            // Start CPU polling AFTER render
            this._cpuPollingInterval = startCPUPolling(this._state);

            // Update apps count badge after loading apps
            if (typeof window.updateAppsCount === 'function') {
                window.updateAppsCount();
            }
        }).catch(error => {
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
        });

        // Call parent mount (SYNCHRONOUS!)
        return super.mount(container, state);
    }

    /**
     * MOVED FROM app.js (line 1192): renderAppsView()
     * Renders the apps view HTML structure and app cards
     * @param {HTMLElement} container - Container element
     * @param {Object} state - Application state
     */
    renderAppsView(container, state) {
        const ENABLE_PERF_LOGS = false; // Set to true for debugging
        container.classList.remove('has-sub-nav'); // Remove old sub-nav class

        // Search bar is now in the submenu - no need for it here anymore
        const content = `
            <div class="apps-grid deployed" id="allAppsGrid"></div>
        `;

        container.innerHTML = content;

        // Render app cards using template cloning (existing pattern)
        const grid = document.getElementById('allAppsGrid');

        if (!state.deployedApps || state.deployedApps.length === 0) {
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
            if (ENABLE_PERF_LOGS) console.time('⏱️ Render Cards Loop');

            // PERFORMANCE OPTIMIZATION: Batch render all cards using DocumentFragment
            // This reduces reflows from N to 1
            const fragment = document.createDocumentFragment();
            const tempContainer = document.createElement('div');

            for (const app of state.deployedApps) {
                renderAppCard(app, tempContainer, true);
            }
            if (ENABLE_PERF_LOGS) console.timeEnd('⏱️ Render Cards Loop');

            if (ENABLE_PERF_LOGS) console.time('⏱️ DOM Fragment Insert');
            // Move all rendered cards to fragment
            while (tempContainer.firstChild) {
                fragment.appendChild(tempContainer.firstChild);
            }

            // Single DOM insertion (much faster!)
            grid.appendChild(fragment);
            if (ENABLE_PERF_LOGS) console.timeEnd('⏱️ DOM Fragment Insert');
        }

        // PERFORMANCE OPTIMIZATION: Event delegation at grid level
        // Instead of attaching listeners to each card, we use a single delegated listener
        if (ENABLE_PERF_LOGS) console.time('⏱️ Setup Event Delegation');
        this._setupEventDelegation(grid, state);
        if (ENABLE_PERF_LOGS) console.timeEnd('⏱️ Setup Event Delegation');

        // PERFORMANCE CRITICAL: Defer icons/tooltips to next frame
        // This makes rendering feel instant by not blocking the main thread
        requestAnimationFrame(() => {
            // Initialize Lucide icons ONLY in the grid
            if (typeof window.initLucideIcons === 'function') {
                window.initLucideIcons(grid);
            }

            // Refresh tooltips ONLY in the grid
            if (typeof window.refreshTooltips === 'function') {
                window.refreshTooltips(grid);
            }
        });
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
    }

    /**
     * Unmount apps view and cleanup
     */
    unmount() {
        // Stop CPU polling by clearing the interval
        if (this._cpuPollingInterval) {
            clearInterval(this._cpuPollingInterval);
            this._cpuPollingInterval = null;
        }

        // Remove delegated event listener
        const grid = document.getElementById('allAppsGrid');
        if (grid && this._gridClickHandler) {
            grid.removeEventListener('click', this._gridClickHandler);
            this._gridClickHandler = null;
        }

        super.unmount();
    }
}

// Create singleton instance
export const appsView = new AppsView();
