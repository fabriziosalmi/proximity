/**
 * Search Service
 * 
 * Provides search and filter functionality for apps and catalog.
 * Handles debouncing, results counting, and UI state management.
 * 
 * Features:
 * - Catalog search (name, description, category)
 * - Apps search (name, ID, hostname)
 * - Category filtering
 * - Status filtering (running, stopped, all)
 * - Debounced search (300ms)
 * - Results counting
 * - Empty state rendering
 * 
 * @module searchService
 */

import { getState } from '../state/appState.js';
import { renderAppCard } from '../components/app-card.js';

/**
 * Get debounce utility
 * @returns {Function} Debounce function
 */
function getDebounce() {
    return window.debounce || ((fn) => fn);
}

/**
 * Reinitialize Lucide icons after DOM update
 */
function initIcons() {
    if (window.initLucideIcons) {
        window.initLucideIcons();
    }
}

/**
 * Internal catalog search (not debounced)
 * Searches by name, description, or category
 * Works in combination with category filters
 * 
 * @param {string} query - Search query
 */
function _searchCatalogInternal(query) {
    const clearBtn = document.getElementById('catalogClearSearch');
    const resultsCount = document.getElementById('catalogResultsCount');
    const grid = document.getElementById('catalogGrid');

    if (!grid) return;

    // Show/hide clear button based on query
    if (clearBtn) {
        clearBtn.style.display = query ? 'flex' : 'none';
    }

    // Get active category filter
    const activeCategory = document.querySelector('.sub-nav-item[data-category].active');
    const category = activeCategory ? activeCategory.dataset.category : 'all';

    // Apply category filter first
    const state = getState();
    let filtered = state.catalog.items || [];
    if (category !== 'all') {
        filtered = filtered.filter(app => app.category === category);
    }

    // Then apply search query if present
    if (query && query.trim()) {
        const searchTerm = query.toLowerCase().trim();
        filtered = filtered.filter(app => {
            const appName = (app.name || '').toLowerCase();
            const appDescription = (app.description || '').toLowerCase();
            const appCategory = (app.category || '').toLowerCase();

            return appName.includes(searchTerm) ||
                   appDescription.includes(searchTerm) ||
                   appCategory.includes(searchTerm);
        });

        // Show results count
        if (resultsCount) {
            resultsCount.textContent = `${filtered.length} result${filtered.length !== 1 ? 's' : ''} found`;
            resultsCount.style.display = 'block';
        }
    } else {
        // Hide results count when no search query
        if (resultsCount) {
            resultsCount.style.display = 'none';
        }
    }

    // Render filtered results
    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i data-lucide="search"></i>
                </div>
                <h3 class="empty-title">No matches found</h3>
                <p class="empty-message">Try adjusting your search or category filter</p>
                <button class="btn btn-secondary" id="catalogClearSearchBtn">Clear Search</button>
            </div>
        `;
        // Add event listener for clear button
        setTimeout(() => {
            const clearSearchBtn = document.getElementById('catalogClearSearchBtn');
            if (clearSearchBtn) {
                clearSearchBtn.addEventListener('click', () => {
                    const searchInput = document.getElementById('catalogSearchInput');
                    const clearBtn = document.getElementById('catalogClearSearch');
                    const resultsCount = document.getElementById('catalogResultsCount');
                    if (searchInput) searchInput.value = '';
                    if (clearBtn) clearBtn.style.display = 'none';
                    if (resultsCount) resultsCount.style.display = 'none';
                    _searchCatalogInternal('');
                });
            }
        }, 0);
    } else {
        // Clear grid and render using imported function
        grid.innerHTML = '';
        for (const app of filtered) {
            renderAppCard(app, grid, false);
        }
    }

    // Reinitialize Lucide icons
    initIcons();
}

/**
 * Search catalog items (debounced)
 * Searches by name, description, or category
 * Works in combination with category filters
 * 
 * @param {string} query - Search query
 */
export function searchCatalog(query) {
    _searchCatalogInternal(query);
}

// Create debounced version (300ms delay)
const searchCatalogDebounced = getDebounce()(_searchCatalogInternal, 300);

/**
 * Clear catalog search
 * Resets search input, clear button, and results count
 */
export function clearCatalogSearch() {
    const searchInput = document.getElementById('catalogSearchInput');
    const clearBtn = document.getElementById('catalogClearSearch');
    const resultsCount = document.getElementById('catalogResultsCount');

    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }

    if (clearBtn) {
        clearBtn.style.display = 'none';
    }

    if (resultsCount) {
        resultsCount.style.display = 'none';
    }

    // Trigger search with empty query to reset
    _searchCatalogInternal('');
}

/**
 * Filter catalog by category
 * Updates active tab state and triggers search
 * 
 * @param {string} category - Category to filter by ('all', 'web', 'database', etc.)
 * @param {Event} event - Click event (for tab activation)
 */
export function filterCatalog(category, event) {
    // Update tab active state
    document.querySelectorAll('.sub-nav-item[data-category]').forEach(tab => {
        tab.classList.remove('active');
    });
    if (event && event.target) {
        event.target.classList.add('active');
    }

    // Get current search query
    const searchInput = document.getElementById('catalogSearchInput');
    const currentQuery = searchInput ? searchInput.value : '';

    // Apply both filter and search
    _searchCatalogInternal(currentQuery);
}

/**
 * Internal apps search (not debounced)
 * Searches by name, ID, or hostname
 * Works in combination with status filters
 * 
 * @param {string} query - Search query
 */
function _searchAppsInternal(query) {
    const searchInput = document.getElementById('appsSearchInput');
    const clearBtn = document.getElementById('appsClearSearch');
    const resultsCount = document.getElementById('appsResultsCount');
    const grid = document.getElementById('allAppsGrid');

    if (!grid) return;

    // Show/hide clear button
    if (clearBtn) {
        clearBtn.style.display = query ? 'flex' : 'none';
    }

    // Get current filter (all, running, stopped)
    const activeFilter = document.querySelector('.sub-nav-item[data-filter].active');
    const filter = activeFilter ? activeFilter.dataset.filter : 'all';

    // Apply filter first
    const state = getState();
    let filtered = state.deployedApps || [];
    if (filter !== 'all') {
        filtered = filtered.filter(app => app.status === filter);
    }

    // Then apply search
    if (query && query.trim()) {
        const searchTerm = query.toLowerCase().trim();
        filtered = filtered.filter(app => {
            const appName = (app.name || app.id || '').toLowerCase();
            const appId = (app.id || '').toLowerCase();
            const hostname = (app.hostname || '').toLowerCase();
            return appName.includes(searchTerm) ||
                   appId.includes(searchTerm) ||
                   hostname.includes(searchTerm);
        });

        // Show results count
        if (resultsCount) {
            resultsCount.textContent = `${filtered.length} result${filtered.length !== 1 ? 's' : ''} found`;
            resultsCount.style.display = 'block';
        }
    } else {
        // Hide results count when no search
        if (resultsCount) {
            resultsCount.style.display = 'none';
        }
    }

    // Render filtered results
    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i data-lucide="search"></i>
                </div>
                <h3 class="empty-title">No matches found</h3>
                <p class="empty-message">Try adjusting your search or filter</p>
                <button class="btn btn-secondary" id="appsClearSearchBtn">Clear Search</button>
            </div>
        `;
        // Add event listener for clear button
        setTimeout(() => {
            const clearSearchBtn = document.getElementById('appsClearSearchBtn');
            if (clearSearchBtn) {
                clearSearchBtn.addEventListener('click', () => {
                    const searchInput = document.getElementById('appsSearchInput');
                    const clearBtn = document.getElementById('appsClearSearch');
                    const resultsCount = document.getElementById('appsResultsCount');
                    if (searchInput) searchInput.value = '';
                    if (clearBtn) clearBtn.style.display = 'none';
                    if (resultsCount) resultsCount.style.display = 'none';
                    _searchAppsInternal('');
                });
            }
        }, 0);
    } else {
        // Clear grid and render using imported function
        grid.innerHTML = '';
        for (const app of filtered) {
            renderAppCard(app, grid, true);
        }
    }

    // Reinitialize Lucide icons
    initIcons();
}

/**
 * Search apps (debounced)
 * Searches by name, ID, or hostname
 * Works in combination with status filters
 * 
 * @param {string} query - Search query
 */
export function searchApps(query) {
    _searchAppsInternal(query);
}

// Create debounced version (300ms delay)
const searchAppsDebounced = getDebounce()(_searchAppsInternal, 300);

/**
 * Clear apps search
 * Resets search input, clear button, and results count
 */
export function clearAppsSearch() {
    const searchInput = document.getElementById('appsSearchInput');
    const clearBtn = document.getElementById('appsClearSearch');
    const resultsCount = document.getElementById('appsResultsCount');

    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }

    if (clearBtn) {
        clearBtn.style.display = 'none';
    }

    if (resultsCount) {
        resultsCount.style.display = 'none';
    }

    // Trigger search with empty query to reset
    _searchAppsInternal('');
}

/**
 * Filter apps by status
 * Updates active tab state and re-renders filtered apps
 * 
 * @param {string} filter - Status filter ('all', 'running', 'stopped')
 * @param {Event} event - Click event (for tab activation)
 */
export function filterApps(filter, event) {
    // Update tab active state
    document.querySelectorAll('.sub-nav-item').forEach(tab => {
        tab.classList.remove('active');
    });
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Filter apps
    const state = getState();
    let filtered = state.deployedApps || [];
    if (filter !== 'all') {
        filtered = filtered.filter(app => app.status === filter);
    }
    
    const grid = document.getElementById('allAppsGrid');
    if (!grid) return;

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h3 class="empty-title">No ${filter} applications</h3>
                <p class="empty-message">No applications match the current filter.</p>
            </div>
        `;
    } else {
        // Clear grid and render using template cloning
        grid.innerHTML = '';
        const renderCard = getRenderCard();
        for (const app of filtered) {
            renderCard(app, grid, true);
        }
        // Reinitialize Lucide icons after updating the DOM
        initIcons();
    }
}

// Backward compatibility: Expose to window
if (typeof window !== 'undefined') {
    window.searchService = {
        searchCatalog: searchCatalogDebounced,
        clearCatalogSearch,
        filterCatalog,
        searchApps: searchAppsDebounced,
        clearAppsSearch,
        filterApps
    };
}
