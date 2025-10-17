/**
 * Dashboard View Component
 *
 * Displays a clean, static dashboard with hero section and quick action buttons.
 * Includes infrastructure diagram showing Proxmox host and deployed apps.
 * Focus on "My Apps" page for full application management.
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
    }

    /**
     * Mount the dashboard view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    mount(container, state) {
        console.log('✅ Mounting Dashboard View (Static)');

        // ALWAYS regenerate HTML (no caching)
        console.log('🏗️  Generating dashboard HTML...');
        container.innerHTML = this.generateDashboardHTML();

        // Re-initialize Lucide icons
        if (window.lucide && window.lucide.createIcons) {
            window.lucide.createIcons();
            console.log('✅ Lucide icons re-initialized');
        }

        // Load and render infrastructure diagram
        this.loadInfrastructureDiagram();

        // Call parent mount
        return super.mount(container, state);
    }

    /**
     * Load infrastructure data and render diagram
     */
    async loadInfrastructureDiagram() {
        try {
            // Fetch system status and apps data
            let status = null;
            let apps = [];

            // Fetch system information with auth
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

            // Fetch all apps with auth
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

            console.log('📊 Infrastructure data ready (system info:', !!status, 'apps:', apps.length, ')');

            // Initialize diagram with whatever data we have
            this.infraDiagram.init(status, apps);

        } catch (error) {
            console.error('❌ Error loading infrastructure diagram:', error);
            // Still initialize diagram with empty data as fallback
            this.infraDiagram.init(null, []);
        }
    }


    /**
     * Generate dashboard HTML structure
     * @returns {string} Dashboard HTML
     */
    generateDashboardHTML() {
        return `
            <!-- Infrastructure Diagram Section -->
            <div id="infrastructure-diagram"></div>
        `;
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
