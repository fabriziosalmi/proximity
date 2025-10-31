/**
 * Centralized Action Dispatcher
 *
 * This store centralizes all user-initiated actions, combining:
 * - API calls
 * - Toast notifications
 * - Sound effects
 *
 * This follows the DRY principle and makes the codebase more maintainable
 * by removing scattered SoundService and toast calls from UI components.
 */

import { myAppsStore } from './apps';
import { toasts } from './toast';
import { SoundService } from '$lib/services/SoundService';
import { api } from '$lib/api';

/**
 * Application Actions
 */

export async function startApp(appId: string, appName: string) {
	SoundService.play('click');

	try {
		toasts.info(`Starting ${appName}...`, 2000);
		const result = await myAppsStore.performAction(appId, 'start');

		if (result.success) {
			toasts.success(`${appName} start command sent`, 5000);
			// Success sound will be played by the store when status changes to 'running'
		} else {
			toasts.error(result.error || `Failed to start ${appName}`, 7000);
			SoundService.play('error');
		}

		return result;
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error(`An error occurred: ${message}`, 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

export async function stopApp(appId: string, appName: string) {
	SoundService.play('click');

	try {
		toasts.info(`Stopping ${appName}...`, 2000);
		const result = await myAppsStore.performAction(appId, 'stop');

		if (result.success) {
			toasts.success(`${appName} stop command sent`, 5000);
			SoundService.play('success');
		} else {
			toasts.error(result.error || `Failed to stop ${appName}`, 7000);
			SoundService.play('error');
		}

		return result;
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error(`An error occurred: ${message}`, 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

export async function restartApp(appId: string, appName: string) {
	SoundService.play('click');

	try {
		toasts.info(`Restarting ${appName}...`, 2000);
		const result = await myAppsStore.performAction(appId, 'restart');

		if (result.success) {
			toasts.success(`${appName} restart command sent`, 5000);
			SoundService.play('success');
		} else {
			toasts.error(result.error || `Failed to restart ${appName}`, 7000);
			SoundService.play('error');
		}

		return result;
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error(`An error occurred: ${message}`, 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

export async function deleteApp(appId: string, appName: string) {
	SoundService.play('click');

	try {
		toasts.info(`Deleting ${appName}...`, 2000);
		const result = await myAppsStore.performAction(appId, 'delete');

		if (result.success) {
			toasts.success(`${appName} deleted successfully`, 5000);
			SoundService.play('success');
		} else {
			toasts.error(result.error || `Failed to delete ${appName}`, 7000);
			SoundService.play('error');
		}

		return result;
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error(`An error occurred: ${message}`, 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

export async function cloneApp(appId: string, appName: string, newHostname: string) {
	logger.debug('Action dispatcher: cloneApp called. Invoking myAppsStore...');
	SoundService.play('click');

	try {
		toasts.info(`Cloning ${appName} to ${newHostname}...`, 3000);
		const result = await myAppsStore.cloneApplication(appId, newHostname);

		if (result.success) {
			toasts.success(`Clone started! ${newHostname} will be ready soon.`, 5000);
			// Success sound will be played when clone reaches 'running' status
		} else {
			toasts.error(result.error || 'Failed to start clone operation', 7000);
			SoundService.play('error');
		}

		return result;
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error(`An error occurred: ${message}`, 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

/**
 * Deploy a new application with optimistic UI update
 * 
 * This provides instant visual feedback by adding a placeholder card
 * to the UI immediately, before the API call completes.
 */
export async function deployApp(deploymentData: {
	catalog_id: string;
	hostname: string;
	node?: string;
	config?: Record<string, any>;
	ports?: Record<string, number>;
	environment?: Record<string, string>;
}) {
	logger.debug('🚀 [Actions] deployApp called with data:', deploymentData);
	SoundService.play('click');

	try {
		// Show toast immediately
		toasts.info(`Deploying ${deploymentData.hostname}...`, 3000);
		
		// 🎯 OPTIMISTIC UPDATE: Add placeholder to UI immediately
		logger.debug('🎯 [Actions] Triggering optimistic deployment update...');
		const result = await myAppsStore.deployApp(deploymentData);

		if (result.success) {
			toasts.success(`Deployment started! ${deploymentData.hostname} will be ready soon.`, 5000);
			// Success sound will be played when app reaches 'running' status
		} else {
			toasts.error(result.error || 'Failed to start deployment', 7000);
			SoundService.play('error');
		}

		return result;
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error(`An error occurred: ${message}`, 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

/**
 * Backup Actions
 */

export async function createBackup(appId: string) {
	SoundService.play('backup-create');

	try {
		const response = await api.createAppBackup(appId);

		if (response.success && response.data) {
			toasts.success('Backup creation started', 3000);
			return { success: true, data: response.data };
		} else {
			toasts.error(response.error || 'Failed to create backup', 7000);
			SoundService.play('error');
			return { success: false, error: response.error };
		}
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error('An error occurred while creating backup', 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

export async function restoreBackup(appId: string, backupId: number, backupFilename: string) {
	SoundService.play('restore');

	try {
		const response = await api.restoreBackup(appId, backupId);

		if (response.success) {
			toasts.success('Restore operation started', 5000);
			return { success: true };
		} else {
			toasts.error(response.error || 'Failed to start restore', 7000);
			SoundService.play('error');
			return { success: false, error: response.error };
		}
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error('An error occurred during restore', 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

export async function deleteBackup(appId: string, backupId: number) {
	SoundService.play('click');

	try {
		const response = await api.deleteBackup(appId, backupId);

		if (response.success) {
			toasts.success('Backup deleted successfully', 5000);
			SoundService.play('success');
			return { success: true };
		} else {
			toasts.error(response.error || 'Failed to delete backup', 7000);
			SoundService.play('error');
			return { success: false, error: response.error };
		}
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error('An error occurred while deleting', 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

/**
 * Settings Actions
 */

export async function saveProxmoxSettings(data: any) {
	try {
		const response = await api.saveProxmoxSettings(data);

		if (response.success) {
			toasts.success('Proxmox settings saved successfully', 5000);
			SoundService.play('success');
			return { success: true };
		} else {
			toasts.error(response.error || 'Failed to save settings', 7000);
			SoundService.play('error');
			return { success: false, error: response.error };
		}
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error('An error occurred while saving', 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

export async function testProxmoxConnection(hostId?: number) {
	try {
		const response = await api.testProxmoxConnection(hostId);

		if (response.success) {
			toasts.success('✅ Connection successful!', 5000);
			SoundService.play('success');
			return { success: true };
		} else {
			toasts.error(response.error || 'Connection failed', 7000);
			SoundService.play('error');
			return { success: false, error: response.error };
		}
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown error';
		toasts.error('An error occurred during connection test', 7000);
		SoundService.play('error');
		return { success: false, error: message };
	}
}

/**
 * UI Actions (non-API)
 */

export function switchTab(tabName: string) {
	SoundService.play('click');
	// Tab switching is handled by local component state
	// This just provides the sound feedback
}

export function flipCard() {
	SoundService.play('flip');
	// Flip animation is handled by local component state
	// This just provides the sound feedback
}
