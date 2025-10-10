/**
 * Toast Notification System
 *
 * Provides a robust, non-intrusive notification system for user feedback.
 * Supports success, error, warning, and info types with auto-dismiss and manual close.
 * Integrated with SoundService for audio feedback.
 */

/**
 * Show loading overlay
 * @param {string} text - Loading text to display
 */
export function showLoading(text = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');

    if (loadingText) loadingText.textContent = text;
    if (overlay) overlay.classList.add('show');
}

/**
 * Hide loading overlay
 */
export function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('show');
}

/**
 * Toast icon mapping using Lucide icons
 */
const TOAST_ICONS = {
    success: 'check-circle',
    error: 'alert-circle',
    warning: 'alert-triangle',
    info: 'info'
};

/**
 * Toast title mapping
 */
const TOAST_TITLES = {
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Information'
};

/**
 * Create and show a toast notification
 * @param {string} message - The notification message
 * @param {string} type - Type of notification (success, error, warning, info)
 * @param {number} duration - Duration in ms before auto-dismiss (0 = no auto-dismiss)
 * @param {string} title - Optional custom title (defaults to type-based title)
 */
export function showNotification(message, type = 'info', duration = 5000, title = null) {
    // Play appropriate sound
    if (window.SoundService) {
        switch (type) {
            case 'success':
                window.SoundService.play('success');
                break;
            case 'error':
                window.SoundService.play('error');
                break;
            case 'warning':
            case 'info':
                window.SoundService.play('notification');
                break;
        }
    }

    // Get or create container
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const iconName = TOAST_ICONS[type] || TOAST_ICONS.info;
    const toastTitle = title || TOAST_TITLES[type] || TOAST_TITLES.info;

    // Build toast HTML
    toast.innerHTML = `
        <div class="toast-icon">
            <i data-lucide="${iconName}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${toastTitle}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" aria-label="Close notification">×</button>
        ${duration > 0 ? '<div class="toast-progress"></div>' : ''}
    `;

    // Add close button handler
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => removeToast(toast));

    // Add to container
    container.appendChild(toast);

    // Initialize Lucide icons for the new toast
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // Auto-dismiss with progress bar animation
    if (duration > 0) {
        const progressBar = toast.querySelector('.toast-progress');
        if (progressBar) {
            // Animate progress bar
            progressBar.style.animation = `toastProgress ${duration}ms linear`;
        }

        // Schedule removal
        setTimeout(() => removeToast(toast), duration);
    }

    // Log to console for debugging
    const logPrefix = `[${type.toUpperCase()}]`;
    if (type === 'error') {
        console.error(logPrefix, message);
    } else if (type === 'warning') {
        console.warn(logPrefix, message);
    } else {
        console.log(logPrefix, message);
    }

    return toast;
}

/**
 * Remove a toast with animation
 * @param {HTMLElement} toast - The toast element to remove
 */
function removeToast(toast) {
    if (!toast || !toast.parentElement) return;

    // Add exit animation
    toast.classList.add('toast-exit');

    // Remove after animation completes
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 200); // Match CSS animation duration
}

/**
 * Show success notification
 * @param {string} message - Success message
 * @param {number} duration - Duration in ms (default: 5000)
 */
export function showSuccess(message, duration = 5000) {
    return showNotification(message, 'success', duration);
}

/**
 * Show error notification
 * @param {string} message - Error message
 * @param {number} duration - Duration in ms (default: 0 - no auto-dismiss for errors)
 */
export function showError(message, duration = 0) {
    return showNotification(message, 'error', duration);
}

/**
 * Show warning notification
 * @param {string} message - Warning message
 * @param {number} duration - Duration in ms (default: 7000)
 */
export function showWarning(message, duration = 7000) {
    return showNotification(message, 'warning', duration);
}

/**
 * Show info notification
 * @param {string} message - Info message
 * @param {number} duration - Duration in ms (default: 5000)
 */
export function showInfo(message, duration = 5000) {
    return showNotification(message, 'info', duration);
}

/**
 * Clear all active toast notifications
 */
export function clearAllToasts() {
    const container = document.getElementById('toast-container');
    if (container) {
        const toasts = container.querySelectorAll('.toast');
        toasts.forEach(toast => removeToast(toast));
    }
}

// Add progress bar animation to CSS keyframes (injected at runtime)
if (typeof window !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes toastProgress {
            from { transform: scaleX(1); }
            to { transform: scaleX(0); }
        }
    `;
    document.head.appendChild(style);
}
