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

    // Render the tabs (default to register)
    renderAuthTabs('register');

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
function renderAuthTabs(defaultTab = 'register') {
    const body = document.getElementById('authModalBody');
    body.innerHTML = `
        <div class="auth-tabs">
            <button id="registerTab" class="auth-tab ${defaultTab === 'register' ? 'active' : ''}" data-tab="register">Register</button>
            <button id="loginTab" class="auth-tab ${defaultTab === 'login' ? 'active' : ''}" data-tab="login">Login</button>
        </div>
        <div id="authTabContent"></div>
    `;

    // Attach event listeners
    document.getElementById('registerTab').addEventListener('click', () => switchAuthTab('register'));
    document.getElementById('loginTab').addEventListener('click', () => switchAuthTab('login'));

    // Show the default tab
    switchAuthTab(defaultTab);
}

/**
 * Switch between register and login tabs
 * @param {string} tab - Tab to show ('register' or 'login')
 */
function switchAuthTab(tab) {
    document.getElementById('registerTab').classList.toggle('active', tab === 'register');
    document.getElementById('loginTab').classList.toggle('active', tab === 'login');

    if (tab === 'register') {
        renderRegisterForm();
    } else {
        renderLoginForm();
    }
}

/**
 * Render the registration form
 */
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

    document.getElementById('registerForm').addEventListener('submit', handleRegisterSubmit);
}

/**
 * Render the login form
 * @param {object} prefill - Optional values to pre-fill
 */
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

    document.getElementById('loginForm').addEventListener('submit', handleLoginSubmit);
}

/**
 * Handle registration form submission
 * @param {Event} e - Form submit event
 */
async function handleRegisterSubmit(e) {
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
        errorDiv.textContent = err.message || 'Registration failed. Please try again.';
    }
}

/**
 * Handle login form submission
 * @param {Event} e - Form submit event
 */
async function handleLoginSubmit(e) {
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

        // Update application state
        AppState.setState({
            isAuthenticated: true,
            currentUser: data.user,
            currentView: 'dashboard'
        });

        // Close auth modal
        closeAuthModal();

    } catch (err) {
        console.error('Login error:', err);
        errorDiv.textContent = err.message || 'Login failed. Please try again.';
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
    window.showAuthModal = showAuthModal;
    window.closeAuthModal = closeAuthModal;
    window.handleLogout = handleLogout;
}
