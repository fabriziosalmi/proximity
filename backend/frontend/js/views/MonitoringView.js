/**
 * Monitoring View Component
 *
 * Displays system monitoring and metrics.
 * Wrapper around existing renderMonitoringView() with lifecycle management.
 *
 * @module views/MonitoringView
 */

import { Component } from '../core/Component.js';

export class MonitoringView extends Component {
    constructor() {
        super();
    }

    /**
     * Mount the monitoring view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    mount(container, state) {
        console.log('✅ Mounting Monitoring View');

        // Delegate to existing renderMonitoringView() function
        // This is a WRAPPER approach for complex views during transition
        if (typeof window.renderMonitoringView === 'function') {
            window.renderMonitoringView();
        } else {
            console.error('❌ renderMonitoringView() not found');
            container.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="alert-circle"></i>
                    <p>Monitoring view not available</p>
                </div>
            `;
        }

        // Call parent mount
        return super.mount(container, state);
    }

    /**
     * Unmount monitoring view and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Monitoring View');
        super.unmount();
    }
}

// Create singleton instance
export const monitoringView = new MonitoringView();
