/**
 * Dashboard View Component
 *
 * Displays the Living Infrastructure Atlas - a dynamic, real-time visualization
 * of the entire homelab infrastructure from internet connection to app containers.
 * Features interactive drill-down navigation, live status indicators, and
 * animated data flow visualization.
 *
 * @module views/DashboardView
 */

import { Component } from '../core/Component.js';
import { InfrastructureDiagram } from '../components/InfrastructureDiagram.js';
import { authFetch, API_BASE } from '../services/api.js';

export class DashboardView extends Component {
    constructor() {
        super();
        this.infraDiagram = new InfrastructureDiagram();
        this.refreshInterval = null;
    }

    /**
     * Mount the dashboard view with Living Infrastructure Atlas
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    mount(container, state) {
        console.log('✅ Mounting Living Infrastructure Atlas Dashboard');

        // Generate and render dashboard HTML
        container.innerHTML = this.generateDashboardHTML();

        // Re-initialize Lucide icons if available
        if (window.lucide && window.lucide.createIcons) {
            window.lucide.createIcons();
        }

        // Load and render infrastructure diagram with real data
        this.loadInfrastructureDiagram();

        // Set up auto-refresh (every 10 seconds)
        this.setupAutoRefresh();

        // Setup global event listeners for app actions
        this.setupEventListeners();

        return super.mount(container, state);
    }

    /**
     * Setup event listeners for app interactions
     */
    setupEventListeners() {
        // Listen for app open events from diagram
        window.addEventListener('appOpen', (event) => {
            console.log('🚀 App open requested:', event.detail.appId);
            // Handler can be extended based on app shell capabilities
        });
    }

    /**
     * Setup auto-refresh of infrastructure data
     */
    setupAutoRefresh() {
        // Refresh every 10 seconds to keep dashboard live
        this.refreshInterval = setInterval(() => {
            console.log('🔄 Auto-refreshing infrastructure data...');
            this.loadInfrastructureDiagram();
        }, 10000);
    }

    /**
     * Load infrastructure data from multiple API endpoints and render diagram
     */
    async loadInfrastructureDiagram() {
        try {
            // Fetch data in parallel from all endpoints
            let status = null;
            let apps = [];
            let networkStatus = null;

            // Fetch system information
            try {
                const statusResponse = await authFetch(`${API_BASE}/system/info`);
                if (statusResponse.ok) {
                    status = await statusResponse.json();
                    console.log('✅ System info loaded:', status);
                } else {
                    console.warn('⚠️  System info returned status:', statusResponse.status);
                }
            } catch (e) {
                console.warn('⚠️  Could not load system info:', e.message);
            }

            // Fetch all apps
            try {
                const appsResponse = await authFetch(`${API_BASE}/apps`);
                if (appsResponse.ok) {
                    const appsData = await appsResponse.json();
                    apps = Array.isArray(appsData) ? appsData : [];
                    console.log('✅ Apps loaded:', apps.length, 'apps');
                } else {
                    console.warn('⚠️  Apps endpoint returned status:', appsResponse.status);
                }
            } catch (e) {
                console.warn('⚠️  Could not load apps:', e.message);
            }

            // Optional: Fetch network status if available
            try {
                const networkResponse = await authFetch(`${API_BASE}/system/network`);
                if (networkResponse.ok) {
                    networkStatus = await networkResponse.json();
                    console.log('✅ Network status loaded');
                }
            } catch (e) {
                console.warn('⚠️  Network status not available:', e.message);
            }

            console.log('📊 Infrastructure data ready:', {
                system: !!status,
                apps: apps.length,
                network: !!networkStatus
            });

            // Initialize diagram with all available data
            this.infraDiagram.init(status, apps, networkStatus);

        } catch (error) {
            console.error('❌ Error loading infrastructure diagram:', error);
            // Initialize with empty/default data as fallback
            this.infraDiagram.init(null, []);
        }
    }

    /**
     * Generate dashboard HTML structure
     * @returns {string} Dashboard HTML
     */
    generateDashboardHTML() {
        return `
            <!-- Living Infrastructure Atlas Container -->
            <div id="infrastructure-diagram"></div>
        `;
    }

    /**
     * Unmount dashboard and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Living Infrastructure Atlas Dashboard');
        
        // Clean up auto-refresh interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }

        super.unmount();
    }
}

// Create singleton instance
export const dashboardView = new DashboardView();
