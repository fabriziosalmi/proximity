/**
 * Dynamic Submenu System
 * Manages seamless submenu display under the top navigation bar
 */

// Show submenu with items
function showSubmenu(items) {
    const submenu = document.getElementById('navSubmenu');
    const submenuContent = document.getElementById('navSubmenuContent');
    const topRack = document.querySelector('.top-nav-rack');

    if (!submenu || !submenuContent || !topRack) return;

    // Clear existing content
    submenuContent.innerHTML = '';

    // Add new items
    items.forEach(item => {
        const submenuItem = document.createElement('a');
        submenuItem.href = item.href || '#';
        submenuItem.className = `nav-submenu-item ${item.active ? 'active' : ''}`;
        submenuItem.setAttribute('data-action', item.action || '');

        if (item.icon) {
            const icon = document.createElement('i');
            icon.setAttribute('data-lucide', item.icon);
            submenuItem.appendChild(icon);
        }

        if (item.label) {
            const label = document.createElement('span');
            label.textContent = item.label;
            submenuItem.appendChild(label);
        }

        if (item.badge) {
            const badge = document.createElement('span');
            badge.className = 'nav-badge';
            badge.textContent = item.badge;
            submenuItem.appendChild(badge);
        }

        if (item.onClick) {
            submenuItem.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation(); // Prevent event from bubbling up
                item.onClick(e);
            });
        }

        submenuContent.appendChild(submenuItem);
    });

    // Show submenu with animation
    submenu.style.display = 'block';
    topRack.classList.add('submenu-open');

    // Trigger reflow for animation
    submenu.offsetHeight;

    // Add show class for transition
    requestAnimationFrame(() => {
        submenu.classList.add('show');
    });

    // Reinitialize Lucide icons for new submenu items
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Hide submenu
function hideSubmenu() {
    const submenu = document.getElementById('navSubmenu');
    const topRack = document.querySelector('.top-nav-rack');

    if (!submenu || !topRack) return;

    // Remove show class for transition
    submenu.classList.remove('show');
    topRack.classList.remove('submenu-open');

    // Wait for transition to complete before hiding
    setTimeout(() => {
        if (!submenu.classList.contains('show')) {
            submenu.style.display = 'none';
        }
    }, 300);
}

// Toggle submenu
function toggleSubmenu(items) {
    const submenu = document.getElementById('navSubmenu');

    if (submenu && submenu.classList.contains('show')) {
        hideSubmenu();
    } else {
        showSubmenu(items);
    }
}

// Example: Show Settings submenu
function showSettingsSubmenu() {
    const settingsItems = [
        {
            icon: 'server',
            label: 'Proxmox',
            action: 'proxmox',
            active: true,
            onClick: () => {
                console.log('Proxmox settings clicked');
                showView('settings');
                activateSettingsTab('proxmox');
            }
        },
        {
            icon: 'network',
            label: 'Network',
            action: 'network',
            onClick: () => {
                console.log('Network settings clicked');
                showView('settings');
                activateSettingsTab('network');
            }
        },
        {
            icon: 'cpu',
            label: 'Resources',
            action: 'resources',
            onClick: () => {
                console.log('Resources settings clicked');
                showView('settings');
                activateSettingsTab('resources');
            }
        },
        {
            icon: 'info',
            label: 'System',
            action: 'system',
            onClick: () => {
                console.log('System settings clicked');
                showView('settings');
                activateSettingsTab('system');
            }
        },
        {
            icon: 'volume-2',
            label: 'Audio',
            action: 'audio',
            onClick: () => {
                console.log('Audio settings clicked');
                showView('settings');
                activateSettingsTab('audio');
            }
        }
    ];

    showSubmenu(settingsItems);
}

// Helper function to activate a specific settings tab
function activateSettingsTab(tabName) {
    // Small delay to ensure view is rendered
    setTimeout(() => {
        const tabs = document.querySelectorAll('.sub-nav-item[data-tab]');
        const panels = document.querySelectorAll('.settings-panel');

        // Remove active from all
        tabs.forEach(t => t.classList.remove('active'));
        panels.forEach(p => p.classList.remove('active'));

        // Activate the selected tab and panel
        const selectedTab = document.querySelector(`.sub-nav-item[data-tab="${tabName}"]`);
        const selectedPanel = document.getElementById(`${tabName}-panel`);

        if (selectedTab) selectedTab.classList.add('active');
        if (selectedPanel) selectedPanel.classList.add('active');

        // Reinitialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 50);
}

// Example: Show Apps submenu with filters
function showAppsSubmenu() {
    const appsItems = [
        {
            icon: 'layout-grid',
            label: 'All Apps',
            active: true,
            onClick: () => {
                console.log('All apps filter clicked');
                showView('apps');
                setTimeout(() => applyAppsFilter('all'), 100);
            }
        },
        {
            icon: 'play',
            label: 'Running',
            onClick: () => {
                console.log('Running apps filter clicked');
                showView('apps');
                setTimeout(() => applyAppsFilter('running'), 100);
            }
        },
        {
            icon: 'pause',
            label: 'Stopped',
            onClick: () => {
                console.log('Stopped apps filter clicked');
                showView('apps');
                setTimeout(() => applyAppsFilter('stopped'), 100);
            }
        },
        {
            icon: 'alert-circle',
            label: 'Issues',
            onClick: () => {
                console.log('Apps with issues clicked');
                showView('apps');
                setTimeout(() => applyAppsFilter('issues'), 100);
            }
        },
        {
            icon: 'star',
            label: 'Favorites',
            onClick: () => {
                console.log('Favorite apps clicked');
                showView('apps');
                setTimeout(() => applyAppsFilter('favorites'), 100);
            }
        }
    ];

    showSubmenu(appsItems);
}

// Apply filter to apps view
function applyAppsFilter(filter) {
    if (typeof state === 'undefined' || !state.deployedApps) {
        console.warn('State or deployedApps not available');
        return;
    }

    let filtered = state.deployedApps;

    if (filter === 'running') {
        filtered = state.deployedApps.filter(app => app.status === 'running');
    } else if (filter === 'stopped') {
        filtered = state.deployedApps.filter(app => app.status === 'stopped');
    } else if (filter === 'issues') {
        filtered = state.deployedApps.filter(app => app.status === 'error' || app.status === 'failed');
    } else if (filter === 'favorites') {
        // TODO: Implement favorites functionality
        filtered = state.deployedApps.filter(app => app.favorite);
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
        grid.innerHTML = '';
        for (const app of filtered) {
            if (typeof renderAppCard === 'function') {
                renderAppCard(app, grid, true);
            }
        }
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
}

// Show Store submenu with categories (icon-only with ALL label)
function showStoreSubmenu() {
    const storeItems = [
        {
            icon: 'layout-grid',
            label: 'ALL',
            active: true,
            onClick: () => {
                console.log('All categories clicked');
                showView('catalog');
                setTimeout(() => applyCatalogFilter('all'), 100);
            }
        },
        {
            icon: 'database',
            onClick: () => {
                console.log('Database category clicked');
                showView('catalog');
                setTimeout(() => applyCatalogFilter('Database'), 100);
            }
        },
        {
            icon: 'globe',
            onClick: () => {
                console.log('Web Server category clicked');
                showView('catalog');
                setTimeout(() => applyCatalogFilter('Web Server'), 100);
            }
        },
        {
            icon: 'code',
            onClick: () => {
                console.log('Development category clicked');
                showView('catalog');
                setTimeout(() => applyCatalogFilter('Development'), 100);
            }
        },
        {
            icon: 'file-text',
            onClick: () => {
                console.log('CMS category clicked');
                showView('catalog');
                setTimeout(() => applyCatalogFilter('CMS'), 100);
            }
        },
        {
            icon: 'shield',
            onClick: () => {
                console.log('Security category clicked');
                showView('catalog');
                setTimeout(() => applyCatalogFilter('Security'), 100);
            }
        },
        {
            icon: 'activity',
            onClick: () => {
                console.log('Monitoring category clicked');
                showView('catalog');
                setTimeout(() => applyCatalogFilter('Monitoring'), 100);
            }
        },
        {
            icon: 'network',
            onClick: () => {
                console.log('Networking category clicked');
                showView('catalog');
                setTimeout(() => applyCatalogFilter('Networking'), 100);
            }
        }
    ];

    showSubmenu(storeItems);
}

// Apply filter to catalog view
function applyCatalogFilter(category) {
    if (typeof state === 'undefined' || !state.catalog || !state.catalog.items) {
        console.warn('State or catalog not available');
        return;
    }

    let filtered = state.catalog.items;

    if (category !== 'all') {
        filtered = state.catalog.items.filter(app => app.category === category);
    }

    const grid = document.getElementById('catalogGrid');
    if (!grid) return;

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h3 class="empty-title">No ${category} applications</h3>
                <p class="empty-message">No applications match the current category.</p>
            </div>
        `;
    } else {
        grid.innerHTML = '';
        for (const app of filtered) {
            if (typeof renderAppCard === 'function') {
                renderAppCard(app, grid, false);
            }
        }
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
}

// Show UI Lab submenu with experimental features
function showUILabSubmenu() {
    const uilabItems = [
        {
            icon: 'palette',
            label: 'Theme Editor',
            onClick: () => {
                console.log('Theme editor clicked');
                showView('uilab');
                // TODO: Navigate to theme section
                // hideSubmenu is called automatically by showView()
            }
        },
        {
            icon: 'layout',
            label: 'Component Library',
            onClick: () => {
                console.log('Component library clicked');
                showView('uilab');
                // hideSubmenu is called automatically by showView()
            }
        },
        {
            icon: 'grid',
            label: 'Layout Tester',
            onClick: () => {
                console.log('Layout tester clicked');
                showView('uilab');
                // hideSubmenu is called automatically by showView()
            }
        },
        {
            icon: 'sparkles',
            label: 'Animations',
            onClick: () => {
                console.log('Animations clicked');
                showView('uilab');
                // hideSubmenu is called automatically by showView()
            }
        },
        {
            icon: 'zap',
            label: 'Experimental',
            badge: 'NEW',
            onClick: () => {
                console.log('Experimental features clicked');
                showView('uilab');
                // hideSubmenu is called automatically by showView()
            }
        }
    ];

    showSubmenu(uilabItems);
}

// Auto-hide submenu when clicking outside
document.addEventListener('click', (e) => {
    const submenu = document.getElementById('navSubmenu');
    const topRack = document.querySelector('.top-nav-rack');

    if (submenu && topRack && submenu.classList.contains('show')) {
        // Check if click is outside top-nav-rack
        if (!topRack.contains(e.target)) {
            hideSubmenu();
        }
    }
});

// Export functions for global use
window.showSubmenu = showSubmenu;
window.hideSubmenu = hideSubmenu;
window.toggleSubmenu = toggleSubmenu;
window.showSettingsSubmenu = showSettingsSubmenu;
window.showAppsSubmenu = showAppsSubmenu;
window.showStoreSubmenu = showStoreSubmenu;
window.showUILabSubmenu = showUILabSubmenu;
window.activateSettingsTab = activateSettingsTab;
window.applyAppsFilter = applyAppsFilter;
window.applyCatalogFilter = applyCatalogFilter;
