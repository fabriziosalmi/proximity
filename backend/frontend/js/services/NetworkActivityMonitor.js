/**
 * NetworkActivityMonitor - Monitors network TX/RX activity in real-time
 * 
 * Polls network statistics periodically, calculates byte deltas, and triggers
 * visual LED animations based on actual network traffic.
 */

import * as API from './api.js';
import { isAuthenticated } from './api.js';

class NetworkActivityMonitor {
    constructor(pollInterval = 2500) { // 2.5 seconds
        this.pollInterval = pollInterval;
        this.previousStats = new Map(); // node/vmid -> {netin, netout, timestamp}
        this.subscribers = new Map(); // id -> {txLed, rxLed, onActivity}
        this.intervalId = null;
        this.activityThreshold = 1024; // Minimum bytes/sec to trigger LED (1 KB/s)
    }

    /**
     * Start monitoring network activity
     */
    start() {
        if (this.intervalId) {
            console.warn('NetworkActivityMonitor already started');
            return;
        }

        console.log('Starting NetworkActivityMonitor...');
        this.intervalId = setInterval(() => this.poll(), this.pollInterval);
        this.poll(); // Immediate first poll
    }

    /**
     * Stop monitoring
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('NetworkActivityMonitor stopped');
        }
    }

    /**
     * Subscribe a node or container for network activity monitoring
     * @param {string} id - Unique identifier (node name or vmid)
     * @param {HTMLElement} txLed - TX LED element
     * @param {HTMLElement} rxLed - RX LED element
     * @param {Function} onActivity - Optional callback(txActive, rxActive, txRate, rxRate)
     */
    subscribe(id, txLed, rxLed, onActivity = null) {
        this.subscribers.set(id, { txLed, rxLed, onActivity });
        console.log(`Subscribed ${id} for network activity monitoring`);
    }

    /**
     * Unsubscribe from monitoring
     * @param {string} id - Identifier to unsubscribe
     */
    unsubscribe(id) {
        this.subscribers.delete(id);
        this.previousStats.delete(id);
    }

    /**
     * Poll network statistics and update LEDs
     */
    async poll() {
        // Skip polling if not authenticated
        if (!isAuthenticated()) {
            return;
        }

        try {
            const now = Date.now();

            // Fetch all nodes and their stats
            const nodes = await API.getNodes();

            // Process nodes
            for (const node of nodes) {
                if (!this.subscribers.has(node.node)) continue;
                
                this.updateActivity(
                    node.node,
                    node.netin || 0,
                    node.netout || 0,
                    now
                );
            }

            // Fetch all apps and their stats
            const apps = await API.getApps();
            
            // Process each app's network stats
            for (const app of apps) {
                const vmId = `vm-${app.lxc_id}`;
                if (!this.subscribers.has(vmId)) continue;
                
                try {
                    // Fetch individual app stats
                    const stats = await API.getAppStats(app.id);
                    
                    this.updateActivity(
                        vmId,
                        stats.network_in || 0,
                        stats.network_out || 0,
                        now
                    );
                } catch (error) {
                    console.warn(`Failed to fetch stats for app ${app.id}:`, error);
                }
            }

        } catch (error) {
            console.error('NetworkActivityMonitor poll error:', error);
        }
    }

    /**
     * Update activity for a specific entity
     * @param {string} id - Entity identifier
     * @param {number} netin - Total bytes received
     * @param {number} netout - Total bytes transmitted
     * @param {number} timestamp - Current timestamp
     */
    updateActivity(id, netin, netout, timestamp) {
        const subscriber = this.subscribers.get(id);
        if (!subscriber) return;

        const previous = this.previousStats.get(id);
        
        if (!previous) {
            // First reading - just store it
            this.previousStats.set(id, { netin, netout, timestamp });
            this.setLedState(subscriber.txLed, false);
            this.setLedState(subscriber.rxLed, false);
            return;
        }

        // Calculate deltas
        const timeDelta = (timestamp - previous.timestamp) / 1000; // seconds
        if (timeDelta <= 0) return; // Prevent division by zero

        const rxBytes = netin - previous.netin;
        const txBytes = netout - previous.netout;

        // Calculate rates (bytes per second)
        const rxRate = Math.max(0, rxBytes / timeDelta);
        const txRate = Math.max(0, txBytes / timeDelta);

        // Determine if activity is significant
        const txActive = txRate >= this.activityThreshold;
        const rxActive = rxRate >= this.activityThreshold;

        // Update LEDs
        this.setLedState(subscriber.txLed, txActive);
        this.setLedState(subscriber.rxLed, rxActive);

        // Call subscriber callback if provided
        if (subscriber.onActivity) {
            subscriber.onActivity(txActive, rxActive, txRate, rxRate);
        }

        // Store current stats for next iteration
        this.previousStats.set(id, { netin, netout, timestamp });
    }

    /**
     * Set LED visual state
     * @param {HTMLElement} led - LED element
     * @param {boolean} active - Whether activity is detected
     */
    setLedState(led, active) {
        if (!led) return;

        if (active) {
            led.classList.add('led-active');
        } else {
            led.classList.remove('led-active');
        }
    }

    /**
     * Clear all subscriptions and stats
     */
    reset() {
        this.subscribers.clear();
        this.previousStats.clear();
    }
}

// Create singleton instance
const networkActivityMonitor = new NetworkActivityMonitor();

// Auto-start when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        networkActivityMonitor.start();
    });
} else {
    networkActivityMonitor.start();
}

export default networkActivityMonitor;
