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

        // Update rack notification display (ONLY THIS, no toast popup)
        updateRackNotification(message, type, duration);

        // Log to console for debugging
        const logPrefix = `[${type.toUpperCase()}]`;
        if (type === 'error') {
            console.error(logPrefix, message);
        } else if (type === 'warning') {
            console.warn(logPrefix, message);
        } else {
            console.log(logPrefix, message);
        }

        // Return null since we're not creating a toast element anymore
        return null;
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

    // Store current auto-dismiss timeout
    let rackNotificationTimeout = null;
    let idleAnimationInterval = null;

    /**
     * Start idle animation (thinking effect with asterisks)
     */
    function startIdleAnimation() {
        const display = document.getElementById('rackNotificationDisplay');
        if (!display) return;

        const icon = display.querySelector('.rack-notif-icon');
        const messageEl = display.querySelector('.rack-notif-message');

        // Hide icon during idle animation
        if (icon) {
            icon.style.display = 'none';
        }

        // Set base class
        display.className = 'rack-notification-display rack-idle';

        let frame = 0;
        const frames = [
            '∗ PROXIMITY ∗',
            '• PROXIMITY •',
            '◦ PROXIMITY ◦',
            '∘ PROXIMITY ∘',
            '· PROXIMITY ·',
            '  PROXIMITY  ',
            '· PROXIMITY ·',
            '∘ PROXIMITY ∘',
            '◦ PROXIMITY ◦',
            '• PROXIMITY •'
        ];

        // Set initial frame
        if (messageEl) {
            messageEl.textContent = frames[0];
        }

        idleAnimationInterval = setInterval(() => {
            if (messageEl) {
                frame = (frame + 1) % frames.length;
                messageEl.textContent = frames[frame];
            }
        }, 400);
    }

    /**
     * Stop idle animation
     */
    function stopIdleAnimation() {
        if (idleAnimationInterval) {
            clearInterval(idleAnimationInterval);
            idleAnimationInterval = null;
        }

        const display = document.getElementById('rackNotificationDisplay');
        if (!display) return;

        const icon = display.querySelector('.rack-notif-icon');
        if (icon) {
            icon.style.display = '';
        }
    }

    /**
     * Update rack notification display
     * @param {string} message - The notification message
     * @param {string} type - Type of notification (success, error, warning, info)
     * @param {number} duration - Duration in ms before auto-dismiss (0 = no auto-dismiss)
     */
    function updateRackNotification(message, type = 'info', duration = 5000) {
        const display = document.getElementById('rackNotificationDisplay');
        if (!display) return;

        // Stop idle animation when showing notification
        stopIdleAnimation();

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

        // Update type class and make visible
        display.className = `rack-notification-display notif-${type} notif-new notif-visible`;

        // Re-initialize Lucide icons for the new icon
        if (window.lucide && window.lucide.createIcons) {
            window.lucide.createIcons();
        }

        // Remove animation class after animation completes
        setTimeout(() => {
            display.classList.remove('notif-new');
        }, 500);

        // Clear existing auto-dismiss timeout
        if (rackNotificationTimeout) {
            clearTimeout(rackNotificationTimeout);
            rackNotificationTimeout = null;
        }

        // Set auto-dismiss (if duration > 0)
        if (duration > 0) {
            rackNotificationTimeout = setTimeout(() => {
                // Fade out
                display.classList.add('notif-fadeout');

                setTimeout(() => {
                    display.classList.remove('notif-visible', 'notif-fadeout');
                    // Start idle animation after dismiss
                    startIdleAnimation();
                }, 300);
            }, duration);
        }
    }

    // Expose to global scope
    window.showNotification = showNotification;
    window.showSuccess = showSuccess;
    window.showError = showError;
    window.showWarning = showWarning;
    window.showInfo = showInfo;
    window.clearAllToasts = clearAllToasts;
    window.updateRackNotification = updateRackNotification;
    window.startIdleAnimation = startIdleAnimation;
    window.stopIdleAnimation = stopIdleAnimation;

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
