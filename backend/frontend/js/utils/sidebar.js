/**
 * Sidebar Utility Module
 * 
 * Handles sidebar toggle functionality for mobile and desktop.
 * Extracted from app.js as part of final modularization.
 * 
 * @module utils/sidebar
 */

/**
 * Initialize sidebar toggle functionality
 * Handles both mobile and desktop sidebar behavior
 */
export function initSidebarToggle() {
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
                setTimeout(() => {
                    if (typeof window.initLucideIcons === 'function') {
                        window.initLucideIcons();
                    }
                }, 300);
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
                setTimeout(() => {
                    if (typeof window.initLucideIcons === 'function') {
                        window.initLucideIcons();
                    }
                }, 300);
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

/**
 * Toggle sidebar programmatically
 * @param {boolean} forceState - Optional: true to open, false to close
 */
export function toggleSidebar(forceState = null) {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const isMobile = window.innerWidth <= 1024;
    
    if (!sidebar) return;
    
    if (isMobile) {
        if (forceState === null) {
            sidebar.classList.toggle('active');
            if (overlay) overlay.classList.toggle('active');
        } else {
            sidebar.classList.toggle('active', forceState);
            if (overlay) overlay.classList.toggle('active', forceState);
        }
    } else {
        if (forceState === null) {
            sidebar.classList.toggle('collapsed');
        } else {
            sidebar.classList.toggle('collapsed', !forceState);
        }
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    }
}

/**
 * Close sidebar (useful for mobile after navigation)
 */
export function closeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar) {
        sidebar.classList.remove('active');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }
}

/**
 * Open sidebar
 */
export function openSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const isMobile = window.innerWidth <= 1024;
    
    if (sidebar) {
        if (isMobile) {
            sidebar.classList.add('active');
            if (overlay) {
                overlay.classList.add('active');
            }
        } else {
            sidebar.classList.remove('collapsed');
            localStorage.setItem('sidebarCollapsed', 'false');
        }
    }
}
