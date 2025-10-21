/**
 * Svelte store for managing deployed applications state.
 * Provides real-time polling and state management for deployed apps.
 * 
 * AUTH-AWARE: This store waits for authStore to be initialized before
 * making any API calls, preventing 401 errors from race conditions.
 */

import { writable, derived, get } from 'svelte/store';
import { api } from '../api';
import { authStore } from './auth';
import { SoundService } from '../services/SoundService';
import type { Writable } from 'svelte/store';

export interface DeployedApp {
	id: string;
	catalog_app_id: string;
	name: string;
	hostname: string;
	status: 'deploying' | 'cloning' | 'running' | 'stopped' | 'error' | 'deleting';
	icon?: string;
	category?: string;
	description?: string;
	host_id: number;
	node_name: string;
	vmid?: number;
	ports?: Record<string, number>;
	environment?: Record<string, string>;
	volumes?: Record<string, string>;
	created_at: string;
	updated_at: string;
	deployment_logs?: string[];
}

interface AppsState {
	apps: DeployedApp[];
	loading: boolean;
	error: string | null;
	lastUpdated: Date | null;
}

// Create the main store
function createAppsStore() {
	const initialState: AppsState = {
		apps: [],
		loading: false,
		error: null,
		lastUpdated: null
	};

	const { subscribe, set, update }: Writable<AppsState> = writable(initialState);

	let pollingInterval: number | null = null;

	// Fetch all deployed apps (AUTH-AWARE)
	async function fetchApps() {
		// 🔐 SAFETY CHECK: Verify authStore is initialized before making API call
		const currentAuthState = get(authStore);
		if (!currentAuthState.isInitialized) {
			console.warn('⚠️ [myAppsStore] fetchApps() called before authStore initialized. Skipping to avoid 401.');
			return; // Don't fetch if auth isn't ready
		}
		
		// Capture previous state for comparison
		let previousApps: DeployedApp[] = [];
		update((state) => {
			previousApps = state.apps;
			return { ...state, loading: true, error: null };
		});

		const response = await api.listApps();

		if (response.success && response.data) {
			// Extract apps array from response object
			const appsArray = response.data.apps || response.data || [];

			// Detect state transitions and play appropriate sounds
			appsArray.forEach((newApp: DeployedApp) => {
				const previousApp = previousApps.find(app => app.id === newApp.id);
				if (previousApp && previousApp.status !== newApp.status) {
					// State transition detected
					if ((previousApp.status === 'deploying' || previousApp.status === 'cloning') &&
					    newApp.status === 'running') {
						// Success: deployment/clone completed
						SoundService.play('success');
					} else if (previousApp.status !== 'error' && newApp.status === 'error') {
						// Error: app entered error state
						SoundService.play('error');
					}
				}
			});

			update((state) => {
				// 🔧 PRESERVE OPTIMISTIC PLACEHOLDERS FOR CLONING & DEPLOYING
				// Step 1: Find all cloning placeholders currently in state
				const cloningPlaceholders = state.apps.filter(
					app => app.status === 'cloning' && app.id.startsWith('cloning-')
				);

				// Step 2: Find all deploying placeholders currently in state
				const deployingPlaceholders = state.apps.filter(
					app => app.status === 'deploying' && app.id.startsWith('deploying-temp-')
				);

				// Step 3: Filter out placeholders that have been replaced by real apps
				const unresolvedCloningPlaceholders = cloningPlaceholders.filter(
					placeholder => !appsArray.some((realApp: DeployedApp) => realApp.hostname === placeholder.hostname)
				);

				const unresolvedDeployingPlaceholders = deployingPlaceholders.filter(
					placeholder => !appsArray.some((realApp: DeployedApp) => realApp.hostname === placeholder.hostname)
				);

				// Step 4: Combine real apps from server with unresolved placeholders
				const finalApps = [
					...unresolvedCloningPlaceholders,
					...unresolvedDeployingPlaceholders,
					...appsArray
				];

				return {
					...state,
					apps: finalApps,
					loading: false,
					lastUpdated: new Date()
				};
			});
		} else {
			update((state) => ({
				...state,
				error: response.error || 'Failed to fetch apps',
				loading: false
			}));
		}
	}

	// Fetch a single app (useful for updating status) - AUTH-AWARE
	async function refreshApp(appId: string) {
		// 🔐 SAFETY CHECK: Verify authStore is initialized
		const currentAuthState = get(authStore);
		if (!currentAuthState.isInitialized) {
			console.warn('⚠️ [myAppsStore] refreshApp() called before authStore initialized. Skipping.');
			return;
		}
		
		const response = await api.getApp(appId);

		if (response.success && response.data) {
			// Capture previous state for sound feedback
			let previousApp: DeployedApp | undefined;
			update((state) => {
				previousApp = state.apps.find(app => app.id === appId);
				return state;
			});

			// Detect state transition and play appropriate sound
			if (previousApp && previousApp.status !== response.data.status) {
				if ((previousApp.status === 'deploying' || previousApp.status === 'cloning') &&
				    response.data.status === 'running') {
					// Success: deployment/clone completed
					SoundService.play('success');
				} else if (previousApp.status !== 'error' && response.data.status === 'error') {
					// Error: app entered error state
					SoundService.play('error');
				}
			}

			update((state) => ({
				...state,
				apps: state.apps.map((app) => (app.id === appId ? response.data : app))
			}));
		}
	}

	// Start polling for real-time updates (AUTH-AWARE)
	function startPolling(intervalMs: number = 5000) {
		stopPolling(); // Clear any existing interval

		// 🔐 CRITICAL: Wait for authStore to be initialized before fetching
		const currentAuthState = get(authStore);
		
		if (!currentAuthState.isInitialized) {
			console.log('📦 [myAppsStore] Waiting for authStore to initialize...');
			
			// Subscribe to authStore and wait for initialization
			const unsubscribe = authStore.subscribe((authState) => {
				if (authState.isInitialized) {
					console.log('✅ [myAppsStore] authStore is ready! Starting polling...');
					unsubscribe(); // Stop listening once we're ready
					
					// Now we can safely fetch
					fetchApps();
					
					// Set up polling interval
					pollingInterval = setInterval(() => {
						fetchApps();
					}, intervalMs) as unknown as number;
				}
			});
		} else {
			// authStore is already initialized, proceed immediately
			console.log('✅ [myAppsStore] authStore was already ready. Starting polling immediately...');
			
			// Initial fetch
			fetchApps();

			// Set up polling
			pollingInterval = setInterval(() => {
				fetchApps();
			}, intervalMs) as unknown as number;
		}
	}

	// Stop polling
	function stopPolling() {
		if (pollingInterval !== null) {
			clearInterval(pollingInterval);
			pollingInterval = null;
		}
	}

	// Perform an action on an app
	async function performAction(
		appId: string,
		action: 'start' | 'stop' | 'restart' | 'delete'
	): Promise<{ success: boolean; error?: string }> {
		// Optimistically update the state
		if (action === 'delete') {
			update((state) => ({
				...state,
				apps: state.apps.map((app) =>
					app.id === appId ? { ...app, status: 'deleting' as const } : app
				)
			}));
		}

		const response = await api.performAppAction(appId, action);

		if (response.success) {
			// For delete action, remove from list after success
			if (action === 'delete') {
				update((state) => ({
					...state,
					apps: state.apps.filter((app) => app.id !== appId)
				}));
			} else {
				// Refresh the specific app to get updated status
				await refreshApp(appId);
			}
			return { success: true };
		} else {
			// Revert optimistic update on error
			await refreshApp(appId);
			return { success: false, error: response.error };
		}
	}

	// Clone an existing app
	async function cloneApplication(
		sourceAppId: string,
		newHostname: string
	): Promise<{ success: boolean; error?: string }> {
		console.log('myAppsStore: cloneApplication called. Performing optimistic update...');

		// 🔧 OPTIMISTIC UPDATE - BEFORE API CALL
		// Create placeholder immediately for instant UI feedback
		const optimisticId = `cloning-${Date.now()}`;
		let sourceApp: DeployedApp | undefined;

		update((state: AppsState) => {
			sourceApp = state.apps.find((app: DeployedApp) => app.id === sourceAppId);
			if (sourceApp) {
				const placeholderApp: DeployedApp = {
					...sourceApp,
					id: optimisticId, // Temporary ID until backend provides real one
					hostname: newHostname,
					name: `${sourceApp.name}-clone`,
					status: 'cloning' as const,
					created_at: new Date().toISOString(),
					updated_at: new Date().toISOString()
				};
				console.log('myAppsStore: Optimistic update applied. State should now contain a cloning card:', placeholderApp);
				return {
					...state,
					apps: [...state.apps, placeholderApp]
				};
			}
			console.warn('myAppsStore: Source app not found for optimistic update');
			return state;
		});

		// NOW make the API call
		const response = await api.cloneApp(sourceAppId, newHostname);

		if (response.success) {
			// Replace optimistic placeholder with real data from backend
			setTimeout(() => {
				fetchApps(); // This will replace the optimistic app with real data
			}, 2000);

			return { success: true };
		} else {
			// ROLLBACK: Remove optimistic placeholder on error
			update((state: AppsState) => ({
				...state,
				apps: state.apps.filter((app: DeployedApp) => app.id !== optimisticId)
			}));
			console.error('myAppsStore: Clone API failed. Optimistic update rolled back.');
			return { success: false, error: response.error };
		}
	}

	// Deploy a new app
	async function deployApp(deploymentData: {
		catalog_id: string;
		hostname: string;
		node?: string;
		config?: Record<string, any>;
		ports?: Record<string, number>;
		environment?: Record<string, string>;
	}): Promise<{ success: boolean; data?: any; error?: string }> {
		const response = await api.deployApp(deploymentData);

		if (response.success) {
			// Refresh the list to include the new app
			await fetchApps();
			return { success: true, data: response.data };
		} else {
			return { success: false, error: response.error };
		}
	}

	return {
		subscribe,
		fetchApps,
		refreshApp,
		startPolling,
		stopPolling,
		performAction,
		cloneApplication,
		deployApp,
		reset: () => set(initialState)
	};
}

export const myAppsStore = createAppsStore();

// Derived store for apps by status
export const appsByStatus = derived(myAppsStore, ($apps: AppsState) => {
	const byStatus: Record<string, DeployedApp[]> = {
		deploying: [],
		cloning: [],
		running: [],
		stopped: [],
		error: [],
		deleting: []
	};

	$apps.apps.forEach((app: DeployedApp) => {
		if (byStatus[app.status]) {
			byStatus[app.status].push(app);
		}
	});

	return byStatus;
});

// Derived store for deployment/cloning in progress check
export const hasDeployingApps = derived(myAppsStore, ($apps: AppsState) => {
	return $apps.apps.some((app: DeployedApp) => app.status === 'deploying' || app.status === 'cloning');
});
