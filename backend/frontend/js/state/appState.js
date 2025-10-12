/**
 * Application State Management
 *
 * THE SINGLE SOURCE OF TRUTH for application state.
 * This module owns and manages ALL application state.
 *
 * ARCHITECTURE:
 * - Pure module-based state management
 * - NO dependencies on legacy global variables
 * - Implements observer pattern for reactive updates
 */

// Main application state - THE ONLY STATE
const state = {
    systemInfo: null,
    nodes: [],
    apps: [],
    catalog: { items: [] }, // Initialize with empty items array
    currentView: 'dashboard',
    deployedApps: [],
    proxyStatus: null,
    proximityMode: 'AUTO', // AUTO or PRO mode
    currentUser: null,
    isAuthenticated: false
};

// Subscribers for reactive state updates
const subscribers = [];

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
        return { ...state }; // Return a copy to prevent external mutations
    }
    return state[key];
}

/**
 * Update state with new values and notify subscribers
 * @param {object|string} keyOrUpdates - State property key or object of updates
 * @param {any} value - New value (if first param is string)
 */
export function setState(keyOrUpdates, value) {
    if (typeof keyOrUpdates === 'object') {
        // Batch update: merge multiple properties
        Object.assign(state, keyOrUpdates);
    } else {
        // Single property update
        state[keyOrUpdates] = value;
    }

    // Notify all subscribers of state change
    notifySubscribers();
}

/**
 * Subscribe to state changes
 * @param {function} callback - Function to call when state changes
 * @returns {function} Unsubscribe function
 */
export function subscribe(callback) {
    subscribers.push(callback);

    // Return unsubscribe function
    return () => {
        const index = subscribers.indexOf(callback);
        if (index > -1) {
            subscribers.splice(index, 1);
        }
    };
}

/**
 * Notify all subscribers of state change
 */
function notifySubscribers() {
    const currentState = getState();
    subscribers.forEach(callback => {
        try {
            callback(currentState);
        } catch (error) {
            console.error('Error in state subscriber:', error);
        }
    });
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
 * Get proximity mode from localStorage or default
 * @returns {string} 'AUTO' or 'PRO'
 */
export function getProximityMode() {
    const stored = localStorage.getItem('proximityMode');
    return stored || state.proximityMode;
}

/**
 * Set proximity mode and persist to localStorage
 * @param {string} mode - 'AUTO' or 'PRO'
 */
export function setProximityMode(mode) {
    if (mode !== 'AUTO' && mode !== 'PRO') {
        console.error('Invalid proximity mode:', mode);
        return;
    }
    state.proximityMode = mode;
    localStorage.setItem('proximityMode', mode);
}

/**
 * Initialize proximity mode from localStorage
 */
export function initProximityMode() {
    const stored = getProximityMode();
    state.proximityMode = stored;
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
    state.proximityMode = getProximityMode(); // Preserve mode across resets

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

// ===========================================================================
// BACKWARD COMPATIBILITY: Expose state as window.state
// ===========================================================================
// This allows legacy code to access state via window.state
// TODO: Remove this once all code is migrated to use getState()
if (typeof window !== 'undefined') {
    // Create a Proxy that always returns fresh state
    window.state = new Proxy(state, {
        get(target, prop) {
            return target[prop];
        },
        set(target, prop, value) {
            // Redirect writes to setState for proper reactivity
            setState(prop, value);
            return true;
        }
    });
    
    // Also expose getState function globally
    window.getState = getState;
    console.log('✅ window.state compatibility layer enabled');
}
