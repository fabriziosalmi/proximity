/**
 * API Service Layer
 *
 * Centralized API communication layer for Proximity.
 * Handles all HTTP requests to the backend API.
 */

export const API_BASE = 'http://localhost:8765/api/v1';
const TOKEN_KEY = 'proximity_token';

/**
 * Get authentication token from localStorage
 * @returns {string|null} JWT token
 */
function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * Check if user is authenticated
 * @returns {boolean} True if token exists
 */
export function isAuthenticated() {
    return !!getToken();
}

/**
 * Authenticated fetch wrapper
 * Automatically includes JWT token in Authorization header
 * @param {string} url - API endpoint URL
 * @param {object} options - Fetch options
 * @returns {Promise<Response>} Fetch response
 */
export async function authFetch(url, options = {}) {
    const token = getToken();
    if (!token) {
        throw new Error('No authentication token found');
    }

    const defaultOptions = {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    const response = await fetch(url, defaultOptions);

    // Handle unauthorized responses
    if (response.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        window.location.reload();
        throw new Error('Authentication expired');
    }

    return response;
}

// ============================================================================
// AUTH API
// ============================================================================

/**
 * Register new user
 * @param {string} username - Username
 * @param {string} email - Email
 * @param {string} password - Password
 * @returns {Promise<object>} User data with token
 */
export async function register(username, email, password) {
    const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
    }

    return await response.json();
}

/**
 * Login user
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Promise<object>} User data with token
 */
export async function login(username, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
    }

    return await response.json();
}

/**
 * Logout user
 * @returns {Promise<void>}
 */
export async function logout() {
    await authFetch(`${API_BASE}/auth/logout`, { method: 'POST' });
    localStorage.removeItem(TOKEN_KEY);
}

/**
 * Get current user information
 * @returns {Promise<object>} User data
 */
export async function fetchUserInfo() {
    const response = await authFetch(`${API_BASE}/auth/me`);
    if (!response.ok) throw new Error('Failed to fetch user info');
    return await response.json();
}

// ============================================================================
// SYSTEM API
// ============================================================================

/**
 * Get system information
 * @returns {Promise<object>} System info
 */
export async function getSystemInfo() {
    const response = await authFetch(`${API_BASE}/system/info`);
    if (!response.ok) throw new Error('Failed to fetch system info');
    return await response.json();
}

/**
 * Get Proxmox nodes
 * @returns {Promise<array>} List of nodes
 */
export async function getNodes() {
    const response = await authFetch(`${API_BASE}/system/nodes`);
    if (!response.ok) throw new Error('Failed to fetch nodes');
    return await response.json();
}

/**
 * Get proxy status
 * @returns {Promise<object>} Proxy status
 */
export async function getProxyStatus() {
    const response = await authFetch(`${API_BASE}/system/proxy/status`);
    if (!response.ok) throw new Error('Failed to fetch proxy status');
    return await response.json();
}

/**
 * Get infrastructure status
 * @returns {Promise<object>} Infrastructure status
 */
export async function getInfrastructureStatus() {
    const response = await authFetch(`${API_BASE}/system/infrastructure/status`, {
        method: 'GET'
    });
    if (!response.ok) throw new Error('Failed to fetch infrastructure status');
    return await response.json();
}

/**
 * Restart appliance services
 * @returns {Promise<object>} Restart result
 */
export async function restartAppliance() {
    const response = await authFetch(`${API_BASE}/system/infrastructure/appliance/restart`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to restart appliance');
    return await response.json();
}

/**
 * Get appliance logs
 * @param {number} lines - Number of log lines to retrieve
 * @returns {Promise<object>} Log data
 */
export async function getApplianceLogs(lines = 50) {
    const response = await authFetch(`${API_BASE}/system/infrastructure/appliance/logs?lines=${lines}`, {
        method: 'GET'
    });
    if (!response.ok) throw new Error('Failed to fetch appliance logs');
    return await response.json();
}

/**
 * Test NAT configuration
 * @returns {Promise<object>} NAT test results
 */
export async function testNAT() {
    const response = await authFetch(`${API_BASE}/system/infrastructure/test-nat`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to test NAT');
    return await response.json();
}

// ============================================================================
// APPS API
// ============================================================================

/**
 * Get all deployed apps
 * @returns {Promise<array>} List of apps
 */
export async function getApps() {
    const response = await authFetch(`${API_BASE}/apps`);
    if (!response.ok) throw new Error('Failed to fetch apps');
    return await response.json();
}

/**
 * Get single app by ID
 * @param {string} appId - App ID
 * @returns {Promise<object>} App data
 */
export async function getApp(appId) {
    const response = await authFetch(`${API_BASE}/apps/${appId}`);
    if (!response.ok) throw new Error('Failed to fetch app');
    return await response.json();
}

/**
 * Get app catalog
 * @returns {Promise<array>} List of catalog apps
 */
export async function getCatalog() {
    const response = await authFetch(`${API_BASE}/apps/catalog`);
    if (!response.ok) throw new Error('Failed to fetch catalog');
    return await response.json();
}

/**
 * Deploy new app
 * @param {object} deploymentData - Deployment configuration
 * @returns {Promise<object>} Deployment result
 */
export async function deployApp(deploymentData) {
    const response = await authFetch(`${API_BASE}/apps/deploy`, {
        method: 'POST',
        body: JSON.stringify(deploymentData)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Deployment failed');
    }
    return await response.json();
}

/**
 * Get deployment status
 * @param {string} appId - App ID
 * @returns {Promise<object>} Deployment status
 */
export async function getDeploymentStatus(appId) {
    const response = await authFetch(`${API_BASE}/apps/deploy/${appId}/status`);
    if (!response.ok) throw new Error('Failed to fetch deployment status');
    return await response.json();
}

/**
 * Perform app action (start, stop, restart, destroy)
 * @param {string} appId - App ID
 * @param {string} action - Action to perform
 * @returns {Promise<object>} Action result
 */
export async function performAppAction(appId, action) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/actions`, {
        method: 'POST',
        body: JSON.stringify({ action })
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to ${action} app`);
    }
    return await response.json();
}

/**
 * Delete app
 * @param {string} appId - App ID
 * @returns {Promise<object>} Deletion result
 */
export async function deleteApp(appId) {
    const response = await authFetch(`${API_BASE}/apps/${appId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete app');
    }
    return await response.json();
}

/**
 * Update app (pull new images and restart)
 * @param {string} appId - App ID
 * @returns {Promise<object>} Update result
 */
export async function updateApp(appId) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/update`, {
        method: 'POST'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update app');
    }
    return await response.json();
}

/**
 * Get app logs
 * @param {string} appId - App ID
 * @returns {Promise<object>} Log data
 */
export async function getAppLogs(appId) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/logs`);
    if (!response.ok) throw new Error('Failed to fetch logs');
    return await response.json();
}

/**
 * Execute command in app container
 * @param {string} appId - App ID
 * @param {string} command - Command to execute
 * @returns {Promise<object>} Execution result
 */
export async function execCommand(appId, command) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/exec`, {
        method: 'POST',
        body: JSON.stringify({ command })
    });
    if (!response.ok) throw new Error('Failed to execute command');
    return await response.json();
}

/**
 * Clone an app
 * @param {string} appId - Source app ID
 * @param {string} newHostname - New hostname for clone
 * @returns {Promise<object>} Cloned app data
 */
export async function cloneApp(appId, newHostname) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/clone?new_hostname=${encodeURIComponent(newHostname)}`, {
        method: 'POST'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Clone failed');
    }
    return await response.json();
}

/**
 * Update app configuration
 * @param {string} appId - App ID
 * @param {object} config - Configuration updates (cpu_cores, memory_mb, disk_gb)
 * @returns {Promise<object>} Updated app data
 */
export async function updateAppConfig(appId, config) {
    const params = new URLSearchParams();
    if (config.cpu_cores) params.append('cpu_cores', config.cpu_cores);
    if (config.memory_mb) params.append('memory_mb', config.memory_mb);
    if (config.disk_gb) params.append('disk_gb', config.disk_gb);

    const response = await authFetch(`${API_BASE}/apps/${appId}/config?${params.toString()}`, {
        method: 'PUT'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Config update failed');
    }
    return await response.json();
}

// ============================================================================
// BACKUP API
// ============================================================================

/**
 * Get app backups
 * @param {string} appId - App ID
 * @returns {Promise<array>} List of backups
 */
export async function getBackups(appId) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/backups`);
    if (!response.ok) throw new Error('Failed to fetch backups');
    return await response.json();
}

/**
 * Create app backup
 * @param {string} appId - App ID
 * @returns {Promise<object>} Backup creation result
 */
export async function createBackup(appId) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/backups`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to create backup');
    return await response.json();
}

/**
 * Restore app from backup
 * @param {string} appId - App ID
 * @param {string} backupId - Backup ID
 * @returns {Promise<object>} Restore result
 */
export async function restoreBackup(appId, backupId) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/backups/${backupId}/restore`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to restore backup');
    return await response.json();
}

/**
 * Delete backup
 * @param {string} appId - App ID
 * @param {string} backupId - Backup ID
 * @returns {Promise<object>} Deletion result
 */
export async function deleteBackup(appId, backupId) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/backups/${backupId}`, {
        method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to delete backup');
    return await response.json();
}

// ============================================================================
// MONITORING API
// ============================================================================

/**
 * Get app metrics
 * @param {string} appId - App ID
 * @returns {Promise<object>} App metrics
 */
export async function getAppMetrics(appId) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/metrics`);
    if (!response.ok) throw new Error('Failed to fetch metrics');
    return await response.json();
}

/**
 * Get app current stats (for monitoring modal)
 * @param {string} appId - App ID
 * @returns {Promise<object>} Current stats with CPU, memory, disk usage
 */
export async function getAppStats(appId) {
    const response = await authFetch(`${API_BASE}/apps/${appId}/stats/current`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return await response.json();
}

// ============================================================================
// SETTINGS API
// ============================================================================

/**
 * Get Proxmox settings
 * @returns {Promise<object>} Proxmox settings
 */
export async function getProxmoxSettings() {
    const response = await authFetch(`${API_BASE}/settings/proxmox`, {
        method: 'GET'
    });
    if (!response.ok) throw new Error('Failed to fetch Proxmox settings');
    return await response.json();
}

/**
 * Update Proxmox settings
 * @param {object} settings - New settings
 * @returns {Promise<object>} Updated settings
 */
export async function updateProxmoxSettings(settings) {
    const response = await authFetch(`${API_BASE}/settings/proxmox`, {
        method: 'POST',
        body: JSON.stringify(settings)
    });
    if (!response.ok) throw new Error('Failed to update Proxmox settings');
    return await response.json();
}

/**
 * Get network settings
 * @returns {Promise<object>} Network settings
 */
export async function getNetworkSettings() {
    const response = await authFetch(`${API_BASE}/settings/network`, {
        method: 'GET'
    });
    if (!response.ok) throw new Error('Failed to fetch network settings');
    return await response.json();
}

/**
 * Update network settings
 * @param {object} settings - New settings
 * @returns {Promise<object>} Updated settings
 */
export async function updateNetworkSettings(settings) {
    const response = await authFetch(`${API_BASE}/settings/network`, {
        method: 'POST',
        body: JSON.stringify(settings)
    });
    if (!response.ok) throw new Error('Failed to update network settings');
    return await response.json();
}

/**
 * Get resource settings
 * @returns {Promise<object>} Resource settings
 */
export async function getResourceSettings() {
    const response = await authFetch(`${API_BASE}/settings/resources`, {
        method: 'GET'
    });
    if (!response.ok) throw new Error('Failed to fetch resource settings');
    return await response.json();
}

/**
 * Update resource settings
 * @param {object} settings - New settings
 * @returns {Promise<object>} Updated settings
 */
export async function updateResourceSettings(settings) {
    const response = await authFetch(`${API_BASE}/settings/resources`, {
        method: 'POST',
        body: JSON.stringify(settings)
    });
    if (!response.ok) throw new Error('Failed to update resource settings');
    return await response.json();
}

/**
 * Update system info (proximity mode)
 * @param {object} updates - System info updates
 * @returns {Promise<object>} Updated system info
 */
export async function updateSystemInfo(updates) {
    const response = await authFetch(`${API_BASE}/system/info`, {
        method: 'PUT',
        body: JSON.stringify(updates)
    });
    if (!response.ok) throw new Error('Failed to update system info');
    return await response.json();
}
