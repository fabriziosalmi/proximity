/**
 * Clipboard Utility Module
 * 
 * Provides clipboard copy functionality with user feedback.
 * Extracted from app.js as part of final modularization.
 * 
 * @module utils/clipboard
 */

/**
 * Copy text to clipboard with visual feedback
 * @param {string} text - Text to copy
 * @param {HTMLElement} button - Optional button element to provide visual feedback
 * @returns {Promise<boolean>} - True if successful, false otherwise
 */
export async function copyToClipboard(text, button = null) {
    try {
        await navigator.clipboard.writeText(text);
        
        // Provide visual feedback on the button if provided
        if (button) {
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i data-lucide="check"></i> Copied!';
            button.disabled = true;
            
            // Reinitialize Lucide icons for the new check icon
            if (typeof lucide !== 'undefined') {
                setTimeout(() => lucide.createIcons(), 0);
            }
            
            // Reset after 2 seconds
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.disabled = false;
                if (typeof lucide !== 'undefined') {
                    setTimeout(() => lucide.createIcons(), 0);
                }
            }, 2000);
        }
        
        // Show notification if available
        if (typeof window.showNotification === 'function') {
            window.showNotification('Copied to clipboard!', 'success');
        }
        
        return true;
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        
        // Show error notification if available
        if (typeof window.showNotification === 'function') {
            window.showNotification('Failed to copy to clipboard', 'error');
        }
        
        return false;
    }
}

/**
 * Copy text from an input element
 * @param {string} inputId - ID of the input element
 * @param {HTMLElement} button - Optional button element for feedback
 * @returns {Promise<boolean>}
 */
export async function copyFromInput(inputId, button = null) {
    const input = document.getElementById(inputId);
    if (!input) {
        console.error(`Input element with ID '${inputId}' not found`);
        return false;
    }
    
    return await copyToClipboard(input.value, button);
}

/**
 * Copy text from element's textContent
 * @param {string} elementId - ID of the element
 * @param {HTMLElement} button - Optional button element for feedback
 * @returns {Promise<boolean>}
 */
export async function copyFromElement(elementId, button = null) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error(`Element with ID '${elementId}' not found`);
        return false;
    }
    
    return await copyToClipboard(element.textContent || element.innerText, button);
}

/**
 * Create a copy button that copies specific text
 * @param {string} text - Text to copy
 * @param {string} className - Optional CSS class for the button
 * @returns {HTMLButtonElement}
 */
export function createCopyButton(text, className = 'btn btn-ghost btn-sm') {
    const button = document.createElement('button');
    button.className = className;
    button.innerHTML = '<i data-lucide="copy"></i> Copy';
    button.title = 'Copy to clipboard';
    
    button.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await copyToClipboard(text, button);
    });
    
    // Initialize Lucide icon
    if (typeof lucide !== 'undefined') {
        setTimeout(() => lucide.createIcons(), 0);
    }
    
    return button;
}
