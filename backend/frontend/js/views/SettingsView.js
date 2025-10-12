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
        console.group('📍 SettingsView Mount');
        console.log('🔐 Auth Status:', state.isAuthenticated ? '✅ Authenticated' : '❌ Not Authenticated');
        console.log('👤 Current User:', state.currentUser?.username || 'none');
        console.log('📦 Container:', container.id, 'Empty:', !container.innerHTML.trim());
        console.log('🔧 window.renderSettingsView available:', typeof window.renderSettingsView === 'function');

        try {
            // Delegate to existing renderSettingsView() function
            // This is a WRAPPER approach for complex views during transition
            if (typeof window.renderSettingsView === 'function') {
                await window.renderSettingsView();
                console.log('✅ renderSettingsView() executed successfully');
            } else {
                console.error('❌ renderSettingsView() not found in window object');
                console.error('Available window functions:', Object.keys(window).filter(k => k.includes('render')));
                container.innerHTML = `
                    <div class="empty-state">
                        <i data-lucide="alert-circle"></i>
                        <h3>Settings View Unavailable</h3>
                        <p>The settings view requires app.js to be loaded.</p>
                        <p style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 1rem;">
                            This is a temporary issue during frontend migration. The view wrapper cannot find window.renderSettingsView().
                        </p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('❌ Error mounting Settings view:', error);
            console.error('Stack:', error.stack);
            container.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="alert-triangle"></i>
                    <h3>Error Loading Settings</h3>
                    <p>${error.message}</p>
                </div>
            `;
        } finally {
            console.groupEnd();
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
