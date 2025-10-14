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
                    </div>
                </div>
                <div class="hero-visual">
                    <div class="hero-grid-bg"></div>
                    <div class="hero-glow"></div>
                </div>
            </div>

            <!-- App Card Example Section -->
            <div class="dashboard-section">
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="layers"></i>
                        Application Management Preview
                    </h2>
                    <p class="section-subtitle">Example of how your deployed applications appear in Proximity</p>
                </div>

                <!-- Example App Card (Static Demo) -->
                <div class="app-card-container-demo">
                    <div class="app-card deployed demo-card">
                        <!-- Header: Icon, Name, Quick Actions -->
                        <div class="app-card-header">
                            <div class="app-icon-lg" style="background: linear-gradient(135deg, #00f5ff 0%, #00d4ff 100%);">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 32px; height: 32px; color: #0a0e1a;">
                                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                                    <line x1="8" y1="21" x2="16" y2="21"></line>
                                    <line x1="12" y1="17" x2="12" y2="21"></line>
                                </svg>
                            </div>
                            <div class="app-info">
                                <h3 class="app-name">Sample Application</h3>
                            </div>

                            <!-- Quick Actions -->
                            <div class="app-quick-actions">
                                <button class="action-icon" data-tooltip="Running" disabled>
                                    <i data-lucide="pause"></i>
                                </button>
                                <button class="action-icon" data-tooltip="Open in New Tab" disabled>
                                    <i data-lucide="external-link"></i>
                                </button>
                                <button class="action-icon" data-tooltip="View Logs" disabled>
                                    <i data-lucide="file-text"></i>
                                </button>
                                <button class="action-icon" data-tooltip="Open Console" disabled>
                                    <i data-lucide="terminal"></i>
                                </button>
                                <button class="action-icon" data-tooltip="Manage Backups" disabled>
                                    <i data-lucide="database"></i>
                                </button>
                                <button class="action-icon" data-tooltip="Update Application" disabled>
                                    <i data-lucide="arrow-up-circle"></i>
                                </button>
                                <button class="action-icon" data-tooltip="View Volumes" disabled>
                                    <i data-lucide="hard-drive"></i>
                                </button>
                                <button class="action-icon" data-tooltip="View Monitoring" disabled>
                                    <i data-lucide="activity"></i>
                                </button>
                                <button class="action-icon" data-tooltip="Restart App" disabled>
                                    <i data-lucide="refresh-cw"></i>
                                </button>
                                <button class="action-icon pro-feature" data-tooltip="Clone App" disabled>
                                    <i data-lucide="copy"></i>
                                </button>
                                <button class="action-icon pro-feature" data-tooltip="Edit Resources" disabled>
                                    <i data-lucide="sliders"></i>
                                </button>
                                <button class="action-icon danger" data-tooltip="Delete App" disabled>
                                    <i data-lucide="trash-2"></i>
                                </button>
                            </div>
                        </div>

                        <!-- Connection Info: Status, URL, Node, Container, Date -->
                        <div class="app-connection-info">
                            <div class="connection-item status-indicator">
                                <span class="status-dot running"></span>
                            </div>
                            <div class="connection-item">
                                <i data-lucide="link" class="connection-icon"></i>
                                <span class="connection-value">http://192.168.1.100:8080</span>
                            </div>
                            <div class="connection-item">
                                <i data-lucide="server" class="connection-icon"></i>
                                <span class="connection-value">pve</span>
                            </div>
                            <div class="connection-item">
                                <i data-lucide="box" class="connection-icon"></i>
                                <span class="connection-value">LXC-100</span>
                            </div>
                            <div class="connection-item">
                                <i data-lucide="clock" class="connection-icon"></i>
                                <span class="connection-value">2 days ago</span>
                            </div>
                        </div>

                        <!-- Resource Metrics: CPU and RAM Usage -->
                        <div class="app-metrics">
                            <div class="metric-item">
                                <i data-lucide="cpu" class="metric-icon"></i>
                                <div class="metric-bar-container">
                                    <div class="metric-bar cpu-bar" style="width: 45%;"></div>
                                </div>
                                <span class="metric-value">45%</span>
                            </div>
                            <div class="metric-item">
                                <i data-lucide="database" class="metric-icon"></i>
                                <div class="metric-bar-container">
                                    <div class="metric-bar ram-bar" style="width: 62%;"></div>
                                </div>
                                <span class="metric-value">512 MB</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="demo-card-note">
                    <i data-lucide="info"></i>
                    <span>This is a preview of how your deployed applications will appear. Go to <strong>My Applications</strong> to manage your real apps.</span>
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
