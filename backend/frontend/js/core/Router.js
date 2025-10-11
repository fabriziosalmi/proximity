/**
 * Centralized View Router with Lifecycle Management
 *
 * This router is responsible for:
 * 1. Managing view transitions
 * 2. Calling unmount() on the previous view to cleanup resources
 * 3. Calling mount() on the new view to initialize it
 * 4. Preventing memory leaks by ensuring proper cleanup
 *
 * @module core/Router
 */

/**
 * Router class that manages view lifecycle
 */
export class Router {
    constructor() {
        this._currentUnmountFn = null;
        this._currentViewName = null;
        this._viewComponents = new Map();
        this._onViewChangeCallbacks = [];
    }

    /**
     * Register a view component
     * @param {string} viewName - Name of the view (e.g., 'dashboard', 'apps')
     * @param {Object} component - Component object with mount() function
     */
    registerView(viewName, component) {
        if (!component || typeof component.mount !== 'function') {
            throw new Error(`Component for view '${viewName}' must have a mount() function`);
        }

        this._viewComponents.set(viewName, component);
        console.log(`🔌 Registered view: ${viewName}`);
    }

    /**
     * Register multiple views at once
     * @param {Object} viewMap - Map of viewName => component
     */
    registerViews(viewMap) {
        Object.entries(viewMap).forEach(([viewName, component]) => {
            this.registerView(viewName, component);
        });
    }

    /**
     * Navigate to a specific view
     * @param {string} viewName - Name of the view to navigate to
     * @param {Object} state - State to pass to the view
     * @returns {Promise<void>}
     */
    async navigateTo(viewName, state = {}) {
        console.log(`🧭 Router: Navigating from '${this._currentViewName}' to '${viewName}'`);

        // Step 1: Unmount the current view (CRITICAL for preventing memory leaks)
        if (this._currentUnmountFn) {
            console.log(`🧹 Router: Unmounting previous view '${this._currentViewName}'`);
            try {
                this._currentUnmountFn();
            } catch (error) {
                console.error(`❌ Error unmounting view '${this._currentViewName}':`, error);
            }
            this._currentUnmountFn = null;
        }

        // Step 2: Find the component for the new view
        const component = this._viewComponents.get(viewName);
        if (!component) {
            console.error(`❌ View '${viewName}' not registered!`);
            return;
        }

        // Step 3: Hide all views
        this._hideAllViews();

        // Step 4: Get the container for the new view
        const container = document.getElementById(`${viewName}View`);
        if (!container) {
            console.error(`❌ Container element '#${viewName}View' not found!`);
            return;
        }

        // Step 5: Show the container
        container.classList.remove('hidden');

        // Step 6: Mount the new view and store its unmount function
        try {
            console.log(`✅ Router: Mounting new view '${viewName}'`);
            this._currentUnmountFn = component.mount(container, state);
            this._currentViewName = viewName;

            // Ensure unmount function is valid
            if (typeof this._currentUnmountFn !== 'function') {
                console.warn(`⚠️  View '${viewName}' did not return an unmount function`);
                this._currentUnmountFn = null;
            }
        } catch (error) {
            console.error(`❌ Error mounting view '${viewName}':`, error);
            this._currentUnmountFn = null;
        }

        // Step 7: Update navigation UI
        this._updateNavigationUI(viewName);

        // Step 8: Trigger callbacks
        this._triggerViewChangeCallbacks(viewName, state);
    }

    /**
     * Hide all view containers
     * @private
     */
    _hideAllViews() {
        const views = ['dashboard', 'apps', 'catalog', 'nodes', 'monitoring', 'settings', 'uilab'];
        views.forEach(view => {
            const container = document.getElementById(`${view}View`);
            if (container) {
                container.classList.add('hidden');
            }
        });
    }

    /**
     * Update navigation UI to reflect current view
     * @param {string} viewName - Name of the current view
     * @private
     */
    _updateNavigationUI(viewName) {
        const navItems = document.querySelectorAll('.nav-rack-item');
        navItems.forEach(item => {
            const itemView = item.getAttribute('data-view');
            if (itemView === viewName) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    /**
     * Register a callback to be called when view changes
     * @param {Function} callback - Callback function(viewName, state)
     */
    onViewChange(callback) {
        this._onViewChangeCallbacks.push(callback);
    }

    /**
     * Trigger all registered view change callbacks
     * @param {string} viewName - Name of the new view
     * @param {Object} state - State passed to the view
     * @private
     */
    _triggerViewChangeCallbacks(viewName, state) {
        this._onViewChangeCallbacks.forEach(callback => {
            try {
                callback(viewName, state);
            } catch (error) {
                console.error('Error in view change callback:', error);
            }
        });
    }

    /**
     * Get the current view name
     * @returns {string|null}
     */
    getCurrentView() {
        return this._currentViewName;
    }

    /**
     * Cleanup all resources (call this on app shutdown)
     */
    destroy() {
        console.log(`🧹 Router: Destroying and cleaning up all resources`);
        if (this._currentUnmountFn) {
            this._currentUnmountFn();
            this._currentUnmountFn = null;
        }
        this._currentViewName = null;
        this._onViewChangeCallbacks = [];
    }
}

// Create singleton instance
export const router = new Router();

// Export convenience function
export function navigateTo(viewName, state) {
    return router.navigateTo(viewName, state);
}

// Make router available globally for transition period
if (typeof window !== 'undefined') {
    window.ProximityRouter = router;
}
