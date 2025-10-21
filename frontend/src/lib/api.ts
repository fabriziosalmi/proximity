/**
 * API client library for Proximity 2.0 frontend.
 * 
 * CRITICAL: This client subscribes to authStore as the SINGLE SOURCE OF TRUTH.
 * It NEVER accesses localStorage directly. All auth state flows through authStore.
 */

import * as Sentry from '@sentry/sveltekit';
import { authStore } from '$lib/stores/auth';
import { get } from 'svelte/store';

const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
	success: boolean;
	data?: T;
	error?: string;
}

class ApiClient {
	private baseUrl: string;
	private accessToken: string | null = null;

	constructor(baseUrl: string = API_BASE_URL) {
		this.baseUrl = baseUrl;
		
		console.log('🏗️ [ApiClient] Constructor called - setting up authStore subscription');
		
		// Subscribe to authStore - this is the ONLY way to get the token
		if (typeof window !== 'undefined') {
			authStore.subscribe(state => {
				const previousToken = this.accessToken;
				this.accessToken = state.token;
				
				console.log(`6️⃣ [ApiClient] Subscription fired - Auth state received:`, {
					isInitialized: state.isInitialized,
					isAuthenticated: state.isAuthenticated,
					tokenChanged: previousToken !== this.accessToken,
					tokenStatus: this.accessToken ? 'SET' : 'NULL',
					tokenPrefix: this.accessToken ? this.accessToken.substring(0, 20) + '...' : 'NULL'
				});
				
				// Log for debugging (never log the actual token!)
				if (this.accessToken) {
					console.log('7️⃣ [ApiClient] Token IS SET - Ready for authenticated requests');
					// Signal to document that we're ready
					if (state.isInitialized && typeof document !== 'undefined') {
						document.body.setAttribute('data-api-client-ready', 'true');
					}
				} else {
					console.log('7️⃣ [ApiClient] Token IS NULL - Operating in unauthenticated mode');
				}
			});
		}
	}

	/**
	 * @deprecated Use authStore.login() instead
	 * This method is kept for backward compatibility but will be removed
	 */
	setToken(token: string) {
		console.warn('⚠️ [ApiClient] setToken() is deprecated. Use authStore.login() instead.');
		// Do nothing - the token should come through authStore
	}

	/**
	 * @deprecated Use authStore.logout() instead
	 */
	clearToken() {
		console.warn('⚠️ [ApiClient] clearToken() is deprecated. Use authStore.logout() instead.');
		// Do nothing - logout should go through authStore
	}

	private async request<T>(
		endpoint: string,
		options: RequestInit = {}
	): Promise<ApiResponse<T>> {
		console.log(`🚀 [ApiClient] request() called for ${options.method || 'GET'} ${endpoint}`, {
			hasToken: !!this.accessToken,
			tokenPrefix: this.accessToken ? this.accessToken.substring(0, 20) + '...' : 'NULL'
		});
		
		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
			...(options.headers as Record<string, string>)
		};

		// Get token from internal state (updated by authStore subscription)
		if (this.accessToken) {
			headers['Authorization'] = `Bearer ${this.accessToken}`;
			console.log(`🔑 [ApiClient] Authorization header ADDED to request`);
		} else {
			console.log(`⚠️  [ApiClient] NO Authorization header - token is NULL`);
		}

		try {
			console.log(`📡 [ApiClient] Executing fetch to ${this.baseUrl}${endpoint}`);
			const response = await fetch(`${this.baseUrl}${endpoint}`, {
				...options,
				headers
			});

			console.log(`🌐 API ${options.method || 'GET'} ${endpoint}:`, {
				status: response.status,
				ok: response.ok
			});

			const data = await response.json();
			console.log(`📦 Response data:`, data);

			if (!response.ok) {
				console.error(`❌ API Error ${response.status}:`, data);
				return {
					success: false,
					error: data.error || data.detail || 'An error occurred'
				};
			}

			return {
				success: true,
				data
			};
		} catch (error) {
			console.error(`💥 API Exception for ${endpoint}:`, error);
			return {
				success: false,
				error: error instanceof Error ? error.message : 'Network error'
			};
		}
	}

	// Authentication
	async login(username: string, password: string) {
		const response = await this.request<{ access_token: string; user: any }>('/api/core/auth/login', {
			method: 'POST',
			body: JSON.stringify({ username, password })
		});

		// NOTE: The actual login state management happens in the UI layer
		// The login page calls authStore.login() with the response data
		// We just return the response here
		
		if (response.success && response.data?.user) {
			// Set Sentry user context for better error tracking
			Sentry.setUser({
				id: response.data.user.id,
				username: response.data.user.username,
				email: response.data.user.email
			});
		}

		return response;
	}

	async register(username: string, email: string, password: string) {
		return this.request('/api/core/auth/register', {
			method: 'POST',
			body: JSON.stringify({ username, email, password })
		});
	}

	logout() {
		// Clear Sentry user context on logout
		Sentry.setUser(null);
		// NOTE: The actual logout happens through authStore.logout() in the UI
	}

	// System
	async getSystemInfo() {
		return this.request('/api/core/system/info');
	}

	async healthCheck() {
		return this.request('/api/core/health');
	}

	// Proxmox Hosts
	async listHosts() {
		return this.request('/api/proxmox/hosts');
	}

	async createHost(data: any) {
		return this.request('/api/proxmox/hosts', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	async getHost(id: number) {
		return this.request(`/api/proxmox/hosts/${id}`);
	}

	async updateHost(id: number, data: any) {
		return this.request(`/api/proxmox/hosts/${id}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	}

	async deleteHost(id: number) {
		return this.request(`/api/proxmox/hosts/${id}`, {
			method: 'DELETE'
		});
	}

	async testHostConnection(id: number) {
		return this.request(`/api/proxmox/hosts/${id}/test`, {
			method: 'POST'
		});
	}

	async syncNodes(id: number) {
		return this.request(`/api/proxmox/hosts/${id}/sync-nodes`, {
			method: 'POST'
		});
	}

	// Proxmox Nodes
	async getProxmoxNodes(hostId?: number) {
		const params = hostId ? `?host_id=${hostId}` : '';
		return this.request(`/api/proxmox/nodes${params}`);
	}

	// Catalog API
	async getCatalogApps() {
		return this.request('/api/catalog/');
	}

	async getCatalogApp(appId: string) {
		return this.request(`/api/catalog/${appId}`);
	}

	async getCatalogCategories() {
		return this.request('/api/catalog/categories');
	}

	async searchCatalog(query: string) {
		return this.request(`/api/catalog/search?q=${encodeURIComponent(query)}`);
	}

	async getCatalogByCategory(category: string) {
		return this.request(`/api/catalog/category/${encodeURIComponent(category)}`);
	}

	async getCatalogStats() {
		return this.request('/api/catalog/stats');
	}

	async reloadCatalog() {
		return this.request('/api/catalog/reload', {
			method: 'POST'
		});
	}

	// Application Management
	async listApps() {
		return this.request('/api/apps/');
	}

	async getApp(appId: string) {
		return this.request(`/api/apps/${appId}`);
	}

	async deployApp(data: {
		catalog_id: string;
		hostname: string;
		config?: any;
		environment?: any;
		node?: string;
	}) {
		return this.request('/api/apps/', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	async cloneApp(appId: string, newHostname: string) {
		return this.request(`/api/apps/${appId}/clone`, {
			method: 'POST',
			body: JSON.stringify({ new_hostname: newHostname })
		});
	}

	async performAppAction(appId: string, action: 'start' | 'stop' | 'restart' | 'delete') {
		return this.request(`/api/apps/${appId}/action`, {
			method: 'POST',
			body: JSON.stringify({ action })
		});
	}

	async getAppLogs(appId: string, tail?: number) {
		const params = tail ? `?tail=${tail}` : '';
		return this.request(`/api/apps/${appId}/logs${params}`);
	}

	async getAppStats(appId: string) {
		return this.request(`/api/apps/${appId}/stats`);
	}

	// Container Discovery & Adoption
	async discoverUnmanagedContainers(hostId?: number) {
		const params = hostId ? `?host_id=${hostId}` : '';
		return this.request(`/api/apps/discover${params}`);
	}

	async adoptContainer(data: {
		vmid: number;
		node_name: string;
		suggested_type?: string;
		port_to_expose?: number;
	}) {
		return this.request('/api/apps/adopt', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	// Backups (placeholder)
	async listBackups() {
		return this.request('/api/backups/');
	}

	// Application Backups
	async listAppBackups(appId: string) {
		return this.request(`/api/apps/${appId}/backups`);
	}

	async createAppBackup(appId: string, options?: { backup_type?: string; compression?: string }) {
		return this.request(`/api/apps/${appId}/backups`, {
			method: 'POST',
			body: JSON.stringify(options || {})
		});
	}

	async getBackupDetails(appId: string, backupId: number) {
		return this.request(`/api/apps/${appId}/backups/${backupId}`);
	}

	async restoreBackup(appId: string, backupId: number) {
		return this.request(`/api/apps/${appId}/backups/${backupId}/restore`, {
			method: 'POST'
		});
	}

	async deleteBackup(appId: string, backupId: number) {
		return this.request(`/api/apps/${appId}/backups/${backupId}`, {
			method: 'DELETE'
		});
	}

	async getBackupStats(appId: string) {
		return this.request(`/api/apps/${appId}/backups/stats`);
	}

	// Settings API
	// These methods provide a convenience layer for managing system settings
	
	// Proxmox Settings (uses the default/primary host)
	async getProxmoxSettings() {
		const response = await this.listHosts();
		if (response.success && response.data) {
			// Return the default host or the first host
			const hosts = Array.isArray(response.data) ? response.data : [];
			const defaultHost = hosts.find((h: any) => h.is_default) || hosts[0];
			return {
				success: true,
				data: defaultHost || null
			};
		}
		return response;
	}

	async saveProxmoxSettings(data: {
		name: string;
		host: string;
		port: number;
		user: string;
		password?: string;
		verify_ssl: boolean;
	}) {
		// Get existing settings to determine if we're updating or creating
		const existing = await this.getProxmoxSettings();
		
		if (existing.success && existing.data && existing.data.id) {
			// Update existing host
			return this.updateHost(existing.data.id, data);
		} else {
			// Create new host
			return this.createHost({
				...data,
				is_default: true
			});
		}
	}

	async testProxmoxConnection(hostId?: number) {
		// If no hostId provided, get the default host
		if (!hostId) {
			const settings = await this.getProxmoxSettings();
			if (settings.success && settings.data) {
				hostId = settings.data.id;
			}
		}
		
		if (!hostId) {
			return {
				success: false,
				error: 'No Proxmox host configured'
			};
		}
		
		return this.testHostConnection(hostId);
	}

	// System Settings
	async getSystemSettings() {
		return this.getSystemInfo();
	}

	// Resource Settings
	async getResourceSettings() {
		return this.request('/api/core/settings/resources', {
			method: 'GET'
		});
	}

	async saveResourceSettings(data: {
		default_cpu_cores: number;
		default_memory_mb: number;
		default_disk_gb: number;
		default_swap_mb: number;
	}) {
		return this.request('/api/core/settings/resources', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	// Network Settings
	async getNetworkSettings() {
		return this.request('/api/core/settings/network', {
			method: 'GET'
		});
	}

	async saveNetworkSettings(data: {
		default_subnet: string;
		default_gateway: string;
		default_dns_primary: string;
		default_dns_secondary?: string | null;
		default_bridge: string;
	}) {
		return this.request('/api/core/settings/network', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}
}

export const api = new ApiClient();
export default api;
