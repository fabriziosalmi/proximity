/**
 * Nodes View Component
 *
 * Displays infrastructure nodes (Proxmox hosts) and network appliance.
 * FULLY MIGRATED from app.js renderNodesView() function.
 *
 * @module views/NodesView
 */

import { Component } from '../core/Component.js';
import { authFetch, API_BASE } from '../services/api.js';
import { showLoading, hideLoading } from '../utils/ui.js';
import { formatBytes, formatUptime } from '../utils/formatters.js';
import { getState } from '../state/appState.js';

export class NodesView extends Component {
    constructor() {
        super();
    }

    /**
     * Mount the nodes view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    async mount(container, state) {
        console.group('📍 NodesView Mount');
        console.log('🔐 Auth Status:', state.isAuthenticated ? '✅ Authenticated' : '❌ Not Authenticated');
        console.log('👤 Current User:', state.currentUser?.username || 'none');
        console.log('📦 Container:', container.id, 'Empty:', !container.innerHTML.trim());

        try {
            await this.renderNodesView(container, state);
            console.log('✅ NodesView rendered successfully');
        } catch (error) {
            console.error('❌ Error mounting Nodes view:', error);
            console.error('Stack:', error.stack);
            container.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="alert-triangle"></i>
                    <h3>Error Loading Nodes</h3>
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
     * MIGRATED FROM app.js (line 782): renderNodesView()
     * Render nodes/infrastructure view
     * @param {HTMLElement} container - Container element
     * @param {Object} state - Application state
     */
    async renderNodesView(container, state) {
        // Load nodes directly from API
        showLoading('Loading infrastructure nodes...');
        let nodes = state.nodes || [];
        let error = null;

        try {
            console.log('[Nodes] Fetching nodes from API...');
            const response = await authFetch(`${API_BASE}/system/nodes`);
            console.log('[Nodes] Response status:', response.status);

            if (response.ok) {
                nodes = await response.json();
                console.log('[Nodes] Loaded nodes:', nodes.length);
            } else {
                error = `Failed to load nodes (${response.status})`;
                console.error('[Nodes] Error:', error);
            }
        } catch (err) {
            error = err.message || 'Failed to load nodes';
            console.error('[Nodes] Exception:', err);
        }
        hideLoading();

        console.log('[Nodes] Final state:', {
            nodes: nodes.length,
            error
        });

        // Show error if API call failed
        if (error) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i data-lucide="alert-triangle" style="width: 48px; height: 48px;"></i>
                    </div>
                    <h3 class="empty-title">Failed to Load Nodes</h3>
                    <p class="empty-message">${error}</p>
                    <button class="btn btn-primary" onclick="window.location.reload()">
                        <i data-lucide="refresh-cw"></i>
                        Retry
                    </button>
                </div>
            `;
            if (window.lucide && window.lucide.createIcons) {
                window.lucide.createIcons();
            }
            return;
        }

        // Show empty state if no nodes
        if (!nodes || nodes.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i data-lucide="server" style="width: 48px; height: 48px;"></i>
                    </div>
                    <h3 class="empty-title">No Proxmox Nodes Found</h3>
                    <p class="empty-message">Check your Proxmox connection in settings.</p>
                    <button class="btn btn-primary" data-view="settings">
                        <i data-lucide="settings"></i>
                        Configure Proxmox
                    </button>
                </div>
            `;
            if (window.lucide && window.lucide.createIcons) {
                window.lucide.createIcons();
            }
            return;
        }

        const content = `
            <!-- Network Architecture Info -->
            <div class="app-card deployed" style="margin-bottom: 2rem;">
                <div class="app-card-header">
                    <div class="app-icon-lg">🌐</div>
                    <div class="app-info">
                        <h3 class="app-name">Network Architecture</h3>
                        <p style="margin: 0.5rem 0 0 0; opacity: 0.8; font-size: 0.9rem;">
                            Simple DHCP networking via vmbr0 bridge
                        </p>
                    </div>
                </div>

                <!-- Network info -->
                <div class="app-connection-info" style="margin-top: 1rem;">
                    <div class="connection-item">
                        <i data-lucide="network" class="connection-icon"></i>
                        <span class="connection-value">Bridge: vmbr0</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="wifi" class="connection-icon"></i>
                        <span class="connection-value">IP: DHCP</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="globe" class="connection-icon"></i>
                        <span class="connection-value">Internet: Direct</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="check-circle" class="connection-icon"></i>
                        <span class="connection-value">No complex appliance needed</span>
                    </div>
                </div>
            </div>

            <!-- Proxmox Nodes -->
            <h2 style="margin: 2rem 0 1rem 0;">Proxmox Hosts</h2>
            <div class="apps-grid deployed">
                ${nodes.map(node => {
                    // Calculate percentages
                    const cpuPercent = node.maxcpu > 0 ? Math.round((node.cpu / node.maxcpu) * 100) : 0;
                    const ramPercent = node.maxmem > 0 ? Math.round((node.mem / node.maxmem) * 100) : 0;
                    const diskPercent = node.maxdisk > 0 ? Math.round((node.disk / node.maxdisk) * 100) : 0;
                    
                    return `
                        <div class="app-card deployed ${node.status === 'online' ? 'status-running' : 'status-stopped'}">
                            <div class="app-card-header">
                                <div class="app-icon-lg">🖥️</div>
                                <div class="app-info">
                                    <h3 class="app-name">${node.node}</h3>
                                </div>
                            </div>

                            <!-- Connection Info with Status Dot -->
                            <div class="app-connection-info">
                                <div class="connection-item status-indicator">
                                    <span class="status-dot"></span>
                                </div>
                                <div class="connection-item">
                                    <i data-lucide="activity" class="connection-icon"></i>
                                    <span class="connection-value">Uptime: ${node.uptime ? formatUptime(node.uptime) : 'N/A'}</span>
                                </div>
                            </div>

                            <!-- Resource Metrics: CPU, RAM, Disk with bars -->
                            <div class="app-metrics">
                                <div class="metric-item">
                                    <i data-lucide="cpu" class="metric-icon"></i>
                                    <div class="metric-bar-container">
                                        <div class="metric-bar cpu-bar" style="width: ${cpuPercent}%"></div>
                                    </div>
                                    <span class="metric-value">${cpuPercent}%</span>
                                </div>
                                <div class="metric-item">
                                    <i data-lucide="database" class="metric-icon"></i>
                                    <div class="metric-bar-container">
                                        <div class="metric-bar ram-bar" style="width: ${ramPercent}%"></div>
                                    </div>
                                    <span class="metric-value">${formatBytes(node.mem || 0)}</span>
                                </div>
                                <div class="metric-item">
                                    <i data-lucide="hard-drive" class="metric-icon"></i>
                                    <div class="metric-bar-container">
                                        <div class="metric-bar disk-bar" style="width: ${diskPercent}%"></div>
                                    </div>
                                    <span class="metric-value">${formatBytes(node.disk || 0)}</span>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        container.innerHTML = content;

        // Initialize Lucide icons
        if (window.lucide && window.lucide.createIcons) {
            window.lucide.createIcons();
        }
    }

    /**
     * Unmount nodes view and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Nodes View');
        super.unmount();
    }
}

// Create singleton instance
export const nodesView = new NodesView();
