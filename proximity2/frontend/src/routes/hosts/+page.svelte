<!-- Hosts/Nodes View -->
<!-- Manage and monitor Proxmox nodes in rack-mounted style -->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Loader2, Server, RotateCw, RefreshCw, TestTube } from 'lucide-svelte';
	import HostRackCard from '$lib/components/HostRackCard.svelte';
	import { api } from '$lib/api';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import { toasts } from '$lib/stores/toast';

	interface ProxmoxNode {
		id: number;
		host_name: string;
		name: string;
		status: string;
		cpu_count?: number;
		cpu_usage?: number;
		memory_total?: number;
		memory_used?: number;
		storage_total?: number;
		storage_used?: number;
		uptime?: number;
		ip_address?: string;
		pve_version?: string;
	}

	let nodes: ProxmoxNode[] = [];
	let loading = true;
	let error = '';
	let pollingInterval: number;
	let lastUpdated: Date | null = null;

	async function loadNodes() {
		const wasLoading = loading;
		loading = true;
		error = '';

		try {
			const response = await api.getProxmoxNodes();

			if (response.success && response.data) {
				nodes = response.data || [];
				lastUpdated = new Date();
			} else {
				error = response.error || 'Failed to load Proxmox nodes';
				toasts.error(error, 5000);
			}
		} catch (err) {
			error = 'An unexpected error occurred';
			console.error(err);
			toasts.error(error, 5000);
		} finally {
			loading = false;
		}
	}

	async function handleRefresh() {
		toasts.info('Refreshing hosts...', 2000);
		await loadHosts();
		toasts.success('Hosts refreshed', 3000);
	}

	async function handleSync(hostId: number, hostName: string) {
		toasts.info(`Syncing nodes for ${hostName}...`, 2000);

		const response = await api.syncNodes(hostId);

		if (response.success) {
			toasts.success(`Nodes synced for ${hostName}`, 3000);
			await loadHosts();
		} else {
			toasts.error(response.error || `Failed to sync nodes for ${hostName}`, 5000);
		}
	}

	async function handleTest(hostId: number, hostName: string) {
		toasts.info(`Testing connection to ${hostName}...`, 2000);

		const response = await api.testHostConnection(hostId);

		if (response.success) {
			toasts.success(`Connection to ${hostName} successful`, 3000);
		} else {
			toasts.error(response.error || `Failed to connect to ${hostName}`, 5000);
		}
	}

	onMount(() => {
		// Set page title
		pageTitleStore.setTitle('Hosts');

		loadHosts();

		// Poll for updates every 30 seconds
		pollingInterval = setInterval(loadHosts, 30000) as unknown as number;
	});

	onDestroy(() => {
		if (pollingInterval) {
			clearInterval(pollingInterval);
		}
	});

	// Reactive stats
	$: onlineHosts = hosts.filter((h) => h.status === 'online').length;
	$: offlineHosts = hosts.filter((h) => h.status === 'offline').length;
</script>

<svelte:head>
	<title>Hosts - Proximity</title>
</svelte:head>

<div class="page-container">
	<!-- Header -->
	<div class="page-header">
		<div>
			<h1 class="page-title">Proxmox Hosts</h1>
			<p class="page-subtitle">Manage and monitor your infrastructure</p>
		</div>
		<div class="page-header-actions">
			<button
				on:click={handleRefresh}
				disabled={loading}
				class="btn-secondary"
			>
				<RefreshCw size={16} class={loading ? 'animate-spin' : ''} />
				Refresh
			</button>
			<button
				on:click={() => toasts.info('Add host feature coming soon', 3000)}
				class="btn-primary"
			>
				<Plus size={16} />
				Add Host
			</button>
		</div>
	</div>

	<!-- Stats Summary -->
	{#if !loading && hosts.length > 0}
		<div class="stats-summary">
			<div class="stat-item">
				<span class="stat-label">Total Hosts</span>
				<span class="stat-value">{hosts.length}</span>
			</div>
			<div class="stat-item stat-success">
				<span class="stat-label">Online</span>
				<span class="stat-value">{onlineHosts}</span>
			</div>
			<div class="stat-item stat-danger">
				<span class="stat-label">Offline</span>
				<span class="stat-value">{offlineHosts}</span>
			</div>
		</div>
	{/if}

	<!-- Loading State -->
	{#if loading && hosts.length === 0}
		<div class="loading-container">
			<Loader2 size={48} class="animate-spin" style="color: var(--text-color-secondary)" />
			<p style="color: var(--text-color-secondary); margin-top: 1rem;">Loading hosts...</p>
		</div>
	{:else if error}
		<!-- Error State -->
		<div class="error-container">
			<p class="error-message">{error}</p>
			<button on:click={loadHosts} class="btn-secondary">
				Try Again
			</button>
		</div>
	{:else if hosts.length === 0}
		<!-- Empty State -->
		<div class="empty-container">
			<HardDrive size={64} style="color: var(--text-color-secondary); opacity: 0.5;" />
			<p class="empty-title">No hosts configured</p>
			<p class="empty-subtitle">Add your first Proxmox host to get started</p>
			<button
				on:click={() => toasts.info('Add host feature coming soon', 3000)}
				class="btn-primary"
				style="margin-top: 1rem;"
			>
				<Plus size={16} />
				Add Host
			</button>
		</div>
	{:else}
		<!-- Hosts Rack -->
		<div class="rack-canvas">
			{#each hosts as host (host.id)}
				<HostCard {host}>
					<div slot="actions" class="host-actions">
						<button
							on:click={() => handleTest(host.id, host.name)}
							class="btn-small btn-secondary"
						>
							Test
						</button>
						<button
							on:click={() => handleSync(host.id, host.name)}
							class="btn-small btn-secondary"
						>
							<RefreshCw size={14} />
							Sync
						</button>
					</div>
				</HostCard>
			{/each}
		</div>
	{/if}
</div>

<style>
	/* Page Container */
	.page-container {
		padding: 2rem;
		max-width: 1400px;
		margin: 0 auto;
	}

	/* Header */
	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 2rem;
		gap: 1rem;
	}

	.page-title {
		font-size: 2rem;
		font-weight: 700;
		color: var(--text-color-primary);
		margin: 0 0 0.5rem 0;
	}

	.page-subtitle {
		font-size: 1rem;
		color: var(--text-color-secondary);
		margin: 0;
	}

	.page-header-actions {
		display: flex;
		gap: 0.75rem;
	}

	/* Stats Summary */
	.stats-summary {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		padding: 1rem 1.5rem;
		background: var(--card-bg-color);
		border: 1px solid var(--card-border-color);
		border-radius: 0.5rem;
		gap: 0.5rem;
	}

	.stat-label {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text-color-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.stat-value {
		font-size: 1.875rem;
		font-weight: 700;
		color: var(--text-color-primary);
	}

	.stat-success .stat-value {
		color: #10b981;
	}

	.stat-danger .stat-value {
		color: #ef4444;
	}

	/* Loading/Error/Empty States */
	.loading-container,
	.error-container,
	.empty-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		text-align: center;
	}

	.error-message {
		color: #ef4444;
		margin-bottom: 1rem;
	}

	.empty-title {
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--text-color-primary);
		margin: 1rem 0 0.5rem 0;
	}

	.empty-subtitle {
		font-size: 0.875rem;
		color: var(--text-color-secondary);
		margin: 0;
	}

	/* Hosts Grid */
	.hosts-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
		gap: 1.5rem;
	}

	/* Host Actions */
	.host-actions {
		display: flex;
		gap: 0.5rem;
		width: 100%;
	}

	/* Buttons */
	.btn-primary,
	.btn-secondary,
	.btn-small {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 1rem;
		font-size: 0.875rem;
		font-weight: 600;
		border-radius: 0.375rem;
		cursor: pointer;
		transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
		border: none;
	}

	.btn-primary {
		background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
		color: white;
		box-shadow: 0 2px 4px rgba(14, 165, 233, 0.3);
	}

	.btn-primary:hover {
		background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
		box-shadow: 0 0 20px rgba(14, 165, 233, 0.4), 0 4px 8px rgba(14, 165, 233, 0.3);
	}

	.btn-secondary {
		background: var(--card-bg-color);
		color: var(--text-color-primary);
		border: 1px solid var(--card-border-color);
	}

	.btn-secondary:hover {
		border-color: var(--border-color-primary);
		background: rgba(255, 255, 255, 0.05);
	}

	.btn-secondary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-small {
		padding: 0.5rem 0.75rem;
		font-size: 0.75rem;
		flex: 1;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.page-container {
			padding: 1rem;
		}

		.page-header {
			flex-direction: column;
		}

		.page-header-actions {
			width: 100%;
		}

		.hosts-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
