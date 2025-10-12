/**
 * Monitoring Modal Module
 *
 * Handles real-time resource monitoring:
 * - CPU, Memory, and Disk usage gauges
 * - Real-time polling (every 5 seconds)
 * - Status indicators (running/stopped/error)
 * - Uptime tracking
 * - Cache indicator for data freshness
 * - Automatic cleanup on modal close
 */

import * as API from '../services/api.js';
import { showNotification } from '../utils/notifications.js';

// Monitoring state
let monitoringState = {
    activeAppId: null,
    pollInterval: null,
    POLL_INTERVAL_MS: 5000  // Poll every 5 seconds when viewing
};

/**
 * Show monitoring modal with real-time resource usage gauges
 * @param {string} appId - App ID
 * @param {string} appName - App name for display
 */
export function showMonitoringModal(appId, appName) {
    const modalBody = `
        <div class="monitoring-container">
            <div class="monitoring-header">
                <i data-lucide="activity" style="width: 24px; height: 24px; color: var(--primary);"></i>
                <div>
                    <h3 style="margin: 0; color: var(--text-primary);">Resource Monitoring</h3>
                    <p style="margin: 0.25rem 0 0 0; color: var(--text-secondary); font-size: 0.875rem;">
                        Real-time container metrics
                    </p>
                </div>
            </div>

            <!-- Status -->
            <div class="monitoring-status" id="monitoring-status">
                <div class="status-indicator status-unknown">
                    <span class="status-dot"></span>
                    <span id="status-text">Loading...</span>
                </div>
                <div class="monitoring-meta">
                    <span id="uptime-text">--</span>
                    <span class="meta-separator">•</span>
                    <span id="timestamp-text">Never updated</span>
                </div>
            </div>

            <!-- Gauges Grid -->
            <div class="monitoring-gauges">
                <!-- CPU Gauge -->
                <div class="gauge-card">
                    <div class="gauge-header">
                        <i data-lucide="cpu" class="gauge-icon"></i>
                        <span class="gauge-title">CPU Usage</span>
                    </div>
                    <div class="gauge-value" id="cpu-value">--%</div>
                    <div class="gauge-bar-container">
                        <div class="gauge-bar" id="cpu-bar" style="width: 0%;"></div>
                    </div>
                    <div class="gauge-label">Processor Load</div>
                </div>

                <!-- Memory Gauge -->
                <div class="gauge-card">
                    <div class="gauge-header">
                        <i data-lucide="database" class="gauge-icon"></i>
                        <span class="gauge-title">Memory Usage</span>
                    </div>
                    <div class="gauge-value" id="mem-value">--%</div>
                    <div class="gauge-bar-container">
                        <div class="gauge-bar" id="mem-bar" style="width: 0%;"></div>
                    </div>
                    <div class="gauge-label" id="mem-label">-- GB / -- GB</div>
                </div>

                <!-- Disk Gauge -->
                <div class="gauge-card">
                    <div class="gauge-header">
                        <i data-lucide="hard-drive" class="gauge-icon"></i>
                        <span class="gauge-title">Disk Usage</span>
                    </div>
                    <div class="gauge-value" id="disk-value">--%</div>
                    <div class="gauge-bar-container">
                        <div class="gauge-bar" id="disk-bar" style="width: 0%;"></div>
                    </div>
                    <div class="gauge-label" id="disk-label">-- GB / -- GB</div>
                </div>
            </div>

            <!-- Cache Indicator -->
            <div class="monitoring-footer">
                <div class="cache-indicator" id="cache-indicator">
                    <i data-lucide="zap" style="width: 14px; height: 14px;"></i>
                    <span id="cache-text">--</span>
                </div>
            </div>
        </div>
    `;

    // Use legacy showModal function (from app.js) for now
    if (typeof window.showModal === 'function') {
        window.showModal('Monitoring: ' + appName, modalBody);
    } else {
        console.error('showModal function not available');
        showNotification('Failed to open monitoring modal', 'error');
        return;
    }

    // Initialize Lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // Start monitoring
    monitoringState.activeAppId = appId;
    startMonitoringPolling(appId);

    // Setup cleanup on modal close
    const modal = document.querySelector('.modal');
    const closeHandler = () => {
        stopMonitoringPolling();
        modal.removeEventListener('click', closeHandler);
    };

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeHandler();
        }
    });

    // Close on close button
    const closeButton = modal.querySelector('.modal-close, .btn-ghost');
    if (closeButton) {
        closeButton.addEventListener('click', closeHandler, { once: true });
    }
}

/**
 * Start polling for monitoring data
 * Only polls when user is viewing the monitoring modal
 * @param {string} appId - App ID
 */
export function startMonitoringPolling(appId) {
    // Clear any existing interval
    stopMonitoringPolling();

    // Immediate first fetch
    updateMonitoringData(appId);

    // Setup polling
    monitoringState.pollInterval = setInterval(() => {
        updateMonitoringData(appId);
    }, monitoringState.POLL_INTERVAL_MS);

    console.log(`📊 Started monitoring polling for app ${appId} (interval: ${monitoringState.POLL_INTERVAL_MS}ms)`);
}

/**
 * Stop polling for monitoring data
 * CRITICAL: Must be called when modal closes to prevent resource leaks
 */
export function stopMonitoringPolling() {
    if (monitoringState.pollInterval) {
        clearInterval(monitoringState.pollInterval);
        monitoringState.pollInterval = null;
        console.log('📊 Stopped monitoring polling');
    }
    monitoringState.activeAppId = null;
}

/**
 * Fetch and display monitoring data
 * @param {string} appId - App ID
 */
async function updateMonitoringData(appId) {
    try {
        const stats = await API.getAppStats(appId);

        // Update status
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.getElementById('status-text');

        if (statusIndicator && statusText) {
            statusIndicator.className = `status-indicator status-${stats.status}`;
            statusText.textContent = stats.status.charAt(0).toUpperCase() + stats.status.slice(1);
        }

        // Update uptime
        const uptimeText = document.getElementById('uptime-text');
        if (uptimeText) {
            uptimeText.textContent = formatUptime(stats.uptime_seconds);
        }

        // Update timestamp
        const timestampText = document.getElementById('timestamp-text');
        if (timestampText) {
            const updateTime = new Date(stats.timestamp);
            const now = new Date();
            const secondsAgo = Math.floor((now - updateTime) / 1000);
            timestampText.textContent = secondsAgo < 2 ? 'Just now' : `${secondsAgo}s ago`;
        }

        // Update CPU
        updateGauge('cpu', stats.cpu_percent, '%');

        // Update Memory
        updateGauge('mem', stats.mem_percent, '%');
        const memLabel = document.getElementById('mem-label');
        if (memLabel) {
            memLabel.textContent = `${stats.mem_used_gb} GB / ${stats.mem_total_gb} GB`;
        }

        // Update Disk
        updateGauge('disk', stats.disk_percent, '%');
        const diskLabel = document.getElementById('disk-label');
        if (diskLabel) {
            diskLabel.textContent = `${stats.disk_used_gb} GB / ${stats.disk_total_gb} GB`;
        }

        // Update cache indicator
        const cacheIndicator = document.getElementById('cache-indicator');
        const cacheText = document.getElementById('cache-text');
        if (cacheIndicator && cacheText) {
            if (stats.cached) {
                cacheIndicator.classList.add('cached');
                cacheText.textContent = 'Cached data';
            } else {
                cacheIndicator.classList.remove('cached');
                cacheText.textContent = 'Live data';
            }
        }

    } catch (error) {
        console.error('Failed to update monitoring data:', error);

        // Show error state
        const statusText = document.getElementById('status-text');
        if (statusText) {
            statusText.textContent = 'Error fetching stats';
        }
    }
}

/**
 * Update a gauge element with new value
 * @param {string} gaugeId - Gauge ID prefix (cpu, mem, disk)
 * @param {number} percent - Percentage value
 * @param {string} suffix - Value suffix (default: '%')
 */
function updateGauge(gaugeId, percent, suffix = '%') {
    const valueElement = document.getElementById(`${gaugeId}-value`);
    const barElement = document.getElementById(`${gaugeId}-bar`);

    if (!valueElement || !barElement) return;

    // Update value text
    valueElement.textContent = `${percent.toFixed(1)}${suffix}`;

    // Update bar width
    barElement.style.width = `${Math.min(percent, 100)}%`;

    // Update bar color based on thresholds
    barElement.className = 'gauge-bar';
    if (percent >= 90) {
        barElement.classList.add('gauge-critical');
    } else if (percent >= 75) {
        barElement.classList.add('gauge-warning');
    } else {
        barElement.classList.add('gauge-ok');
    }
}

/**
 * Format uptime seconds to human-readable string
 * @param {number} seconds - Uptime in seconds
 * @returns {string} Formatted uptime
 */
export function formatUptime(seconds) {
    if (!seconds || seconds < 0) return '--';

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
        return `${days}d ${hours}h`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

// Expose functions globally for legacy compatibility
if (typeof window !== 'undefined') {
    window.showMonitoringModal = showMonitoringModal;
    window.startMonitoringPolling = startMonitoringPolling;
    window.stopMonitoringPolling = stopMonitoringPolling;
    window.formatUptime = formatUptime;
}
