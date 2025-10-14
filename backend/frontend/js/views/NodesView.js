/**
 * Nodes View Component
 *
 * Displays infrastructure nodes (Proxmox hosts) and network appliance.
 * FULLY MIGRATED from app.js renderNodesView() function.
 *
 * @module views/NodesView
 */

import { Component } from '../core/Component.js';
import { authFetch, API_BASE, getPublicNetworkInfo } from '../services/api.js';
import { showLoading, hideLoading } from '../utils/ui.js';
import { formatBytes, formatUptime } from '../utils/formatters.js';
import { getState } from '../state/appState.js';
import { networkMonitor } from '../services/networkMonitor.js';
import networkActivityMonitor from '../services/NetworkActivityMonitor.js';

export class NodesView extends Component {
    constructor() {
        super();
        this.unsubscribe = null;
    }

    /**
     * Mount the nodes view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    mount(container, state) {
        console.group('📍 NodesView Mount');
        console.log('🔐 Auth Status:', state.isAuthenticated ? '✅ Authenticated' : '❌ Not Authenticated');
        console.log('👤 Current User:', state.currentUser?.username || 'none');
        console.log('📦 Container:', container.id, 'Empty:', !container.innerHTML.trim());

        // Start network monitoring
        networkMonitor.startMonitoring();
        
        // Subscribe to network updates
        this.unsubscribe = networkMonitor.subscribe((metrics) => {
            this.updateNetworkStatus(metrics);
        });

        // Start async render WITHOUT blocking mount return
        this.renderNodesView(container, state).then(() => {
            console.log('✅ NodesView rendered successfully');
        }).catch(error => {
            console.error('❌ Error mounting Nodes view:', error);
            console.error('Stack:', error.stack);
            container.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="alert-triangle"></i>
                    <h3>Error Loading Nodes</h3>
                    <p>${error.message}</p>
                </div>
            `;
        }).finally(() => {
            console.groupEnd();
        });

        // Return unmount function
        const parentUnmount = super.mount(container, state);
        return () => {
            // Stop network monitoring
            networkMonitor.stopMonitoring();
            
            // Unsubscribe from updates
            if (this.unsubscribe) {
                this.unsubscribe();
                this.unsubscribe = null;
            }
            
            // Call parent unmount
            if (parentUnmount) {
                parentUnmount();
            }
        };
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
                        <p class="app-description" style="margin-top: 0.25rem; font-size: 0.75rem; opacity: 0.7;">
                        </p>
                    </div>
                </div>

                <!-- Network Status LEDs - Second Row -->
                <div class="app-connection-info">
                    <div class="connection-item">
                        <span class="status-led status-led-active network-led-bridge" title="Bridge Active"></span>
                        <i data-lucide="network" class="connection-icon"></i>
                        <span class="connection-value">Bridge: vmbr0</span>
                    </div>
                    <div class="connection-item">
                        <span class="status-led status-led-pulse network-led-dhcp" title="DHCP Active"></span>
                        <i data-lucide="wifi" class="connection-icon"></i>
                        <span class="connection-value"> DHCP</span>
                    </div>
                    <div class="connection-item">
                        <span class="status-led status-led-blink network-led-gateway" title="Network Activity (TX/RX)"></span>
                        <i data-lucide="activity" class="connection-icon"></i>
                        <span class="connection-value">Gateway: <span class="network-node-count">Checking...</span></span>
                    </div>
                    <div class="connection-item">
                        <span class="status-led status-led-active network-led-internet" title="Internet Connected"></span>
                        <i data-lucide="globe" class="connection-icon"></i>
                        <span class="connection-value"> Connected</span>
                    </div>
                    <div class="connection-item" id="public-ip-item">
                        <i data-lucide="globe-2" class="connection-icon"></i>
                        <span class="connection-value"> <span class="public-ip-value">Loading...</span></span>
                    </div>
                    <div class="connection-item" id="country-item">
                        <span class="country-flag" style="width: 20px; height: 20px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 14px; margin-right: 0.5rem;">🌍</span>
                        <i data-lucide="map-pin" class="connection-icon"></i>
                        <span class="connection-value"> <span class="country-value">Loading...</span></span>
                    </div>
                </div>

                <!-- Network Details - Third Row (styled as metrics) -->
                <div class="app-metrics">
                    <div class="connection-item">
                        <i data-lucide="server" class="metric-icon"></i>
                        <span class="metric-value">Type: Bridge</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="shield" class="metric-icon"></i>
                        <span class="metric-value">Mode: NAT</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="zap" class="metric-icon"></i>
                        <span class="metric-value">Status: Active</span>
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
                    const isOnline = node.status === 'online';
                    
                    // Extract version (e.g., "pve-manager/8.1.3")
                    const pveVersion = node.pveversion || 'N/A';
                    const versionShort = pveVersion.split('/')[1] || pveVersion;
                    
                    return `
                        <div class="app-card deployed ${isOnline ? 'status-running' : 'status-stopped'}">
                            <div class="app-card-header">
                                <div class="app-icon-lg">🖥️</div>
                                <div class="app-info">
                                    <h3 class="app-name">${node.node}</h3>
                                    <p class="app-description" style="margin-top: 0.25rem; font-size: 0.75rem; opacity: 0.7;">
                                        Proxmox VE ${versionShort}
                                    </p>
                                </div>
                            </div>

                            <!-- Connection Info with Status LEDs and Details -->
                            <div class="app-connection-info">
                                <!-- Status LED with label -->
                                <div class="connection-item">
                                    <span class="status-led ${isOnline ? 'status-led-active' : 'status-led-error'}" 
                                          title="${isOnline ? 'Host Online' : 'Host Offline'}"></span>
                                    <i data-lucide="server" class="connection-icon"></i>
                                    <span class="connection-value">Status: ${isOnline ? 'Online' : 'Offline'}</span>
                                </div>
                                
                                <!-- Network LED with IP -->
                                <div class="connection-item">
                                    <span class="status-led ${isOnline ? 'status-led-blink' : 'status-led-off'}" 
                                          title="Network Activity"></span>
                                    <i data-lucide="network" class="connection-icon"></i>
                                    <span class="connection-value"> ${node.ip || 'N/A'}</span>
                                </div>
                                
                                <!-- Network TX (Upload) with LED -->
                                <div class="connection-item">
                                    <span class="status-led led-tx" 
                                          data-node="${node.node}" 
                                          data-type="tx"
                                          title="TX - Network Upload"></span>
                                    <i data-lucide="upload" class="connection-icon"></i>
                                    <span class="connection-value">TX</span>
                                </div>
                                
                                <!-- Network RX (Download) with LED -->
                                <div class="connection-item">
                                    <span class="status-led led-rx" 
                                          data-node="${node.node}" 
                                          data-type="rx"
                                          title="RX - Network Download"></span>
                                    <i data-lucide="download" class="connection-icon"></i>
                                    <span class="connection-value">RX</span>
                                </div>
                                
                                <!-- Uptime -->
                                <div class="connection-item">
                                    <i data-lucide="clock" class="connection-icon"></i>
                                    <span class="connection-value">Uptime: ${node.uptime ? formatUptime(node.uptime) : 'N/A'}</span>
                                </div>
                                
                                <!-- LXC Containers count -->
                                <div class="connection-item">
                                    <i data-lucide="box" class="connection-icon"></i>
                                    <span class="connection-value">LXCs: ${node.lxc_count || '0'}</span>
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
                                    <i data-lucide="memory-stick" class="metric-icon"></i>
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

        // Subscribe node LEDs to network activity monitor
        nodes.forEach(node => {
            const txLed = container.querySelector(`[data-node="${node.node}"][data-type="tx"]`);
            const rxLed = container.querySelector(`[data-node="${node.node}"][data-type="rx"]`);
            
            if (txLed && rxLed) {
                networkActivityMonitor.subscribe(node.node, txLed, rxLed);
            }
        });

        // Fetch public IP and geolocation info
        this.fetchPublicNetworkInfo();
    }

    /**
     * Fetch and update public IP and geolocation information
     */
    async fetchPublicNetworkInfo() {
        try {
            const publicInfo = await getPublicNetworkInfo();
            
            // Update Public IP
            const publicIpEl = document.querySelector('.public-ip-value');
            if (publicIpEl && publicInfo.public_ip) {
                publicIpEl.textContent = publicInfo.public_ip;
            } else if (publicIpEl) {
                publicIpEl.textContent = 'N/A';
            }
            
            // Update Country/Location
            const countryEl = document.querySelector('.country-value');
            const flagEl = document.querySelector('.country-flag');
            
            if (countryEl && publicInfo.country) {
                const cityPart = publicInfo.city ? `${publicInfo.city}, ` : '';
                countryEl.textContent = `${cityPart}${publicInfo.country}`;
            } else if (countryEl) {
                countryEl.textContent = 'N/A';
            }
            
            // Update flag emoji
            if (flagEl && publicInfo.flag_emoji) {
                flagEl.textContent = publicInfo.flag_emoji;
                flagEl.title = publicInfo.country || '';
            }
            
        } catch (error) {
            console.error('Failed to fetch public network info:', error);
            
            // Show error state
            const publicIpEl = document.querySelector('.public-ip-value');
            if (publicIpEl) publicIpEl.textContent = 'Error';
            
            const countryEl = document.querySelector('.country-value');
            if (countryEl) countryEl.textContent = 'Error';
        }
    }

    /**
     * Update network status LEDs based on real-time metrics
     * @param {Object} metrics - Network metrics from API
     */
    updateNetworkStatus(metrics) {
        if (!metrics || !metrics.summary) return;

        const summary = metrics.summary;

        // Update Bridge LED
        const bridgeLED = document.querySelector('.network-led-bridge');
        if (bridgeLED) {
            bridgeLED.className = 'status-led network-led-bridge ' + networkMonitor.getLEDClass('bridge');
            bridgeLED.title = `Bridge: ${networkMonitor.getStatusText('bridge')}`;
        }

        // Update DHCP LED
        const dhcpLED = document.querySelector('.network-led-dhcp');
        if (dhcpLED) {
            dhcpLED.className = 'status-led network-led-dhcp ' + networkMonitor.getLEDClass('dhcp');
            dhcpLED.title = `DHCP: ${networkMonitor.getStatusText('dhcp')}`;
        }

        // Update Gateway LED (TX/RX activity)
        const gatewayLED = document.querySelector('.network-led-gateway');
        if (gatewayLED) {
            gatewayLED.className = 'status-led network-led-gateway ' + networkMonitor.getLEDClass('gateway');
            gatewayLED.title = `Gateway: ${networkMonitor.getStatusText('gateway')} (TX/RX Activity)`;
        }

        // Update Internet LED
        const internetLED = document.querySelector('.network-led-internet');
        if (internetLED) {
            internetLED.className = 'status-led network-led-internet ' + networkMonitor.getLEDClass('internet');
            internetLED.title = `Internet: ${networkMonitor.getStatusText('internet')}`;
        }

        // Update node count text if exists
        const nodeCountEl = document.querySelector('.network-node-count');
        if (nodeCountEl) {
            nodeCountEl.textContent = networkMonitor.getStatusText('nodes');
        }
    }

    /**
     * Unmount nodes view and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Nodes View');
        
        // Stop network monitoring
        networkMonitor.stopMonitoring();
        
        // Unsubscribe from updates
        if (this.unsubscribe) {
            this.unsubscribe();
            this.unsubscribe = null;
        }
        
        super.unmount();
    }
}

// Create singleton instance
export const nodesView = new NodesView();
