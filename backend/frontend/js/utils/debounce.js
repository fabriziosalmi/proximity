/**
 * Debounce Utility
 *
 * Delays function execution until after a specified wait time has elapsed
 * since the last time it was invoked. Perfect for search inputs and resize handlers.
 *
 * @module utils/debounce
 */

/**
 * Creates a debounced function that delays invoking func until after wait milliseconds
 * have elapsed since the last time the debounced function was invoked.
 *
 * @param {Function} func - The function to debounce
 * @param {number} wait - The number of milliseconds to delay
 * @returns {Function} Returns the new debounced function
 *
 * @example
 * const debouncedSearch = debounce((query) => {
 *     console.log('Searching for:', query);
 * }, 300);
 *
 * input.addEventListener('input', (e) => {
 *     debouncedSearch(e.target.value);
 * });
 */
export function debounce(func, wait) {
    let timeout;

    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };

        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Creates a debounced function with immediate execution option
 *
 * @param {Function} func - The function to debounce
 * @param {number} wait - The number of milliseconds to delay
 * @param {boolean} immediate - Execute on the leading edge instead of trailing
 * @returns {Function} Returns the new debounced function
 */
export function debounceImmediate(func, wait, immediate = false) {
    let timeout;

    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };

        const callNow = immediate && !timeout;

        clearTimeout(timeout);
        timeout = setTimeout(later, wait);

        if (callNow) func(...args);
    };
}

// Make available globally for legacy code
window.debounce = debounce;
window.debounceImmediate = debounceImmediate;
