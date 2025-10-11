/**
 * Dashboard View Component
 *
 * Displays the main dashboard with hero section and quick apps.
 * THIS IS THE TRUE MIGRATION: Code moved from app.js, not recreated.
 *
 * @module views/DashboardView
 */

import { Component } from '../core/Component.js';

export class DashboardView extends Component {
    constructor() {
        super();
        this._refreshInterval = null;
    }

    /**
     * Mount the dashboard view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    mount(container, state) {
        console.log('✅ Mounting Dashboard View');

        // Dashboard HTML is already in index.html (hero section)
        // We just update the dynamic parts

        // MOVED FROM app.js: Update hero stats and recent apps
        this.updateHeroStats();
        this.updateRecentApps();

        // Optional: Auto-refresh dashboard every 30 seconds
        this._refreshInterval = this.trackInterval(() => {
            this.updateHeroStats();
            this.updateRecentApps();
        }, 30000);

        // Call parent mount
        return super.mount(container, state);
    }

    /**
     * MOVED FROM app.js (line 406): updateHeroStats()
     * Update hero section stats (apps count, nodes count, containers count)
     */
    updateHeroStats() {
        // Update hero section stats
        const heroAppsCount = document.getElementById('heroAppsCount');
        const heroNodesCount = document.getElementById('heroNodesCount');
        const heroContainersCount = document.getElementById('heroContainersCount');

        if (heroAppsCount) {
            const totalApps = window.state.deployedApps.length;
            heroAppsCount.textContent = totalApps;
        }

        if (heroNodesCount) {
            const activeNodes = window.state.nodes.filter(n => n.status === 'online').length;
            heroNodesCount.textContent = activeNodes;
        }

        if (heroContainersCount) {
            const runningContainers = window.state.deployedApps.filter(a => a.status === 'running').length;
            heroContainersCount.textContent = runningContainers;
        }
    }

    /**
     * MOVED FROM app.js (line 457): updateRecentApps()
     * Update quick apps grid in hero section
     */
    updateRecentApps() {
        console.log('📱 updateRecentApps() called');
        const container = document.getElementById('quickApps');

        if (!container) {
            console.warn('⚠️  quickApps container not found in DOM');
            return;
        }

        console.log(`✓ quickApps container found, deployedApps count: ${window.state.deployedApps.length}`);

        if (window.state.deployedApps.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i data-lucide="package" style="width: 48px; height: 48px;"></i>
                    </div>
                    <h3 class="empty-title">No applications yet</h3>
                    <p class="empty-message">Deploy your first application from the catalog to get started.</p>
                    <button class="btn btn-primary" onclick="showView('catalog')">Browse Catalog</button>
                </div>
            `;
            if (typeof window.initLucideIcons === 'function') {
                window.initLucideIcons();
            }
            return;
        }

        // Show all apps as quick access icons
        container.innerHTML = window.state.deployedApps.map(app => {
            const isRunning = app.status === 'running';
            const appUrl = (app.url && app.url !== 'None' && app.url !== 'null') ? app.url : null;

            // Get icon - uses global getAppIcon function
            let icon = window.getAppIcon ? window.getAppIcon(app.name || app.id) : '📦';
            if (app.icon) {
                const escapedFallback = typeof icon === 'string' ? icon.replace(/'/g, "&#39;").replace(/"/g, "&quot;") : icon;
                icon = `<img
                    src="${app.icon}"
                    alt="${app.name}"
                    style="width: 100%; height: 100%; object-fit: contain;"
                    onerror="this.style.display='none'; this.insertAdjacentHTML('afterend', '${escapedFallback}');"
                />`;
            }

            // Prepare app data for canvas click
            const appDataForCanvas = JSON.stringify({
                id: app.id,
                name: app.name,
                hostname: app.hostname,
                iframe_url: appUrl || app.url,
                url: appUrl || app.url,
                status: app.status
            }).replace(/"/g, '&quot;');

            // Click handler
            const clickHandler = (isRunning && appUrl)
                ? `onclick="openCanvas(${appDataForCanvas})" style="cursor: pointer;"`
                : `onclick="showView('apps')" style="cursor: pointer;"`;

            return `
                <div class="quick-app-item ${isRunning ? 'running' : 'stopped'}"
                     ${clickHandler}
                     title="${app.name || app.hostname} - ${isRunning ? 'Click to open' : 'Not running'}">
                    <div class="quick-app-icon">
                        ${icon}
                    </div>
                    <div class="quick-app-status ${isRunning ? 'running' : 'stopped'}"></div>
                    <div class="quick-app-name">${app.name || app.hostname}</div>
                </div>
            `;
        }).join('');

        // Reinitialize Lucide icons
        if (typeof window.initLucideIcons === 'function') {
            window.initLucideIcons();
        }
    }

    /**
     * Unmount dashboard and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Dashboard View');
        super.unmount();
    }
}

// Create singleton instance
export const dashboardView = new DashboardView();
