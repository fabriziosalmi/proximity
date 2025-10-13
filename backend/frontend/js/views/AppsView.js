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
        console.log('✅ Mounting Apps View');

        // Store state reference
        this._state = state;

        // Mark container as loading
        container.setAttribute('data-loading', 'true');

        // CRITICAL FIX: Reload deployed apps from API before rendering
        // Don't update global state to avoid re-render during mount
        console.log('🔄 Reloading deployed apps from API...');
        
        try {
            const deployedApps = await loadDeployedApps(false);  // Don't trigger setState
            
            // Update local state copy with fresh data
            state.deployedApps = deployedApps;
            this._state = state;

            // MOVED FROM app.js: renderAppsView() function
            this.renderAppsView(container, state);

            // MOVED FROM app.js: Start CPU polling using imported function
            this._cpuPollingInterval = startCPUPolling(state);
            
            // Mark as fully loaded
            container.setAttribute('data-loading', 'false');
            container.setAttribute('data-loaded', 'true');
            console.log('✅ Apps View fully loaded and rendered');
        } catch (error) {
            console.error('❌ Failed to load apps:', error);
            
            // Mark as failed
            container.setAttribute('data-loading', 'false');
            container.setAttribute('data-loaded', 'error');
            
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
            
            // Initialize icons for the retry button
            if (window.lucide) {
                window.lucide.createIcons();
            }
        }

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
            // Render each app card using imported renderAppCard function
            for (const app of state.deployedApps) {
                renderAppCard(app, grid, true);
            }
        }

        // Initialize Lucide icons
        if (typeof window.initLucideIcons === 'function') {
            window.initLucideIcons();
        }

        // Refresh tooltips after rendering new content
        if (typeof window.refreshTooltips === 'function') {
            window.refreshTooltips();
        }
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
        super.unmount();
    }
}

// Create singleton instance
export const appsView = new AppsView();
