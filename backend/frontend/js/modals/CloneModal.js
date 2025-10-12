/**
 * CloneModal.js
 * 
 * Handles the application cloning modal and logic.
 * 
 * Features:
 * - Prompts user for new hostname
 * - Clones app via API with new hostname
 * - Updates app list after successful clone
 * - Uses generic PromptModal for user input
 * 
 * Dependencies:
 * - api.js: API.cloneApp()
 * - appState.js: AppState.getState(), AppState.setState()
 * - notifications.js: showNotification()
 * - PromptModal.js: showPromptModal()
 */

import * as API from '../services/api.js';
import * as AppState from '../state/appState.js';
import { showNotification } from '../utils/notifications.js';
import { showPromptModal } from './PromptModal.js';

/**
 * Show clone modal and handle cloning
 * @param {string} appId - ID of app to clone
 * @param {string} appName - Name of app to clone
 */
export async function showCloneModal(appId, appName) {
    // Prompt user for new hostname
    const hostname = await showPromptModal(
        'Clone Application',
        `Enter a new hostname for the cloned copy of "${appName}":`,
        '',
        'Clone',
        'clone-hostname'
    );

    // User cancelled
    if (!hostname) return;

    try {
        showNotification(`Cloning ${appName}...`, 'info');

        // Call API to clone app
        const clonedApp = await API.cloneApp(appId, hostname);

        showNotification(`✓ Successfully cloned to ${hostname}`, 'success');

        // Update app state with new cloned app
        const currentState = AppState.getState();
        const updatedApps = [...currentState.apps, clonedApp];
        
        AppState.setState({ 
            apps: updatedApps 
        });

        // If we're on apps view, the observer will trigger re-render
        // No need to manually call loadApps()

    } catch (error) {
        console.error('Clone error:', error);
        showNotification(`Failed to clone: ${error.message}`, 'error');
    }
}

// ======================
// Global Exposure (Backward Compatibility)
// ======================

if (typeof window !== 'undefined') {
    window.showCloneModal = showCloneModal;
}
