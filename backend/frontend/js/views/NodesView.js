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
                                
                                <!-- Bridge Status -->
                                <div class="connection-item">
                                    <span class="status-led status-led-active network-led-bridge-host" title="Bridge Active"></span>
                                    <i data-lucide="network" class="connection-icon"></i>
                                    <span class="connection-value"> vmbr0</span>
                                </div>
                                
                                <!-- DHCP Status -->
                                <div class="connection-item">
                                    <span class="status-led status-led-pulse network-led-dhcp-host" title="DHCP Active"></span>
                                    <i data-lucide="wifi" class="connection-icon"></i>
                                    <span class="connection-value">DHCP</span>
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

                                <!-- Public IP -->
                                <div class="connection-item">
                                    <i data-lucide="globe" class="connection-icon"></i>
                                    <span class="connection-value"><span class="public-ip-value-host">Loading...</span></span>
                                </div>
                                
                                <!-- Country/Location with flag -->
                                <div class="connection-item">
                                    <i data-lucide="map-pin" class="connection-icon"></i>
                                    <span class="connection-value"><span class="country-value-host">Loading...</span></span>
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
            
            // Update Public IP in Host cards
            const publicIpHostEls = document.querySelectorAll('.public-ip-value-host');
            publicIpHostEls.forEach(el => {
                if (publicInfo.public_ip) {
                    el.textContent = publicInfo.public_ip;
                } else {
                    el.textContent = 'N/A';
                }
            });
            
            // Update Country/Location in Host cards
            const countryHostEls = document.querySelectorAll('.country-value-host');
            const flagHostEls = document.querySelectorAll('.country-flag-host');
            
            countryHostEls.forEach(el => {
                if (publicInfo.country) {
                    const cityPart = publicInfo.city ? `${publicInfo.city}, ` : '';
                    el.textContent = `${cityPart}${publicInfo.country}`;
                } else {
                    el.textContent = 'N/A';
                }
            });
            
            flagHostEls.forEach(el => {
                if (publicInfo.flag_emoji) {
                    el.textContent = publicInfo.flag_emoji;
                    el.title = publicInfo.country || '';
                }
            });
            
        } catch (error) {
            console.error('Failed to fetch public network info:', error);
            
            // Show error state in Host cards
            const publicIpHostEls = document.querySelectorAll('.public-ip-value-host');
            publicIpHostEls.forEach(el => el.textContent = 'Error');
            
            const countryHostEls = document.querySelectorAll('.country-value-host');
            countryHostEls.forEach(el => el.textContent = 'Error');
        }
    }

    /**
     * Update network status LEDs based on real-time metrics
     * @param {Object} metrics - Network metrics from API
     */
    updateNetworkStatus(metrics) {
        if (!metrics || !metrics.summary) return;

        const summary = metrics.summary;

        // Update Bridge LEDs in Host cards
        const bridgeHostLEDs = document.querySelectorAll('.network-led-bridge-host');
        bridgeHostLEDs.forEach(led => {
            led.className = 'status-led network-led-bridge-host ' + networkMonitor.getLEDClass('bridge');
            led.title = `Bridge: ${networkMonitor.getStatusText('bridge')}`;
        });

        // Update DHCP LEDs in Host cards
        const dhcpHostLEDs = document.querySelectorAll('.network-led-dhcp-host');
        dhcpHostLEDs.forEach(led => {
            led.className = 'status-led network-led-dhcp-host ' + networkMonitor.getLEDClass('dhcp');
            led.title = `DHCP: ${networkMonitor.getStatusText('dhcp')}`;
        });

        // Update Gateway LEDs in Host cards
        const gatewayHostLEDs = document.querySelectorAll('.network-led-gateway-host');
        gatewayHostLEDs.forEach(led => {
            led.className = 'status-led network-led-gateway-host ' + networkMonitor.getLEDClass('gateway');
            led.title = `Gateway: ${networkMonitor.getStatusText('gateway')}`;
        });

        // Update Internet LEDs in Host cards
        const internetHostLEDs = document.querySelectorAll('.network-led-internet-host');
        internetHostLEDs.forEach(led => {
            led.className = 'status-led network-led-internet-host ' + networkMonitor.getLEDClass('internet');
            led.title = `Internet: ${networkMonitor.getStatusText('internet')}`;
        });
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
