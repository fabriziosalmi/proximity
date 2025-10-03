// Authentication UI Components and Functions

// Show login modal
function showLoginModal() {
    const modalHtml = `
        <div class="auth-modal" id="authModal">
            <div class="auth-modal-content">
                <div class="auth-modal-header">
                    <h2 class="auth-modal-title">Welcome to Proximity</h2>
                    <p class="auth-modal-subtitle">Please log in to continue</p>
                </div>
                
                <div class="auth-modal-body">
                    <form id="loginForm" class="auth-form">
                        <div class="form-group">
                            <label for="loginUsername">Username</label>
                            <input 
                                type="text" 
                                id="loginUsername" 
                                class="form-control" 
                                required 
                                autocomplete="username"
                                placeholder="Enter your username"
                            />
                        </div>
                        
                        <div class="form-group">
                            <label for="loginPassword">Password</label>
                            <input 
                                type="password" 
                                id="loginPassword" 
                                class="form-control" 
                                required 
                                autocomplete="current-password"
                                placeholder="Enter your password"
                            />
                        </div>
                        
                        <div class="auth-form-actions">
                            <button type="submit" class="btn btn-primary btn-block">
                                <i data-lucide="log-in"></i>
                                <span>Log In</span>
                            </button>
                        </div>
                        
                        <div class="auth-form-footer">
                            <p>Don't have an account? <a href="#" onclick="showRegisterModal(); return false;">Register</a></p>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('authModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Add event listener to form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    
    // Initialize Lucide icons
    setTimeout(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 100);
}

// Show registration modal
function showRegisterModal() {
    const modalHtml = `
        <div class="auth-modal" id="authModal">
            <div class="auth-modal-content">
                <div class="auth-modal-header">
                    <h2 class="auth-modal-title">Create Your Account</h2>
                    <p class="auth-modal-subtitle">Get started with Proximity</p>
                </div>
                
                <div class="auth-modal-body">
                    <form id="registerForm" class="auth-form">
                        <div class="form-group">
                            <label for="registerUsername">Username</label>
                            <input 
                                type="text" 
                                id="registerUsername" 
                                class="form-control" 
                                required 
                                autocomplete="username"
                                placeholder="Choose a username"
                                minlength="3"
                            />
                            <small class="form-text">At least 3 characters</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="registerEmail">Email</label>
                            <input 
                                type="email" 
                                id="registerEmail" 
                                class="form-control" 
                                required 
                                autocomplete="email"
                                placeholder="your@email.com"
                            />
                        </div>
                        
                        <div class="form-group">
                            <label for="registerPassword">Password</label>
                            <input 
                                type="password" 
                                id="registerPassword" 
                                class="form-control" 
                                required 
                                autocomplete="new-password"
                                placeholder="Choose a strong password"
                                minlength="8"
                            />
                            <small class="form-text">At least 8 characters</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="registerPasswordConfirm">Confirm Password</label>
                            <input 
                                type="password" 
                                id="registerPasswordConfirm" 
                                class="form-control" 
                                required 
                                autocomplete="new-password"
                                placeholder="Confirm your password"
                            />
                        </div>
                        
                        <div class="auth-form-actions">
                            <button type="submit" class="btn btn-primary btn-block">
                                <i data-lucide="user-plus"></i>
                                <span>Create Account</span>
                            </button>
                        </div>
                        
                        <div class="auth-form-footer">
                            <p>Already have an account? <a href="#" onclick="showLoginModal(); return false;">Log In</a></p>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    const existingModal = document.getElementById('authModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Add event listener to form
    document.getElementById('registerForm').addEventListener('submit', handleRegister);
    
    // Initialize Lucide icons
    setTimeout(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 100);
}

// Handle login form submission
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showNotification('Please enter username and password', 'error');
        return;
    }
    
    // Disable submit button
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Logging in...</span>';
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.access_token) {
            // Store token and user info
            Auth.setToken(data.access_token, data.user);
            
            showNotification('Login successful! Welcome back.', 'success');
            
            // Close modal
            const modal = document.getElementById('authModal');
            if (modal) {
                modal.remove();
            }
            
            // Initialize the app
            setTimeout(() => {
                init();
            }, 500);
        } else {
            showNotification(data.detail || 'Login failed', 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed. Please check your connection.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    }
}

// Handle registration form submission
async function handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value;
    
    // Validation
    if (!username || !email || !password) {
        showNotification('Please fill in all fields', 'error');
        return;
    }
    
    if (username.length < 3) {
        showNotification('Username must be at least 3 characters', 'error');
        return;
    }
    
    if (password.length < 8) {
        showNotification('Password must be at least 8 characters', 'error');
        return;
    }
    
    if (password !== passwordConfirm) {
        showNotification('Passwords do not match', 'error');
        return;
    }
    
    // Disable submit button
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Creating account...</span>';
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password,
                role: 'admin'  // First user is admin
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.access_token) {
            // Store token and user info
            Auth.setToken(data.access_token, data.user);
            
            showNotification('Account created successfully! Welcome to Proximity.', 'success');
            
            // Close modal
            const modal = document.getElementById('authModal');
            if (modal) {
                modal.remove();
            }
            
            // Initialize the app
            setTimeout(() => {
                init();
            }, 500);
        } else {
            showNotification(data.detail || 'Registration failed', 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Registration failed. Please check your connection.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    }
}

// Check if this is first time setup (no users exist)
async function checkFirstTimeSetup() {
    try {
        // Try to get system info without auth to see if we get a specific error
        const response = await fetch(`${API_BASE}/auth/first-time-check`);
        
        if (response.status === 404) {
            // Endpoint doesn't exist, assume we need registration
            return true;
        }
        
        const data = await response.json();
        return data.is_first_time || false;
    } catch (error) {
        // If we can't check, assume we need to show registration
        return true;
    }
}

// Update user info in sidebar
function updateUserInfo() {
    const user = Auth.getUser();
    if (!user) return;
    
    const userNameElement = document.querySelector('.user-name');
    const userRoleElement = document.querySelector('.user-role');
    const userAvatarElement = document.querySelector('.user-avatar');
    
    if (userNameElement) {
        userNameElement.textContent = user.username || 'User';
    }
    
    if (userRoleElement) {
        userRoleElement.textContent = user.role === 'admin' ? 'Administrator' : 'User';
    }
    
    if (userAvatarElement) {
        // Create initials from username
        const initials = user.username ? user.username.substring(0, 2).toUpperCase() : 'US';
        userAvatarElement.textContent = initials;
    }
}

// Add logout button handler
function setupLogoutHandler() {
    // Add logout option to user profile menu
    const userProfile = document.querySelector('.user-profile');
    if (userProfile) {
        userProfile.style.cursor = 'pointer';
        userProfile.addEventListener('click', (e) => {
            if (confirm('Are you sure you want to log out?')) {
                Auth.logout();
            }
        });
    }
}
