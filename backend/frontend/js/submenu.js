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
            action: 'proxmox-settings',
            onClick: () => {
                console.log('Proxmox settings clicked');
                // Navigate to proxmox settings
            }
        },
        {
            icon: 'network',
            label: 'Network',
            action: 'network-settings',
            onClick: () => {
                console.log('Network settings clicked');
            }
        },
        {
            icon: 'hard-drive',
            label: 'Resources',
            action: 'resources-settings',
            onClick: () => {
                console.log('Resources settings clicked');
            }
        },
        {
            icon: 'shield',
            label: 'Security',
            action: 'security-settings',
            onClick: () => {
                console.log('Security settings clicked');
            }
        }
    ];

    showSubmenu(settingsItems);
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
            }
        },
        {
            icon: 'play',
            label: 'Running',
            badge: '5',
            onClick: () => {
                console.log('Running apps filter clicked');
            }
        },
        {
            icon: 'pause',
            label: 'Stopped',
            badge: '2',
            onClick: () => {
                console.log('Stopped apps filter clicked');
            }
        },
        {
            icon: 'alert-circle',
            label: 'Issues',
            onClick: () => {
                console.log('Apps with issues clicked');
            }
        }
    ];

    showSubmenu(appsItems);
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
