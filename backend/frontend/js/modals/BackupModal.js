/**
 * Backup Modal Module
 *
 * Handles backup management:
 * - List backups for an app
 * - Create new backups
 * - Restore from backup
 * - Delete backups
 * - Real-time backup status polling
 */

import * as API from '../services/api.js';
import * as AppState from '../state/appState.js';
import { showNotification } from '../utils/notifications.js';

// State
let currentBackupAppId = null;
let backupPollingInterval = null;

/**
 * Show backup management modal for an app
 * @param {string} appId - App ID
 */
export async function showBackupModal(appId) {
    currentBackupAppId = appId;

    try {
        // Get app details
        const app = await API.getApp(appId);
        document.getElementById('backup-app-name').textContent = app.name;

        // Load backups
        await loadBackups(appId);

        // Show modal
        const modal = document.getElementById('backupModal');
        modal.style.display = 'flex';

        // Refresh Lucide icons after modal content is added
        setTimeout(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }, 100);
    } catch (error) {
        showNotification('Failed to load backup modal', 'error');
        console.error('Error showing backup modal:', error);
    }
}

/**
 * Hide backup management modal
 */
export function hideBackupModal() {
    const modal = document.getElementById('backupModal');
    modal.style.display = 'none';
    currentBackupAppId = null;

    // Stop polling
    if (backupPollingInterval) {
        clearInterval(backupPollingInterval);
        backupPollingInterval = null;
    }
}

/**
 * Load backups for current app
 * @param {string} appId - App ID
 */
async function loadBackups(appId) {
    try {
        const backups = await API.getBackups(appId);

        const listEl = document.getElementById('backup-list');

        if (!backups || backups.length === 0) {
            listEl.innerHTML = '<p class="empty-state">No backups yet. Create your first backup to protect your data.</p>';
            return;
        }

        listEl.innerHTML = backups.map(backup => `
            <div class="backup-item" data-backup-id="${backup.id}">
                <div class="backup-info">
                    <div class="backup-filename">${backup.filename}</div>
                    <div class="backup-meta">
                        <span class="backup-date">
                            <i data-lucide="calendar"></i>
                            ${formatDate(backup.created_at)}
                        </span>
                        <span class="backup-size">
                            <i data-lucide="hard-drive"></i>
                            ${formatSize(backup.size_bytes)}
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
                        <button class="btn btn-sm btn-secondary" data-action="restore" data-backup-id="${backup.id}" title="Restore from this backup">
                            <i data-lucide="rotate-ccw"></i>
                            Restore
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-danger" data-action="delete" data-backup-id="${backup.id}" title="Delete this backup">
                        <i data-lucide="trash-2"></i>
                        Delete
                    </button>
                </div>
            </div>
        `).join('');

        // Attach event listeners to backup action buttons
        listEl.querySelectorAll('[data-action="restore"]').forEach(btn => {
            btn.addEventListener('click', () => {
                const backupId = btn.getAttribute('data-backup-id');
                restoreBackup(appId, backupId);
            });
        });

        listEl.querySelectorAll('[data-action="delete"]').forEach(btn => {
            btn.addEventListener('click', () => {
                const backupId = btn.getAttribute('data-backup-id');
                deleteBackup(appId, backupId);
            });
        });

        // Refresh Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // Start polling if there are creating backups
        const creatingBackups = backups.filter(b => b.status === 'creating');
        if (creatingBackups.length > 0) {
            startBackupPolling(appId);
        }

    } catch (error) {
        showNotification('Failed to load backups', 'error');
        console.error('Error loading backups:', error);
    }
}

/**
 * Create a new backup
 */
export async function createBackup() {
    if (!currentBackupAppId) return;

    try {
        showNotification('Creating backup...', 'info');

        await API.createBackup(currentBackupAppId);

        showNotification('Backup creation started', 'success');

        // Reload backups
        await loadBackups(currentBackupAppId);

    } catch (error) {
        showNotification('Failed to create backup', 'error');
        console.error('Error creating backup:', error);
    }
}

/**
 * Restore from backup
 * @param {string} appId - App ID
 * @param {string} backupId - Backup ID
 */
async function restoreBackup(appId, backupId) {
    if (!confirm('Are you sure you want to restore from this backup? This will replace the current application state.')) {
        return;
    }

    try {
        showNotification('Restoring from backup...', 'info');

        await API.restoreBackup(appId, backupId);

        showNotification('Restore completed successfully', 'success');
        hideBackupModal();

        // Refresh app list
        const apps = await API.getApps();
        AppState.setState({ apps: apps, deployedApps: apps });

    } catch (error) {
        showNotification('Failed to restore backup', 'error');
        console.error('Error restoring backup:', error);
    }
}

/**
 * Delete a backup
 * @param {string} appId - App ID
 * @param {string} backupId - Backup ID
 */
async function deleteBackup(appId, backupId) {
    if (!confirm('Are you sure you want to delete this backup? This action cannot be undone.')) {
        return;
    }

    try {
        await API.deleteBackup(appId, backupId);

        showNotification('Backup deleted successfully', 'success');

        // Reload backups
        await loadBackups(appId);

    } catch (error) {
        showNotification('Failed to delete backup', 'error');
        console.error('Error deleting backup:', error);
    }
}

/**
 * Refresh backups list
 */
export async function refreshBackups() {
    if (!currentBackupAppId) return;

    showNotification('Refreshing backups...', 'info');
    await loadBackups(currentBackupAppId);
    showNotification('Backups refreshed', 'success');
}

/**
 * Start polling for backup completion
 * @param {string} appId - App ID
 */
function startBackupPolling(appId) {
    // Clear existing interval
    if (backupPollingInterval) {
        clearInterval(backupPollingInterval);
    }

    // Poll every 5 seconds
    backupPollingInterval = setInterval(async () => {
        if (currentBackupAppId === appId) {
            await loadBackups(appId);
        } else {
            clearInterval(backupPollingInterval);
            backupPollingInterval = null;
        }
    }, 5000);
}

/**
 * Format backup size
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size
 */
function formatSize(bytes) {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    return date.toLocaleDateString();
}

/**
 * Get status icon HTML
 * @param {string} status - Backup status
 * @returns {string} Icon HTML
 */
function getStatusIcon(status) {
    const icons = {
        'creating': '<i data-lucide="loader" class="spin"></i>',
        'available': '<i data-lucide="check-circle"></i>',
        'failed': '<i data-lucide="x-circle"></i>',
        'restoring': '<i data-lucide="rotate-cw" class="spin"></i>'
    };
    return icons[status] || '';
}

// Expose functions globally for legacy compatibility
if (typeof window !== 'undefined') {
    window.showBackupModal = showBackupModal;
    window.hideBackupModal = hideBackupModal;
    window.createBackup = createBackup;
    window.refreshBackups = refreshBackups;
}
