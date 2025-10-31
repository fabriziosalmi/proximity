/**
 * TypeScript type definitions for API responses
 * Ensures type safety and prevents runtime errors from unexpected response structures
 */

import type { DeployedApp } from '$lib/stores/apps';
import type { User } from '$lib/stores/auth';

// ===== Generic API Response =====
export interface ApiResponse<T = any> {
	success: boolean;
	data?: T;
	error?: string;
	detail?: string;
}

// ===== Authentication Responses =====
export interface LoginResponse {
	user: User;
}

export interface UserResponse extends User {}

// ===== Host Responses =====
export interface ProxmoxHost {
	id: number;
	name: string;
	host: string;
	port: number;
	user: string;
	realm?: string;
	verify_ssl: boolean;
	is_active: boolean;
	created_at?: string;
	updated_at?: string;
}

export interface HostsResponse {
	success: boolean;
	data?: ProxmoxHost[];
	error?: string;
}

// ===== Node Responses =====
export interface ProxmoxNode {
	node: string;
	status: 'online' | 'offline';
	uptime?: number;
	cpu?: number;
	maxcpu?: number;
	memory?: number;
	maxmemory?: number;
	disk?: number;
	maxdisk?: number;
}

export interface NodesResponse {
	success: boolean;
	data?: ProxmoxNode[];
	error?: string;
}

// ===== Application Responses =====
export interface AppsListResponse {
	success: boolean;
	data?: DeployedApp[];
	error?: string;
}

export interface AppResponse {
	success: boolean;
	data?: DeployedApp;
	error?: string;
}

export interface DeployAppResponse {
	success: boolean;
	data?: {
		id: string;
		status: string;
		task_id?: string;
	};
	error?: string;
}

// ===== Type Guards =====

export function isDeployedApp(data: any): data is DeployedApp {
	return (
		data &&
		typeof data === 'object' &&
		'id' in data &&
		'hostname' in data &&
		'status' in data &&
		'host_id' in data &&
		'node_name' in data
	);
}

export function isDeployedAppArray(data: any): data is DeployedApp[] {
	return Array.isArray(data) && data.every(isDeployedApp);
}

export function isProxmoxHost(data: any): data is ProxmoxHost {
	return (
		data &&
		typeof data === 'object' &&
		'id' in data &&
		'host' in data &&
		'port' in data &&
		'is_active' in data
	);
}

export function isProxmoxHostArray(data: any): data is ProxmoxHost[] {
	return Array.isArray(data) && data.every(isProxmoxHost);
}

export function isProxmoxNode(data: any): data is ProxmoxNode {
	return (
		data &&
		typeof data === 'object' &&
		'node' in data &&
		'status' in data
	);
}

export function isProxmoxNodeArray(data: any): data is ProxmoxNode[] {
	return Array.isArray(data) && data.every(isProxmoxNode);
}

// ===== Response Validation Helpers =====

export function validateAppsResponse(response: any): DeployedApp[] {
	if (!response?.success || !response?.data) {
		return [];
	}

	// Handle both array and object with apps property
	let appsData = response.data;
	if (!Array.isArray(appsData) && appsData?.apps) {
		appsData = appsData.apps;
	}

	if (!isDeployedAppArray(appsData)) {
		console.error('Invalid apps response structure:', appsData);
		return [];
	}

	return appsData;
}

export function validateHostResponse(response: any): ProxmoxHost | null {
	if (!response?.success || !response?.data) {
		return null;
	}

	if (!isProxmoxHost(response.data)) {
		console.error('Invalid host response structure:', response.data);
		return null;
	}

	return response.data;
}

export function validateHostsResponse(response: any): ProxmoxHost[] {
	if (!response?.success || !response?.data) {
		return [];
	}

	if (!isProxmoxHostArray(response.data)) {
		console.error('Invalid hosts response structure:', response.data);
		return [];
	}

	return response.data;
}

export function validateNodesResponse(response: any): ProxmoxNode[] {
	if (!response?.success || !response?.data) {
		return [];
	}

	if (!isProxmoxNodeArray(response.data)) {
		console.error('Invalid nodes response structure:', response.data);
		return [];
	}

	return response.data;
}
