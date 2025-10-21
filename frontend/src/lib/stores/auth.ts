/**
 * Authentication Store - Single Source of Truth (Refactored for HttpOnly Cookies)
 *
 * Key Principles:
 * - Manages user state and authentication status, NOT tokens.
 * - The browser's cookie jar is the single source of truth for the session.
 * - The store hydrates itself by calling a 'user' endpoint on startup.
 */
import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import api from '$lib/api'; // Import the api client
import * as Sentry from '@sentry/sveltekit';

export interface User {
	id: number;
	pk: number; // dj-rest-auth often returns 'pk'
	username: string;
	email: string;
	first_name: string;
	last_name: string;
}

interface AuthState {
	user: User | null;
	isAuthenticated: boolean;
	isInitialized: boolean; // Signals when init() has completed
}

function createAuthStore() {
	const initialState: AuthState = {
		user: null,
		isAuthenticated: false,
		isInitialized: false
	};

	const { subscribe, set, update } = writable<AuthState>(initialState);

	// Function to set the user state and handle Sentry context
	const setUserState = (user: User | null) => {
		if (user) {
			set({ user, isAuthenticated: true, isInitialized: true });
			Sentry.setUser({
				id: user.pk || user.id,
				username: user.username,
				email: user.email
			});
			console.log('✅ [AuthStore] Session is valid. User set:', user.username);
		} else {
			set({ user: null, isAuthenticated: false, isInitialized: true });
			Sentry.setUser(null);
			console.log('🔐 [AuthStore] Session is invalid or ended. User cleared.');
		}
	};

	return {
		subscribe,

		/**
		 * Initialize the store by verifying the session with the backend.
		 * This is the ONLY way to confirm authentication status on startup.
		 */
		init: async () => {
			if (!browser) return;
			console.log('1️⃣ [AuthStore] init() called - Verifying session with backend...');

			const response = await api.getUser();

			if (response.success && response.data) {
				// The HttpOnly cookie was valid, backend returned user data.
				setUserState(response.data);
			} else {
				// No valid cookie, or an error occurred.
				setUserState(null);
			}
		},

		/**
		 * Login: The API client handles the request. Here we just process the result.
		 * The browser automatically receives the HttpOnly cookie from the server.
		 */
		login: (user: User) => {
			console.log('🟢 [AuthStore] login() called - Setting user state.');
			setUserState(user);
		},

		/**
		 * Logout: Tell the backend to clear the session cookie.
		 */
		logout: async () => {
			console.log('👋 [AuthStore] logout() called - Logging out via API...');
			await api.logout(); // Tell backend to delete the cookie
			setUserState(null); // Clear the state in the frontend
		},

		/**
		 * Update user info (e.g., after profile changes)
		 */
		updateUser: (user: User) => {
			update(state => {
				return { ...state, user };
			});
		}
	};
}

export const authStore = createAuthStore();

// Derived store for easy access to authentication status
export const isAuthenticated = derived(authStore, $authStore => $authStore.isAuthenticated);

// Derived store for current user
export const currentUser = derived(authStore, $authStore => $authStore.user);