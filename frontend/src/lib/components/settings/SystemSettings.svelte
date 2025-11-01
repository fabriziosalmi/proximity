<script lang="ts">
	/**
	 * System Settings Component
	 * Manage general system configuration and preferences
	 */
	import { onMount } from 'svelte';
	import { Loader2, Settings, Save, Palette } from 'lucide-svelte';
	import { api } from '$lib/api';
	import { toasts } from '$lib/stores/toast';
	import { ThemeService } from '$lib/services/ThemeService';
	import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';
	import { logger } from '$lib/logger';

	let loading = true;
	let saving = false;

	// Form data
	let version = '';
	let defaultTheme = 'dark';
	let enableAiAgent = false;
	let enableCommunityChat = false;
	let enableMultiHost = false;

	async function loadSettings() {
		loading = true;

		try {
			const response = await api.getSystemSettings();

			if (response.success && response.data) {
				const settings = response.data;
				version = settings.version || '2.0.0';
				defaultTheme = settings.default_theme || 'dark';
				enableAiAgent = settings.enable_ai_agent || false;
				enableCommunityChat = settings.enable_community_chat || false;
				enableMultiHost = settings.enable_multi_host || false;
			}
		} catch (err) {
			logger.error('Failed to load system settings:', err);
			toasts.error('Failed to load system settings', 5000);
		} finally {
			loading = false;
		}
	}

	async function handleSave() {
		saving = true;

		try {
			// Note: The backend doesn't have a save endpoint for system settings yet
			// This is a placeholder for future implementation
			toasts.info('System settings are read-only in this version', 5000);
		} catch (err) {
			logger.error('Save error:', err);
			toasts.error('An error occurred while saving', 7000);
		} finally {
			saving = false;
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
			<Loader2 class="h-8 w-8 animate-spin text-blue-400" />
			<span class="ml-3 text-gray-400">Loading system settings...</span>
		</div>
	{:else}
		<!-- Settings Form -->
		<div class="settings-form">
			<div class="form-header">
				<Settings class="h-6 w-6 text-blue-400" />
				<h2 class="form-title">System Configuration</h2>
			</div>

			<p class="form-description">
				View and manage system-wide settings and feature flags.
			</p>

			<!-- Theme Switcher Component -->
			<ThemeSwitcher />

			<div class="form-grid">
				<!-- Version (Read-only) -->
				<div class="form-group col-span-2">
					<label for="version" class="form-label">Version</label>
					<input
						id="version"
						type="text"
						bind:value={version}
						class="form-input"
						disabled
						readonly
					/>
					<p class="form-hint">Current Proximity version</p>
				</div>

				<!-- Default Theme -->
				<div class="form-group">
					<label for="theme" class="form-label">Default Theme</label>
					<select
						id="theme"
						bind:value={defaultTheme}
						class="form-input"
						disabled={saving}
					>
						<option value="dark">Dark</option>
						<option value="light">Light</option>
						<option value="auto">Auto</option>
					</select>
					<p class="form-hint">Default theme for new users</p>
				</div>

				<!-- Feature Flags -->
				<div class="form-group col-span-2">
					<h3 class="feature-section-title">Feature Flags</h3>

					<label class="form-checkbox-label">
						<input
							type="checkbox"
							bind:checked={enableMultiHost}
							disabled={saving}
							class="form-checkbox"
						/>
						<span class="ml-2">Enable Multi-Host Support</span>
					</label>
					<p class="form-hint ml-6">
						Allow managing multiple Proxmox hosts
					</p>

					<label class="form-checkbox-label mt-3">
						<input
							type="checkbox"
							bind:checked={enableAiAgent}
							disabled={saving}
							class="form-checkbox"
						/>
						<span class="ml-2">Enable AI Agent</span>
					</label>
					<p class="form-hint ml-6">
						Experimental AI-powered assistance features
					</p>

					<label class="form-checkbox-label mt-3">
						<input
							type="checkbox"
							bind:checked={enableCommunityChat}
							disabled={saving}
							class="form-checkbox"
						/>
						<span class="ml-2">Enable Community Chat</span>
					</label>
					<p class="form-hint ml-6">
						Real-time community support and discussions
					</p>
				</div>
			</div>

			<!-- Info Box -->
			<div class="info-box">
				<p class="text-sm text-gray-400">
					<strong>Note:</strong> Some system settings require server restart to take effect.
					Contact your system administrator for configuration changes.
				</p>
			</div>

			<!-- Action Buttons -->
			<div class="form-actions">
				<button
					on:click={handleSave}
					disabled={saving}
					class="btn-primary"
					data-testid="save-system-settings-button"
				>
					{#if saving}
						<Loader2 class="h-4 w-4 animate-spin" />
					{:else}
						<Save class="h-4 w-4" />
					{/if}
					Save Settings
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
		margin-bottom: 1.5rem;
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
	}

	.feature-section-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--color-text-primary, #e5e7eb);
		margin-bottom: 1rem;
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
		border-color: var(--color-accent, #3b82f6);
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}

	.form-input:disabled,
	.form-input:read-only {
		opacity: 0.5;
		cursor: not-allowed;
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

	.info-box {
		background: rgba(59, 130, 246, 0.1);
		border: 1px solid rgba(59, 130, 246, 0.2);
		border-radius: 0.5rem;
		padding: 1rem;
		margin-bottom: 1.5rem;
	}

	.form-actions {
		display: flex;
		gap: 1rem;
		justify-content: flex-end;
		padding-top: 1.5rem;
		border-top: 1px solid var(--border-color-secondary, #374151);
	}

	.btn-primary {
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
		background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
		color: white;
		box-shadow: 0 2px 4px rgba(14, 165, 233, 0.3);
	}

	.btn-primary:hover:not(:disabled) {
		background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
		box-shadow: 0 0 20px rgba(14, 165, 233, 0.4);
	}

	.btn-primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.section-card {
		background: rgba(0, 0, 0, 0.2);
		border: 1px solid var(--border-color-secondary, #374151);
		border-radius: 0.5rem;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.section-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.section-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--color-text-primary, #e5e7eb);
		margin: 0;
	}

	.theme-preview-notice {
		margin-top: 1rem;
		padding: 0.75rem;
		background: rgba(147, 51, 234, 0.1);
		border: 1px solid rgba(147, 51, 234, 0.2);
		border-radius: 0.375rem;
	}

	@media (max-width: 768px) {
		.form-grid {
			grid-template-columns: 1fr;
		}

		.form-group.col-span-2 {
			grid-column: span 1;
		}
	}
</style>
