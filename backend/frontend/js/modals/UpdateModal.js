/**
 * UpdateModal.js
 * 
 * Handles the application update modal and process.
 * 
 * Features:
 * - Confirms update with user
 * - Creates safety backup before update
 * - Pulls latest images
 * - Restarts application
 * - Verifies health after update
 * - Real-time progress tracking
 * - Polls app status during update
 * 
 * Dependencies:
 * - api.js: API.getApp(), API.updateApp()
 * - appState.js: AppState.getState(), AppState.setState()
 * - notifications.js: showNotification()
 */

import * as API from '../services/api.js';
import * as AppState from '../state/appState.js';
import { showNotification } from '../utils/notifications.js';

/**
 * Show update modal and confirm
 * @param {string} appId - ID of app to update
 */
export async function showUpdateModal(appId) {
    try {
        // Get app details
        const app = await API.getApp(appId);

        const confirmed = confirm(
            `Update ${app.name}?\n\n` +
            `✅ A safety backup will be automatically created before starting\n` +
            `⏸️  The application will be briefly unavailable during the process\n` +
            `🔄 Latest images will be pulled and containers recreated\n` +
            `🏥 Health check will verify the update\n\n` +
            `Continue with update?`
        );

        if (confirmed) {
            await performUpdate(appId, app.name);
        }
    } catch (error) {
        showNotification('Failed to load app details', 'error');
        console.error('Error showing update modal:', error);
    }
}

/**
 * Perform the update with status feedback
 * @param {string} appId - ID of app to update
 * @param {string} appName - Name of app to update
 */
async function performUpdate(appId, appName) {
    // Create progress notification
    const progressSteps = [
        { icon: 'database', text: 'Creating safety backup...', status: 'in-progress' },
        { icon: 'download', text: 'Pulling new images...', status: 'pending' },
        { icon: 'refresh-cw', text: 'Restarting application...', status: 'pending' },
        { icon: 'activity', text: 'Verifying health...', status: 'pending' }
    ];

    let currentStep = 0;

    // Show initial notification
    showUpdateProgress(progressSteps, currentStep);

    try {
        // Start the update
        await API.updateApp(appId);

        // Poll app status and update progress based on actual status
        const progressInterval = setInterval(async () => {
            try {
                const app = await API.getApp(appId);
                
                // Update progress based on actual app status
                if (app.status === 'updating') {
                    // Still updating - cycle through steps based on elapsed time
                    currentStep = Math.min(currentStep + 1, progressSteps.length - 1);
                    if (currentStep > 0) {
                        progressSteps[currentStep - 1].status = 'completed';
                    }
                    progressSteps[currentStep].status = 'in-progress';
                    showUpdateProgress(progressSteps, currentStep);
                } else if (app.status === 'running') {
                    // Update completed successfully
                    clearInterval(progressInterval);
                } else if (app.status === 'update_failed') {
                    // Update failed
                    clearInterval(progressInterval);
                }
            } catch (pollError) {
                console.warn('Status poll error:', pollError);
            }
        }, 5000); // Check every 5 seconds

        // Wait for update to complete (poll app status)
        // Timeout increased to 7 minutes to accommodate:
        // - Backup: up to 5 min
        // - Image pull: 2-3 min
        // - Service restart: 30s
        // - Health check: 50s
        await pollAppStatus(appId, 'running', 420000); // 7 minute timeout

        clearInterval(progressInterval);

        // Mark all as completed
        progressSteps.forEach(step => step.status = 'completed');
        showUpdateProgress(progressSteps, progressSteps.length);

        setTimeout(() => {
            showNotification(`✅ ${appName} updated successfully!`, 'success');
            
            // Refresh app list
            refreshApps();
        }, 1000);

    } catch (error) {
        // Provide more specific error messages
        let errorMessage = 'Update failed';
        
        if (error.message.includes('timeout')) {
            errorMessage = '⏱️ Update timeout - The update is taking longer than expected. Please check the app status in a few minutes or review the logs.';
        } else if (error.message.includes('Health check failed')) {
            errorMessage = '❌ Update failed: Application health check failed after restart. The app may need manual intervention.';
        } else if (error.message.includes('backup')) {
            errorMessage = '❌ Update aborted: Pre-update backup failed. Your app is safe and unchanged.';
        } else if (error.message) {
            errorMessage = `❌ Update failed: ${error.message}`;
        }
        
        showNotification(errorMessage, 'error');
        console.error('Update error:', error);

        // Reload apps to show current state
        refreshApps();
    }
}

/**
 * Poll app status until it reaches expected status
 * @param {string} appId - App ID
 * @param {string} expectedStatus - Expected status (e.g., 'running')
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<object>} App object when status matches
 */
async function pollAppStatus(appId, expectedStatus, timeout = 60000) {
    const startTime = Date.now();
    const pollInterval = 2000; // 2 seconds

    while (Date.now() - startTime < timeout) {
        try {
            const app = await API.getApp(appId);

            if (app.status === expectedStatus) {
                return app;
            }

            if (app.status === 'update_failed') {
                throw new Error('Update failed - check logs for details');
            }

            await new Promise(resolve => setTimeout(resolve, pollInterval));
        } catch (error) {
            if (Date.now() - startTime >= timeout) {
                throw new Error('Update timeout - The operation is taking longer than expected. The update may still be in progress. Please refresh the page and check the app status.');
            }
            // Continue polling on errors
            await new Promise(resolve => setTimeout(resolve, pollInterval));
        }
    }

    throw new Error('Update timeout - The operation exceeded the maximum time limit. Please check the app status and logs.');
}

/**
 * Show update progress notification
 * @param {Array} steps - Array of step objects
 * @param {number} currentStep - Current step index
 */
function showUpdateProgress(steps, currentStep) {
    const stepsHtml = steps.map((step, index) => {
        let statusIcon = '';
        let statusClass = '';

        if (step.status === 'completed') {
            statusIcon = '<i data-lucide="check-circle" class="text-success"></i>';
            statusClass = 'completed';
        } else if (step.status === 'in-progress') {
            statusIcon = '<i data-lucide="loader" class="spin"></i>';
            statusClass = 'in-progress';
        } else {
            statusIcon = '<i data-lucide="circle" class="text-muted"></i>';
            statusClass = 'pending';
        }

        return `
            <div class="update-step ${statusClass}">
                ${statusIcon}
                <span>${step.text}</span>
            </div>
        `;
    }).join('');

    const container = document.getElementById('notification-container') || createNotificationContainer();

    const existingUpdate = document.querySelector('.update-progress-notification');
    if (existingUpdate) {
        existingUpdate.innerHTML = `
            <div class="notification-header">
                <i data-lucide="refresh-cw"></i>
                <span>Updating Application</span>
            </div>
            <div class="update-steps">
                ${stepsHtml}
            </div>
        `;
        // Reinitialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    } else {
        const notification = document.createElement('div');
        notification.className = 'notification info update-progress-notification';
        notification.innerHTML = `
            <div class="notification-header">
                <i data-lucide="refresh-cw"></i>
                <span>Updating Application</span>
            </div>
            <div class="update-steps">
                ${stepsHtml}
            </div>
        `;
        container.appendChild(notification);
        // Reinitialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
}

/**
 * Create notification container if it doesn't exist
 * @returns {HTMLElement} Notification container
 */
function createNotificationContainer() {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Refresh apps list
 */
async function refreshApps() {
    try {
        const apps = await API.getApps();
        AppState.setState({ apps });
    } catch (error) {
        console.error('Failed to refresh apps:', error);
    }
}

// ======================
// Global Exposure (Backward Compatibility)
// ======================

if (typeof window !== 'undefined') {
    window.showUpdateModal = showUpdateModal;
}
