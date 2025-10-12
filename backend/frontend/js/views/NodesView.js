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
        // Load infrastructure status
        showLoading('Loading infrastructure status...');
        let infrastructure = null;
        let error = null;

        try {
            const token = localStorage.getItem('proximity_token');
            if (token) {
                console.log('[Infrastructure] Fetching status...');
                const response = await authFetch(`${API_BASE}/system/infrastructure/status`);
                console.log('[Infrastructure] Response status:', response.status);
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('[Infrastructure] Result:', result);
                    infrastructure = result.data;
                    console.log('[Infrastructure] Infrastructure data:', infrastructure);
                } else {
                    error = `Failed to load infrastructure status (${response.status})`;
                    console.error('[Infrastructure] Error:', error);
                }
            } else {
                error = 'Not authenticated';
                console.error('[Infrastructure] No auth token');
            }
        } catch (err) {
            error = err.message || 'Failed to load infrastructure';
            console.error('[Infrastructure] Exception:', err);
        }
        hideLoading();

        // Prepare appliance info
        const appliance = infrastructure?.appliance || null;
        const services = infrastructure?.services || {};
        const network = infrastructure?.network || {};
        const connected_apps = infrastructure?.applications || infrastructure?.connected_apps || [];
        const health_status = infrastructure?.health_status || 'unknown';
        
        console.log('[Infrastructure] Final state:', {
            appliance: !!appliance,
            services: Object.keys(services).length,
            connected_apps: connected_apps.length,
            health_status,
            error
        });

        const content = `
            <!-- Network Appliance Card -->
            ${appliance ? `
            <div class="app-card deployed" style="margin-bottom: 2rem;">
                <!-- Header with icon, name, status and quick actions -->
                <div class="app-card-header">
                    <div class="app-icon-lg">🌐</div>
                    <div class="app-info">
                        <h3 class="app-name">${appliance.hostname || 'Network Appliance'}</h3>
                        <span class="status-badge ${appliance.status === 'running' ? 'running' : 'stopped'}">
                            <span class="status-dot"></span>
                            ${appliance.status || 'unknown'}
                        </span>
                    </div>
                    
                    <!-- Quick Actions -->
                    <div class="app-quick-actions">
                        <button class="action-icon" title="Restart Appliance" data-action="restart-appliance">
                            <i data-lucide="rotate-cw"></i>
                        </button>
                        <button class="action-icon" title="View Logs" data-action="view-appliance-logs">
                            <i data-lucide="file-text"></i>
                        </button>
                        <button class="action-icon" title="Test NAT" data-action="test-nat">
                            <i data-lucide="zap"></i>
                        </button>
                    </div>
                </div>

                <!-- Connection info -->
                <div class="app-connection-info">
                    <div class="connection-item" title="VMID">
                        <i data-lucide="hash" class="connection-icon"></i>
                        <span class="connection-value">${appliance.vmid || 'N/A'}</span>
                    </div>
                    <div class="connection-item" title="Node">
                        <i data-lucide="server" class="connection-icon"></i>
                        <span class="connection-value">${appliance.node || 'N/A'}</span>
                    </div>
                    <div class="connection-item" title="WAN interface (eth0) - DHCP from external network via vmbr0">
                        <i data-lucide="globe" class="connection-icon"></i>
                        <span class="connection-value">WAN: ${appliance.wan_ip || 'N/A'}</span>
                    </div>
                    <div class="connection-item" title="LAN interface (eth1) - Gateway for applications on proximity-lan">
                        <i data-lucide="network" class="connection-icon"></i>
                        <span class="connection-value">LAN: ${appliance.lan_ip || 'N/A'}</span>
                    </div>
                </div>

                <!-- Resource stats -->
                <div class="app-connection-info" style="margin-top: 0.5rem;">
                    <div class="connection-item">
                        <i data-lucide="cpu" class="connection-icon"></i>
                        <span class="connection-value">${appliance.cores || 'N/A'} cores</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="memory-stick" class="connection-icon"></i>
                        <span class="connection-value">${appliance.memory || 'N/A'} MB</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="hard-drive" class="connection-icon"></i>
                        <span class="connection-value">${appliance.disk || 'N/A'} GB</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="clock" class="connection-icon"></i>
                        <span class="connection-value">${appliance.uptime || 'N/A'}</span>
                    </div>
                </div>

                <div id="infrastructureStatus" style="margin-top: 1rem;"></div>
            </div>
            ` : ''}

            <!-- Services Health Grid -->
            ${Object.keys(services).length > 0 ? `
            <div class="services-grid" style="margin-bottom: 2rem;">
                ${Object.entries(services).map(([name, service]) => `
                    <div class="service-card ${service.healthy ? 'healthy' : 'unhealthy'}">
                        <div class="service-header">
                            <div class="service-icon">
                                ${name === 'dnsmasq' ? '🌐' :
                                  name === 'caddy' ? '🔀' :
                                  name === 'nat' ? '🔗' : '⚙️'}
                            </div>
                            <div class="service-info">
                                <h3 class="service-name">${name.charAt(0).toUpperCase() + name.slice(1)}</h3>
                                <span class="service-status ${service.healthy ? 'healthy' : 'unhealthy'}">
                                    ${service.healthy ? '● Running' : '○ Stopped'}
                                </span>
                            </div>
                        </div>
                        ${service.details ? `
                        <div class="service-details">
                            <small>${service.details}</small>
                        </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
            ` : ''}

            <!-- Network Configuration -->
            ${network.subnet ? `
            <div class="app-card deployed" style="margin-bottom: 2rem;">
                <div class="app-connection-info">
                    <div class="connection-item">
                        <i data-lucide="network" class="connection-icon"></i>
                        <span class="connection-value">Bridge: ${network.bridge || 'proximity-lan'}</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="wifi" class="connection-icon"></i>
                        <span class="connection-value">Subnet: ${network.subnet || 'N/A'}</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="door-open" class="connection-icon"></i>
                        <span class="connection-value">Gateway: ${network.gateway || 'N/A'}</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="settings" class="connection-icon"></i>
                        <span class="connection-value">DHCP: ${network.dhcp_range || 'N/A'}</span>
                    </div>
                </div>
                <div class="app-connection-info" style="margin-top: 0.5rem;">
                    <div class="connection-item">
                        <i data-lucide="globe" class="connection-icon"></i>
                        <span class="connection-value">DNS: ${network.dns_domain || 'prox.local'}</span>
                    </div>
                </div>
            </div>
            ` : ''}

            <!-- Connected Apps -->
            ${connected_apps && connected_apps.length > 0 ? `
            <div class="connected-apps-table">
                <table class="infrastructure-table">
                    <thead>
                        <tr>
                            <th>App Name</th>
                            <th>VMID</th>
                            <th>IP Address</th>
                            <th>Status</th>
                            <th>DNS Name</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${connected_apps.map(app => `
                            <tr>
                                <td><strong>${app.name || 'N/A'}</strong></td>
                                <td>${app.vmid || 'N/A'}</td>
                                <td><code>${app.ip_address || 'N/A'}</code></td>
                                <td>
                                    <span class="status-badge ${app.status === 'running' ? 'running' : 'stopped'}">
                                        <span class="status-dot"></span>
                                        ${app.status || 'unknown'}
                                    </span>
                                </td>
                                <td><code>${app.dns_name || app.name + '.prox.local' || 'N/A'}</code></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            ` : ''}

            <!-- Proxmox Nodes -->
            <div class="apps-grid deployed">
                ${state.nodes.map(node => {
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
