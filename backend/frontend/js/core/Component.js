/**
 * Component Lifecycle Management System
 *
 * This module provides the base contract and utilities for managing component lifecycles
 * in the Proximity frontend. Every view/component MUST implement the lifecycle pattern
 * to prevent memory leaks from intervals, event listeners, and other resources.
 *
 * @module core/Component
 */

/**
 * Base Component class that enforces lifecycle management
 *
 * Usage:
 * ```javascript
 * class DashboardComponent extends Component {
 *   mount(container, state) {
 *     // Render HTML
 *     container.innerHTML = `<div>Dashboard</div>`;
 *
 *     // Add listeners using trackListener for automatic cleanup
 *     const btn = container.querySelector('#btn');
 *     this.trackListener(btn, 'click', this.handleClick);
 *
 *     // Add intervals using trackInterval for automatic cleanup
 *     this.trackInterval(() => this.fetchData(), 5000);
 *
 *     // Call parent mount
 *     return super.mount(container, state);
 *   }
 *
 *   handleClick() {
 *     console.log('clicked');
 *   }
 *
 *   fetchData() {
 *     // fetch data
 *   }
 * }
 * ```
 */
export class Component {
    constructor() {
        this._intervals = [];
        this._listeners = [];
        this._mounted = false;
        this._container = null;
    }

    /**
     * Mount the component into the DOM
     * @param {HTMLElement} container - The container element
     * @param {Object} state - Application state
     * @returns {Function} Unmount function for cleanup
     */
    mount(container, state) {
        if (this._mounted) {
            console.warn(`Component already mounted, unmounting first`);
            this.unmount();
        }

        this._container = container;
        this._mounted = true;

        console.log(`✅ Mounting ${this.constructor.name}`);

        // Return unmount function
        return () => this.unmount();
    }

    /**
     * Unmount the component and cleanup all resources
     */
    unmount() {
        if (!this._mounted) {
            return;
        }

        console.log(`🧹 Unmounting ${this.constructor.name}: cleaning up resources`);

        // Clear all intervals
        this._intervals.forEach(intervalId => {
            clearInterval(intervalId);
        });
        this._intervals = [];

        // Remove all event listeners
        this._listeners.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this._listeners = [];

        // Clear container
        if (this._container) {
            this._container.innerHTML = '';
            this._container = null;
        }

        this._mounted = false;
    }

    /**
     * Track an interval for automatic cleanup
     * @param {Function} callback - Interval callback
     * @param {number} delay - Delay in milliseconds
     * @returns {number} Interval ID
     */
    trackInterval(callback, delay) {
        const intervalId = setInterval(callback, delay);
        this._intervals.push(intervalId);
        console.log(`⏱️  Tracked interval ${intervalId} for ${this.constructor.name}`);
        return intervalId;
    }

    /**
     * Clear a specific tracked interval
     * @param {number} intervalId - Interval ID to clear
     */
    clearTrackedInterval(intervalId) {
        clearInterval(intervalId);
        this._intervals = this._intervals.filter(id => id !== intervalId);
        console.log(`⏹️  Cleared interval ${intervalId} for ${this.constructor.name}`);
    }

    /**
     * Track an event listener for automatic cleanup
     * @param {HTMLElement} element - Element to attach listener to
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     * @param {Object} options - Event listener options
     */
    trackListener(element, event, handler, options = {}) {
        if (!element) {
            console.warn(`Cannot track listener: element is null`);
            return;
        }

        element.addEventListener(event, handler, options);
        this._listeners.push({ element, event, handler });
        console.log(`👂 Tracked listener ${event} for ${this.constructor.name}`);
    }

    /**
     * Remove a specific tracked listener
     * @param {HTMLElement} element - Element to remove listener from
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     */
    removeTrackedListener(element, event, handler) {
        element.removeEventListener(event, handler);
        this._listeners = this._listeners.filter(
            l => !(l.element === element && l.event === event && l.handler === handler)
        );
        console.log(`🔇 Removed listener ${event} for ${this.constructor.name}`);
    }

    /**
     * Check if component is currently mounted
     * @returns {boolean}
     */
    isMounted() {
        return this._mounted;
    }
}

/**
 * Functional component wrapper for components that don't need class inheritance
 *
 * Usage:
 * ```javascript
 * export const dashboard = createComponent((container, state) => {
 *   const cleanup = new ComponentCleanup();
 *
 *   container.innerHTML = `<div>Dashboard</div>`;
 *
 *   const btn = container.querySelector('#btn');
 *   cleanup.trackListener(btn, 'click', () => console.log('clicked'));
 *   cleanup.trackInterval(() => console.log('tick'), 1000);
 *
 *   return () => cleanup.destroy();
 * });
 * ```
 */
export function createComponent(mountFn) {
    return {
        mount(container, state) {
            console.log(`✅ Mounting functional component`);
            return mountFn(container, state);
        }
    };
}

/**
 * Utility class for tracking resources in functional components
 */
export class ComponentCleanup {
    constructor() {
        this._intervals = [];
        this._listeners = [];
    }

    trackInterval(callback, delay) {
        const intervalId = setInterval(callback, delay);
        this._intervals.push(intervalId);
        return intervalId;
    }

    trackListener(element, event, handler, options = {}) {
        if (!element) return;
        element.addEventListener(event, handler, options);
        this._listeners.push({ element, event, handler });
    }

    destroy() {
        console.log(`🧹 Cleaning up: ${this._intervals.length} intervals, ${this._listeners.length} listeners`);

        this._intervals.forEach(id => clearInterval(id));
        this._intervals = [];

        this._listeners.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this._listeners = [];
    }
}
