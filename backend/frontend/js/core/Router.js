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
        // Check authentication from localStorage
        const token = localStorage.getItem('token');
        const isAuthenticated = token && token !== 'null' && token !== 'undefined';
        
        console.group('🧭 Router Navigation');
        console.log('📍 From:', this._currentViewName || 'none');
        console.log('📍 To:', viewName);
        console.log('🔐 Auth:', isAuthenticated ? '✅ Authenticated' : '❌ Not Authenticated');
        console.log('📦 View Registered:', this._viewComponents.has(viewName));
        console.log('📦 Container Exists:', !!document.getElementById(`${viewName}View`));

        // OPTIMIZATION: Skip if already on the requested view
        if (this._currentViewName === viewName) {
            console.log(`⏩ Already on '${viewName}', skipping navigation`);
            console.groupEnd();
            return;
        }

        // Step 1: Unmount the current view (CRITICAL for preventing memory leaks)
        if (this._currentUnmountFn) {
            console.log(`🧹 Unmounting previous view '${this._currentViewName}'`);
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
            console.error('Available views:', Array.from(this._viewComponents.keys()));
            console.groupEnd();
            return;
        }

        // Step 3: Hide all views
        this._hideAllViews();

        // Step 4: Get the container for the new view
        const container = document.getElementById(`${viewName}View`);
        if (!container) {
            console.error(`❌ Container element '#${viewName}View' not found!`);
            console.error('Available containers:', Array.from(document.querySelectorAll('[id$="View"]')).map(el => el.id));
            console.groupEnd();
            return;
        }

        // Step 5: Show the container
        container.classList.remove('hidden');

        // Step 6: Mount the new view and store its unmount function
        try {
            console.log(`✅ Mounting new view '${viewName}'`);
            // CRITICAL FIX: Await mount() to support async data loading
            this._currentUnmountFn = await component.mount(container, state);
            this._currentViewName = viewName;

            // Ensure unmount function is valid
            if (typeof this._currentUnmountFn !== 'function') {
                console.warn(`⚠️  View '${viewName}' did not return an unmount function`);
                this._currentUnmountFn = null;
            }
            
            console.log('✅ Navigation complete');
        } catch (error) {
            console.error(`❌ Error mounting view '${viewName}':`, error);
            console.error('   Error type:', error.constructor.name);
            console.error('   Error message:', error.message);
            
            // Show user-friendly error message in the container
            if (container) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">⚠️</div>
                        <h2>Error Loading View</h2>
                        <p>${error.message || 'An unexpected error occurred'}</p>
                        <button class="btn btn-primary" onclick="window.location.reload()">
                            <i data-lucide="refresh-cw"></i>
                            Reload Page
                        </button>
                    </div>
                `;
                
                // Initialize icons
                if (window.lucide) {
                    window.lucide.createIcons();
                }
            }
            
            this._currentUnmountFn = null;
        } finally {
            console.groupEnd();
        }

        // Step 7: Update navigation UI
        this._updateNavigationUI(viewName);

        // Step 8: Initialize Lucide icons (CRITICAL for icon rendering)
        this._initializeIcons();

        // Step 9: Trigger callbacks
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
     * Initialize Lucide icons after navigation
     * @private
     */
    _initializeIcons() {
        if (typeof lucide !== 'undefined') {
            try {
                // Use requestAnimationFrame to ensure DOM is fully updated
                requestAnimationFrame(() => {
                    lucide.createIcons();
                    console.log('✅ Lucide icons initialized after navigation');
                });
            } catch (error) {
                console.error('❌ Error initializing Lucide icons:', error);
            }
        } else {
            console.warn('⚠️  Lucide library not loaded');
        }
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
