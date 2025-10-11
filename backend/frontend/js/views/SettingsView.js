/**
 * Settings View Component
 *
 * Displays application settings (Proxmox, Network, Resources).
 * Wrapper around existing renderSettingsView() with lifecycle management.
 *
 * @module views/SettingsView
 */

import { Component } from '../core/Component.js';

export class SettingsView extends Component {
    constructor() {
        super();
    }

    /**
     * Mount the settings view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    async mount(container, state) {
        console.log('✅ Mounting Settings View');

        // Delegate to existing renderSettingsView() function
        // This is a WRAPPER approach for complex views during transition
        if (typeof window.renderSettingsView === 'function') {
            await window.renderSettingsView();
        } else {
            console.error('❌ renderSettingsView() not found');
            container.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="alert-circle"></i>
                    <p>Settings view not available</p>
                </div>
            `;
        }

        // Track any event listeners added by the settings view
        // In the future, we'll refactor renderSettingsView to be fully component-based

        // Call parent mount
        return super.mount(container, state);
    }

    /**
     * Unmount settings view and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Settings View');
        super.unmount();
    }
}

// Create singleton instance
export const settingsView = new SettingsView();
