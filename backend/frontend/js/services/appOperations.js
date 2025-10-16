/**
 * App Operations Service
 * 
 * Handles app control operations: start, stop, restart, delete, update
 * Extracted from app.js as part of Phase 4 refactoring
 */

// Import required utilities
// Note: These are accessed via window.* for now during transition
// TODO: Convert to ES6 imports when those modules are created

/**
 * Get API_BASE from window (set by api.js module)
 * Falls back to localhost if not available
 */
function getApiBase() {
    if (window.API_BASE) {
        return window.API_BASE;
    }
    // Fallback: construct it dynamically (same logic as api.js)
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    const port = window.location.port || '8765';
    return `${protocol}//${hostname}:${port}/api/v1`;
}

const API_BASE = getApiBase();

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
    
    // Close the confirmation modal first
    if (window.closeModal) {
        window.closeModal();
    }
    
    // Add breadcrumb for deletion start
    if (window.addDebugBreadcrumb) {
        window.addDebugBreadcrumb('App deletion started', {
            app_id: appId,
            app_name: appName
        });
    }
    
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
        
        // Add breadcrumb for successful deletion
        if (window.addDebugBreadcrumb) {
            window.addDebugBreadcrumb('App deletion succeeded', {
                app_id: appId,
                app_name: appName
            });
        }
        
        showNotification('Application deleted successfully', 'success');
        
        // CRITICAL: Reload apps list to reflect deletion
        if (window.loadDeployedApps) {
            await window.loadDeployedApps();
        }
        
        // CRITICAL: Update UI to reflect changes
        if (window.updateUI) {
            window.updateUI();
        }
        
        // If we're on the apps view, re-render it
        if (window.router && window.router.currentView === 'apps') {
            const currentState = window.getState ? window.getState() : {};
            if (window.router.views.apps) {
                window.router.views.apps.render(currentState);
            }
        }
        
        return true;
        
    } catch (error) {
        if (window.hideDeletionProgress) {
            window.hideDeletionProgress();
        }
        
        // Report deletion failure to Sentry
        if (window.reportToSentry) {
            window.reportToSentry(error, {
                context: 'app_deletion',
                app_id: appId,
                app_name: appName,
                error_message: error.message
            });
        }
        
        // Add breadcrumb for failed deletion
        if (window.addDebugBreadcrumb) {
            window.addDebugBreadcrumb('App deletion failed', {
                app_id: appId,
                app_name: appName,
                error: error.message
            });
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

/**
 * Show application details (placeholder for future implementation)
 * @param {string} appId - The application ID
 */
export function showAppDetails(appId) {
    // Get state from window during transition
    const state = window.state || { deployedApps: [] };
    const app = state.deployedApps.find(a => a.id === appId);
    if (!app) return;
    
    const showNotification = getNotification();
    // TODO: Implement detailed app view
    showNotification('App details view coming soon', 'info');
}

/**
 * Show deletion progress modal
 * @param {string} appName - The application name being deleted
 */
export function showDeletionProgress(appName) {
    const modal = document.getElementById('deployModal');
    const modalBody = document.getElementById('modalBody');
    const modalTitle = document.getElementById('modalTitle');
    
    if (!modal || !modalBody || !modalTitle) {
        console.error('Modal elements not found');
        return;
    }
    
    modalTitle.textContent = 'Deleting Application';
    
    modalBody.innerHTML = `
        <div style="text-align: center; padding: 2rem 1rem;">
            <div style="margin-bottom: 1.5rem;">
                <div class="loading-spinner" style="display: inline-block; margin-bottom: 1rem;"></div>
                <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">${appName}</h3>
                <p style="color: var(--text-secondary); font-size: 0.875rem;">Removing application...</p>
            </div>
            
            <div style="background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 1.5rem; margin-bottom: 1rem;">
                <div id="deletionProgressSteps" style="text-align: left;">
                    <div class="progress-step active">
                        <div class="progress-step-icon">🟠</div>
                        <div class="progress-step-text">Stopping application</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Removing from proxy</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Deleting container</div>
                    </div>
                </div>
                
                <div style="margin-top: 1rem;">
                    <div style="background: var(--bg-tertiary); border-radius: 999px; height: 6px; overflow: hidden;">
                        <div id="deletionProgressBar" style="height: 100%; background: linear-gradient(90deg, #ef4444, #dc2626); transition: width 0.3s ease; width: 0%;"></div>
                    </div>
                </div>
            </div>
            
            <div id="deletionProgressMessage" style="color: var(--text-tertiary); font-size: 0.875rem; min-height: 1.5rem;">
                Initializing deletion...
            </div>
            
            <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border);">
                <p style="color: var(--text-tertiary); font-size: 0.75rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #f59e0b;"></span>
                    Please wait while the application is removed
                </p>
            </div>
        </div>
    `;
    
    modal.classList.add('show');
    modal.style.pointerEvents = 'none';
    
    // Call openModal if available
    if (window.openModal) {
        window.openModal();
    }
}

/**
 * Update deletion progress display
 * @param {number} progress - Progress percentage (0-100)
 * @param {string} message - Status message to display
 */
export async function updateDeletionProgress(progress, message) {
    const progressBar = document.getElementById('deletionProgressBar');
    const progressMessage = document.getElementById('deletionProgressMessage');
    const progressSteps = document.getElementById('deletionProgressSteps');
    
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
    
    if (progressMessage) {
        progressMessage.textContent = message;
    }
    
    if (progressSteps) {
        const steps = progressSteps.querySelectorAll('.progress-step');
        steps.forEach((step, index) => {
            if (progress >= (index * 33)) {
                step.classList.add('active');
                const icon = step.querySelector('.progress-step-icon');
                if (progress > ((index + 1) * 33)) {
                    icon.textContent = '🟢';
                    step.classList.remove('pulse');
                } else if (progress >= (index * 33)) {
                    icon.textContent = '🟠';
                    step.classList.add('pulse');
                }
            }
        });
    }
}

/**
 * Hide deletion progress modal and restore page interaction
 */
export function hideDeletionProgress() {
    const modal = document.getElementById('deployModal');
    if (!modal) return;
    
    modal.classList.remove('show');
    modal.style.pointerEvents = 'auto';
    
    // Properly clean up modal state to re-enable page interaction
    const anyModalOpen = Array.from(document.querySelectorAll('.modal.show')).length > 0;
    if (!anyModalOpen) {
        const scrollPosition = parseInt(document.body.style.top || '0') * -1;
        document.body.classList.remove('modal-open');
        document.body.style.top = '';
        
        // Re-enable pointer events on main content
        const mainContent = document.querySelector('.app-container');
        if (mainContent) {
            mainContent.style.pointerEvents = '';
        }
        
        // Restore scroll position
        window.scrollTo(0, scrollPosition);
    }
}

/**
 * Show application logs in a modal
 * @param {string} appId - The application ID
 * @param {string} hostname - The application hostname
 */
export function showAppLogs(appId, hostname) {
    const modal = document.getElementById('deployModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    if (!modal || !modalTitle || !modalBody) {
        console.error('Modal elements not found');
        return;
    }
    
    modalTitle.textContent = `📋 Logs - ${hostname}`;
    
    modalBody.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
                <button class="btn btn-sm btn-secondary" onclick="refreshLogs('${appId}', 'all')">
                    All
                </button>
                <button class="btn btn-sm btn-ghost" onclick="refreshLogs('${appId}', 'docker')">
                    Docker
                </button>
                <button class="btn btn-sm btn-ghost" onclick="refreshLogs('${appId}', 'system')">
                    System
                </button>
                <button class="btn btn-sm btn-ghost" onclick="downloadLogs('${appId}')" style="margin-left: auto;">
                    💾 Download
                </button>
            </div>
        </div>
        
        <div style="background: #1a1a1a; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1rem; height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.875rem; color: #e0e0e0;">
            <div id="logsContent">
                <div style="text-align: center; padding: 2rem; color: var(--text-tertiary);">
                    <div class="loading-spinner" style="display: inline-block; margin-bottom: 1rem;"></div>
                    <div>Loading logs...</div>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 1rem; display: flex; justify-content: space-between; align-items: center;">
            <label style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; color: var(--text-secondary);">
                <input type="checkbox" id="autoRefreshLogs" onchange="toggleAutoRefresh('${appId}')">
                Auto-refresh (5s)
            </label>
            <span style="font-size: 0.75rem; color: var(--text-tertiary);">
                Last updated: <span id="logsTimestamp">-</span>
            </span>
        </div>
    `;
    
    modal.classList.add('show');
    
    // Call openModal if available
    if (window.openModal) {
        window.openModal();
    }
    
    // Load logs
    loadAppLogs(appId, 'all');
    
    // Store cleanup function for when modal closes
    modal._cleanupLogs = () => {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
            console.log('🧹 Logs auto-refresh stopped (modal closed)');
        }
    };
}

/**
 * Show application volumes in a modal
 * @param {string} appId - The application ID
```
 */
export async function showAppVolumes(appId) {
    const authFetch = getAuthFetch();
    const showNotification = getNotification();
    
    try {
        const app = await authFetch(`${API_BASE}/apps/${appId}`);

        if (!app.volumes || app.volumes.length === 0) {
            showNotification('This app has no persistent volumes', 'info');
            return;
        }

        const volumesHtml = app.volumes.map(vol => `
            <tr>
                <td>${vol.container_path}</td>
                <td class="volume-host-path">
                    <code>${vol.host_path}</code>
                    <button class="btn btn-sm btn-ghost" onclick="window.Clipboard?.copyToClipboard?.('${vol.host_path}') || window.copyToClipboard?.('${vol.host_path}')" title="Copy to clipboard">
                        <i data-lucide="copy"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        const modalBody = `
            <div class="volumes-info">
                <p class="help-text">
                    <i data-lucide="info"></i>
                    These are the locations on your Proxmox server where persistent data is stored.
                    <strong>Do not modify these files directly unless you know what you are doing.</strong>
                </p>
                <table class="volumes-table">
                    <thead>
                        <tr>
                            <th>Container Path</th>
                            <th>Host Path (Proxmox)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${volumesHtml}
                    </tbody>
                </table>
            </div>
        `;

        // Call showModal if available
        if (window.showModal) {
            window.showModal('Persistent Volumes', modalBody);
        }
        
        // Reinitialize Lucide icons if available
        if (window.lucide && window.lucide.createIcons) {
            window.lucide.createIcons();
        }

    } catch (error) {
        showNotification('Failed to load volumes', 'error');
        console.error('Error loading volumes:', error);
    }
}

// ============================================================================
// LOG MANAGEMENT FUNCTIONS
// ============================================================================

let autoRefreshInterval = null;
let currentLogType = 'all';

/**
 * Load and display app logs
 * @param {string} appId - The application ID
 * @param {string} logType - Type of logs to display (all, docker, system)
 */
export async function loadAppLogs(appId, logType = 'all') {
    const authFetch = getAuthFetch();
    const logsContent = document.getElementById('logsContent');
    const timestamp = document.getElementById('logsTimestamp');

    if (!logsContent) return;

    currentLogType = logType;

    console.log(`📄 Loading logs for app: ${appId}, type: ${logType}`);

    try {
        // Show loading state
        logsContent.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-tertiary);">
                <div class="loading-spinner" style="display: inline-block; margin-bottom: 1rem;"></div>
                <div>Loading logs...</div>
            </div>
        `;

        // Fetch logs from API
        const url = `${API_BASE}/apps/${appId}/logs`;
        console.log(`📡 Fetching logs from: ${url}`);
        
        const response = await authFetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch logs');
        }

        // Format and display logs
        let logs = '';
        
        if (logType === 'all' || logType === 'docker') {
            if (data.docker_logs) {
                logs += `<div style="color: #22d3ee; font-weight: bold; margin-bottom: 0.5rem;">📦 Docker Logs:</div>`;
                logs += `<pre style="white-space: pre-wrap; word-wrap: break-word; margin-bottom: 1rem;">${escapeHtml(data.docker_logs)}</pre>`;
            }
        }

        if (logType === 'all' || logType === 'system') {
            if (data.system_logs) {
                logs += `<div style="color: #fbbf24; font-weight: bold; margin-bottom: 0.5rem;">⚙️  System Logs:</div>`;
                logs += `<pre style="white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(data.system_logs)}</pre>`;
            }
        }

        if (!logs) {
            logs = '<div style="text-align: center; padding: 2rem; color: var(--text-tertiary);">No logs available</div>';
        }

        logsContent.innerHTML = logs;

        // Update timestamp
        if (timestamp) {
            const now = new Date();
            timestamp.textContent = now.toLocaleTimeString();
        }

        // Scroll to bottom
        logsContent.scrollTop = logsContent.scrollHeight;

    } catch (error) {
        console.error('Error loading logs:', error);
        logsContent.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #ef4444;">
                <div style="margin-bottom: 0.5rem;">❌ Error loading logs</div>
                <div style="font-size: 0.875rem;">${escapeHtml(error.message)}</div>
            </div>
        `;
    }
}

/**
 * Refresh logs with a specific type
 * @param {string} appId - The application ID
 * @param {string} logType - Type of logs to display (all, docker, system)
 */
export function refreshLogs(appId, logType) {
    // Update button states
    const buttons = document.querySelectorAll('.btn-sm');
    buttons.forEach(btn => {
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-ghost');
    });
    
    // Highlight active button
    event.target.classList.remove('btn-ghost');
    event.target.classList.add('btn-secondary');
    
    // Load logs
    loadAppLogs(appId, logType);
}

/**
 * Toggle auto-refresh for logs
 * @param {string} appId - The application ID
 */
export function toggleAutoRefresh(appId) {
    const checkbox = document.getElementById('autoRefreshLogs');
    
    if (!checkbox) return;

    if (checkbox.checked) {
        // Start auto-refresh (every 5 seconds)
        autoRefreshInterval = setInterval(() => {
            loadAppLogs(appId, currentLogType);
        }, 5000);
        console.log('🔄 Auto-refresh enabled for logs');
    } else {
        // Stop auto-refresh
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
        console.log('⏸️  Auto-refresh disabled for logs');
    }
}

/**
 * Download logs as a text file
 * @param {string} appId - The application ID
 */
export async function downloadLogs(appId) {
    const authFetch = getAuthFetch();
    const showNotification = getNotification();

    try {
        const response = await authFetch(`${API_BASE}/apps/${appId}/logs`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch logs');
        }

        // Combine all logs
        let logContent = `Application Logs - ${appId}\n`;
        logContent += `Generated: ${new Date().toLocaleString()}\n`;
        logContent += `${'='.repeat(80)}\n\n`;

        if (data.docker_logs) {
            logContent += `DOCKER LOGS\n${'='.repeat(80)}\n`;
            logContent += data.docker_logs + '\n\n';
        }

        if (data.system_logs) {
            logContent += `SYSTEM LOGS\n${'='.repeat(80)}\n`;
            logContent += data.system_logs + '\n\n';
        }

        // Create and download file
        const blob = new Blob([logContent], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${appId}-logs-${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        showNotification('Logs downloaded successfully', 'success');

    } catch (error) {
        console.error('Error downloading logs:', error);
        showNotification('Failed to download logs', 'error');
    }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
        stopApp,
        showAppDetails,
        showDeletionProgress,
        updateDeletionProgress,
        hideDeletionProgress,
        showAppLogs,
        showAppVolumes,
        loadAppLogs,
        refreshLogs,
        toggleAutoRefresh,
        downloadLogs
    };
    
    // Also expose individual functions for onclick handlers
    window.loadAppLogs = loadAppLogs;
    window.refreshLogs = refreshLogs;
    window.toggleAutoRefresh = toggleAutoRefresh;
    window.downloadLogs = downloadLogs;
}
