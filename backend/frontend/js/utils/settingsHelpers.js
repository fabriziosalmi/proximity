/**
 * Settings Helpers Module
 *
 * Helper functions for the Settings view including:
 * - Form submission handlers
 * - Tab switching
 * - Network validation
 * - Audio controls
 * - Mode toggling
 *
 * @module utils/settingsHelpers
 */

import { authFetch, API_BASE } from '../services/api.js';
import { showLoading, hideLoading } from './ui.js';
import { showNotification } from './notifications.js';
import { setState, getState } from '../state/appState.js';

/**
 * Setup settings tabs event listeners
 */
export function setupSettingsTabs() {
    console.log('🔧 Setting up settings tabs');
    const tabs = document.querySelectorAll('.settings-tab[data-tab]');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const tabName = tab.getAttribute('data-tab');
            console.log('📑 Switching to tab:', tabName);
            activateSettingsTab(tabName);
        });
    });
}

/**
 * Activate a specific settings tab
 * @param {string} tabName - Name of the tab to activate
 */
function activateSettingsTab(tabName) {
    // Remove active class from all tabs
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.settings-panel').forEach(p => p.classList.remove('active'));
    
    // Add active class to selected tab and panel
    const selectedTab = document.querySelector(`.settings-tab[data-tab="${tabName}"]`);
    const selectedPanel = document.getElementById(`${tabName}-panel`);
    
    if (selectedTab) selectedTab.classList.add('active');
    if (selectedPanel) selectedPanel.classList.add('active');
}

/**
 * Setup all settings forms with validation and submission handlers
 */
export function setupSettingsForms() {
    console.log('🔧 Setting up settings forms');
    
    // Setup Proxmox form
    const proxmoxForm = document.getElementById('proxmoxForm');
    if (proxmoxForm) {
        proxmoxForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveProxmoxSettings(new FormData(proxmoxForm));
        });
    }

    // Setup Network form with validation
    const networkForm = document.getElementById('networkForm');
    if (networkForm) {
        setupNetworkFormValidation(networkForm);
        networkForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveNetworkSettings(new FormData(networkForm));
        });
    }

    // Setup Resources form
    const resourcesForm = document.getElementById('resourcesForm');
    if (resourcesForm) {
        resourcesForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveResourceSettings(new FormData(resourcesForm));
        });
    }

    // Setup audio settings
    setupAudioSettings();
}

/**
 * Setup network form validation (IP ranges, subnets, etc.)
 * @param {HTMLFormElement} networkForm - Network form element
 */
function setupNetworkFormValidation(networkForm) {
    const subnetInput = networkForm.querySelector('[name="lan_subnet"]');
    const gatewayInput = networkForm.querySelector('[name="lan_gateway"]');
    const dhcpStartInput = networkForm.querySelector('[name="dhcp_start"]');
    const dhcpEndInput = networkForm.querySelector('[name="dhcp_end"]');

    // Helper: Convert IP to number for comparison
    const ipToNumber = (ip) => {
        const parts = ip.split('.');
        return (parseInt(parts[0]) << 24) + (parseInt(parts[1]) << 16) + 
               (parseInt(parts[2]) << 8) + parseInt(parts[3]);
    };

    // Helper: Check if IP is in subnet
    const isIpInSubnet = (ip, cidr) => {
        const [subnet, maskBits] = cidr.split('/');
        const mask = parseInt(maskBits);
        const maskNum = (0xFFFFFFFF << (32 - mask)) >>> 0;
        const ipNum = ipToNumber(ip);
        const subnetNum = ipToNumber(subnet);
        return (ipNum & maskNum) === (subnetNum & maskNum);
    };

    // Validate gateway is in subnet
    if (gatewayInput && subnetInput) {
        const validateGateway = () => {
            const gateway = gatewayInput.value.trim();
            const subnet = subnetInput.value.trim();
            
            if (!gateway || !subnet) return;
            
            const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
            const cidrPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([0-9]|[1-2][0-9]|3[0-2])$/;
            
            if (!ipPattern.test(gateway) || !cidrPattern.test(subnet)) return;
            
            if (!isIpInSubnet(gateway, subnet)) {
                gatewayInput.setCustomValidity(`Gateway IP must be within subnet ${subnet}`);
            } else {
                gatewayInput.setCustomValidity('');
            }
        };

        gatewayInput.addEventListener('blur', validateGateway);
        subnetInput.addEventListener('blur', validateGateway);
    }

    // Validate DHCP range
    if (dhcpStartInput && dhcpEndInput && subnetInput) {
        const validateDhcpRange = () => {
            const start = dhcpStartInput.value.trim();
            const end = dhcpEndInput.value.trim();
            const subnet = subnetInput.value.trim();
            
            if (!start || !end || !subnet) return;
            
            const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
            const cidrPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([0-9]|[1-2][0-9]|3[0-2])$/;
            
            if (!ipPattern.test(start) || !ipPattern.test(end) || !cidrPattern.test(subnet)) return;
            
            const startNum = ipToNumber(start);
            const endNum = ipToNumber(end);
            
            if (startNum >= endNum) {
                dhcpEndInput.setCustomValidity('DHCP end must be greater than DHCP start');
                return;
            } else {
                dhcpEndInput.setCustomValidity('');
            }
            
            if (!isIpInSubnet(start, subnet)) {
                dhcpStartInput.setCustomValidity(`DHCP start must be within subnet ${subnet}`);
            } else {
                dhcpStartInput.setCustomValidity('');
            }
            
            if (!isIpInSubnet(end, subnet)) {
                dhcpEndInput.setCustomValidity(`DHCP end must be within subnet ${subnet}`);
            } else if (dhcpEndInput.validity.valid) {
                dhcpEndInput.setCustomValidity('');
            }
        };

        dhcpStartInput.addEventListener('blur', validateDhcpRange);
        dhcpEndInput.addEventListener('blur', validateDhcpRange);
        subnetInput.addEventListener('blur', validateDhcpRange);
    }
}

/**
 * Save Proxmox settings
 * @param {FormData} formData - Form data from Proxmox form
 */
async function saveProxmoxSettings(formData) {
    const statusDiv = document.getElementById('proxmoxStatus');
    const token = localStorage.getItem('proximity_token');

    if (!token) {
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Not authenticated. Please log in.</div>
                </div>
            </div>
        `;
        return;
    }

    const data = {
        host: formData.get('host'),
        port: parseInt(formData.get('port')),
        user: formData.get('user'),
        password: formData.get('password') || '******',
        verify_ssl: formData.get('verify_ssl') === 'on'
    };

    try {
        showLoading('Saving Proxmox settings...');

        const response = await authFetch(`${API_BASE}/settings/proxmox`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        hideLoading();

        if (response.ok) {
            statusDiv.innerHTML = `
                <div class="alert success">
                    <span class="alert-icon">✅</span>
                    <div class="alert-content">
                        <div class="alert-title">Settings Saved</div>
                        <div class="alert-message">${result.message || 'Proxmox settings updated successfully'}</div>
                    </div>
                </div>
            `;
            showNotification('Proxmox settings saved successfully', 'success');
        } else {
            statusDiv.innerHTML = `
                <div class="alert error">
                    <span class="alert-icon">❌</span>
                    <div class="alert-content">
                        <div class="alert-title">Error</div>
                        <div class="alert-message">${result.error || 'Failed to save settings'}</div>
                    </div>
                </div>
            `;
            showNotification('Failed to save Proxmox settings', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error saving Proxmox settings:', error);
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Network error: ${error.message}</div>
                </div>
            </div>
        `;
        showNotification('Failed to save Proxmox settings', 'error');
    }
}

/**
 * Test Proxmox connection
 */
export async function testProxmoxConnection() {
    const statusDiv = document.getElementById('proxmoxStatus');
    const token = localStorage.getItem('proximity_token');

    if (!token) {
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Not authenticated. Please log in.</div>
                </div>
            </div>
        `;
        return;
    }

    try {
        showLoading('Testing Proxmox connection...');

        const response = await authFetch(`${API_BASE}/system/info`);
        hideLoading();

        if (response.ok) {
            const data = await response.json();
            statusDiv.innerHTML = `
                <div class="alert success">
                    <span class="alert-icon">✅</span>
                    <div class="alert-content">
                        <div class="alert-title">Connection Successful</div>
                        <div class="alert-message">Connected to Proxmox cluster: ${data.cluster_name || 'Default'}</div>
                    </div>
                </div>
            `;
            showNotification('Proxmox connection test successful', 'success');
        } else {
            statusDiv.innerHTML = `
                <div class="alert error">
                    <span class="alert-icon">❌</span>
                    <div class="alert-content">
                        <div class="alert-title">Connection Failed</div>
                        <div class="alert-message">Unable to connect to Proxmox server. Check your credentials and network.</div>
                    </div>
                </div>
            `;
            showNotification('Proxmox connection test failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error testing Proxmox connection:', error);
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Network error: ${error.message}</div>
                </div>
            </div>
        `;
        showNotification('Proxmox connection test failed', 'error');
    }
}

/**
 * Save network settings
 * @param {FormData} formData - Form data from network form
 */
async function saveNetworkSettings(formData) {
    const statusDiv = document.getElementById('networkStatus');
    const token = localStorage.getItem('proximity_token');

    if (!token) {
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Not authenticated. Please log in.</div>
                </div>
            </div>
        `;
        return;
    }

    const data = {
        lan_subnet: formData.get('lan_subnet'),
        lan_gateway: formData.get('lan_gateway'),
        dhcp_start: formData.get('dhcp_start'),
        dhcp_end: formData.get('dhcp_end'),
        dns_domain: formData.get('dns_domain')
    };

    try {
        showLoading('Saving network settings...');

        const response = await authFetch(`${API_BASE}/settings/network`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        hideLoading();

        if (response.ok) {
            statusDiv.innerHTML = `
                <div class="alert success">
                    <span class="alert-icon">✅</span>
                    <div class="alert-content">
                        <div class="alert-title">Settings Saved</div>
                        <div class="alert-message">${result.message || 'Network settings updated successfully'}</div>
                    </div>
                </div>
            `;
            showNotification('Network settings saved successfully', 'success');
        } else {
            statusDiv.innerHTML = `
                <div class="alert error">
                    <span class="alert-icon">❌</span>
                    <div class="alert-content">
                        <div class="alert-title">Error</div>
                        <div class="alert-message">${result.error || 'Failed to save settings'}</div>
                    </div>
                </div>
            `;
            showNotification('Failed to save network settings', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error saving network settings:', error);
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Network error: ${error.message}</div>
                </div>
            </div>
        `;
        showNotification('Failed to save network settings', 'error');
    }
}

/**
 * Save resource settings
 * @param {FormData} formData - Form data from resources form
 */
async function saveResourceSettings(formData) {
    const statusDiv = document.getElementById('resourcesStatus');
    const token = localStorage.getItem('proximity_token');

    if (!token) {
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Not authenticated. Please log in.</div>
                </div>
            </div>
        `;
        return;
    }

    const data = {
        lxc_memory: parseInt(formData.get('lxc_memory')),
        lxc_cores: parseInt(formData.get('lxc_cores')),
        lxc_disk: parseInt(formData.get('lxc_disk')),
        lxc_storage: formData.get('lxc_storage')
    };

    try {
        showLoading('Saving resource settings...');

        const response = await authFetch(`${API_BASE}/settings/resources`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        hideLoading();

        if (response.ok) {
            statusDiv.innerHTML = `
                <div class="alert success">
                    <span class="alert-icon">✅</span>
                    <div class="alert-content">
                        <div class="alert-title">Settings Saved</div>
                        <div class="alert-message">${result.message || 'Resource settings updated successfully'}</div>
                    </div>
                </div>
            `;
            showNotification('Resource settings saved successfully', 'success');
        } else {
            statusDiv.innerHTML = `
                <div class="alert error">
                    <span class="alert-icon">❌</span>
                    <div class="alert-content">
                        <div class="alert-title">Error</div>
                        <div class="alert-message">${result.error || 'Failed to save settings'}</div>
                    </div>
                </div>
            `;
            showNotification('Failed to save resource settings', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error saving resource settings:', error);
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Network error: ${error.message}</div>
                </div>
            </div>
        `;
        showNotification('Failed to save resource settings', 'error');
    }
}

/**
 * Setup audio settings controls
 */
function setupAudioSettings() {
    if (!window.SoundService) {
        console.warn('SoundService not available');
        return;
    }

    // Volume slider
    const volumeSlider = document.getElementById('settingsVolumeSlider');
    const volumeValue = document.getElementById('settingsVolumeValue');
    if (volumeSlider && volumeValue) {
        volumeSlider.addEventListener('input', (e) => {
            const volume = parseInt(e.target.value) / 100;
            window.SoundService.setVolume(volume);
            volumeValue.textContent = `${e.target.value}%`;
        });

        volumeSlider.addEventListener('change', () => {
            if (!window.SoundService.getMute()) {
                window.SoundService.play('click');
            }
        });
    }

    // Mute toggle
    const muteToggle = document.getElementById('settingsMuteToggle');
    if (muteToggle) {
        muteToggle.addEventListener('change', (e) => {
            window.SoundService.setMute(e.target.checked);
        });
    }

    // Preset buttons
    const presetButtons = document.querySelectorAll('.preset-btn[data-preset]');
    presetButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const preset = btn.getAttribute('data-preset');
            let volume = 0.7; // standard
            
            if (preset === 'minimal') volume = 0.3;
            else if (preset === 'immersive') volume = 1.0;
            
            window.SoundService.setVolume(volume);
            window.SoundService.setPreset(preset);
            
            // Update UI
            if (volumeSlider) volumeSlider.value = Math.round(volume * 100);
            if (volumeValue) volumeValue.textContent = `${Math.round(volume * 100)}%`;
            
            presetButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Play test sound
            if (!window.SoundService.getMute()) {
                window.SoundService.play('click');
            }
        });
    });

    // Test sound button
    const testSoundBtn = document.getElementById('testSoundBtn');
    if (testSoundBtn) {
        testSoundBtn.addEventListener('click', () => {
            window.SoundService.play('notification');
        });
    }
}

/**
 * Handle proximity mode toggle
 * @param {HTMLInputElement} checkbox - Mode toggle checkbox
 */
export function handleModeToggle(checkbox) {
    const newMode = checkbox.checked ? 'PRO' : 'AUTO';
    console.log('🔄 Switching mode to:', newMode);

    // Update state
    setState('proximityMode', newMode);
    localStorage.setItem('proximityMode', newMode);
    document.body.classList.toggle('pro-mode', newMode === 'PRO');

    // Update slider text
    const slider = checkbox.nextElementSibling;
    if (slider) {
        slider.textContent = newMode;
    }

    // Update badge
    const badge = document.getElementById('current-mode-badge');
    if (badge) {
        badge.className = `mode-badge ${newMode.toLowerCase()}`;
        badge.innerHTML = `
            <i data-lucide="${newMode === 'AUTO' ? 'zap' : 'wrench'}"></i>
            ${newMode}
        `;
        if (window.lucide && window.lucide.createIcons) {
            window.lucide.createIcons();
        }
    }

    // Update mode cards
    const autoCard = document.getElementById('auto-mode-card');
    const proCard = document.getElementById('pro-mode-card');
    if (autoCard && proCard) {
        autoCard.classList.toggle('active', newMode === 'AUTO');
        proCard.classList.toggle('active', newMode === 'PRO');
    }

    showNotification(`Switched to ${newMode} mode`, 'success');
}
