/**
 * Authentication Store - Single Source of Truth
 * 
 * This is the ONLY place in the frontend that manages authentication state.
 * All components, services, and API clients MUST use this store.
 * 
 * Key Principles:
 * - Singleton pattern ensures one source of truth
 * - Bidirectional sync with localStorage
 * - Reactive updates propagate to all subscribers
 * - No direct localStorage access anywhere else
 */
import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

export interface User {
	id: number;
	username: string;
	email: string;
	preferred_theme?: string;
}

interface AuthState {
	user: User | null;
	token: string | null;
	isAuthenticated: boolean;
	isInitialized: boolean; // NEW: Signals when init() has completed
}

function createAuthStore() {
	// Start with empty state - will be initialized via init()
	const initialState: AuthState = {
		user: null,
		token: null,
		isAuthenticated: false,
		isInitialized: false // Store is not ready until init() completes
	};

	const { subscribe, set, update } = writable<AuthState>(initialState);

	return {
		subscribe,
		
		/**
		 * Initialize the store from localStorage
		 * MUST be called once on app startup in +layout.svelte
		 */
		init: () => {
			if (!browser) return;
			
			console.log('🔐 [AuthStore] Initializing from localStorage...');
			
			const storedToken = localStorage.getItem('access_token');
			const storedUser = localStorage.getItem('user');
			
			if (storedToken && storedUser) {
				try {
					const user = JSON.parse(storedUser);
					const newState = {
						token: storedToken,
						user,
						isAuthenticated: true,
						isInitialized: true // CRITICAL: Signal that initialization is complete
					};
					set(newState);
					console.log('✅ [AuthStore] Initialized with existing session:', { 
						userId: user.id, 
						username: user.username,
						tokenPrefix: storedToken.substring(0, 20) + '...'
					});
					
					// Signal to E2E tests that we're ready
					if (browser) {
						document.body.setAttribute('data-api-client-ready', 'true');
					}
				} catch (e) {
					console.error('❌ [AuthStore] Invalid stored data, clearing:', e);
					// Invalid stored data, clear it
					localStorage.removeItem('access_token');
					localStorage.removeItem('user');
					// Still mark as initialized even if session is invalid
					update(state => ({ ...state, isInitialized: true }));
				}
			} else {
				console.log('ℹ️ [AuthStore] No existing session found');
				// Mark as initialized even without a session
				update(state => ({ ...state, isInitialized: true }));
			}
		},
		
		/**
		 * Login: Store token and user, sync to localStorage
		 */
		login: (token: string, user: User) => {
			console.log('🔐 [AuthStore] Logging in:', { 
				userId: user.id, 
				username: user.username,
				tokenPrefix: token.substring(0, 20) + '...'
			});
			
			const newState = {
				user,
				token,
				isAuthenticated: true,
				isInitialized: true // Login also marks the store as initialized
			};
			
			// Sync to localStorage
			if (browser) {
				localStorage.setItem('access_token', token);
				localStorage.setItem('user', JSON.stringify(user));
				// Signal readiness to E2E tests
				document.body.setAttribute('data-api-client-ready', 'true');
			}
			
			// Update store (this will trigger all subscribers including ApiClient)
			set(newState);
			
			console.log('✅ [AuthStore] Login complete - all subscribers notified');
		},
		
		/**
		 * Logout: Clear everything (but keep isInitialized = true)
		 */
		logout: () => {
			console.log('🔐 [AuthStore] Logging out...');
			
			// Clear localStorage
			if (browser) {
				localStorage.removeItem('access_token');
				localStorage.removeItem('user');
				document.body.removeAttribute('data-api-client-ready');
			}
			
			// Clear store but keep isInitialized = true (store is still ready to use)
			set({
				user: null,
				token: null,
				isAuthenticated: false,
				isInitialized: true // Store remains initialized after logout
			});
			
			console.log('✅ [AuthStore] Logout complete');
		},
		
		/**
		 * Update user info (e.g., after profile changes)
		 */
		updateUser: (user: User) => {
			update(state => {
				if (browser && user) {
					localStorage.setItem('user', JSON.stringify(user));
				}
				return { ...state, user };
			});
		}
	};
}

export const authStore = createAuthStore();

// Derived store for easy access to authentication status
export const isAuthenticated = derived(
	authStore,
	$authStore => $authStore.isAuthenticated
);

// Derived store for current user
export const currentUser = derived(
	authStore,
	$authStore => $authStore.user
);
