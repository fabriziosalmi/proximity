<script lang="ts">
	/**
	 * Network Settings Component
	 * Manage default network configuration for deployments
	 */
	import { onMount } from 'svelte';
	import { Loader2, Network, Wifi, Globe, Save } from 'lucide-svelte';
	import { toasts } from '$lib/stores/toast';
	import { api } from '$lib/api';

	let loading = false;
	let saving = false;

	// Form data - Network configuration
	let networkMode = 'bridge'; // bridge, nat, or host
	let defaultSubnet = '10.0.0.0/24';
	let defaultGateway = '10.0.0.1';
	let dnsServers = '8.8.8.8, 8.8.4.4';
	let dhcpEnabled = true;
	let ipv6Enabled = false;
	let vlanId = '';

	// Validation
	let errors: Record<string, string> = {};

	async function loadSettings() {
		loading = true;
		errors = {};

		try {
			// Load from backend API
			const response = await api.getNetworkSettings();

			if (response.success && response.data) {
				// Map backend field names to frontend variables
				defaultSubnet = response.data.default_subnet || '10.0.0.0/24';
				defaultGateway = response.data.default_gateway || '10.0.0.1';

				// Handle DNS servers - backend provides separate fields
				const dnsPrimary = response.data.default_dns_primary || '8.8.8.8';
				const dnsSecondary = response.data.default_dns_secondary || '8.8.4.4';
				dnsServers = dnsSecondary ? `${dnsPrimary}, ${dnsSecondary}` : dnsPrimary;

				logger.debug('✅ Network settings loaded from backend:', response.data);
			} else {
				throw new Error(response.error || 'Failed to load settings');
			}
		} catch (err) {
			logger.error('Failed to load network settings:', err);
			toasts.error('Failed to load network settings', 5000);
		} finally {
			loading = false;
		}
	}

	function validateIP(ip: string): boolean {
		const ipPattern =
			/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
		return ipPattern.test(ip);
	}

	function validateCIDR(cidr: string): boolean {
		const cidrPattern = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
		return cidrPattern.test(cidr);
	}

	function validateForm(): boolean {
		errors = {};

		// Subnet validation
		if (!validateCIDR(defaultSubnet)) {
			errors.defaultSubnet = 'Invalid CIDR notation (e.g., 10.0.0.0/24)';
		}

		// Gateway validation
		if (!validateIP(defaultGateway)) {
			errors.defaultGateway = 'Invalid IP address';
		}

		// DNS validation
		const dnsArray = dnsServers.split(',').map((s) => s.trim());
		const invalidDns = dnsArray.filter((dns) => !validateIP(dns));
		if (invalidDns.length > 0) {
			errors.dnsServers = 'Invalid DNS server IP addresses';
		}

		// VLAN validation (if provided)
		if (vlanId && (isNaN(parseInt(vlanId)) || parseInt(vlanId) < 1 || parseInt(vlanId) > 4094)) {
			errors.vlanId = 'VLAN ID must be between 1 and 4094';
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
			// Parse DNS servers
			const dnsArray = dnsServers.split(',').map((s) => s.trim()).filter((s) => s);
			const dnsPrimary = dnsArray[0] || '8.8.8.8';
			const dnsSecondary = dnsArray[1] || null;

			// Map frontend variables to backend field names
			const settings = {
				default_subnet: defaultSubnet,
				default_gateway: defaultGateway,
				default_dns_primary: dnsPrimary,
				default_dns_secondary: dnsSecondary,
				default_bridge: 'vmbr0' // Default bridge name for Proxmox
			};

			// Save to backend API
			const response = await api.saveNetworkSettings(settings);

			if (response.success) {
				toasts.success('Network settings saved successfully', 5000);
				logger.debug('✅ Network settings saved to backend:', response.data);
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
			<span class="ml-3 text-gray-400">Loading network settings...</span>
		</div>
	{:else}
		<!-- Settings Form -->
		<div class="settings-form">
			<div class="form-header">
				<Network class="h-6 w-6 text-blue-400" />
				<h2 class="form-title">Network Configuration</h2>
			</div>

			<p class="form-description">
				Configure default network settings for new container deployments. These settings ensure
				proper network connectivity and IP address management.
			</p>

			<!-- Network Mode Section -->
			<div class="section-card">
				<div class="section-header">
					<Wifi class="h-5 w-5 text-cyan-400" />
					<h3 class="section-title">Network Mode</h3>
				</div>

				<div class="form-group">
					<label for="networkMode" class="form-label">
						Networking Type
						<span class="text-red-400">*</span>
					</label>
					<select id="networkMode" bind:value={networkMode} class="form-input" disabled={saving}>
						<option value="bridge">Bridge (Recommended)</option>
						<option value="nat">NAT</option>
						<option value="host">Host</option>
					</select>
					<p class="form-hint">
						{#if networkMode === 'bridge'}
							Containers get their own IP on a virtual bridge
						{:else if networkMode === 'nat'}
							Containers share host IP with port forwarding
						{:else}
							Containers use host network stack directly
						{/if}
					</p>
				</div>
			</div>

			<!-- IP Configuration Section -->
			<div class="section-card">
				<div class="section-header">
					<Globe class="h-5 w-5 text-green-400" />
					<h3 class="section-title">IP Address Configuration</h3>
				</div>

				<div class="form-grid">
					<div class="form-group">
						<label for="defaultSubnet" class="form-label">
							Default Subnet (CIDR)
							<span class="text-red-400">*</span>
						</label>
						<input
							id="defaultSubnet"
							type="text"
							bind:value={defaultSubnet}
							placeholder="10.0.0.0/24"
							class="form-input"
							class:error={errors.defaultSubnet}
							disabled={saving}
						/>
						{#if errors.defaultSubnet}
							<span class="form-error">{errors.defaultSubnet}</span>
						{/if}
						<p class="form-hint">Network range for container IPs</p>
					</div>

					<div class="form-group">
						<label for="defaultGateway" class="form-label">
							Default Gateway
							<span class="text-red-400">*</span>
						</label>
						<input
							id="defaultGateway"
							type="text"
							bind:value={defaultGateway}
							placeholder="10.0.0.1"
							class="form-input"
							class:error={errors.defaultGateway}
							disabled={saving}
						/>
						{#if errors.defaultGateway}
							<span class="form-error">{errors.defaultGateway}</span>
						{/if}
						<p class="form-hint">Gateway IP for routing</p>
					</div>

					<div class="form-group">
						<label for="dnsServers" class="form-label">
							DNS Servers
							<span class="text-red-400">*</span>
						</label>
						<input
							id="dnsServers"
							type="text"
							bind:value={dnsServers}
							placeholder="8.8.8.8, 8.8.4.4"
							class="form-input"
							class:error={errors.dnsServers}
							disabled={saving}
						/>
						{#if errors.dnsServers}
							<span class="form-error">{errors.dnsServers}</span>
						{/if}
						<p class="form-hint">Comma-separated DNS server IPs</p>
					</div>
				</div>
			</div>

			<!-- Advanced Settings Section -->
			<div class="section-card">
				<div class="section-header">
					<Network class="h-5 w-5 text-purple-400" />
					<h3 class="section-title">Advanced Settings</h3>
				</div>

				<div class="form-grid">
					<div class="form-group">
						<label for="vlanId" class="form-label">VLAN ID (Optional)</label>
						<input
							id="vlanId"
							type="text"
							bind:value={vlanId}
							placeholder="e.g., 100"
							class="form-input"
							class:error={errors.vlanId}
							disabled={saving}
						/>
						{#if errors.vlanId}
							<span class="form-error">{errors.vlanId}</span>
						{/if}
						<p class="form-hint">VLAN tag for network isolation</p>
					</div>

					<div class="form-group">
						<label class="form-checkbox-label">
							<input
								type="checkbox"
								bind:checked={dhcpEnabled}
								disabled={saving}
								class="form-checkbox"
							/>
							<span class="ml-2">Enable DHCP</span>
						</label>
						<p class="form-hint mt-1">Automatically assign IP addresses</p>
					</div>

					<div class="form-group">
						<label class="form-checkbox-label">
							<input
								type="checkbox"
								bind:checked={ipv6Enabled}
								disabled={saving}
								class="form-checkbox"
							/>
							<span class="ml-2">Enable IPv6</span>
						</label>
						<p class="form-hint mt-1">Support IPv6 addressing</p>
					</div>
				</div>
			</div>

			<!-- Info Box -->
			<div class="info-box">
				<p class="text-sm text-gray-400">
					<strong>Note:</strong> Network changes may require restarting containers to take effect.
					Ensure your network configuration doesn't conflict with existing infrastructure.
				</p>
			</div>

			<!-- Action Buttons -->
			<div class="form-actions">
				<button
					on:click={handleSave}
					disabled={saving}
					class="btn-primary"
					data-testid="save-network-settings-button"
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

	@media (max-width: 768px) {
		.form-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
