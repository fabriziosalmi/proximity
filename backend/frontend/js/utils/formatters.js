/**
 * Formatters Utility Module
 * 
 * Provides formatting functions for dates, sizes, uptime, and other display values.
 * Extracted from app.js as part of final modularization.
 * 
 * @module utils/formatters
 */

/**
 * Format a date string for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date (e.g., "1/15/2025")
 */
export function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

/**
 * Format bytes to human-readable size
 * @param {number} bytes - Number of bytes
 * @returns {string} Formatted size (e.g., "1.50 GB")
 */
export function formatSize(bytes) {
    if (!bytes || bytes < 0) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
}

/**
 * Format bytes to human-readable size (alias for consistency)
 * @param {number} bytes - Number of bytes
 * @returns {string} Formatted size (e.g., "1.50 GB")
 */
export function formatBytes(bytes) {
    if (!bytes || bytes < 0) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
}

/**
 * Format uptime seconds to human-readable string
 * @param {number} seconds - Uptime in seconds
 * @returns {string} Formatted uptime (e.g., "5d 12h", "3h 45m", "25m")
 */
export function formatUptime(seconds) {
    if (!seconds || seconds < 0) return '--';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
}

/**
 * Format memory size in MB for display
 * @param {number} mb - Memory in megabytes
 * @returns {string} Formatted memory (e.g., "2048 MB", "4 GB")
 */
export function formatMemory(mb) {
    if (!mb || mb < 0) return 'Unknown';
    if (mb >= 1024) {
        return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb} MB`;
}

/**
 * Format percentage with proper bounds
 * @param {number} value - Value to format
 * @param {number} max - Maximum value
 * @param {number} decimals - Number of decimal places (default: 0)
 * @returns {string} Formatted percentage (e.g., "75%", "33.5%")
 */
export function formatPercentage(value, max, decimals = 0) {
    if (!value || !max || max === 0) return '0%';
    const percent = (value / max) * 100;
    return `${Math.min(100, Math.max(0, percent)).toFixed(decimals)}%`;
}

/**
 * Format timestamp to relative time (e.g., "2 hours ago", "just now")
 * @param {string|Date} timestamp - Timestamp to format
 * @returns {string} Relative time string
 */
export function formatRelativeTime(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return 'just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    
    return formatDate(timestamp);
}

/**
 * Format duration in milliseconds to human-readable string
 * @param {number} ms - Duration in milliseconds
 * @returns {string} Formatted duration (e.g., "1.5s", "250ms")
 */
export function formatDuration(ms) {
    if (!ms || ms < 0) return '0ms';
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
}

/**
 * Truncate string with ellipsis
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated string
 */
export function truncate(str, maxLength = 50) {
    if (!str) return '';
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength - 3) + '...';
}

/**
 * Capitalize first letter of string
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
export function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}
