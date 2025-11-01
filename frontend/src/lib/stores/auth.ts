/**
 * Authentication Store - Atomic State Management (Refactored)
 *
 * Key Principles:
 * - ATOMIC STATE: User state is updated in a single synchronous operation.
 * - DERIVED AUTHENTICATION: isAuthenticated is computed from user state, not stored separately.
 * - NO RACE CONDITIONS: Authentication status is always consistent with user data.
 * - HttpOnly cookies are the source of truth for the session.
 * - The store hydrates itself by calling a 'user' endpoint on startup.
 */
import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import api from '$lib/api'; // Import the api client
import * as Sentry from '@sentry/sveltekit';
import { logger } from '$lib/logger';

export interface User {
	id: number;
	pk: number; // dj-rest-auth often returns 'pk'
	username: string;
	email: string;
	first_name: string;
	last_name: string;
}

/**
 * Core authentication state - SIMPLIFIED
 * The ONLY source of truth is the user object.
 * isInitialized tracks whether init() has completed.
 */
interface AuthState {
	user: User | null;
	isInitialized: boolean;
}

function createAuthStore() {
	const initialState: AuthState = {
		user: null,
		isInitialized: false
	};

	const { subscribe, set, update } = writable<AuthState>(initialState);

	/**
	 * ATOMIC STATE UPDATE: Sets user and handles Sentry in a single operation.
	 * This ensures state consistency - no intermediate states possible.
	 */
	const setUserState = (user: User | null, isInitialized: boolean = true) => {
		// Update Sentry context
		if (user) {
			Sentry.setUser({
				id: user.pk || user.id,
				username: user.username,
				email: user.email
			});
			logger.debug('✅ [AuthStore] Session is valid. User set:', user.username);
		} else {
			Sentry.setUser(null);
			logger.debug('🔐 [AuthStore] Session is invalid or ended. User cleared.');
		}

		// ATOMIC UPDATE: Single operation, no intermediate state
		set({ user, isInitialized });
	};

	return {
		subscribe,

		/**
		 * Initialize the store by verifying the session with the backend.
		 * This is the ONLY way to confirm authentication status on startup.
		 * CRITICAL: This function is async and MUST complete before any API calls.
		 */
		init: async () => {
			if (!browser) return;
			logger.debug('1️⃣ [AuthStore] init() called - Verifying session with backend...');

			const response = await api.getUser();

			if (response.success && response.data) {
				// The HttpOnly cookie was valid, backend returned user data.
				// ATOMIC: User and initialized status set together
				setUserState(response.data, true);
			} else {
				// No valid cookie, or an error occurred.
				// ATOMIC: Clear user and mark as initialized
				setUserState(null, true);
			}
		},

		/**
		 * Login: The API client handles the request. Here we just process the result.
		 * The browser automatically receives the HttpOnly cookie from the server.
		 */
		login: (user: User) => {
			logger.debug('🟢 [AuthStore] login() called - Setting user state.');
			// ATOMIC: User is set in one operation
			setUserState(user, true);
		},

		/**
		 * Logout: Tell the backend to clear the session cookie.
		 */
		logout: async () => {
			logger.debug('👋 [AuthStore] logout() called - Logging out via API...');
			await api.logout(); // Tell backend to delete the cookie
			// ATOMIC: User is cleared in one operation
			setUserState(null, true);
		},

		/**
		 * Update user info (e.g., after profile changes)
		 */
		updateUser: (user: User) => {
			update(state => {
				// Preserve isInitialized, update user
				if (user) {
					Sentry.setUser({
						id: user.pk || user.id,
						username: user.username,
						email: user.email
					});
				}
				return { ...state, user };
			});
		}
	};
}

export const authStore = createAuthStore();

/**
 * DERIVED STORE: isAuthenticated
 *
 * This is the KEY to atomic state management. Instead of storing isAuthenticated
 * as a separate piece of state, we DERIVE it from the user object.
 *
 * This guarantees that:
 * - If isAuthenticated is true, user is ALWAYS non-null
 * - If isAuthenticated is false, user is ALWAYS null
 * - NO RACE CONDITIONS are possible
 *
 * Components and stores should subscribe to this derived store instead of
 * checking a stored isAuthenticated flag.
 */
export const isAuthenticated = derived(
	authStore,
	$authStore => $authStore.user !== null
);

// Derived store for current user (convenience accessor)
export const currentUser = derived(authStore, $authStore => $authStore.user);
