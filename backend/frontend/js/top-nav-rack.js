/* ============================================================================
   TOP NAVIGATION RACK - JavaScript
   Handles the new horizontal navigation system
   ============================================================================ */

// Initialize Top Navigation Rack
function initTopNavRack() {
    console.log('🎯 Initializing Top Navigation Rack...');
    
    // Navigation items click handler
    const navItems = document.querySelectorAll('.nav-rack-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            if (view) {
                // Remove active class from all items
                navItems.forEach(nav => nav.classList.remove('active'));
                // Add active class to clicked item
                item.classList.add('active');
                // Show the view
                showView(view);
            }
        });
    });
    
    // User profile button toggle
    const userProfileBtn = document.getElementById('userProfileBtn');
    const userMenu = document.getElementById('userMenu');
    
    if (userProfileBtn && userMenu) {
        userProfileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenu.classList.toggle('show');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!userProfileBtn.contains(e.target) && !userMenu.contains(e.target)) {
                userMenu.classList.remove('show');
            }
        });
    }
    
    console.log('✓ Top Navigation Rack initialized');
}

// Update active navigation item
function updateActiveNav(viewName) {
    const navItems = document.querySelectorAll('.nav-rack-item');
    navItems.forEach(item => {
        if (item.dataset.view === viewName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// Update user info in navigation
function updateUserInfoNav() {
    const user = Auth.getUser();
    if (user) {
        const userNameEl = document.querySelector('.nav-rack-user .user-name');
        const userRoleEl = document.querySelector('.nav-rack-user .user-role');
        const userAvatarEl = document.querySelector('.nav-rack-user .user-avatar');
        
        if (userNameEl) {
            userNameEl.textContent = user.username || 'User';
        }
        if (userRoleEl) {
            userRoleEl.textContent = user.role === 'admin' ? 'Admin' : 'User';
        }
        if (userAvatarEl) {
            const initials = (user.username || 'U').substring(0, 2).toUpperCase();
            userAvatarEl.textContent = initials;
        }
    }
}

// Update apps count badge
function updateAppsCountBadge(count) {
    const badge = document.getElementById('appsCount');
    if (badge) {
        badge.textContent = count || '0';
        // Add pulse animation if count > 0
        if (count > 0) {
            badge.style.animation = 'pulse 2s ease-in-out infinite';
        } else {
            badge.style.animation = 'none';
        }
    }
}

// Export functions for use in main app.js
if (typeof window !== 'undefined') {
    window.initTopNavRack = initTopNavRack;
    window.updateActiveNav = updateActiveNav;
    window.updateUserInfoNav = updateUserInfoNav;
    window.updateAppsCountBadge = updateAppsCountBadge;
}
