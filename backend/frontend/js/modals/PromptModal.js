/**
 * PromptModal.js
 * 
 * Generic prompt modal for user input.
 * 
 * Features:
 * - Reusable prompt dialog
 * - Returns Promise that resolves with user input or null on cancel
 * - Supports Enter key to confirm
 * - Supports Escape key to cancel
 * - Auto-focus and select input text
 * - Customizable title, message, default value, and confirm button text
 * 
 * Usage:
 * const value = await showPromptModal('Title', 'Message', 'default', 'OK');
 * if (value) {
 *   // User entered value
 * } else {
 *   // User cancelled
 * }
 */

/**
 * Show prompt modal and return user input
 * @param {string} title - Modal title
 * @param {string} message - Prompt message
 * @param {string} defaultValue - Default input value
 * @param {string} confirmText - Confirm button text
 * @param {string} inputId - ID for input element
 * @returns {Promise<string|null>} User input or null if cancelled
 */
export function showPromptModal(title, message, defaultValue = '', confirmText = 'OK', inputId = 'promptInput') {
    return new Promise((resolve) => {
        // Create modal HTML
        const modalHTML = `
            <div class="modal-overlay" id="promptOverlay">
                <div class="modal-dialog">
                    <div class="modal-header">
                        <h2>${title}</h2>
                        <button class="modal-close" id="promptCloseBtn">✕</button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                        <input type="text" id="${inputId}" class="form-control" value="${defaultValue}">
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" id="promptCancelBtn">
                            Cancel
                        </button>
                        <button id="promptConfirm" class="btn btn-primary">${confirmText}</button>
                    </div>
                </div>
            </div>
        `;

        // Insert modal into DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Get DOM elements
        const overlay = document.getElementById('promptOverlay');
        const input = document.getElementById(inputId);
        const confirmBtn = document.getElementById('promptConfirm');
        const cancelBtn = document.getElementById('promptCancelBtn');
        const closeBtn = document.getElementById('promptCloseBtn');

        // Handler to close and resolve with null
        const handleCancel = () => {
            cleanup();
            resolve(null);
        };

        // Handler to close and resolve with value
        const handleConfirm = () => {
            const val = input.value.trim();
            cleanup();
            resolve(val);
        };

        // Cleanup function
        const cleanup = () => {
            // Remove event listeners
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
            closeBtn.removeEventListener('click', handleCancel);
            input.removeEventListener('keypress', handleKeyPress);
            document.removeEventListener('keydown', handleEscape);
            
            // Remove modal from DOM
            overlay.remove();
        };

        // Enter key handler for input
        const handleKeyPress = (event) => {
            if (event.key === 'Enter') {
                handleConfirm();
            }
        };

        // Escape key handler
        const handleEscape = (event) => {
            if (event.key === 'Escape') {
                handleCancel();
            }
        };

        // Attach event listeners
        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
        closeBtn.addEventListener('click', handleCancel);
        input.addEventListener('keypress', handleKeyPress);
        document.addEventListener('keydown', handleEscape);

        // Auto-focus and select input
        setTimeout(() => {
            if (input) {
                input.focus();
                input.select();
            }
        }, 100);
    });
}

// ======================
// Global Exposure (Backward Compatibility)
// ======================

if (typeof window !== 'undefined') {
    window.showPromptModal = showPromptModal;
}
