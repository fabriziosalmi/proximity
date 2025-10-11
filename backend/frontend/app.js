// Utility function to reinitialize Lucide icons
function initLucideIcons() {
    if (typeof lucide !== 'undefined') {
        setTimeout(() => lucide.createIcons(), 0);
    }
}

// Sidebar collapse functionality
function initSidebarToggle() {
    const sidebar = document.querySelector('.sidebar');
    const toggleButton = document.getElementById('sidebarToggle');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar) {
        // Load saved state for desktop
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
        }
        
        // Desktop toggle button
        if (toggleButton) {
            toggleButton.addEventListener('click', () => {
                const isMobile = window.innerWidth <= 1024;
                
                if (isMobile) {
                    // On mobile: toggle 'active' class to show/hide sidebar
                    sidebar.classList.toggle('active');
                    if (overlay) {
                        overlay.classList.toggle('active');
                    }
                } else {
                    // On desktop: toggle 'collapsed' class to collapse/expand
                    sidebar.classList.toggle('collapsed');
                    // Save state
                    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
                }
                
                // Reinitialize icons after toggle animation
                setTimeout(() => initLucideIcons(), 300);
            });
        }
        
        // Mobile menu button
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => {
                sidebar.classList.add('active');
                if (overlay) {
                    overlay.classList.add('active');
                }
                // Reinitialize icons after toggle animation
                setTimeout(() => initLucideIcons(), 300);
            });
        }
        
        // Close sidebar when clicking overlay (mobile)
        if (overlay) {
            overlay.addEventListener('click', () => {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
            });
        }
        
        // Handle window resize: reset classes appropriately
        window.addEventListener('resize', () => {
            const isMobile = window.innerWidth <= 1024;
            if (!isMobile) {
                // Desktop: remove mobile 'active' class
                sidebar.classList.remove('active');
                if (overlay) {
                    overlay.classList.remove('active');
                }
            } else {
                // Mobile: remove desktop 'collapsed' class
                sidebar.classList.remove('collapsed');
            }
        });
    }
}

// Proximity UI - State-of-the-Art Application Management Interface
const API_BASE = 'http://localhost:8765/api/v1';

// Authentication Management
const Auth = {
    TOKEN_KEY: 'proximity_token',
    USER_KEY: 'proximity_user',
    
    // Migrate old token if exists
    migrateOldToken() {
        const oldToken = localStorage.getItem('authToken');
        const newToken = localStorage.getItem(this.TOKEN_KEY);
        
        // If old token exists but new one doesn't, migrate it
        if (oldToken && !newToken) {
            console.log('🔄 Migrating auth token to new key...');
            localStorage.setItem(this.TOKEN_KEY, oldToken);
            localStorage.removeItem('authToken');
        }
    },
    
    // Get stored token
    getToken() {
        // Ensure migration has happened
        this.migrateOldToken();
        const token = localStorage.getItem(this.TOKEN_KEY);
        console.log('[Auth.getToken] Retrieved token:', token ? `${token.substring(0, 20)}... (${token.length} chars)` : 'NONE');
        return token;
    },
    
    // Store token and user info
    setToken(token, user) {
        console.log('[Auth.setToken] Storing token:', token ? `${token.substring(0, 20)}... (${token.length} chars)` : 'NONE');
        console.log('[Auth.setToken] Storing user:', user ? user.username : 'NONE');
        localStorage.setItem(this.TOKEN_KEY, token);
        if (user) {
            localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        }
        console.log('[Auth.setToken] ✓ Token and user saved to localStorage');
    },
    
    // Get stored user info
    getUser() {
        const userJson = localStorage.getItem(this.USER_KEY);
        return userJson ? JSON.parse(userJson) : null;
    },
    
    // Check if user is authenticated
    isAuthenticated() {
        return !!this.getToken();
    },
    
    // Clear authentication
    logout() {
        console.warn('[Auth] Logging out - clearing token and user data');
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        // Don't reload immediately - let the caller decide
        // window.location.reload();
    },
    
    // Get authorization headers
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        return headers;
    }
};

// Enhanced fetch with authentication
async function authFetch(url, options = {}) {
    const token = Auth.getToken();
    
    console.log('[authFetch] Preparing request');
    console.log('  • URL:', url);
    console.log('  • Token present:', !!token);
    console.log('  • Token (first 20 chars):', token ? token.substring(0, 20) + '...' : 'NONE');
    console.log('  • Method:', options.method || 'GET');
    
    const defaultOptions = {
        headers: Auth.getHeaders(),
        ...options
    };
    
    // Merge headers properly
    if (options.headers) {
        defaultOptions.headers = {
            ...defaultOptions.headers,
            ...options.headers
        };
    }
    
    try {
        const response = await fetch(url, defaultOptions);
        
        console.log('[authFetch] Response received');
        console.log('  • Status:', response.status);
        console.log('  • OK:', response.ok);
        
        // Handle 401 Unauthorized
        if (response.status === 401) {
            console.error('[authFetch] ❌ 401 Unauthorized');
            const responseText = await response.text();
            console.error('  • Response body:', responseText);
            console.warn('  • Logging out and showing login modal');
            Auth.logout();
            showLoginModal();
            throw new Error('Authentication required');
        }
        
        return response;
    } catch (error) {
        // Network errors
        if (error.message === 'Authentication required') {
            throw error;
        }
        console.error('[authFetch] Network error:', error);
        throw error;
    }
}


// Update user info in sidebar
function updateUserInfo() {
    const user = Auth.getUser();
    if (user) {
        const userNameEl = document.querySelector('.user-name');
        const userRoleEl = document.querySelector('.user-role');
        const userAvatarEl = document.querySelector('.user-avatar');
        
        if (userNameEl) {
            userNameEl.textContent = user.username || 'User';
        }
        if (userRoleEl) {
            userRoleEl.textContent = user.role === 'admin' ? 'Administrator' : 'User';
        }
        if (userAvatarEl) {
            const initials = (user.username || 'U').substring(0, 2).toUpperCase();
            userAvatarEl.textContent = initials;
        }
    }
}

// Application State
const state = {
    systemInfo: null,
    nodes: [],
    apps: [],
    catalog: null,
    currentView: 'dashboard',
    deployedApps: [],
    proximityMode: 'AUTO' // AUTO or PRO mode
};

// Initialize Application
async function init() {
    console.log('🚀 Initializing Proximity UI...');
    
    // Initialize Top Navigation Rack (new horizontal nav)
    if (typeof initTopNavRack !== 'undefined') {
        initTopNavRack();
    }
    
    // Check authentication first
    if (!Auth.isAuthenticated()) {
        console.log('⚠️  No authentication token found - showing auth modal');
        showAuthModal();
        return;
    }
    
    // Update user info in navigation
    if (typeof updateUserInfoNav !== 'undefined') {
        updateUserInfoNav();
    } else {
        updateUserInfo(); // Fallback to old function
    }
    
    showLoading('Connecting to Proximity API...');
    
    try {
        await Promise.all([
            loadSystemInfo(),
            loadNodes(),
            loadDeployedApps(),
            loadCatalog()
        ]);
        
        updateUI();
        setupEventListeners();
        hideLoading();

        // Initialize Lucide icons
        initLucideIcons();

        // Initialize card hover sounds (event delegation - once for all cards)
        initCardHoverSounds();

        console.log('✓ Proximity UI initialized successfully');
    } catch (error) {
        hideLoading();
        console.error('Failed to initialize:', error);
        // Show error notification only if it's a real connection issue
        if (error.message.includes('fetch') || error.message.includes('network')) {
            showNotification('Failed to connect to API. Please check the backend is running.', 'error');
        }
    }
    
    // Auto-refresh every 30 seconds
    setInterval(async () => {
        await loadSystemInfo();
        await loadDeployedApps();
        updateUI();
    }, 30000);
}

// API Calls
async function loadSystemInfo() {
    try {
        const response = await authFetch(`${API_BASE}/system/info`);
        if (!response.ok) {
            console.warn('Failed to load system info:', response.status);
            state.systemInfo = null;
            return;
        }
        state.systemInfo = await response.json();
    } catch (error) {
        console.error('Error loading system info:', error);
        state.systemInfo = null;
        // Don't throw - allow app to continue
    }
}

async function loadNodes() {
    try {
        const response = await authFetch(`${API_BASE}/system/nodes`);
        if (!response.ok) {
            console.warn('Failed to load nodes:', response.status);
            state.nodes = [];
            return;
        }
        state.nodes = await response.json();
    } catch (error) {
        console.error('Error loading nodes:', error);
        state.nodes = [];
        // Don't throw - allow app to continue
    }
}

async function loadDeployedApps() {
    try {
        const response = await authFetch(`${API_BASE}/apps`);
        if (!response.ok) throw new Error('Failed to load apps');
        state.deployedApps = await response.json();
        
        console.log('Deployed apps loaded:', state.deployedApps);
        
        // Enrich deployed apps with icon URLs from catalog
        enrichDeployedAppsWithIcons();
    } catch (error) {
        console.error('Error loading deployed apps:', error);
        state.deployedApps = [];
    }
}

async function loadCatalog() {
    try {
        const response = await authFetch(`${API_BASE}/apps/catalog`);
        if (!response.ok) {
            console.warn('Failed to load catalog:', response.status);
            state.catalog = { items: [], categories: [] };
            return;
        }
        state.catalog = await response.json();
        
        // Enrich deployed apps with icon URLs after catalog is loaded
        enrichDeployedAppsWithIcons();
    } catch (error) {
        console.error('Error loading catalog:', error);
        state.catalog = { items: [], categories: [] };
        // Don't throw - allow app to continue
    }
}

function enrichDeployedAppsWithIcons() {
    // Only run if both catalog and deployed apps are loaded
    if (!state.catalog.items || !state.deployedApps || state.deployedApps.length === 0) {
        return;
    }
    
    // Match deployed apps with catalog items to get icon URLs
    state.deployedApps.forEach(deployedApp => {
        const catalogItem = state.catalog.items.find(item => item.id === deployedApp.catalog_id);
        if (catalogItem && catalogItem.icon) {
            deployedApp.icon = catalogItem.icon;
        }
    });
}

// UI Update Functions
function updateUI() {
    updateStats();
    updateAppsCount();
    updateRecentApps();
}

function updateStats() {
    // Update hero stats
    updateHeroStats();
}

function updateHeroStats() {
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


function oldUpdateStats() {
    // Legacy function - kept for compatibility
    if (state.systemInfo) {
        // Calculate resource usage
        if (state.systemInfo.nodes && state.systemInfo.nodes.length > 0 && statResources) {
            const totalMem = state.systemInfo.nodes.reduce((sum, n) => sum + (n.maxmem || 0), 0);
            const usedMem = state.systemInfo.nodes.reduce((sum, n) => sum + (n.mem || 0), 0);
            const percentage = totalMem > 0 ? Math.round((usedMem / totalMem) * 100) : 0;
            statResources.textContent = `${percentage}%`;
        }
    }
}

function updateAppsCount() {
    const count = state.deployedApps.length;
    
    // Update both old sidebar badge (if exists) and new nav rack badge
    const appsCountEl = document.getElementById('appsCount');
    if (appsCountEl) {
        appsCountEl.textContent = count;
    }
    
    // Update new navigation badge
    if (typeof updateAppsCountBadge !== 'undefined') {
        updateAppsCountBadge(count);
    }
}

function updateRecentApps() {
    const container = document.getElementById('quickApps');

    if (!container) return;

    if (state.deployedApps.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i data-lucide="package" style="width: 48px; height: 48px;"></i>
                </div>
                <h3 class="empty-title">No applications yet</h3>
                <p class="empty-message">Deploy your first application from the catalog to get started.</p>
                <button class="btn btn-primary" onclick="showView('catalog')">Browse Catalog</button>
            </div>
        `;
        initLucideIcons();
        return;
    }

    // Show all apps as quick access icons
    container.innerHTML = state.deployedApps.map(app => {
        const isRunning = app.status === 'running';
        const appUrl = (app.url && app.url !== 'None' && app.url !== 'null') ? app.url : null;

        // Get icon
        let icon = getAppIcon(app.name || app.id);
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
            : `onclick="showView('apps')" style="cursor: pointer;"`;

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
    initLucideIcons();
}

// ============================================
// APP CARD RENDERING (Template-based)
// ============================================

/**
 * Render app icon with proper fallback handling
 * @param {HTMLElement} iconContainer - The icon container element
 * @param {Object} app - App data
 */
function renderAppIcon(iconContainer, app) {
    // Clear existing content
    iconContainer.innerHTML = '';

    // Get fallback icon (emoji or SVG)
    const fallbackIcon = getAppIcon(app.name || app.id);

    // If app has custom icon URL from catalog
    if (app.icon) {
        const img = document.createElement('img');
        img.src = app.icon;
        img.alt = app.name || app.id;
        img.style.width = '75%';
        img.style.height = '75%';
        img.style.objectFit = 'contain';

        // Fallback to emoji/SVG on error
        img.onerror = function() {
            this.style.display = 'none';
            if (typeof fallbackIcon === 'string') {
                iconContainer.insertAdjacentHTML('beforeend', fallbackIcon);
            }
        };

        iconContainer.appendChild(img);
    } else {
        // Use fallback icon directly
        if (typeof fallbackIcon === 'string') {
            iconContainer.innerHTML = fallbackIcon;
        }
    }
}

/**
 * Populate deployed app card with data
 * @param {DocumentFragment} cardElement - Cloned template
 * @param {Object} app - App data
 */
function populateDeployedCard(cardElement, app) {
    const isRunning = app.status === 'running';
    const appUrl = (app.url && app.url !== 'None' && app.url !== 'null') ? app.url : null;
    const displayUrl = appUrl || 'IP not available';

    // Populate icon
    const iconContainer = cardElement.querySelector('.app-icon-lg');
    renderAppIcon(iconContainer, app);

    // Populate text (safe textContent)
    cardElement.querySelector('.app-name').textContent = app.name || app.id;
    cardElement.querySelector('.status-text').textContent = app.status || 'Unknown';

    // Add status class to badge
    const statusBadge = cardElement.querySelector('.status-badge-compact');
    const statusClass = app.status ? app.status.toLowerCase() : 'stopped';
    statusBadge.classList.add(statusClass);

    // Populate URL
    const urlLink = cardElement.querySelector('.connection-link');
    if (appUrl) {
        urlLink.href = appUrl;
        urlLink.textContent = displayUrl;
        if (!isRunning) {
            urlLink.style.opacity = '0.5';
            urlLink.style.pointerEvents = 'none';
        }
    } else {
        urlLink.href = '#';
        urlLink.textContent = 'IP not available';
        urlLink.style.opacity = '0.5';
        urlLink.style.pointerEvents = 'none';
    }

    // Populate node, LXC ID, date
    cardElement.querySelector('.node-value').textContent = app.node || 'N/A';
    cardElement.querySelector('.lxc-id-value').textContent = app.lxc_id || 'N/A';
    cardElement.querySelector('.date-value').textContent = formatDate(app.created_at);

    // Update action button states
    const toggleBtn = cardElement.querySelector('[data-action="toggle-status"]');
    const toggleIcon = toggleBtn.querySelector('i');
    toggleBtn.title = isRunning ? 'Stop' : 'Start';
    toggleIcon.setAttribute('data-lucide', isRunning ? 'pause' : 'play');

    const restartBtn = cardElement.querySelector('[data-action="restart"]');
    restartBtn.title = isRunning ? 'Restart' : 'Start';

    const openExternalBtn = cardElement.querySelector('[data-action="open-external"]');
    if (!isRunning || !appUrl) {
        openExternalBtn.disabled = true;
        openExternalBtn.style.opacity = '0.5';
    }

    // Show canvas button if iframe_url exists
    const canvasBtn = cardElement.querySelector('[data-action="canvas"]');
    if (app.iframe_url || appUrl) {
        canvasBtn.style.display = 'flex';
    }
}

/**
 * Attach event listeners to deployed app card
 * @param {DocumentFragment} cardElement - Cloned template
 * @param {Object} app - App data
 */
function attachDeployedCardEvents(cardElement, app) {
    const isRunning = app.status === 'running';
    const appUrl = (app.url && app.url !== 'None' && app.url !== 'null') ? app.url : null;

    // Action button handlers
    const actions = {
        'toggle-status': () => controlApp(app.id, isRunning ? 'stop' : 'start'),
        'open-external': () => appUrl && window.open(appUrl, '_blank'),
        'view-logs': () => showAppLogs(app.id, app.hostname),
        'console': () => showAppConsole(app.id, app.hostname),
        'backups': () => showBackupModal(app.id),
        'update': () => showUpdateModal(app.id),
        'volumes': () => showAppVolumes(app.id),
        'monitoring': () => showMonitoringModal(app.id, app.name),
        'canvas': () => openCanvas({
            id: app.id,
            name: app.name,
            hostname: app.hostname,
            iframe_url: appUrl || app.url,
            url: appUrl || app.url,
            status: app.status
        }),
        'restart': () => controlApp(app.id, isRunning ? 'restart' : 'start'),
        'clone': () => showCloneModal(app.id, app.name),
        'edit-config': () => showEditConfigModal(app.id, app.name),
        'delete': () => confirmDeleteApp(app.id, app.name)
    };

    // Attach event listeners to action buttons
    cardElement.querySelectorAll('.action-icon').forEach(btn => {
        const action = btn.dataset.action;
        if (actions[action]) {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                actions[action]();
            });
        }
    });

    // Canvas click on whole card (if running and has URL)
    const card = cardElement.querySelector('.app-card');
    if (isRunning && appUrl) {
        card.style.cursor = 'pointer';
        card.title = 'Click to open in canvas';
        card.addEventListener('click', (e) => {
            // Don't trigger if clicking on action buttons or links
            if (!e.target.closest('.action-icon, .connection-link')) {
                openCanvas({
                    id: app.id,
                    name: app.name,
                    hostname: app.hostname,
                    iframe_url: appUrl,
                    url: appUrl,
                    status: app.status
                });
            }
        });
    } else {
        card.style.cursor = 'default';
        card.title = 'App must be running to open in canvas';
    }

    // Prevent link propagation
    const urlLink = cardElement.querySelector('.connection-link');
    if (urlLink) {
        urlLink.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
}

/**
 * Populate catalog app card with data
 * @param {DocumentFragment} cardElement - Cloned template
 * @param {Object} app - App data
 */
function populateCatalogCard(cardElement, app) {
    // Populate icon
    const iconContainer = cardElement.querySelector('.app-icon-md');
    renderAppIcon(iconContainer, app);

    // Populate text (safe textContent)
    cardElement.querySelector('.app-name').textContent = app.name || 'Unknown';
    cardElement.querySelector('.category-badge').textContent = app.category || 'Other';
    cardElement.querySelector('.app-description-compact').textContent = app.description || 'No description available';
    cardElement.querySelector('.cpu-value').textContent = `${app.min_cpu || 1} vCPU`;
    cardElement.querySelector('.memory-value').textContent = `${app.min_memory || 512}MB`;
}

/**
 * Attach event listeners to catalog app card
 * @param {DocumentFragment} cardElement - Cloned template
 * @param {Object} app - App data
 */
function attachCatalogCardEvents(cardElement, app) {
    const card = cardElement.querySelector('.app-card');
    card.style.cursor = 'pointer';
    card.addEventListener('click', () => {
        showDeployModal(app.id);
    });
}

/**
 * Render app card using template cloning (NEW PATTERN)
 * @param {Object} app - App data
 * @param {HTMLElement} container - Container to append card to
 * @param {boolean} isDeployed - Whether this is a deployed app card
 */
function renderAppCard(app, container, isDeployed = false) {
    const templateId = isDeployed ? 'deployed-app-card-template' : 'catalog-app-card-template';
    const template = document.getElementById(templateId);

    if (!template) {
        console.error(`Template ${templateId} not found!`);
        return;
    }

    // Clone template
    const clone = template.content.cloneNode(true);

    // Populate and attach events
    if (isDeployed) {
        populateDeployedCard(clone, app);
        attachDeployedCardEvents(clone, app);
    } else {
        populateCatalogCard(clone, app);
        attachCatalogCardEvents(clone, app);
    }

    // Append to container
    container.appendChild(clone);
}

// ============================================
// View Management
function showView(viewName) {
    // Hide submenu when changing views
    if (typeof hideSubmenu === 'function') {
        hideSubmenu();
    }

    // Update navigation - handle both .nav-item and .nav-rack-item
    document.querySelectorAll('.nav-item, .nav-rack-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.view === viewName) {
            item.classList.add('active');
        }
    });

    // Hide all views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.add('hidden');
    });

    // Show requested view
    const viewElement = document.getElementById(`${viewName}View`);
    if (viewElement) {
        viewElement.classList.remove('hidden');
        state.currentView = viewName;

        // Load view content
        switch(viewName) {
            case 'dashboard':
                // Already loaded
                break;
            case 'apps':
                renderAppsView();
                break;
            case 'catalog':
                renderCatalogView();
                break;
            case 'nodes':
                renderNodesView();
                break;
            case 'monitoring':
                renderMonitoringView();
                break;
            case 'settings':
                renderSettingsView();
                break;
            case 'uilab':
                renderUiLabView();
                break;
        }

        // Reinitialize Lucide icons after view change
        initLucideIcons();
    }
}

// Deploy New App Button Click with Sound and Animation
function deployNewAppClick(event) {
    const button = event.currentTarget;
    
    // Add clicked class for animation
    button.classList.add('clicked');
    
    // Play click sound
    playClickSound();
    
    // Remove clicked class after animation
    setTimeout(() => {
        button.classList.remove('clicked');
    }, 600);
    
    // Navigate to catalog after a brief delay for effect
    setTimeout(() => {
        showView('catalog');
    }, 150);
}

// Play subtle click sound using Web Audio API
function playClickSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Create oscillator for a subtle "click" sound
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Configure sound - high pitch, very short duration
        oscillator.frequency.value = 800; // Hz
        oscillator.type = 'sine';
        
        // Very subtle volume with quick fade
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.05);
        
        // Play for just 50ms
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.05);
    } catch (e) {
        // Silently fail if audio not supported
        console.log('Audio not supported');
    }
}

function renderAppsView() {
    const view = document.getElementById('appsView');
    view.classList.remove('has-sub-nav'); // Remove old sub-nav class

    // Search bar is now in the submenu - no need for it here anymore
    const content = `
        <div class="apps-grid deployed" id="allAppsGrid"></div>
    `;

    view.innerHTML = content;

    // Render app cards using template cloning (NEW PATTERN)
    const grid = document.getElementById('allAppsGrid');

    if (state.deployedApps.length === 0) {
        // Show empty state
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📦</div>
                <h3 class="empty-title">No applications deployed</h3>
                <p class="empty-message">Start by deploying an application from the catalog.</p>
                <button class="btn btn-primary" onclick="showView('catalog')">Browse Catalog</button>
            </div>
        `;
    } else {
        // Render each app card using template
        for (const app of state.deployedApps) {
            renderAppCard(app, grid, true);
        }
    }

    // Initialize Lucide icons
    initLucideIcons();

    // Hover sounds are handled automatically via event delegation (initCardHoverSounds)
}

function renderCatalogView() {
    console.log('🏪 renderCatalogView() called');
    const view = document.getElementById('catalogView');
    view.classList.remove('has-sub-nav'); // Remove old sub-nav class

    if (!state.catalog || !state.catalog.items) {
        console.log('⚠️  Catalog data not loaded yet');
        view.innerHTML = '<div class="loading-spinner"></div>';
        return;
    }
    console.log(`✓ Rendering ${state.catalog.items.length} catalog items`);

    const content = `
        <div class="search-bar-container">
            <div class="search-bar">
                <i data-lucide="search" class="search-icon"></i>
                <input
                    type="text"
                    class="search-input"
                    id="catalogSearchInput"
                    placeholder="Search applications by name, description, or category..."
                    oninput="searchCatalog(this.value)"
                />
                <button class="search-clear" id="catalogClearSearch" onclick="clearCatalogSearch()" style="display: none;">
                    <i data-lucide="x"></i>
                </button>
            </div>
            <div class="search-results-count" id="catalogResultsCount" style="display: none;"></div>
        </div>

        <div class="apps-grid" id="catalogGrid"></div>
    `;
    
    view.innerHTML = content;

    // Render catalog app cards using template cloning (NEW PATTERN)
    const grid = document.getElementById('catalogGrid');
    for (const app of state.catalog.items) {
        renderAppCard(app, grid, false);
    }

    // Initialize Lucide icons
    initLucideIcons();

    // Hover sounds are handled automatically via event delegation (initCardHoverSounds)
}

async function renderNodesView() {
    const view = document.getElementById('nodesView');

    // Load infrastructure status
    showLoading('Loading infrastructure status...');
    let infrastructure = null;
    let error = null;

    try {
        const token = Auth.getToken();
        if (token) {
            console.log('[Infrastructure] Fetching status...');
            const response = await authFetch(`${API_BASE}/system/infrastructure/status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            console.log('[Infrastructure] Response status:', response.status);
            
            if (response.ok) {
                const result = await response.json();
                console.log('[Infrastructure] Result:', result);
                infrastructure = result.data;
                console.log('[Infrastructure] Infrastructure data:', infrastructure);
                console.log('[Infrastructure] Appliance:', infrastructure?.appliance);
                console.log('[Infrastructure] Health status:', infrastructure?.health_status);
            } else {
                error = `Failed to load infrastructure status (${response.status})`;
                console.error('[Infrastructure] Error:', error);
            }
        } else {
            error = 'Not authenticated';
            console.error('[Infrastructure] No auth token');
        }
    } catch (err) {
        error = err.message || 'Failed to load infrastructure';
        console.error('[Infrastructure] Exception:', err);
    }
    hideLoading();

    // Prepare appliance info
    const appliance = infrastructure?.appliance || null;
    const services = infrastructure?.services || {};
    const network = infrastructure?.network || {};
    const connected_apps = infrastructure?.applications || infrastructure?.connected_apps || [];
    const health_status = infrastructure?.health_status || 'unknown';
    
    console.log('[Infrastructure] Final state:', {
        appliance: !!appliance,
        services: Object.keys(services).length,
        connected_apps: connected_apps.length,
        health_status,
        error
    });

    const content = `
        <!-- Network Appliance Card -->
        ${appliance ? `
        <div class="app-card deployed" style="margin-bottom: 2rem;">
            <!-- Header with icon, name, status and quick actions -->
            <div class="app-card-header">
                <div class="app-icon-lg">🌐</div>
                <div class="app-info">
                    <h3 class="app-name">${appliance.hostname || 'Network Appliance'}</h3>
                        <span class="status-badge ${appliance.status === 'running' ? 'running' : 'stopped'}">
                            <span class="status-dot"></span>
                            ${appliance.status || 'unknown'}
                        </span>
                    </div>
                        
                        <!-- Quick Actions -->
                        <div class="app-quick-actions">
                            <button class="action-icon" title="Restart Appliance" onclick="restartAppliance()">
                                <i data-lucide="rotate-cw"></i>
                            </button>
                            <button class="action-icon" title="View Logs" onclick="viewApplianceLogs()">
                                <i data-lucide="file-text"></i>
                            </button>
                            <button class="action-icon" title="Test NAT" onclick="testNAT()">
                                <i data-lucide="zap"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Connection info -->
                    <div class="app-connection-info">
                        <div class="connection-item" title="VMID">
                            <i data-lucide="hash" class="connection-icon"></i>
                            <span class="connection-value">${appliance.vmid || 'N/A'}</span>
                        </div>
                        <div class="connection-item" title="Node">
                            <i data-lucide="server" class="connection-icon"></i>
                            <span class="connection-value">${appliance.node || 'N/A'}</span>
                        </div>
                        <div class="connection-item" title="WAN interface (eth0) - DHCP from external network via vmbr0">
                            <i data-lucide="globe" class="connection-icon"></i>
                            <span class="connection-value">WAN: ${appliance.wan_ip || 'N/A'}</span>
                        </div>
                        <div class="connection-item" title="LAN interface (eth1) - Gateway for applications on proximity-lan">
                            <i data-lucide="network" class="connection-icon"></i>
                            <span class="connection-value">LAN: ${appliance.lan_ip || 'N/A'}</span>
                        </div>
                    </div>

                    <!-- Resource stats -->
                    <div class="app-connection-info" style="margin-top: 0.5rem;">
                        <div class="connection-item">
                            <i data-lucide="cpu" class="connection-icon"></i>
                            <span class="connection-value">${appliance.cores || 'N/A'} cores</span>
                        </div>
                        <div class="connection-item">
                            <i data-lucide="memory-stick" class="connection-icon"></i>
                            <span class="connection-value">${appliance.memory || 'N/A'} MB</span>
                        </div>
                        <div class="connection-item">
                            <i data-lucide="hard-drive" class="connection-icon"></i>
                            <span class="connection-value">${appliance.disk || 'N/A'} GB</span>
                        </div>
                        <div class="connection-item">
                            <i data-lucide="clock" class="connection-icon"></i>
                            <span class="connection-value">${appliance.uptime || 'N/A'}</span>
                        </div>
                    </div>

                    <div id="infrastructureStatus" style="margin-top: 1rem;"></div>
                </div>
        ` : ''}

        <!-- Services Health Grid -->
        ${Object.keys(services).length > 0 ? `
        <div class="services-grid" style="margin-bottom: 2rem;">
            ${Object.entries(services).map(([name, service]) => `
                    <div class="service-card ${service.healthy ? 'healthy' : 'unhealthy'}">
                        <div class="service-header">
                            <div class="service-icon">
                                ${name === 'dnsmasq' ? '🌐' :
                                  name === 'caddy' ? '🔀' :
                                  name === 'nat' ? '🔗' : '⚙️'}
                            </div>
                            <div class="service-info">
                                <h3 class="service-name">${name.charAt(0).toUpperCase() + name.slice(1)}</h3>
                                <span class="service-status ${service.healthy ? 'healthy' : 'unhealthy'}">
                                    ${service.healthy ? '● Running' : '○ Stopped'}
                                </span>
                            </div>
                        </div>
                        ${service.details ? `
                        <div class="service-details">
                            <small>${service.details}</small>
                        </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        ` : ''}

        <!-- Network Configuration -->
        ${network.subnet ? `
        <div class="app-card deployed" style="margin-bottom: 2rem;">
            <div class="app-connection-info">
                    <div class="connection-item">
                        <i data-lucide="network" class="connection-icon"></i>
                        <span class="connection-value">Bridge: ${network.bridge || 'proximity-lan'}</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="wifi" class="connection-icon"></i>
                        <span class="connection-value">Subnet: ${network.subnet || 'N/A'}</span>
                    </div>
                    <div class="connection-item">
                            <i data-lucide="door-open" class="connection-icon"></i>
                            <span class="connection-value">Gateway: ${network.gateway || 'N/A'}</span>
                        </div>
                        <div class="connection-item">
                            <i data-lucide="settings" class="connection-icon"></i>
                            <span class="connection-value">DHCP: ${network.dhcp_range || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="app-connection-info" style="margin-top: 0.5rem;">
                        <div class="connection-item">
                        <i data-lucide="globe" class="connection-icon"></i>
                        <span class="connection-value">DNS: ${network.dns_domain || 'prox.local'}</span>
                    </div>
                </div>
            </div>
        ` : ''}

        <!-- Connected Apps -->
        ${connected_apps && connected_apps.length > 0 ? `
        <div class="connected-apps-table">
            <table class="infrastructure-table">
                    <thead>
                        <tr>
                            <th>App Name</th>
                            <th>VMID</th>
                            <th>IP Address</th>
                            <th>Status</th>
                            <th>DNS Name</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${connected_apps.map(app => `
                            <tr>
                                <td><strong>${app.name || 'N/A'}</strong></td>
                                <td>${app.vmid || 'N/A'}</td>
                                <td><code>${app.ip_address || 'N/A'}</code></td>
                                <td>
                                    <span class="status-badge ${app.status === 'running' ? 'running' : 'stopped'}">
                                        <span class="status-dot"></span>
                                        ${app.status || 'unknown'}
                                    </span>
                                </td>
                                <td><code>${app.dns_name || app.name + '.prox.local' || 'N/A'}</code></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        ` : ''}

        <!-- Proxmox Nodes -->
        <div class="apps-grid deployed">
            ${state.nodes.map(node => `
                    <div class="app-card deployed">
                        <div class="app-card-header">
                            <div class="app-icon-lg">🖥️</div>
                            <div class="app-info">
                                <h3 class="app-name">${node.node}</h3>
                                <span class="status-badge ${node.status === 'online' ? 'running' : 'stopped'}">
                                    <span class="status-dot"></span>
                                    ${node.status}
                                </span>
                            </div>
                        </div>

                        <!-- Resource Usage -->
                        <div class="app-connection-info">
                            <div class="connection-item">
                                <i data-lucide="cpu" class="connection-icon"></i>
                                <span class="connection-value">${node.maxcpu || 0} vCPU (${node.maxcpu > 0 ? Math.round((node.cpu / node.maxcpu) * 100) : 0}% used)</span>
                            </div>
                            <div class="connection-item">
                                <i data-lucide="memory-stick" class="connection-icon"></i>
                                <span class="connection-value">${formatBytes(node.mem || 0)} / ${formatBytes(node.maxmem || 0)} RAM</span>
                            </div>
                            <div class="connection-item">
                                <i data-lucide="hard-drive" class="connection-icon"></i>
                                <span class="connection-value">${formatBytes(node.disk || 0)} / ${formatBytes(node.maxdisk || 0)} Disk</span>
                            </div>
                            <div class="connection-item">
                                <i data-lucide="activity" class="connection-icon"></i>
                                <span class="connection-value">Uptime: ${node.uptime ? formatUptime(node.uptime) : 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    view.innerHTML = content;

    // Initialize icons
    initLucideIcons();
}

function renderMonitoringView() {
    const view = document.getElementById('monitoringView');

    // Calculate statistics for Applications Summary
    const totalApps = state.deployedApps.length;

    const content = `
        <!-- Node-by-Node Breakdown -->
        ${state.nodes.length > 0 ? `
        <div class="monitor-section">
            <h2 class="monitor-section-title">
                <i data-lucide="server"></i>
                Node Resource Breakdown
            </h2>
            ${state.nodes.map(node => {
                const nodeCpuPercent = node.maxcpu > 0 ? Math.round((node.cpu / node.maxcpu) * 100) : 0;
                const nodeRamPercent = node.maxmem > 0 ? Math.round((node.mem / node.maxmem) * 100) : 0;
                const nodeDiskPercent = node.maxdisk > 0 ? Math.round((node.disk / node.maxdisk) * 100) : 0;

                return `
                <div class="node-monitor-card">
                    <div class="node-monitor-header">
                        <div class="node-monitor-title">
                            <i data-lucide="server"></i>
                            <h3>${node.node}</h3>
                            <span class="status-badge ${node.status === 'online' ? 'running' : 'stopped'}">
                                <span class="status-dot"></span>
                                ${node.status}
                            </span>
                        </div>
                    </div>

                    <div class="node-monitor-resources">
                        <!-- CPU -->
                        <div class="node-resource">
                            <div class="node-resource-header">
                                <span class="node-resource-label">
                                    <i data-lucide="cpu"></i>
                                    CPU
                                </span>
                                <span class="node-resource-value">${nodeCpuPercent}%</span>
                            </div>
                            <div class="monitor-bar-container">
                                <div class="monitor-bar small">
                                    <div class="monitor-bar-fill ${nodeCpuPercent >= 80 ? 'critical' : nodeCpuPercent >= 60 ? 'warning' : 'normal'}"
                                         style="width: ${nodeCpuPercent}%"></div>
                                </div>
                            </div>
                            <div class="node-resource-details">
                                ${node.cpu?.toFixed(2) || 0} / ${node.maxcpu || 0} cores
                            </div>
                        </div>

                        <!-- RAM -->
                        <div class="node-resource">
                            <div class="node-resource-header">
                                <span class="node-resource-label">
                                    <i data-lucide="memory-stick"></i>
                                    RAM
                                </span>
                                <span class="node-resource-value">${nodeRamPercent}%</span>
                            </div>
                            <div class="monitor-bar-container">
                                <div class="monitor-bar small">
                                    <div class="monitor-bar-fill ${nodeRamPercent >= 80 ? 'critical' : nodeRamPercent >= 60 ? 'warning' : 'normal'}"
                                         style="width: ${nodeRamPercent}%"></div>
                                </div>
                            </div>
                            <div class="node-resource-details">
                                ${formatBytes(node.mem || 0)} / ${formatBytes(node.maxmem || 0)}
                            </div>
                        </div>

                        <!-- Disk -->
                        <div class="node-resource">
                            <div class="node-resource-header">
                                <span class="node-resource-label">
                                    <i data-lucide="hard-drive"></i>
                                    Storage
                                </span>
                                <span class="node-resource-value">${nodeDiskPercent}%</span>
                            </div>
                            <div class="monitor-bar-container">
                                <div class="monitor-bar small">
                                    <div class="monitor-bar-fill ${nodeDiskPercent >= 80 ? 'critical' : nodeDiskPercent >= 60 ? 'warning' : 'normal'}"
                                         style="width: ${nodeDiskPercent}%"></div>
                                </div>
                            </div>
                            <div class="node-resource-details">
                                ${formatBytes(node.disk || 0)} / ${formatBytes(node.maxdisk || 0)}
                            </div>
                        </div>
                    </div>
                </div>
                `;
            }).join('')}
        </div>
        ` : ''}

        <!-- Applications Summary Table -->
        ${totalApps > 0 ? `
        <div class="monitor-section">
            <h2 class="monitor-section-title">
                <i data-lucide="package"></i>
                Application Resources
            </h2>
            <div class="monitor-table-container">
                <table class="monitor-table">
                    <thead>
                        <tr>
                            <th>Application</th>
                            <th>Status</th>
                            <th>Node</th>
                            <th>CPU</th>
                            <th>RAM</th>
                            <th>Disk</th>
                            <th>IP Address</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${state.deployedApps.map(app => `
                            <tr>
                                <td>
                                    <div class="table-app-name">
                                        <span class="table-app-icon">${app.icon || '📦'}</span>
                                        <strong>${app.name || app.hostname}</strong>
                                    </div>
                                </td>
                                <td>
                                    <span class="status-badge ${app.status === 'running' ? 'running' : 'stopped'}">
                                        <span class="status-dot"></span>
                                        ${app.status || 'unknown'}
                                    </span>
                                </td>
                                <td><code>${app.node || 'N/A'}</code></td>
                                <td>${app.cores || app.cpu || 'N/A'}</td>
                                <td>${app.memory ? (app.memory + ' MB') : 'N/A'}</td>
                                <td>${app.disk || 'N/A'} GB</td>
                                <td><code>${app.ip || 'N/A'}</code></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
        ` : `
        <div class="empty-state">
            <div class="empty-icon">
                <i data-lucide="activity" style="width: 48px; height: 48px;"></i>
            </div>
            <h3 class="empty-title">No applications to monitor</h3>
            <p class="empty-message">Deploy applications to see monitoring data here.</p>
            <button class="btn btn-primary" onclick="showView('catalog')">Browse Catalog</button>
        </div>
        `}
    `;

    view.innerHTML = content;

    // Initialize icons
    initLucideIcons();
}

async function renderSettingsView() {
    const view = document.getElementById('settingsView');
    view.classList.remove('has-sub-nav'); // Remove old sub-nav class

    // Load settings data
    showLoading('Loading settings...');
    let proxmoxSettings = { host: '', user: '', password: '', port: 8006, verify_ssl: false };
    let networkSettings = { lan_subnet: '10.20.0.0/24', lan_gateway: '10.20.0.1', dhcp_start: '10.20.0.100', dhcp_end: '10.20.0.250', dns_domain: 'prox.local' };
    let resourceSettings = { lxc_memory: 2048, lxc_cores: 2, lxc_disk: 8, lxc_storage: 'local-lvm' };

    try {
        const token = Auth.getToken();
        if (token) {
            // Load Proxmox settings
            try {
                const proxmoxRes = await authFetch(`${API_BASE}/settings/proxmox`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (proxmoxRes.ok) {
                    proxmoxSettings = await proxmoxRes.json();
                } else {
                    console.warn('Failed to load Proxmox settings:', proxmoxRes.status);
                }
            } catch (err) {
                console.warn('Error loading Proxmox settings:', err);
            }

            // Load Network settings
            try {
                const networkRes = await authFetch(`${API_BASE}/settings/network`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (networkRes.ok) {
                    networkSettings = await networkRes.json();
                } else {
                    console.warn('Failed to load Network settings:', networkRes.status);
                }
            } catch (err) {
                console.warn('Error loading Network settings:', err);
            }

            // Load Resource settings
            try {
                const resourceRes = await authFetch(`${API_BASE}/settings/resources`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (resourceRes.ok) {
                    resourceSettings = await resourceRes.json();
                } else {
                    console.warn('Failed to load Resource settings:', resourceRes.status);
                }
            } catch (err) {
                console.warn('Error loading Resource settings:', err);
            }
        } else {
            console.warn('No auth token found, using default settings');
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    } finally {
        hideLoading();
    }

    const content = `
        <div class="settings-content">
            <!-- Proxmox Settings -->
            <div class="settings-panel active" id="proxmox-panel">
                <div class="app-card">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="server"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Proxmox Connection</h3>
                            <p>Configure connection to your Proxmox VE server</p>
                        </div>
                    </div>

                    <form id="proxmoxForm" class="settings-form">
                        <div class="form-group">
                            <label class="form-label">Host</label>
                            <input type="text" class="form-input" name="host" value="${proxmoxSettings.host || ''}" placeholder="192.168.1.100" required>
                            <small class="form-help">IP address or hostname of your Proxmox server</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Port</label>
                            <input type="number" class="form-input" name="port" value="${proxmoxSettings.port || 8006}" required>
                            <small class="form-help">Proxmox web interface port (default: 8006)</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Username</label>
                            <input type="text" class="form-input" name="user" value="${proxmoxSettings.user || ''}" placeholder="root@pam" required>
                            <small class="form-help">Proxmox username (e.g., root@pam)</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input type="password" class="form-input" name="password" value="${proxmoxSettings.password || ''}" placeholder="${proxmoxSettings.password === '******' ? 'Leave unchanged' : 'Enter password'}">
                            <small class="form-help">Password is encrypted before storage. Leave blank to keep current password.</small>
                        </div>

                        <div class="form-group">
                            <label class="form-checkbox">
                                <input type="checkbox" name="verify_ssl" ${proxmoxSettings.verify_ssl ? 'checked' : ''}>
                                <span>Verify SSL Certificate</span>
                            </label>
                            <small class="form-help">Disable for self-signed certificates</small>
                        </div>

                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="testProxmoxConnection()">
                                <i data-lucide="check-circle"></i>
                                <span>Test Connection</span>
                            </button>
                            <button type="submit" class="btn btn-primary">
                                <i data-lucide="save"></i>
                                <span>Save Settings</span>
                            </button>
                        </div>

                        <div id="proxmoxStatus" style="margin-top: 1rem;"></div>
                    </form>
                </div>
            </div>

            <!-- Network Settings -->
            <div class="settings-panel" id="network-panel">
                <div class="app-card">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="network"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Network Configuration</h3>
                            <p>Configure network settings for deployed applications</p>
                        </div>
                    </div>

                    <form id="networkForm" class="settings-form">
                        <div class="form-group">
                            <label class="form-label">LAN Subnet</label>
                            <input type="text" class="form-input" name="lan_subnet" value="${networkSettings.lan_subnet || '10.20.0.0/24'}" required>
                            <small class="form-help">Private network subnet in CIDR notation</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Gateway IP</label>
                            <input type="text" class="form-input" name="lan_gateway" value="${networkSettings.lan_gateway || '10.20.0.1'}" required>
                            <small class="form-help">Network gateway IP address</small>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">DHCP Start</label>
                                <input type="text" class="form-input" name="dhcp_start" value="${networkSettings.dhcp_start || '10.20.0.100'}" required>
                            </div>

                            <div class="form-group">
                                <label class="form-label">DHCP End</label>
                                <input type="text" class="form-input" name="dhcp_end" value="${networkSettings.dhcp_end || '10.20.0.250'}" required>
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label">DNS Domain</label>
                            <input type="text" class="form-input" name="dns_domain" value="${networkSettings.dns_domain || 'prox.local'}" required>
                            <small class="form-help">Local DNS domain suffix (e.g., prox.local)</small>
                        </div>

                        <div class="alert warning" style="margin-bottom: 1.5rem;">
                            <span class="alert-icon">⚠️</span>
                            <div class="alert-content">
                                <div class="alert-message">Network changes only apply to newly deployed apps. Existing apps retain their current configuration.</div>
                            </div>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                <i data-lucide="save"></i>
                                <span>Save Settings</span>
                            </button>
                        </div>

                        <div id="networkStatus" style="margin-top: 1rem;"></div>
                    </form>
                </div>
            </div>

            <!-- Resource Settings -->
            <div class="settings-panel" id="resources-panel">
                <div class="app-card">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="cpu"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Default Resources</h3>
                            <p>Set default resource allocations for new LXC containers</p>
                        </div>
                    </div>

                    <form id="resourcesForm" class="settings-form">
                        <div class="form-group">
                            <label class="form-label">Memory (MB)</label>
                            <input type="number" class="form-input" name="lxc_memory" value="${resourceSettings.lxc_memory || 2048}" min="512" step="512" required>
                            <small class="form-help">Default RAM allocation in megabytes</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">CPU Cores</label>
                            <input type="number" class="form-input" name="lxc_cores" value="${resourceSettings.lxc_cores || 2}" min="1" max="32" required>
                            <small class="form-help">Number of CPU cores to allocate</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Disk Size (GB)</label>
                            <input type="number" class="form-input" name="lxc_disk" value="${resourceSettings.lxc_disk || 8}" min="4" step="1" required>
                            <small class="form-help">Root disk size in gigabytes</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Storage Pool</label>
                            <input type="text" class="form-input" name="lxc_storage" value="${resourceSettings.lxc_storage || 'local-lvm'}" required>
                            <small class="form-help">Proxmox storage pool for container disks</small>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                <i data-lucide="save"></i>
                                <span>Save Settings</span>
                            </button>
                        </div>

                        <div id="resourcesStatus" style="margin-top: 1rem;"></div>
                    </form>
                </div>
            </div>

            <!-- System Settings -->
            <div class="settings-panel" id="system-panel">
                <div class="app-card">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="info"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>System Information</h3>
                            <p>Platform status and configuration details</p>
                        </div>
                    </div>
                    <div class="app-meta">
                        <div class="app-meta-item">
                            <span>📌</span>
                            <span>Version: ${state.systemInfo?.version || 'N/A'}</span>
                        </div>
                        <div class="app-meta-item">
                            <span>🔗</span>
                            <span>API: ${API_BASE}</span>
                        </div>
                    </div>
                    <div class="app-meta" style="margin-top: 1rem;">
                        <div class="app-meta-item">
                            <span>🖥️</span>
                            <span>Nodes: ${state.nodes.length}</span>
                        </div>
                        <div class="app-meta-item">
                            <span>📦</span>
                            <span>Apps: ${state.deployedApps.length}</span>
                        </div>
                    </div>
                </div>

                <!-- Proximity Mode Toggle -->
                <div class="app-card" style="margin-top: 1.5rem;">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="zap"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Proximity Mode</h3>
                            <p>Choose between automated or professional control</p>
                        </div>
                    </div>

                    <div class="mode-toggle">
                        <div class="mode-toggle-label">
                            <h3>Current Mode: <span class="mode-badge ${(state.proximityMode || 'AUTO').toLowerCase()}" id="current-mode-badge">
                                <i data-lucide="${(state.proximityMode || 'AUTO') === 'AUTO' ? 'zap' : 'wrench'}"></i>
                                ${state.proximityMode || 'AUTO'}
                            </span></h3>
                            <p>Switch between AUTO (automated) and PRO (professional control) modes</p>
                        </div>
                        <label class="mode-toggle-switch">
                            <input type="checkbox" id="modeToggleInput" ${(state.proximityMode || 'AUTO') === 'PRO' ? 'checked' : ''} onchange="handleModeToggle(this)">
                            <div class="mode-toggle-slider">${(state.proximityMode || 'AUTO') === 'AUTO' ? 'AUTO' : 'PRO'}</div>
                        </label>
                    </div>

                    <div class="mode-description">
                        <div class="mode-card ${(state.proximityMode || 'AUTO') === 'AUTO' ? 'active' : ''}" id="auto-mode-card">
                            <h4>
                                <i data-lucide="zap" style="width: 16px; height: 16px;"></i>
                                AUTO Mode
                            </h4>
                            <ul>
                                <li>Daily automated backups</li>
                                <li>Automatic update notifications</li>
                                <li>Simplified interface</li>
                                <li>Hands-free operation</li>
                            </ul>
                        </div>
                        <div class="mode-card ${(state.proximityMode || 'AUTO') === 'PRO' ? 'active' : ''}" id="pro-mode-card">
                            <h4>
                                <i data-lucide="wrench" style="width: 16px; height: 16px;"></i>
                                PRO Mode
                            </h4>
                            <ul>
                                <li>Manual backup control</li>
                                <li>Clone applications</li>
                                <li>Edit resource configurations</li>
                                <li>Full professional control</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="app-card" style="margin-top: 1.5rem;">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="shield"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Security</h3>
                            <p>Authentication and access control settings</p>
                        </div>
                    </div>

                    <div class="alert info">
                        <span class="alert-icon">🔐</span>
                        <div class="alert-content">
                            <div class="alert-title">Authentication Enabled</div>
                            <div class="alert-message">All API endpoints are protected with JWT authentication. Sensitive data is encrypted at rest.</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Audio Settings -->
            <div class="settings-panel" id="audio-panel">
                <div class="app-card">
                    <div class="settings-card-header">
                        <div class="settings-card-icon">
                            <i data-lucide="volume-2"></i>
                        </div>
                        <div class="settings-card-title">
                            <h3>Audio Settings</h3>
                            <p>Configure sound effects and volume levels</p>
                        </div>
                    </div>

                    <form id="audioForm" class="settings-form">
                        <!-- Master Volume Control -->
                        <div class="form-group">
                            <label class="form-label">Master Volume</label>
                            <div class="volume-slider-wrapper" style="margin-top: 0.75rem;">
                                <i data-lucide="volume-1" style="width: 18px; height: 18px; color: var(--text-secondary);"></i>
                                <input type="range" min="0" max="100" value="${Math.round((window.SoundService?.getVolume() || 0.7) * 100)}"
                                       class="volume-slider" id="settingsVolumeSlider" style="flex: 1;">
                                <span class="volume-value" id="settingsVolumeValue">${Math.round((window.SoundService?.getVolume() || 0.7) * 100)}%</span>
                            </div>
                            <small class="form-help">Adjust the volume of all sound effects (0-100%)</small>
                        </div>

                        <!-- Mute Toggle -->
                        <div class="form-group">
                            <label class="form-checkbox">
                                <input type="checkbox" id="settingsMuteToggle" ${window.SoundService?.getMute() ? 'checked' : ''}>
                                <span>Mute All Sounds</span>
                            </label>
                            <small class="form-help">Disable all audio feedback throughout the application</small>
                        </div>

                        <!-- Audio Presets -->
                        <div class="form-group">
                            <label class="form-label">Audio Preset</label>
                            <div class="preset-buttons" style="display: flex; gap: 0.75rem; margin-top: 0.75rem;">
                                <button type="button" class="preset-btn ${(window.SoundService?.getPreset() || 'standard') === 'minimal' ? 'active' : ''}"
                                        data-preset="minimal" style="flex: 1;">
                                    <i data-lucide="volume-1" style="width: 16px; height: 16px;"></i>
                                    <span>Minimal</span>
                                    <small style="display: block; margin-top: 0.25rem; font-size: 0.7rem; opacity: 0.7;">30%</small>
                                </button>
                                <button type="button" class="preset-btn ${(window.SoundService?.getPreset() || 'standard') === 'standard' ? 'active' : ''}"
                                        data-preset="standard" style="flex: 1;">
                                    <i data-lucide="volume-2" style="width: 16px; height: 16px;"></i>
                                    <span>Standard</span>
                                    <small style="display: block; margin-top: 0.25rem; font-size: 0.7rem; opacity: 0.7;">70%</small>
                                </button>
                                <button type="button" class="preset-btn ${(window.SoundService?.getPreset() || 'standard') === 'immersive' ? 'active' : ''}"
                                        data-preset="immersive" style="flex: 1;">
                                    <i data-lucide="volume" style="width: 16px; height: 16px;"></i>
                                    <span>Immersive</span>
                                    <small style="display: block; margin-top: 0.25rem; font-size: 0.7rem; opacity: 0.7;">100%</small>
                                </button>
                            </div>
                            <small class="form-help">Quick presets for different listening environments</small>
                        </div>

                        <!-- Test Sound Button -->
                        <div class="form-group">
                            <button type="button" class="btn btn-secondary" id="testSoundBtn" style="width: 100%;">
                                <i data-lucide="play-circle"></i>
                                <span>Test Sound</span>
                            </button>
                            <small class="form-help">Play a test sound to preview current volume settings</small>
                        </div>

                        <div class="alert info" style="margin-top: 1.5rem;">
                            <span class="alert-icon">ℹ️</span>
                            <div class="alert-content">
                                <div class="alert-message">Audio settings are saved automatically and persist across sessions.</div>
                            </div>
                        </div>
                    </form>
                </div>

                <!-- Sound Effects Info -->
                <div class="app-card" style="margin-top: 1.5rem;">
                    <h3 class="app-name" style="margin-bottom: 1.5rem;">Available Sound Effects</h3>
                    <div class="app-meta">
                        <div class="app-meta-item">
                            <span>✅</span>
                            <span>Success notifications</span>
                        </div>
                        <div class="app-meta-item">
                            <span>❌</span>
                            <span>Error alerts</span>
                        </div>
                    </div>
                    <div class="app-meta" style="margin-top: 1rem;">
                        <div class="app-meta-item">
                            <span>🔔</span>
                            <span>General notifications</span>
                        </div>
                        <div class="app-meta-item">
                            <span>👆</span>
                            <span>Click feedback</span>
                        </div>
                    </div>
                    <div class="app-meta" style="margin-top: 1rem;">
                        <div class="app-meta-item">
                            <span>🚀</span>
                            <span>Deployment events</span>
                        </div>
                        <div class="app-meta-item">
                            <span>💥</span>
                            <span>Completion sounds</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    view.innerHTML = content;
    view.classList.add('has-sub-nav');

    // Show the view
    view.classList.remove('hidden');
    view.style.display = 'block';

    // Initialize icons after rendering
    initLucideIcons();

    // Setup tab switching
    setupSettingsTabs();

    // Setup form handlers
    setupSettingsForms();
}

// ============================================
// UI Lab View - Testing Ground for UI Components
// ============================================
async function renderUiLabView() {
    const view = document.getElementById('uilabView');
    
    const content = `
        <div class="sub-nav-bar">
            <div class="sub-nav-items">
                <button class="sub-nav-item active" data-tab="rackcards">
                    <i data-lucide="credit-card"></i>
                    Rack Cards
                    <span class="nav-badge">6</span>
                </button>
                <button class="sub-nav-item" data-tab="components">
                    <i data-lucide="box"></i>
                    Components
                    <span class="nav-badge">12</span>
                </button>
                <button class="sub-nav-item" data-tab="theme">
                    <i data-lucide="palette"></i>
                    Theme System
                </button>
            </div>
        </div>

        <div class="uilab-content">
            <!-- Rack Cards Panel -->
            <div class="uilab-panel active" id="rackcards-panel">
                <div class="page-header">
                    <div class="page-header-content">
                        <h1 class="page-title">
                            <i data-lucide="credit-card"></i>
                            Rack Cards - Horizontal Compact Layout
                        </h1>
                        <p class="page-subtitle">Card compatte in stile rack server per dashboard e liste applicazioni</p>
                    </div>
                </div>

                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="server"></i>
                        Server & Application States
                    </h2>
                    <p class="section-description">Esempi di rack cards con diversi stati operativi</p>
                </div>

                <div class="rack-cards-grid">
                    <!-- Rack Card 1: Server Status -->
                    <div class="rack-card">
                        <div class="rack-card-indicator running"></div>
                        <div class="rack-card-icon">
                            <i data-lucide="server"></i>
                        </div>
                        <div class="rack-card-content">
                            <div class="rack-card-header">
                                <h3 class="rack-card-title">ProxmoxVE-01</h3>
                                <span class="rack-card-badge success">Online</span>
                            </div>
                            <div class="rack-card-meta">
                                <span class="meta-item">
                                    <i data-lucide="cpu"></i>
                                    <span>16 Cores</span>
                                </span>
                                <span class="meta-item">
                                    <i data-lucide="memory-stick"></i>
                                    <span>64 GB RAM</span>
                                </span>
                                <span class="meta-item">
                                    <i data-lucide="hard-drive"></i>
                                    <span>2 TB SSD</span>
                                </span>
                            </div>
                        </div>
                        <div class="rack-card-actions">
                            <button class="action-btn" title="Monitoring">
                                <i data-lucide="activity"></i>
                            </button>
                            <button class="action-btn" title="Console">
                                <i data-lucide="terminal"></i>
                            </button>
                            <button class="action-btn" title="Settings">
                                <i data-lucide="settings"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Rack Card 2: Application -->
                    <div class="rack-card">
                        <div class="rack-card-indicator stopped"></div>
                        <div class="rack-card-icon">
                            <i data-lucide="package"></i>
                        </div>
                        <div class="rack-card-content">
                            <div class="rack-card-header">
                                <h3 class="rack-card-title">PostgreSQL Database</h3>
                                <span class="rack-card-badge stopped">Stopped</span>
                            </div>
                            <div class="rack-card-meta">
                                <span class="meta-item">
                                    <i data-lucide="container"></i>
                                    <span>LXC-105</span>
                                </span>
                                <span class="meta-item">
                                    <i data-lucide="network"></i>
                                    <span>10.20.0.105</span>
                                </span>
                                <span class="meta-item">
                                    <i data-lucide="clock"></i>
                                    <span>2h ago</span>
                                </span>
                            </div>
                        </div>
                        <div class="rack-card-actions">
                            <button class="action-btn success" title="Start">
                                <i data-lucide="play"></i>
                            </button>
                            <button class="action-btn" title="Logs">
                                <i data-lucide="file-text"></i>
                            </button>
                            <button class="action-btn danger" title="Delete">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Rack Card 3: Deployment -->
                    <div class="rack-card">
                        <div class="rack-card-indicator deploying"></div>
                        <div class="rack-card-icon">
                            <i data-lucide="rocket"></i>
                        </div>
                        <div class="rack-card-content">
                            <div class="rack-card-header">
                                <h3 class="rack-card-title">Nextcloud Instance</h3>
                                <span class="rack-card-badge deploying">Deploying</span>
                            </div>
                            <div class="rack-card-meta">
                                <span class="meta-item">
                                    <i data-lucide="loader"></i>
                                    <span>Installing packages...</span>
                                </span>
                            </div>
                            <div class="rack-card-progress">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: 65%;"></div>
                                </div>
                                <span class="progress-text">65%</span>
                            </div>
                        </div>
                        <div class="rack-card-actions">
                            <button class="action-btn" title="View Logs" disabled>
                                <i data-lucide="file-text"></i>
                            </button>
                            <button class="action-btn danger" title="Cancel">
                                <i data-lucide="x"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Rack Card 4: Warning State -->
                    <div class="rack-card warning">
                        <div class="rack-card-indicator warning"></div>
                        <div class="rack-card-icon">
                            <i data-lucide="alert-triangle"></i>
                        </div>
                        <div class="rack-card-content">
                            <div class="rack-card-header">
                                <h3 class="rack-card-title">MySQL Server</h3>
                                <span class="rack-card-badge warning">High CPU</span>
                            </div>
                            <div class="rack-card-meta">
                                <span class="meta-item warning">
                                    <i data-lucide="cpu"></i>
                                    <span>CPU: 95%</span>
                                </span>
                                <span class="meta-item">
                                    <i data-lucide="memory-stick"></i>
                                    <span>RAM: 4.2/8 GB</span>
                                </span>
                                <span class="meta-item warning">
                                    <i data-lucide="thermometer"></i>
                                    <span>Temp: 82°C</span>
                                </span>
                            </div>
                        </div>
                        <div class="rack-card-actions">
                            <button class="action-btn warning" title="Restart">
                                <i data-lucide="refresh-cw"></i>
                            </button>
                            <button class="action-btn" title="Monitoring">
                                <i data-lucide="bar-chart"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Rack Card 5: Success State -->
                    <div class="rack-card success">
                        <div class="rack-card-indicator running"></div>
                        <div class="rack-card-icon">
                            <i data-lucide="check-circle"></i>
                        </div>
                        <div class="rack-card-content">
                            <div class="rack-card-header">
                                <h3 class="rack-card-title">Backup Completed</h3>
                                <span class="rack-card-badge success">Healthy</span>
                            </div>
                            <div class="rack-card-meta">
                                <span class="meta-item">
                                    <i data-lucide="database"></i>
                                    <span>Size: 2.4 GB</span>
                                </span>
                                <span class="meta-item">
                                    <i data-lucide="calendar"></i>
                                    <span>Today 03:00</span>
                                </span>
                                <span class="meta-item success">
                                    <i data-lucide="check"></i>
                                    <span>Verified</span>
                                </span>
                            </div>
                        </div>
                        <div class="rack-card-actions">
                            <button class="action-btn" title="Restore">
                                <i data-lucide="upload"></i>
                            </button>
                            <button class="action-btn" title="Download">
                                <i data-lucide="download"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Rack Card 6: Error State -->
                    <div class="rack-card error">
                        <div class="rack-card-indicator stopped"></div>
                        <div class="rack-card-icon">
                            <i data-lucide="x-circle"></i>
                        </div>
                        <div class="rack-card-content">
                            <div class="rack-card-header">
                                <h3 class="rack-card-title">Redis Cache</h3>
                                <span class="rack-card-badge danger">Connection Failed</span>
                            </div>
                            <div class="rack-card-meta">
                                <span class="meta-item danger">
                                    <i data-lucide="wifi-off"></i>
                                    <span>Network unreachable</span>
                                </span>
                                <span class="meta-item">
                                    <i data-lucide="clock"></i>
                                    <span>Failed 5m ago</span>
                                </span>
                            </div>
                        </div>
                        <div class="rack-card-actions">
                            <button class="action-btn warning" title="Retry">
                                <i data-lucide="rotate-cw"></i>
                            </button>
                            <button class="action-btn" title="Logs">
                                <i data-lucide="file-text"></i>
                            </button>
                            <button class="action-btn danger" title="Delete">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Components Panel -->
            <div class="uilab-panel" id="components-panel">
                <div class="page-header">
                    <div class="page-header-content">
                        <h1 class="page-title">
                            <i data-lucide="box"></i>
                            UI Components Library
                        </h1>
                        <p class="page-subtitle">Libreria completa dei componenti UI utilizzati in Proximity</p>
                    </div>
                </div>

                <!-- Buttons Section -->
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="mouse-pointer"></i>
                        Buttons
                    </h2>
                    <p class="section-description">Stili dei pulsanti con varianti e stati</p>
                </div>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 3rem;">
                    <button class="btn btn-primary">
                        <i data-lucide="check"></i>
                        <span>Primary Button</span>
                    </button>
                    <button class="btn btn-secondary">
                        <i data-lucide="settings"></i>
                        <span>Secondary</span>
                    </button>
                    <button class="btn btn-success">
                        <i data-lucide="play"></i>
                        <span>Success</span>
                    </button>
                    <button class="btn btn-danger">
                        <i data-lucide="trash-2"></i>
                        <span>Danger</span>
                    </button>
                    <button class="btn btn-primary" disabled>
                        <span>Disabled</span>
                    </button>
                </div>

                <!-- Alerts Section -->
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="bell"></i>
                        Alerts & Notifications
                    </h2>
                    <p class="section-description">Alert box per messaggi informativi, warning e errori</p>
                </div>
                <div style="display: flex; flex-direction: column; gap: 1rem; margin-bottom: 3rem;">
                    <div class="alert info">
                        <span class="alert-icon">ℹ️</span>
                        <div class="alert-content">
                            <div class="alert-title">Info Alert</div>
                            <div class="alert-message">Questo è un messaggio informativo con titolo e descrizione dettagliata.</div>
                        </div>
                    </div>
                    <div class="alert success">
                        <span class="alert-icon">✓</span>
                        <div class="alert-content">
                            <div class="alert-title">Success Alert</div>
                            <div class="alert-message">Operazione completata con successo!</div>
                        </div>
                    </div>
                    <div class="alert warning">
                        <span class="alert-icon">⚠️</span>
                        <div class="alert-content">
                            <div class="alert-title">Warning Alert</div>
                            <div class="alert-message">Attenzione: questa azione richiede conferma.</div>
                        </div>
                    </div>
                    <div class="alert error">
                        <span class="alert-icon">✕</span>
                        <div class="alert-content">
                            <div class="alert-title">Error Alert</div>
                            <div class="alert-message">Si è verificato un errore durante l'operazione.</div>
                        </div>
                    </div>
                </div>

                <!-- Badges Section -->
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="tag"></i>
                        Badges & Labels
                    </h2>
                    <p class="section-description">Badge per status e categorizzazione</p>
                </div>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; margin-bottom: 3rem;">
                    <span class="nav-badge">24</span>
                    <span class="nav-badge dev-badge">DEV</span>
                    <span class="rack-card-badge success">Running</span>
                    <span class="rack-card-badge stopped">Stopped</span>
                    <span class="rack-card-badge deploying">Deploying</span>
                    <span class="rack-card-badge warning">Warning</span>
                    <span class="rack-card-badge danger">Error</span>
                </div>

                <!-- Form Elements Section -->
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="file-text"></i>
                        Form Elements
                    </h2>
                    <p class="section-description">Input fields con validazione e stati</p>
                </div>
                <div style="max-width: 600px; margin-bottom: 3rem;">
                    <div class="form-group">
                        <label class="form-label">Text Input <span class="required">*</span></label>
                        <input type="text" class="form-input" placeholder="Enter text here" value="Sample value">
                        <p class="form-help">Helper text for this input field</p>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Select Dropdown</label>
                        <select class="form-input">
                            <option>Option 1</option>
                            <option selected>Option 2</option>
                            <option>Option 3</option>
                        </select>
                    </div>
                    <div class="form-group success">
                        <label class="form-label">Valid Input</label>
                        <input type="text" class="form-input valid" value="192.168.1.1">
                        <p class="form-help success">✓ Valid IP address</p>
                    </div>
                    <div class="form-group error">
                        <label class="form-label">Invalid Input</label>
                        <input type="text" class="form-input invalid" value="invalid-value">
                        <p class="form-help error">✕ This field contains an error</p>
                    </div>
                </div>

                <!-- Loading States Section -->
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="loader"></i>
                        Loading States
                    </h2>
                    <p class="section-description">Spinner e indicatori di caricamento</p>
                </div>
                <div style="display: flex; gap: 2rem; align-items: center; margin-bottom: 3rem;">
                    <div class="loading-spinner"></div>
                    <div style="flex: 1; max-width: 300px;">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 45%;"></div>
                        </div>
                    </div>
                </div>

                <!-- Icons Section -->
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="smile"></i>
                        Icon System
                    </h2>
                    <p class="section-description">Lucide Icons integration</p>
                </div>
                <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 3rem;">
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                        <i data-lucide="server" style="width: 32px; height: 32px; color: var(--primary);"></i>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">server</span>
                    </div>
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                        <i data-lucide="database" style="width: 32px; height: 32px; color: var(--success);"></i>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">database</span>
                    </div>
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                        <i data-lucide="cloud" style="width: 32px; height: 32px; color: #3b82f6;"></i>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">cloud</span>
                    </div>
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                        <i data-lucide="shield" style="width: 32px; height: 32px; color: #f59e0b;"></i>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">shield</span>
                    </div>
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                        <i data-lucide="zap" style="width: 32px; height: 32px; color: var(--secondary);"></i>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">zap</span>
                    </div>
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                        <i data-lucide="terminal" style="width: 32px; height: 32px; color: var(--text-primary);"></i>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">terminal</span>
                    </div>
                </div>
            </div>

            <!-- Theme System Panel -->
            <div class="uilab-panel" id="theme-panel">
                <div class="page-header">
                    <div class="page-header-content">
                        <h1 class="page-title">
                            <i data-lucide="palette"></i>
                            Theme System & Design Tokens
                        </h1>
                        <p class="page-subtitle">Sistema di colori e variabili CSS utilizzate nel tema</p>
                    </div>
                </div>

                <!-- Color Palette Section -->
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="droplet"></i>
                        Color Palette
                    </h2>
                    <p class="section-description">Palette di colori primari e semantici</p>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 3rem;">
                    <div style="padding: 1.5rem; background: var(--primary); border-radius: var(--radius-lg); color: white;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">Primary</div>
                        <div style="font-size: 0.875rem; opacity: 0.9;">--primary</div>
                    </div>
                    <div style="padding: 1.5rem; background: var(--secondary); border-radius: var(--radius-lg); color: white;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">Secondary</div>
                        <div style="font-size: 0.875rem; opacity: 0.9;">--secondary</div>
                    </div>
                    <div style="padding: 1.5rem; background: var(--success); border-radius: var(--radius-lg); color: white;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">Success</div>
                        <div style="font-size: 0.875rem; opacity: 0.9;">--success</div>
                    </div>
                    <div style="padding: 1.5rem; background: var(--danger); border-radius: var(--radius-lg); color: white;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">Danger</div>
                        <div style="font-size: 0.875rem; opacity: 0.9;">--danger</div>
                    </div>
                    <div style="padding: 1.5rem; background: #f59e0b; border-radius: var(--radius-lg); color: white;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">Warning</div>
                        <div style="font-size: 0.875rem; opacity: 0.9;">#f59e0b</div>
                    </div>
                    <div style="padding: 1.5rem; background: #3b82f6; border-radius: var(--radius-lg); color: white;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">Info</div>
                        <div style="font-size: 0.875rem; opacity: 0.9;">#3b82f6</div>
                    </div>
                </div>

                <!-- Background Colors Section -->
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="layers"></i>
                        Background Layers
                    </h2>
                    <p class="section-description">Livelli di background per profondità visiva</p>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 3rem;">
                    <div style="padding: 1.5rem; background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: var(--radius-lg);">
                        <div style="font-weight: 600; margin-bottom: 0.5rem; color: var(--text-primary);">BG Primary</div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">--bg-primary</div>
                    </div>
                    <div style="padding: 1.5rem; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-lg);">
                        <div style="font-weight: 600; margin-bottom: 0.5rem; color: var(--text-primary);">BG Secondary</div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">--bg-secondary</div>
                    </div>
                    <div style="padding: 1.5rem; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--radius-lg);">
                        <div style="font-weight: 600; margin-bottom: 0.5rem; color: var(--text-primary);">BG Tertiary</div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">--bg-tertiary</div>
                    </div>
                    <div style="padding: 1.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: var(--radius-lg);">
                        <div style="font-weight: 600; margin-bottom: 0.5rem; color: var(--text-primary);">Card BG</div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">--card-bg</div>
                    </div>
                </div>

                <!-- Text Colors Section -->
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="type"></i>
                        Text Hierarchy
                    </h2>
                    <p class="section-description">Livelli di testo per gerarchia visiva</p>
                </div>
                <div style="display: flex; flex-direction: column; gap: 1rem; margin-bottom: 3rem;">
                    <div style="padding: 1rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: var(--radius-lg);">
                        <div style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;">Primary Text</div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 0.25rem;">--text-primary (Headings, important content)</div>
                    </div>
                    <div style="padding: 1rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: var(--radius-lg);">
                        <div style="color: var(--text-secondary); font-size: 1rem;">Secondary Text</div>
                        <div style="color: var(--text-tertiary); font-size: 0.875rem; margin-top: 0.25rem;">--text-secondary (Body text, descriptions)</div>
                    </div>
                    <div style="padding: 1rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: var(--radius-lg);">
                        <div style="color: var(--text-tertiary); font-size: 0.875rem;">Tertiary Text</div>
                        <div style="color: var(--text-tertiary); font-size: 0.75rem; margin-top: 0.25rem;">--text-tertiary (Meta info, timestamps)</div>
                    </div>
                </div>

                <!-- Spacing & Radius Section -->
                <div class="section-header">
                    <h2 class="section-title">
                        <i data-lucide="maximize"></i>
                        Spacing & Border Radius
                    </h2>
                    <p class="section-description">Token per spacing e border radius consistenti</p>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 3rem;">
                    <div style="text-align: center;">
                        <div style="width: 100%; height: 80px; background: var(--primary-opacity-10); border-radius: var(--radius-sm); margin-bottom: 0.5rem;"></div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">radius-sm (4px)</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="width: 100%; height: 80px; background: var(--primary-opacity-10); border-radius: var(--radius-md); margin-bottom: 0.5rem;"></div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">radius-md (8px)</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="width: 100%; height: 80px; background: var(--primary-opacity-10); border-radius: var(--radius-lg); margin-bottom: 0.5rem;"></div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">radius-lg (12px)</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="width: 100%; height: 80px; background: var(--primary-opacity-10); border-radius: var(--radius-xl); margin-bottom: 0.5rem;"></div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">radius-xl (16px)</div>
                    </div>
                </div>

                <!-- Info Card -->
                <div class="alert info">
                    <span class="alert-icon">💡</span>
                    <div class="alert-content">
                        <div class="alert-title">Design System Usage</div>
                        <div class="alert-message">Usa sempre le variabili CSS per mantenere la coerenza del design. Le variabili si trovano nel file <code>:root</code> in <code>styles.css</code>.</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    view.innerHTML = content;
    
    // Setup tab switching
    setupUiLabTabs();
    
    // Initialize icons
    initLucideIcons();
}

function setupUiLabTabs() {
    // Fix: sub-nav-bar is outside .uilab-content, so we need a more specific selector
    const tabs = document.querySelectorAll('#uilabView .sub-nav-item');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            
            // Add active to clicked tab
            tab.classList.add('active');
            
            // Hide all panels
            document.querySelectorAll('.uilab-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            
            // Show corresponding panel
            const panelId = `${tab.dataset.tab}-panel`;
            const panel = document.getElementById(panelId);
            if (panel) {
                panel.classList.add('active');
            }
            
            // Reinitialize icons
            initLucideIcons();
        });
    });
}


// Modal Functions
function showDeployModal(catalogId) {
    const app = state.catalog.items.find(a => a.id === catalogId);
    if (!app) return;
    
    const modal = document.getElementById('deployModal');
    document.getElementById('modalTitle').textContent = `Deploy ${app.name}`;
    
    document.getElementById('modalBody').innerHTML = `
        <div class="alert info">
            <span class="alert-icon">ℹ️</span>
            <div class="alert-content">
                <div class="alert-message">${app.description}</div>
            </div>
        </div>
        
        <form id="deployForm" onsubmit="event.preventDefault(); deployApp('${catalogId}');">
            <div class="form-group">
                <label class="form-label">Hostname <span class="required">*</span></label>
                <input type="text" class="form-input" id="hostname" value="${app.id}-01" required>
                <p class="form-help">Unique identifier for this application instance</p>
            </div>
            
            <div class="form-group">
                <label class="form-label">Target Node</label>
                <select class="form-input" id="targetNode">
                    <option value="">Auto-select (recommended)</option>
                    ${state.nodes.map(node => `
                        <option value="${node.node}">${node.node} (${Math.round((node.mem / node.maxmem) * 100)}% used)</option>
                    `).join('')}
                </select>
                <p class="form-help">Leave empty to automatically select the best node</p>
            </div>
            
            <div class="app-meta">
                <div class="app-meta-item">
                    <span>💾</span>
                    <span>${app.min_memory}MB RAM required</span>
                </div>
                <div class="app-meta-item">
                    <span>⚡</span>
                    <span>${app.min_cpu} vCPU required</span>
                </div>
            </div>
        </form>
    `;
    
    const footer = `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="deployApp('${catalogId}')">
            Deploy Application
        </button>
    `;
    
    document.querySelector('.modal-footer')?.remove();
    const footerDiv = document.createElement('div');
    footerDiv.className = 'modal-footer';
    footerDiv.innerHTML = footer;
    document.querySelector('.modal-content').appendChild(footerDiv);
    
    modal.classList.add('show');
    openModal(); // Prevent body scrolling
}

function openModal() {
    // Save current scroll position
    const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
    
    // Add modal-open class and set top position to maintain scroll position visually
    document.body.classList.add('modal-open');
    document.body.style.top = `-${scrollPosition}px`;
    
    // Disable pointer events on main content to prevent interaction with background
    const mainContent = document.querySelector('.app-container');
    if (mainContent) {
        mainContent.style.pointerEvents = 'none';
    }
}

function closeModal() {
    const modal = document.getElementById('deployModal');
    modal.classList.remove('show');
    
    // Only remove modal-open if no other modals are open
    const anyModalOpen = Array.from(document.querySelectorAll('.modal.show')).length > 0;
    if (!anyModalOpen) {
        const scrollPosition = parseInt(document.body.style.top || '0') * -1;
        document.body.classList.remove('modal-open');
        document.body.style.top = '';
        
        // Re-enable pointer events on main content
        const mainContent = document.querySelector('.app-container');
        if (mainContent) {
            mainContent.style.pointerEvents = '';
        }
        
        // Restore scroll position
        window.scrollTo(0, scrollPosition);
    }
}

// App Actions
async function deployApp(catalogId) {
    const hostname = document.getElementById('hostname').value;
    const targetNode = document.getElementById('targetNode')?.value || null;
    
    if (!hostname) {
        showNotification('Please enter a hostname', 'error');
        return;
    }
    
    closeModal();
    
    // Play deploy start sound
    if (window.SoundService) {
        window.SoundService.play('deploy_start');
        
        // Start ambient dub-techno loop after a short delay
        setTimeout(() => {
            window.SoundService.startLoop('deployment_loop', 2.0); // 2s fade in
        }, 500); // Start loop 500ms after deploy_start
    }
    
    try {
        const payload = {
            catalog_id: catalogId,
            hostname: hostname,
            config: {},
            environment: {}
        };
        
        if (targetNode) {
            payload.node = targetNode;
        }
        
        // Show deployment progress modal
        showDeploymentProgress(catalogId, hostname);

        const response = await authFetch(`${API_BASE}/apps/deploy`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Deployment failed');
        }
        
        const result = await response.json();
        
        // Stop deployment loop with fade out, then play explosion
        if (window.SoundService) {
            await window.SoundService.stopLoop(2.0); // 2s fade out
            window.SoundService.play('explosion'); // Satisfying completion impact
        }
        
        hideDeploymentProgress();
        closeModal(); // Close the deployment modal
        showNotification(`Application deployed successfully!`, 'success');
        
        // Wait a moment for proxy vhost to be fully propagated
        // Then reload to get the correct proxy URL instead of direct LXC IP
        console.log('Waiting for proxy vhost propagation...');
        await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
        
        // Reload apps to get updated URLs
        await loadDeployedApps();
        await loadSystemInfo();
        
        // Show deployed app - don't call updateUI() since showView('apps') will render everything fresh
        showView('apps');
        
    } catch (error) {
        // Stop deployment loop immediately on error (no explosion)
        if (window.SoundService) {
            await window.SoundService.stopLoop(1.0); // Quick 1s fade out on error
        }
        
        hideDeploymentProgress();
        closeModal(); // Close the deployment modal on error
        showNotification('Deployment failed: ' + error.message, 'error');
        console.error('Deployment error:', error);
    }
}

// Deployment progress tracking
let deploymentProgressInterval = null;

function showDeploymentProgress(catalogId, hostname) {
    const modal = document.getElementById('deployModal');
    const modalBody = document.getElementById('modalBody');
    const modalTitle = document.getElementById('modalTitle');
    
    modalTitle.textContent = 'Deploying Application';
    
    modalBody.innerHTML = `
        <div style="text-align: center; padding: 2rem 1rem;">
            <div style="margin-bottom: 1.5rem;">
                <div class="loading-spinner" style="display: inline-block; margin-bottom: 1rem;"></div>
                <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">${hostname}</h3>
                <p style="color: var(--text-secondary); font-size: 0.875rem;">Setting up your application</p>
            </div>
            
            <div style="background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 1.5rem; margin-bottom: 1rem;">
                <div id="progressSteps" style="text-align: left;">
                    <div class="progress-step active">
                        <div class="progress-step-icon">🟠</div>
                        <div class="progress-step-text">Creating LXC container</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Starting container</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Installing Docker</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Pulling Docker images</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Starting services</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Finalizing deployment</div>
                    </div>
                </div>
            </div>
            
            <div style="width: 100%; background: var(--bg-tertiary); border-radius: var(--radius-md); height: 8px; overflow: hidden; margin-bottom: 1rem;">
                <div id="progressBar" style="width: 10%; height: 100%; background: linear-gradient(90deg, var(--primary), var(--secondary)); transition: width 0.5s ease;"></div>
            </div>
            
            <div id="progressMessage" style="color: var(--text-tertiary); font-size: 0.875rem; min-height: 1.5rem;">
                Initializing deployment...
            </div>
            
            <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border);">
                <p style="color: var(--text-tertiary); font-size: 0.75rem; margin-bottom: 0.5rem;">
                    This may take 2-5 minutes
                </p>
                <p style="color: var(--text-tertiary); font-size: 0.75rem;">
                    Docker images are being downloaded and configured
                </p>
            </div>
        </div>
    `;
    
    // Remove footer since deployment is already in progress (no cancel/deploy buttons needed)
    document.querySelector('.modal-footer')?.remove();
    
    modal.classList.add('show');
    modal.style.pointerEvents = 'none'; // Prevent closing during deployment
    openModal(); // Prevent body scrolling
    
    // Start polling for real deployment status
    pollDeploymentStatus(`${catalogId}-${hostname}`);
}

async function pollDeploymentStatus(appId) {
    let pollAttempts = 0;
    const maxAttempts = 120; // 120 attempts * 2 seconds = 4 minutes max
    let lastKnownProgress = 10; // Start at 10% (initial state)
    
    deploymentProgressInterval = setInterval(async () => {
        pollAttempts++;
        
        try {
            const response = await authFetch(`${API_BASE}/apps/deploy/${appId}/status`);
            
            if (response.ok) {
                const status = await response.json();
                console.log('✓ Deployment status received:', status);
                
                // Update UI with real status
                updateDeploymentProgressFromStatus(status);
                lastKnownProgress = status.progress || lastKnownProgress;
                
                // Check if deployment is complete or failed
                if (status.status === 'running' || status.status === 'error') {
                    clearInterval(deploymentProgressInterval);
                    deploymentProgressInterval = null;
                    console.log('✓ Deployment complete or failed, stopping polling');
                    
                    // Don't hide modal automatically - let deployApp() handle it
                }
            } else if (response.status === 404) {
                // Deployment status not found yet, use simulated progress
                console.log('⚠️ Deployment status not available yet, using simulated progress');
                
                // Simulate progress advancement (slower as we get closer to 90%)
                if (lastKnownProgress < 90) {
                    lastKnownProgress += Math.random() * 2 + 1; // Increase by 1-3%
                    
                    // Update simulated progress
                    const simulatedStep = getStepFromProgress(lastKnownProgress);
                    updateDeploymentProgressFromStatus({
                        progress: Math.min(lastKnownProgress, 90),
                        current_step: simulatedStep,
                        message: simulatedStep
                    });
                }
            }
            
        } catch (error) {
            console.error('Error polling deployment status:', error);
            
            // Even on error, advance simulated progress slightly
            if (lastKnownProgress < 85) {
                lastKnownProgress += 1;
            }
        }
        
        // Stop polling after max attempts
        if (pollAttempts >= maxAttempts) {
            clearInterval(deploymentProgressInterval);
            deploymentProgressInterval = null;
            console.warn('⚠️ Deployment polling timeout reached');
        }
    }, 2000); // Poll every 2 seconds
}

// Helper function to determine step based on progress percentage
function getStepFromProgress(progress) {
    if (progress < 20) return 'Creating LXC container';
    if (progress < 35) return 'Starting container';
    if (progress < 50) return 'Installing Docker';
    if (progress < 70) return 'Pulling Docker images';
    if (progress < 85) return 'Starting services';
    return 'Finalizing deployment';
}

function updateDeploymentProgressFromStatus(status) {
    console.log('📊 Updating deployment progress:', status);
    
    const progressBar = document.getElementById('progressBar');
    const progressMessage = document.getElementById('progressMessage');
    
    if (progressBar) {
        const progress = status.progress || 0;
        progressBar.style.width = `${progress}%`;
        console.log(`Progress bar: ${progress}%`);
    }
    
    if (progressMessage) {
        const message = status.current_step || status.message || 'Processing...';
        progressMessage.textContent = message;
        console.log(`Progress message: ${message}`);
    }
    
    // Update step indicators based on current_step
    const progressSteps = document.getElementById('progressSteps');
    if (progressSteps && (status.current_step || status.message)) {
        updateProgressSteps(status.current_step || status.message);
    }
}

function updateProgressSteps(currentStepText) {
    const progressSteps = document.getElementById('progressSteps');
    if (!progressSteps) {
        console.warn('Progress steps container not found');
        return;
    }
    
    console.log('📊 Updating progress steps with:', currentStepText);
    
    // Map status text to step names
    const stepMap = {
        'Creating container': 'creating',
        'Reserving container ID': 'creating',
        'Creating LXC': 'creating',
        'Starting container': 'starting',
        'Container started': 'starting',
        'Setting up Docker': 'docker',
        'Installing Docker': 'docker',
        'Docker installed': 'docker',
        'Pulling Docker images': 'images',
        'Pulling images': 'images',
        'Images pulled': 'images',
        'Setting up application': 'services',
        'Starting application': 'services',
        'Configuring reverse proxy': 'services',
        'Application started': 'services',
        'Finalizing deployment': 'finalizing',
        'Deployment complete': 'finalizing',
        'Complete': 'finalizing'
    };
    
    // Find which step we're on
    let currentStep = 'creating';
    for (const [text, step] of Object.entries(stepMap)) {
        if (currentStepText.toLowerCase().includes(text.toLowerCase())) {
            currentStep = step;
            console.log(`✓ Matched step: ${text} -> ${step}`);
            break;
        }
    }
    
    const allSteps = ['creating', 'starting', 'docker', 'images', 'services', 'finalizing'];
    const stepMessages = {
        creating: 'Creating LXC container',
        starting: 'Starting container',
        docker: 'Installing Docker',
        images: 'Pulling Docker images',
        services: 'Starting services',
        finalizing: 'Finalizing deployment'
    };
    
    const currentStepIndex = allSteps.indexOf(currentStep);
    console.log(`Current step index: ${currentStepIndex} (${currentStep})`);
    
    // Update the steps display with colored circles
    progressSteps.innerHTML = allSteps.map((step, index) => {
        const isDone = index < currentStepIndex;
        const isCurrent = step === currentStep;
        // Use colored circles: green (done), orange (current), gray (pending)
        const icon = isDone ? '🟢' : (isCurrent ? '🟠' : '⚪');
        const stepClass = isDone ? 'completed' : (isCurrent ? 'active' : '');
        
        return `
            <div class="progress-step ${stepClass}">
                <div class="progress-step-icon">${icon}</div>
                <div class="progress-step-text">${stepMessages[step]}</div>
            </div>
        `;
    }).join('');
}

function hideDeploymentProgress() {
    const modal = document.getElementById('deployModal');
    modal.classList.remove('show');
    modal.style.pointerEvents = 'auto';
    
    if (deploymentProgressInterval) {
        clearInterval(deploymentProgressInterval);
        deploymentProgressInterval = null;
    }
    
    // Properly clean up modal state to re-enable page interaction
    const anyModalOpen = Array.from(document.querySelectorAll('.modal.show')).length > 0;
    if (!anyModalOpen) {
        const scrollPosition = parseInt(document.body.style.top || '0') * -1;
        document.body.classList.remove('modal-open');
        document.body.style.top = '';
        
        // Re-enable pointer events on main content
        const mainContent = document.querySelector('.app-container');
        if (mainContent) {
            mainContent.style.pointerEvents = '';
        }
        
        // Restore scroll position
        window.scrollTo(0, scrollPosition);
    }
}

async function controlApp(appId, action) {
    showLoading(`${action}ing application...`);
    
    try {
        const response = await authFetch(`${API_BASE}/apps/${appId}/actions`, {
            method: 'POST',
            // Don't override headers - authFetch adds Authorization automatically
            body: JSON.stringify({ action: action })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Failed to ${action} app`);
        }
        
        hideLoading();
        showNotification(`Application ${action}ed successfully`, 'success');
        
        // Reload apps
        await loadDeployedApps();
        updateUI();
        
    } catch (error) {
        hideLoading();
        showNotification(`Failed to ${action} app: ` + error.message, 'error');
        console.error('Control error:', error);
    }
}

function showAppDetails(appId) {
    const app = state.deployedApps.find(a => a.id === appId);
    if (!app) return;
    
    // TODO: Implement detailed app view
    showNotification('App details view coming soon', 'info');
}

function confirmDeleteApp(appId, appName) {
    const modal = document.getElementById('deployModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Delete Application';
    modalBody.innerHTML = `
        <div style="padding: 1.5rem; text-align: center;">
            <div style="width: 64px; height: 64px; margin: 0 auto 1rem; border-radius: 50%; background: rgba(239, 68, 68, 0.1); display: flex; align-items: center; justify-content: center;">
                <div style="width: 40px; height: 40px; border-radius: 50%; background: #ef4444;"></div>
            </div>
            <h3 style="color: var(--text-primary); margin-bottom: 1rem;">${appName}</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6;">
                Are you sure you want to delete this application?
            </p>
            
            <div style="background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 1rem; margin-bottom: 1.5rem; text-align: left;">
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #f59e0b;"></span>
                    This action will:
                </p>
                <ul style="color: var(--text-secondary); font-size: 0.875rem; margin: 0; padding-left: 1.5rem; line-height: 1.8;">
                    <li>Stop the application</li>
                    <li>Delete the LXC container</li>
                    <li>Remove all data permanently</li>
                    <li>Remove from reverse proxy</li>
                </ul>
                <p style="color: #ef4444; font-size: 0.875rem; margin-top: 0.75rem; font-weight: 600; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #ef4444;"></span>
                    This action cannot be undone!
                </p>
            </div>
            
            <div style="display: flex; gap: 0.75rem; justify-content: center;">
                <button class="btn btn-ghost" onclick="closeModal()" style="min-width: 120px;">Cancel</button>
                <button class="btn btn-primary" onclick="deleteApp('${appId}', '${appName}')" style="min-width: 120px; background: #ef4444; border-color: #ef4444;">
                    Delete Forever
                </button>
            </div>
        </div>
    `;
    
    // Remove any existing modal footer since we have inline buttons
    document.querySelector('.modal-footer')?.remove();
    
    modal.classList.add('show');
    openModal(); // Prevent body scrolling
}

async function deleteApp(appId, appName) {
    showDeletionProgress(appName);
    
    try {
        // Simulate progress steps
        await updateDeletionProgress(0, 'Stopping application...');
        await new Promise(resolve => setTimeout(resolve, 800));
        
        await updateDeletionProgress(33, 'Removing from reverse proxy...');
        await new Promise(resolve => setTimeout(resolve, 800));
        
        await updateDeletionProgress(66, 'Deleting LXC container...');
        
        const response = await authFetch(`${API_BASE}/apps/${appId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete app');
        }
        
        await updateDeletionProgress(100, 'Deletion complete');
        await new Promise(resolve => setTimeout(resolve, 500));
        
        hideDeletionProgress();
        showNotification('Application deleted successfully', 'success');
        
        // Reload apps and update UI
        await loadDeployedApps();
        await loadSystemInfo();
        
        // If we're on the apps view, refresh it (don't call updateUI() to avoid double-rendering)
        if (state.currentView === 'apps') {
            showView('apps');
        } else {
            // Only update UI if we're not on apps view (e.g., on dashboard)
            updateUI();
        }
        
    } catch (error) {
        hideDeletionProgress();
        showNotification('Failed to delete app: ' + error.message, 'error');
        console.error('Delete error:', error);
    }
}

function showDeletionProgress(appName) {
    const modal = document.getElementById('deployModal');
    const modalBody = document.getElementById('modalBody');
    const modalTitle = document.getElementById('modalTitle');
    
    modalTitle.textContent = 'Deleting Application';
    
    modalBody.innerHTML = `
        <div style="text-align: center; padding: 2rem 1rem;">
            <div style="margin-bottom: 1.5rem;">
                <div class="loading-spinner" style="display: inline-block; margin-bottom: 1rem;"></div>
                <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">${appName}</h3>
                <p style="color: var(--text-secondary); font-size: 0.875rem;">Removing application...</p>
            </div>
            
            <div style="background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 1.5rem; margin-bottom: 1rem;">
                <div id="deletionProgressSteps" style="text-align: left;">
                    <div class="progress-step active">
                        <div class="progress-step-icon">🟠</div>
                        <div class="progress-step-text">Stopping application</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Removing from proxy</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Deleting container</div>
                    </div>
                </div>
                
                <div style="margin-top: 1rem;">
                    <div style="background: var(--bg-tertiary); border-radius: 999px; height: 6px; overflow: hidden;">
                        <div id="deletionProgressBar" style="height: 100%; background: linear-gradient(90deg, #ef4444, #dc2626); transition: width 0.3s ease; width: 0%;"></div>
                    </div>
                </div>
            </div>
            
            <div id="deletionProgressMessage" style="color: var(--text-tertiary); font-size: 0.875rem; min-height: 1.5rem;">
                Initializing deletion...
            </div>
            
            <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border);">
                <p style="color: var(--text-tertiary); font-size: 0.75rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #f59e0b;"></span>
                    Please wait while the application is removed
                </p>
            </div>
        </div>
    `;
    
    modal.classList.add('show');
    modal.style.pointerEvents = 'none';
    openModal(); // Prevent body scrolling
}

async function updateDeletionProgress(progress, message) {
    const progressBar = document.getElementById('deletionProgressBar');
    const progressMessage = document.getElementById('deletionProgressMessage');
    const progressSteps = document.getElementById('deletionProgressSteps');
    
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
    
    if (progressMessage) {
        progressMessage.textContent = message;
    }
    
    if (progressSteps) {
        const steps = progressSteps.querySelectorAll('.progress-step');
        steps.forEach((step, index) => {
            if (progress >= (index * 33)) {
                step.classList.add('active');
                const icon = step.querySelector('.progress-step-icon');
                if (progress > ((index + 1) * 33)) {
                    icon.textContent = '🟢';
                    step.classList.remove('pulse');
                } else if (progress >= (index * 33)) {
                    icon.textContent = '🟠';
                    step.classList.add('pulse');
                }
            }
        });
    }
}

function hideDeletionProgress() {
    const modal = document.getElementById('deployModal');
    modal.classList.remove('show');
    modal.style.pointerEvents = 'auto';
    
    // Properly clean up modal state to re-enable page interaction
    const anyModalOpen = Array.from(document.querySelectorAll('.modal.show')).length > 0;
    if (!anyModalOpen) {
        const scrollPosition = parseInt(document.body.style.top || '0') * -1;
        document.body.classList.remove('modal-open');
        document.body.style.top = '';
        
        // Re-enable pointer events on main content
        const mainContent = document.querySelector('.app-container');
        if (mainContent) {
            mainContent.style.pointerEvents = '';
        }
        
        // Restore scroll position
        window.scrollTo(0, scrollPosition);
    }
}

// Utility Functions
function getAppIcon(name) {
    // Comprehensive icon mapping with SVG support
    const iconMap = {
        // Popular Apps
        'wordpress': { svg: 'wordpress', emoji: '📝', color: '#21759b' },
        'nextcloud': { svg: 'nextcloud', emoji: '☁️', color: '#0082c9' },
        'portainer': { svg: 'portainer', emoji: '🐳', color: '#13bef9' },
        'nginx': { svg: 'nginx', emoji: '🌐', color: '#009639' },
        'apache': { svg: 'apache', emoji: '🪶', color: '#d22128' },
        
        // Databases
        'mysql': { svg: 'mysql', emoji: '🗄️', color: '#4479a1' },
        'mariadb': { svg: 'mariadb', emoji: '🗄️', color: '#003545' },
        'postgresql': { svg: 'postgresql', emoji: '🐘', color: '#4169e1' },
        'postgres': { svg: 'postgresql', emoji: '🐘', color: '#4169e1' },
        'redis': { svg: 'redis', emoji: '🔴', color: '#dc382d' },
        'mongodb': { svg: 'mongodb', emoji: '🍃', color: '#47a248' },
        
        // Development
        'git': { svg: 'git', emoji: '🔀', color: '#f05032' },
        'gitlab': { svg: 'gitlab', emoji: '🦊', color: '#fc6d26' },
        'github': { svg: 'github', emoji: '🐙', color: '#181717' },
        'jenkins': { svg: 'jenkins', emoji: '👨‍🔧', color: '#d24939' },
        'docker': { svg: 'docker', emoji: '🐳', color: '#2496ed' },
        
        // Monitoring & Analytics
        'grafana': { svg: 'grafana', emoji: '📊', color: '#f46800' },
        'prometheus': { svg: 'prometheus', emoji: '🔥', color: '#e6522c' },
        'elasticsearch': { svg: 'elasticsearch', emoji: '🔍', color: '#005571' },
        'kibana': { svg: 'kibana', emoji: '🔍', color: '#005571' },
        
        // Communication
        'rocketchat': { svg: 'rocketdotchat', emoji: '💬', color: '#f5455c' },
        'mattermost': { svg: 'mattermost', emoji: '💬', color: '#0058cc' },
        'jitsi': { svg: 'jitsi', emoji: '📹', color: '#1d76ba' },
        
        // Media
        'plex': { svg: 'plex', emoji: '🎬', color: '#ebaf00' },
        'jellyfin': { svg: 'jellyfin', emoji: '🎬', color: '#00a4dc' },
        'emby': { svg: null, emoji: '🎬', color: '#52b54b' },
        
        // Productivity
        'bitwarden': { svg: 'bitwarden', emoji: '🔐', color: '#175ddc' },
        'vaultwarden': { svg: 'bitwarden', emoji: '🔐', color: '#175ddc' },
        'bookstack': { svg: 'bookstack', emoji: '📚', color: '#0288d1' },
        'wikijs': { svg: 'wikidotjs', emoji: '📖', color: '#1976d2' },
        
        // File Management
        'syncthing': { svg: 'syncthing', emoji: '🔄', color: '#0891d1' },
        'filebrowser': { svg: null, emoji: '📁', color: '#3f51b5' },
        
        // Security
        'traefik': { svg: 'traefikproxy', emoji: '🔀', color: '#24a1c1' },
        'certbot': { svg: 'letsencrypt', emoji: '🔒', color: '#003a70' },
        'fail2ban': { svg: null, emoji: '🛡️', color: '#d32f2f' },
        
        // CMS & E-commerce
        'drupal': { svg: 'drupal', emoji: '💧', color: '#0678be' },
        'joomla': { svg: 'joomla', emoji: '🌟', color: '#5091cd' },
        'magento': { svg: 'magento', emoji: '🛒', color: '#ee672f' },
        'prestashop': { svg: 'prestashop', emoji: '🛒', color: '#df0067' },
        
        // Others
        'pihole': { svg: 'pihole', emoji: '🕳️', color: '#96060c' },
        'homeassistant': { svg: 'homeassistant', emoji: '🏠', color: '#18bcf2' },
        'node-red': { svg: 'nodered', emoji: '🔴', color: '#8f0000' },
    };
    
    const nameLower = (name || '').toLowerCase();
    
    // Find matching icon
    for (const [key, config] of Object.entries(iconMap)) {
        if (nameLower.includes(key)) {
            return createIconElement(config, name);
        }
    }
    
    // Default fallback
    return createIconElement({ svg: null, emoji: '📦', color: '#6366f1' }, name);
}

function createIconElement(config, appName) {
    // For now, return emoji (SVG implementation can be added later)
    // When implementing SVG: use Simple Icons CDN or local SVG files
    // Example: https://cdn.simpleicons.org/${config.svg}/${config.color.replace('#', '')}
    
    if (config.svg) {
        // Return SVG icon with fallback to emoji
        const escapedEmoji = config.emoji.replace(/'/g, "&#39;").replace(/"/g, "&quot;");
        return `<img 
            src="https://cdn.simpleicons.org/${config.svg}" 
            alt="${appName}" 
            style="width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));"
            onerror="this.style.display='none'; this.insertAdjacentHTML('afterend', '${escapedEmoji}');"
        />`;
    }
    
    // Fallback to emoji
    return config.emoji;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    return date.toLocaleDateString();
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showLoading(text = 'Loading...') {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingOverlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('show');
}

// showNotification is now provided by /js/notifications-global.js
// Supports: showNotification(message, type, duration, title)
// Helper functions: showSuccess(), showError(), showWarning(), showInfo()
// All toast notifications are managed globally with proper animations and icons

/**
 * Initialize hover sound effects using event delegation
 * This approach is more efficient and survives innerHTML updates
 */
let cardHoverSoundsInitialized = false;

function initCardHoverSounds() {
    if (cardHoverSoundsInitialized) return;

    // Use event delegation on document body - works for all cards forever
    const hoveredCards = new WeakSet();

    document.body.addEventListener('mouseenter', async (e) => {
        const card = e.target.closest('.app-card');
        if (!card || hoveredCards.has(card)) return;

        hoveredCards.add(card);

        // Play click sound as a subtle tick
        if (window.SoundService && window.SoundService.play) {
            try {
                await window.SoundService.play('click');
            } catch (err) {
                // Silently fail if sound can't play
                console.debug('Card hover sound failed:', err);
            }
        }
    }, true); // Use capture phase

    document.body.addEventListener('mouseleave', (e) => {
        const card = e.target.closest('.app-card');
        if (card) {
            hoveredCards.delete(card);
        }
    }, true);

    cardHoverSoundsInitialized = true;
    console.log('🎵 Card hover sounds initialized with event delegation');
}

/**
 * @deprecated Use initCardHoverSounds() once at app startup instead
 * Kept for backward compatibility
 */
function attachCardHoverSounds() {
    // No-op: event delegation handles this automatically now
    console.debug('attachCardHoverSounds() called but using event delegation instead');
}

function filterApps(filter) {
    // Update tab active state
    document.querySelectorAll('.sub-nav-item').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Filter apps
    let filtered = state.deployedApps;
    if (filter !== 'all') {
        filtered = state.deployedApps.filter(app => app.status === filter);
    }
    
    const grid = document.getElementById('allAppsGrid');
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
        for (const app of filtered) {
            renderAppCard(app, grid, true);
        }
        // Reinitialize Lucide icons after updating the DOM
        initLucideIcons();
        // Hover sounds handled automatically via event delegation
    }
}

function filterCatalog(category) {
    // Update tab active state
    document.querySelectorAll('.sub-nav-item[data-category]').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Get current search query
    const searchInput = document.getElementById('catalogSearchInput');
    const currentQuery = searchInput ? searchInput.value : '';

    // Apply both filter and search via searchCatalog()
    searchCatalog(currentQuery);
}

// Search functionality for Apps
function searchApps(query) {
    const searchInput = document.getElementById('appsSearchInput');
    const clearBtn = document.getElementById('appsClearSearch');
    const resultsCount = document.getElementById('appsResultsCount');
    const grid = document.getElementById('allAppsGrid');

    // Show/hide clear button
    if (clearBtn) {
        clearBtn.style.display = query ? 'flex' : 'none';
    }

    // Get current filter (all, running, stopped)
    const activeFilter = document.querySelector('.sub-nav-item[data-filter].active');
    const filter = activeFilter ? activeFilter.dataset.filter : 'all';

    // Apply filter first
    let filtered = state.deployedApps;
    if (filter !== 'all') {
        filtered = state.deployedApps.filter(app => app.status === filter);
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
                <button class="btn btn-secondary" onclick="clearAppsSearch()">Clear Search</button>
            </div>
        `;
    } else {
        // Clear grid and render using template cloning
        grid.innerHTML = '';
        for (const app of filtered) {
            renderAppCard(app, grid, true);
        }
    }

    // Reinitialize Lucide icons
    initLucideIcons();
}

function clearAppsSearch() {
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
    searchApps('');
}

/**
 * Search catalog items by name, description, or category
 * Works in combination with category filters
 */
function searchCatalog(query) {
    const clearBtn = document.getElementById('catalogClearSearch');
    const resultsCount = document.getElementById('catalogResultsCount');
    const grid = document.getElementById('catalogGrid');

    // Show/hide clear button based on query
    if (clearBtn) {
        clearBtn.style.display = query ? 'flex' : 'none';
    }

    // Get active category filter
    const activeCategory = document.querySelector('.sub-nav-item[data-category].active');
    const category = activeCategory ? activeCategory.dataset.category : 'all';

    // Apply category filter first
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
                <button class="btn btn-secondary" onclick="clearCatalogSearch()">Clear Search</button>
            </div>
        `;
    } else {
        // Clear grid and render using template cloning
        grid.innerHTML = '';
        for (const app of filtered) {
            renderAppCard(app, grid, false);
        }
    }

    // Reinitialize Lucide icons
    initLucideIcons();
}

function clearCatalogSearch() {
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
    searchCatalog('');
}

// Console and Logs Modal Functions
function showAppLogs(appId, hostname) {
    const modal = document.getElementById('deployModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = `📋 Logs - ${hostname}`;
    
    modalBody.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
                <button class="btn btn-sm btn-secondary" onclick="refreshLogs('${appId}', 'all')">
                    All
                </button>
                <button class="btn btn-sm btn-ghost" onclick="refreshLogs('${appId}', 'docker')">
                    Docker
                </button>
                <button class="btn btn-sm btn-ghost" onclick="refreshLogs('${appId}', 'system')">
                    System
                </button>
                <button class="btn btn-sm btn-ghost" onclick="downloadLogs('${appId}')" style="margin-left: auto;">
                    💾 Download
                </button>
            </div>
        </div>
        
        <div style="background: #1a1a1a; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1rem; height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.875rem; color: #e0e0e0;">
            <div id="logsContent">
                <div style="text-align: center; padding: 2rem; color: var(--text-tertiary);">
                    <div class="loading-spinner" style="display: inline-block; margin-bottom: 1rem;"></div>
                    <div>Loading logs...</div>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 1rem; display: flex; justify-content: space-between; align-items: center;">
            <label style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; color: var(--text-secondary);">
                <input type="checkbox" id="autoRefreshLogs" onchange="toggleAutoRefresh('${appId}')">
                Auto-refresh (5s)
            </label>
            <span style="font-size: 0.75rem; color: var(--text-tertiary);">
                Last updated: <span id="logsTimestamp">-</span>
            </span>
        </div>
    `;
    
    modal.classList.add('show');
    openModal(); // Prevent body scrolling
    loadAppLogs(appId);
}

function showAppConsole(appId, hostname) {
    // Check authentication first
    if (!Auth.isAuthenticated()) {
        console.warn('⚠️  User not authenticated - showing login modal');
        showToast('Please login to access the console', 'warning');
        showAuthModal();
        return;
    }
    
    const modal = document.getElementById('deployModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    // Hide the modal header for console view
    const modalHeader = modal.querySelector('.modal-header');
    if (modalHeader) {
        modalHeader.style.display = 'none';
    }
    
    // Remove all padding for console view
    modalBody.style.padding = '0';
    
    modalBody.innerHTML = `
        <div id="xtermContainer" style="position: relative; background: #000; border: 2px solid var(--border-cyan); border-radius: 15px; height: 92vh; padding: 0.5rem;">
            <button onclick="closeModal()" 
                onmouseover="this.style.background='rgba(239, 68, 68, 0.2)'; this.style.borderColor='#ef4444'; this.style.color='#ef4444';" 
                onmouseout="this.style.background='rgba(0, 0, 0, 0.5)'; this.style.borderColor='var(--border-cyan)'; this.style.color='var(--text-secondary)';"
                style="position: absolute; top: 0.75rem; right: 0.75rem; width: 36px; height: 36px; border-radius: var(--radius-md); background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(10px); border: 1px solid var(--border-cyan); color: var(--text-secondary); cursor: pointer; transition: var(--transition); display: flex; align-items: center; justify-content: center; font-size: 1.25rem; flex-shrink: 0; z-index: 1000; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);">✕</button>
        </div>
    `;
    
    modal.classList.add('show');
    openModal(); // Prevent body scrolling
    
    // Initialize xterm.js
    setTimeout(() => initializeXterm(appId, hostname), 100);
}

let logsRefreshInterval = null;

async function loadAppLogs(appId, type = 'all') {
    try {
        const response = await authFetch(`${API_BASE}/apps/${appId}/logs`);
        if (!response.ok) throw new Error('Failed to load logs');
        
        const data = await response.json();
        const logsContent = document.getElementById('logsContent');
        const timestamp = document.getElementById('logsTimestamp');
        
        if (logsContent) {
            const logs = data.logs || 'No logs available';
            logsContent.innerHTML = `<pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(logs)}</pre>`;
            logsContent.parentElement.scrollTop = logsContent.parentElement.scrollHeight;
        }
        
        if (timestamp) {
            timestamp.textContent = new Date().toLocaleTimeString();
        }
    } catch (error) {
        const logsContent = document.getElementById('logsContent');
        if (logsContent) {
            logsContent.innerHTML = `<div style="color: var(--danger); padding: 1rem;">Error loading logs: ${error.message}</div>`;
        }
    }
}

function refreshLogs(appId, type) {
    document.querySelectorAll('#modalBody .btn-sm').forEach(btn => {
        if (!btn.textContent.includes('Download')) {
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-ghost');
        }
    });
    event.target.classList.remove('btn-ghost');
    event.target.classList.add('btn-secondary');
    loadAppLogs(appId, type);
}

function toggleAutoRefresh(appId) {
    const checkbox = document.getElementById('autoRefreshLogs');
    if (checkbox.checked) {
        logsRefreshInterval = setInterval(() => loadAppLogs(appId), 5000);
    } else {
        if (logsRefreshInterval) {
            clearInterval(logsRefreshInterval);
            logsRefreshInterval = null;
        }
    }
}

async function downloadLogs(appId) {
    try {
        const response = await authFetch(`${API_BASE}/apps/${appId}/logs`);
        if (!response.ok) throw new Error('Failed to download logs');
        
        const data = await response.json();
        const logs = data.logs || 'No logs available';
        
        const blob = new Blob([logs], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `app-${appId}-logs-${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showNotification('Logs downloaded successfully', 'success');
    } catch (error) {
        showNotification('Failed to download logs: ' + error.message, 'error');
    }
}

async function executeCommand(appId) {
    const input = document.getElementById('consoleCommand');
    const command = input.value.trim();
    if (!command) return;
    
    const output = document.getElementById('consoleOutput');
    const commandDiv = document.createElement('div');
    commandDiv.style.color = '#4ade80';
    commandDiv.style.marginTop = '0.5rem';
    commandDiv.textContent = `$ ${command}`;
    output.appendChild(commandDiv);
    
    const loadingDiv = document.createElement('div');
    loadingDiv.style.color = '#94a3b8';
    loadingDiv.textContent = 'Executing...';
    output.appendChild(loadingDiv);
    output.parentElement.scrollTop = output.parentElement.scrollHeight;
    
    try {
        const response = await authFetch(`${API_BASE}/apps/${appId}/exec`, {
            method: 'POST',
            // Don't override headers - authFetch adds Authorization automatically
            body: JSON.stringify({ command })
        });
        
        if (!response.ok) throw new Error('Command execution failed');
        const data = await response.json();
        output.removeChild(loadingDiv);
        
        const resultDiv = document.createElement('div');
        resultDiv.style.color = data.success ? '#e0e0e0' : '#ef4444';
        resultDiv.style.whiteSpace = 'pre-wrap';
        resultDiv.textContent = data.output || data.error || 'Command executed';
        output.appendChild(resultDiv);
    } catch (error) {
        output.removeChild(loadingDiv);
        const errorDiv = document.createElement('div');
        errorDiv.style.color = '#ef4444';
        errorDiv.textContent = `Error: ${error.message}`;
        output.appendChild(errorDiv);
    }
    
    input.value = '';
    output.parentElement.scrollTop = output.parentElement.scrollHeight;
}

function setCommand(command) {
    const input = document.getElementById('consoleCommand');
    if (input) {
        input.value = command;
        input.focus();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// XTerm.js Terminal Management
let terminalInstance = null;
let terminalFitAddon = null;
let currentAppId = null;
let currentHostname = null;
let commandHistory = [];
let historyIndex = -1;
let currentCommand = '';

function initializeXterm(appId, hostname) {
    currentAppId = appId;
    currentHostname = hostname;
    
    // Clean up existing terminal if any
    if (terminalInstance) {
        terminalInstance.dispose();
        terminalInstance = null;
    }
    
    const container = document.getElementById('xtermContainer');
    if (!container) return;
    
    // Create terminal with custom theme
    terminalInstance = new Terminal({
        cursorBlink: true,
        cursorStyle: 'block',
        fontSize: 14,
        fontFamily: '"Cascadia Code", "Courier New", monospace',
        theme: {
            background: '#000000',
            foreground: '#e0e0e0',
            cursor: '#4ade80',
            black: '#000000',
            red: '#ef4444',
            green: '#4ade80',
            yellow: '#fbbf24',
            blue: '#3b82f6',
            magenta: '#a855f7',
            cyan: '#06b6d4',
            white: '#e0e0e0',
            brightBlack: '#666666',
            brightRed: '#f87171',
            brightGreen: '#86efac',
            brightYellow: '#fcd34d',
            brightBlue: '#60a5fa',
            brightMagenta: '#c084fc',
            brightCyan: '#22d3ee',
            brightWhite: '#ffffff'
        },
        rows: 24,
        cols: 80
    });
    
    // Add fit addon
    terminalFitAddon = new FitAddon.FitAddon();
    terminalInstance.loadAddon(terminalFitAddon);
    
    // Open terminal in container
    terminalInstance.open(container);
    terminalFitAddon.fit();
    
    // Write welcome message
    terminalInstance.writeln('\x1b[1;32mProximity Console\x1b[0m');
    terminalInstance.writeln(`Connected to: \x1b[1;36m${hostname}\x1b[0m`);
    terminalInstance.writeln('Type commands and press Enter to execute.');
    terminalInstance.writeln('');
    writePrompt();
    
    // Handle terminal input
    terminalInstance.onData(data => handleTerminalInput(data));
    
    // Handle window resize
    const resizeObserver = new ResizeObserver(() => {
        if (terminalFitAddon && terminalInstance) {
            try {
                terminalFitAddon.fit();
            } catch (e) {
                // Ignore resize errors
            }
        }
    });
    resizeObserver.observe(container);
    
    // Store observer for cleanup
    container._resizeObserver = resizeObserver;
    
    // Focus terminal
    terminalInstance.focus();
}

function writePrompt() {
    if (!terminalInstance) return;
    terminalInstance.write(`\x1b[1;32mproximity@${currentHostname}\x1b[0m:\x1b[1;34m~\x1b[0m$ `);
}

function handleTerminalInput(data) {
    if (!terminalInstance) return;
    
    const code = data.charCodeAt(0);
    
    // Handle Enter key
    if (code === 13) {
        terminalInstance.write('\r\n');
        if (currentCommand.trim()) {
            commandHistory.push(currentCommand);
            historyIndex = commandHistory.length;
            executeTerminalCommand(currentCommand.trim());
        } else {
            writePrompt();
        }
        currentCommand = '';
        return;
    }
    
    // Handle Backspace
    if (code === 127) {
        if (currentCommand.length > 0) {
            currentCommand = currentCommand.slice(0, -1);
            terminalInstance.write('\b \b');
        }
        return;
    }
    
    // Handle Ctrl+C
    if (code === 3) {
        terminalInstance.write('^C\r\n');
        currentCommand = '';
        writePrompt();
        return;
    }
    
    // Handle Ctrl+L (clear)
    if (code === 12) {
        terminalInstance.clear();
        currentCommand = '';
        writePrompt();
        return;
    }
    
    // Handle Up Arrow (previous command)
    if (data === '\x1b[A') {
        if (historyIndex > 0) {
            // Clear current line
            terminalInstance.write('\r\x1b[K');
            writePrompt();
            
            historyIndex--;
            currentCommand = commandHistory[historyIndex];
            terminalInstance.write(currentCommand);
        }
        return;
    }
    
    // Handle Down Arrow (next command)
    if (data === '\x1b[B') {
        if (historyIndex < commandHistory.length - 1) {
            // Clear current line
            terminalInstance.write('\r\x1b[K');
            writePrompt();
            
            historyIndex++;
            currentCommand = commandHistory[historyIndex];
            terminalInstance.write(currentCommand);
        } else if (historyIndex === commandHistory.length - 1) {
            // Clear current line
            terminalInstance.write('\r\x1b[K');
            writePrompt();
            
            historyIndex = commandHistory.length;
            currentCommand = '';
        }
        return;
    }
    
    // Ignore other control sequences
    if (code === 27 || data.startsWith('\x1b')) {
        return;
    }
    
    // Add character to command
    currentCommand += data;
    terminalInstance.write(data);
}

async function executeTerminalCommand(command) {
    if (!terminalInstance || !currentAppId) return;
    
    // Double-check authentication before executing
    if (!Auth.isAuthenticated()) {
        console.error('[Terminal] Not authenticated - no token found');
        terminalInstance.writeln('\r\n\x1b[1;31mError: Not authenticated. Please login first.\x1b[0m\r\n');
        showAuthModal();
        return;
    }
    
    console.log('[Terminal] Executing command:', command, 'for app:', currentAppId);
    console.log('[Terminal] Token exists:', !!Auth.getToken());
    
    try {
        const response = await authFetch(`${API_BASE}/apps/${currentAppId}/exec`, {
            method: 'POST',
            // Don't override headers - authFetch will add Authorization + Content-Type
            body: JSON.stringify({ command })
        });
        
        console.log('[Terminal] Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Terminal] Response not OK:', response.status, errorText);
            throw new Error(`Command execution failed: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('[Terminal] Response data:', data);
        
        if (data.success && data.output) {
            // Write output line by line
            const lines = data.output.split('\n');
            lines.forEach(line => {
                terminalInstance.writeln(line);
            });
        } else if (data.error) {
            terminalInstance.writeln(`\x1b[1;31m${data.error}\x1b[0m`);
        }
    } catch (error) {
        console.error('[Terminal] Execution error:', error);
        terminalInstance.writeln(`\x1b[1;31mError: ${error.message}\x1b[0m`);
    }
    
    writePrompt();
}

function cleanupTerminal() {
    if (terminalInstance) {
        terminalInstance.dispose();
        terminalInstance = null;
        terminalFitAddon = null;
    }
    
    const container = document.getElementById('xtermContainer');
    if (container && container._resizeObserver) {
        container._resizeObserver.disconnect();
        delete container._resizeObserver;
    }
    
    currentAppId = null;
    currentHostname = null;
    currentCommand = '';
}

const originalCloseModal = window.closeModal;
function closeModal() {
    // Cleanup terminal if exists
    cleanupTerminal();
    
    if (logsRefreshInterval) {
        clearInterval(logsRefreshInterval);
        logsRefreshInterval = null;
    }
    
    const modal = document.getElementById('deployModal');
    const modalBody = modal.querySelector('.modal-body');
    
    // Restore modal header visibility
    const modalHeader = modal.querySelector('.modal-header');
    if (modalHeader) {
        modalHeader.style.display = '';
    }
    
    // Restore modal body padding
    if (modalBody) {
        modalBody.style.padding = '';
    }
    
    modal.classList.remove('show');
    
    // Only remove modal-open if no other modals are open
    const anyModalOpen = Array.from(document.querySelectorAll('.modal.show')).length > 0;
    if (!anyModalOpen) {
        const scrollPosition = parseInt(document.body.style.top || '0') * -1;
        document.body.classList.remove('modal-open');
        document.body.style.top = '';
        
        // Re-enable pointer events on main content
        const mainContent = document.querySelector('.app-container');
        if (mainContent) {
            mainContent.style.pointerEvents = '';
        }
        
        // Restore scroll position
        window.scrollTo(0, scrollPosition);
    }
}

// Settings Page Helpers
// Proximity Mode Toggle Handler
function handleModeToggle(checkbox) {
    const newMode = checkbox.checked ? 'PRO' : 'AUTO';

    // Use the modular UI utility
    if (window.UI && window.UI.switchProximityMode) {
        window.UI.switchProximityMode(newMode);
    } else {
        // Fallback if modular system not loaded
        state.proximityMode = newMode;
        localStorage.setItem('proximityMode', newMode);
        document.body.classList.toggle('pro-mode', newMode === 'PRO');
    }

    // Update slider text
    const slider = checkbox.nextElementSibling;
    if (slider) {
        slider.textContent = newMode;
    }

    // Update badge
    const badge = document.getElementById('current-mode-badge');
    if (badge) {
        badge.className = `mode-badge ${newMode.toLowerCase()}`;
        badge.innerHTML = `
            <i data-lucide="${newMode === 'AUTO' ? 'zap' : 'wrench'}"></i>
            ${newMode}
        `;
        initLucideIcons();
    }

    // Update mode cards
    const autoCard = document.getElementById('auto-mode-card');
    const proCard = document.getElementById('pro-mode-card');
    if (autoCard && proCard) {
        autoCard.classList.toggle('active', newMode === 'AUTO');
        proCard.classList.toggle('active', newMode === 'PRO');
    }

    // Show notification
    showNotification(`✓ Switched to ${newMode} mode`, 'success');

    console.log(`🎯 Mode toggled to: ${newMode}`);
}

function setupSettingsTabs() {
    // NOTE: Settings tabs are now managed by the top navigation submenu
    // The activateSettingsTab() function in submenu.js handles tab switching
    // No need to setup event listeners here anymore
}

function setupSettingsForms() {
    // Initialize validation for all settings forms
    if (typeof initFormValidation === 'function') {
        initFormValidation('proxmoxForm');
        initFormValidation('networkForm');
        initFormValidation('resourcesForm');
    }

    // Advanced Network Validation - DHCP Range & Subnet Checking
    const networkForm = document.getElementById('networkForm');
    if (networkForm) {
        const subnetInput = networkForm.querySelector('[name="lan_subnet"]');
        const gatewayInput = networkForm.querySelector('[name="lan_gateway"]');
        const dhcpStartInput = networkForm.querySelector('[name="dhcp_start"]');
        const dhcpEndInput = networkForm.querySelector('[name="dhcp_end"]');

        // Helper: Convert IP to number for comparison
        const ipToNumber = (ip) => {
            const parts = ip.split('.');
            return (parseInt(parts[0]) << 24) + (parseInt(parts[1]) << 16) + 
                   (parseInt(parts[2]) << 8) + parseInt(parts[3]);
        };

        // Helper: Check if IP is in subnet
        const isIpInSubnet = (ip, cidr) => {
            const [subnet, maskBits] = cidr.split('/');
            const mask = parseInt(maskBits);
            const maskNum = (0xFFFFFFFF << (32 - mask)) >>> 0;
            const ipNum = ipToNumber(ip);
            const subnetNum = ipToNumber(subnet);
            return (ipNum & maskNum) === (subnetNum & maskNum);
        };

        // Validate gateway is in subnet
        if (gatewayInput && subnetInput) {
            const validateGateway = () => {
                const gateway = gatewayInput.value.trim();
                const subnet = subnetInput.value.trim();
                
                if (!gateway || !subnet) return;
                
                // First check if both are valid formats
                const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
                const cidrPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([0-9]|[1-2][0-9]|3[0-2])$/;
                
                if (!ipPattern.test(gateway) || !cidrPattern.test(subnet)) return;
                
                if (!isIpInSubnet(gateway, subnet)) {
                    if (typeof showFieldError === 'function') {
                        showFieldError(gatewayInput, `Gateway IP must be within subnet ${subnet}`);
                    }
                } else if (gatewayInput.classList.contains('error')) {
                    if (typeof showFieldSuccess === 'function') {
                        showFieldSuccess(gatewayInput);
                    }
                }
            };

            gatewayInput.addEventListener('blur', validateGateway);
            subnetInput.addEventListener('blur', validateGateway);
        }

        // Validate DHCP range
        if (dhcpStartInput && dhcpEndInput && subnetInput) {
            const validateDhcpRange = () => {
                const start = dhcpStartInput.value.trim();
                const end = dhcpEndInput.value.trim();
                const subnet = subnetInput.value.trim();
                
                if (!start || !end || !subnet) return;
                
                // Check format validity first
                const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
                const cidrPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([0-9]|[1-2][0-9]|3[0-2])$/;
                
                if (!ipPattern.test(start) || !ipPattern.test(end) || !cidrPattern.test(subnet)) return;
                
                // Check if start < end
                const startNum = ipToNumber(start);
                const endNum = ipToNumber(end);
                
                if (startNum >= endNum) {
                    if (typeof showFieldError === 'function') {
                        showFieldError(dhcpEndInput, 'DHCP end must be greater than DHCP start');
                    }
                    return;
                }
                
                // Check if both are in subnet
                if (!isIpInSubnet(start, subnet)) {
                    if (typeof showFieldError === 'function') {
                        showFieldError(dhcpStartInput, `DHCP start must be within subnet ${subnet}`);
                    }
                } else if (dhcpStartInput.classList.contains('error')) {
                    if (typeof showFieldSuccess === 'function') {
                        showFieldSuccess(dhcpStartInput);
                    }
                }
                
                if (!isIpInSubnet(end, subnet)) {
                    if (typeof showFieldError === 'function') {
                        showFieldError(dhcpEndInput, `DHCP end must be within subnet ${subnet}`);
                    }
                } else if (dhcpEndInput.classList.contains('error')) {
                    if (typeof showFieldSuccess === 'function') {
                        showFieldSuccess(dhcpEndInput);
                    }
                }
            };

            dhcpStartInput.addEventListener('blur', validateDhcpRange);
            dhcpEndInput.addEventListener('blur', validateDhcpRange);
            subnetInput.addEventListener('blur', validateDhcpRange);
        }

        // Form submission with advanced validation
        networkForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Run all advanced validations before submit
            const subnet = subnetInput?.value.trim();
            const gateway = gatewayInput?.value.trim();
            const dhcpStart = dhcpStartInput?.value.trim();
            const dhcpEnd = dhcpEndInput?.value.trim();
            
            let hasErrors = false;
            
            // Validate gateway in subnet
            if (gateway && subnet && !isIpInSubnet(gateway, subnet)) {
                if (typeof showFieldError === 'function') {
                    showFieldError(gatewayInput, `Gateway IP must be within subnet ${subnet}`);
                }
                hasErrors = true;
            }
            
            // Validate DHCP range
            if (dhcpStart && dhcpEnd) {
                const startNum = ipToNumber(dhcpStart);
                const endNum = ipToNumber(dhcpEnd);
                
                if (startNum >= endNum) {
                    if (typeof showFieldError === 'function') {
                        showFieldError(dhcpEndInput, 'DHCP end must be greater than DHCP start');
                    }
                    hasErrors = true;
                }
                
                if (subnet) {
                    if (!isIpInSubnet(dhcpStart, subnet)) {
                        if (typeof showFieldError === 'function') {
                            showFieldError(dhcpStartInput, `DHCP start must be within subnet ${subnet}`);
                        }
                        hasErrors = true;
                    }
                    
                    if (!isIpInSubnet(dhcpEnd, subnet)) {
                        if (typeof showFieldError === 'function') {
                            showFieldError(dhcpEndInput, `DHCP end must be within subnet ${subnet}`);
                        }
                        hasErrors = true;
                    }
                }
            }
            
            if (hasErrors) {
                if (window.showWarning) {
                    showWarning('Please fix network configuration errors before saving');
                }
                return;
            }
            
            await saveNetworkSettings(new FormData(networkForm));
        });
    }

    // Proxmox form
    const proxmoxForm = document.getElementById('proxmoxForm');
    if (proxmoxForm) {
        proxmoxForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveProxmoxSettings(new FormData(proxmoxForm));
        });
    }

    // Resources form
    const resourcesForm = document.getElementById('resourcesForm');
    if (resourcesForm) {
        resourcesForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveResourceSettings(new FormData(resourcesForm));
        });
    }

    // Audio settings
    setupAudioSettings();
}

function setupAudioSettings() {
    if (!window.SoundService) {
        console.warn('SoundService not available');
        return;
    }

    // Volume slider
    const volumeSlider = document.getElementById('settingsVolumeSlider');
    const volumeValue = document.getElementById('settingsVolumeValue');
    if (volumeSlider && volumeValue) {
        volumeSlider.addEventListener('input', (e) => {
            const volume = parseInt(e.target.value) / 100;
            window.SoundService.setVolume(volume);
            volumeValue.textContent = `${e.target.value}%`;
        });

        // Test sound on release
        volumeSlider.addEventListener('change', () => {
            if (!window.SoundService.getMute()) {
                window.SoundService.play('click');
            }
        });
    }

    // Mute toggle
    const muteToggle = document.getElementById('settingsMuteToggle');
    if (muteToggle) {
        muteToggle.addEventListener('change', (e) => {
            window.SoundService.setMute(e.target.checked);

            // Update sound button in top nav
            const soundBtn = document.getElementById('soundToggleBtn');
            const soundIcon = document.getElementById('soundIcon');
            if (soundBtn && soundIcon && window.updateSoundButton) {
                window.updateSoundButton(soundBtn, soundIcon);
            }
        });
    }

    // Preset buttons
    const presetButtons = document.querySelectorAll('#audio-panel .preset-btn');
    presetButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const preset = btn.dataset.preset;
            window.SoundService.applyPreset(preset);

            // Update active state
            presetButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update slider
            if (volumeSlider && volumeValue) {
                const newVolume = Math.round(window.SoundService.getVolume() * 100);
                volumeSlider.value = newVolume;
                volumeValue.textContent = `${newVolume}%`;
            }

            // Test sound
            if (!window.SoundService.getMute()) {
                window.SoundService.play('notification');
            }
        });
    });

    // Test sound button
    const testSoundBtn = document.getElementById('testSoundBtn');
    if (testSoundBtn) {
        testSoundBtn.addEventListener('click', () => {
            if (window.SoundService.getMute()) {
                // Temporarily unmute for test
                window.SoundService.setMute(false);
                window.SoundService.play('success');
                setTimeout(() => {
                    window.SoundService.setMute(true);
                    if (muteToggle) muteToggle.checked = true;
                }, 1000);
            } else {
                window.SoundService.play('success');
            }
        });
    }
}

async function saveProxmoxSettings(formData) {
    const statusDiv = document.getElementById('proxmoxStatus');
    const token = Auth.getToken();

    if (!token) {
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Not authenticated. Please log in.</div>
                </div>
            </div>
        `;
        return;
    }

    const data = {
        host: formData.get('host'),
        port: parseInt(formData.get('port')),
        user: formData.get('user'),
        password: formData.get('password') || '******',
        verify_ssl: formData.get('verify_ssl') === 'on'
    };

    try {
        showLoading('Saving Proxmox settings...');

        const response = await authFetch(`${API_BASE}/settings/proxmox`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        hideLoading();

        if (response.ok) {
            statusDiv.innerHTML = `
                <div class="alert success">
                    <span class="alert-icon">✅</span>
                    <div class="alert-content">
                        <div class="alert-title">Settings Saved</div>
                        <div class="alert-message">${result.message || 'Proxmox settings updated successfully'}</div>
                        ${result.warning ? `<div class="alert-message" style="margin-top: 0.5rem;"><strong>⚠️ ${result.warning}</strong></div>` : ''}
                    </div>
                </div>
            `;
            showNotification('Proxmox settings saved successfully', 'success');
        } else {
            statusDiv.innerHTML = `
                <div class="alert error">
                    <span class="alert-icon">❌</span>
                    <div class="alert-content">
                        <div class="alert-title">Error</div>
                        <div class="alert-message">${result.error || 'Failed to save settings'}</div>
                    </div>
                </div>
            `;
            showNotification('Failed to save Proxmox settings', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error saving Proxmox settings:', error);
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Network error: ${error.message}</div>
                </div>
            </div>
        `;
        showNotification('Failed to save Proxmox settings', 'error');
    }
}

async function testProxmoxConnection() {
    const statusDiv = document.getElementById('proxmoxStatus');
    const token = Auth.getToken();

    if (!token) {
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Not authenticated. Please log in.</div>
                </div>
            </div>
        `;
        return;
    }

    try {
        showLoading('Testing Proxmox connection...');

        const response = await authFetch(`${API_BASE}/system/info`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        hideLoading();

        if (response.ok) {
            const data = await response.json();
            statusDiv.innerHTML = `
                <div class="alert success">
                    <span class="alert-icon">✅</span>
                    <div class="alert-content">
                        <div class="alert-title">Connection Successful</div>
                        <div class="alert-message">Connected to Proxmox cluster: ${data.cluster_name || 'Default'}</div>
                    </div>
                </div>
            `;
            showNotification('Proxmox connection test successful', 'success');
        } else {
            statusDiv.innerHTML = `
                <div class="alert error">
                    <span class="alert-icon">❌</span>
                    <div class="alert-content">
                        <div class="alert-title">Connection Failed</div>
                        <div class="alert-message">Unable to connect to Proxmox server. Check your credentials and network.</div>
                    </div>
                </div>
            `;
            showNotification('Proxmox connection test failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error testing Proxmox connection:', error);
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Network error: ${error.message}</div>
                </div>
            </div>
        `;
        showNotification('Proxmox connection test failed', 'error');
    }
}

async function saveNetworkSettings(formData) {
    const statusDiv = document.getElementById('networkStatus');
    const token = Auth.getToken();

    if (!token) {
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Not authenticated. Please log in.</div>
                </div>
            </div>
        `;
        return;
    }

    const data = {
        lan_subnet: formData.get('lan_subnet'),
        lan_gateway: formData.get('lan_gateway'),
        dhcp_start: formData.get('dhcp_start'),
        dhcp_end: formData.get('dhcp_end'),
        dns_domain: formData.get('dns_domain')
    };

    try {
        showLoading('Saving network settings...');

        const response = await authFetch(`${API_BASE}/settings/network`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        hideLoading();

        if (response.ok) {
            statusDiv.innerHTML = `
                <div class="alert success">
                    <span class="alert-icon">✅</span>
                    <div class="alert-content">
                        <div class="alert-title">Settings Saved</div>
                        <div class="alert-message">${result.message || 'Network settings updated successfully'}</div>
                    </div>
                </div>
            `;
            showNotification('Network settings saved successfully', 'success');
        } else {
            statusDiv.innerHTML = `
                <div class="alert error">
                    <span class="alert-icon">❌</span>
                    <div class="alert-content">
                        <div class="alert-title">Error</div>
                        <div class="alert-message">${result.error || 'Failed to save settings'}</div>
                    </div>
                </div>
            `;
            showNotification('Failed to save network settings', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error saving network settings:', error);
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Network error: ${error.message}</div>
                </div>
            </div>
        `;
        showNotification('Failed to save network settings', 'error');
    }
}

async function saveResourceSettings(formData) {
    const statusDiv = document.getElementById('resourcesStatus');
    const token = Auth.getToken();

    if (!token) {
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Not authenticated. Please log in.</div>
                </div>
            </div>
        `;
        return;
    }

    const data = {
        lxc_memory: parseInt(formData.get('lxc_memory')),
        lxc_cores: parseInt(formData.get('lxc_cores')),
        lxc_disk: parseInt(formData.get('lxc_disk')),
        lxc_storage: formData.get('lxc_storage')
    };

    try {
        showLoading('Saving resource settings...');

        const response = await authFetch(`${API_BASE}/settings/resources`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        hideLoading();

        if (response.ok) {
            statusDiv.innerHTML = `
                <div class="alert success">
                    <span class="alert-icon">✅</span>
                    <div class="alert-content">
                        <div class="alert-title">Settings Saved</div>
                        <div class="alert-message">${result.message || 'Resource settings updated successfully'}</div>
                    </div>
                </div>
            `;
            showNotification('Resource settings saved successfully', 'success');
        } else {
            statusDiv.innerHTML = `
                <div class="alert error">
                    <span class="alert-icon">❌</span>
                    <div class="alert-content">
                        <div class="alert-title">Error</div>
                        <div class="alert-message">${result.error || 'Failed to save settings'}</div>
                    </div>
                </div>
            `;
            showNotification('Failed to save resource settings', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error saving resource settings:', error);
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Network error: ${error.message}</div>
                </div>
            </div>
        `;
        showNotification('Failed to save resource settings', 'error');
    }
}

// Infrastructure Page Helpers
async function refreshInfrastructure() {
    showNotification('Refreshing infrastructure status...', 'info');
    await renderNodesView();
    showNotification('Infrastructure status refreshed', 'success');
}

async function restartAppliance() {
    const statusDiv = document.getElementById('infrastructureStatus');
    const token = Auth.getToken();

    if (!token) {
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Not authenticated. Please log in.</div>
                </div>
            </div>
        `;
        return;
    }

    if (!confirm('Restart the Network Appliance? This will temporarily interrupt network services for all containers.')) {
        return;
    }

    try {
        showLoading('Restarting network appliance...');

        const response = await authFetch(`${API_BASE}/system/infrastructure/appliance/restart`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const result = await response.json();
        hideLoading();

        if (response.ok) {
            statusDiv.innerHTML = `
                <div class="alert success">
                    <span class="alert-icon">✅</span>
                    <div class="alert-content">
                        <div class="alert-title">Appliance Restarted</div>
                        <div class="alert-message">${result.message || 'Network appliance restarted successfully'}</div>
                    </div>
                </div>
            `;
            showNotification('Network appliance restarted successfully', 'success');

            // Refresh infrastructure view after delay
            setTimeout(async () => {
                await refreshInfrastructure();
            }, 5000);
        } else {
            statusDiv.innerHTML = `
                <div class="alert error">
                    <span class="alert-icon">❌</span>
                    <div class="alert-content">
                        <div class="alert-title">Restart Failed</div>
                        <div class="alert-message">${result.detail || result.error || 'Failed to restart appliance'}</div>
                    </div>
                </div>
            `;
            showNotification('Failed to restart appliance', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error restarting appliance:', error);
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Network error: ${error.message}</div>
                </div>
            </div>
        `;
        showNotification('Failed to restart appliance', 'error');
    }
}

async function viewApplianceLogs() {
    const token = Auth.getToken();

    if (!token) {
        showNotification('Not authenticated', 'error');
        return;
    }

    try {
        showLoading('Fetching appliance logs...');

        const response = await authFetch(`${API_BASE}/system/infrastructure/appliance/logs?lines=50`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const result = await response.json();
        hideLoading();

        if (response.ok && result.data) {
            const logs = result.data.logs;

            // Display logs in a modal
            const modalBody = document.getElementById('modalBody');
            const modalTitle = document.getElementById('modalTitle');

            modalTitle.textContent = 'Network Appliance Logs';
            modalBody.innerHTML = `
                <div class="logs-viewer">
                    <div class="log-section">
                        <h4 class="log-section-title">System Logs</h4>
                        <pre class="log-output">${logs.system || 'No system logs available'}</pre>
                    </div>

                    <div class="log-section">
                        <h4 class="log-section-title">DNSMASQ Status</h4>
                        <pre class="log-output">${logs.dnsmasq_status || 'No dnsmasq status available'}</pre>
                    </div>

                    <div class="log-section">
                        <h4 class="log-section-title">Network Status</h4>
                        <pre class="log-output">${logs.network_status || 'No network status available'}</pre>
                    </div>

                    <div class="log-section">
                        <h4 class="log-section-title">NAT Rules</h4>
                        <pre class="log-output">${logs.nat_rules || 'No NAT rules available'}</pre>
                    </div>
                </div>

                <div class="modal-actions" style="margin-top: 1.5rem; display: flex; justify-content: flex-end;">
                    <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                </div>
            `;

            document.getElementById('deployModal').classList.add('show');
        } else {
            showNotification('Failed to fetch logs', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error fetching logs:', error);
        showNotification('Failed to fetch logs', 'error');
    }
}

async function testNAT() {
    const statusDiv = document.getElementById('infrastructureStatus');
    const token = Auth.getToken();

    if (!token) {
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Not authenticated. Please log in.</div>
                </div>
            </div>
        `;
        return;
    }

    try {
        showLoading('Testing NAT connectivity...');

        const response = await authFetch(`${API_BASE}/system/infrastructure/test-nat`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const result = await response.json();
        hideLoading();

        if (response.ok && result.data) {
            const { success, tests } = result.data;

            const testResults = Object.entries(tests).map(([name, test]) => `
                <div class="test-result ${test.passed ? 'passed' : 'failed'}">
                    <div class="test-name">
                        ${test.passed ? '✅' : '❌'}
                        ${name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                    </div>
                </div>
            `).join('');

            statusDiv.innerHTML = `
                <div class="alert ${success ? 'success' : 'error'}">
                    <span class="alert-icon">${success ? '✅' : '❌'}</span>
                    <div class="alert-content">
                        <div class="alert-title">NAT Connectivity Test ${success ? 'Passed' : 'Failed'}</div>
                        <div class="test-results" style="margin-top: 0.75rem;">
                            ${testResults}
                        </div>
                    </div>
                </div>
            `;
            showNotification(`NAT test ${success ? 'passed' : 'failed'}`, success ? 'success' : 'error');
        } else {
            statusDiv.innerHTML = `
                <div class="alert error">
                    <span class="alert-icon">❌</span>
                    <div class="alert-content">
                        <div class="alert-title">Test Failed</div>
                        <div class="alert-message">${result.detail || result.error || 'Failed to run NAT test'}</div>
                    </div>
                </div>
            `;
            showNotification('NAT test failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Error testing NAT:', error);
        statusDiv.innerHTML = `
            <div class="alert error">
                <span class="alert-icon">❌</span>
                <div class="alert-content">
                    <div class="alert-message">Network error: ${error.message}</div>
                </div>
            </div>
        `;
        showNotification('NAT test failed', 'error');
    }
}

// Event Listeners
// User Menu Toggle
function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    const profileBtn = document.getElementById('userProfileBtn');

    menu.classList.toggle('active');
    profileBtn.classList.toggle('active');

    // Reinitialize Lucide icons
    initLucideIcons();
}

// Close user menu when clicking outside
document.addEventListener('click', (e) => {
    const menu = document.getElementById('userMenu');
    const profileBtn = document.getElementById('userProfileBtn');

    if (menu && profileBtn && !profileBtn.contains(e.target) && !menu.contains(e.target)) {
        menu.classList.remove('active');
        profileBtn.classList.remove('active');
    }
});

// Handle Logout
async function handleLogout(e) {
    e.preventDefault();

    try {
        // Call logout endpoint for audit logging
        await authFetch(`${API_BASE}/auth/logout`, {
            method: 'POST'
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        // Always clear local auth data
        Auth.logout();
        showNotification('You have been logged out', 'info');
    }
}

// Show User Profile (placeholder)
function showUserProfile(e) {
    e.preventDefault();
    toggleUserMenu();
    showNotification('Profile view coming soon!', 'info');
}

function setupEventListeners() {
    console.log('🔧 setupEventListeners() called');

    // Navigation
    const navItems = document.querySelectorAll('.nav-item');
    console.log(`📍 Found ${navItems.length} nav items`);

    navItems.forEach((item, index) => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            console.log(`🖱️  Nav item clicked: ${view}`);
            if (view) showView(view);
        });
        console.log(`  ✓ Attached listener to nav item ${index}: ${item.dataset.view}`);
    });

    // User profile menu toggle
    const userProfileBtn = document.getElementById('userProfileBtn');
    if (userProfileBtn) {
        userProfileBtn.addEventListener('click', toggleUserMenu);
    }

    // Close modal on outside click
    document.getElementById('deployModal').addEventListener('click', (e) => {
        if (e.target.id === 'deployModal') {
            closeModal();
        }
    });
}

// Initialize on load - DISABLED: Now handled by main.js with onboarding
// document.addEventListener('DOMContentLoaded', init);

// Make init available globally so main.js can call it after onboarding
window.init = init;

// --- Auth Modal (Register/Login) Logic ---
// Show Auth Modal (Register/Login)
function showAuthModal() {
        const modal = document.getElementById('authModal');
        if (!modal) {
                console.error('Auth modal element not found');
                return;
        }

        // Show the modal with proper Bootstrap mechanics
        modal.style.display = 'flex';
        modal.classList.add('show');
        
        // Force reflow for animation
        modal.offsetHeight;
        
        // Prevent body scrolling
        document.body.classList.add('modal-open');
        document.body.style.overflow = 'hidden';
        
        // Create backdrop if it doesn't exist
        let backdrop = document.querySelector('.modal-backdrop');
        if (!backdrop) {
                backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                document.body.appendChild(backdrop);
        }
        backdrop.classList.add('show');

        // Render the tabs
        renderAuthTabs('register');

        console.log('✅ Auth modal displayed');
}

function closeAuthModal() {
        const modal = document.getElementById('authModal');
        if (modal) {
                modal.classList.remove('show');
                modal.style.display = 'none';
        }

        // Restore body scrolling
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        
        // Remove backdrop
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
                backdrop.remove();
        }
}

function renderAuthTabs(defaultTab = 'register') {
        const body = document.getElementById('authModalBody');
        body.innerHTML = `
            <div class="auth-tabs">
                <button id="registerTab" class="auth-tab ${defaultTab === 'register' ? 'active' : ''}" onclick="switchAuthTab('register')">Register</button>
                <button id="loginTab" class="auth-tab ${defaultTab === 'login' ? 'active' : ''}" onclick="switchAuthTab('login')">Login</button>
            </div>
            <div id="authTabContent"></div>
        `;
        switchAuthTab(defaultTab);
}

function switchAuthTab(tab) {
        document.getElementById('registerTab').classList.toggle('active', tab === 'register');
        document.getElementById('loginTab').classList.toggle('active', tab === 'login');
        if (tab === 'register') {
                renderRegisterForm();
        } else {
                renderLoginForm();
        }
}

function renderRegisterForm() {
    const content = document.getElementById('authTabContent');
    content.innerHTML = `
      <form id="registerForm" class="auth-form">
        <div class="form-group">
          <label class="form-label">Username</label>
          <input type="text" class="form-input" id="registerUsername" required autocomplete="username" placeholder="Enter username">
        </div>
        <div class="form-group">
          <label class="form-label">Password</label>
          <input type="password" class="form-input" id="registerPassword" required autocomplete="new-password" placeholder="Min. 8 characters">
        </div>
        <div class="form-group">
          <label class="form-label">Email</label>
          <input type="email" class="form-input" id="registerEmail" required autocomplete="email" placeholder="your@email.com">
        </div>
        <div id="registerError" class="form-error"></div>
        <button type="submit" class="btn btn-primary" style="width:100%;">Register</button>
      </form>
    `;
    document.getElementById('registerForm').onsubmit = handleRegisterSubmit;
}

function renderLoginForm(prefill = {}) {
    const content = document.getElementById('authTabContent');
    content.innerHTML = `
      <form id="loginForm" class="auth-form">
        <div class="form-group">
          <label class="form-label">Username</label>
          <input type="text" class="form-input" id="loginUsername" required autocomplete="username" value="${prefill.username || ''}" placeholder="Enter username">
        </div>
        <div class="form-group">
          <label class="form-label">Password</label>
          <input type="password" class="form-input" id="loginPassword" required autocomplete="current-password" value="${prefill.password || ''}" placeholder="Enter password">
        </div>
        <div id="loginError" class="form-error"></div>
        <button type="submit" class="btn btn-primary" style="width:100%;">Login</button>
      </form>
    `;
    document.getElementById('loginForm').onsubmit = handleLoginSubmit;
}

async function handleRegisterSubmit(e) {
    e.preventDefault();
    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value;
    const email = document.getElementById('registerEmail').value.trim();
    const errorDiv = document.getElementById('registerError');
    errorDiv.textContent = '';
    
    // Build payload (email is required)
    const payload = { username, password, email };
    
    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) {
            const err = await res.json();
            // Handle validation errors properly
            if (err.detail && Array.isArray(err.detail)) {
                errorDiv.textContent = err.detail.map(e => e.msg).join(', ');
            } else if (typeof err.detail === 'string') {
                errorDiv.textContent = err.detail;
            } else {
                errorDiv.textContent = 'Registration failed.';
            }
            return;
        }
        
        // Registration successful - switch to login tab
        const result = await res.json();

        // Show success notification
        showNotification('✓ Registration successful! Please log in.', 'success');

        // Switch to login tab with pre-filled credentials
        switchAuthTab('login');

        // Pre-fill the login form after a brief delay to ensure DOM is ready
        setTimeout(() => {
            const usernameInput = document.getElementById('loginUsername');
            const passwordInput = document.getElementById('loginPassword');
            if (usernameInput) usernameInput.value = username;
            if (passwordInput) passwordInput.value = password;
        }, 100);
        
    } catch (err) {
        console.error('Registration error:', err);
        errorDiv.textContent = 'Network error. Please try again.';
    }
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    errorDiv.textContent = '';
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (!res.ok) {
            const err = await res.json();
            errorDiv.textContent = err.detail || 'Login failed.';
            return;
        }
        const data = await res.json();
        
        // Store the token and user data
        Auth.setToken(data.access_token, data.user);
        
        showNotification('Login successful!', 'success');
        
        // Initialize authenticated session (uses same flow as registration)
        await initializeAuthenticatedSession();
        
    } catch (err) {
        console.error('Login error:', err);
        errorDiv.textContent = 'Network error. Please try again.';
    }
}

/**
 * Centralized function to initialize authenticated session
 * Called after both successful registration and login
 * Ensures consistent authentication state across the application
 */
async function initializeAuthenticatedSession() {
    console.log('🔐 Initializing authenticated session...');
    
    try {
        // 1. Close the auth modal
        closeAuthModal();
        
        // 2. Update user info in sidebar
        updateUserInfo();
        
        // 3. Show loading state
        showLoading('Loading your applications...');
        
        // 4. Load all necessary data with individual error handling
        console.log('4️⃣ Loading data...');
        console.log('   ⏳ Loading system info...');
        await loadSystemInfo();
        console.log('   ✓ System info loaded');
        
        console.log('   ⏳ Loading nodes...');
        await loadNodes();
        console.log('   ✓ Nodes loaded');
        
        console.log('   ⏳ Loading deployed apps...');
        await loadDeployedApps();
        console.log('   ✓ Deployed apps loaded');
        
        console.log('   ⏳ Loading catalog...');
        await loadCatalog();
        console.log('   ✓ Catalog loaded');
        
        // 5. Update the UI with loaded data
        console.log('5️⃣ Updating UI...');
        updateUI();

        // 6. Setup event listeners FIRST (before showing views)
        console.log('6️⃣ Setting up event listeners...');
        setupEventListeners();
        console.log('   ✓ Event listeners attached');

        // Set global flag to indicate event listeners are ready
        window.eventListenersReady = true;

        // 7. Initialize Lucide icons
        initLucideIcons();

        // 8. Hide loading state
        hideLoading();

        // 9. Show the dashboard view (LAST - after everything is ready)
        console.log('7️⃣ Showing dashboard view...');
        showView('dashboard');
        
        console.log('✅ Authenticated session initialized successfully');
        
    } catch (error) {
        console.error('❌ Error initializing authenticated session:', error);
        hideLoading();
        showNotification('Failed to load application data. Please refresh the page.', 'error');
    }
}

// Patch: override showLoginModal to showAuthModal for legacy calls
window.showLoginModal = showAuthModal;

// ============================================================================
// BACKUP MANAGEMENT
// ============================================================================

let currentBackupAppId = null;
let backupPollingInterval = null;

/**
 * Show backup management modal for an app
 */
async function showBackupModal(appId) {
    currentBackupAppId = appId;

    try {
        // Get app details
        const app = await authFetch(`${API_BASE}/apps/${appId}`);
        document.getElementById('backup-app-name').textContent = app.name;

        // Load backups
        await loadBackups(appId);

        // Show modal
        document.getElementById('backupModal').style.display = 'flex';

        // Refresh icons after modal content is added
        setTimeout(() => lucide.createIcons(), 100);
    } catch (error) {
        showNotification('Failed to load backup modal', 'error');
        console.error('Error showing backup modal:', error);
    }
}

/**
 * Hide backup management modal
 */
function hideBackupModal() {
    document.getElementById('backupModal').style.display = 'none';
    currentBackupAppId = null;

    // Stop polling
    if (backupPollingInterval) {
        clearInterval(backupPollingInterval);
        backupPollingInterval = null;
    }
}

/**
 * Load backups for current app
 */
async function loadBackups(appId) {
    try {
        const response = await authFetch(`${API_BASE}/apps/${appId}/backups`);
        const backups = response.backups || [];

        const listEl = document.getElementById('backup-list');

        if (backups.length === 0) {
            listEl.innerHTML = '<p class="empty-state">No backups yet. Create your first backup to protect your data.</p>';
            return;
        }

        listEl.innerHTML = backups.map(backup => `
            <div class="backup-item" data-backup-id="${backup.id}">
                <div class="backup-info">
                    <div class="backup-filename">${backup.filename}</div>
                    <div class="backup-meta">
                        <span class="backup-date">
                            <i data-lucide="calendar"></i>
                            ${formatDate(backup.created_at)}
                        </span>
                        <span class="backup-size">
                            <i data-lucide="hard-drive"></i>
                            ${formatSize(backup.size_bytes)}
                        </span>
                        <span class="backup-status status-${backup.status}">
                            ${getStatusIcon(backup.status)}
                            ${backup.status}
                        </span>
                    </div>
                    ${backup.error_message ? `<div class="backup-error">${backup.error_message}</div>` : ''}
                </div>
                <div class="backup-actions">
                    ${backup.status === 'available' ? `
                        <button class="btn btn-sm btn-secondary" onclick="restoreBackup('${appId}', ${backup.id})" title="Restore from this backup">
                            <i data-lucide="rotate-ccw"></i>
                            Restore
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-danger" onclick="deleteBackup('${appId}', ${backup.id})" title="Delete this backup">
                        <i data-lucide="trash-2"></i>
                        Delete
                    </button>
                </div>
            </div>
        `).join('');

        // Refresh icons
        lucide.createIcons();

        // Start polling if there are creating backups
        const creatingBackups = backups.filter(b => b.status === 'creating');
        if (creatingBackups.length > 0) {
            startBackupPolling(appId);
        }

    } catch (error) {
        showNotification('Failed to load backups', 'error');
        console.error('Error loading backups:', error);
    }
}

/**
 * Create a new backup
 */
async function createBackup() {
    if (!currentBackupAppId) return;

    try {
        showNotification('Creating backup...', 'info');

        await authFetch(`${API_BASE}/apps/${currentBackupAppId}/backups`, {
            method: 'POST',
            body: JSON.stringify({
                storage: 'local',
                compress: 'zstd',
                mode: 'snapshot'
            })
        });

        showNotification('Backup creation started', 'success');

        // Reload backups
        await loadBackups(currentBackupAppId);

    } catch (error) {
        showNotification('Failed to create backup', 'error');
        console.error('Error creating backup:', error);
    }
}

/**
 * Restore from backup
 */
async function restoreBackup(appId, backupId) {
    if (!confirm('Are you sure you want to restore from this backup? This will replace the current application state.')) {
        return;
    }

    try {
        showNotification('Restoring from backup...', 'info');

        await authFetch(`${API_BASE}/apps/${appId}/backups/${backupId}/restore`, {
            method: 'POST'
        });

        showNotification('Restore completed successfully', 'success');
        hideBackupModal();

        // Refresh app list
        await loadApps();

    } catch (error) {
        showNotification('Failed to restore backup', 'error');
        console.error('Error restoring backup:', error);
    }
}

/**
 * Delete a backup
 */
async function deleteBackup(appId, backupId) {
    if (!confirm('Are you sure you want to delete this backup? This action cannot be undone.')) {
        return;
    }

    try {
        await authFetch(`${API_BASE}/apps/${appId}/backups/${backupId}`, {
            method: 'DELETE'
        });

        showNotification('Backup deleted successfully', 'success');

        // Reload backups
        await loadBackups(appId);

    } catch (error) {
        showNotification('Failed to delete backup', 'error');
        console.error('Error deleting backup:', error);
    }
}

/**
 * Refresh backups list
 */
async function refreshBackups() {
    if (!currentBackupAppId) return;
    
    showNotification('Refreshing backups...', 'info');
    await loadBackups(currentBackupAppId);
    showNotification('Backups refreshed', 'success');
}

/**
 * Start polling for backup completion
 */
function startBackupPolling(appId) {
    // Clear existing interval
    if (backupPollingInterval) {
        clearInterval(backupPollingInterval);
    }

    // Poll every 5 seconds
    backupPollingInterval = setInterval(async () => {
        if (currentBackupAppId === appId) {
            await loadBackups(appId);
        } else {
            clearInterval(backupPollingInterval);
            backupPollingInterval = null;
        }
    }, 5000);
}

/**
 * Format backup size
 */
function formatSize(bytes) {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
}

/**
 * Get status icon
 */
function getStatusIcon(status) {
    const icons = {
        'creating': '<i data-lucide="loader" class="spin"></i>',
        'available': '<i data-lucide="check-circle"></i>',
        'failed': '<i data-lucide="x-circle"></i>',
        'restoring': '<i data-lucide="rotate-cw" class="spin"></i>'
    };
    return icons[status] || '';
}

// ============================================================================
// FEARLESS UPDATE WORKFLOW
// ============================================================================

let updateStatusInterval = null;

/**
 * Show update confirmation modal
 */
async function showUpdateModal(appId) {
    try {
        // Get app details
        const app = await authFetch(`${API_BASE}/apps/${appId}`);

        const confirmed = confirm(
            `Update ${app.name}?\n\n` +
            `✅ A safety backup will be automatically created before starting\n` +
            `⏸️  The application will be briefly unavailable during the process\n` +
            `🔄 Latest images will be pulled and containers recreated\n` +
            `🏥 Health check will verify the update\n\n` +
            `Continue with update?`
        );

        if (confirmed) {
            await performUpdate(appId, app.name);
        }
    } catch (error) {
        showNotification('Failed to load app details', 'error');
        console.error('Error showing update modal:', error);
    }
}

/**
 * Perform the update with status feedback
 */
async function performUpdate(appId, appName) {
    // Create progress notification
    const progressSteps = [
        { icon: 'database', text: 'Creating safety backup...', status: 'in-progress' },
        { icon: 'download', text: 'Pulling new images...', status: 'pending' },
        { icon: 'refresh-cw', text: 'Restarting application...', status: 'pending' },
        { icon: 'activity', text: 'Verifying health...', status: 'pending' }
    ];

    let currentStep = 0;

    // Show initial notification
    showUpdateProgress(progressSteps, currentStep);

    try {
        // Start the update
        const response = await authFetch(`${API_BASE}/apps/${appId}/update`, {
            method: 'POST'
        });

        // Poll app status and update progress based on actual status
        const progressInterval = setInterval(async () => {
            try {
                const app = await authFetch(`${API_BASE}/apps/${appId}`);
                
                // Update progress based on actual app status
                if (app.status === 'updating') {
                    // Still updating - cycle through steps based on elapsed time
                    currentStep = Math.min(currentStep + 1, progressSteps.length - 1);
                    if (currentStep > 0) {
                        progressSteps[currentStep - 1].status = 'completed';
                    }
                    progressSteps[currentStep].status = 'in-progress';
                    showUpdateProgress(progressSteps, currentStep);
                } else if (app.status === 'running') {
                    // Update completed successfully
                    clearInterval(progressInterval);
                } else if (app.status === 'update_failed') {
                    // Update failed
                    clearInterval(progressInterval);
                }
            } catch (pollError) {
                console.warn('Status poll error:', pollError);
            }
        }, 5000); // Check every 5 seconds

        // Wait for update to complete (poll app status)
        // Timeout increased to 7 minutes to accommodate:
        // - Backup: up to 5 min
        // - Image pull: 2-3 min
        // - Service restart: 30s
        // - Health check: 50s
        await pollAppStatus(appId, 'running', 420000); // 7 minute timeout

        clearInterval(progressInterval);

        // Mark all as completed
        progressSteps.forEach(step => step.status = 'completed');
        showUpdateProgress(progressSteps, progressSteps.length);

        setTimeout(() => {
            showNotification(`✅ ${appName} updated successfully!`, 'success');
            loadApps(); // Refresh app list
        }, 1000);

    } catch (error) {
        // Provide more specific error messages
        let errorMessage = 'Update failed';
        
        if (error.message.includes('timeout')) {
            errorMessage = '⏱️ Update timeout - The update is taking longer than expected. Please check the app status in a few minutes or review the logs.';
        } else if (error.message.includes('Health check failed')) {
            errorMessage = '❌ Update failed: Application health check failed after restart. The app may need manual intervention.';
        } else if (error.message.includes('backup')) {
            errorMessage = '❌ Update aborted: Pre-update backup failed. Your app is safe and unchanged.';
        } else if (error.message) {
            errorMessage = `❌ Update failed: ${error.message}`;
        }
        
        showNotification(errorMessage, 'error');
        console.error('Update error:', error);

        // Reload apps to show current state
        loadApps();
    }
}

/**
 * Show update progress notification
 */
function showUpdateProgress(steps, currentStep) {
    const stepsHtml = steps.map((step, index) => {
        let statusIcon = '';
        let statusClass = '';

        if (step.status === 'completed') {
            statusIcon = '<i data-lucide="check-circle" class="text-success"></i>';
            statusClass = 'completed';
        } else if (step.status === 'in-progress') {
            statusIcon = '<i data-lucide="loader" class="spin"></i>';
            statusClass = 'in-progress';
        } else {
            statusIcon = '<i data-lucide="circle" class="text-muted"></i>';
            statusClass = 'pending';
        }

        return `
            <div class="update-step ${statusClass}">
                ${statusIcon}
                <span>${step.text}</span>
            </div>
        `;
    }).join('');

    const container = document.getElementById('notification-container') || createNotificationContainer();

    const existingUpdate = document.querySelector('.update-progress-notification');
    if (existingUpdate) {
        existingUpdate.innerHTML = `
            <div class="notification-header">
                <i data-lucide="refresh-cw"></i>
                <span>Updating Application</span>
            </div>
            <div class="update-steps">
                ${stepsHtml}
            </div>
        `;
        lucide.createIcons();
    } else {
        const notification = document.createElement('div');
        notification.className = 'notification info update-progress-notification';
        notification.innerHTML = `
            <div class="notification-header">
                <i data-lucide="refresh-cw"></i>
                <span>Updating Application</span>
            </div>
            <div class="update-steps">
                ${stepsHtml}
            </div>
        `;
        container.appendChild(notification);
        lucide.createIcons();
    }
}

/**
 * Create notification container if it doesn't exist
 */
function createNotificationContainer() {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Poll app status until it reaches expected status
 */
async function pollAppStatus(appId, expectedStatus, timeout = 60000) {
    const startTime = Date.now();
    const pollInterval = 2000; // 2 seconds

    while (Date.now() - startTime < timeout) {
        try {
            const app = await authFetch(`${API_BASE}/apps/${appId}`);

            if (app.status === expectedStatus) {
                return app;
            }

            if (app.status === 'update_failed') {
                throw new Error('Update failed - check logs for details');
            }

            await new Promise(resolve => setTimeout(resolve, pollInterval));
        } catch (error) {
            if (Date.now() - startTime >= timeout) {
                throw new Error('Update timeout - The operation is taking longer than expected. The update may still be in progress. Please refresh the page and check the app status.');
            }
            // Continue polling on errors
            await new Promise(resolve => setTimeout(resolve, pollInterval));
        }
    }

    throw new Error('Update timeout - The operation exceeded the maximum time limit. Please check the app status and logs.');
}

// ============================================================================
// VOLUME MANAGEMENT
// ============================================================================

/**
 * Show volumes for an app
 */
async function showAppVolumes(appId) {
    try {
        const app = await authFetch(`${API_BASE}/apps/${appId}`);

        if (!app.volumes || app.volumes.length === 0) {
            showNotification('This app has no persistent volumes', 'info');
            return;
        }

        const volumesHtml = app.volumes.map(vol => `
            <tr>
                <td>${vol.container_path}</td>
                <td class="volume-host-path">
                    <code>${vol.host_path}</code>
                    <button class="btn btn-sm btn-ghost" onclick="copyToClipboard('${vol.host_path}')" title="Copy to clipboard">
                        <i data-lucide="copy"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        const modalBody = `
            <div class="volumes-info">
                <p class="help-text">
                    <i data-lucide="info"></i>
                    These are the locations on your Proxmox server where persistent data is stored.
                    <strong>Do not modify these files directly unless you know what you are doing.</strong>
                </p>
                <table class="volumes-table">
                    <thead>
                        <tr>
                            <th>Container Path</th>
                            <th>Host Path (Proxmox)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${volumesHtml}
                    </tbody>
                </table>
            </div>
        `;

        showModal('Persistent Volumes', modalBody);
        lucide.createIcons();

    } catch (error) {
        showNotification('Failed to load volumes', 'error');
        console.error('Error loading volumes:', error);
    }
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    }).catch(err => {
        showNotification('Failed to copy', 'error');
        console.error('Clipboard error:', err);
    });
}

// ============================================================================
// MONITORING - At-a-Glance Resource Usage
// ============================================================================

/**
 * Global monitoring state
 */
let monitoringState = {
    activeAppId: null,
    pollInterval: null,
    POLL_INTERVAL_MS: 5000  // Poll every 5 seconds when viewing
};

/**
 * Show monitoring modal with real-time resource usage gauges.
 *
 * Performance Design:
 * - Polling ONLY active when modal is open
 * - Automatic cleanup on modal close prevents resource leaks
 * - Cache-backed API ensures scalability
 */
async function showMonitoringModal(appId, appName) {
    const modalBody = `
        <div class="monitoring-container">
            <div class="monitoring-header">
                <i data-lucide="activity" style="width: 24px; height: 24px; color: var(--primary);"></i>
                <div>
                    <h3 style="margin: 0; color: var(--text-primary);">Resource Monitoring</h3>
                    <p style="margin: 0.25rem 0 0 0; color: var(--text-secondary); font-size: 0.875rem;">
                        Real-time container metrics
                    </p>
                </div>
            </div>

            <!-- Status -->
            <div class="monitoring-status" id="monitoring-status">
                <div class="status-indicator status-unknown">
                    <span class="status-dot"></span>
                    <span id="status-text">Loading...</span>
                </div>
                <div class="monitoring-meta">
                    <span id="uptime-text">--</span>
                    <span class="meta-separator">•</span>
                    <span id="timestamp-text">Never updated</span>
                </div>
            </div>

            <!-- Gauges Grid -->
            <div class="monitoring-gauges">
                <!-- CPU Gauge -->
                <div class="gauge-card">
                    <div class="gauge-header">
                        <i data-lucide="cpu" class="gauge-icon"></i>
                        <span class="gauge-title">CPU Usage</span>
                    </div>
                    <div class="gauge-value" id="cpu-value">--%</div>
                    <div class="gauge-bar-container">
                        <div class="gauge-bar" id="cpu-bar" style="width: 0%;"></div>
                    </div>
                    <div class="gauge-label">Processor Load</div>
                </div>

                <!-- Memory Gauge -->
                <div class="gauge-card">
                    <div class="gauge-header">
                        <i data-lucide="database" class="gauge-icon"></i>
                        <span class="gauge-title">Memory Usage</span>
                    </div>
                    <div class="gauge-value" id="mem-value">--%</div>
                    <div class="gauge-bar-container">
                        <div class="gauge-bar" id="mem-bar" style="width: 0%;"></div>
                    </div>
                    <div class="gauge-label" id="mem-label">-- GB / -- GB</div>
                </div>

                <!-- Disk Gauge -->
                <div class="gauge-card">
                    <div class="gauge-header">
                        <i data-lucide="hard-drive" class="gauge-icon"></i>
                        <span class="gauge-title">Disk Usage</span>
                    </div>
                    <div class="gauge-value" id="disk-value">--%</div>
                    <div class="gauge-bar-container">
                        <div class="gauge-bar" id="disk-bar" style="width: 0%;"></div>
                    </div>
                    <div class="gauge-label" id="disk-label">-- GB / -- GB</div>
                </div>
            </div>

            <!-- Cache Indicator -->
            <div class="monitoring-footer">
                <div class="cache-indicator" id="cache-indicator">
                    <i data-lucide="zap" style="width: 14px; height: 14px;"></i>
                    <span id="cache-text">--</span>
                </div>
            </div>
        </div>
    `;

    showModal('Monitoring: ' + appName, modalBody);

    // Initialize Lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // Start monitoring
    monitoringState.activeAppId = appId;
    startMonitoringPolling(appId);

    // Setup cleanup on modal close
    const modal = document.querySelector('.modal');
    const closeHandler = () => {
        stopMonitoringPolling();
        modal.removeEventListener('click', closeHandler);
    };

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeHandler();
        }
    });

    // Close on close button
    const closeButton = modal.querySelector('.modal-close, .btn-ghost');
    if (closeButton) {
        closeButton.addEventListener('click', closeHandler, { once: true });
    }
}

/**
 * Start polling for monitoring data.
 * CRITICAL: Only poll when user is viewing the monitoring modal.
 */
function startMonitoringPolling(appId) {
    // Clear any existing interval
    stopMonitoringPolling();

    // Immediate first fetch
    updateMonitoringData(appId);

    // Setup polling
    monitoringState.pollInterval = setInterval(() => {
        updateMonitoringData(appId);
    }, monitoringState.POLL_INTERVAL_MS);

    console.log(`📊 Started monitoring polling for app ${appId} (interval: ${monitoringState.POLL_INTERVAL_MS}ms)`);
}

/**
 * Stop polling for monitoring data.
 * CRITICAL: Must be called when modal closes to prevent resource leaks.
 */
function stopMonitoringPolling() {
    if (monitoringState.pollInterval) {
        clearInterval(monitoringState.pollInterval);
        monitoringState.pollInterval = null;
        console.log('📊 Stopped monitoring polling');
    }
    monitoringState.activeAppId = null;
}

/**
 * Fetch and display monitoring data.
 */
async function updateMonitoringData(appId) {
    try {
        const response = await authFetch(`${API_BASE}/apps/${appId}/stats/current`);

        if (!response.ok) {
            throw new Error('Failed to fetch stats');
        }

        const stats = await response.json();

        // Update status
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.getElementById('status-text');

        if (statusIndicator && statusText) {
            statusIndicator.className = `status-indicator status-${stats.status}`;
            statusText.textContent = stats.status.charAt(0).toUpperCase() + stats.status.slice(1);
        }

        // Update uptime
        const uptimeText = document.getElementById('uptime-text');
        if (uptimeText) {
            uptimeText.textContent = formatUptime(stats.uptime_seconds);
        }

        // Update timestamp
        const timestampText = document.getElementById('timestamp-text');
        if (timestampText) {
            const updateTime = new Date(stats.timestamp);
            const now = new Date();
            const secondsAgo = Math.floor((now - updateTime) / 1000);
            timestampText.textContent = secondsAgo < 2 ? 'Just now' : `${secondsAgo}s ago`;
        }

        // Update CPU
        updateGauge('cpu', stats.cpu_percent, '%');

        // Update Memory
        updateGauge('mem', stats.mem_percent, '%');
        const memLabel = document.getElementById('mem-label');
        if (memLabel) {
            memLabel.textContent = `${stats.mem_used_gb} GB / ${stats.mem_total_gb} GB`;
        }

        // Update Disk
        updateGauge('disk', stats.disk_percent, '%');
        const diskLabel = document.getElementById('disk-label');
        if (diskLabel) {
            diskLabel.textContent = `${stats.disk_used_gb} GB / ${stats.disk_total_gb} GB`;
        }

        // Update cache indicator
        const cacheIndicator = document.getElementById('cache-indicator');
        const cacheText = document.getElementById('cache-text');
        if (cacheIndicator && cacheText) {
            if (stats.cached) {
                cacheIndicator.classList.add('cached');
                cacheText.textContent = 'Cached data';
            } else {
                cacheIndicator.classList.remove('cached');
                cacheText.textContent = 'Live data';
            }
        }

    } catch (error) {
        console.error('Failed to update monitoring data:', error);

        // Show error state
        const statusText = document.getElementById('status-text');
        if (statusText) {
            statusText.textContent = 'Error fetching stats';
        }
    }
}

/**
 * Update a gauge element with new value.
 */
function updateGauge(gaugeId, percent, suffix = '%') {
    const valueElement = document.getElementById(`${gaugeId}-value`);
    const barElement = document.getElementById(`${gaugeId}-bar`);

    if (!valueElement || !barElement) return;

    // Update value text
    valueElement.textContent = `${percent.toFixed(1)}${suffix}`;

    // Update bar width
    barElement.style.width = `${Math.min(percent, 100)}%`;

    // Update bar color based on thresholds
    barElement.className = 'gauge-bar';
    if (percent >= 90) {
        barElement.classList.add('gauge-critical');
    } else if (percent >= 75) {
        barElement.classList.add('gauge-warning');
    } else {
        barElement.classList.add('gauge-ok');
    }
}

/**
 * Format uptime seconds to human-readable string.
 */
function formatUptime(seconds) {
    if (!seconds || seconds < 0) return '--';

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
        return `${days}d ${hours}h`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}
// ==================== In-App Canvas Modal ====================

let currentCanvasApp = null;

/**
 * Open an application in the in-app canvas modal
 * @param {Object} app - App object with iframe_url
 */
function openCanvas(app) {
    if (!app.iframe_url) {
        showNotification('Canvas URL not available for this app', 'error');
        return;
    }
    
    currentCanvasApp = app;
    
    const modal = document.getElementById('canvasModal');
    const appName = document.getElementById('canvasAppName');
    const iframe = document.getElementById('canvasIframe');
    const loading = document.getElementById('canvasLoading');
    const error = document.getElementById('canvasError');
    
    // Set app name
    appName.textContent = app.name || app.hostname;
    
    // Reset state
    iframe.classList.add('hidden');
    error.classList.add('hidden');
    loading.classList.remove('hidden');
    
    // Reset iframe completely before loading new content
    iframe.src = 'about:blank';
    
    // Wait a moment then load the actual URL
    setTimeout(() => {
        // Show modal
        modal.classList.add('show');
        document.body.classList.add('modal-open');
        
        // Load iframe with the app URL
        iframe.src = app.iframe_url;
    }, 50);
    
    // Handle iframe load events
    const onLoad = () => {
        loading.classList.add('hidden');
        iframe.classList.remove('hidden');
        
        // Try to inject CSS reset if same-origin (will fail silently for cross-origin)
        try {
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            if (iframeDoc && iframeDoc.body) {
                // Inject CSS reset into iframe to prevent parent styles from leaking
                const style = iframeDoc.createElement('style');
                style.textContent = `
                    /* Reset any inherited styles from parent */
                    html, body {
                        margin: 0 !important;
                        padding: 0 !important;
                        width: 100% !important;
                        height: 100% !important;
                        overflow: auto !important;
                        box-sizing: border-box !important;
                    }
                    body {
                        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                    }
                `;
                iframeDoc.head.appendChild(style);
            }
        } catch (e) {
            // Cross-origin - can't access iframe content, which is fine
            console.log('[Canvas] Cross-origin iframe - CSS reset not applied (expected)');
        }
        
        iframe.removeEventListener('load', onLoad);
        iframe.removeEventListener('error', onError);
    };
    
    const onError = () => {
        loading.classList.add('hidden');
        error.classList.remove('hidden');
        document.getElementById('canvasErrorMessage').textContent = 
            `Unable to load ${app.name}. The application may not support iframe embedding.`;
        iframe.removeEventListener('load', onLoad);
        iframe.removeEventListener('error', onError);
    };
    
    // Set timeout for load detection
    const timeout = setTimeout(() => {
        if (!iframe.classList.contains('hidden')) return; // Already loaded
        // Check if iframe is accessible
        try {
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            if (iframeDoc.readyState === 'complete') {
                onLoad();
            }
        } catch (e) {
            // Cross-origin frame - assume it loaded successfully if no error
            onLoad();
        }
    }, 10000); // 10 second timeout
    
    iframe.addEventListener('load', () => {
        clearTimeout(timeout);
        onLoad();
    });
    
    iframe.addEventListener('error', () => {
        clearTimeout(timeout);
        onError();
    });
    
    // Reinitialize icons
    initLucideIcons();
}

/**
 * Close the canvas modal
 */
function closeCanvas() {
    const modal = document.getElementById('canvasModal');
    const iframe = document.getElementById('canvasIframe');
    const header = document.querySelector('.canvas-modal-header');
    
    // Reset header state
    if (header) {
        header.classList.remove('minimized');
    }
    
    // Hide modal
    modal.classList.remove('show');
    document.body.classList.remove('modal-open');
    
    // Clear iframe after animation
    setTimeout(() => {
        iframe.src = '';
        currentCanvasApp = null;
    }, 300);
}

/**
 * Toggle canvas header between minimized and normal state
 */
function toggleCanvasHeader() {
    const header = document.querySelector('.canvas-modal-header');
    const icon = document.getElementById('canvasHeaderToggleIcon');
    
    if (header && icon) {
        const isMinimized = header.classList.toggle('minimized');
        
        // Update icon
        if (isMinimized) {
            icon.setAttribute('data-lucide', 'maximize-2');
        } else {
            icon.setAttribute('data-lucide', 'minimize-2');
        }
        
        // Reinitialize icons
        lucide.createIcons();
    }
}

/**
 * Refresh the canvas iframe
 */
function refreshCanvas() {
    if (!currentCanvasApp || !currentCanvasApp.iframe_url) return;
    
    const iframe = document.getElementById('canvasIframe');
    const loading = document.getElementById('canvasLoading');
    const error = document.getElementById('canvasError');
    
    // Show loading state
    iframe.classList.add('hidden');
    error.classList.add('hidden');
    loading.classList.remove('hidden');
    
    // Reload iframe
    iframe.src = currentCanvasApp.iframe_url;
}

/**
 * Open current canvas app in new tab
 */
function openInNewTab() {
    if (!currentCanvasApp) return;
    
    // Prefer public URL over iframe URL
    const url = currentCanvasApp.url || currentCanvasApp.iframe_url;
    if (url) {
        window.open(url, '_blank');
    }
}

/**
 * Add canvas button to app cards
 */
function addCanvasButton(app, container) {
    if (!app.iframe_url) return; // No canvas URL available
    
    const button = document.createElement('button');
    button.className = 'btn btn-secondary';
    button.innerHTML = '<i data-lucide="monitor"></i><span>Canvas</span>';
    button.onclick = (e) => {
        e.stopPropagation();
        openCanvas(app);
    };
    
    container.appendChild(button);
    initLucideIcons();
}

/**
 * Show clone app modal
 */
async function showCloneModal(appId, appName) {
    const hostname = await showPromptModal(
        'Clone Application',
        `Enter a new hostname for the cloned copy of "${appName}":`,
        '',
        'Clone',
        'clone-hostname'
    );

    if (!hostname) return;

    try {
        showNotification(`Cloning ${appName}...`, 'info');

        const response = await fetch(`/api/v1/apps/${appId}/clone?new_hostname=${encodeURIComponent(hostname)}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Clone failed');
        }

        const clonedApp = await response.json();

        showNotification(`✓ Successfully cloned to ${hostname}`, 'success');

        // Refresh apps view
        if (currentView === 'apps') {
            await loadApps();
        }

    } catch (error) {
        console.error('Clone error:', error);
        showNotification(`Failed to clone: ${error.message}`, 'error');
    }
}

/**
 * Show edit config modal
 */
async function showEditConfigModal(appId, appName) {
    // Create modal HTML
    const modalHTML = `
        <div class="modal-overlay" id="editConfigOverlay">
            <div class="modal-dialog">
                <div class="modal-header">
                    <h2>Edit Resources: ${appName}</h2>
                    <button class="modal-close" onclick="closeEditConfigModal()">✕</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="editCpu">CPU Cores (1-16)</label>
                        <input type="number" id="editCpu" min="1" max="16" step="1"
                               placeholder="Leave empty to keep current">
                    </div>
                    <div class="form-group">
                        <label for="editMemory">Memory (MB) (512-32768)</label>
                        <input type="number" id="editMemory" min="512" max="32768" step="512"
                               placeholder="Leave empty to keep current">
                    </div>
                    <div class="form-group">
                        <label for="editDisk">Disk Size (GB) (1-500)</label>
                        <input type="number" id="editDisk" min="1" max="500" step="1"
                               placeholder="Leave empty to keep current">
                        <small class="form-help">⚠️ Disk can only be increased, not decreased</small>
                    </div>
                    <div class="alert alert-warning">
                        <strong>Note:</strong> The application will be restarted to apply changes.
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeEditConfigModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="submitEditConfig('${appId}', '${appName}')">
                        Apply Changes
                    </button>
                </div>
            </div>
        </div>
    `;

    // Add to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Focus first input
    setTimeout(() => document.getElementById('editCpu')?.focus(), 100);
}

/**
 * Close edit config modal
 */
function closeEditConfigModal() {
    const overlay = document.getElementById('editConfigOverlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Submit config update
 */
async function submitEditConfig(appId, appName) {
    const cpuCores = document.getElementById('editCpu')?.value;
    const memoryMb = document.getElementById('editMemory')?.value;
    const diskGb = document.getElementById('editDisk')?.value;

    // Validate at least one field is set
    if (!cpuCores && !memoryMb && !diskGb) {
        showNotification('Please specify at least one resource to update', 'warning');
        return;
    }

    try {
        closeEditConfigModal();
        showNotification(`Updating resources for ${appName}...`, 'info');

        // Build query params
        const params = new URLSearchParams();
        if (cpuCores) params.append('cpu_cores', cpuCores);
        if (memoryMb) params.append('memory_mb', memoryMb);
        if (diskGb) params.append('disk_gb', diskGb);

        const response = await fetch(`/api/v1/apps/${appId}/config?${params.toString()}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Config update failed');
        }

        showNotification(`✓ Resources updated successfully`, 'success');

        // Refresh apps view
        if (currentView === 'apps') {
            await loadApps();
        }

    } catch (error) {
        console.error('Config update error:', error);
        showNotification(`Failed to update config: ${error.message}`, 'error');
    }
}

/**
 * Show prompt modal for text input
 */
function showPromptModal(title, message, defaultValue = '', confirmText = 'OK', inputId = 'promptInput') {
    return new Promise((resolve) => {
        const modalHTML = `
            <div class="modal-overlay" id="promptOverlay">
                <div class="modal-dialog">
                    <div class="modal-header">
                        <h2>${title}</h2>
                        <button class="modal-close" onclick="document.getElementById('promptOverlay').remove(); window.promptResolve(null);">✕</button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                        <input type="text" id="${inputId}" class="form-control" value="${defaultValue}"
                               onkeypress="if(event.key==='Enter') document.getElementById('promptConfirm').click()">
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="document.getElementById('promptOverlay').remove(); window.promptResolve(null);">
                            Cancel
                        </button>
                        <button id="promptConfirm" class="btn btn-primary" onclick="
                            const val = document.getElementById('${inputId}').value.trim();
                            document.getElementById('promptOverlay').remove();
                            window.promptResolve(val);
                        ">${confirmText}</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        window.promptResolve = resolve;

        setTimeout(() => {
            const input = document.getElementById(inputId);
            if (input) {
                input.focus();
                input.select();
            }
        }, 100);
    });
}

// Close canvas modal when clicking outside
document.getElementById('canvasModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'canvasModal') {
        closeCanvas();
    }
});

// Close canvas modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('canvasModal')?.classList.contains('show')) {
        closeCanvas();
    }
});

// Helper function to get icon for category
function getCategoryIcon(category) {
    const icons = {
        'Development': 'code',
        'Database': 'database',
        'Web Server': 'globe',
        'Monitoring': 'activity',
        'CMS': 'file-text',
        'E-Commerce': 'shopping-cart',
        'Communication': 'message-circle',
        'Media': 'play-circle',
        'Storage': 'hard-drive',
        'Security': 'shield',
        'Networking': 'network',
        'Automation': 'zap'
    };
    return icons[category] || 'box';
}
