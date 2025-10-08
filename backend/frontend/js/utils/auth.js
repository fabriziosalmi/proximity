/**
 * Authentication Utilities
 *
 * Handles JWT token management and authenticated requests.
 */

const TOKEN_KEY = 'proximity_token';

/**
 * Get authentication token from localStorage
 * @returns {string|null} JWT token
 */
export function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * Set authentication token in localStorage
 * @param {string} token - JWT token
 */
export function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Remove authentication token from localStorage
 */
export function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

/**
 * Check if user is authenticated
 * @returns {boolean} True if token exists
 */
export function isAuthenticated() {
    return !!getToken();
}

/**
 * Get user info from token (simple base64 decode)
 * @returns {object|null} User info
 */
export function getUserInfo() {
    const token = getToken();
    if (!token) return null;

    try {
        const payload = token.split('.')[1];
        const decoded = atob(payload);
        return JSON.parse(decoded);
    } catch (e) {
        console.error('Failed to decode token:', e);
        return null;
    }
}

/**
 * Handle logout
 */
export function logout() {
    clearToken();
    window.location.reload();
}
