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
// MIGRATION NOTE: State is now managed by the modular system (js/state/appState.js)
// We keep this for backward compatibility during the transition period.
// The modular system will override window.state when it loads.
const state = {
    systemInfo: null,
    nodes: [],
    apps: [],
    catalog: null,
    currentView: 'dashboard',
    deployedApps: [],
    proximityMode: 'AUTO', // AUTO or PRO mode
    cpuPollingInterval: null // Store polling interval ID
};

// Expose state globally for modular views
// NOTE: This will be overridden by js/state/appState.js when the modular system loads
window.state = state;

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
    console.log('🚀 Loading deployed apps...');
    try {
        const response = await authFetch(`${API_BASE}/apps`);
        if (!response.ok) {
            console.error(`❌ Failed to load apps: ${response.status} ${response.statusText}`);
            throw new Error('Failed to load apps');
        }
        state.deployedApps = await response.json();
        
        console.log(`✅ Deployed apps loaded: ${state.deployedApps.length} apps`);
        
        // Enrich deployed apps with icon URLs from catalog
        enrichDeployedAppsWithIcons();
    } catch (error) {
        console.error('❌ Error loading deployed apps:', error);
        state.deployedApps = [];
    }
}

async function loadCatalog() {
    console.log('📚 Loading catalog...');
    try {
        const response = await authFetch(`${API_BASE}/apps/catalog`);
        if (!response.ok) {
            console.warn(`⚠️  Failed to load catalog: ${response.status} ${response.statusText}`);
            state.catalog = { items: [], categories: [] };
            return;
        }
        state.catalog = await response.json();
        console.log(`✅ Catalog loaded: ${state.catalog.items?.length || 0} items`);
        
        // Enrich deployed apps with icon URLs after catalog is loaded
        enrichDeployedAppsWithIcons();
    } catch (error) {
        console.error('❌ Error loading catalog:', error);
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
    // Update navigation badge
    updateAppsCount();
    
    // DEPRECATED: Dashboard stats are now updated by DashboardView.js component
    // The Router-based lifecycle system automatically calls DashboardView.updateHeroStats()
    // and DashboardView.updateRecentApps() when the dashboard is mounted and on refresh intervals.
    // Keeping the old functions below for backward compatibility until full migration.
}

// DELETED: updateStats(), updateHeroStats(), oldUpdateStats() - Fully migrated to js/views/DashboardView.js
//          DashboardView component handles all dashboard stats via mount() and auto-refresh.
//          These 3 functions (62 lines total) are now obsolete.

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

// DELETED: updateRecentApps() - Fully migrated to js/views/DashboardView.js (90 lines)
//          DashboardView.updateRecentApps() is called in mount() and auto-refreshes every 30 seconds.
//          This duplicate implementation is now obsolete.

// ============================================
// View Management
function showView(viewName) {
    console.log(`👁️  showView('${viewName}') called`);
    
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
        console.log(`✓ View '${viewName}' is now visible`);

        // Stop CPU polling when leaving apps view
        if (viewName !== 'apps') {
            stopCPUPolling();
        }

        // Load view content
        switch(viewName) {
            case 'dashboard':
                // MIGRATED: Use new router for dashboard view
                if (window.ProximityRouter) {
                    console.log('🌉 Routing dashboard view through new router');
                    window.ProximityRouter.navigateTo('dashboard');
                    return; // Early return to prevent double rendering
                }
                // Fallback for transition period
                console.log('✓ Dashboard view shown (fallback)');
                break;
            case 'apps':
                // MIGRATED: Use new router for apps view
                if (window.ProximityRouter) {
                    console.log('🌉 Routing apps view through new router');
                    window.ProximityRouter.navigateTo('apps');
                    return; // Early return to prevent double rendering
                }
                // Fallback for transition period
                renderAppsView();
                startCPUPolling();
                break;
            case 'catalog':
                // MIGRATED: Use new router for catalog view
                if (window.ProximityRouter) {
                    console.log('🌉 Routing catalog view through new router');
                    window.ProximityRouter.navigateTo('catalog');
                    return; // Early return to prevent double rendering
                }
                // Fallback for transition period
                renderCatalogView();
                break;
            case 'nodes':
                // MIGRATED: Use new router for nodes view
                if (window.ProximityRouter) {
                    console.log('🌉 Routing nodes view through new router');
                    window.ProximityRouter.navigateTo('nodes');
                    return;
                }
                renderNodesView();
                break;
            case 'monitoring':
                // MIGRATED: Use new router for monitoring view
                if (window.ProximityRouter) {
                    console.log('🌉 Routing monitoring view through new router');
                    window.ProximityRouter.navigateTo('monitoring');
                    return;
                }
                renderMonitoringView();
                break;
            case 'settings':
                // MIGRATED: Use new router for settings view
                if (window.ProximityRouter) {
                    console.log('🌉 Routing settings view through new router');
                    window.ProximityRouter.navigateTo('settings');
                    return;
                }
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

// ⚠️ DEPRECATED: Legacy view rendering and utility functions
// ⚠️ These are kept only for transition fallback if router fails
// ⚠️ TODO: Remove entirely once router is stable

function renderAppsView() {
    console.warn('⚠️ DEPRECATED: renderAppsView() - Use ProximityRouter instead');
    if (window.ProximityRouter) {
        window.ProximityRouter.navigateTo('apps');
    }
}

function renderCatalogView() {
    console.warn('⚠️ DEPRECATED: renderCatalogView() - Use ProximityRouter instead');
    if (window.ProximityRouter) {
        window.ProximityRouter.navigateTo('catalog');
    }
}

// Stub for backward compatibility - actual polling is handled by AppsView
function stopCPUPolling() {
    console.warn('⚠️ DEPRECATED: stopCPUPolling() - Handled by AppsView unmount()');
}

// ⚠️ Utility function stubs for backward compatibility
// These forward to the new modular utilities
// TODO: Migrate these call sites to import directly from the modules

// Import utility functions dynamically when needed
let _uiHelpers = null;
let _appCard = null;

async function _loadUtilities() {
    if (!_uiHelpers) {
        const module = await import('./js/utils/ui-helpers.js');
        _uiHelpers = module;
    }
    if (!_appCard) {
        const module = await import('./js/components/app-card.js');
        _appCard = module;
    }
}

// ⚠️ DEPRECATED: These functions have been moved to modular utilities
// They are kept here only as fallback stubs for any remaining legacy code
// TODO: Remove once all references are updated to use imports

function getAppIcon(name) {
    // Fallback stub - real implementation in js/utils/icons.js
    return window.Icons?.getAppIcon(name) || '📦';
}

function formatDate(dateString) {
    // Fallback stub - real implementation in js/utils/formatters.js
    return window.Formatters?.formatDate(dateString) || 'N/A';
}

function formatSize(bytes) {
    // Fallback stub - real implementation in js/utils/formatters.js
    return window.Formatters?.formatSize(bytes) || 'Unknown';
}

function formatUptime(seconds) {
    // Fallback stub - real implementation in js/utils/formatters.js
    return window.Formatters?.formatUptime(seconds) || '--';
}

function getStatusIcon(status) {
    // Fallback stub - real implementation in js/utils/icons.js
    return window.Icons?.getStatusIcon(status) || '';
}

function renderAppCard(app, container, isDeployed) {
    console.warn('⚠️ DEPRECATED: renderAppCard() in app.js - Use import from app-card.js');
    // Fallback - do nothing, router should handle rendering
}

// End Legacy View Functions

// DELETED: renderNodesView() - Fully migrated to js/views/NodesView.js (348 lines)
//          Router handles component lifecycle directly. This 282-line wrapper is obsolete.

// DELETED: renderMonitoringView() - Fully migrated to js/views/MonitoringView.js (233 lines)
//          Router handles component lifecycle directly. This 163-line wrapper is obsolete.

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
        <!-- Settings Sub-Navigation -->
        <div class="sub-nav">
            <button class="settings-tab sub-nav-item active" data-tab="proxmox">
                <i data-lucide="server"></i>
                <span>Proxmox</span>
            </button>
            <button class="settings-tab sub-nav-item" data-tab="network">
                <i data-lucide="network"></i>
                <span>Network</span>
            </button>
            <button class="settings-tab sub-nav-item" data-tab="resources">
                <i data-lucide="cpu"></i>
                <span>Resources</span>
            </button>
            <button class="settings-tab sub-nav-item" data-tab="system">
                <i data-lucide="info"></i>
                <span>System</span>
            </button>
        </div>

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

// DELETED: showAppDetails() - Migrated to js/services/appOperations.js
//          Exposed globally via main.js as window.showAppDetails

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

// DELETED: showDeletionProgress(), updateDeletionProgress(), hideDeletionProgress() - Migrated to js/services/appOperations.js (109 lines)
//          These three functions managed the deletion progress modal UI
//          Exposed globally via main.js as window.showDeletionProgress, window.updateDeletionProgress, window.hideDeletionProgress

// ⚠️ DEPRECATED: Moved to js/utils/formatters.js
function formatBytes(bytes) {
    // Fallback stub - real implementation in js/utils/formatters.js
    return window.Formatters?.formatBytes(bytes) || '0 B';
}

// ⚠️ DEPRECATED: Moved to js/utils/ui.js
function showLoading(text = 'Loading...') {
    // Fallback stub - real implementation in js/utils/ui.js
    if (window.UI?.showLoading) {
        window.UI.showLoading(text);
    }
}

function hideLoading() {
    // Fallback stub - real implementation in js/utils/ui.js
    if (window.UI?.hideLoading) {
        window.UI.hideLoading();
    }
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

// DELETED: Search & Filter Functions - Fully migrated to js/services/searchService.js (243 lines)
//          Functions deleted: filterApps, filterCatalog, _searchAppsInternal, searchApps, clearAppsSearch,
//                             _searchCatalogInternal, searchCatalog, clearCatalogSearch
//          All search/filter functionality now in searchService.js with debouncing and proper state management
//          Exposed globally via window.searchService (searchService.js handles this automatically)

// DELETED: showAppLogs() - Migrated to js/services/appOperations.js (45 lines)
//          Displays application logs in a modal with filtering and auto-refresh options
//          Exposed globally via main.js as window.showAppLogs

// DELETED: Settings Page Helper Functions (635 lines) - Fully migrated to js/utils/settingsHelpers.js
// Functions deleted: handleModeToggle, setupSettingsTabs, setupSettingsForms, setupAudioSettings, 
//                    saveProxmoxSettings, testProxmoxConnection, saveNetworkSettings, saveResourceSettings
// These functions are imported by SettingsView.js and exposed globally via main.js where needed

// Infrastructure Page Helpers

// Infrastructure Page Helpers
// DELETED: Infrastructure management functions (223 lines) - Migrated to js/utils/settingsHelpers.js
// refreshInfrastructure(), restartAppliance(), viewApplianceLogs(), testNAT()
// Now exposed globally via main.js (window.refreshInfrastructure, window.restartAppliance, etc.)

// ============================================================================
// AUTHENTICATION UI - PHASE C.3 MIGRATION (401 lines deleted)
// ============================================================================
// DELETED: All authentication UI functions migrated to js/components/auth-ui.js
// 
// Functions removed (10 total):
//   1. toggleUserMenu() - User profile menu toggle (18 lines)
//   2. showAuthModal() - Display register/login modal (32 lines)
//   3. closeAuthModal() - Close auth modal and restore state (19 lines)
//   4. renderAuthTabs() - Render register/login tabs (11 lines)
//   5. switchAuthTab() - Switch between tabs (8 lines)
//   6. renderRegisterForm() - Render registration form (21 lines)
//   7. renderLoginForm() - Render login form (18 lines)
//   8. handleRegisterSubmit() - Process registration (41 lines)
//   9. handleLoginSubmit() - Process login (31 lines)
//  10. initializeAuthenticatedSession() - Initialize auth flow (91 lines)
//
// Plus related event listeners and legacy patches (111 additional lines)
//
// All functions now:
//   - Imported in js/main.js from auth-ui.js
//   - Exposed globally via window.authUI and individual window.* properties
//   - Available as: window.showAuthModal, window.closeAuthModal, etc.
//   - Fully backward compatible with existing onclick handlers
//
// Migration stats: 401 lines deleted, zero syntax errors
// ============================================================================

// Event Listeners
// ⚠️ DEPRECATED: Moved to js/utils/ui.js
// User Menu Toggle

// ============================================================================
// VOLUME MANAGEMENT
// ============================================================================

// DELETED: showAppVolumes() - Migrated to js/services/appOperations.js (58 lines)
//          Displays application persistent volumes in a modal with host paths
//          Exposed globally via main.js as window.showAppVolumes

/**
 * ⚠️ DEPRECATED: Moved to js/utils/clipboard.js
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    // Fallback stub - real implementation in js/utils/clipboard.js
    if (window.Clipboard?.copyToClipboard) {
        window.Clipboard.copyToClipboard(text);
    } else {
        // Legacy fallback
        navigator.clipboard.writeText(text).then(() => {
            if (window.showNotification) {
                window.showNotification('Copied to clipboard!', 'success');
            }
        }).catch(err => {
            if (window.showNotification) {
                window.showNotification('Failed to copy', 'error');
            }
            console.error('Clipboard error:', err);
        });
    }
}


