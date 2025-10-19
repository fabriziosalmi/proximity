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
				nodes = Array.isArray(response.data) ? response.data : [];
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
</script>

<svelte:head>
	<title>Proxmox Nodes - Proximity</title>
</svelte:head>

<div class="min-h-screen bg-rack-darker p-6">
	<!-- Header -->
	<div class="mb-8">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="mb-2 text-4xl font-bold text-white">Proxmox Nodes</h1>
				<p class="text-gray-400">Monitor and manage your Proxmox cluster nodes</p>
			</div>
			<button
				on:click={handleRefresh}
				disabled={loading}
				class="flex items-center gap-2 rounded-lg bg-rack-primary/10 px-4 py-2 text-rack-primary transition-colors hover:bg-rack-primary/20 disabled:opacity-50"
			>
				<RotateCw class={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
				Refresh
			</button>
		</div>

		{#if lastUpdated}
			<p class="mt-2 text-xs text-gray-500">
				Last updated: {lastUpdated.toLocaleTimeString()}
			</p>
		{/if}
	</div>

	<!-- Stats Summary -->
	{#if !loading && nodes.length > 0}
		<div class="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
			<div class="rounded-lg border border-gray-700/50 bg-gray-800/50 p-4">
				<div class="flex items-center gap-3">
					<Server class="h-8 w-8 text-blue-400" />
					<div>
						<div class="text-sm text-gray-400">Total Nodes</div>
						<div class="text-2xl font-bold text-white">{totalNodes}</div>
					</div>
				</div>
			</div>
			<div class="rounded-lg border border-green-500/20 bg-green-500/10 p-4">
				<div class="flex items-center gap-3">
					<Server class="h-8 w-8 text-green-400" />
					<div>
						<div class="text-sm text-green-200">Online</div>
						<div class="text-2xl font-bold text-green-400">{onlineNodes}</div>
					</div>
				</div>
			</div>
			<div class="rounded-lg border border-red-500/20 bg-red-500/10 p-4">
				<div class="flex items-center gap-3">
					<Server class="h-8 w-8 text-red-400" />
					<div>
						<div class="text-sm text-red-200">Offline</div>
						<div class="text-2xl font-bold text-red-400">{offlineNodes}</div>
					</div>
				</div>
			</div>
		</div>
	{/if}

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
</div>
