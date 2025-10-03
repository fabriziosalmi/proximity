// Utility function to reinitialize Lucide icons
function initLucideIcons() {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

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
    
    if (toggleButton && sidebar) {
        // Load saved state
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
        }
        
        toggleButton.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            // Save state
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            // Reinitialize icons after toggle animation
            setTimeout(() => initLucideIcons(), 300);
        });
    }
}

// Proximity UI - State-of-the-Art Application Management Interface
const API_BASE = 'http://localhost:8765/api/v1';

// Application State
const state = {
    systemInfo: null,
    nodes: [],
    apps: [],
    catalog: null,
    currentView: 'dashboard',
    deployedApps: [],
    proxyStatus: null
};

// Initialize Application
async function init() {
    initSidebarToggle();
    console.log('🚀 Initializing Proximity UI...');
    
    showLoading('Connecting to Proximity API...');
    
    try {
        await Promise.all([
            loadSystemInfo(),
            loadNodes(),
            loadDeployedApps(),
            loadCatalog(),
            loadProxyStatus()
        ]);
        
        updateUI();
        setupEventListeners();
        hideLoading();
        
        // Initialize Lucide icons
        initLucideIcons();
        
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
        await loadProxyStatus();
        updateUI();
    }, 30000);
}

// API Calls
async function loadSystemInfo() {
    try {
        const response = await fetch(`${API_BASE}/system/info`);
        if (!response.ok) throw new Error('Failed to load system info');
        state.systemInfo = await response.json();
    } catch (error) {
        console.error('Error loading system info:', error);
        throw error;
    }
}

async function loadNodes() {
    try {
        const response = await fetch(`${API_BASE}/system/nodes`);
        if (!response.ok) throw new Error('Failed to load nodes');
        state.nodes = await response.json();
    } catch (error) {
        console.error('Error loading nodes:', error);
        throw error;
    }
}

async function loadDeployedApps() {
    try {
        const response = await fetch(`${API_BASE}/apps`);
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
        const response = await fetch(`${API_BASE}/apps/catalog`);
        if (!response.ok) throw new Error('Failed to load catalog');
        state.catalog = await response.json();
        
        // Enrich deployed apps with icon URLs after catalog is loaded
        enrichDeployedAppsWithIcons();
    } catch (error) {
        console.error('Error loading catalog:', error);
        throw error;
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

async function loadProxyStatus() {
    try {
        const response = await fetch(`${API_BASE}/system/proxy/status`);
        if (!response.ok) throw new Error('Failed to load proxy status');
        const result = await response.json();
        state.proxyStatus = result.data;
        console.log('Proxy status loaded:', state.proxyStatus);
    } catch (error) {
        console.error('Error loading proxy status:', error);
        state.proxyStatus = null;
    }
}

// UI Update Functions
function updateUI() {
    updateStats();
    updateAppsCount();
    updateRecentApps();
}

function updateStats() {
    // Update basic stats (only if systemInfo is available)
    if (state.systemInfo) {
        document.getElementById('statTotalApps').textContent = state.systemInfo.total_apps || 0;
        document.getElementById('statRunningApps').textContent = state.systemInfo.running_apps || 0;
        document.getElementById('statNodes').textContent = state.systemInfo.nodes?.length || 0;
        
        // Calculate resource usage
        if (state.systemInfo.nodes && state.systemInfo.nodes.length > 0) {
            const totalMem = state.systemInfo.nodes.reduce((sum, n) => sum + (n.maxmem || 0), 0);
            const usedMem = state.systemInfo.nodes.reduce((sum, n) => sum + (n.mem || 0), 0);
            const percentage = totalMem > 0 ? Math.round((usedMem / totalMem) * 100) : 0;
            document.getElementById('statResources').textContent = `${percentage}%`;
        }
    }
    
    // Update proxy status (independent of systemInfo)
    const proxyStatusEl = document.getElementById('statProxyStatus');
    const proxyInfoEl = document.getElementById('statProxyInfo');
    
    console.log('Updating proxy status UI, state.proxyStatus:', state.proxyStatus);
    
    if (state.proxyStatus && state.proxyStatus.deployed) {
        const status = state.proxyStatus.status;
        const appCount = state.proxyStatus.registered_apps || 0;
        
        proxyStatusEl.textContent = appCount;
        
        if (status === 'running') {
            proxyInfoEl.innerHTML = `
                <span>●</span>
                <span>${state.proxyStatus.ip_address || 'Active'}</span>
            `;
            proxyInfoEl.className = 'stat-change positive';
        } else {
            proxyInfoEl.innerHTML = `
                <span>●</span>
                <span>Offline</span>
            `;
            proxyInfoEl.className = 'stat-change';
        }
    } else {
        proxyStatusEl.textContent = '--';
        proxyInfoEl.innerHTML = `
            <span>●</span>
            <span>Not deployed</span>
        `;
        proxyInfoEl.className = 'stat-change';
    }
}

function updateAppsCount() {
    const count = state.deployedApps.length;
    document.getElementById('appsCount').textContent = count;
}

function updateRecentApps() {
    const container = document.getElementById('recentApps');
    
    if (state.deployedApps.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📦</div>
                <h3 class="empty-title">No applications yet</h3>
                <p class="empty-message">Deploy your first application from the catalog to get started.</p>
                <button class="btn btn-primary" onclick="showView('catalog')">Browse Catalog</button>
            </div>
        `;
        return;
    }
    
    // Show last 3 apps
    const recentApps = state.deployedApps.slice(-3).reverse();
    container.innerHTML = recentApps.map(app => createAppCard(app, true)).join('');
    
    // Reinitialize Lucide icons
    initLucideIcons();
}

function createAppCard(app, isDeployed = false) {
    // Get icon - prefer catalog icon, then auto-detect
    let icon = getAppIcon(app.name || app.id);
    let fallbackIcon = icon; // Store the fallback (emoji or SVG)
    
    // If app has custom icon URL from catalog (works for both deployed and catalog apps)
    if (app.icon) {
        // Properly escape the fallback for use in HTML attribute
        const escapedFallback = typeof fallbackIcon === 'string' ? fallbackIcon.replace(/'/g, "&#39;").replace(/"/g, "&quot;") : fallbackIcon;
        icon = `<img 
            src="${app.icon}" 
            alt="${app.name}" 
            style="width: 100%; height: 100%; object-fit: contain;"
            onerror="this.style.display='none'; this.insertAdjacentHTML('afterend', '${escapedFallback}');"
        />`;
    }
    
    const statusClass = app.status ? app.status.toLowerCase() : 'stopped';
    const statusText = app.status || 'Unknown';
    
    if (isDeployed) {
        // Parse URL if available - handle null/None from backend
        const appUrl = (app.url && app.url !== 'None' && app.url !== 'null') ? app.url : null;
        const displayUrl = appUrl || 'IP not available';
        const isRunning = statusText === 'running';
        
        console.log('Rendering deployed app:', app.name, 'URL:', app.url, 'Parsed URL:', appUrl);
        
        return `
            <div class="app-card deployed">
                <!-- Line 1: Icon, Name, Status, Quick Actions -->
                <div class="app-card-header">
                    <div class="app-icon-lg">${icon}</div>
                    <div class="app-info">
                        <h3 class="app-name">${app.name}</h3>
                        <span class="status-badge ${statusClass}">
                            <span class="status-dot"></span>
                            ${statusText}
                        </span>
                    </div>
                    
                    <!-- Quick Actions in header -->
                    <div class="app-quick-actions">
                        <button class="action-icon" title="${isRunning ? 'Stop' : 'Start'}" onclick="controlApp('${app.id}', '${isRunning ? 'stop' : 'start'}')">
                            <i data-lucide="${isRunning ? 'pause' : 'play'}"></i>
                        </button>
                        <button class="action-icon" title="Open in new tab" ${isRunning && appUrl ? '' : 'disabled'} onclick="${appUrl ? `window.open('${appUrl}', '_blank')` : 'return false;'}">
                            <i data-lucide="external-link"></i>
                        </button>
                        <button class="action-icon" title="View logs" onclick="showAppLogs('${app.id}', '${app.hostname}')">
                            <i data-lucide="file-text"></i>
                        </button>
                        <button class="action-icon" title="Console" onclick="showAppConsole('${app.id}', '${app.hostname}')">
                            <i data-lucide="terminal"></i>
                        </button>
                        <button class="action-icon" title="${isRunning ? 'Restart' : 'Start'}" onclick="controlApp('${app.id}', '${isRunning ? 'restart' : 'start'}')">
                            <i data-lucide="refresh-cw"></i>
                        </button>
                        <button class="action-icon danger" title="Delete" onclick="confirmDeleteApp('${app.id}', '${app.name}')">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Line 2: Access URL, Container, Date -->
                <div class="app-connection-info">
                    <div class="connection-item">
                        <i data-lucide="link" class="connection-icon"></i>
                        ${appUrl ? `<a href="${appUrl}" target="_blank" class="connection-value connection-link" ${isRunning ? '' : 'style="opacity: 0.5; pointer-events: none;"'}>
                            ${displayUrl}
                        </a>` : `<span class="connection-value" style="opacity: 0.5;">IP not available</span>`}
                    </div>
                    <div class="connection-item">
                        <i data-lucide="server" class="connection-icon"></i>
                        <span class="connection-value">${app.node}</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="box" class="connection-icon"></i>
                        <span class="connection-value">LXC ${app.lxc_id}</span>
                    </div>
                    <div class="connection-item">
                        <i data-lucide="clock" class="connection-icon"></i>
                        <span class="connection-value">${formatDate(app.created_at)}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Catalog app card
    return `
        <div class="app-card" onclick="showDeployModal('${app.id}')">
            <div class="app-card-header">
                <div class="app-icon-lg">${icon}</div>
                <div class="app-info">
                    <h3 class="app-name">${app.name}</h3>
                    <span class="app-category">${app.category}</span>
                </div>
            </div>
            <p class="app-description">${app.description}</p>
            <div class="app-meta">
                <div class="app-meta-item">
                    <span>💾</span>
                    <span>${app.min_memory}MB RAM</span>
                </div>
                <div class="app-meta-item">
                    <span>⚡</span>
                    <span>${app.min_cpu} vCPU</span>
                </div>
            </div>
            <div class="app-actions">
                <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); showDeployModal('${app.id}')">
                    🚀 Deploy
                </button>
                <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation(); showAppInfo('${app.id}')">
                    Info
                </button>
            </div>
        </div>
    `;
}

// View Management
function showView(viewName) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
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
        }
        
        // Reinitialize Lucide icons after view change
        initLucideIcons();
    }
}

function renderAppsView() {
    const view = document.getElementById('appsView');
    
    const content = `
        <div class="page-header">
            <div class="page-title-row">
                <div>
                    <h1 class="page-title">My Applications</h1>
                    <p class="page-subtitle">Manage all your deployed applications</p>
                </div>
                <button class="btn btn-primary" onclick="showView('catalog')">
                    <span>➕</span>
                    <span>Deploy New App</span>
                </button>
            </div>
        </div>
        
        <div class="filter-tabs">
            <button class="filter-tab active" onclick="filterApps('all')">All Apps</button>
            <button class="filter-tab" onclick="filterApps('running')">Running</button>
            <button class="filter-tab" onclick="filterApps('stopped')">Stopped</button>
        </div>
        
        <div class="apps-grid deployed" id="allAppsGrid">
            ${state.deployedApps.length > 0 
                ? state.deployedApps.map(app => createAppCard(app, true)).join('')
                : `
                <div class="empty-state">
                    <div class="empty-icon">📦</div>
                    <h3 class="empty-title">No applications deployed</h3>
                    <p class="empty-message">Start by deploying an application from the catalog.</p>
                    <button class="btn btn-primary" onclick="showView('catalog')">Browse Catalog</button>
                </div>
                `
            }
        </div>
    `;
    
    view.innerHTML = content;
}

function renderCatalogView() {
    const view = document.getElementById('catalogView');
    
    if (!state.catalog || !state.catalog.items) {
        view.innerHTML = '<div class="loading-spinner"></div>';
        return;
    }
    
    const categories = state.catalog.categories || [];
    
    const content = `
        <div class="page-header">
            <div class="page-title-row">
                <div>
                    <h1 class="page-title">App Store</h1>
                    <p class="page-subtitle">Deploy popular applications with one click</p>
                </div>
            </div>
        </div>
        
        <div class="filter-tabs">
            <button class="filter-tab active" onclick="filterCatalog('all')">All</button>
            ${categories.map(cat => `
                <button class="filter-tab" onclick="filterCatalog('${cat}')">${cat}</button>
            `).join('')}
        </div>
        
        <div class="apps-grid" id="catalogGrid">
            ${state.catalog.items.map(app => createAppCard(app, false)).join('')}
        </div>
    `;
    
    view.innerHTML = content;
}

function renderNodesView() {
    const view = document.getElementById('nodesView');
    
    const content = `
        <div class="page-header">
            <div class="page-title-row">
                <div>
                    <h1 class="page-title">Infrastructure</h1>
                    <p class="page-subtitle">Proxmox nodes and resources</p>
                </div>
            </div>
        </div>
        
        <div class="apps-grid">
            ${state.nodes.map(node => `
                <div class="app-card">
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
                    <div class="app-meta">
                        <div class="app-meta-item">
                            <span>💾</span>
                            <span>${formatBytes(node.mem || 0)} / ${formatBytes(node.maxmem || 0)}</span>
                        </div>
                        <div class="app-meta-item">
                            <span>⚡</span>
                            <span>${node.maxcpu || 0} vCPU</span>
                        </div>
                    </div>
                    <div class="app-meta">
                        <div class="app-meta-item">
                            <span>📊</span>
                            <span>${node.maxcpu > 0 ? Math.round((node.cpu / node.maxcpu) * 100) : 0}% CPU</span>
                        </div>
                        <div class="app-meta-item">
                            <span>💿</span>
                            <span>${formatBytes(node.disk || 0)} / ${formatBytes(node.maxdisk || 0)}</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    view.innerHTML = content;
}

function renderMonitoringView() {
    const view = document.getElementById('monitoringView');
    
    const content = `
        <div class="page-header">
            <div class="page-title-row">
                <div>
                    <h1 class="page-title">Monitoring</h1>
                    <p class="page-subtitle">System and application metrics</p>
                </div>
            </div>
        </div>
        
        <div class="alert info">
            <span class="alert-icon">ℹ️</span>
            <div class="alert-content">
                <div class="alert-title">Monitoring Dashboard</div>
                <div class="alert-message">Advanced monitoring features coming soon. Integration with Prometheus, Grafana, and custom metrics.</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-label">Total Applications</span>
                    <div class="stat-icon primary">📦</div>
                </div>
                <div class="stat-value">${state.deployedApps.length}</div>
            </div>
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-label">Running</span>
                    <div class="stat-icon success">✓</div>
                </div>
                <div class="stat-value">${state.deployedApps.filter(a => a.status === 'running').length}</div>
            </div>
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-label">Stopped</span>
                    <div class="stat-icon warning">⏸</div>
                </div>
                <div class="stat-value">${state.deployedApps.filter(a => a.status === 'stopped').length}</div>
            </div>
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-label">Containers</span>
                    <div class="stat-icon info">🐳</div>
                </div>
                <div class="stat-value">${state.systemInfo?.total_lxc || 0}</div>
            </div>
        </div>
    `;
    
    view.innerHTML = content;
}

async function renderSettingsView() {
    const view = document.getElementById('settingsView');

    // Load settings data
    showLoading('Loading settings...');
    let proxmoxSettings = { host: '', user: '', password: '', port: 8006, verify_ssl: false };
    let networkSettings = { lan_subnet: '10.20.0.0/24', lan_gateway: '10.20.0.1', dhcp_start: '10.20.0.100', dhcp_end: '10.20.0.250', dns_domain: 'prox.local' };
    let resourceSettings = { lxc_memory: 2048, lxc_cores: 2, lxc_disk: 8, lxc_storage: 'local-lvm' };

    try {
        const token = localStorage.getItem('auth_token');
        if (token) {
            // Load Proxmox settings
            const proxmoxRes = await fetch(`${API_BASE}/settings/proxmox`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (proxmoxRes.ok) proxmoxSettings = await proxmoxRes.json();

            // Load Network settings
            const networkRes = await fetch(`${API_BASE}/settings/network`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (networkRes.ok) networkSettings = await networkRes.json();

            // Load Resource settings
            const resourceRes = await fetch(`${API_BASE}/settings/resources`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (resourceRes.ok) resourceSettings = await resourceRes.json();
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
    hideLoading();

    const content = `
        <div class="page-header">
            <div class="page-title-row">
                <div>
                    <h1 class="page-title">Settings</h1>
                    <p class="page-subtitle">Configure Proximity platform settings</p>
                </div>
            </div>
        </div>

        <div class="settings-tabs">
            <button class="settings-tab active" data-tab="proxmox">
                <i data-lucide="server"></i>
                <span>Proxmox</span>
            </button>
            <button class="settings-tab" data-tab="network">
                <i data-lucide="network"></i>
                <span>Network</span>
            </button>
            <button class="settings-tab" data-tab="resources">
                <i data-lucide="cpu"></i>
                <span>Resources</span>
            </button>
            <button class="settings-tab" data-tab="system">
                <i data-lucide="settings"></i>
                <span>System</span>
            </button>
        </div>

        <div class="settings-content">
            <!-- Proxmox Settings -->
            <div class="settings-panel active" id="proxmox-panel">
                <div class="app-card">
                    <h3 class="app-name" style="margin-bottom: 1.5rem;">Proxmox Connection</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Configure connection to your Proxmox VE server</p>

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
                    <h3 class="app-name" style="margin-bottom: 1.5rem;">Network Configuration</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Configure network settings for deployed applications</p>

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
                    <h3 class="app-name" style="margin-bottom: 1.5rem;">Default Resources</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Set default resource allocations for new LXC containers</p>

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
                    <h3 class="app-name" style="margin-bottom: 1.5rem;">System Information</h3>
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

                <div class="app-card" style="margin-top: 1.5rem;">
                    <h3 class="app-name" style="margin-bottom: 1.5rem;">Security</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Manage authentication and access control</p>

                    <div class="alert info">
                        <span class="alert-icon">🔐</span>
                        <div class="alert-content">
                            <div class="alert-title">Authentication Enabled</div>
                            <div class="alert-message">All API endpoints are protected with JWT authentication. Sensitive data is encrypted at rest.</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    view.innerHTML = content;

    // Initialize icons after rendering
    initLucideIcons();

    // Setup tab switching
    setupSettingsTabs();

    // Setup form handlers
    setupSettingsForms();
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
}

function closeModal() {
    document.getElementById('deployModal').classList.remove('show');
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
        
        const response = await fetch(`${API_BASE}/apps/deploy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Deployment failed');
        }
        
        const result = await response.json();
        
        hideDeploymentProgress();
        showNotification(`Application deployed successfully!`, 'success');
        
        // Wait a moment for proxy vhost to be fully propagated
        // Then reload to get the correct proxy URL instead of direct LXC IP
        console.log('Waiting for proxy vhost propagation...');
        await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
        
        // Reload apps and proxy status to get updated URLs
        await loadDeployedApps();
        await loadSystemInfo();
        await loadProxyStatus();
        updateUI();
        
        // Show deployed app
        showView('apps');
        
    } catch (error) {
        hideDeploymentProgress();
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
    
    // Start polling for real deployment status
    pollDeploymentStatus(`${catalogId}-${hostname}`);
}

async function pollDeploymentStatus(appId) {
    let pollAttempts = 0;
    const maxAttempts = 120; // 120 attempts * 2 seconds = 4 minutes max
    
    deploymentProgressInterval = setInterval(async () => {
        pollAttempts++;
        
        try {
            const response = await fetch(`${API_BASE}/apps/deploy/${appId}/status`);
            
            if (response.ok) {
                const status = await response.json();
                
                // Update UI with real status
                updateDeploymentProgressFromStatus(status);
                
                // Check if deployment is complete or failed
                if (status.status === 'running' || status.status === 'error') {
                    clearInterval(deploymentProgressInterval);
                    deploymentProgressInterval = null;
                    
                    // Don't hide modal automatically - let deployApp() handle it
                }
            } else if (response.status === 404) {
                // Deployment status not found yet, keep polling
                console.log('Deployment status not available yet, continuing to poll...');
            }
            
        } catch (error) {
            console.error('Error polling deployment status:', error);
        }
        
        // Stop polling after max attempts
        if (pollAttempts >= maxAttempts) {
            clearInterval(deploymentProgressInterval);
            deploymentProgressInterval = null;
            console.warn('Deployment polling timeout reached');
        }
    }, 2000); // Poll every 2 seconds
}

function updateDeploymentProgressFromStatus(status) {
    const progressBar = document.getElementById('progressBar');
    const progressMessage = document.getElementById('progressMessage');
    
    if (progressBar) {
        progressBar.style.width = `${status.progress || 0}%`;
    }
    
    if (progressMessage) {
        progressMessage.textContent = status.current_step || 'Processing...';
    }
    
    // Update step indicators based on current_step
    const progressSteps = document.getElementById('progressSteps');
    if (progressSteps && status.current_step) {
        updateProgressSteps(status.current_step);
    }
}

function updateProgressSteps(currentStepText) {
    const progressSteps = document.getElementById('progressSteps');
    if (!progressSteps) return;
    
    // Map status text to step names
    const stepMap = {
        'Creating container': 'creating',
        'Reserving container ID': 'creating',
        'Starting container': 'starting',
        'Setting up Docker': 'docker',
        'Installing Docker': 'docker',
        'Pulling Docker images': 'images',
        'Setting up application': 'services',
        'Configuring reverse proxy': 'services',
        'Finalizing deployment': 'finalizing',
        'Deployment complete': 'finalizing'
    };
    
    // Find which step we're on
    let currentStep = 'creating';
    for (const [text, step] of Object.entries(stepMap)) {
        if (currentStepText.includes(text)) {
            currentStep = step;
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
}

async function controlApp(appId, action) {
    showLoading(`${action}ing application...`);
    
    try {
        const response = await fetch(`${API_BASE}/apps/${appId}/actions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
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
        
        const response = await fetch(`${API_BASE}/apps/${appId}`, {
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
        await loadProxyStatus();
        updateUI();
        
        // If we're on the apps view, refresh it
        if (state.currentView === 'apps') {
            showView('apps');
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

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `toast-notification toast-${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    notification.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;
    
    // Add to document
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'toastSlideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
    
    // Log to console
    console.log(`[${type.toUpperCase()}] ${message}`);
    if (type === 'error') {
        console.error(message);
    }
}

function filterApps(filter) {
    // Update tab active state
    document.querySelectorAll('.filter-tab').forEach(tab => {
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
        grid.innerHTML = filtered.map(app => createAppCard(app, true)).join('');
        // Reinitialize Lucide icons after updating the DOM
        initLucideIcons();
    }
}

function filterCatalog(category) {
    // Update tab active state
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Filter catalog
    let filtered = state.catalog.items;
    if (category !== 'all') {
        filtered = state.catalog.items.filter(app => app.category === category);
    }
    
    const grid = document.getElementById('catalogGrid');
    grid.innerHTML = filtered.map(app => createAppCard(app, false)).join('');
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
    loadAppLogs(appId);
}

function showAppConsole(appId, hostname) {
    const modal = document.getElementById('deployModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = `💻 Console - ${hostname}`;
    
    modalBody.innerHTML = `
        <div class="alert info" style="margin-bottom: 1rem;">
            <span class="alert-icon">ℹ️</span>
            <div class="alert-content">
                <div class="alert-message">Execute commands inside the container. Use with caution!</div>
            </div>
        </div>
        
        <div style="background: #1a1a1a; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1rem; height: 350px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.875rem; color: #e0e0e0; margin-bottom: 1rem;">
            <div id="consoleOutput">
                <div style="color: #4ade80;">proximity@${hostname}:~$</div>
            </div>
        </div>
        
        <form onsubmit="event.preventDefault(); executeCommand('${appId}');" style="display: flex; gap: 0.5rem;">
            <input 
                type="text" 
                id="consoleCommand" 
                class="form-input" 
                placeholder="Enter command (e.g., docker ps, ls -la)" 
                style="flex: 1; font-family: 'Courier New', monospace;"
                autocomplete="off"
            >
            <button type="submit" class="btn btn-primary">
                Execute
            </button>
        </form>
        
        <div style="margin-top: 1rem;">
            <details style="font-size: 0.75rem; color: var(--text-tertiary);">
                <summary style="cursor: pointer; margin-bottom: 0.5rem;">Common Commands</summary>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; margin-top: 0.5rem;">
                    <code style="cursor: pointer; padding: 0.25rem 0.5rem; background: var(--bg-tertiary); border-radius: 4px;" onclick="setCommand('docker ps')">docker ps</code>
                    <code style="cursor: pointer; padding: 0.25rem 0.5rem; background: var(--bg-tertiary); border-radius: 4px;" onclick="setCommand('docker compose logs')">docker compose logs</code>
                    <code style="cursor: pointer; padding: 0.25rem 0.5rem; background: var(--bg-tertiary); border-radius: 4px;" onclick="setCommand('docker compose ps')">docker compose ps</code>
                    <code style="cursor: pointer; padding: 0.25rem 0.5rem; background: var(--bg-tertiary); border-radius: 4px;" onclick="setCommand('free -h')">free -h</code>
                    <code style="cursor: pointer; padding: 0.25rem 0.5rem; background: var(--bg-tertiary); border-radius: 4px;" onclick="setCommand('df -h')">df -h</code>
                    <code style="cursor: pointer; padding: 0.25rem 0.5rem; background: var(--bg-tertiary); border-radius: 4px;" onclick="setCommand('top -bn1')">top -bn1</code>
                </div>
            </details>
        </div>
    `;
    
    modal.classList.add('show');
    setTimeout(() => document.getElementById('consoleCommand')?.focus(), 100);
}

let logsRefreshInterval = null;

async function loadAppLogs(appId, type = 'all') {
    try {
        const response = await fetch(`${API_BASE}/apps/${appId}/logs`);
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
        const response = await fetch(`${API_BASE}/apps/${appId}/logs`);
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
        const response = await fetch(`${API_BASE}/apps/${appId}/exec`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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

const originalCloseModal = window.closeModal;
function closeModal() {
    if (logsRefreshInterval) {
        clearInterval(logsRefreshInterval);
        logsRefreshInterval = null;
    }
    document.getElementById('deployModal').classList.remove('show');
}

// Settings Page Helpers
function setupSettingsTabs() {
    const tabs = document.querySelectorAll('.settings-tab');
    const panels = document.querySelectorAll('.settings-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and panels
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));

            // Add active class to clicked tab
            tab.classList.add('active');

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

function setupSettingsForms() {
    // Proxmox form
    const proxmoxForm = document.getElementById('proxmoxForm');
    if (proxmoxForm) {
        proxmoxForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveProxmoxSettings(new FormData(proxmoxForm));
        });
    }

    // Network form
    const networkForm = document.getElementById('networkForm');
    if (networkForm) {
        networkForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveNetworkSettings(new FormData(networkForm));
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
}

async function saveProxmoxSettings(formData) {
    const statusDiv = document.getElementById('proxmoxStatus');
    const token = localStorage.getItem('auth_token');

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

        const response = await fetch(`${API_BASE}/settings/proxmox`, {
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
    const token = localStorage.getItem('auth_token');

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

        const response = await fetch(`${API_BASE}/system/info`, {
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
    const token = localStorage.getItem('auth_token');

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

        const response = await fetch(`${API_BASE}/settings/network`, {
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
    const token = localStorage.getItem('auth_token');

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

        const response = await fetch(`${API_BASE}/settings/resources`, {
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

// Event Listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            if (view) showView(view);
        });
    });

    // Close modal on outside click
    document.getElementById('deployModal').addEventListener('click', (e) => {
        if (e.target.id === 'deployModal') {
            closeModal();
        }
    });
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);