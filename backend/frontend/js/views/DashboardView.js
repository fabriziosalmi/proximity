/**
 * Dashboard View Component
 *
 * Displays a clean, static dashboard with hero section and quick action buttons.
 * Removed dynamic app loading for improved performance and cleaner layout.
 * Focus on "My Apps" page for full application management.
 *
 * @module views/DashboardView
 */

import { Component } from '../core/Component.js';

export class DashboardView extends Component {
    constructor() {
        super();
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

                    <div class="hero-actions">
                        <button class="btn btn-primary btn-lg" data-view="apps">
                            <i data-lucide="package"></i>
                            My Applications
                        </button>
                        <button class="btn btn-primary btn-lg" data-view="catalog">
                            <i data-lucide="rocket"></i>
                            Deploy New App
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
     * Unmount dashboard and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Dashboard View');
        super.unmount();
    }
}

// Create singleton instance
export const dashboardView = new DashboardView();
