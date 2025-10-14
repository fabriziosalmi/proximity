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

        // Step 3: Update UI IMMEDIATELY (feels instant to user)
        this._updateActiveNavIndicator(viewName);
        this._updatePageTitle(viewName);

        // Step 4: Hide all views
        this._hideAllViews();

        // Step 5: Get the container for the new view
        const container = document.getElementById(`${viewName}View`);
        if (!container) {
            console.error(`❌ Container element '#${viewName}View' not found!`);
            console.error('Available containers:', Array.from(document.querySelectorAll('[id$="View"]')).map(el => el.id));
            console.groupEnd();
            return;
        }

        // Step 6: Mount/prepare the view BEFORE showing it (prevents flash of old content)
        // Check if component is already mounted (for singleton views)
        if (component.isMounted && component.isMounted()) {
            console.log(`⚡ Component '${viewName}' already mounted, reusing instance`);
            this._currentViewName = viewName;
            // Create unmount function that calls the component's unmount
            this._currentUnmountFn = () => component.unmount();
        } else {
            // Mount the new view and store its unmount function
            try {
                console.log(`✅ Mounting new view '${viewName}'`);
                // CRITICAL FIX: Await mount() to support async data loading
                // Mount happens WHILE container is still hidden
                this._currentUnmountFn = await component.mount(container, state);
                this._currentViewName = viewName;

                // Ensure unmount function is valid
                if (typeof this._currentUnmountFn !== 'function') {
                    console.warn(`⚠️  View '${viewName}' did not return an unmount function`);
                    this._currentUnmountFn = null;
                }
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
            }
        }

        // Step 7: NOW show the container (content is already rendered)
        container.classList.remove('hidden');

        // Step 8: Initialize Lucide icons SCOPED to this container (MUCH faster!)
        this._initializeIcons(container);

        // Step 9: Trigger callbacks
        this._triggerViewChangeCallbacks(viewName, state);

        console.log('✅ Navigation complete');
        console.groupEnd();
    }

    /**
     * Hide all view containers
     * @private
     */
    _hideAllViews() {
        const views = ['dashboard', 'apps', 'catalog', 'nodes', 'monitoring', 'settings'];
        views.forEach(view => {
            const container = document.getElementById(`${view}View`);
            if (container) {
                container.classList.add('hidden');
            }
        });
    }

    /**
     * Initialize Lucide icons after navigation
     * @param {HTMLElement} container - Container with new icons (optional)
     * @private
     */
    _initializeIcons(container = null) {
        if (typeof lucide !== 'undefined') {
            try {
                // PERFORMANCE: When using CDN version of Lucide, we can pass attrs.nameAttr
                // to only process specific elements, but simpler to just call createIcons()
                // which is already pretty fast with modern browsers
                lucide.createIcons();

                if (container) {
                    const iconCount = container.querySelectorAll('[data-lucide]').length;
                    console.log(`✅ Lucide icons initialized (${iconCount} in ${container.id})`);
                } else {
                    console.log('✅ Lucide icons initialized (document-wide)');
                }
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
     * Update active navigation indicator for current view
     * Adds 'active' class to current nav item, removes from others
     * @param {string} viewName - Name of the current view
     * @private
     */
    _updateActiveNavIndicator(viewName) {
        // Remove 'active' class from all nav items
        const allNavItems = document.querySelectorAll('.nav-rack-item[data-view]');
        allNavItems.forEach(item => {
            item.classList.remove('active');
        });

        // Add 'active' class to current view's nav item
        const currentNavItem = document.querySelector(`.nav-rack-item[data-view="${viewName}"]`);
        if (currentNavItem) {
            currentNavItem.classList.add('active');
            console.log(`✓ Active indicator set for '${viewName}'`);
        }
    }

    /**
     * Update page title based on current view
     * @param {string} viewName - Name of the current view
     * @private
     */
    _updatePageTitle(viewName) {
        const titleMap = {
            'dashboard': 'Dashboard',
            'catalog': 'App Store',
            'apps': 'My Apps',
            'nodes': 'Infrastructure',
            'settings': 'Settings'
        };

        const viewTitle = titleMap[viewName] || viewName;
        document.title = `Proximity - ${viewTitle}`;
        console.log(`✓ Page title updated: ${document.title}`);
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
