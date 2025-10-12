/**
 * Settings View Component
 *
 * Handles the settings view with multiple configuration panels:
 * - Proxmox connection settings
 * - Network configuration
 * - Resource defaults
 * - System information
 * - Proximity mode toggle
 * - Audio settings
 * 
 * @module views/SettingsView
 */

import { View } from '../core/View.js';
import { getState } from '../state/appState.js';
import { authFetch, API_BASE } from '../services/api.js';
import { showLoading, hideLoading } from '../utils/ui.js';
import { initLucideIcons } from '../utils/icons.js';
import { 
    setupSettingsTabs, 
    setupSettingsForms, 
    testProxmoxConnection,
    handleModeToggle 
} from '../utils/settingsHelpers.js';

export class SettingsView extends View {
    constructor() {
        super('settingsView');
        console.log('🔧 SettingsView constructor called');
    }

    /**
     * Called when the view is mounted/navigated to
     */
    async mount() {
        console.group('🔧 SettingsView.mount()');
        console.log('Container element:', this.container);
        
        try {
            await this.renderSettingsView();
        } catch (error) {
            console.error('❌ Error in SettingsView.mount():', error);
            if (this.container) {
                this.container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">❌</div>
                        <h2>Error Loading Settings</h2>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        } finally {
            console.groupEnd();
        }
    }

    /**
     * Render the settings view with all panels
     */
    async renderSettingsView() {
        console.log('🎨 Rendering Settings View');
        
        if (!this.container) {
            console.error('No container element found');
            return;
        }

        this.container.classList.remove('has-sub-nav');

        // Load settings data
        showLoading('Loading settings...');
        let proxmoxSettings = { host: '', user: '', password: '', port: 8006, verify_ssl: false };
        let networkSettings = { lan_subnet: '10.20.0.0/24', lan_gateway: '10.20.0.1', dhcp_start: '10.20.0.100', dhcp_end: '10.20.0.250', dns_domain: 'prox.local' };
        let resourceSettings = { lxc_memory: 2048, lxc_cores: 2, lxc_disk: 8, lxc_storage: 'local-lvm' };

        try {
            const token = localStorage.getItem('proximity_token');
            if (token) {
                // Load Proxmox settings
                try {
                    const proxmoxRes = await authFetch(`${API_BASE}/settings/proxmox`);
                    if (proxmoxRes.ok) {
                        proxmoxSettings = await proxmoxRes.json();
                    } else {
                        console.warn('Failed to load Proxmox settings:', proxmoxRes.status);
                    }
                } catch (err) {
                    console.warn('Error loading Proxmox settings:', err);
                }

                // Load Network settings
                try {
                    const networkRes = await authFetch(`${API_BASE}/settings/network`);
                    if (networkRes.ok) {
                        networkSettings = await networkRes.json();
                    } else {
                        console.warn('Failed to load Network settings:', networkRes.status);
                    }
                } catch (err) {
                    console.warn('Error loading Network settings:', err);
                }

                // Load Resource settings
                try {
                    const resourceRes = await authFetch(`${API_BASE}/settings/resources`);
                    if (resourceRes.ok) {
                        resourceSettings = await resourceRes.json();
                    } else {
                        console.warn('Failed to load Resource settings:', resourceRes.status);
                    }
                } catch (err) {
                    console.warn('Error loading Resource settings:', err);
                }
            } else {
                console.warn('No auth token found, using default settings');
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        } finally {
            hideLoading();
        }

        const state = getState();
        const content = this.generateSettingsHTML(proxmoxSettings, networkSettings, resourceSettings, state);

        this.container.innerHTML = content;
        this.container.classList.add('has-sub-nav');
        this.container.classList.remove('hidden');
        this.container.style.display = 'block';

        // Initialize icons
        initLucideIcons();

        // Setup tab switching
        setupSettingsTabs();

        // Setup form handlers
        setupSettingsForms();

        // Expose testProxmoxConnection to window for onclick handler
        window.testProxmoxConnection = testProxmoxConnection;
        window.handleModeToggle = handleModeToggle;

        console.log('✅ Settings view rendered successfully');
    }

    /**
     * Generate the complete settings HTML
     */
    generateSettingsHTML(proxmoxSettings, networkSettings, resourceSettings, state) {
        return `
        <!-- Settings Sub-Navigation -->
        <div class="sub-nav">
            <button class="settings-tab sub-nav-item active" data-tab="proxmox">
                <i data-lucide="server"></i>
                <span>Proxmox</span>
            </button>
            <button class="settings-tab sub-nav-item" data-tab="network">
                <i data-lucide="network"></i>
                <span>Network</span>
            </button>
            <button class="settings-tab sub-nav-item" data-tab="resources">
                <i data-lucide="cpu"></i>
                <span>Resources</span>
            </button>
            <button class="settings-tab sub-nav-item" data-tab="system">
                <i data-lucide="info"></i>
                <span>System</span>
            </button>
        </div>

        <div class="settings-content">
            <!-- Proxmox Settings -->
            <div class="settings-panel active" id="proxmox-panel">
                <div class="app-card">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="server"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Proxmox Connection</h3>
                            <p>Configure connection to your Proxmox VE server</p>
                        </div>
                    </div>

                    <form id="proxmoxForm" class="settings-form">
                        <div class="form-group">
                            <label class="form-label">Host</label>
                            <input type="text" class="form-input" name="host" value="${proxmoxSettings.host || ''}" placeholder="192.168.1.100" required>
                            <small class="form-help">IP address or hostname of your Proxmox server</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Port</label>
                            <input type="number" class="form-input" name="port" value="${proxmoxSettings.port || 8006}" required>
                            <small class="form-help">Proxmox web interface port (default: 8006)</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Username</label>
                            <input type="text" class="form-input" name="user" value="${proxmoxSettings.user || ''}" placeholder="root@pam" required>
                            <small class="form-help">Proxmox username (e.g., root@pam)</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input type="password" class="form-input" name="password" value="${proxmoxSettings.password || ''}" placeholder="${proxmoxSettings.password === '******' ? 'Leave unchanged' : 'Enter password'}">
                            <small class="form-help">Password is encrypted before storage. Leave blank to keep current password.</small>
                        </div>

                        <div class="form-group">
                            <label class="form-checkbox">
                                <input type="checkbox" name="verify_ssl" ${proxmoxSettings.verify_ssl ? 'checked' : ''}>
                                <span>Verify SSL Certificate</span>
                            </label>
                            <small class="form-help">Disable for self-signed certificates</small>
                        </div>

                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="testProxmoxConnection()">
                                <i data-lucide="check-circle"></i>
                                <span>Test Connection</span>
                            </button>
                            <button type="submit" class="btn btn-primary">
                                <i data-lucide="save"></i>
                                <span>Save Settings</span>
                            </button>
                        </div>

                        <div id="proxmoxStatus" style="margin-top: 1rem;"></div>
                    </form>
                </div>
            </div>

            <!-- Network Settings -->
            <div class="settings-panel" id="network-panel">
                <div class="app-card">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="network"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Network Configuration</h3>
                            <p>Configure network settings for deployed applications</p>
                        </div>
                    </div>

                    <form id="networkForm" class="settings-form">
                        <div class="form-group">
                            <label class="form-label">LAN Subnet</label>
                            <input type="text" class="form-input" name="lan_subnet" value="${networkSettings.lan_subnet || '10.20.0.0/24'}" required>
                            <small class="form-help">Private network subnet in CIDR notation</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Gateway IP</label>
                            <input type="text" class="form-input" name="lan_gateway" value="${networkSettings.lan_gateway || '10.20.0.1'}" required>
                            <small class="form-help">Network gateway IP address</small>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">DHCP Start</label>
                                <input type="text" class="form-input" name="dhcp_start" value="${networkSettings.dhcp_start || '10.20.0.100'}" required>
                            </div>

                            <div class="form-group">
                                <label class="form-label">DHCP End</label>
                                <input type="text" class="form-input" name="dhcp_end" value="${networkSettings.dhcp_end || '10.20.0.250'}" required>
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label">DNS Domain</label>
                            <input type="text" class="form-input" name="dns_domain" value="${networkSettings.dns_domain || 'prox.local'}" required>
                            <small class="form-help">Local DNS domain suffix (e.g., prox.local)</small>
                        </div>

                        <div class="alert warning" style="margin-bottom: 1.5rem;">
                            <span class="alert-icon">⚠️</span>
                            <div class="alert-content">
                                <div class="alert-message">Network changes only apply to newly deployed apps. Existing apps retain their current configuration.</div>
                            </div>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                <i data-lucide="save"></i>
                                <span>Save Settings</span>
                            </button>
                        </div>

                        <div id="networkStatus" style="margin-top: 1rem;"></div>
                    </form>
                </div>
            </div>

            <!-- Resource Settings -->
            <div class="settings-panel" id="resources-panel">
                <div class="app-card">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="cpu"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Default Resources</h3>
                            <p>Set default resource allocations for new LXC containers</p>
                        </div>
                    </div>

                    <form id="resourcesForm" class="settings-form">
                        <div class="form-group">
                            <label class="form-label">Memory (MB)</label>
                            <input type="number" class="form-input" name="lxc_memory" value="${resourceSettings.lxc_memory || 2048}" min="512" step="512" required>
                            <small class="form-help">Default RAM allocation in megabytes</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">CPU Cores</label>
                            <input type="number" class="form-input" name="lxc_cores" value="${resourceSettings.lxc_cores || 2}" min="1" max="32" required>
                            <small class="form-help">Number of CPU cores to allocate</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Disk Size (GB)</label>
                            <input type="number" class="form-input" name="lxc_disk" value="${resourceSettings.lxc_disk || 8}" min="4" step="1" required>
                            <small class="form-help">Root disk size in gigabytes</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Storage Pool</label>
                            <input type="text" class="form-input" name="lxc_storage" value="${resourceSettings.lxc_storage || 'local-lvm'}" required>
                            <small class="form-help">Proxmox storage pool for container disks</small>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                <i data-lucide="save"></i>
                                <span>Save Settings</span>
                            </button>
                        </div>

                        <div id="resourcesStatus" style="margin-top: 1rem;"></div>
                    </form>
                </div>
            </div>

            <!-- System Settings -->
            <div class="settings-panel" id="system-panel">
                <div class="app-card">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="info"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>System Information</h3>
                            <p>Platform status and configuration details</p>
                        </div>
                    </div>
                    <div class="app-meta">
                        <div class="app-meta-item">
                            <span>📌</span>
                            <span>Version: ${state.systemInfo?.version || 'N/A'}</span>
                        </div>
                        <div class="app-meta-item">
                            <span>🔗</span>
                            <span>API: ${API_BASE}</span>
                        </div>
                    </div>
                    <div class="app-meta" style="margin-top: 1rem;">
                        <div class="app-meta-item">
                            <span>🖥️</span>
                            <span>Nodes: ${state.nodes.length}</span>
                        </div>
                        <div class="app-meta-item">
                            <span>📦</span>
                            <span>Apps: ${state.deployedApps.length}</span>
                        </div>
                    </div>
                </div>

                <!-- Proximity Mode Toggle -->
                <div class="app-card" style="margin-top: 1.5rem;">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="zap"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Proximity Mode</h3>
                            <p>Choose between automated or professional control</p>
                        </div>
                    </div>

                    <div class="mode-toggle">
                        <div class="mode-toggle-label">
                            <h3>Current Mode: <span class="mode-badge ${(state.proximityMode || 'AUTO').toLowerCase()}" id="current-mode-badge">
                                <i data-lucide="${(state.proximityMode || 'AUTO') === 'AUTO' ? 'zap' : 'wrench'}"></i>
                                ${state.proximityMode || 'AUTO'}
                            </span></h3>
                            <p>Switch between AUTO (automated) and PRO (professional control) modes</p>
                        </div>
                        <label class="mode-toggle-switch">
                            <input type="checkbox" id="modeToggleInput" ${(state.proximityMode || 'AUTO') === 'PRO' ? 'checked' : ''} onchange="handleModeToggle(this)">
                            <div class="mode-toggle-slider">${(state.proximityMode || 'AUTO') === 'AUTO' ? 'AUTO' : 'PRO'}</div>
                        </label>
                    </div>

                    <div class="mode-description">
                        <div class="mode-card ${(state.proximityMode || 'AUTO') === 'AUTO' ? 'active' : ''}" id="auto-mode-card">
                            <h4>
                                <i data-lucide="zap" style="width: 16px; height: 16px;"></i>
                                AUTO Mode
                            </h4>
                            <ul>
                                <li>Daily automated backups</li>
                                <li>Automatic update notifications</li>
                                <li>Simplified interface</li>
                                <li>Hands-free operation</li>
                            </ul>
                        </div>
                        <div class="mode-card ${(state.proximityMode || 'AUTO') === 'PRO' ? 'active' : ''}" id="pro-mode-card">
                            <h4>
                                <i data-lucide="wrench" style="width: 16px; height: 16px;"></i>
                                PRO Mode
                            </h4>
                            <ul>
                                <li>Manual backup control</li>
                                <li>Clone applications</li>
                                <li>Edit resource configurations</li>
                                <li>Full professional control</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="app-card" style="margin-top: 1.5rem;">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="shield"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Security</h3>
                            <p>Authentication and access control settings</p>
                        </div>
                    </div>

                    <div class="alert info">
                        <span class="alert-icon">🔐</span>
                        <div class="alert-content">
                            <div class="alert-title">Authentication Enabled</div>
                            <div class="alert-message">All API endpoints are protected with JWT authentication. Sensitive data is encrypted at rest.</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
    }

    /**
     * Called when the view is unmounted/navigated away from
     */
    unmount() {
        console.log('🔧 SettingsView.unmount()');
        
        // Clean up window functions
        delete window.testProxmoxConnection;
        delete window.handleModeToggle;
        
        if (this.container) {
            this.container.classList.add('hidden');
            this.container.style.display = 'none';
        }
    }
}
