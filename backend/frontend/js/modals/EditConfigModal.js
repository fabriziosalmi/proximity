/**
 * EditConfigModal.js
 * 
 * Handles the application resource configuration editing modal.
 * 
 * Features:
 * - Edit CPU cores (1-16)
 * - Edit memory in MB (512-32768)
 * - Edit disk size in GB (1-500, increase only)
 * - Validates at least one field is updated
 * - Restarts app to apply changes
 * - Updates app state after successful change
 * 
 * Dependencies:
 * - api.js: API.updateAppConfig()
 * - appState.js: AppState.getState(), AppState.setState()
 * - notifications.js: showNotification()
 */

import * as API from '../services/api.js';
import * as AppState from '../state/appState.js';
import { showNotification } from '../utils/notifications.js';

/**
 * Show edit config modal
 * @param {string} appId - ID of app to edit
 * @param {string} appName - Name of app to edit
 */
export async function showEditConfigModal(appId, appName) {
    // Create modal HTML
    const modalHTML = `
        <div class="modal-overlay" id="editConfigOverlay">
            <div class="modal-dialog">
                <div class="modal-header">
                    <h2>Edit Resources: ${appName}</h2>
                    <button class="modal-close" id="editConfigCloseBtn">✕</button>
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
                    <button class="btn btn-secondary" id="editConfigCancelBtn">Cancel</button>
                    <button class="btn btn-primary" id="editConfigSubmitBtn">
                        Apply Changes
                    </button>
                </div>
            </div>
        </div>
    `;

    // Add to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Get DOM elements
    const overlay = document.getElementById('editConfigOverlay');
    const closeBtn = document.getElementById('editConfigCloseBtn');
    const cancelBtn = document.getElementById('editConfigCancelBtn');
    const submitBtn = document.getElementById('editConfigSubmitBtn');
    const cpuInput = document.getElementById('editCpu');

    // Attach event listeners
    closeBtn.addEventListener('click', closeEditConfigModal);
    cancelBtn.addEventListener('click', closeEditConfigModal);
    submitBtn.addEventListener('click', () => submitEditConfig(appId, appName));

    // Focus first input
    setTimeout(() => cpuInput?.focus(), 100);
}

/**
 * Close edit config modal
 */
export function closeEditConfigModal() {
    const overlay = document.getElementById('editConfigOverlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Submit config update
 * @param {string} appId - ID of app to update
 * @param {string} appName - Name of app to update
 */
async function submitEditConfig(appId, appName) {
    const cpuCores = document.getElementById('editCpu')?.value;
    const memoryMb = document.getElementById('editMemory')?.value;
    const diskGb = document.getElementById('editDisk')?.value;

    // Validate at least one field is set
    if (!cpuCores && !memoryMb && !diskGb) {
        showNotification('Please specify at least one resource to update', 'warning');
        return;
    }

    try {
        closeEditConfigModal();
        showNotification(`Updating resources for ${appName}...`, 'info');

        // Build config object
        const config = {};
        if (cpuCores) config.cpu_cores = parseInt(cpuCores, 10);
        if (memoryMb) config.memory_mb = parseInt(memoryMb, 10);
        if (diskGb) config.disk_gb = parseInt(diskGb, 10);

        // Call API
        await API.updateAppConfig(appId, config);

        showNotification(`✓ Resources updated successfully`, 'success');

        // Update app state - fetch fresh app list
        const currentState = AppState.getState();
        const apps = await API.getApps();
        
        AppState.setState({ 
            apps: apps 
        });

        // The observer will trigger re-render automatically

    } catch (error) {
        console.error('Config update error:', error);
        showNotification(`Failed to update config: ${error.message}`, 'error');
    }
}

// ======================
// Global Exposure (Backward Compatibility)
// ======================

if (typeof window !== 'undefined') {
    window.showEditConfigModal = showEditConfigModal;
    window.closeEditConfigModal = closeEditConfigModal;
}
