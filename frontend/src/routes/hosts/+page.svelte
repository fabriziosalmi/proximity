<!-- Hosts/Nodes View -->
<!-- Manage and monitor Proxmox nodes in rack-mounted style -->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { Loader2, Server, RotateCw, RefreshCw, TestTube, Plus, CheckCircle2, XCircle, Cpu, HardDrive } from 'lucide-svelte';
	import HostRackCard from '$lib/components/HostRackCard.svelte';
	import { api } from '$lib/api';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import { toasts } from '$lib/stores/toast';
	import StatBlock from '$lib/components/dashboard/StatBlock.svelte';
	import NavigationRack from '$lib/components/layout/NavigationRack.svelte';
	import OperationalRack from '$lib/components/layout/OperationalRack.svelte';

	interface ProxmoxNode {
		id: number;
		name: string;
		host: string;
		port?: number;
		user?: string;
		is_active?: boolean;
		is_default?: boolean;
		last_seen?: string | null;
		// Optional node stats (might not be available)
		status?: string;
		cpu_count?: number;
		cpu_usage?: number;
		memory_total?: number;
		memory_used?: number;
		storage_total?: number;
		storage_used?: number;
		uptime?: number;
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
			const response = await api.listHosts();

			if (response.success && response.data) {
				nodes = Array.isArray(response.data) ? response.data : [];
				lastUpdated = new Date();
			} else {
				error = response.error || 'Failed to load Proxmox hosts';
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
		toasts.info('Refreshing nodes...', 2000);
		await loadNodes();
		if (!error) {
			toasts.success('Nodes refreshed successfully', 3000);
		}
	}

	onMount(() => {
		// Set page title
		pageTitleStore.setTitle('Proxmox Nodes');

		loadNodes();

		// Poll for updates every 30 seconds
		pollingInterval = setInterval(loadNodes, 30000) as unknown as number;
	});

	onDestroy(() => {
		if (pollingInterval) {
			clearInterval(pollingInterval);
		}
	});

	// Reactive stats
	$: onlineNodes = nodes.filter((n) => n.status === 'online').length;
	$: offlineNodes = nodes.filter((n) => n.status === 'offline').length;
	$: totalNodes = nodes.length;
	
	// Aggregate CPU usage (average of online nodes)
	$: avgCpuUsage = onlineNodes > 0 
		? Math.round(
			nodes
				.filter(n => n.status === 'online' && n.cpu_usage !== undefined)
				.reduce((sum, n) => sum + (n.cpu_usage || 0), 0) / 
			nodes.filter(n => n.status === 'online' && n.cpu_usage !== undefined).length
		)
		: 0;
	
	// Aggregate Memory usage (average of online nodes)
	$: avgMemoryUsage = onlineNodes > 0
		? Math.round(
			nodes
				.filter(n => n.status === 'online' && n.memory_used !== undefined && n.memory_total !== undefined)
				.reduce((sum, n) => sum + ((n.memory_used || 0) / (n.memory_total || 1) * 100), 0) /
			nodes.filter(n => n.status === 'online' && n.memory_used !== undefined && n.memory_total !== undefined).length
		)
		: 0;
	
	function handleAddHost() {
		goto('/settings/proxmox');
	}
</script>

<svelte:head>
	<title>Proxmox Nodes - Proximity</title>
</svelte:head>

<div class="bg-rack-darker">
	<!-- ============================================ -->
	<!-- STICKY HEADER: Always-Visible Control Surface -->
	<!-- ============================================ -->
	<header class="sticky-header">
		<!-- Desktop Navigation Rack (visible only on lg: screens) -->
		<div class="px-6 pt-6">
			<NavigationRack />
		</div>
		
		<!-- Operational Control Panel Rack -->
		<div class="px-6 pb-6">
			<OperationalRack title="Infrastructure Operations">
		<!-- Stats Slot -->
		<svelte:fragment slot="stats">
			<StatBlock 
				label="Total Hosts" 
				value={totalNodes} 
				icon={Server}
				ledColor="var(--color-accent)"
				borderColor="var(--color-accent)"
			/>
			
			<StatBlock 
				label="Online" 
				value={onlineNodes} 
				icon={CheckCircle2}
				ledColor="var(--color-led-active)"
				borderColor="rgba(16, 185, 129, 0.3)"
				pulse={onlineNodes > 0}
			/>
			
			<StatBlock 
				label="Offline" 
				value={offlineNodes} 
				icon={XCircle}
				ledColor={offlineNodes > 0 ? "var(--color-led-danger)" : "var(--color-led-inactive)"}
				borderColor={offlineNodes > 0 ? "rgba(239, 68, 68, 0.3)" : "var(--border-color-secondary)"}
			/>
			
			{#if onlineNodes > 0}
				<StatBlock 
					label="Avg CPU" 
					value={`${avgCpuUsage}%`} 
					icon={Cpu}
					ledColor="var(--color-accent)"
					borderColor="rgba(14, 165, 233, 0.3)"
				/>
				
				<StatBlock 
					label="Avg Memory" 
					value={`${avgMemoryUsage}%`} 
					icon={HardDrive}
					ledColor="var(--color-accent)"
					borderColor="rgba(14, 165, 233, 0.3)"
				/>
			{/if}
		</svelte:fragment>

		<!-- Actions Slot -->
		<svelte:fragment slot="actions">
			{#if lastUpdated}
				<div class="last-updated">
					<RefreshCw class="h-3.5 w-3.5" />
					<span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
				</div>
			{/if}

			<div class="flex gap-2">
				<!-- Add Host Button -->
				<button
					on:click={handleAddHost}
					class="flex items-center gap-2 rounded-lg bg-rack-primary px-4 py-2 text-sm font-semibold text-white transition-all hover:bg-rack-primary/90"
					title="Add new Proxmox host"
				>
					<Plus class="h-4 w-4" />
					<span>Add Host</span>
				</button>
				
				<!-- Refresh Button -->
				<button
					on:click={handleRefresh}
					disabled={loading}
					class="refresh-button"
					title="Refresh node status"
				>
					<RotateCw class={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
					<span>Refresh</span>
				</button>
			</div>
		</svelte:fragment>
		</OperationalRack>
		</div>
	</header>

	<!-- ============================================ -->
	<!-- SCROLLABLE CONTENT: Host Racks Flow Beneath -->
	<!-- ============================================ -->
	<main class="px-10 pt-6 pb-6">
		<!-- Loading state with skeleton -->
	{#if loading && nodes.length === 0}
		<div class="space-y-4">
			{#each Array(3) as _, i}
				<div class="animate-pulse rounded-lg border-2 border-gray-700/50 bg-gray-800/50" style="height: 7rem;">
					<div class="flex h-full items-center gap-4 p-4">
						<div class="h-12 w-12 flex-shrink-0 rounded-lg bg-gray-700/50"></div>
						<div class="flex-1 space-y-2">
							<div class="h-5 w-1/3 rounded bg-gray-700/50"></div>
							<div class="h-4 w-1/4 rounded bg-gray-700/50"></div>
						</div>
						<div class="h-8 w-24 rounded bg-gray-700/50"></div>
					</div>
				</div>
			{/each}
		</div>
	{:else if error}
		<!-- Error State -->
		<div class="flex min-h-[400px] flex-col items-center justify-center rounded-lg border-2 border-red-500/20 bg-red-500/5 p-8">
			<div class="mb-4 text-red-400">
				<Server class="h-16 w-16" />
			</div>
			<p class="mb-4 text-lg font-semibold text-red-400">{error}</p>
			<button
				on:click={handleRefresh}
				class="flex items-center gap-2 rounded-lg bg-red-500/20 px-4 py-2 text-red-400 transition-colors hover:bg-red-500/30"
			>
				<RefreshCw class="h-4 w-4" />
				Try Again
			</button>
		</div>
	{:else if nodes.length === 0}
		<!-- Empty State -->
		<div class="flex min-h-[400px] flex-col items-center justify-center rounded-lg border-2 border-gray-700/50 bg-gray-800/30 p-8">
			<Server class="mb-4 h-16 w-16 text-gray-600" />
			<p class="mb-2 text-xl font-semibold text-gray-400">No Nodes Found</p>
			<p class="text-sm text-gray-500">No Proxmox nodes are currently registered in the system</p>
		</div>
	{:else}
		<!-- Nodes Rack - Vertical Stack -->
		<div class="space-y-4">
			{#each nodes as node (node.id)}
				<HostRackCard host={node}>
					<div slot="actions" class="flex gap-2">
						<!-- Actions can be added here if needed -->
					</div>
				</HostRackCard>
			{/each}
		</div>
	{/if}
	</main>
</div>

