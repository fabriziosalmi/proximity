/**
 * Authentication UI Module
 *
 * Handles all authentication-related UI:
 * - Auth modal (register/login)
 * - Form rendering
 * - User registration
 * - User login
 * - Session initialization
 */

import * as API from '../services/api.js';
import * as Auth from '../utils/auth.js';
import * as AppState from '../state/appState.js';
import { showNotification } from '../utils/notifications.js';

const API_BASE = 'http://localhost:8765/api/v1';

/**
 * Toggle user profile menu visibility
 * Handles menu open/close with proper class management
 */
export function toggleUserMenu() {
    // Fallback stub - real implementation in js/utils/ui.js
    if (window.UI?.toggleUserMenu) {
        window.UI.toggleUserMenu();
    } else {
        // Legacy fallback
        const menu = document.getElementById('userMenu');
        const profileBtn = document.getElementById('userProfileBtn');
        if (menu && profileBtn) {
            menu.classList.toggle('active');
            profileBtn.classList.toggle('active');
        }
    }
}

/**
 * Show the authentication modal
 * Displays register/login tabs
 */
export function showAuthModal() {
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

    // Render the tabs (default to login for easier access)
    renderAuthTabs('login');

    console.log('✅ Auth modal displayed');
}

/**
 * Close the authentication modal
 */
export function closeAuthModal() {
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

/**
 * Render auth modal tabs (Register/Login)
 * @param {string} defaultTab - Default tab to show ('register' or 'login')
 */
export function renderAuthTabs(defaultTab = 'login') {
    const body = document.getElementById('authModalBody');
    body.innerHTML = `
        <div class="auth-tabs">
            <button id="registerTab" class="auth-tab ${defaultTab === 'register' ? 'active' : ''}" onclick="window.authUI.switchAuthTab('register')">Register</button>
            <button id="loginTab" class="auth-tab ${defaultTab === 'login' ? 'active' : ''}" onclick="window.authUI.switchAuthTab('login')">Login</button>
        </div>
        <div id="authTabContent"></div>
    `;

    // Show the default tab
    switchAuthTab(defaultTab);
}

/**
 * Switch between register and login tabs
 * @param {string} tab - Tab to show ('register' or 'login')
 */
export function switchAuthTab(tab) {
    document.getElementById('registerTab').classList.toggle('active', tab === 'register');
    document.getElementById('loginTab').classList.toggle('active', tab === 'login');

    if (tab === 'register') {
        renderRegisterForm();
    } else {
        renderLoginForm();
    }
}

/**
 * Switch to a tab with pre-filled data (used after registration)
 * @param {string} tab - Tab to show ('register' or 'login')
 * @param {object} prefill - Data to pre-fill in the form
 */
export function switchAuthTabWithPrefill(tab, prefill = {}) {
    // Update tab buttons
    const registerTab = document.getElementById('registerTab');
    const loginTab = document.getElementById('loginTab');
    
    if (registerTab && loginTab) {
        registerTab.classList.toggle('active', tab === 'register');
        loginTab.classList.toggle('active', tab === 'login');
    }

    if (tab === 'register') {
        renderRegisterForm();
    } else {
        renderLoginForm(prefill);
        
        // Focus on submit button after pre-fill (since fields are already filled)
        setTimeout(() => {
            const submitBtn = document.querySelector('#loginForm button[type="submit"]');
            if (submitBtn) submitBtn.focus();
        }, 100);
    }
}

/**
 * Render the registration form
 */
export function renderRegisterForm() {
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

    document.getElementById('registerForm').addEventListener('submit', handleRegisterSubmit);
}

/**
 * Render the login form
 * @param {object} prefill - Optional values to pre-fill
 */
export function renderLoginForm(prefill = {}) {
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

    document.getElementById('loginForm').addEventListener('submit', handleLoginSubmit);
}

/**
 * Handle registration form submission
 * @param {Event} e - Form submit event
 */
export async function handleRegisterSubmit(e) {
    e.preventDefault();

    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value;
    const email = document.getElementById('registerEmail').value.trim();
    const errorDiv = document.getElementById('registerError');
    errorDiv.textContent = '';

    try {
        const result = await API.register(username, email, password);

        // Show success notification
        showNotification('✓ Registration successful! Please log in.', 'success');

        // Switch to login tab and pre-fill credentials
        switchAuthTabWithPrefill('login', { username, password });

    } catch (err) {
        console.error('Registration error:', err);
        errorDiv.textContent = err.message || 'Registration failed. Please try again.';
    }
}

/**
 * Handle login form submission
 * @param {Event} e - Form submit event
 */
export async function handleLoginSubmit(e) {
    e.preventDefault();

    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    errorDiv.textContent = '';

    try {
        const data = await API.login(username, password);

        // Store the token and user data
        Auth.setToken(data.access_token, data.user);

        showNotification('Login successful!', 'success');

        // Initialize authenticated session (uses same flow as app.js)
        await initializeAuthenticatedSession();

    } catch (err) {
        console.error('Login error:', err);
        errorDiv.textContent = err.message || 'Login failed. Please try again.';
    }
}

/**
 * Centralized function to initialize authenticated session
 * Called after both successful registration and login
 * Ensures consistent authentication state across the application
 */
export async function initializeAuthenticatedSession() {
    console.log('🔐 Initializing authenticated session...');
    
    try {
        // 1. Close the auth modal
        closeAuthModal();
        
        // 2. Update user info in sidebar and navigation
        if (window.updateUserInfo) {
            window.updateUserInfo();
        }
        if (window.updateUserInfoNav) {
            window.updateUserInfoNav();
        }
        
        // 3. Show loading state (legacy function from app.js)
        if (window.showLoading) {
            window.showLoading('Loading your applications...');
        }
        
        // 4. Load all necessary data with individual error handling
        console.log('4️⃣ Loading data...');
        console.log('   ⏳ Loading system info...');
        if (window.loadSystemInfo) await window.loadSystemInfo();
        console.log('   ✓ System info loaded');
        
        console.log('   ⏳ Loading nodes...');
        if (window.loadNodes) await window.loadNodes();
        console.log('   ✓ Nodes loaded');
        
        console.log('   ⏳ Loading deployed apps...');
        if (window.loadDeployedApps) await window.loadDeployedApps();
        console.log('   ✓ Deployed apps loaded');
        
        console.log('   ⏳ Loading catalog...');
        if (window.loadCatalog) await window.loadCatalog();
        console.log('   ✓ Catalog loaded');
        
        // 5. Setup event listeners FIRST (before showing views)
        console.log('5️⃣ Setting up event listeners...');
        if (window.setupEventListeners) {
            window.setupEventListeners();
        }
        console.log('   ✓ Event listeners attached');

        // Set global flag to indicate event listeners are ready
        window.eventListenersReady = true;

        // 6. Initialize Lucide icons
        if (window.initLucideIcons) {
            window.initLucideIcons();
        }

        // 7. Hide loading state
        if (window.hideLoading) {
            window.hideLoading();
        }

        // 8. Show the dashboard view (BEFORE updating UI so DOM elements exist)
        console.log('6️⃣ Showing dashboard view...');
        if (window.showView) {
            window.showView('dashboard');
        }
        
        // 9. Update UI AFTER view is shown to ensure DOM elements exist
        console.log('7️⃣ Updating UI with loaded data...');
        if (window.updateUI) {
            window.updateUI();
        }
        
        console.log('✅ Authenticated session initialized successfully');
        
    } catch (error) {
        console.error('❌ Error initializing authenticated session:', error);
        if (window.hideLoading) {
            window.hideLoading();
        }
        showNotification('Failed to load application data. Please refresh the page.', 'error');
    }
}

/**
 * Handle user logout
 * @param {Event} e - Click event
 */
export async function handleLogout(e) {
    if (e) e.preventDefault();

    try {
        // Call logout API
        await API.logout();
    } catch (error) {
        console.error('Logout API error:', error);
        // Continue with logout even if API call fails
    }

    // Clear local authentication
    Auth.clearToken();

    // Reset application state
    AppState.resetState();
    AppState.setState({
        isAuthenticated: false,
        currentUser: null
    });

    // Show auth modal
    showAuthModal();

    showNotification('Logged out successfully', 'success');
}

// Expose functions globally for legacy compatibility
if (typeof window !== 'undefined') {
    window.authUI = {
        showAuthModal,
        closeAuthModal,
        renderAuthTabs,
        switchAuthTab,
        renderRegisterForm,
        renderLoginForm,
        handleRegisterSubmit,
        handleLoginSubmit,
        initializeAuthenticatedSession,
        toggleUserMenu,
        handleLogout
    };
    
    // Also expose top-level for backward compatibility
    window.showAuthModal = showAuthModal;
    window.closeAuthModal = closeAuthModal;
    window.handleLogout = handleLogout;
    window.toggleUserMenu = toggleUserMenu;
    window.renderAuthTabs = renderAuthTabs;
    window.switchAuthTab = switchAuthTab;
    window.renderRegisterForm = renderRegisterForm;
    window.renderLoginForm = renderLoginForm;
    window.handleRegisterSubmit = handleRegisterSubmit;
    window.handleLoginSubmit = handleLoginSubmit;
    window.initializeAuthenticatedSession = initializeAuthenticatedSession;
}
