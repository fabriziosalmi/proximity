<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { addToast } from '$lib/stores/toastStore';
	import Icon from '@iconify/svelte';

	interface UnmanagedContainer {
		vmid: number;
		name: string;
		status: string;
		node: string;
		memory: number;
		disk: number;
		uptime: number;
		cpus: number;
	}

	interface ContainerSelection {
		container: UnmanagedContainer;
		selected: boolean;
		suggested_type: string;
		port_to_expose: number;
	}

	interface CatalogApp {
		id: string;
		name: string;
		icon: string;
		ports: number[];
	}

	let loading = true;
	let containers: ContainerSelection[] = [];
	let catalogApps: CatalogApp[] = [];
	let showConfirmModal = false;
	let adopting = false;
	let adoptionProgress = 0;
	let adoptionTotal = 0;

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		loading = true;

		try {
			// Load unmanaged containers
			const containersResponse = await api.discoverUnmanagedContainers();
			if (containersResponse.success && containersResponse.data) {
				containers = (containersResponse.data as UnmanagedContainer[]).map((c) => ({
					container: c,
					selected: false,
					suggested_type: 'custom',
					port_to_expose: 80
				}));
			}

			// Load catalog for app type matching
			const catalogResponse = await api.getCatalog();
			if (catalogResponse.success && catalogResponse.data) {
				catalogApps = catalogResponse.data.applications || [];
			}
		} catch (error) {
			console.error('Failed to load data:', error);
			addToast('Failed to load containers', 'error');
		} finally {
			loading = false;
		}
	}

	function toggleSelection(index: number) {
		containers[index].selected = !containers[index].selected;
		containers = [...containers]; // Trigger reactivity
	}

	function selectAll() {
		const allSelected = containers.every((c) => c.selected);
		containers = containers.map((c) => ({ ...c, selected: !allSelected }));
	}

	$: selectedCount = containers.filter((c) => c.selected).length;
	$: allValid = containers
		.filter((c) => c.selected)
		.every((c) => c.suggested_type && c.port_to_expose > 0);

	function openConfirmModal() {
		if (selectedCount === 0) {
			addToast('Please select at least one container', 'warning');
			return;
		}
		if (!allValid) {
			addToast('Please configure all selected containers', 'warning');
			return;
		}
		showConfirmModal = true;
	}

	async function confirmAdoption() {
		showConfirmModal = false;
		adopting = true;
		adoptionProgress = 0;

		const selectedContainers = containers.filter((c) => c.selected);
		adoptionTotal = selectedContainers.length;

		for (const item of selectedContainers) {
			try {
				const response = await api.adoptContainer({
					vmid: item.container.vmid,
					node_name: item.container.node,
					suggested_type: item.suggested_type,
					port_to_expose: item.port_to_expose
				});

				if (response.success) {
					addToast(
						`Container "${item.container.name}" adoption started`,
						'success'
					);
				} else {
					addToast(
						`Failed to adopt "${item.container.name}": ${response.error}`,
						'error'
					);
				}
			} catch (error) {
				addToast(`Error adopting "${item.container.name}"`, 'error');
			}

			adoptionProgress++;
		}

		adopting = false;

		// Redirect to apps page after a short delay
		addToast(
			`Adoption process started for ${adoptionTotal} container(s). Check /apps page for status.`,
			'info'
		);
		setTimeout(() => {
			goto('/apps');
		}, 2000);
	}

	function formatBytes(bytes: number): string {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
	}

	function formatUptime(seconds: number): string {
		const days = Math.floor(seconds / 86400);
		const hours = Math.floor((seconds % 86400) / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);

		if (days > 0) return `${days}d ${hours}h`;
		if (hours > 0) return `${hours}h ${minutes}m`;
		return `${minutes}m`;
	}
</script>

<div class="container mx-auto px-4 py-8 max-w-7xl">
	<!-- Header -->
	<div class="mb-8">
		<div class="flex items-center gap-4 mb-4">
			<button
				on:click={() => goto('/apps')}
				class="btn btn-ghost btn-sm gap-2"
			>
				<Icon icon="mdi:arrow-left" class="w-5 h-5" />
				Back to Apps
			</button>
		</div>

		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-4xl font-bold mb-2">Adopt Existing Containers</h1>
				<p class="text-base-content/70">
					Import existing LXC containers into Proximity management. Containers will keep their
					original configuration and hostname.
				</p>
			</div>

			<button
				on:click={loadData}
				class="btn btn-outline gap-2"
				disabled={loading}
			>
				<Icon icon="mdi:refresh" class="w-5 h-5" class:animate-spin={loading} />
				Refresh
			</button>
		</div>
	</div>

	{#if loading}
		<!-- Loading State -->
		<div class="space-y-4">
			{#each Array(3) as _}
				<div class="skeleton h-20 w-full"></div>
			{/each}
		</div>
	{:else if containers.length === 0}
		<!-- Empty State -->
		<div class="card bg-base-200">
			<div class="card-body items-center text-center py-16">
				<Icon icon="mdi:inbox" class="w-24 h-24 text-base-content/30 mb-4" />
				<h2 class="text-2xl font-bold mb-2">No Unmanaged Containers Found</h2>
				<p class="text-base-content/70 mb-6 max-w-md">
					All containers on your Proxmox nodes are already managed by Proximity, or there are no
					containers to discover.
				</p>
				<div class="flex gap-3">
					<button on:click={loadData} class="btn btn-primary gap-2">
						<Icon icon="mdi:refresh" class="w-5 h-5" />
						Refresh Discovery
					</button>
					<button on:click={() => goto('/apps')} class="btn btn-outline">
						Go to Apps
					</button>
				</div>
			</div>
		</div>
	{:else}
		<!-- Main Content -->
		<div class="space-y-6">
			<!-- Selection Summary -->
			<div class="alert alert-info">
				<Icon icon="mdi:information" class="w-6 h-6" />
				<div class="flex-1">
					<h3 class="font-bold">Discovery Complete</h3>
					<div class="text-sm">
						Found {containers.length} unmanaged container{containers.length !== 1 ? 's' : ''}.
						{#if selectedCount > 0}
							<span class="font-semibold">{selectedCount} selected</span> for adoption.
						{:else}
							Select containers below to begin adoption.
						{/if}
					</div>
				</div>
			</div>

			<!-- Containers Table -->
			<div class="card bg-base-100 shadow-xl">
				<div class="card-body p-0">
					<div class="overflow-x-auto">
						<table class="table table-zebra">
							<thead>
								<tr>
									<th>
										<label>
											<input
												type="checkbox"
												class="checkbox checkbox-sm"
												checked={containers.every((c) => c.selected)}
												on:change={selectAll}
											/>
										</label>
									</th>
									<th>Container</th>
									<th>Status</th>
									<th>Resources</th>
									<th>App Type</th>
									<th>Port</th>
								</tr>
							</thead>
							<tbody>
								{#each containers as item, index}
									<tr class:bg-primary/5={item.selected}>
										<td>
											<label>
												<input
													type="checkbox"
													class="checkbox checkbox-primary"
													bind:checked={item.selected}
													on:change={() => toggleSelection(index)}
												/>
											</label>
										</td>
										<td>
											<div class="flex flex-col">
												<div class="font-bold">{item.container.name}</div>
												<div class="text-sm opacity-60">
													VMID {item.container.vmid} · Node {item.container.node}
												</div>
											</div>
										</td>
										<td>
											<div class="badge badge-sm"
												class:badge-success={item.container.status === 'running'}
												class:badge-error={item.container.status === 'stopped'}
											>
												{item.container.status}
											</div>
											<div class="text-xs opacity-60 mt-1">
												{formatUptime(item.container.uptime)}
											</div>
										</td>
										<td>
											<div class="text-sm space-y-1">
												<div class="flex items-center gap-2">
													<Icon icon="mdi:memory" class="w-4 h-4 opacity-60" />
													<span>{formatBytes(item.container.memory)}</span>
												</div>
												<div class="flex items-center gap-2">
													<Icon icon="mdi:harddisk" class="w-4 h-4 opacity-60" />
													<span>{formatBytes(item.container.disk)}</span>
												</div>
												<div class="flex items-center gap-2">
													<Icon icon="mdi:cpu-64-bit" class="w-4 h-4 opacity-60" />
													<span>{item.container.cpus} CPU{item.container.cpus !== 1 ? 's' : ''}</span>
												</div>
											</div>
										</td>
										<td>
											{#if item.selected}
												<select
													bind:value={item.suggested_type}
													class="select select-bordered select-sm w-full max-w-xs"
												>
													<option value="custom">Custom App</option>
													{#each catalogApps as app}
														<option value={app.id}>{app.name}</option>
													{/each}
												</select>
											{:else}
												<span class="text-sm opacity-40">—</span>
											{/if}
										</td>
										<td>
											{#if item.selected}
												<input
													type="number"
													bind:value={item.port_to_expose}
													min="1"
													max="65535"
													class="input input-bordered input-sm w-24"
													placeholder="80"
												/>
											{:else}
												<span class="text-sm opacity-40">—</span>
											{/if}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- Action Bar -->
			<div class="card bg-base-200">
				<div class="card-body">
					<div class="flex items-center justify-between">
						<div>
							<p class="font-semibold">
								{selectedCount} container{selectedCount !== 1 ? 's' : ''} selected
							</p>
							{#if selectedCount > 0 && !allValid}
								<p class="text-sm text-warning">
									<Icon icon="mdi:alert" class="w-4 h-4 inline" />
									Please configure app type and port for all selected containers
								</p>
							{/if}
						</div>
						<button
							on:click={openConfirmModal}
							class="btn btn-primary gap-2"
							disabled={selectedCount === 0 || !allValid || adopting}
						>
							<Icon icon="mdi:check-circle" class="w-5 h-5" />
							Adopt Selected Containers
						</button>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<!-- Confirmation Modal -->
{#if showConfirmModal}
	<div class="modal modal-open">
		<div class="modal-box max-w-2xl">
			<h3 class="font-bold text-2xl mb-4">
				<Icon icon="mdi:check-circle" class="w-6 h-6 inline text-primary" />
				Confirm Container Adoption
			</h3>

			<div class="alert alert-warning mb-6">
				<Icon icon="mdi:alert" class="w-6 h-6" />
				<div class="text-sm">
					You are about to adopt <strong>{selectedCount}</strong> container{selectedCount !== 1
						? 's'
						: ''}. They will be imported into Proximity with their original configurations.
				</div>
			</div>

			<div class="space-y-3 mb-6 max-h-96 overflow-y-auto">
				{#each containers.filter((c) => c.selected) as item}
					<div class="card bg-base-200">
						<div class="card-body p-4">
							<div class="flex items-start justify-between gap-4">
								<div class="flex-1">
									<div class="font-bold">{item.container.name}</div>
									<div class="text-sm opacity-60">VMID {item.container.vmid}</div>
								</div>
								<div class="text-right text-sm">
									<div class="badge badge-sm badge-outline mb-1">{item.suggested_type}</div>
									<div class="opacity-60">Port: {item.port_to_expose}</div>
								</div>
							</div>
						</div>
					</div>
				{/each}
			</div>

			<div class="modal-action">
				<button class="btn btn-ghost" on:click={() => (showConfirmModal = false)}>
					Cancel
				</button>
				<button class="btn btn-primary gap-2" on:click={confirmAdoption}>
					<Icon icon="mdi:check" class="w-5 h-5" />
					Confirm Adoption
				</button>
			</div>
		</div>
		<div class="modal-backdrop" on:click={() => (showConfirmModal = false)}></div>
	</div>
{/if}

<!-- Adoption Progress Modal -->
{#if adopting}
	<div class="modal modal-open">
		<div class="modal-box">
			<h3 class="font-bold text-lg mb-4">Adopting Containers...</h3>
			<div class="space-y-4">
				<progress
					class="progress progress-primary w-full"
					value={adoptionProgress}
					max={adoptionTotal}
				></progress>
				<p class="text-center text-sm">
					Processing {adoptionProgress} of {adoptionTotal} containers
				</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.animate-spin {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}
</style>
