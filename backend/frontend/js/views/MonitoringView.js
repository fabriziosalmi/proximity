/**
 * Monitoring View Component
 *
 * Displays system monitoring and metrics for nodes and applications.
 * FULLY MIGRATED from app.js renderMonitoringView() function.
 *
 * @module views/MonitoringView
 */

import { Component } from '../core/Component.js';
import { formatBytes } from '../utils/formatters.js';
import { authFetch, API_BASE } from '../services/api.js';
import { showLoading, hideLoading } from '../utils/ui.js';

export class MonitoringView extends Component {
    constructor() {
        super();
    }

    /**
     * Mount the monitoring view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    mount(container, state) {
        console.group('📍 MonitoringView Mount');
        console.log('🔐 Auth Status:', state.isAuthenticated ? '✅ Authenticated' : '❌ Not Authenticated');
        console.log('👤 Current User:', state.currentUser?.username || 'none');
        console.log('📦 Container:', container.id, 'Empty:', !container.innerHTML.trim());
        console.log('� Nodes count:', state.nodes?.length || 0);
        console.log('📦 Apps count:', state.deployedApps?.length || 0);

        try {
            this.renderMonitoringView(container, state);
            console.log('✅ MonitoringView rendered successfully');
        } catch (error) {
            console.error('❌ Error mounting Monitoring view:', error);
            console.error('Stack:', error.stack);
            container.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="alert-triangle"></i>
                    <h3>Error Loading Monitoring</h3>
                    <p>${error.message}</p>
                </div>
            `;
        } finally {
            console.groupEnd();
        }

        // Call parent mount
        return super.mount(container, state);
    }

    /**
     * MIGRATED FROM app.js (line 1064): renderMonitoringView()
     * Render monitoring view with node and application metrics
     * @param {HTMLElement} container - Container element
     * @param {Object} state - Application state
     */
    async renderMonitoringView(container, state) {
        // Fetch nodes if not in state
        let nodes = state.nodes || [];
        if (!nodes || nodes.length === 0) {
            showLoading('Loading monitoring data...');
            try {
                console.log('[Monitoring] Fetching nodes from API...');
                const response = await authFetch(`${API_BASE}/system/nodes`);
                if (response.ok) {
                    nodes = await response.json();
                    console.log('[Monitoring] Loaded nodes:', nodes.length);
                }
            } catch (err) {
                console.error('[Monitoring] Failed to load nodes:', err);
            }
            hideLoading();
        }

        // Calculate statistics for Applications Summary with safe defaults
        const deployedApps = state.deployedApps || [];
        const totalApps = deployedApps.length;

        const content = `
            <!-- Node-by-Node Breakdown -->
            ${nodes.length > 0 ? `
            <div class="monitor-section">
                <h2 class="monitor-section-title">
                    <i data-lucide="server"></i>
                    Node Resource Breakdown
                </h2>
                ${nodes.map(node => {
                    const nodeCpuPercent = node.maxcpu > 0 ? Math.round((node.cpu / node.maxcpu) * 100) : 0;
                    const nodeRamPercent = node.maxmem > 0 ? Math.round((node.mem / node.maxmem) * 100) : 0;
                    const nodeDiskPercent = node.maxdisk > 0 ? Math.round((node.disk / node.maxdisk) * 100) : 0;

                    return `
                    <div class="node-monitor-card">
                        <div class="node-monitor-header">
                            <div class="node-monitor-title">
                                <i data-lucide="server"></i>
                                <h3>${node.node}</h3>
                                <span class="status-badge ${node.status === 'online' ? 'running' : 'stopped'}">
                                    <span class="status-dot"></span>
                                    ${node.status}
                                </span>
                            </div>
                        </div>

                        <div class="node-monitor-resources">
                            <!-- CPU -->
                            <div class="node-resource">
                                <div class="node-resource-header">
                                    <span class="node-resource-label">
                                        <i data-lucide="cpu"></i>
                                        CPU
                                    </span>
                                    <span class="node-resource-value">${nodeCpuPercent}%</span>
                                </div>
                                <div class="monitor-bar-container">
                                    <div class="monitor-bar small">
                                        <div class="monitor-bar-fill ${nodeCpuPercent >= 80 ? 'critical' : nodeCpuPercent >= 60 ? 'warning' : 'normal'}"
                                             style="width: ${nodeCpuPercent}%"></div>
                                    </div>
                                </div>
                                <div class="node-resource-details">
                                    ${node.cpu?.toFixed(2) || 0} / ${node.maxcpu || 0} cores
                                </div>
                            </div>

                            <!-- RAM -->
                            <div class="node-resource">
                                <div class="node-resource-header">
                                    <span class="node-resource-label">
                                        <i data-lucide="memory-stick"></i>
                                        RAM
                                    </span>
                                    <span class="node-resource-value">${nodeRamPercent}%</span>
                                </div>
                                <div class="monitor-bar-container">
                                    <div class="monitor-bar small">
                                        <div class="monitor-bar-fill ${nodeRamPercent >= 80 ? 'critical' : nodeRamPercent >= 60 ? 'warning' : 'normal'}"
                                             style="width: ${nodeRamPercent}%"></div>
                                    </div>
                                </div>
                                <div class="node-resource-details">
                                    ${formatBytes(node.mem || 0)} / ${formatBytes(node.maxmem || 0)}
                                </div>
                            </div>

                            <!-- Disk -->
                            <div class="node-resource">
                                <div class="node-resource-header">
                                    <span class="node-resource-label">
                                        <i data-lucide="hard-drive"></i>
                                        Storage
                                    </span>
                                    <span class="node-resource-value">${nodeDiskPercent}%</span>
                                </div>
                                <div class="monitor-bar-container">
                                    <div class="monitor-bar small">
                                        <div class="monitor-bar-fill ${nodeDiskPercent >= 80 ? 'critical' : nodeDiskPercent >= 60 ? 'warning' : 'normal'}"
                                             style="width: ${nodeDiskPercent}%"></div>
                                    </div>
                                </div>
                                <div class="node-resource-details">
                                    ${formatBytes(node.disk || 0)} / ${formatBytes(node.maxdisk || 0)}
                                </div>
                            </div>
                        </div>
                    </div>
                    `;
                }).join('')}
            </div>
            ` : ''}

            <!-- Applications Summary Table -->
            ${totalApps > 0 ? `
            <div class="monitor-section">
                <h2 class="monitor-section-title">
                    <i data-lucide="package"></i>
                    Application Resources
                </h2>
                <div class="monitor-table-container">
                    <table class="monitor-table">
                        <thead>
                            <tr>
                                <th>Application</th>
                                <th>Status</th>
                                <th>Node</th>
                                <th>CPU</th>
                                <th>RAM</th>
                                <th>Disk</th>
                                <th>IP Address</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${state.deployedApps.map(app => `
                                <tr>
                                    <td>
                                        <div class="table-app-name">
                                            <span class="table-app-icon">${app.icon || '📦'}</span>
                                            <strong>${app.name || app.hostname}</strong>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="status-badge ${app.status === 'running' ? 'running' : 'stopped'}">
                                            <span class="status-dot"></span>
                                            ${app.status || 'unknown'}
                                        </span>
                                    </td>
                                    <td><code>${app.node || 'N/A'}</code></td>
                                    <td>${app.cores || app.cpu || 'N/A'}</td>
                                    <td>${app.memory ? (app.memory + ' MB') : 'N/A'}</td>
                                    <td>${app.disk || 'N/A'} GB</td>
                                    <td><code>${app.ip || 'N/A'}</code></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
            ` : `
            <div class="empty-state">
                <div class="empty-icon">
                    <i data-lucide="activity" style="width: 48px; height: 48px;"></i>
                </div>
                <h3 class="empty-title">No applications to monitor</h3>
                <p class="empty-message">Deploy applications to see monitoring data here.</p>
                <button class="btn btn-primary" data-view="catalog">Browse Catalog</button>
            </div>
            `}
        `;

        container.innerHTML = content;

        // Initialize Lucide icons
        if (window.lucide && window.lucide.createIcons) {
            window.lucide.createIcons();
        }
    }

    /**
     * Unmount monitoring view and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Monitoring View');
        super.unmount();
    }
}

// Create singleton instance
export const monitoringView = new MonitoringView();
