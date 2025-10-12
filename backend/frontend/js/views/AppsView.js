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

        // CRITICAL FIX: Reload deployed apps from API before rendering
        // This ensures we always show fresh data when navigating to Apps view
        if (typeof window.loadDeployedApps === 'function') {
            console.log('🔄 Reloading deployed apps from API...');
            await window.loadDeployedApps();
        } else {
            console.warn('⚠️  window.loadDeployedApps not available - using cached app data');
        }

        // MOVED FROM app.js: renderAppsView() function
        this.renderAppsView(container, state);

        // MOVED FROM app.js: Start CPU polling using imported function
        this._cpuPollingInterval = startCPUPolling(state);

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
                    <button class="btn btn-primary" onclick="showView('catalog')">Browse Catalog</button>
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
