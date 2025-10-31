/**
 * API client library for Proximity 2.0 frontend (Refactored for HttpOnly Cookies)
 *
 * CRITICAL: This client is now stateless regarding authentication.
 * It does NOT store tokens. It relies on the browser sending HttpOnly cookies.
 */

import * as Sentry from '@sentry/sveltekit';
import type { User } from '$lib/stores/auth';
import { logger } from '$lib/logger';

// 🔐 Security: API URL must be configured via environment variable
// No fallback to prevent accidental use of localhost or wrong server
const API_BASE_URL = import.meta.env.VITE_API_URL;
if (!API_BASE_URL && import.meta.env.PROD) {
	throw new Error('VITE_API_URL environment variable is required in production');
}

interface ApiResponse<T> {
	success: boolean;
	data?: T;
	error?: string;
	detail?: string; // dj-rest-auth often uses 'detail' for errors
}

class ApiClient {
	private baseUrl: string;

	constructor(baseUrl: string = API_BASE_URL) {
		this.baseUrl = baseUrl;
		logger.debug('ApiClient initialized with base URL', { baseUrl });
	}

	private getCsrfToken(): string | null {
		// Try to get CSRF token from cookie
		const name = 'csrftoken';
		const value = `; ${document.cookie}`;
		const parts = value.split(`; ${name}=`);
		if (parts.length === 2) {
			return parts.pop()?.split(';').shift() || null;
		}

		// Try to get from meta tag
		const meta = document.querySelector('meta[name="csrf-token"]');
		return meta ? meta.getAttribute('content') : null;
	}

	private buildQueryString(params: Record<string, any>): string {
		const searchParams = new URLSearchParams();

		for (const [key, value] of Object.entries(params)) {
			if (value !== null && value !== undefined && value !== '') {
				// Validate numbers for ID and count parameters
				if (key.includes('id') || key === 'tail' || key === 'vmid') {
					const numValue = Number(value);
					if (!isNaN(numValue) && numValue >= 0) {
						searchParams.append(key, String(Math.floor(numValue)));
					}
				} else {
					// For strings, use URL encoding
					searchParams.append(key, String(value));
				}
			}
		}

		const query = searchParams.toString();
		return query ? `?${query}` : '';
	}

	private async request<T>(
		endpoint: string,
		options: RequestInit = {},
		timeoutMs: number = 30000
	): Promise<ApiResponse<T>> {
		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
			...(options.headers as Record<string, string>)
		};

		// 🔐 Add CSRF token for state-changing requests (POST, PUT, DELETE, PATCH)
		const method = options.method?.toUpperCase() || 'GET';
		if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
			const csrfToken = this.getCsrfToken();
			if (!csrfToken) {
				// CSRF token is required for security - fail fast instead of silently proceeding
				const error = new Error(
					'CSRF token is required for state-changing requests. This should not happen in normal operation.'
				);
				logger.error('Missing CSRF token for state-changing request', error);
				throw error;
			}
			headers['X-CSRFToken'] = csrfToken;
			logger.debug(`CSRF token added for ${method} ${endpoint}`);
		}

		// ⏱️ Create abort controller for timeout handling
		const controller = new AbortController();
		const timeout = setTimeout(() => controller.abort(), timeoutMs);

		// CRITICAL: Ensure cookies are sent with every request.
		const fetchOptions: RequestInit = {
			...options,
			headers,
			credentials: 'include',
			signal: controller.signal
		};

		try {
			const response = await fetch(`${this.baseUrl}${endpoint}`, fetchOptions);

			// Handle responses that don't return a body (e.g., 204 No Content on logout)
			if (response.status === 204) {
				return { success: true };
			}

			const data = await response.json();

			if (!response.ok) {
				logger.error(`API Error ${response.status}: ${endpoint}`, { status: response.status, endpoint, error: data });
				return {
					success: false,
					error: data.detail || data.error || 'An unknown error occurred'
				};
			}

			return { success: true, data };
		} catch (error) {
			logger.error(`API Exception for ${endpoint}:`, error);
			return {
				success: false,
				error: error instanceof Error ? error.message : 'A network error occurred'
			};
		}
	}

	// ===================================================================
	// NEW AUTHENTICATION METHODS
	// ===================================================================

	async login(username: string, password: string) {
		// dj-rest-auth returns user details and sets an HttpOnly cookie.
		return this.request<{ user: User }>('/api/auth/login/', {
			method: 'POST',
			body: JSON.stringify({ username, password })
		});
	}

	async logout() {
		// This endpoint clears the HttpOnly cookie on the backend.
		return this.request('/api/auth/logout/', {
			method: 'POST'
		});
	}

	async register(username: string, email: string, password: string, password2: string) {
		return this.request('/api/auth/registration/', {
			method: 'POST',
			body: JSON.stringify({ username, email, password, password2 })
		});
	}

	async getUser() {
		// This endpoint returns the user if the session cookie is valid.
		return this.request<User>('/api/auth/user/');
	}

	// ===================================================================
	// ALL OTHER API METHODS (UNCHANGED)
	// ===================================================================

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
		const params = hostId ? this.buildQueryString({ host_id: hostId }) : '';
		return this.request(`/api/proxmox/nodes${params}`);
	}

	// Alias for convenience (list all nodes with statistics)
	async listNodes() {
		return this.getProxmoxNodes();
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
		const params = tail ? this.buildQueryString({ tail }) : '';
		return this.request(`/api/apps/${appId}/logs${params}`);
	}

	async getAppStats(appId: string) {
		return this.request(`/api/apps/${appId}/stats`);
	}

	// Container Discovery & Adoption
	async discoverUnmanagedContainers(hostId?: number) {
		const params = hostId ? this.buildQueryString({ host_id: hostId }) : '';
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

	// Proxmox Settings (convenience methods)
	async getProxmoxSettings() {
		// Get the primary Proxmox host configuration
		const response = await this.listHosts();
		if (response.success && Array.isArray(response.data) && response.data.length > 0) {
			return { success: true, data: response.data[0] };
		}
		return { success: false, error: 'No Proxmox host configured' };
	}

	async saveProxmoxSettings(data: any) {
		// Update the primary Proxmox host configuration
		const response = await this.listHosts();
		if (response.success && Array.isArray(response.data) && response.data.length > 0) {
			const hostId = response.data[0].id;
			return this.updateHost(hostId, data);
		}
		// If no host exists, create one
		return this.createHost(data);
	}

	async testProxmoxConnection(hostId?: number) {
		if (hostId) {
			return this.testHostConnection(hostId);
		}
		// Test the primary host
		const response = await this.listHosts();
		if (response.success && Array.isArray(response.data) && response.data.length > 0) {
			return this.testHostConnection(response.data[0].id);
		}
		return { success: false, error: 'No Proxmox host configured' };
	}
}

export const api = new ApiClient();
export default api;