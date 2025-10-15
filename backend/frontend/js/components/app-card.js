/**
 * App Card Component
 * Handles rendering and event attachment for deployed and catalog app cards
 */

import { renderAppIcon, formatDate } from '../utils/ui-helpers.js';
import { authFetch, API_BASE } from '../services/api.js';

/**
 * Populate deployed app card with data
 * @param {DocumentFragment} cardElement - Cloned template
 * @param {Object} app - App data
 */
export function populateDeployedCard(cardElement, app) {
    // ============================================================================
    // Basic App Information
    // ============================================================================
    
    // Populate icon - deployed cards use .app-icon-lg
    const iconContainer = cardElement.querySelector('.app-icon-lg');
    if (iconContainer) {
        renderAppIcon(iconContainer, app);
    }
    
    // Populate text fields (safe textContent prevents XSS)
    cardElement.querySelector('.app-name').textContent = app.name || app.hostname || 'Unknown';
    
    // Add data attribute for E2E tests
    const appCard = cardElement.querySelector('.app-card');
    if (appCard) {
        appCard.setAttribute('data-hostname', app.hostname || '');
    }
    
    // ============================================================================
    // Connection URL
    // ============================================================================
    
    const urlElement = cardElement.querySelector('.connection-link');
    const appUrl = (app.url && app.url !== 'None' && app.url !== 'null') ? app.url : null;
    
    if (urlElement) {
        if (appUrl) {
            urlElement.href = appUrl;
            urlElement.textContent = appUrl;
            urlElement.style.display = '';
        } else {
            urlElement.textContent = 'No URL';
            urlElement.href = '#';
            urlElement.style.pointerEvents = 'none';
            urlElement.style.opacity = '0.5';
        }
    }
    
    // ============================================================================
    // Metadata (Node, LXC ID, Creation Date)
    // ============================================================================

    const nodeElement = cardElement.querySelector('.node-value');
    if (nodeElement) {
        nodeElement.textContent = app.node || 'Unknown';
    }

    const lxcElement = cardElement.querySelector('.lxc-id-value');
    if (lxcElement) {
        lxcElement.textContent = `LXC ${app.lxc_id || 'N/A'}`;
    }

    const createdElement = cardElement.querySelector('.date-value');
    if (createdElement) {
        createdElement.textContent = formatDate(app.created_at);
    }
    
    // ============================================================================
    // Status Indication - Smart LED color based on app state and load
    // ============================================================================
    
    const status = app.status ? app.status.toLowerCase() : 'stopped';
    const statusElement = cardElement.querySelector('.status-indicator');
    
    // Calculate CPU and RAM usage percentages
    let cpuUsage = app.stats?.cpu_usage || app.cpu_usage || 0;
    let ramUsageMB = app.stats?.memory_usage || app.memory_usage || 0;
    let ramMaxMB = app.stats?.memory_max || app.memory_max || 1024;
    const ramPercentage = ramMaxMB > 0 ? (ramUsageMB / ramMaxMB) * 100 : 0;
    
    // Determine smart status class based on priority:
    // 1. Maintenance operations (backup, update) -> Orange LED
    // 2. High load (CPU > 80% or RAM > 85%) while running -> Yellow LED
    // 3. Standard states (running, stopped, error, in-progress)
    
    if (statusElement) {
        // Remove all existing status classes
        statusElement.classList.remove(
            'status-running', 
            'status-error', 
            'status-in-progress', 
            'status-stopped',
            'status-high-load',
            'status-maintenance'
        );
        
        // Maintenance operations have highest priority
        const maintenanceStates = ['backing_up', 'updating', 'restoring', 'backing up', 'update in progress'];
        const isInMaintenance = maintenanceStates.some(state => status.includes(state));
        
        if (isInMaintenance) {
            // Orange LED - App is being backed up or updated
            statusElement.classList.add('status-maintenance');
        } else if (status === 'running') {
            // Check if under high load
            const isHighLoad = cpuUsage > 80 || ramPercentage > 85;
            
            if (isHighLoad) {
                // Yellow LED - App running but under heavy load
                statusElement.classList.add('status-high-load');
            } else {
                // Cyan LED - Normal running state
                statusElement.classList.add('status-running');
            }
        } else if (status === 'error' || status === 'failed') {
            // Red LED - Error state
            statusElement.classList.add('status-error');
        } else if (status === 'creating' || status === 'starting' || status === 'stopping') {
            // Amber LED (pulsing) - Transitional state
            statusElement.classList.add('status-in-progress');
        } else {
            // Red LED - Stopped or unknown state
            statusElement.classList.add('status-stopped');
        }
    }
    
    // Store current load state on card element for polling updates
    if (cardElement.tagName === 'DIV') {
        cardElement.setAttribute('data-cpu-usage', cpuUsage);
        cardElement.setAttribute('data-ram-percentage', ramPercentage.toFixed(1));
    }
    
    // ============================================================================
    // Action Bar - Conditional Button States
    // ============================================================================
    
    const isRunning = status === 'running';
    
    // Update toggle-status button icon based on app status
    const toggleBtn = cardElement.querySelector('[data-action="toggle-status"]');
    if (toggleBtn) {
        const icon = toggleBtn.querySelector('i[data-lucide]');
        if (icon) {
            if (isRunning) {
                // App is running - show pause/stop icon
                icon.setAttribute('data-lucide', 'pause');
                toggleBtn.setAttribute('data-tooltip', 'Stop App');
            } else {
                // App is stopped - show play icon
                icon.setAttribute('data-lucide', 'play');
                toggleBtn.setAttribute('data-tooltip', 'Start App');
            }
        }
    }
    
    // Actions that require app to be running
    const runningOnlyActions = ['open-external', 'canvas', 'restart', 'monitoring'];
    
    runningOnlyActions.forEach(action => {
        const btn = cardElement.querySelector(`[data-action="${action}"]`);
        if (btn) {
            if (!isRunning) {
                btn.classList.add('disabled');
                btn.setAttribute('disabled', 'true');
            } else {
                btn.classList.remove('disabled');
                btn.removeAttribute('disabled');
            }
        }
    });
    
    // Special handling for open-external - requires both running AND URL
    const openExternalBtn = cardElement.querySelector('[data-action="open-external"]');
    if (openExternalBtn) {
        if (!isRunning || !appUrl) {
            openExternalBtn.classList.add('disabled');
            openExternalBtn.setAttribute('disabled', 'true');
        } else {
            openExternalBtn.classList.remove('disabled');
            openExternalBtn.removeAttribute('disabled');
        }
    }
    
    // Canvas button - only show if app has iframe_url/url available
    const canvasBtn = cardElement.querySelector('[data-action="canvas"]');
    if (canvasBtn) {
        const hasCanvasUrl = appUrl || app.iframe_url;
        if (!hasCanvasUrl) {
            canvasBtn.style.display = 'none';
        } else {
            canvasBtn.style.display = '';
        }
    }
    
    // ============================================================================
    // Real-time Resource Metrics (CPU & RAM)
    // ============================================================================
    
    // Add data-app-id to metric bars for polling
    const cpuBar = cardElement.querySelector('.cpu-bar');
    const ramBar = cardElement.querySelector('.ram-bar');
    if (cpuBar) cpuBar.setAttribute('data-app-id', app.id);
    if (ramBar) ramBar.setAttribute('data-app-id', app.id);
    
    updateResourceMetrics(cardElement, app);
}

/**
 * Update resource metrics (CPU & RAM) for an app card
 * @param {DocumentFragment|HTMLElement} cardElement - Card element
 * @param {Object} app - App data with stats
 */
export function updateResourceMetrics(cardElement, app) {
    const cpuBar = cardElement.querySelector('.cpu-bar');
    const ramBar = cardElement.querySelector('.ram-bar');
    const cpuValueSpan = cardElement.querySelector('.cpu-value');
    const ramValueSpan = cardElement.querySelector('.ram-value');

    if (!cpuBar || !ramBar) {
        console.warn('⚠️ Metric bars not found for app:', app.name);
        return;
    }

    // Check if app is running
    const status = app.status ? app.status.toLowerCase() : 'stopped';
    const isRunning = status === 'running';

    // Hide metrics if app is not running
    if (!isRunning) {
        cpuBar.style.width = '0%';
        ramBar.style.width = '0%';
        cpuBar.classList.remove('high-usage', 'critical-usage');
        ramBar.classList.remove('high-usage', 'critical-usage');
        if (cpuValueSpan) cpuValueSpan.textContent = '0%';
        if (ramValueSpan) ramValueSpan.textContent = '0 MB';
        return;
    }

    // Get CPU usage from app stats
    let cpuUsage = app.stats?.cpu_usage || app.cpu_usage || 0;

    // For testing: if no real CPU data, generate a random value
    if (cpuUsage === 0) {
        cpuUsage = Math.floor(Math.random() * 100);
    }

    // Update CPU bar
    cpuBar.style.width = `${cpuUsage}%`;
    if (cpuValueSpan) cpuValueSpan.textContent = `${cpuUsage}%`;

    cpuBar.classList.remove('high-usage', 'critical-usage');
    if (cpuUsage >= 95) {
        cpuBar.classList.add('critical-usage');
    } else if (cpuUsage >= 80) {
        cpuBar.classList.add('high-usage');
    }

    // Get RAM usage from app stats
    let ramUsageMB = app.stats?.memory_usage || app.memory_usage || 0;
    let ramMaxMB = app.stats?.memory_max || app.memory_max || 1024;

    // For testing: if no real RAM data, generate random values
    if (ramUsageMB === 0) {
        ramMaxMB = 1024;
        ramUsageMB = Math.floor(Math.random() * 800);
    }

    const ramPercentage = (ramUsageMB / ramMaxMB) * 100;

    // Update RAM bar
    ramBar.style.width = `${ramPercentage}%`;
    if (ramValueSpan) ramValueSpan.textContent = `${ramUsageMB} MB`;

    ramBar.classList.remove('high-usage', 'critical-usage');
    if (ramPercentage >= 95) {
        ramBar.classList.add('critical-usage');
    } else if (ramPercentage >= 80) {
        ramBar.classList.add('high-usage');
    }

    // Store app ID for polling updates
    cpuBar.setAttribute('data-app-id', app.id);
    ramBar.setAttribute('data-app-id', app.id);
}

/**
 * Attach event listeners to deployed app card
 * @param {DocumentFragment} cardElement - Cloned template
 * @param {Object} app - App data
 */
export function attachDeployedCardEvents(cardElement, app) {
    const isRunning = app.status === 'running';
    const appUrl = (app.url && app.url !== 'None' && app.url !== 'null') ? app.url : null;

    // Action button handlers - call global window functions
    const actions = {
        'toggle-status': () => window.controlApp(app.id, isRunning ? 'stop' : 'start'),
        'open-external': () => appUrl && window.open(appUrl, '_blank'),
        'view-logs': () => window.showAppLogs(app.id, app.hostname),
        'console': () => window.showAppConsole(app.id, app.hostname),
        'backups': () => window.showBackupModal(app.id),
        'update': () => window.showUpdateModal(app.id),
        'volumes': () => window.showAppVolumes(app.id),
        'monitoring': () => window.showMonitoringModal(app.id, app.name),
        'canvas': () => window.openCanvas({
            id: app.id,
            name: app.name,
            hostname: app.hostname,
            iframe_url: appUrl || app.url,
            url: appUrl || app.url,
            status: app.status
        }),
        'restart': () => window.controlApp(app.id, isRunning ? 'restart' : 'start'),
        'clone': () => window.showCloneModal(app.id, app.name),
        'edit-config': () => window.showEditConfigModal(app.id, app.name),
        'delete': () => window.confirmDeleteApp(app.id, app.name)
    };

    // Attach event listeners to action buttons
    cardElement.querySelectorAll('.action-icon').forEach(btn => {
        const action = btn.dataset.action;
        if (actions[action]) {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                actions[action]();
            });
        }
    });

    // Canvas click on whole card (if running and has URL)
    const card = cardElement.querySelector('.app-card');
    if (isRunning && appUrl) {
        card.style.cursor = 'pointer';
        card.title = 'Click to open in canvas';
        card.addEventListener('click', (e) => {
            // Don't trigger if clicking on action buttons or links
            if (!e.target.closest('.action-icon, .connection-link')) {
                window.openCanvas({
                    id: app.id,
                    name: app.name,
                    hostname: app.hostname,
                    iframe_url: appUrl,
                    url: appUrl,
                    status: app.status
                });
            }
        });
    } else {
        card.style.cursor = 'default';
        card.title = 'App must be running to open in canvas';
    }

    // Prevent link propagation
    const urlLink = cardElement.querySelector('.connection-link');
    if (urlLink) {
        urlLink.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
}

/**
 * Populate catalog app card with data
 * @param {DocumentFragment} cardElement - Cloned template
 * @param {Object} app - App data
 */
export function populateCatalogCard(cardElement, app) {
    // Populate icon
    const iconContainer = cardElement.querySelector('.app-icon-md');
    renderAppIcon(iconContainer, app);

    // Populate text (safe textContent)
    cardElement.querySelector('.app-name').textContent = app.name || 'Unknown';
    cardElement.querySelector('.category-badge').textContent = app.category || 'Other';
    cardElement.querySelector('.app-description-compact').textContent = app.description || 'No description available';
    cardElement.querySelector('.cpu-value').textContent = `${app.min_cpu || 1} vCPU`;
    cardElement.querySelector('.memory-value').textContent = `${app.min_memory || 512}MB`;
}

/**
 * Attach event listeners to catalog app card
 * @param {DocumentFragment} cardElement - Cloned template
 * @param {Object} app - App data
 */
export function attachCatalogCardEvents(cardElement, app) {
    const card = cardElement.querySelector('.app-card');
    if (!card) {
        console.error('❌ Could not find .app-card in catalog card template!');
        return;
    }
    card.style.cursor = 'pointer';
    card.addEventListener('click', (e) => {
        console.log(`🖱️ Catalog card clicked: ${app.name} (id: ${app.id})`);
        console.log(`   Checking window.showDeployModal:`, typeof window.showDeployModal);
        if (typeof window.showDeployModal === 'function') {
            console.log(`   ✓ Calling showDeployModal with id: ${app.id}`);
            try {
                window.showDeployModal(app.id);
                console.log(`   ✅ showDeployModal call completed`);
            } catch (error) {
                console.error(`   ❌ Error calling showDeployModal:`, error);
            }
        } else {
            console.error(`   ❌ window.showDeployModal is not a function!`);
        }
    });
    console.log(`✅ Click handler attached to catalog card: ${app.name}`);
}

/**
 * Render app card using template cloning (MASTER FUNCTION)
 * @param {Object} app - App data
 * @param {HTMLElement} container - Container to append card to
 * @param {boolean} isDeployed - Whether this is a deployed app card
 * @param {boolean} attachEvents - Whether to attach event listeners (default: false for delegation)
 */
export function renderAppCard(app, container, isDeployed = false, attachEvents = false) {
    const templateId = isDeployed ? 'deployed-app-card-template' : 'catalog-app-card-template';
    const template = document.getElementById(templateId);

    if (!template) {
        console.error(`❌ Template ${templateId} not found in DOM!`);
        console.error(`App data:`, app);
        return;
    }

    // Clone template
    const clone = template.content.cloneNode(true);

    // Populate card
    if (isDeployed) {
        populateDeployedCard(clone, app);
        // PERFORMANCE: Event delegation handles clicks, no individual listeners needed
        if (attachEvents) {
            attachDeployedCardEvents(clone, app);
        }
    } else {
        populateCatalogCard(clone, app);
        // Catalog cards still need individual listeners (not as many)
        attachCatalogCardEvents(clone, app);
    }

    // Append to container
    container.appendChild(clone);
}

/**
 * Start polling for resource metrics updates (CPU & RAM)
 * Called when Apps view is shown
 * @param {Object} state - Global app state
 * @returns {number} - Interval ID for cleanup
 */
export function startCPUPolling(state) {
    // Poll every 3 seconds
    const intervalId = setInterval(async () => {
        // Only poll if we're on the apps view
        if (state.currentView !== 'apps') {
            clearInterval(intervalId);
            return;
        }

        try {
            // Fetch updated app stats using authFetch
            const response = await authFetch(`${API_BASE}/apps`);

            if (response.ok) {
                const apps = await response.json();

                // Update metrics for all visible apps
                apps.forEach(app => {
                    const cpuBar = document.querySelector(`.cpu-bar[data-app-id="${app.id}"]`);
                    const ramBar = document.querySelector(`.ram-bar[data-app-id="${app.id}"]`);

                    if (!cpuBar || !ramBar) {
                        return;
                    }

                    // Check if app is running
                    const status = app.status ? app.status.toLowerCase() : 'stopped';
                    const isRunning = status === 'running';

                    if (!isRunning) {
                        // Hide metrics for stopped apps
                        cpuBar.style.width = '0%';
                        ramBar.style.width = '0%';
                        cpuBar.classList.remove('high-usage', 'critical-usage');
                        ramBar.classList.remove('high-usage', 'critical-usage');
                        
                        const cpuValueSpan = cpuBar.closest('.metric-item')?.querySelector('.cpu-value');
                        const ramValueSpan = ramBar.closest('.metric-item')?.querySelector('.ram-value');
                        if (cpuValueSpan) cpuValueSpan.textContent = '0%';
                        if (ramValueSpan) ramValueSpan.textContent = '0 MB';
                    } else {
                        // For running apps, fetch current stats
                        fetchAndUpdateAppStats(app.id, cpuBar, ramBar);
                    }
                });

                // Update state.deployedApps status only, preserve existing stats
                state.deployedApps.forEach(stateApp => {
                    const updatedApp = apps.find(a => a.id === stateApp.id);
                    if (updatedApp) {
                        stateApp.status = updatedApp.status;
                        stateApp.url = updatedApp.url;
                        stateApp.iframe_url = updatedApp.iframe_url;
                    }
                });
            } else if (response.status === 401) {
                console.error('❌ Authentication failed in CPU polling');
                clearInterval(intervalId);
            } else {
                console.error(`❌ Polling failed with status ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Error polling resource metrics:', error);
            // Don't stop polling on network errors, just log and continue
        }
    }, 3000); // Poll every 3 seconds

    return intervalId;
}

/**
 * Fetch and update stats for a specific app
 * @param {string} appId - App ID
 * @param {HTMLElement} cpuBar - CPU bar element
 * @param {HTMLElement} ramBar - RAM bar element
 */
async function fetchAndUpdateAppStats(appId, cpuBar, ramBar) {
    try {
        const response = await authFetch(`${API_BASE}/apps/${appId}/stats/current`);

        if (response.ok) {
            const stats = await response.json();

            // Update CPU - use cpu_percent from API
            const cpuUsage = Math.round(stats.cpu_percent || 0);
            cpuBar.style.width = `${cpuUsage}%`;

            const cpuValueSpan = cpuBar.closest('.metric-item')?.querySelector('.cpu-value');
            if (cpuValueSpan) cpuValueSpan.textContent = `${cpuUsage}%`;

            cpuBar.classList.remove('high-usage', 'critical-usage');
            if (cpuUsage >= 95) {
                cpuBar.classList.add('critical-usage');
            } else if (cpuUsage >= 80) {
                cpuBar.classList.add('high-usage');
            }

            // Update RAM - convert GB to MB for display
            const ramUsageMB = Math.round((stats.mem_used_gb || 0) * 1024);
            const ramMaxMB = Math.round((stats.mem_total_gb || 1) * 1024);
            const ramPercentage = ramMaxMB > 0 ? (ramUsageMB / ramMaxMB) * 100 : 0;

            ramBar.style.width = `${ramPercentage}%`;

            const ramValueSpan = ramBar.closest('.metric-item')?.querySelector('.ram-value');
            if (ramValueSpan) ramValueSpan.textContent = `${ramUsageMB} MB`;

            ramBar.classList.remove('high-usage', 'critical-usage');
            if (ramPercentage >= 95) {
                ramBar.classList.add('critical-usage');
            } else if (ramPercentage >= 80) {
                ramBar.classList.add('high-usage');
            }
            
            // ============================================================================
            // Update Status LED based on load
            // ============================================================================
            
            // Find the app card and status indicator
            const appCard = cpuBar.closest('.app-card');
            const statusElement = appCard?.querySelector('.status-indicator');
            
            if (statusElement && appCard) {
                // Get current status from card
                const currentStatus = appCard.classList.contains('status-running') ? 'running' :
                                    appCard.classList.contains('status-stopped') ? 'stopped' :
                                    appCard.classList.contains('status-error') ? 'error' : 'running';
                
                // Only update LED for running apps (don't override stopped/error states)
                if (currentStatus === 'running') {
                    const isHighLoad = cpuUsage > 80 || ramPercentage > 85;
                    
                    // Check if currently in maintenance (don't override maintenance state)
                    const isInMaintenance = statusElement.classList.contains('status-maintenance');
                    
                    if (!isInMaintenance) {
                        // Remove load-related classes
                        statusElement.classList.remove('status-running', 'status-high-load');
                        
                        if (isHighLoad) {
                            // Switch to yellow LED for high load
                            statusElement.classList.add('status-high-load');
                        } else {
                            // Switch back to cyan LED for normal operation
                            statusElement.classList.add('status-running');
                        }
                    }
                }
            }
        }
    } catch (error) {
        // Silent fail - don't spam console during polling
    }
}
