/**
 * Backup Service
 * 
 * Provides backup management functionality for applications.
 * Handles creation, restoration, deletion, and polling of backups.
 * 
 * Features:
 * - List backups for an app
 * - Create new backups (snapshot mode, zstd compression)
 * - Restore from backup
 * - Delete backups
 * - Poll for backup completion (5s interval)
 * - Backup modal management
 * 
 * @module backupService
 */

/**
 * Current app ID for backup modal
 * @private
 */
let currentBackupAppId = null;

/**
 * Backup polling interval
 * @private
 */
let backupPollingInterval = null;

/**
 * Get API base URL
 * @returns {string} API base URL
 */
function getAPIBase() {
    return window.API_BASE || '/api/v1';
}

/**
 * Get authFetch function
 * @returns {Function} Auth fetch function
 */
function getAuthFetch() {
    return window.authFetch || fetch;
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
 * Format date
 */
function fmtDate(date) {
    return window.formatDate ? window.formatDate(date) : new Date(date).toLocaleString();
}

/**
 * Format size
 */
function fmtSize(bytes) {
    return window.formatSize ? window.formatSize(bytes) : `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

/**
 * Get status icon
 */
function getStatusIcon(status) {
    if (window.getStatusIcon) {
        return window.getStatusIcon(status);
    }
    const icons = {
        'available': '✅',
        'creating': '⏳',
        'failed': '❌',
        'restoring': '🔄'
    };
    return icons[status] || '❓';
}

/**
 * Initialize Lucide icons
 */
function initIcons() {
    if (window.lucide && window.lucide.createIcons) {
        setTimeout(() => window.lucide.createIcons(), 100);
    }
}

/**
 * Show backup management modal
 * Opens modal and loads backups for specified app
 * 
 * @param {string} appId - Application ID
 * @returns {Promise<void>}
 */
export async function showBackupModal(appId) {
    currentBackupAppId = appId;
    const authFetch = getAuthFetch();
    const apiBase = getAPIBase();

    try {
        // Get app details
        const response = await authFetch(`${apiBase}/apps/${appId}`);
        const app = await response.json();
        
        const appNameEl = document.getElementById('backup-app-name');
        if (appNameEl) {
            appNameEl.textContent = app.name;
        }

        // Load backups
        await listBackups(appId);

        // Show modal
        const modal = document.getElementById('backupModal');
        if (modal) {
            modal.style.display = 'flex';
        }

        // Refresh icons after modal content is added
        initIcons();
    } catch (error) {
        notify('Failed to load backup modal', 'error');
        console.error('Error showing backup modal:', error);
    }
}

/**
 * Hide backup management modal
 * Closes modal and stops polling
 */
export function hideBackupModal() {
    const modal = document.getElementById('backupModal');
    if (modal) {
        modal.style.display = 'none';
    }
    currentBackupAppId = null;

    // Stop polling
    stopBackupPolling();
}

/**
 * List backups for an application
 * Fetches and renders backup list with status
 * 
 * @param {string} appId - Application ID
 * @returns {Promise<Array>} Array of backups
 */
export async function listBackups(appId) {
    const authFetch = getAuthFetch();
    const apiBase = getAPIBase();

    try {
        const response = await authFetch(`${apiBase}/apps/${appId}/backups`);
        const data = await response.json();
        const backups = data.backups || [];

        const listEl = document.getElementById('backup-list');
        if (!listEl) return backups;

        if (backups.length === 0) {
            listEl.innerHTML = '<p class="empty-state">No backups yet. Create your first backup to protect your data.</p>';
            return backups;
        }

        listEl.innerHTML = backups.map(backup => `
            <div class="backup-item" data-backup-id="${backup.id}">
                <div class="backup-info">
                    <div class="backup-filename">${backup.filename}</div>
                    <div class="backup-meta">
                        <span class="backup-date">
                            <i data-lucide="calendar"></i>
                            ${fmtDate(backup.created_at)}
                        </span>
                        <span class="backup-size">
                            <i data-lucide="hard-drive"></i>
                            ${fmtSize(backup.size_bytes)}
                        </span>
                        <span class="backup-status status-${backup.status}">
                            ${getStatusIcon(backup.status)}
                            ${backup.status}
                        </span>
                    </div>
                    ${backup.error_message ? `<div class="backup-error">${backup.error_message}</div>` : ''}
                </div>
                <div class="backup-actions">
                    ${backup.status === 'available' ? `
                        <button class="btn btn-sm btn-secondary" onclick="window.backupService.restoreBackup('${appId}', ${backup.id})" title="Restore from this backup">
                            <i data-lucide="rotate-ccw"></i>
                            Restore
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-danger" onclick="window.backupService.deleteBackup('${appId}', ${backup.id})" title="Delete this backup">
                        <i data-lucide="trash-2"></i>
                        Delete
                    </button>
                </div>
            </div>
        `).join('');

        // Refresh icons
        initIcons();

        // Start polling if there are creating backups
        const creatingBackups = backups.filter(b => b.status === 'creating');
        if (creatingBackups.length > 0) {
            startBackupPolling(appId);
        }

        return backups;

    } catch (error) {
        notify('Failed to load backups', 'error');
        console.error('Error loading backups:', error);
        return [];
    }
}

/**
 * Create a new backup
 * Initiates backup creation with snapshot mode and zstd compression
 * 
 * @param {string} appId - Application ID (optional if modal is open)
 * @returns {Promise<void>}
 */
export async function createBackup(appId = null) {
    const targetAppId = appId || currentBackupAppId;
    if (!targetAppId) {
        notify('No app selected for backup', 'error');
        return;
    }

    const authFetch = getAuthFetch();
    const apiBase = getAPIBase();

    try {
        notify('Creating backup...', 'info');

        await authFetch(`${apiBase}/apps/${targetAppId}/backups`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                storage: 'local',
                compress: 'zstd',
                mode: 'snapshot'
            })
        });

        notify('Backup creation started', 'success');

        // Reload backups
        await listBackups(targetAppId);

    } catch (error) {
        notify('Failed to create backup', 'error');
        console.error('Error creating backup:', error);
        throw error;
    }
}

/**
 * Restore from backup
 * Restores application state from specified backup
 * 
 * @param {string} appId - Application ID
 * @param {number} backupId - Backup ID
 * @returns {Promise<void>}
 */
export async function restoreBackup(appId, backupId) {
    if (!confirm('Are you sure you want to restore from this backup? This will replace the current application state.')) {
        return;
    }

    const authFetch = getAuthFetch();
    const apiBase = getAPIBase();

    try {
        notify('Restoring from backup...', 'info');

        await authFetch(`${apiBase}/apps/${appId}/backups/${backupId}/restore`, {
            method: 'POST'
        });

        notify('Restore completed successfully', 'success');
        hideBackupModal();

        // Refresh app list
        if (window.dataService && window.dataService.loadDeployedApps) {
            await window.dataService.loadDeployedApps();
        } else if (window.loadApps) {
            await window.loadApps();
        }

    } catch (error) {
        notify('Failed to restore backup', 'error');
        console.error('Error restoring backup:', error);
        throw error;
    }
}

/**
 * Delete a backup
 * Permanently deletes specified backup
 * 
 * @param {string} appId - Application ID
 * @param {number} backupId - Backup ID
 * @returns {Promise<void>}
 */
export async function deleteBackup(appId, backupId) {
    if (!confirm('Are you sure you want to delete this backup? This action cannot be undone.')) {
        return;
    }

    const authFetch = getAuthFetch();
    const apiBase = getAPIBase();

    try {
        await authFetch(`${apiBase}/apps/${appId}/backups/${backupId}`, {
            method: 'DELETE'
        });

        notify('Backup deleted successfully', 'success');

        // Reload backups
        await listBackups(appId);

    } catch (error) {
        notify('Failed to delete backup', 'error');
        console.error('Error deleting backup:', error);
        throw error;
    }
}

/**
 * Refresh backups list
 * Reloads backups for current app
 * 
 * @returns {Promise<void>}
 */
export async function refreshBackups() {
    if (!currentBackupAppId) {
        notify('No app selected', 'error');
        return;
    }
    
    notify('Refreshing backups...', 'info');
    await listBackups(currentBackupAppId);
    notify('Backups refreshed', 'success');
}

/**
 * Start polling for backup completion
 * Polls every 5 seconds until backups are complete
 * @private
 * 
 * @param {string} appId - Application ID
 */
function startBackupPolling(appId) {
    // Clear existing interval
    stopBackupPolling();

    // Poll every 5 seconds
    backupPollingInterval = setInterval(async () => {
        if (currentBackupAppId === appId) {
            await listBackups(appId);
        } else {
            stopBackupPolling();
        }
    }, 5000);
}

/**
 * Stop backup polling
 * @private
 */
function stopBackupPolling() {
    if (backupPollingInterval) {
        clearInterval(backupPollingInterval);
        backupPollingInterval = null;
    }
}

/**
 * Get current backup app ID
 * @returns {string|null} Current app ID or null
 */
export function getCurrentBackupAppId() {
    return currentBackupAppId;
}

/**
 * Check if polling is active
 * @returns {boolean} True if polling is active
 */
export function isPolling() {
    return backupPollingInterval !== null;
}

// Backward compatibility: Expose to window
if (typeof window !== 'undefined') {
    window.backupService = {
        showBackupModal,
        hideBackupModal,
        listBackups,
        createBackup,
        restoreBackup,
        deleteBackup,
        refreshBackups,
        getCurrentBackupAppId,
        isPolling
    };
}
