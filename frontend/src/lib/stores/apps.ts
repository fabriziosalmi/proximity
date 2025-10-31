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
import { validateAppsResponse, isDeployedApp } from '../types/api';
import { logger } from '../logger';
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
	let isPollingActive = false; // Track if we want polling to be active
	let authUnsubscribe: (() => void) | null = null; // Track auth subscription
	let failureCount = 0; // Track consecutive API failures for exponential backoff
	let basePollingIntervalMs = 5000; // Base interval in milliseconds
	const maxBackoffIntervalMs = 60000; // Max interval (1 minute)

	// Fetch all deployed apps (AUTH-AWARE)
	async function fetchApps() {
		logger.debug('🎯 [myAppsStore] fetchApps() called');
		
		// 🔐 SAFETY CHECK: Verify authStore is initialized before making API call
		const currentAuthState = get(authStore);
		logger.debug('8️⃣ [myAppsStore] Checked authStore state:', {
			isInitialized: currentAuthState.isInitialized,
			hasUser: !!currentAuthState.user
		});
		
		if (!currentAuthState.isInitialized) {
			logger.warn('⚠️ [myAppsStore] fetchApps() called before authStore initialized. Skipping to avoid 401.');
			return; // Don't fetch if auth isn't ready
		}
		
		logger.debug('9️⃣ [myAppsStore] Auth check passed - proceeding with API call');
		
		// Capture previous state for comparison
		let previousApps: DeployedApp[] = [];
		update((state) => {
			previousApps = state.apps;
			return { ...state, loading: true, error: null };
		});

		logger.debug('🔟 [myAppsStore] Calling api.listApps()...');
		const response = await api.listApps();

		if (response.success && response.data) {
			// ✅ Validate and extract apps array with type checking
			const appsArray = validateAppsResponse(response);

			// Reset failure count on successful fetch
			if (failureCount > 0) {
				failureCount = 0;
				logger.debug('✅ [myAppsStore] API success - backoff reset');
			}

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

				logger.debug(`📦 [myAppsStore] Updated apps store:`, {
					totalApps: finalApps.length,
					apiApps: appsArray.length,
					cloningPlaceholders: unresolvedCloningPlaceholders.length,
					deployingPlaceholders: unresolvedDeployingPlaceholders.length,
					hostnames: finalApps.map(app => app.hostname)
				});

				return {
					...state,
					apps: finalApps,
					loading: false,
					lastUpdated: new Date()
				};
			});
		} else {
			// Increment failure count for exponential backoff
			failureCount++;
			const backoffFactor = Math.min(Math.pow(2, failureCount - 1), 10); // Cap at 2^10
			const nextIntervalMs = Math.min(basePollingIntervalMs * backoffFactor, maxBackoffIntervalMs);

			logger.warn(`⚠️ [myAppsStore] API fetch failed (attempt ${failureCount}), backoff interval: ${nextIntervalMs}ms`, {
				error: response.error
			});

			// Update polling interval with exponential backoff
			if (pollingInterval !== null && nextIntervalMs !== basePollingIntervalMs) {
				clearInterval(pollingInterval);
				pollingInterval = setInterval(() => {
					fetchApps();
				}, nextIntervalMs) as unknown as number;
			}

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
			logger.warn('⚠️ [myAppsStore] refreshApp() called before authStore initialized. Skipping.');
			return;
		}

		const response = await api.getApp(appId);

		if (response.success && response.data) {
			// ✅ Validate response data before using
			if (!isDeployedApp(response.data)) {
				logger.error('Invalid app response structure:', response.data);
				return;
			}

			// Capture previous state for sound feedback
			let previousApp: DeployedApp | undefined;
			const appData = response.data;
			
			update((state) => {
				previousApp = state.apps.find(app => app.id === appId);
				return state;
			});

			// Detect state transition and play appropriate sound
			if (previousApp && previousApp.status !== appData.status) {
				if ((previousApp.status === 'deploying' || previousApp.status === 'cloning') &&
				    appData.status === 'running') {
					// Success: deployment/clone completed
					SoundService.play('success');
				} else if (previousApp.status !== 'error' && appData.status === 'error') {
					// Error: app entered error state
					SoundService.play('error');
				}
			}

			update((state) => ({
				...state,
				apps: state.apps.map((app) => (app.id === appId ? appData : app))
			}));
		}
	}

	// Start polling for real-time updates (AUTH-AWARE)
	function startPolling(intervalMs: number = 5000) {
		logger.debug('🎬 [myAppsStore] startPolling() called with interval:', intervalMs);

		// 🔐 Guard against multiple polling instances
		if (isPollingActive && pollingInterval !== null) {
			logger.warn('⚠️ [myAppsStore] Polling already active, ignoring duplicate startPolling() call');
			return;
		}

		stopPolling(); // Clear any existing interval and subscriptions
		isPollingActive = true; // Mark that we want polling to be active
		basePollingIntervalMs = intervalMs; // Set the base interval
		failureCount = 0; // Reset failure count when polling starts

		// 🔐 CRITICAL: Wait for authStore to be initialized before fetching
		const currentAuthState = get(authStore);

		logger.debug('1️⃣1️⃣ [myAppsStore] Checked authStore for initialization:', {
			isInitialized: currentAuthState.isInitialized,
			hasUser: !!currentAuthState.user
		});

		if (!currentAuthState.isInitialized) {
			logger.debug('1️⃣2️⃣ [myAppsStore] Auth NOT initialized yet - subscribing to wait for it...');

			// Subscribe to authStore and wait for initialization
			// Store reference so we can clean up
			let unsubscribeAuth: (() => void) | null = authStore.subscribe((authState) => {
				logger.debug('1️⃣3️⃣ [myAppsStore] Auth subscription callback fired:', {
					isInitialized: authState.isInitialized,
					isPollingActive: isPollingActive
				});

				if (authState.isInitialized && isPollingActive && unsubscribeAuth) {
					logger.debug('1️⃣4️⃣ [myAppsStore] Auth is NOW ready! Starting polling...');

					// Clean up this subscription
					unsubscribeAuth();
					unsubscribeAuth = null;
					authUnsubscribe = null; // Clear the global reference too

					// Now we can safely fetch
					logger.debug('1️⃣5️⃣ [myAppsStore] Triggering initial fetchApps()...');
					fetchApps();

					// Set up polling interval
					pollingInterval = setInterval(() => {
						fetchApps();
					}, intervalMs) as unknown as number;

					logger.debug(`1️⃣6️⃣ [myAppsStore] Polling interval set - will fetch every ${intervalMs}ms`);
				} else if (!isPollingActive && unsubscribeAuth) {
					// Polling was stopped before auth initialized
					logger.debug('🛑 [myAppsStore] Polling stopped before auth initialized, cleaning up subscription');
					unsubscribeAuth();
					unsubscribeAuth = null;
					authUnsubscribe = null;
				}
			});

			authUnsubscribe = unsubscribeAuth;
		} else {
			// authStore is already initialized, proceed immediately
			logger.debug('1️⃣2️⃣ [myAppsStore] Auth ALREADY initialized - starting polling immediately');

			// Initial fetch
			logger.debug('1️⃣3️⃣ [myAppsStore] Triggering initial fetchApps()...');
			fetchApps();

			// Set up polling
			pollingInterval = setInterval(() => {
				fetchApps();
			}, intervalMs) as unknown as number;

			logger.debug(`1️⃣4️⃣ [myAppsStore] Polling interval set - will fetch every ${intervalMs}ms`);
		}
	}

	// Stop polling
	function stopPolling() {
		logger.debug('🛑 [myAppsStore] stopPolling() called');

		isPollingActive = false; // Mark that polling should stop
		failureCount = 0; // Reset failure count when stopping

		if (pollingInterval !== null) {
			clearInterval(pollingInterval);
			pollingInterval = null;
			logger.debug('🛑 [myAppsStore] Polling interval cleared');
		}

		// Clean up auth subscription if it exists
		if (authUnsubscribe) {
			authUnsubscribe();
			authUnsubscribe = null;
			logger.debug('🛑 [myAppsStore] Auth subscription cleaned up');
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
		logger.debug('myAppsStore: cloneApplication called. Performing optimistic update...');

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
				logger.debug('myAppsStore: Optimistic update applied. State should now contain a cloning card:', placeholderApp);
				return {
					...state,
					apps: [...state.apps, placeholderApp]
				};
			}
			logger.warn('myAppsStore: Source app not found for optimistic update');
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
			logger.error('myAppsStore: Clone API failed. Optimistic update rolled back.');
			return { success: false, error: response.error };
		}
	}

	// Deploy a new app with OPTIMISTIC UPDATE
	async function deployApp(deploymentData: {
		catalog_id: string;
		hostname: string;
		node?: string;
		config?: Record<string, any>;
		ports?: Record<string, number>;
		environment?: Record<string, string>;
	}): Promise<{ success: boolean; data?: any; error?: string }> {
		logger.debug('📦 [myAppsStore] deployApp called. Performing optimistic update...');

		// 🔧 OPTIMISTIC UPDATE - BEFORE API CALL
		// Create placeholder immediately for instant UI feedback
		const optimisticId = `deploying-temp-${Date.now()}`;

		// Create a placeholder app object with known data
		const placeholderApp: DeployedApp = {
			id: optimisticId,
			catalog_app_id: deploymentData.catalog_id,
			name: deploymentData.hostname, // Will be updated with real name from API
			hostname: deploymentData.hostname,
			status: 'deploying' as const,
			icon: undefined,
			category: undefined,
			description: undefined,
			host_id: 0, // Will be updated from API response
			node_name: deploymentData.node || 'unknown',
			vmid: undefined,
			ports: deploymentData.ports || {},
			environment: deploymentData.environment || {},
			volumes: {},
			created_at: new Date().toISOString(),
			updated_at: new Date().toISOString(),
			deployment_logs: []
		};

		logger.debug('📦 [myAppsStore] Optimistic placeholder created:', placeholderApp);

		// Add placeholder to store immediately
		update((state: AppsState) => {
			logger.debug('📦 [myAppsStore] Adding deploying placeholder to apps array');
			return {
				...state,
				apps: [...state.apps, placeholderApp]
			};
		});

		// NOW make the API call
		logger.debug('📦 [myAppsStore] Making API call to deploy app...');
		const response = await api.deployApp(deploymentData);

		if (response.success) {
			logger.debug('✅ [myAppsStore] Deployment API call succeeded');
			
			// Replace optimistic placeholder with real data from backend
			// Use a short delay to allow the backend to process
			setTimeout(() => {
				logger.debug('🔄 [myAppsStore] Fetching apps to replace placeholder with real data');
				fetchApps(); // This will replace the optimistic app with real data
			}, 2000);

			return { success: true, data: response.data };
		} else {
			logger.error('❌ [myAppsStore] Deployment API call failed:', response.error);
			
			// ROLLBACK: Remove optimistic placeholder on error
			update((state: AppsState) => {
				logger.debug('🔄 [myAppsStore] Rolling back optimistic placeholder');
				return {
					...state,
					apps: state.apps.filter((app: DeployedApp) => app.id !== optimisticId)
				};
			});
			
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
