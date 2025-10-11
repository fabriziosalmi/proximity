/**
 * Nodes View Component
 *
 * Displays infrastructure nodes (Proxmox hosts).
 * Wrapper around existing renderNodesView() with lifecycle management.
 *
 * @module views/NodesView
 */

import { Component } from '../core/Component.js';

export class NodesView extends Component {
    constructor() {
        super();
    }

    /**
     * Mount the nodes view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    async mount(container, state) {
        console.log('✅ Mounting Nodes View');

        // Delegate to existing renderNodesView() function
        // This is a WRAPPER approach for complex views during transition
        if (typeof window.renderNodesView === 'function') {
            await window.renderNodesView();
        } else {
            console.error('❌ renderNodesView() not found');
            container.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="alert-circle"></i>
                    <p>Nodes view not available</p>
                </div>
            `;
        }

        // Call parent mount
        return super.mount(container, state);
    }

    /**
     * Unmount nodes view and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Nodes View');
        super.unmount();
    }
}

// Create singleton instance
export const nodesView = new NodesView();
