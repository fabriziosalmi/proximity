/**
 * App Operations Service
 * 
 * Handles app control operations: start, stop, restart, delete, update
 * Extracted from app.js as part of Phase 4 refactoring
 */

// Import required utilities
// Note: These are accessed via window.* for now during transition
// TODO: Convert to ES6 imports when those modules are created

const API_BASE = window.API_BASE || '/api';

/**
 * Get authFetch function (will be properly imported later)
 */
function getAuthFetch() {
    return window.authFetch || fetch;
}

/**
 * Get notification function
 */
function getNotification() {
    return window.showNotification || (() => {});
}

/**
 * Get loading functions
 */
function getLoadingFunctions() {
    return {
        show: window.showLoading || (() => {}),
        hide: window.hideLoading || (() => {})
    };
}

/**
 * Control an application (start, stop, restart)
 * @param {string} appId - The application ID
 * @param {string} action - The action to perform (start, stop, restart)
 * @returns {Promise<void>}
 */
export async function controlApp(appId, action) {
    const authFetch = getAuthFetch();
    const showNotification = getNotification();
    const { show: showLoading, hide: hideLoading } = getLoadingFunctions();
    
    showLoading(`${action}ing application...`);
    
    try {
        const response = await authFetch(`${API_BASE}/apps/${appId}/actions`, {
            method: 'POST',
            body: JSON.stringify({ action: action })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Failed to ${action} app`);
        }
        
        hideLoading();
        showNotification(`Application ${action}ed successfully`, 'success');
        
        return true;
        
    } catch (error) {
        hideLoading();
        showNotification(`Failed to ${action} app: ` + error.message, 'error');
        console.error('Control error:', error);
        throw error;
    }
}

/**
 * Show delete confirmation modal for an application
 * @param {string} appId - The application ID
 * @param {string} appName - The application name
 */
export function confirmDeleteApp(appId, appName) {
    const modal = document.getElementById('deployModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    if (!modal || !modalTitle || !modalBody) {
        console.error('Modal elements not found');
        return;
    }
    
    modalTitle.textContent = 'Delete Application';
    modalBody.innerHTML = `
        <div style="padding: 1.5rem; text-align: center;">
            <div style="width: 64px; height: 64px; margin: 0 auto 1rem; border-radius: 50%; background: rgba(239, 68, 68, 0.1); display: flex; align-items: center; justify-content: center;">
                <div style="width: 40px; height: 40px; border-radius: 50%; background: #ef4444;"></div>
            </div>
            <h3 style="color: var(--text-primary); margin-bottom: 1rem;">${appName}</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6;">
                Are you sure you want to delete this application?
            </p>
            
            <div style="background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 1rem; margin-bottom: 1.5rem; text-align: left;">
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #f59e0b;"></span>
                    This action will:
                </p>
                <ul style="color: var(--text-secondary); font-size: 0.875rem; margin: 0; padding-left: 1.5rem; line-height: 1.8;">
                    <li>Stop the application</li>
                    <li>Delete the LXC container</li>
                    <li>Remove all data permanently</li>
                    <li>Remove from reverse proxy</li>
                </ul>
                <p style="color: #ef4444; font-size: 0.875rem; margin-top: 0.75rem; font-weight: 600; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #ef4444;"></span>
                    This action cannot be undone!
                </p>
            </div>
            
            <div style="display: flex; gap: 0.75rem; justify-content: center;">
                <button class="btn btn-ghost" onclick="window.closeModal?.()" style="min-width: 120px;">Cancel</button>
                <button class="btn btn-primary" onclick="window.appOperations?.deleteApp('${appId}', '${appName}')" style="min-width: 120px; background: #ef4444; border-color: #ef4444;">
                    Delete Forever
                </button>
            </div>
        </div>
    `;
    
    // Remove any existing modal footer since we have inline buttons
    document.querySelector('.modal-footer')?.remove();
    
    modal.classList.add('show');
    
    // Call openModal if available
    if (window.openModal) {
        window.openModal();
    }
}

/**
 * Delete an application
 * @param {string} appId - The application ID
 * @param {string} appName - The application name
 * @returns {Promise<void>}
 */
export async function deleteApp(appId, appName) {
    const authFetch = getAuthFetch();
    const showNotification = getNotification();
    
    // Show deletion progress if function exists
    if (window.showDeletionProgress) {
        window.showDeletionProgress(appName);
    }
    
    try {
        // Progress updates
        if (window.updateDeletionProgress) {
            await window.updateDeletionProgress(0, 'Stopping application...');
            await new Promise(resolve => setTimeout(resolve, 800));
            
            await window.updateDeletionProgress(33, 'Removing from reverse proxy...');
            await new Promise(resolve => setTimeout(resolve, 800));
            
            await window.updateDeletionProgress(66, 'Deleting LXC container...');
        }
        
        // Perform deletion
        const response = await authFetch(`${API_BASE}/apps/${appId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete app');
        }
        
        if (window.updateDeletionProgress) {
            await window.updateDeletionProgress(100, 'Deletion complete');
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        if (window.hideDeletionProgress) {
            window.hideDeletionProgress();
        }
        
        showNotification('Application deleted successfully', 'success');
        
        return true;
        
    } catch (error) {
        if (window.hideDeletionProgress) {
            window.hideDeletionProgress();
        }
        showNotification('Failed to delete app: ' + error.message, 'error');
        console.error('Delete error:', error);
        throw error;
    }
}

/**
 * Poll application status until it reaches expected status
 * @param {string} appId - The application ID
 * @param {string} expectedStatus - The expected status (running, stopped, etc.)
 * @param {number} timeout - Timeout in milliseconds (default: 60000)
 * @returns {Promise<Object>} - The app object when status matches
 */
export async function pollAppStatus(appId, expectedStatus, timeout = 60000) {
    const authFetch = getAuthFetch();
    const startTime = Date.now();
    const pollInterval = 2000; // 2 seconds

    while (Date.now() - startTime < timeout) {
        try {
            const app = await authFetch(`${API_BASE}/apps/${appId}`);

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
 * Restart an application (convenience method)
 * @param {string} appId - The application ID
 * @returns {Promise<void>}
 */
export async function restartApp(appId) {
    return controlApp(appId, 'restart');
}

/**
 * Start an application (convenience method)
 * @param {string} appId - The application ID
 * @returns {Promise<void>}
 */
export async function startApp(appId) {
    return controlApp(appId, 'start');
}

/**
 * Stop an application (convenience method)
 * @param {string} appId - The application ID
 * @returns {Promise<void>}
 */
export async function stopApp(appId) {
    return controlApp(appId, 'stop');
}

// Expose to window for backward compatibility during transition
if (typeof window !== 'undefined') {
    window.appOperations = {
        controlApp,
        confirmDeleteApp,
        deleteApp,
        pollAppStatus,
        restartApp,
        startApp,
        stopApp
    };
}
