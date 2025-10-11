/**
 * Apps View Component
 *
 * Displays all deployed applications with real-time CPU/RAM metrics.
 * THIS IS THE TRUE MIGRATION: Code moved from app.js, not recreated.
 *
 * @module views/AppsView
 */

import { Component } from '../core/Component.js';

export class AppsView extends Component {
    constructor() {
        super();
        this._cpuPollingInterval = null;
    }

    /**
     * Mount the apps view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    mount(container, state) {
        console.log('✅ Mounting Apps View');

        // MOVED FROM app.js: renderAppsView() function
        this.renderAppsView(container);

        // MOVED FROM app.js: Start CPU polling
        this.startCPUPolling();

        // Call parent mount
        return super.mount(container, state);
    }

    /**
     * MOVED FROM app.js (line 1192): renderAppsView()
     * Renders the apps view HTML structure and app cards
     */
    renderAppsView(container) {
        container.classList.remove('has-sub-nav'); // Remove old sub-nav class

        // Search bar is now in the submenu - no need for it here anymore
        const content = `
            <div class="apps-grid deployed" id="allAppsGrid"></div>
        `;

        container.innerHTML = content;

        // Render app cards using template cloning (existing pattern)
        const grid = document.getElementById('allAppsGrid');

        if (window.state.deployedApps.length === 0) {
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
            // Render each app card using template (relies on global renderAppCard for now)
            for (const app of window.state.deployedApps) {
                if (typeof window.renderAppCard === 'function') {
                    window.renderAppCard(app, grid, true);
                }
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
     * MOVED FROM app.js (line 785): startCPUPolling()
     * Start polling for real-time CPU/RAM metrics
     */
    startCPUPolling() {
        // Clear any existing interval
        this.stopCPUPolling();

        console.log('🔄 Starting resource metrics polling...');

        // Poll every 3 seconds - tracked for automatic cleanup
        this._cpuPollingInterval = this.trackInterval(async () => {
            console.log('📊 Polling cycle started...');

            try {
                // Fetch updated app stats using authFetch
                const response = await window.authFetch(`${window.API_BASE}/apps`);

                if (response.ok) {
                    const apps = await response.json();
                    console.log(`✓ Fetched ${apps.length} apps from API`);

                    // Update metrics for all visible apps
                    apps.forEach(app => {
                        const cpuBar = document.querySelector(`.cpu-bar[data-app-id="${app.id}"]`);
                        const ramBar = document.querySelector(`.ram-bar[data-app-id="${app.id}"]`);

                        if (!cpuBar || !ramBar) {
                            console.warn(`⚠️ Bars not found for app ${app.id} (${app.name})`);
                            return;
                        }

                        console.log(`📈 Updating metrics for ${app.name} (${app.id})`);

                        // Check if app is running
                        const status = app.status ? app.status.toLowerCase() : 'stopped';
                        const isRunning = status === 'running';

                        if (!isRunning) {
                            console.log(`  ⏸️ App ${app.name} is ${status} - resetting bars to 0`);
                            // Hide metrics for stopped apps
                            cpuBar.style.width = '0%';
                            ramBar.style.width = '0%';
                            cpuBar.classList.remove('high-usage', 'critical-usage');
                            ramBar.classList.remove('high-usage', 'critical-usage');

                            const cpuValueSpan = cpuBar.closest('.metric-item')?.querySelector('.cpu-value');
                            const ramValueSpan = ramBar.closest('.metric-item')?.querySelector('.ram-value');
                            if (cpuValueSpan) cpuValueSpan.textContent = '0%';
                            if (ramValueSpan) ramValueSpan.textContent = '0 MB';
                        } else {
                            console.log(`  ✓ App ${app.name} is running - fetching stats...`);
                            // For running apps, fetch current stats
                            this.fetchAndUpdateAppStats(app.id, cpuBar, ramBar);
                        }
                    });

                    // Update state.deployedApps status only, preserve existing stats
                    window.state.deployedApps.forEach(stateApp => {
                        const updatedApp = apps.find(a => a.id === stateApp.id);
                        if (updatedApp) {
                            stateApp.status = updatedApp.status;
                            stateApp.url = updatedApp.url;
                            stateApp.iframe_url = updatedApp.iframe_url;
                        }
                    });
                } else if (response.status === 401) {
                    console.error('❌ Authentication failed in CPU polling');
                    this.stopCPUPolling();
                } else {
                    console.error(`❌ Polling failed with status ${response.status}`);
                }
            } catch (error) {
                console.error('❌ Error polling resource metrics:', error);
                // Don't stop polling on network errors, just log and continue
            }
        }, 3000); // Poll every 3 seconds
    }

    /**
     * MOVED FROM app.js (line 870): fetchAndUpdateAppStats()
     * Fetch and update stats for a specific app
     */
    async fetchAndUpdateAppStats(appId, cpuBar, ramBar) {
        try {
            console.log(`    🔍 Fetching stats for app ${appId}...`);
            const response = await window.authFetch(`${window.API_BASE}/apps/${appId}/stats/current`);

            if (response.ok) {
                const stats = await response.json();
                console.log(`    ✓ Stats received:`, {
                    cpu_percent: stats.cpu_percent,
                    mem_used_gb: stats.mem_used_gb,
                    mem_total_gb: stats.mem_total_gb,
                    cached: stats.cached
                });

                // Update CPU - use cpu_percent from API
                const cpuUsage = Math.round(stats.cpu_percent || 0);
                cpuBar.style.width = `${cpuUsage}%`;

                const cpuValueSpan = cpuBar.closest('.metric-item')?.querySelector('.cpu-value');
                if (cpuValueSpan) cpuValueSpan.textContent = `${cpuUsage}%`;

                cpuBar.classList.remove('high-usage', 'critical-usage');
                if (cpuUsage >= 95) {
                    cpuBar.classList.add('critical-usage');
                } else if (cpuUsage >= 80) {
                    cpuBar.classList.add('high-usage');
                }

                // Update RAM - convert GB to MB for display
                const ramUsageMB = Math.round((stats.mem_used_gb || 0) * 1024);
                const ramMaxMB = Math.round((stats.mem_total_gb || 1) * 1024);
                const ramPercentage = ramMaxMB > 0 ? (ramUsageMB / ramMaxMB) * 100 : 0;

                ramBar.style.width = `${ramPercentage}%`;

                const ramValueSpan = ramBar.closest('.metric-item')?.querySelector('.ram-value');
                if (ramValueSpan) ramValueSpan.textContent = `${ramUsageMB} MB`;

                ramBar.classList.remove('high-usage', 'critical-usage');
                if (ramPercentage >= 95) {
                    ramBar.classList.add('critical-usage');
                } else if (ramPercentage >= 80) {
                    ramBar.classList.add('high-usage');
                }

                console.log(`    ✓ Updated bars: CPU=${cpuUsage}%, RAM=${ramUsageMB}MB (${Math.round(ramPercentage)}%)`);
            } else {
                console.error(`    ❌ Stats API returned ${response.status} for app ${appId}`);
            }
        } catch (error) {
            console.error(`    ❌ Error fetching stats for app ${appId}:`, error);
        }
    }

    /**
     * MOVED FROM app.js (line 928): stopCPUPolling()
     * Stop polling for CPU usage updates
     */
    stopCPUPolling() {
        if (this._cpuPollingInterval) {
            console.log('⏹️ Stopping CPU usage polling...');
            // Interval is already tracked by Component.trackInterval()
            // so it will be auto-cleared on unmount, but we clear it here too
            clearInterval(this._cpuPollingInterval);
            this._cpuPollingInterval = null;
        }
    }

    /**
     * Unmount apps view and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Apps View');
        this.stopCPUPolling();
        super.unmount();
    }
}

// Create singleton instance
export const appsView = new AppsView();
