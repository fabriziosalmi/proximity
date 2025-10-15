/**
 * Toast Notification System - Global Version
 *
 * Non-module version for use in app.js (non-ES6 module context)
 * Provides a robust notification system for user feedback.
 */

(function() {
    'use strict';

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
     * Remove a toast with animation
     */
    function removeToast(toast) {
        if (!toast || !toast.parentElement) return;

        toast.classList.add('toast-exit');

        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 200);
    }

    /**
     * Create and show a toast notification
     * @param {string} message - The notification message
     * @param {string} type - Type of notification (success, error, warning, info)
     * @param {number} duration - Duration in ms before auto-dismiss (0 = no auto-dismiss)
     * @param {string} title - Optional custom title
     */
    function showNotification(message, type = 'info', duration = 5000, title = null) {
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

        // Update rack notification display
        updateRackNotification(message, type);

        // Get or create container (keep toast for fallback)
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
                progressBar.style.animation = `toastProgress ${duration}ms linear`;
            }

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
     * Show success notification
     */
    function showSuccess(message, duration = 5000) {
        return showNotification(message, 'success', duration);
    }

    /**
     * Show error notification (no auto-dismiss by default)
     */
    function showError(message, duration = 0) {
        return showNotification(message, 'error', duration);
    }

    /**
     * Show warning notification
     */
    function showWarning(message, duration = 7000) {
        return showNotification(message, 'warning', duration);
    }

    /**
     * Show info notification
     */
    function showInfo(message, duration = 5000) {
        return showNotification(message, 'info', duration);
    }

    /**
     * Clear all active toast notifications
     */
    function clearAllToasts() {
        const container = document.getElementById('toast-container');
        if (container) {
            const toasts = container.querySelectorAll('.toast');
            toasts.forEach(toast => removeToast(toast));
        }
    }

    /**
     * Update rack notification display
     * @param {string} message - The notification message
     * @param {string} type - Type of notification (success, error, warning, info)
     */
    function updateRackNotification(message, type = 'info') {
        const display = document.getElementById('rackNotificationDisplay');
        if (!display) return;

        const icon = display.querySelector('.rack-notif-icon');
        const messageEl = display.querySelector('.rack-notif-message');

        // Update icon
        const iconName = TOAST_ICONS[type] || TOAST_ICONS.info;
        if (icon) {
            icon.setAttribute('data-lucide', iconName);
        }

        // Update message
        if (messageEl) {
            messageEl.textContent = message;
        }

        // Update type class
        display.className = `rack-notification-display notif-${type} notif-new`;

        // Re-initialize Lucide icons for the new icon
        if (window.lucide && window.lucide.createIcons) {
            window.lucide.createIcons();
        }

        // Remove animation class after animation completes
        setTimeout(() => {
            display.classList.remove('notif-new');
        }, 500);
    }

    // Expose to global scope
    window.showNotification = showNotification;
    window.showSuccess = showSuccess;
    window.showError = showError;
    window.showWarning = showWarning;
    window.showInfo = showInfo;
    window.clearAllToasts = clearAllToasts;
    window.updateRackNotification = updateRackNotification;

    // Add progress bar animation keyframe
    const style = document.createElement('style');
    style.textContent = `
        @keyframes toastProgress {
            from { transform: scaleX(1); }
            to { transform: scaleX(0); }
        }
    `;
    document.head.appendChild(style);

})();
