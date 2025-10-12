/**
 * Config Service
 * 
 * Provides configuration and cloning functionality for applications.
 * Handles resource updates, app cloning, and configuration modals.
 * 
 * Features:
 * - Clone applications
 * - Edit resource config (CPU, memory, disk)
 * - Show/hide config modal
 * - Config validation
 * - Prompt modal for user input
 * 
 * @module configService
 */

/**
 * Get API base URL
 * @returns {string} API base URL
 */
function getAPIBase() {
    return window.API_BASE || '/api/v1';
}

/**
 * Get auth token
 * @returns {string} Auth token
 */
function getToken() {
    return window.getToken ? window.getToken() : localStorage.getItem('token');
}

/**
 * Show notification
 */
function notify(message, type = 'info') {
    if (window.showNotification) {
        window.showNotification(message, type);
    } else {
        console.log(`[${type}] ${message}`);
    }
}

/**
 * Get current view
 */
function getCurrentView() {
    return window.currentView || 'dashboard';
}

/**
 * Load apps function
 */
async function reloadApps() {
    if (window.dataService && window.dataService.loadDeployedApps) {
        await window.dataService.loadDeployedApps();
    } else if (window.loadApps) {
        await window.loadApps();
    }
}

/**
 * Show prompt modal for text input
 * Creates a modal dialog with text input and returns user's input
 * 
 * @param {string} title - Modal title
 * @param {string} message - Prompt message
 * @param {string} defaultValue - Default input value
 * @param {string} confirmText - Confirm button text
 * @param {string} inputId - Input element ID
 * @returns {Promise<string|null>} User input or null if cancelled
 */
export function showPromptModal(title, message, defaultValue = '', confirmText = 'OK', inputId = 'promptInput') {
    return new Promise((resolve) => {
        const modalHTML = `
            <div class="modal-overlay" id="promptOverlay">
                <div class="modal-dialog">
                    <div class="modal-header">
                        <h2>${title}</h2>
                        <button class="modal-close" onclick="document.getElementById('promptOverlay').remove(); window.promptResolve(null);">✕</button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                        <input type="text" id="${inputId}" class="form-control" value="${defaultValue}"
                               onkeypress="if(event.key==='Enter') document.getElementById('promptConfirm').click()">
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="document.getElementById('promptOverlay').remove(); window.promptResolve(null);">
                            Cancel
                        </button>
                        <button id="promptConfirm" class="btn btn-primary" onclick="
                            const val = document.getElementById('${inputId}').value.trim();
                            document.getElementById('promptOverlay').remove();
                            window.promptResolve(val);
                        ">${confirmText}</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        window.promptResolve = resolve;

        setTimeout(() => {
            const input = document.getElementById(inputId);
            if (input) {
                input.focus();
                input.select();
            }
        }, 100);
    });
}

/**
 * Clone an application
 * Creates a copy of an app with a new hostname
 * 
 * @param {string} appId - Application ID to clone
 * @param {string} appName - Application name (for display)
 * @returns {Promise<Object>} Cloned app object
 */
export async function cloneApp(appId, appName) {
    const hostname = await showPromptModal(
        'Clone Application',
        `Enter a new hostname for the cloned copy of "${appName}":`,
        '',
        'Clone',
        'clone-hostname'
    );

    if (!hostname) return null;

    try {
        notify(`Cloning ${appName}...`, 'info');

        const response = await fetch(`${getAPIBase()}/apps/${appId}/clone?new_hostname=${encodeURIComponent(hostname)}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Clone failed');
        }

        const clonedApp = await response.json();

        notify(`✓ Successfully cloned to ${hostname}`, 'success');

        // Refresh apps view
        if (getCurrentView() === 'apps') {
            await reloadApps();
        }

        return clonedApp;

    } catch (error) {
        console.error('Clone error:', error);
        notify(`Failed to clone: ${error.message}`, 'error');
        throw error;
    }
}

/**
 * Show clone modal
 * Wrapper for cloneApp with legacy name
 * 
 * @param {string} appId - Application ID
 * @param {string} appName - Application name
 * @returns {Promise<Object>} Cloned app object
 */
export async function showCloneModal(appId, appName) {
    return cloneApp(appId, appName);
}

/**
 * Show edit config modal
 * Opens modal for editing resource configuration
 * 
 * @param {string} appId - Application ID
 * @param {string} appName - Application name
 */
export async function showEditConfigModal(appId, appName) {
    // Create modal HTML
    const modalHTML = `
        <div class="modal-overlay" id="editConfigOverlay">
            <div class="modal-dialog">
                <div class="modal-header">
                    <h2>Edit Resources: ${appName}</h2>
                    <button class="modal-close" onclick="window.configService.closeEditConfigModal()">✕</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="editCpu">CPU Cores (1-16)</label>
                        <input type="number" id="editCpu" min="1" max="16" step="1"
                               placeholder="Leave empty to keep current">
                    </div>
                    <div class="form-group">
                        <label for="editMemory">Memory (MB) (512-32768)</label>
                        <input type="number" id="editMemory" min="512" max="32768" step="512"
                               placeholder="Leave empty to keep current">
                    </div>
                    <div class="form-group">
                        <label for="editDisk">Disk Size (GB) (1-500)</label>
                        <input type="number" id="editDisk" min="1" max="500" step="1"
                               placeholder="Leave empty to keep current">
                        <small class="form-help">⚠️ Disk can only be increased, not decreased</small>
                    </div>
                    <div class="alert alert-warning">
                        <strong>Note:</strong> The application will be restarted to apply changes.
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="window.configService.closeEditConfigModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="window.configService.submitEditConfig('${appId}', '${appName}')">
                        Apply Changes
                    </button>
                </div>
            </div>
        </div>
    `;

    // Add to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Focus first input
    setTimeout(() => document.getElementById('editCpu')?.focus(), 100);
}

/**
 * Close edit config modal
 * Removes modal from DOM
 */
export function closeEditConfigModal() {
    const overlay = document.getElementById('editConfigOverlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Validate config values
 * Checks if values are within allowed ranges
 * 
 * @param {Object} config - Config object
 * @param {number} config.cpuCores - CPU cores
 * @param {number} config.memoryMb - Memory in MB
 * @param {number} config.diskGb - Disk in GB
 * @returns {Object} Validation result with isValid and errors
 */
export function validateConfig(config) {
    const errors = [];
    
    if (config.cpuCores !== undefined && config.cpuCores !== null) {
        const cpu = parseInt(config.cpuCores);
        if (isNaN(cpu) || cpu < 1 || cpu > 16) {
            errors.push('CPU cores must be between 1 and 16');
        }
    }
    
    if (config.memoryMb !== undefined && config.memoryMb !== null) {
        const mem = parseInt(config.memoryMb);
        if (isNaN(mem) || mem < 512 || mem > 32768) {
            errors.push('Memory must be between 512 and 32768 MB');
        }
    }
    
    if (config.diskGb !== undefined && config.diskGb !== null) {
        const disk = parseInt(config.diskGb);
        if (isNaN(disk) || disk < 1 || disk > 500) {
            errors.push('Disk size must be between 1 and 500 GB');
        }
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
}

/**
 * Update application config
 * Updates resource configuration (CPU, memory, disk)
 * 
 * @param {string} appId - Application ID
 * @param {Object} config - Config object
 * @param {number} config.cpuCores - CPU cores (optional)
 * @param {number} config.memoryMb - Memory in MB (optional)
 * @param {number} config.diskGb - Disk in GB (optional)
 * @returns {Promise<void>}
 */
export async function updateConfig(appId, config) {
    // Validate config
    const validation = validateConfig(config);
    if (!validation.isValid) {
        throw new Error(validation.errors.join(', '));
    }

    // Build query params
    const params = new URLSearchParams();
    if (config.cpuCores) params.append('cpu_cores', config.cpuCores);
    if (config.memoryMb) params.append('memory_mb', config.memoryMb);
    if (config.diskGb) params.append('disk_gb', config.diskGb);

    const response = await fetch(`${getAPIBase()}/apps/${appId}/config?${params.toString()}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${getToken()}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Config update failed');
    }

    return response.json();
}

/**
 * Submit config update from modal
 * Reads form values, validates, and updates config
 * 
 * @param {string} appId - Application ID
 * @param {string} appName - Application name (for display)
 * @returns {Promise<void>}
 */
export async function submitEditConfig(appId, appName) {
    const cpuCores = document.getElementById('editCpu')?.value;
    const memoryMb = document.getElementById('editMemory')?.value;
    const diskGb = document.getElementById('editDisk')?.value;

    // Validate at least one field is set
    if (!cpuCores && !memoryMb && !diskGb) {
        notify('Please specify at least one resource to update', 'warning');
        return;
    }

    try {
        closeEditConfigModal();
        notify(`Updating resources for ${appName}...`, 'info');

        await updateConfig(appId, {
            cpuCores: cpuCores || null,
            memoryMb: memoryMb || null,
            diskGb: diskGb || null
        });

        notify(`✓ Resources updated successfully`, 'success');

        // Refresh apps view
        if (getCurrentView() === 'apps') {
            await reloadApps();
        }

    } catch (error) {
        console.error('Config update error:', error);
        notify(`Failed to update config: ${error.message}`, 'error');
    }
}

/**
 * Get current config for an app
 * Fetches current resource configuration
 * 
 * @param {string} appId - Application ID
 * @returns {Promise<Object>} Config object
 */
export async function getConfig(appId) {
    const response = await fetch(`${getAPIBase()}/apps/${appId}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${getToken()}`
        }
    });

    if (!response.ok) {
        throw new Error('Failed to get config');
    }

    const app = await response.json();
    return {
        cpuCores: app.cpu_cores,
        memoryMb: app.memory_mb,
        diskGb: app.disk_gb
    };
}

// Backward compatibility: Expose to window
if (typeof window !== 'undefined') {
    window.configService = {
        showPromptModal,
        cloneApp,
        showCloneModal,
        showEditConfigModal,
        closeEditConfigModal,
        validateConfig,
        updateConfig,
        submitEditConfig,
        getConfig
    };
}
