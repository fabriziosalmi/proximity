/**
 * Data Service
 * 
 * Provides data loading and state management for apps and catalog.
 * Handles API calls, caching, enrichment, and UI updates.
 * 
 * Features:
 * - Load deployed apps from API
 * - Load catalog from API
 * - Enrich deployed apps with catalog icons
 * - Update dashboard stats
 * - Update recent apps section
 * - Caching (5 min TTL for catalog)
 * 
 * @module dataService
 */

import { authFetch, API_BASE } from './api.js';
import { getState, setState } from '../state/appState.js';

/**
 * Get API base URL
 * @returns {string} API base URL
 */
function getAPIBase() {
    return API_BASE;
}

/**
 * Get authFetch function
 * @returns {Function} Auth fetch function
 */
function getAuthFetch() {
    return authFetch;
}

/**
 * Initialize Lucide icons
 */
function initIcons() {
    if (window.initLucideIcons) {
        window.initLucideIcons();
    }
}

/**
 * Get app icon
 */
function getIcon(appName) {
    return window.getAppIcon ? window.getAppIcon(appName) : '📦';
}

/**
 * Catalog cache
 */
let catalogCache = null;
let catalogCacheTime = 0;
const CATALOG_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Load deployed apps from API
 * Fetches list of deployed applications and enriches with catalog icons
 * 
 * @returns {Promise<Array>} Array of deployed apps
 * @throws {Error} If API call fails
 */
/**
 * Load deployed apps from API
 * Fetches all deployed applications
 * 
 * @param {boolean} updateState - Whether to update global state (default: true)
 * @returns {Promise<Array>} Array of deployed apps
 * @throws {Error} If API call fails
 */
export async function loadDeployedApps(updateState = true) {
    console.log('🚀 Loading deployed apps...');

    try {
        const response = await authFetch(`${API_BASE}/apps`);
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`❌ Failed to load apps: ${response.status} ${response.statusText}`, errorText);
            throw new Error(`Failed to load apps: ${response.status} ${response.statusText}`);
        }
        const deployedApps = await response.json();
        
        // Update state only if requested
        if (updateState) {
            setState('deployedApps', deployedApps);
        }
        
        console.log(`✅ Deployed apps loaded: ${deployedApps.length} apps`);
        
        // Enrich deployed apps with icon URLs from catalog
        enrichDeployedAppsWithIcons();
        
        return deployedApps;
    } catch (error) {
        console.error('❌ Error loading deployed apps:', error);
        console.error('   Error type:', error.constructor.name);
        console.error('   Error message:', error.message);
        
        // Check if it's a network error (no connection)
        if (error instanceof TypeError && error.message.includes('fetch')) {
            console.error('   ⚠️  Network error: Cannot connect to backend server');
            console.error('   ⚠️  Make sure the backend is running on', API_BASE);
        }
        
        if (updateState) {
            setState('deployedApps', []);
        }
        
        // Return empty array instead of throwing to allow graceful degradation
        return [];
    }
}

/**
 * Load catalog from API
 * Fetches catalog of available applications
 * Uses caching (5 min TTL) to reduce API calls
 * 
 * @param {boolean} force - Force refresh (bypass cache)
 * @param {boolean} updateState - Whether to update global state (default: true)
 * @returns {Promise<Object>} Catalog object with items and categories
 */
export async function loadCatalog(force = false, updateState = true) {
    console.log('📚 Loading catalog...');

    // Check cache (unless forced)
    if (!force && catalogCache && (Date.now() - catalogCacheTime < CATALOG_CACHE_TTL)) {
        console.log('✓ Using cached catalog');
        if (updateState) {
            setState('catalog', catalogCache);
        }
        enrichDeployedAppsWithIcons();
        return catalogCache;
    }

    try {
        const response = await authFetch(`${API_BASE}/apps/catalog`);
        if (!response.ok) {
            console.warn(`⚠️  Failed to load catalog: ${response.status} ${response.statusText}`);
            const emptyCatalog = { items: [], categories: [] };
            if (updateState) {
                setState('catalog', emptyCatalog);
            }
            return emptyCatalog;
        }
        const catalog = await response.json();
        
        // Update state only if requested
        if (updateState) {
            setState('catalog', catalog);
        }
        
        // Update cache
        catalogCache = catalog;
        catalogCacheTime = Date.now();
        
        console.log(`✅ Catalog loaded: ${catalog.items?.length || 0} items`);
        
        // Enrich deployed apps with icon URLs after catalog is loaded
        enrichDeployedAppsWithIcons();
        
        return catalog;
    } catch (error) {
        console.error('❌ Error loading catalog:', error);
        const emptyCatalog = { items: [], categories: [] };
        if (updateState) {
            setState('catalog', emptyCatalog);
        }
        return emptyCatalog;
    }
}

/**
 * Enrich deployed apps with icon URLs from catalog
 * Matches deployed apps with catalog items to get icon URLs
 * @private
 */
function enrichDeployedAppsWithIcons() {
    const state = getState();

    // Only run if both catalog and deployed apps are loaded
    // CRITICAL: Check state.catalog is not null before accessing .items
    if (!state.catalog || !state.catalog.items || !state.deployedApps || state.deployedApps.length === 0) {
        console.log('⏭️ Skipping icon enrichment (catalog or apps not loaded yet)');
        return;
    }

    // Match deployed apps with catalog items to get icon URLs
    let enrichedCount = 0;
    state.deployedApps.forEach(deployedApp => {
        const catalogItem = state.catalog.items.find(item => item.id === deployedApp.catalog_id);
        if (catalogItem && catalogItem.icon) {
            deployedApp.icon = catalogItem.icon;
            enrichedCount++;
        }
    });

    console.log(`✅ Enriched ${enrichedCount} apps with catalog icons`);
}

/**
 * Refresh app list
 * Reloads deployed apps and updates UI
 * 
 * @returns {Promise<void>}
 */
export async function refreshAppList() {
    await loadDeployedApps();
    updateUI();
}

/**
 * Update all UI components
 * Updates stats, counts, and recent apps section
 */
export function updateUI() {
    updateStats();
    updateAppsCount();
    updateRecentApps();
}

/**
 * Update dashboard statistics
 * Updates hero section stats (apps, nodes, containers)
 */
export function updateStats() {
    updateHeroStats();
}

/**
 * Update hero section stats
 * @private
 */
function updateHeroStats() {
    const state = getState();
    
    // Update hero section stats
    const heroAppsCount = document.getElementById('heroAppsCount');
    const heroNodesCount = document.getElementById('heroNodesCount');
    const heroContainersCount = document.getElementById('heroContainersCount');

    if (heroAppsCount) {
        const totalApps = state.deployedApps.length;
        heroAppsCount.textContent = totalApps;
    }

    if (heroNodesCount) {
        const activeNodes = state.nodes.filter(n => n.status === 'online').length;
        heroNodesCount.textContent = activeNodes;
    }

    if (heroContainersCount) {
        const runningContainers = state.deployedApps.filter(a => a.status === 'running').length;
        heroContainersCount.textContent = runningContainers;
    }
}

/**
 * Update apps count badge
 * Updates count display in navigation
 */
export function updateAppsCount() {
    const state = getState();
    const count = (state.deployedApps && state.deployedApps.length) || 0;

    // Update both old sidebar badge (if exists) and new nav rack badge
    const appsCountEl = document.getElementById('appsCount');
    if (appsCountEl) {
        appsCountEl.textContent = count;
    }

    // Update new navigation badge
    if (typeof window.updateAppsCountBadge !== 'undefined') {
        window.updateAppsCountBadge(count);
    }
}

/**
 * Update recent apps section
 * Renders quick access icons for deployed apps on dashboard
 */
export function updateRecentApps() {
    console.log('📱 updateRecentApps() called');
    const state = getState();
    const container = document.getElementById('quickApps');

    if (!container) {
        console.warn('⚠️  quickApps container not found in DOM');
        return;
    }
    
    console.log(`✓ quickApps container found, deployedApps count: ${state.deployedApps.length}`);

    if (state.deployedApps.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i data-lucide="package" style="width: 48px; height: 48px;"></i>
                </div>
                <h3 class="empty-title">No applications yet</h3>
                <p class="empty-message">Deploy your first application from the catalog to get started.</p>
                <button class="btn btn-primary" onclick="window.router.navigateTo('catalog')">Browse Catalog</button>
            </div>
        `;
        initIcons();
        return;
    }

    // Show all apps as quick access icons
    container.innerHTML = state.deployedApps.map(app => {
        const isRunning = app.status === 'running';
        const appUrl = (app.url && app.url !== 'None' && app.url !== 'null') ? app.url : null;

        // Get icon
        let icon = getIcon(app.name || app.id);
        if (app.icon) {
            const escapedFallback = typeof icon === 'string' ? icon.replace(/'/g, "&#39;").replace(/"/g, "&quot;") : icon;
            icon = `<img
                src="${app.icon}"
                alt="${app.name}"
                style="width: 100%; height: 100%; object-fit: contain;"
                onerror="this.style.display='none'; this.insertAdjacentHTML('afterend', '${escapedFallback}');"
            />`;
        }

        // Prepare app data for canvas click
        const appDataForCanvas = JSON.stringify({
            id: app.id,
            name: app.name,
            hostname: app.hostname,
            iframe_url: appUrl || app.url,
            url: appUrl || app.url,
            status: app.status
        }).replace(/"/g, '&quot;');

        // Click handler
        const clickHandler = (isRunning && appUrl)
            ? `onclick="openCanvas(${appDataForCanvas})" style="cursor: pointer;"`
            : `onclick="window.router.navigateTo('apps')" style="cursor: pointer;"`;

        return `
            <div class="quick-app-item ${isRunning ? 'running' : 'stopped'}"
                 ${clickHandler}
                 title="${app.name || app.hostname} - ${isRunning ? 'Click to open' : 'Not running'}">
                <div class="quick-app-icon">
                    ${icon}
                </div>
                <div class="quick-app-status ${isRunning ? 'running' : 'stopped'}"></div>
                <div class="quick-app-name">${app.name || app.hostname}</div>
            </div>
        `;
    }).join('');

    // Reinitialize Lucide icons
    initIcons();
}

/**
 * Clear catalog cache
 * Forces next loadCatalog() to fetch fresh data
 */
export function clearCatalogCache() {
    catalogCache = null;
    catalogCacheTime = 0;
}

/**
 * Get catalog cache status
 * @returns {Object} Cache status with isCached and age
 */
export function getCatalogCacheStatus() {
    return {
        isCached: !!catalogCache,
        age: catalogCache ? Date.now() - catalogCacheTime : 0,
        ttl: CATALOG_CACHE_TTL
    };
}

// Backward compatibility: Expose to window
if (typeof window !== 'undefined') {
    window.dataService = {
        loadDeployedApps,
        loadCatalog,
        refreshAppList,
        updateUI,
        updateStats,
        updateAppsCount,
        updateRecentApps,
        clearCatalogCache,
        getCatalogCacheStatus
    };
}
