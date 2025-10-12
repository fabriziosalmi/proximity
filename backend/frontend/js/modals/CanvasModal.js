/**
 * Canvas Modal Module
 *
 * Handles in-app canvas/iframe viewer:
 * - Open apps in embedded iframe
 * - Canvas controls (refresh, new tab, minimize header)
 * - Load state management
 * - Cross-origin handling
 */

import { showNotification } from '../utils/notifications.js';

// State
let currentCanvasApp = null;

/**
 * Open app in canvas modal
 * @param {object} app - App object with iframe_url
 */
export function openCanvas(app) {
    if (!app.iframe_url) {
        showNotification('Canvas URL not available for this app', 'error');
        return;
    }

    currentCanvasApp = app;

    const modal = document.getElementById('canvasModal');
    const appName = document.getElementById('canvasAppName');
    const iframe = document.getElementById('canvasIframe');
    const loading = document.getElementById('canvasLoading');
    const error = document.getElementById('canvasError');

    // Set app name
    appName.textContent = app.name || app.hostname;

    // Reset state
    iframe.classList.add('hidden');
    error.classList.add('hidden');
    loading.classList.remove('hidden');

    // Reset iframe completely before loading new content
    iframe.src = 'about:blank';

    // Wait a moment then load the actual URL
    setTimeout(() => {
        // Show modal
        modal.classList.add('show');
        document.body.classList.add('modal-open');

        // Load iframe with the app URL
        iframe.src = app.iframe_url;
    }, 50);

    // Handle iframe load events
    const onLoad = () => {
        loading.classList.add('hidden');
        iframe.classList.remove('hidden');

        // Try to inject CSS reset if same-origin (will fail silently for cross-origin)
        try {
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            if (iframeDoc && iframeDoc.body) {
                // Inject CSS reset into iframe to prevent parent styles from leaking
                const style = iframeDoc.createElement('style');
                style.textContent = `
                    /* Reset any inherited styles from parent */
                    html, body {
                        margin: 0 !important;
                        padding: 0 !important;
                        width: 100% !important;
                        height: 100% !important;
                        overflow: auto !important;
                        box-sizing: border-box !important;
                    }
                    body {
                        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                    }
                `;
                iframeDoc.head.appendChild(style);
            }
        } catch (e) {
            // Cross-origin - can't access iframe content, which is fine
            console.log('[Canvas] Cross-origin iframe - CSS reset not applied (expected)');
        }

        iframe.removeEventListener('load', onLoad);
        iframe.removeEventListener('error', onError);
    };

    const onError = () => {
        loading.classList.add('hidden');
        error.classList.remove('hidden');
        document.getElementById('canvasErrorMessage').textContent =
            `Unable to load ${app.name}. The application may not support iframe embedding.`;
        iframe.removeEventListener('load', onLoad);
        iframe.removeEventListener('error', onError);
    };

    // Set timeout for load detection
    const timeout = setTimeout(() => {
        if (!iframe.classList.contains('hidden')) return; // Already loaded
        // Check if iframe is accessible
        try {
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            if (iframeDoc.readyState === 'complete') {
                onLoad();
            }
        } catch (e) {
            // Cross-origin frame - assume it loaded successfully if no error
            onLoad();
        }
    }, 10000); // 10 second timeout

    iframe.addEventListener('load', () => {
        clearTimeout(timeout);
        onLoad();
    });

    iframe.addEventListener('error', () => {
        clearTimeout(timeout);
        onError();
    });

    // Reinitialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

/**
 * Close the canvas modal
 */
export function closeCanvas() {
    const modal = document.getElementById('canvasModal');
    const iframe = document.getElementById('canvasIframe');
    const header = document.querySelector('.canvas-modal-header');

    // Reset header state
    if (header) {
        header.classList.remove('minimized');
    }

    // Hide modal
    modal.classList.remove('show');
    document.body.classList.remove('modal-open');

    // Clear iframe after animation
    setTimeout(() => {
        iframe.src = '';
        currentCanvasApp = null;
    }, 300);
}

/**
 * Toggle canvas header between minimized and normal state
 */
export function toggleCanvasHeader() {
    const header = document.querySelector('.canvas-modal-header');
    const icon = document.getElementById('canvasHeaderToggleIcon');

    if (header && icon) {
        const isMinimized = header.classList.toggle('minimized');

        // Update icon
        if (isMinimized) {
            icon.setAttribute('data-lucide', 'maximize-2');
        } else {
            icon.setAttribute('data-lucide', 'minimize-2');
        }

        // Reinitialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
}

/**
 * Refresh the canvas iframe
 */
export function refreshCanvas() {
    if (!currentCanvasApp || !currentCanvasApp.iframe_url) return;

    const iframe = document.getElementById('canvasIframe');
    const loading = document.getElementById('canvasLoading');
    const error = document.getElementById('canvasError');

    // Show loading state
    iframe.classList.add('hidden');
    error.classList.add('hidden');
    loading.classList.remove('hidden');

    // Reload iframe
    iframe.src = currentCanvasApp.iframe_url;
}

/**
 * Open current canvas app in new tab
 */
export function openInNewTab() {
    if (!currentCanvasApp) return;

    // Prefer public URL over iframe URL
    const url = currentCanvasApp.url || currentCanvasApp.iframe_url;
    if (url) {
        window.open(url, '_blank');
    }
}

/**
 * Add canvas button to app cards (utility function)
 * @param {object} app - App object
 * @param {HTMLElement} container - Container element to add button to
 */
export function addCanvasButton(app, container) {
    if (!app.iframe_url) return; // No canvas URL available

    const button = document.createElement('button');
    button.className = 'btn btn-secondary';
    button.innerHTML = '<i data-lucide="monitor"></i><span>Canvas</span>';
    button.addEventListener('click', (e) => {
        e.stopPropagation();
        openCanvas(app);
    });

    container.appendChild(button);

    // Reinitialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Expose functions globally for legacy compatibility
if (typeof window !== 'undefined') {
    window.openCanvas = openCanvas;
    window.closeCanvas = closeCanvas;
    window.toggleCanvasHeader = toggleCanvasHeader;
    window.refreshCanvas = refreshCanvas;
    window.openInNewTab = openInNewTab;
    window.addCanvasButton = addCanvasButton;
}
