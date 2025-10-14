/**
 * Dashboard View Component
 *
 * Displays the main dashboard with hero section and quick apps.
 * THIS IS THE TRUE MIGRATION: Code moved from app.js, not recreated.
 *
 * @module views/DashboardView
 */

import { Component } from '../core/Component.js';
import { getAppIcon } from '../utils/ui-helpers.js';

export class DashboardView extends Component {
    constructor() {
        super();
        this._refreshInterval = null;
        this._state = null;
    }

    /**
     * Mount the dashboard view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    mount(container, state) {
        console.log('✅ Mounting Dashboard View');

        // Store state reference for refresh interval
        this._state = state;

        // ALWAYS regenerate HTML (no caching)
        console.log('🏗️  Generating dashboard HTML...');
        container.innerHTML = this.generateDashboardHTML();

        // Re-initialize Lucide icons
        if (window.lucide && window.lucide.createIcons) {
            window.lucide.createIcons();
            console.log('✅ Lucide icons re-initialized');
        }

        // MOVED FROM app.js: Update hero stats and recent apps with FRESH data
        const freshState = window.getState ? window.getState() : state;
        this.updateHeroStats(freshState);
        this.updateRecentApps(freshState);
        this._state = freshState;

        // Optional: Auto-refresh dashboard every 30 seconds
        this._refreshInterval = this.trackInterval(() => {
            const currentState = window.getState ? window.getState() : this._state;
            this.updateHeroStats(currentState);
            this.updateRecentApps(currentState);
            this._state = currentState;
        }, 30000);

        // Call parent mount
        return super.mount(container, state);
    }

    /**
     * Generate dashboard HTML structure
     * @returns {string} Dashboard HTML
     */
    generateDashboardHTML() {
        return `
            <!-- Hero Section -->
            <div class="hero-section">
                <div class="hero-content">
                    <div class="hero-badge">
                        <i data-lucide="zap"></i>
                        <span>Next-Gen Application Platform</span>
                    </div>
                    <h1 class="hero-title">Welcome to Proximity</h1>
                    <p class="hero-description">
                        Deploy, manage, and scale your applications effortlessly across your Proxmox infrastructure.
                        Experience the future of container orchestration with an intuitive interface designed for developers.
                    </p>
                    <!-- Hero Stats: Hosts and Apps Count -->
                    <div class="hero-stats-inline">
                        <div class="hero-stat-compact">
                            <i data-lucide="server"></i>
                            <span class="hero-stat-value-inline" id="heroNodesCount">0</span>
                            <span class="hero-stat-label-inline">Hosts</span>
                        </div>
                        <div class="hero-stat-compact">
                            <i data-lucide="package"></i>
                            <span class="hero-stat-value-inline" id="heroAppsCount">0</span>
                            <span class="hero-stat-label-inline">Applications</span>
                        </div>
                    </div>

                    <!-- Quick Apps Grid Integrated -->
                    <div class="hero-apps-container">
                        <div class="hero-apps-header">
                            <h3 class="hero-apps-title">Your Applications</h3>
                            <button class="hero-apps-view-all" data-view="apps" title="View All Applications">
                                <span>View All</span>
                                <i data-lucide="arrow-right"></i>
                            </button>
                        </div>
                        <div id="quickApps" class="hero-apps-grid">
                            <div class="empty-state-compact">
                                <i data-lucide="package"></i>
                                <span>No applications deployed yet</span>
                            </div>
                        </div>
                    </div>

                    <div class="hero-actions">
                        <button class="btn btn-primary btn-lg" data-view="catalog">
                            <i data-lucide="rocket"></i>
                            Deploy Your First App
                        </button>
                        <button class="btn btn-secondary btn-lg" data-view="monitoring">
                            <i data-lucide="activity"></i>
                            View Monitoring
                        </button>
                    </div>
                </div>
                <div class="hero-visual">
                    <div class="hero-grid-bg"></div>
                    <div class="hero-glow"></div>
                </div>
            </div>
        `;
    }

    /**
     * MOVED FROM app.js (line 406): updateHeroStats()
     * Update hero section stats (apps count, nodes count, containers count)
     * @param {Object} state - Application state
     */
    updateHeroStats(state) {
        // Update hero section stats
        const heroAppsCount = document.getElementById('heroAppsCount');
        const heroNodesCount = document.getElementById('heroNodesCount');
        const heroContainersCount = document.getElementById('heroContainersCount');

        if (heroAppsCount) {
            const totalApps = (state.deployedApps || []).length;
            heroAppsCount.textContent = totalApps;
        }

        if (heroNodesCount) {
            const activeNodes = (state.nodes || []).filter(n => n.status === 'online').length;
            heroNodesCount.textContent = activeNodes;
        }

        if (heroContainersCount) {
            const runningContainers = (state.deployedApps || []).filter(a => a.status === 'running').length;
            heroContainersCount.textContent = runningContainers;
        }
    }

    /**
     * MOVED FROM app.js (line 457): updateRecentApps()
     * Update quick apps grid in hero section
     * @param {Object} state - Application state
     */
    updateRecentApps(state) {
        console.log('📱 updateRecentApps() called');
        const container = document.getElementById('quickApps');

        if (!container) {
            console.warn('⚠️  quickApps container not found in DOM');
            return;
        }

        const deployedApps = state.deployedApps || [];
        console.log(`✓ quickApps container found, deployedApps count: ${deployedApps.length}`);

        if (deployedApps.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i data-lucide="package" style="width: 48px; height: 48px;"></i>
                    </div>
                    <h3 class="empty-title">No applications yet</h3>
                    <p class="empty-message">Deploy your first application from the catalog to get started.</p>
                    <button class="btn btn-primary" onclick="window.router.navigateTo('catalog')">Browse Catalog</button>
                </div>
            `;
            if (typeof window.initLucideIcons === 'function') {
                window.initLucideIcons();
            }
            return;
        }

        // Show all apps as quick access icons
        container.innerHTML = deployedApps.map(app => {
            const isRunning = app.status === 'running';
            const appUrl = (app.url && app.url !== 'None' && app.url !== 'null') ? app.url : null;

            // Get icon - uses imported getAppIcon utility
            let icon = getAppIcon(app.name || app.id);
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
                : `onclick="window.router.navigateTo('apps')" style="cursor: pointer;"`;

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
