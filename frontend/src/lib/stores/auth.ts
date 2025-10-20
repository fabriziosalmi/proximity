/**
 * Authentication Store
 * Manages user authentication state across the application
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
}

function createAuthStore() {
	// Initialize from localStorage if available
	const initialState: AuthState = {
		user: null,
		token: null,
		isAuthenticated: false
	};

	if (browser) {
		const storedToken = localStorage.getItem('access_token');
		const storedUser = localStorage.getItem('user');
		
		if (storedToken && storedUser) {
			try {
				initialState.token = storedToken;
				initialState.user = JSON.parse(storedUser);
				initialState.isAuthenticated = true;
			} catch (e) {
				// Invalid stored data, clear it
				localStorage.removeItem('access_token');
				localStorage.removeItem('user');
			}
		}
	}

	const { subscribe, set, update } = writable<AuthState>(initialState);

	return {
		subscribe,
		
		login: (token: string, user: User) => {
			const newState = {
				user,
				token,
				isAuthenticated: true
			};
			
			if (browser) {
				localStorage.setItem('access_token', token);
				localStorage.setItem('user', JSON.stringify(user));
			}
			
			set(newState);
		},
		
		logout: () => {
			if (browser) {
				localStorage.removeItem('access_token');
				localStorage.removeItem('user');
			}
			
			set({
				user: null,
				token: null,
				isAuthenticated: false
			});
		},
		
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
