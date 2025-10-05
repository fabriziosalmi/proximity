/**
 * Application State Management
 *
 * Centralized state management for the Proximity application.
 * Provides getters and setters for global application state.
 */

// Main application state
const state = {
    systemInfo: null,
    nodes: [],
    apps: [],
    catalog: null,
    currentView: 'dashboard',
    deployedApps: [],
    proxyStatus: null
};

// Interval tracking for cleanup
const intervals = {
    deploymentProgress: null,
    logsRefresh: null,
    updateStatus: null,
    backupPolling: null
};

// Monitoring state
const monitoringState = {
    isActive: false,
    pollInterval: null,
    apps: new Map() // appId -> metrics data
};

// Current context state
const contextState = {
    backupAppId: null,
    canvasApp: null
};

/**
 * Get the entire state object or a specific property
 * @param {string} key - Optional key to get specific state property
 * @returns {any} State object or specific property value
 */
export function getState(key = null) {
    if (key === null) {
        return state;
    }
    return state[key];
}

/**
 * Update state with new values
 * @param {string} key - State property to update
 * @param {any} value - New value
 */
export function setState(key, value) {
    state[key] = value;
}

/**
 * Get interval by name
 * @param {string} name - Interval name
 * @returns {number|null} Interval ID
 */
export function getInterval(name) {
    return intervals[name];
}

/**
 * Set interval
 * @param {string} name - Interval name
 * @param {number} intervalId - Interval ID
 */
export function setInterval(name, intervalId) {
    intervals[name] = intervalId;
}

/**
 * Clear interval by name
 * @param {string} name - Interval name
 */
export function clearInterval(name) {
    if (intervals[name]) {
        window.clearInterval(intervals[name]);
        intervals[name] = null;
    }
}

/**
 * Get monitoring state
 * @returns {object} Monitoring state object
 */
export function getMonitoringState() {
    return monitoringState;
}

/**
 * Update monitoring state
 * @param {string} key - Property to update
 * @param {any} value - New value
 */
export function setMonitoringState(key, value) {
    monitoringState[key] = value;
}

/**
 * Get context state
 * @param {string} key - Optional key to get specific context property
 * @returns {any} Context state object or specific property value
 */
export function getContext(key = null) {
    if (key === null) {
        return contextState;
    }
    return contextState[key];
}

/**
 * Set context state
 * @param {string} key - Context property to update
 * @param {any} value - New value
 */
export function setContext(key, value) {
    contextState[key] = value;
}

/**
 * Reset all state to initial values
 */
export function resetState() {
    state.systemInfo = null;
    state.nodes = [];
    state.apps = [];
    state.catalog = null;
    state.currentView = 'dashboard';
    state.deployedApps = [];
    state.proxyStatus = null;

    // Clear all intervals
    Object.keys(intervals).forEach(name => clearInterval(name));

    // Reset monitoring state
    monitoringState.isActive = false;
    monitoringState.pollInterval = null;
    monitoringState.apps.clear();

    // Reset context
    contextState.backupAppId = null;
    contextState.canvasApp = null;
}
