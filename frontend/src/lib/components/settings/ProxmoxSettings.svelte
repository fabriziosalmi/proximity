<script lang="ts">
	/**
	 * Proxmox Settings Component
	 * Manage Proxmox host configuration
	 */
	import { onMount } from 'svelte';
	import { Loader2, Server, TestTube, Save, Check, X, Trash2, AlertCircle } from 'lucide-svelte';
	import { api } from '$lib/api';
	import { toasts } from '$lib/stores/toast';
	import { saveProxmoxSettings as saveProxmoxSettingsAction, testProxmoxConnection as testProxmoxConnectionAction } from '$lib/stores/actions';

	let loading = true;
	let saving = false;
	let testing = false;
	let deleting = false;
	let showDeleteConfirm = false;

	// Form data
	let hostId: number | null = null;
	let name = '';
	let host = '';
	let port = 8006;
	let user = '';
	let password = '';
	let verifySSL = false;

	// Validation
	let errors: Record<string, string> = {};

	async function loadSettings() {
		loading = true;
		errors = {};

		try {
			const response = await api.getProxmoxSettings();

			if (response.success && response.data) {
				const settings = response.data;
				hostId = settings.id || null;
				name = settings.name || '';
				host = settings.host || '';
				port = settings.port || 8006;
				user = settings.user || '';
				password = ''; // Never populate password
				verifySSL = settings.verify_ssl !== undefined ? settings.verify_ssl : false;
			}
		} catch (err) {
			logger.error('Failed to load Proxmox settings:', err);
			toasts.error('Failed to load Proxmox settings', 5000);
		} finally {
			loading = false;
		}
	}

	function validateForm(): boolean {
		errors = {};

		if (!name.trim()) {
			errors.name = 'Name is required';
		}

		if (!host.trim()) {
			errors.host = 'Host/IP address is required';
		}

		if (!port || port < 1 || port > 65535) {
			errors.port = 'Port must be between 1 and 65535';
		}

		if (!user.trim()) {
			errors.user = 'Username is required';
		}

		// Password is only required for new configurations
		if (!hostId && !password.trim()) {
			errors.password = 'Password is required for new configuration';
		}

		return Object.keys(errors).length === 0;
	}

	async function handleSave() {
		if (!validateForm()) {
			toasts.error('Please fix validation errors', 5000);
			return;
		}

		saving = true;

		const data: any = {
			name,
			host,
			port,
			user,
			verify_ssl: verifySSL
		};

		// Only include password if it's been changed/set
		if (password.trim()) {
			data.password = password;
		}

		try {
			// Use centralized action dispatcher (handles API, toasts, and sounds)
			const result = await saveProxmoxSettingsAction(data);

			if (result.success) {
				// 🔐 Clear password immediately after successful save for security
				password = '';
				// Reload to get the updated hostId
				await loadSettings();
			} else {
				// Clear password on failure too (fail-safe security measure)
				password = '';
			}
		} catch (error) {
			// Clear password even on exception for security
			password = '';
			throw error;
		} finally {
			saving = false;
		}
	}

	async function handleTest() {
		testing = true;

		// Use centralized action dispatcher (handles API, toasts, and sounds)
		await testProxmoxConnectionAction(hostId || undefined);

		testing = false;
	}

	async function handleDelete() {
		if (!hostId) {
			toasts.error('No host configured to delete', 3000);
			return;
		}

		// Request confirmation
		const confirmDelete = confirm(
			`Are you sure you want to delete the Proxmox host configuration "${name}"? This action cannot be undone.`
		);

		if (!confirmDelete) {
			return;
		}

		deleting = true;

		try {
			const response = await api.deleteHost(hostId);

			if (response.success) {
				toasts.success('Proxmox host deleted successfully', 3000);
				// Reset the form
				await loadSettings();
			} else {
				toasts.error(response.error || 'Failed to delete host', 5000);
			}
		} catch (error: any) {
			logger.error('Error deleting host:', error);
			toasts.error(error.message || 'Failed to delete host', 5000);
		} finally {
			deleting = false;
			showDeleteConfirm = false;
		}
	}

	onMount(() => {
		loadSettings();
	});
</script>

<div class="settings-section">
	{#if loading}
		<!-- Loading Skeleton -->
		<div class="flex items-center justify-center py-12">
			<Loader2 class="h-8 w-8 animate-spin text-rack-primary" />
			<span class="ml-3 text-gray-400">Loading Proxmox settings...</span>
		</div>
	{:else}
		<!-- Settings Form - No wrapper, integrates into parent rack -->
		<div class="settings-form">
			<div class="form-header">
				<Server class="h-6 w-6 text-rack-primary" />
				<h2 class="form-title">Proxmox Host Configuration</h2>
			</div>

			<p class="form-description">
				Configure your Proxmox VE host connection details. These settings are required for
				Proximity to manage containers and applications.
			</p>

			<div class="form-grid">
				<!-- Name -->
				<div class="form-group">
					<label for="name" class="form-label">
						Configuration Name
						<span class="text-red-400">*</span>
					</label>
					<input
						id="name"
						type="text"
						bind:value={name}
						placeholder="My Proxmox Server"
						class="form-input"
						class:error={errors.name}
						disabled={saving || testing}
					/>
					{#if errors.name}
						<span class="form-error">{errors.name}</span>
					{/if}
				</div>

				<!-- Host -->
				<div class="form-group">
					<label for="host" class="form-label">
						Host / IP Address
						<span class="text-red-400">*</span>
					</label>
					<input
						id="host"
						type="text"
						bind:value={host}
						placeholder="192.168.1.100 or proxmox.local"
						class="form-input"
						class:error={errors.host}
						disabled={saving || testing}
					/>
					{#if errors.host}
						<span class="form-error">{errors.host}</span>
					{/if}
				</div>

				<!-- Port -->
				<div class="form-group">
					<label for="port" class="form-label">
						Port
						<span class="text-red-400">*</span>
					</label>
					<input
						id="port"
						type="number"
						bind:value={port}
						placeholder="8006"
						min="1"
						max="65535"
						class="form-input"
						class:error={errors.port}
						disabled={saving || testing}
					/>
					{#if errors.port}
						<span class="form-error">{errors.port}</span>
					{/if}
				</div>

				<!-- Username -->
				<div class="form-group">
					<label for="user" class="form-label">
						Username
						<span class="text-red-400">*</span>
					</label>
					<input
						id="user"
						type="text"
						bind:value={user}
						placeholder="root@pam"
						class="form-input"
						class:error={errors.user}
						disabled={saving || testing}
					/>
					{#if errors.user}
						<span class="form-error">{errors.user}</span>
					{/if}
					<p class="form-hint">Example: root@pam or admin@pve</p>
				</div>

				<!-- Password -->
				<div class="form-group">
					<label for="password" class="form-label">
						Password
						{#if hostId}
							<span class="text-gray-500 text-xs">(leave blank to keep unchanged)</span>
						{:else}
							<span class="text-red-400">*</span>
						{/if}
					</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						placeholder={hostId ? '••••••••' : 'Enter password'}
						class="form-input"
						class:error={errors.password}
						disabled={saving || testing}
					/>
					{#if errors.password}
						<span class="form-error">{errors.password}</span>
					{/if}
				</div>

				<!-- Verify SSL -->
				<div class="form-group col-span-2">
					<label class="form-checkbox-label">
						<input
							type="checkbox"
							bind:checked={verifySSL}
							disabled={saving || testing}
							class="form-checkbox"
						/>
						<span class="ml-2">Verify SSL Certificate</span>
					</label>
					<p class="form-hint mt-1">
						Disable if using self-signed certificates (not recommended for production)
					</p>
				</div>
			</div>

			<!-- Action Buttons -->
			<div class="form-actions">
				<button
					on:click={handleTest}
					disabled={saving || testing || !host || !user}
					class="btn-secondary"
					data-testid="test-connection-button"
				>
					{#if testing}
						<Loader2 class="h-4 w-4 animate-spin" />
					{:else}
						<TestTube class="h-4 w-4" />
					{/if}
					Test Connection
				</button>

				<button
					on:click={handleSave}
					disabled={saving || testing}
					class="btn-primary"
					data-testid="save-settings-button"
				>
					{#if saving}
						<Loader2 class="h-4 w-4 animate-spin" />
					{:else}
						<Save class="h-4 w-4" />
					{/if}
					Save Settings
				</button>

				<button
					on:click={handleDelete}
					disabled={deleting || saving || testing || !hostId}
					class="btn-danger"
					data-testid="delete-host-button"
					title={!hostId ? 'No host configured to delete' : 'Delete this host configuration'}
				>
					{#if deleting}
						<Loader2 class="h-4 w-4 animate-spin" />
					{:else}
						<Trash2 class="h-4 w-4" />
					{/if}
					Delete Host
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.settings-section {
		width: 100%;
	}

	.settings-form {
		/* No background/border - inherits from parent rack unit */
		background: transparent;
		border: none;
		padding: 0;
	}

	.form-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1rem;
		padding-bottom: 0.75rem;
		border-bottom: 1px solid rgba(var(--color-rack-primary-rgb, 59, 130, 246), 0.2);
	}

	.form-title {
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--color-text-primary, #e5e7eb);
		margin: 0;
	}

	.form-description {
		color: var(--color-text-secondary, #9ca3af);
		font-size: 0.875rem;
		line-height: 1.5;
		margin-bottom: 2rem;
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.form-group.col-span-2 {
		grid-column: span 2;
	}

	.form-label {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--color-text-primary, #e5e7eb);
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}

	.form-input {
		width: 100%;
		padding: 0.625rem 0.875rem;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid var(--border-color-secondary, #374151);
		border-radius: 0.375rem;
		color: var(--color-text-primary, #e5e7eb);
		font-size: 0.875rem;
		transition: all 0.2s ease;
	}

	.form-input:focus {
		outline: none;
		border-color: var(--color-rack-primary, #3b82f6);
		box-shadow: 0 0 0 3px rgba(var(--color-rack-primary-rgb, 59, 130, 246), 0.1);
	}

	.form-input:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.form-input.error {
		border-color: #ef4444;
	}

	.form-input.error:focus {
		box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
	}

	.form-error {
		font-size: 0.75rem;
		color: #ef4444;
		margin-top: -0.25rem;
	}

	.form-hint {
		font-size: 0.75rem;
		color: var(--color-text-secondary, #9ca3af);
	}

	.form-checkbox-label {
		display: flex;
		align-items: center;
		font-size: 0.875rem;
		color: var(--color-text-primary, #e5e7eb);
		cursor: pointer;
	}

	.form-checkbox {
		width: 1rem;
		height: 1rem;
		border-radius: 0.25rem;
		cursor: pointer;
	}

	.form-checkbox:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.form-actions {
		display: flex;
		gap: 1rem;
		justify-content: flex-end;
		padding-top: 1.5rem;
		border-top: 1px solid rgba(var(--color-rack-primary-rgb, 59, 130, 246), 0.2);
	}

	.btn-primary,
	.btn-secondary {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 1.25rem;
		font-size: 0.875rem;
		font-weight: 600;
		border-radius: 0.375rem;
		cursor: pointer;
		transition: all 0.2s ease;
		border: none;
	}

	.btn-primary {
		background: var(--color-rack-primary, #3b82f6);
		color: white;
		box-shadow: 0 2px 4px rgba(var(--color-rack-primary-rgb, 59, 130, 246), 0.3);
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-accent, #0284c7);
		box-shadow: 0 0 20px rgba(var(--color-rack-primary-rgb, 59, 130, 246), 0.4);
		transform: translateY(-1px);
	}

	.btn-primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-secondary {
		background: var(--bg-rack-light, #1f2937);
		color: var(--color-text-primary, #e5e7eb);
		border: 1px solid var(--border-color-primary, #4b5563);
	}

	.btn-secondary:hover:not(:disabled) {
		border-color: var(--color-rack-primary, #3b82f6);
		background: rgba(var(--color-rack-primary-rgb, 59, 130, 246), 0.1);
		transform: translateY(-1px);
	}

	.btn-secondary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-danger {
		background: #dc2626;
		color: white;
		box-shadow: 0 2px 4px rgba(220, 38, 38, 0.3);
	}

	.btn-danger:hover:not(:disabled) {
		background: #991b1b;
		box-shadow: 0 0 20px rgba(220, 38, 38, 0.4);
		transform: translateY(-1px);
	}

	.btn-danger:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	@media (max-width: 768px) {
		.form-grid {
			grid-template-columns: 1fr;
		}

		.form-group.col-span-2 {
			grid-column: span 1;
		}

		.form-actions {
			flex-direction: column;
		}
	}
</style>
