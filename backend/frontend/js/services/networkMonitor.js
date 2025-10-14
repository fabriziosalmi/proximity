/**
 * Network Monitoring Service
 * 
 * Provides real-time network status monitoring for Proxmox infrastructure.
 * Polls /api/v1/system/network/metrics every 5 seconds and updates LED indicators.
 * 
 * @module services/networkMonitor
 */

import { authFetch, API_BASE } from './api.js';

class NetworkMonitor {
    constructor() {
        this.metrics = null;
        this.pollInterval = null;
        this.pollIntervalMs = 5000; // 5 seconds
        this.listeners = new Set();
        this.isPolling = false;
    }

    /**
     * Start monitoring network metrics
     */
    startMonitoring() {
        if (this.isPolling) {
            console.log('[NetworkMonitor] Already monitoring');
            return;
        }

        console.log('[NetworkMonitor] Starting network monitoring');
        this.isPolling = true;

        // Initial fetch
        this.fetchMetrics();

        // Poll every 5 seconds
        this.pollInterval = setInterval(() => {
            this.fetchMetrics();
        }, this.pollIntervalMs);
    }

    /**
     * Stop monitoring network metrics
     */
    stopMonitoring() {
        console.log('[NetworkMonitor] Stopping network monitoring');
        this.isPolling = false;

        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    /**
     * Fetch network metrics from API
     */
    async fetchMetrics() {
        try {
            const response = await authFetch(`${API_BASE}/system/network/metrics`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            this.metrics = await response.json();
            
            // Notify all listeners
            this.notifyListeners(this.metrics);
            
        } catch (error) {
            console.error('[NetworkMonitor] Failed to fetch metrics:', error);
            
            // Set degraded metrics on error
            this.metrics = {
                timestamp: new Date().toISOString(),
                nodes: [],
                summary: {
                    total_nodes: 0,
                    healthy_nodes: 0,
                    bridge_status: 'error',
                    dhcp_active: false,
                    internet_connected: false
                },
                error: error.message
            };
            
            this.notifyListeners(this.metrics);
        }
    }

    /**
     * Subscribe to network metrics updates
     * @param {Function} callback - Called with metrics on each update
     * @returns {Function} Unsubscribe function
     */
    subscribe(callback) {
        this.listeners.add(callback);
        
        // Send current metrics immediately if available
        if (this.metrics) {
            callback(this.metrics);
        }
        
        // Return unsubscribe function
        return () => {
            this.listeners.delete(callback);
        };
    }

    /**
     * Notify all listeners of new metrics
     * @param {Object} metrics - Network metrics
     */
    notifyListeners(metrics) {
        this.listeners.forEach(callback => {
            try {
                callback(metrics);
            } catch (error) {
                console.error('[NetworkMonitor] Listener error:', error);
            }
        });
    }

    /**
     * Get current metrics (synchronous)
     * @returns {Object|null} Current metrics or null
     */
    getCurrentMetrics() {
        return this.metrics;
    }

    /**
     * Get LED status class based on metric value
     * @param {string} metric - Metric name (bridge_status, dhcp_active, etc)
     * @returns {string} LED class name
     */
    getLEDClass(metric) {
        if (!this.metrics || !this.metrics.summary) {
            return 'status-led-off';
        }

        const summary = this.metrics.summary;

        switch (metric) {
            case 'bridge':
                if (summary.bridge_status === 'active') return 'status-led-active';
                if (summary.bridge_status === 'warning') return 'status-led-warning';
                return 'status-led-error';

            case 'dhcp':
                return summary.dhcp_active ? 'status-led-pulse' : 'status-led-off';

            case 'gateway':
                // Blink if healthy nodes > 0 (simulates TX/RX activity)
                return summary.healthy_nodes > 0 ? 'status-led-blink' : 'status-led-off';

            case 'internet':
                return summary.internet_connected ? 'status-led-active' : 'status-led-error';

            default:
                return 'status-led-off';
        }
    }

    /**
     * Get human-readable status text
     * @param {string} metric - Metric name
     * @returns {string} Status text
     */
    getStatusText(metric) {
        if (!this.metrics || !this.metrics.summary) {
            return 'Unknown';
        }

        const summary = this.metrics.summary;

        switch (metric) {
            case 'bridge':
                return summary.bridge_status.charAt(0).toUpperCase() + summary.bridge_status.slice(1);

            case 'dhcp':
                return summary.dhcp_active ? 'Active' : 'Inactive';

            case 'gateway':
                return summary.healthy_nodes > 0 ? 'Active' : 'Unreachable';

            case 'internet':
                return summary.internet_connected ? 'Connected' : 'Disconnected';

            case 'nodes':
                return `${summary.healthy_nodes}/${summary.total_nodes} Online`;

            default:
                return 'Unknown';
        }
    }
}

// Create singleton instance
export const networkMonitor = new NetworkMonitor();

// Export class for testing
export { NetworkMonitor };
