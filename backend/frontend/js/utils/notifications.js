/**
 * Notifications and Loading Utilities
 *
 * Helper functions for showing notifications, loading states, and user feedback.
 */

import { getById, setText, addClass, removeClass } from './dom.js';

/**
 * Show loading overlay
 * @param {string} text - Loading text to display
 */
export function showLoading(text = 'Loading...') {
    setText(getById('loadingText'), text);
    addClass(getById('loadingOverlay'), 'show');
}

/**
 * Hide loading overlay
 */
export function hideLoading() {
    removeClass(getById('loadingOverlay'), 'show');
}

/**
 * Show toast notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, warning, info)
 */
export function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `toast-notification toast-${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    notification.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;

    // Add to document
    let container = getById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    container.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'toastSlideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);

    // Log to console
    console.log(`[${type.toUpperCase()}] ${message}`);
    if (type === 'error') {
        console.error(message);
    }
}

/**
 * Show success notification
 * @param {string} message - Success message
 */
export function showSuccess(message) {
    showNotification(message, 'success');
}

/**
 * Show error notification
 * @param {string} message - Error message
 */
export function showError(message) {
    showNotification(message, 'error');
}

/**
 * Show warning notification
 * @param {string} message - Warning message
 */
export function showWarning(message) {
    showNotification(message, 'warning');
}

/**
 * Show info notification
 * @param {string} message - Info message
 */
export function showInfo(message) {
    showNotification(message, 'info');
}
