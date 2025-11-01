<script lang="ts">
	/**
	 * DeploymentModal - Modal for deploying a new application
	 */
	import { createEventDispatcher, onMount } from 'svelte';
	import { X, Loader2, Server, HardDrive, Settings } from 'lucide-svelte';
	import { api } from '$lib/api';
	import { logger } from '$lib/logger';

	const dispatch = createEventDispatcher();

	export let isOpen = false;
	export let app: any = null;

	let hostname = '';
	let selectedHostId: number | null = null;
	let selectedNode = '';
	let hosts: any[] = [];
	let nodes: any[] = [];
	let loading = false;
	let loadingHosts = false;
	let error = '';

	// Advanced options
	let showAdvanced = false;
	let customPorts: Record<string, number> = {};
	let customEnv: Record<string, string> = {};

	$: if (isOpen && app) {
		// Reset form when modal opens
		// Add timestamp suffix to make hostname unique
		const baseHostname = app.name.toLowerCase().replace(/[^a-z0-9-]/g, '-');
		hostname = `${baseHostname}-${Date.now().toString().slice(-6)}`;
		selectedHostId = null;
		selectedNode = '';
		error = '';
		showAdvanced = false;
		customPorts = {};
		customEnv = {};
		loading = false;
		loadingHosts = false;
		fetchHosts();
	}

	async function fetchHosts() {
		loadingHosts = true;
		const response = await api.listHosts();

		if (response.success && response.data) {
			hosts = response.data;
			// Auto-select first host if available
			if (hosts.length > 0) {
				selectedHostId = hosts[0].id;
				await fetchNodes(hosts[0].id);
			}
		}
		loadingHosts = false;
	}

	async function fetchNodes(hostId: number) {
		// First sync the nodes from Proxmox
		await api.syncNodes(hostId);

		// Then fetch the synced nodes list
		const response = await api.getProxmoxNodes(hostId);
		if (response.success && response.data) {
			nodes = Array.isArray(response.data) ? response.data : [];
			// Auto-select first node
			if (nodes.length > 0) {
				selectedNode = nodes[0].name;
			}
		}
	}

	async function handleHostChange() {
		if (selectedHostId) {
			await fetchNodes(selectedHostId);
		}
	}

	async function handleDeploy() {
		logger.debug('🚀 [DeploymentModal] Deploy clicked');
		logger.debug('Hostname:', hostname);
		logger.debug('SelectedHostId:', selectedHostId);

		if (!hostname || !selectedHostId) {
			error = 'Please fill in all required fields';
			return;
		}

		// Validate hostname
		if (!/^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$/.test(hostname)) {
			error = 'Hostname must start and end with alphanumeric, contain only lowercase letters, numbers, and hyphens, and be 63 characters or less';
			return;
		}

		// Check if all required fields are set
		const deploymentData = {
			catalog_id: app.id,
			hostname,
			...(selectedNode && { node: selectedNode }),
			...(Object.keys(customPorts).length > 0 && { ports: customPorts }),
			...(Object.keys(customEnv).length > 0 && { environment: customEnv })
		};

		logger.debug('📤 Deploying:', deploymentData);

		// Dispatch to parent - parent will handle modal closing and state updates
		// Don't set loading = false here as component might be unmounting
		dispatch('deploy', deploymentData);
	}

	function handleClose() {
		if (!loading) {
			isOpen = false;
			dispatch('close');
		}
	}

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			handleClose();
		}
	}
</script>

{#if isOpen && app}
	<div
		class="fixed inset-0 z-[9999] flex items-center justify-center p-4"
		style="background-color: rgba(0,0,0,0.9) !important;"
		on:click={handleBackdropClick}
		role="dialog"
		aria-modal="true"
		aria-labelledby="modal-title"
	>
		<div
			class="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-lg bg-gray-800 border-2 border-cyan-500 shadow-2xl"
		>
			<!-- Header -->
			<div class="flex items-center justify-between border-b border-rack-primary/20 p-6">
				<div class="flex items-center gap-3">
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-rack-primary/10 text-rack-primary"
					>
						<Server class="h-6 w-6" />
					</div>
					<div>
						<h2 id="modal-title" class="text-xl font-semibold text-white">
							Deploy {app.name}
						</h2>
						<p class="text-sm text-gray-400">Configure deployment settings</p>
					</div>
				</div>
				<button
					on:click={handleClose}
					disabled={loading}
					class="rounded-lg p-2 text-gray-400 transition-colors hover:bg-rack-darker/50 hover:text-white disabled:opacity-50"
					aria-label="Close modal"
				>
					<X class="h-5 w-5" />
				</button>
			</div>

			<!-- Content -->
			<div class="p-6">

				{#if error}
					<div class="mb-4 rounded-lg border border-red-500/50 bg-red-500/10 p-4 text-red-400">
						{error}
					</div>
				{/if}

				<form on:submit|preventDefault={handleDeploy} class="space-y-6">
					<!-- Hostname -->
					<div>
						<label for="hostname" class="mb-2 block text-sm font-medium text-white">
							Hostname <span class="text-red-400">*</span>
						</label>
						<input
							id="hostname"
							name="hostname"
							type="text"
							bind:value={hostname}
							required
							class="w-full rounded-lg border-2 border-cyan-500 bg-gray-900 px-4 py-3 text-white text-lg placeholder-gray-400 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
							placeholder="my-app-hostname"
						/>
						<p class="mt-2 text-sm text-gray-400">
							Lowercase letters, numbers, and hyphens only
						</p>
					</div>

					<!-- Host Selection -->
					<div>
						<label for="host" class="mb-2 block text-sm font-medium text-gray-300">
							Proxmox Host <span class="text-red-400">*</span>
						</label>
						{#if loadingHosts}
							<div class="flex items-center gap-2 text-gray-400">
								<Loader2 class="h-4 w-4 animate-spin" />
								<span>Loading hosts...</span>
							</div>
						{:else if hosts.length === 0}
							<p class="text-sm text-yellow-400">
								No Proxmox hosts configured. Please add a host first.
							</p>
						{:else}
							<select
								id="host"
								bind:value={selectedHostId}
								on:change={handleHostChange}
								disabled={loading}
								required
								class="w-full rounded-lg border border-rack-primary/30 bg-rack-darker px-4 py-3 text-white focus:border-rack-primary focus:outline-none focus:ring-2 focus:ring-rack-primary/20 disabled:opacity-50"
							>
								{#each hosts as host}
									<option value={host.id}>{host.name} ({host.url})</option>
								{/each}
							</select>
						{/if}
					</div>

					<!-- Node Selection -->
					{#if nodes.length > 0}
						<div>
							<label for="node" class="mb-2 block text-sm font-medium text-gray-300">
								Node (Optional)
							</label>
							<select
								id="node"
								bind:value={selectedNode}
								disabled={loading}
								class="w-full rounded-lg border border-rack-primary/30 bg-rack-darker px-4 py-3 text-white focus:border-rack-primary focus:outline-none focus:ring-2 focus:ring-rack-primary/20 disabled:opacity-50"
							>
								<option value="">Auto-select</option>
								{#each nodes as node}
									<option value={node.name}>{node.name}</option>
								{/each}
							</select>
						</div>
					{/if}

					<!-- Advanced Options Toggle -->
					<button
						type="button"
						on:click={() => (showAdvanced = !showAdvanced)}
						class="flex items-center gap-2 text-sm text-rack-primary hover:text-rack-primary/80"
					>
						<Settings class="h-4 w-4" />
						{showAdvanced ? 'Hide' : 'Show'} Advanced Options
					</button>

					{#if showAdvanced}
						<div class="space-y-4 rounded-lg border border-rack-primary/20 bg-rack-darker/50 p-4">
							<p class="text-sm text-gray-400">
								Advanced options for custom ports and environment variables (coming soon)
							</p>
						</div>
					{/if}
				</form>
			</div>

			<!-- Footer -->
			<div class="flex items-center justify-end gap-3 border-t border-rack-primary/20 p-6">
				<button
					on:click={handleClose}
					disabled={loading}
					class="rounded-lg border border-rack-primary/30 px-6 py-2 text-white transition-colors hover:bg-rack-darker/50 disabled:opacity-50"
				>
					Cancel
				</button>
				<button
					type="button"
					on:click={handleDeploy}
					disabled={loading || !hostname || !selectedHostId || hosts.length === 0}
					class="flex items-center gap-2 rounded-lg bg-rack-primary px-6 py-2 font-medium text-white transition-colors hover:bg-rack-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{#if loading}
						<Loader2 class="h-4 w-4 animate-spin" />
						Deploying...
					{:else}
						<HardDrive class="h-4 w-4" />
						Deploy
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Prevent body scroll when modal is open */
	:global(body:has(.fixed)) {
		overflow: hidden;
	}
</style>
