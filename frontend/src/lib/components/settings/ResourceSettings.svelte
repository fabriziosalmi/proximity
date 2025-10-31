<script lang="ts">
	/**
	 * Resource Settings Component
	 * Manage default resource allocation for new deployments
	 */
	import { onMount } from 'svelte';
	import { Loader2, Cpu, MemoryStick, HardDrive, Save } from 'lucide-svelte';
	import { toasts } from '$lib/stores/toast';
	import { api } from '$lib/api';

	let loading = false;
	let saving = false;

	// Form data - Default resource allocations
	let defaultCores = 2;
	let defaultMemory = 2048; // MB
	let defaultDisk = 20; // GB
	let defaultSwap = 512; // MB
	let minCores = 1;
	let maxCores = 8;
	let minMemory = 512;
	let maxMemory = 16384;
	let minDisk = 8;
	let maxDisk = 500;

	// Validation
	let errors: Record<string, string> = {};

	async function loadSettings() {
		loading = true;
		errors = {};

		try {
			// Load from backend API
			const response = await api.getResourceSettings();

			if (response.success && response.data) {
				// Map backend field names to frontend variables
				defaultCores = response.data.default_cpu_cores || 2;
				defaultMemory = response.data.default_memory_mb || 2048;
				defaultDisk = response.data.default_disk_gb || 20;
				defaultSwap = response.data.default_swap_mb || 512;

				logger.debug('✅ Resource settings loaded from backend:', response.data);
			} else {
				throw new Error(response.error || 'Failed to load settings');
			}
		} catch (err) {
			logger.error('Failed to load resource settings:', err);
			toasts.error('Failed to load resource settings', 5000);
		} finally {
			loading = false;
		}
	}

	function validateForm(): boolean {
		errors = {};

		// CPU validation
		if (defaultCores < minCores || defaultCores > maxCores) {
			errors.defaultCores = `Must be between ${minCores} and ${maxCores}`;
		}

		// Memory validation
		if (defaultMemory < minMemory || defaultMemory > maxMemory) {
			errors.defaultMemory = `Must be between ${minMemory} MB and ${maxMemory} MB`;
		}

		// Disk validation
		if (defaultDisk < minDisk || defaultDisk > maxDisk) {
			errors.defaultDisk = `Must be between ${minDisk} GB and ${maxDisk} GB`;
		}

		return Object.keys(errors).length === 0;
	}

	async function handleSave() {
		if (!validateForm()) {
			toasts.error('Please fix validation errors', 5000);
			return;
		}

		saving = true;

		try {
			// Map frontend variables to backend field names
			const settings = {
				default_cpu_cores: defaultCores,
				default_memory_mb: defaultMemory,
				default_disk_gb: defaultDisk,
				default_swap_mb: defaultSwap
			};

			// Save to backend API
			const response = await api.saveResourceSettings(settings);

			if (response.success) {
				toasts.success('Resource settings saved successfully', 5000);
				logger.debug('✅ Resource settings saved to backend:', response.data);
			} else {
				throw new Error(response.error || 'Failed to save settings');
			}
		} catch (err) {
			logger.error('Save error:', err);
			const errorMessage = err instanceof Error ? err.message : 'An error occurred while saving';
			toasts.error(errorMessage, 7000);
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
			<span class="ml-3 text-gray-400">Loading resource settings...</span>
		</div>
	{:else}
		<!-- Settings Form -->
		<div class="settings-form">
			<div class="form-header">
				<Cpu class="h-6 w-6 text-blue-400" />
				<h2 class="form-title">Default Resource Allocation</h2>
			</div>

			<p class="form-description">
				Configure default resource allocations for new container deployments. These values will be
				pre-filled in the deployment form but can be customized per application.
			</p>

			<!-- CPU Section -->
			<div class="section-card">
				<div class="section-header">
					<Cpu class="h-5 w-5 text-green-400" />
					<h3 class="section-title">CPU Configuration</h3>
				</div>

				<div class="form-grid">
					<div class="form-group">
						<label for="defaultCores" class="form-label">
							Default CPU Cores
							<span class="text-red-400">*</span>
						</label>
						<input
							id="defaultCores"
							type="number"
							bind:value={defaultCores}
							min={minCores}
							max={maxCores}
							class="form-input"
							class:error={errors.defaultCores}
							disabled={saving}
						/>
						{#if errors.defaultCores}
							<span class="form-error">{errors.defaultCores}</span>
						{/if}
						<p class="form-hint">Number of CPU cores allocated by default</p>
					</div>

					<div class="form-group">
						<label for="minCores" class="form-label">Minimum Cores</label>
						<input
							id="minCores"
							type="number"
							bind:value={minCores}
							min="1"
							max={maxCores}
							class="form-input"
							disabled={saving}
						/>
						<p class="form-hint">Minimum allowed CPU cores</p>
					</div>

					<div class="form-group">
						<label for="maxCores" class="form-label">Maximum Cores</label>
						<input
							id="maxCores"
							type="number"
							bind:value={maxCores}
							min={minCores}
							max="64"
							class="form-input"
							disabled={saving}
						/>
						<p class="form-hint">Maximum allowed CPU cores</p>
					</div>
				</div>
			</div>

			<!-- Memory Section -->
			<div class="section-card">
				<div class="section-header">
					<MemoryStick class="h-5 w-5 text-purple-400" />
					<h3 class="section-title">Memory Configuration</h3>
				</div>

				<div class="form-grid">
					<div class="form-group">
						<label for="defaultMemory" class="form-label">
							Default Memory (MB)
							<span class="text-red-400">*</span>
						</label>
						<input
							id="defaultMemory"
							type="number"
							bind:value={defaultMemory}
							min={minMemory}
							max={maxMemory}
							step="256"
							class="form-input"
							class:error={errors.defaultMemory}
							disabled={saving}
						/>
						{#if errors.defaultMemory}
							<span class="form-error">{errors.defaultMemory}</span>
						{/if}
						<p class="form-hint">{(defaultMemory / 1024).toFixed(1)} GB</p>
					</div>

					<div class="form-group">
						<label for="minMemory" class="form-label">Minimum Memory (MB)</label>
						<input
							id="minMemory"
							type="number"
							bind:value={minMemory}
							min="256"
							max={maxMemory}
							step="256"
							class="form-input"
							disabled={saving}
						/>
						<p class="form-hint">{(minMemory / 1024).toFixed(1)} GB</p>
					</div>

					<div class="form-group">
						<label for="maxMemory" class="form-label">Maximum Memory (MB)</label>
						<input
							id="maxMemory"
							type="number"
							bind:value={maxMemory}
							min={minMemory}
							max="131072"
							step="1024"
							class="form-input"
							disabled={saving}
						/>
						<p class="form-hint">{(maxMemory / 1024).toFixed(1)} GB</p>
					</div>
				</div>
			</div>

			<!-- Disk Section -->
			<div class="section-card">
				<div class="section-header">
					<HardDrive class="h-5 w-5 text-blue-400" />
					<h3 class="section-title">Disk Configuration</h3>
				</div>

				<div class="form-grid">
					<div class="form-group">
						<label for="defaultDisk" class="form-label">
							Default Disk Size (GB)
							<span class="text-red-400">*</span>
						</label>
						<input
							id="defaultDisk"
							type="number"
							bind:value={defaultDisk}
							min={minDisk}
							max={maxDisk}
							class="form-input"
							class:error={errors.defaultDisk}
							disabled={saving}
						/>
						{#if errors.defaultDisk}
							<span class="form-error">{errors.defaultDisk}</span>
						{/if}
						<p class="form-hint">Disk space allocated by default</p>
					</div>

					<div class="form-group">
						<label for="minDisk" class="form-label">Minimum Disk (GB)</label>
						<input
							id="minDisk"
							type="number"
							bind:value={minDisk}
							min="4"
							max={maxDisk}
							class="form-input"
							disabled={saving}
						/>
						<p class="form-hint">Minimum allowed disk size</p>
					</div>

					<div class="form-group">
						<label for="maxDisk" class="form-label">Maximum Disk (GB)</label>
						<input
							id="maxDisk"
							type="number"
							bind:value={maxDisk}
							min={minDisk}
							max="2000"
							class="form-input"
							disabled={saving}
						/>
						<p class="form-hint">Maximum allowed disk size</p>
					</div>
				</div>
			</div>

			<!-- Info Box -->
			<div class="info-box">
				<p class="text-sm text-gray-400">
					<strong>Note:</strong> These settings define the default values shown in the deployment
					form. Users can still customize resources for individual applications within the allowed
					min/max ranges.
				</p>
			</div>

			<!-- Action Buttons -->
			<div class="form-actions">
				<button
					on:click={handleSave}
					disabled={saving}
					class="btn-primary"
					data-testid="save-resource-settings-button"
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

	.form-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1.5rem;
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
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
		border-color: var(--color-accent, #3b82f6);
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}

	.form-input:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.form-input.error {
		border-color: #ef4444;
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

	@media (max-width: 768px) {
		.form-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
