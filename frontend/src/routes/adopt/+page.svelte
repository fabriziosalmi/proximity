<script lang="ts">
	/**
	 * Adoption Wizard - Multi-Step Container Adoption Interface
	 * Guides users through discovering, configuring, and adopting existing LXC containers
	 */
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { toasts } from '$lib/stores/toast';
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

	// Wizard state
	type WizardStep = 'discovery' | 'configuration' | 'confirmation';
	let currentStep: WizardStep = 'discovery';

	// Data
	let loading = true;
	let containers: ContainerSelection[] = [];
	let catalogApps: CatalogApp[] = [];
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
					port_to_expose: guessPortFromName(c.name)
				}));
			}

			// Load catalog for app type matching
			const catalogResponse = await api.getCatalogApps();
			if (catalogResponse.success && catalogResponse.data) {
				catalogApps = catalogResponse.data.applications || [];
			}
		} catch (error) {
			console.error('Failed to load data:', error);
			toasts.error('Failed to load containers');
		} finally {
			loading = false;
		}
	}

	// Smart port guessing based on container name
	function guessPortFromName(name: string): number {
		const nameLower = name.toLowerCase();
		if (nameLower.includes('nginx') || nameLower.includes('apache') || nameLower.includes('web')) return 80;
		if (nameLower.includes('postgres') || nameLower.includes('psql')) return 5432;
		if (nameLower.includes('mysql') || nameLower.includes('mariadb')) return 3306;
		if (nameLower.includes('redis')) return 6379;
		if (nameLower.includes('mongo')) return 27017;
		if (nameLower.includes('elastic')) return 9200;
		if (nameLower.includes('ghost')) return 2368;
		if (nameLower.includes('wordpress')) return 80;
		if (nameLower.includes('node')) return 3000;
		return 80; // Default fallback
	}

	function toggleSelection(index: number) {
		containers[index].selected = !containers[index].selected;
		containers = [...containers];
	}

	function selectAll() {
		const allSelected = containers.every((c) => c.selected);
		containers = containers.map((c) => ({ ...c, selected: !allSelected }));
	}

	$: selectedContainers = containers.filter((c) => c.selected);
	$: selectedCount = selectedContainers.length;
	$: allValid = selectedContainers.every((c) => c.suggested_type && c.port_to_expose > 0);

	// Wizard navigation
	function goToStep(step: WizardStep) {
		if (step === 'configuration' && selectedCount === 0) {
			toasts.warning('Please select at least one container');
			return;
		}
		if (step === 'confirmation' && !allValid) {
			toasts.warning('Please configure all selected containers');
			return;
		}
		currentStep = step;
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	async function confirmAdoption() {
		adopting = true;
		adoptionProgress = 0;
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
					toasts.success(`✅ "${item.container.name}" adoption started`);
				} else {
					toasts.error(`❌ Failed to adopt "${item.container.name}": ${response.error}`);
				}
			} catch (error) {
				toasts.error(`💥 Error adopting "${item.container.name}"`);
			}

			adoptionProgress++;
		}

		adopting = false;

		// Show completion message
		toasts.success(
			`🎉 Adoption complete! ${adoptionTotal} container(s) are being imported. Redirecting to apps...`
		);
		
		setTimeout(() => {
			goto('/apps');
		}, 2500);
	}

	// Formatting helpers
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

	// Get app icon from catalog
	function getAppIcon(appId: string): string {
		const app = catalogApps.find((a) => a.id === appId);
		return app?.icon || 'mdi:package-variant';
	}
</script>

<div class="min-h-screen bg-base-200">
	<!-- Header -->
	<div class="bg-base-100 border-b border-base-300">
		<div class="container mx-auto px-6 py-6">
			<div class="flex items-center gap-4 mb-6">
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
					<h1 class="text-4xl font-bold mb-2 flex items-center gap-3">
						<Icon icon="mdi:download-circle" class="w-10 h-10 text-primary" />
						Adoption Wizard
					</h1>
					<p class="text-base-content/70">
						Import existing LXC containers into Proximity management while preserving their configuration
					</p>
				</div>

				{#if !loading && containers.length > 0}
					<button
						on:click={loadData}
						class="btn btn-outline gap-2"
						disabled={loading}
					>
						<Icon icon="mdi:refresh" class={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
						Refresh
					</button>
				{/if}
			</div>

			<!-- Step Indicator -->
			{#if !loading && containers.length > 0}
				<div class="mt-8">
					<ul class="steps steps-horizontal w-full">
						<li class="step" class:step-primary={currentStep === 'discovery'} data-content={currentStep === 'discovery' ? '●' : '✓'}>
							<span class="text-sm font-medium">Discovery</span>
						</li>
						<li class="step" class:step-primary={currentStep === 'configuration'} data-content={currentStep === 'confirmation' ? '✓' : (currentStep === 'configuration' ? '●' : '')}>
							<span class="text-sm font-medium">Configuration</span>
						</li>
						<li class="step" class:step-primary={currentStep === 'confirmation'} data-content={currentStep === 'confirmation' ? '●' : ''}>
							<span class="text-sm font-medium">Confirmation</span>
						</li>
					</ul>
				</div>
			{/if}
		</div>
	</div>

	<!-- Main Content -->
	<div class="container mx-auto px-6 py-8">
		{#if loading}
			<!-- Loading State -->
			<div class="card bg-base-100 shadow-xl">
				<div class="card-body items-center py-16">
					<Icon icon="mdi:loading" class="w-16 h-16 animate-spin text-primary mb-4" />
					<h2 class="text-2xl font-bold mb-2">Scanning Proxmox Nodes...</h2>
					<p class="text-base-content/70">
						Discovering unmanaged LXC containers across your infrastructure
					</p>
				</div>
			</div>
		{:else if containers.length === 0}
			<!-- Empty State -->
			<div class="card bg-base-100 shadow-xl">
				<div class="card-body items-center py-20">
					<Icon icon="mdi:check-decagram" class="w-32 h-32 text-success/30 mb-6" />
					<h2 class="text-3xl font-bold mb-3">All Containers Managed!</h2>
					<p class="text-base-content/70 mb-8 max-w-lg text-center text-lg">
						Great news! All containers on your Proxmox nodes are already managed by Proximity, 
						or there are no containers to discover.
					</p>
					<div class="flex gap-4">
						<button on:click={loadData} class="btn btn-primary gap-2">
							<Icon icon="mdi:refresh" class="w-5 h-5" />
							Refresh Discovery
						</button>
						<button on:click={() => goto('/apps')} class="btn btn-outline gap-2">
							<Icon icon="mdi:apps" class="w-5 h-5" />
							Go to Apps
						</button>
					</div>
				</div>
			</div>
		{:else}
			<!-- Step 1: Discovery -->
			{#if currentStep === 'discovery'}
				<div class="space-y-6">
					<!-- Discovery Summary -->
					<div class="alert alert-info shadow-lg">
						<Icon icon="mdi:radar" class="w-6 h-6" />
						<div class="flex-1">
							<h3 class="font-bold text-lg">Discovery Complete!</h3>
							<div class="text-sm mt-1">
								Found <span class="font-bold text-primary">{containers.length}</span> unmanaged container{containers.length !== 1 ? 's' : ''} ready for adoption.
								{#if selectedCount > 0}
									<span class="ml-2 text-primary font-semibold">{selectedCount} selected</span>
								{:else}
									Select containers below to begin.
								{/if}
							</div>
						</div>
					</div>

					<!-- Containers Table -->
					<div class="card bg-base-100 shadow-xl">
						<div class="card-body p-0">
							<div class="p-6 border-b border-base-300">
								<div class="flex items-center justify-between">
									<h3 class="text-xl font-bold">Available Containers</h3>
									<button
										on:click={selectAll}
										class="btn btn-sm btn-ghost gap-2"
									>
										<Icon icon="mdi:checkbox-multiple-marked" class="w-4 h-4" />
										{containers.every((c) => c.selected) ? 'Deselect All' : 'Select All'}
									</button>
								</div>
							</div>

							<div class="overflow-x-auto">
								<table class="table table-zebra">
									<thead>
										<tr>
											<th class="w-12">
												<input
													type="checkbox"
													class="checkbox checkbox-sm"
													checked={containers.every((c) => c.selected)}
													on:change={selectAll}
												/>
											</th>
											<th>Container</th>
											<th>Status</th>
											<th>Node</th>
											<th>Resources</th>
										</tr>
									</thead>
									<tbody>
										{#each containers as item, index}
											<tr 
												class="hover transition-colors"
												class:bg-primary={item.selected}
												class:bg-opacity-5={item.selected}
											>
												<td>
													<input
														type="checkbox"
														class="checkbox checkbox-primary"
														bind:checked={item.selected}
														on:change={() => toggleSelection(index)}
													/>
												</td>
												<td>
													<div class="flex items-center gap-3">
														<div class="avatar placeholder">
															<div class="bg-neutral text-neutral-content w-10 h-10 rounded-lg">
																<Icon icon="mdi:container" class="w-6 h-6" />
															</div>
														</div>
														<div>
															<div class="font-bold">{item.container.name}</div>
															<div class="text-xs opacity-60">VMID {item.container.vmid}</div>
														</div>
													</div>
												</td>
												<td>
													<div class="flex flex-col gap-1">
														<div class="badge badge-sm"
															class:badge-success={item.container.status === 'running'}
															class:badge-error={item.container.status === 'stopped'}
														>
															<Icon 
																icon={item.container.status === 'running' ? 'mdi:play-circle' : 'mdi:stop-circle'} 
																class="w-3 h-3 mr-1"
															/>
															{item.container.status}
														</div>
														{#if item.container.uptime > 0}
															<div class="text-xs opacity-60 flex items-center gap-1">
																<Icon icon="mdi:clock" class="w-3 h-3" />
																{formatUptime(item.container.uptime)}
															</div>
														{/if}
													</div>
												</td>
												<td>
													<div class="badge badge-outline">{item.container.node}</div>
												</td>
												<td>
													<div class="text-sm space-y-1">
														<div class="flex items-center gap-2 opacity-70">
															<Icon icon="mdi:cpu-64-bit" class="w-4 h-4" />
															<span>{item.container.cpus} CPU{item.container.cpus !== 1 ? 's' : ''}</span>
														</div>
														<div class="flex items-center gap-2 opacity-70">
															<Icon icon="mdi:memory" class="w-4 h-4" />
															<span>{formatBytes(item.container.memory)}</span>
														</div>
														<div class="flex items-center gap-2 opacity-70">
															<Icon icon="mdi:harddisk" class="w-4 h-4" />
															<span>{formatBytes(item.container.disk)}</span>
														</div>
													</div>
												</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</div>
					</div>

					<!-- Navigation -->
					<div class="card bg-base-100 shadow-xl">
						<div class="card-body">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-lg font-semibold">
										{selectedCount} container{selectedCount !== 1 ? 's' : ''} selected
									</p>
									<p class="text-sm text-base-content/70">
										Select containers to continue to configuration
									</p>
								</div>
								<button
									on:click={() => goToStep('configuration')}
									class="btn btn-primary gap-2"
									disabled={selectedCount === 0}
								>
									Continue to Configuration
									<Icon icon="mdi:arrow-right" class="w-5 h-5" />
								</button>
							</div>
						</div>
					</div>
				</div>
			{/if}

			<!-- Step 2: Configuration -->
			{#if currentStep === 'configuration'}
				<div class="space-y-6">
					<!-- Configuration Guide -->
					<div class="alert alert-info shadow-lg">
						<Icon icon="mdi:cog" class="w-6 h-6" />
						<div class="flex-1">
							<h3 class="font-bold text-lg">Configure Selected Containers</h3>
							<div class="text-sm mt-1">
								Match each container to an application type and specify the primary port it listens on.
							</div>
						</div>
					</div>

					<!-- Configuration Cards -->
					<div class="grid gap-6 md:grid-cols-2">
						{#each selectedContainers as item}
							<div class="card bg-base-100 shadow-xl border border-primary/20">
								<div class="card-body">
									<div class="flex items-start justify-between mb-4">
										<div class="flex items-center gap-3">
											<div class="avatar placeholder">
												<div class="bg-primary/10 text-primary w-12 h-12 rounded-lg">
													<Icon icon={getAppIcon(item.suggested_type)} class="w-7 h-7" />
												</div>
											</div>
											<div>
												<h3 class="font-bold text-lg">{item.container.name}</h3>
												<p class="text-xs opacity-60">VMID {item.container.vmid} • {item.container.node}</p>
											</div>
										</div>
										<div class="badge badge-sm"
											class:badge-success={item.container.status === 'running'}
											class:badge-error={item.container.status === 'stopped'}
										>
											{item.container.status}
										</div>
									</div>

									<div class="space-y-4">
										<!-- App Type Selection -->
										<div class="form-control">
											<label class="label">
												<span class="label-text font-semibold">Application Type</span>
												<span class="label-text-alt opacity-60">What is this container?</span>
											</label>
											<select
												bind:value={item.suggested_type}
												class="select select-bordered select-primary w-full"
											>
												<option value="custom">🔧 Custom Application</option>
												{#each catalogApps as app}
													<option value={app.id}>{app.name}</option>
												{/each}
											</select>
										</div>

										<!-- Port Configuration -->
										<div class="form-control">
											<label class="label">
												<span class="label-text font-semibold">Container Port</span>
												<span class="label-text-alt opacity-60">Main listening port</span>
											</label>
											<input
												type="number"
												bind:value={item.port_to_expose}
												min="1"
												max="65535"
												placeholder="80"
												class="input input-bordered input-primary w-full"
											/>
											<label class="label">
												<span class="label-text-alt opacity-60">
													<Icon icon="mdi:information" class="w-3 h-3 inline" />
													Port where the application listens inside the container
												</span>
											</label>
										</div>
									</div>
								</div>
							</div>
						{/each}
					</div>

					<!-- Navigation -->
					<div class="card bg-base-100 shadow-xl">
						<div class="card-body">
							<div class="flex items-center justify-between">
								<button
									on:click={() => goToStep('discovery')}
									class="btn btn-ghost gap-2"
								>
									<Icon icon="mdi:arrow-left" class="w-5 h-5" />
									Back to Discovery
								</button>
								<div class="flex gap-3">
									{#if !allValid}
										<div class="alert alert-warning py-2 px-4">
											<Icon icon="mdi:alert" class="w-4 h-4" />
											<span class="text-sm">Please configure all containers</span>
										</div>
									{/if}
									<button
										on:click={() => goToStep('confirmation')}
										class="btn btn-primary gap-2"
										disabled={!allValid}
									>
										Review & Confirm
										<Icon icon="mdi:arrow-right" class="w-5 h-5" />
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/if}

			<!-- Step 3: Confirmation -->
			{#if currentStep === 'confirmation'}
				<div class="space-y-6">
					<!-- Confirmation Alert -->
					<div class="alert alert-warning shadow-lg">
						<Icon icon="mdi:alert-circle" class="w-6 h-6" />
						<div class="flex-1">
							<h3 class="font-bold text-lg">Ready to Adopt</h3>
							<div class="text-sm mt-1">
								You are about to adopt <span class="font-bold">{selectedCount}</span> container{selectedCount !== 1 ? 's' : ''}.
								They will be imported with their original configurations.
							</div>
						</div>
					</div>

					<!-- Summary Cards -->
					<div class="grid gap-4">
						{#each selectedContainers as item}
							<div class="card bg-base-100 shadow-xl border border-success/20">
								<div class="card-body p-6">
									<div class="flex items-center gap-4">
										<div class="avatar placeholder">
											<div class="bg-success/10 text-success w-14 h-14 rounded-lg">
												<Icon icon={getAppIcon(item.suggested_type)} class="w-8 h-8" />
											</div>
										</div>
										
										<div class="flex-1">
											<h3 class="font-bold text-xl mb-1">{item.container.name}</h3>
											<div class="flex flex-wrap gap-3 text-sm text-base-content/70">
												<span class="flex items-center gap-1">
													<Icon icon="mdi:identifier" class="w-4 h-4" />
													VMID {item.container.vmid}
												</span>
												<span class="flex items-center gap-1">
													<Icon icon="mdi:server" class="w-4 h-4" />
													{item.container.node}
												</span>
												<span class="flex items-center gap-1">
													<Icon icon="mdi:application" class="w-4 h-4" />
													{catalogApps.find(a => a.id === item.suggested_type)?.name || 'Custom'}
												</span>
												<span class="flex items-center gap-1">
													<Icon icon="mdi:ethernet" class="w-4 h-4" />
													Port {item.port_to_expose}
												</span>
											</div>
										</div>

										<div class="flex flex-col items-end gap-2">
											<div class="badge badge-success gap-2">
												<Icon icon="mdi:check-circle" class="w-4 h-4" />
												Ready
											</div>
											<div class="badge badge-outline badge-sm">
												{item.container.status}
											</div>
										</div>
									</div>
								</div>
							</div>
						{/each}
					</div>

					<!-- Final Actions -->
					<div class="card bg-base-100 shadow-xl">
						<div class="card-body">
							<div class="flex items-center justify-between">
								<button
									on:click={() => goToStep('configuration')}
									class="btn btn-ghost gap-2"
								>
									<Icon icon="mdi:arrow-left" class="w-5 h-5" />
									Back to Configuration
								</button>
								<button
									on:click={confirmAdoption}
									class="btn btn-success btn-lg gap-3"
									disabled={adopting}
								>
									{#if adopting}
										<Icon icon="mdi:loading" class="w-6 h-6 animate-spin" />
										Adopting...
									{:else}
										<Icon icon="mdi:check-decagram" class="w-6 h-6" />
										Confirm & Adopt {selectedCount} Container{selectedCount !== 1 ? 's' : ''}
									{/if}
								</button>
							</div>
						</div>
					</div>
				</div>
			{/if}
		{/if}
	</div>
</div>

<!-- Adoption Progress Modal -->
{#if adopting}
	<div class="modal modal-open">
		<div class="modal-box max-w-lg">
			<h3 class="font-bold text-2xl mb-6 flex items-center gap-3">
				<Icon icon="mdi:download-circle" class="w-8 h-8 text-primary animate-pulse" />
				Adopting Containers...
			</h3>
			
			<div class="space-y-6">
				<progress
					class="progress progress-primary w-full h-4"
					value={adoptionProgress}
					max={adoptionTotal}
				></progress>
				
				<div class="text-center">
					<p class="text-3xl font-bold text-primary mb-2">
						{adoptionProgress} / {adoptionTotal}
					</p>
					<p class="text-sm text-base-content/70">
						Processing containers and importing into Proximity...
					</p>
				</div>

				<div class="alert alert-info">
					<Icon icon="mdi:information" class="w-5 h-5" />
					<span class="text-sm">
						This process runs in the background. You'll be redirected to the apps page shortly.
					</span>
				</div>
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

	.animate-pulse {
		animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
	}

	@keyframes pulse {
		0%, 100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}
</style>
