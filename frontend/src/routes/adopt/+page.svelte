<script lang="ts"><script lang="ts">

	/**	/**

	 * ENHANCED ADOPTION WIZARD - Genesis Release Premium Experience	 * ENHANCED ADOPTION WIZARD - Genesis Release Premium Experience

	 * 	 * 

	 * A comprehensive, multi-step interface for adopting existing LXC containers.	 * A comprehensive, multi-step interface for adopting existing LXC containers.

	 * Features intelligent port guessing, visual step indicators, and delightful UX.	 * Features intelligent port guessing, visual step indicators, and delightful UX.

	 * 	 * 

	 * Philosophy: "Tranquillità by Default" - Guide users through every decision with clarity.	 * Philosophy: "Tranquillità by Default" - Guide users through every decision with clarity.

	 */	 */

	import { onMount } from 'svelte';	import { onMount } from 'svelte';

	import { goto } from '$app/navigation';	import { goto } from '$app/navigation';

	import { api } from '$lib/api';	import { api } from '$lib/api';

	import { addToast } from '$lib/stores/toastStore';	import { addToast } from '$lib/stores/toastStore';

	import Icon from '@iconify/svelte';	import Icon from '@iconify/svelte';



	interface UnmanagedContainer {	interface UnmanagedContainer {

		vmid: number;		vmid: number;

		name: string;		name: string;

		status: string;		status: string;

		node: string;		node: string;

		memory: number;		memory: number;

		disk: number;		disk: number;

		uptime: number;		uptime: number;

		cpus: number;		cpus: number;

	}	}



	interface ContainerSelection {	interface ContainerSelection {

		container: UnmanagedContainer;		container: UnmanagedContainer;

		selected: boolean;		selected: boolean;

		suggested_type: string;		suggested_type: string;

		port_to_expose: number;		port_to_expose: number;

	}	}



	interface CatalogApp {	interface CatalogApp {

		id: string;		id: string;

		name: string;		name: string;

		icon: string;		icon: string;

		ports: number[];		ports: number[];

	}	}



	// Wizard Steps	// Wizard Steps

	type WizardStep = 'discovery' | 'configuration' | 'confirmation';	type WizardStep = 'discovery' | 'configuration' | 'confirmation';

	let currentStep: WizardStep = 'discovery';	let currentStep: WizardStep = 'discovery';



	// Data State	// Data State

	let loading = true;	let loading = true;

	let containers: ContainerSelection[] = [];	let containers: ContainerSelection[] = [];

	let catalogApps: CatalogApp[] = [];	let catalogApps: CatalogApp[] = [];

	let adopting = false;	let adopting = false;

	let adoptionProgress = 0;	let adoptionProgress = 0;

	let adoptionTotal = 0;	let adoptionTotal = 0;



	onMount(async () => {	onMount(async () => {

		await loadData();		await loadData();

	});	});



	async function loadData() {	async function loadData() {

		loading = true;		loading = true;



		try {		try {

			// Load unmanaged containers			// Load unmanaged containers

			const containersResponse = await api.discoverUnmanagedContainers();			const containersResponse = await api.discoverUnmanagedContainers();

			if (containersResponse.success && containersResponse.data) {			if (containersResponse.success && containersResponse.data) {

				containers = (containersResponse.data as UnmanagedContainer[]).map((c) => ({				containers = (containersResponse.data as UnmanagedContainer[]).map((c) => ({

					container: c,					container: c,

					selected: false,					selected: false,

					suggested_type: 'custom',					suggested_type: 'custom',

					port_to_expose: guessPortFromName(c.name) // 🎯 SMART PORT GUESSING					port_to_expose: guessPortFromName(c.name) // 🎯 SMART PORT GUESSING

				}));				}));

			}			}



			// Load catalog for app type matching			// Load catalog for app type matching

			const catalogResponse = await api.getCatalog();			const catalogResponse = await api.getCatalog();

			if (catalogResponse.success && catalogResponse.data) {			if (catalogResponse.success && catalogResponse.data) {

				catalogApps = catalogResponse.data.applications || [];				catalogApps = catalogResponse.data.applications || [];

			}			}

		} catch (error) {		} catch (error) {

			console.error('Failed to load data:', error);			console.error('Failed to load data:', error);

			addToast('Failed to load containers', 'error');			addToast('Failed to load containers', 'error');

		} finally {		} finally {

			loading = false;			loading = false;

		}		}

	}	}



	/**	/**

	 * 🧠 SMART PORT GUESSING	 * 🧠 SMART PORT GUESSING

	 * Intelligently suggests default ports based on container naming patterns.	 * Intelligently suggests default ports based on container naming patterns.

	 * Reduces user friction while maintaining full control.	 * Reduces user friction while maintaining full control.

	 */	 */

	function guessPortFromName(name: string): number {	function guessPortFromName(name: string): number {

		const nameLower = name.toLowerCase();		const nameLower = name.toLowerCase();

				

		// Web Servers		// Web Servers

		if (nameLower.includes('nginx') || nameLower.includes('apache') || nameLower.includes('caddy')) return 80;		if (nameLower.includes('nginx') || nameLower.includes('apache') || nameLower.includes('caddy')) return 80;

		if (nameLower.includes('traefik')) return 8080;		if (nameLower.includes('traefik')) return 8080;

				

		// Databases		// Databases

		if (nameLower.includes('postgres') || nameLower.includes('psql') || nameLower.includes('pg')) return 5432;		if (nameLower.includes('postgres') || nameLower.includes('psql') || nameLower.includes('pg')) return 5432;

		if (nameLower.includes('mysql') || nameLower.includes('mariadb')) return 3306;		if (nameLower.includes('mysql') || nameLower.includes('mariadb')) return 3306;

		if (nameLower.includes('mongo')) return 27017;		if (nameLower.includes('mongo')) return 27017;

		if (nameLower.includes('redis')) return 6379;		if (nameLower.includes('redis')) return 6379;

		if (nameLower.includes('elastic') || nameLower.includes('elasticsearch')) return 9200;		if (nameLower.includes('elastic') || nameLower.includes('elasticsearch')) return 9200;

		if (nameLower.includes('cassandra')) return 9042;		if (nameLower.includes('cassandra')) return 9042;

				

		// Application Frameworks		// Application Frameworks

		if (nameLower.includes('node') || nameLower.includes('express')) return 3000;		if (nameLower.includes('node') || nameLower.includes('express')) return 3000;

		if (nameLower.includes('django') || nameLower.includes('flask')) return 8000;		if (nameLower.includes('django') || nameLower.includes('flask')) return 8000;

		if (nameLower.includes('rails') || nameLower.includes('ruby')) return 3000;		if (nameLower.includes('rails') || nameLower.includes('ruby')) return 3000;

		if (nameLower.includes('spring') || nameLower.includes('tomcat')) return 8080;		if (nameLower.includes('spring') || nameLower.includes('tomcat')) return 8080;

				

		// CMS & Applications		// CMS & Applications

		if (nameLower.includes('wordpress')) return 80;		if (nameLower.includes('wordpress')) return 80;

		if (nameLower.includes('ghost')) return 2368;		if (nameLower.includes('ghost')) return 2368;

		if (nameLower.includes('nextcloud')) return 80;		if (nameLower.includes('nextcloud')) return 80;

		if (nameLower.includes('jellyfin')) return 8096;		if (nameLower.includes('jellyfin')) return 8096;

		if (nameLower.includes('plex')) return 32400;		if (nameLower.includes('plex')) return 32400;

		if (nameLower.includes('portainer')) return 9000;		if (nameLower.includes('portainer')) return 9000;

		if (nameLower.includes('grafana')) return 3000;		if (nameLower.includes('grafana')) return 3000;

		if (nameLower.includes('prometheus')) return 9090;		if (nameLower.includes('prometheus')) return 9090;

				

		// Default fallback		// Default fallback

		return 80;		return 80;

	}	}



	function toggleSelection(index: number) {	function toggleSelection(index: number) {

		containers[index].selected = !containers[index].selected;		containers[index].selected = !containers[index].selected;

		containers = [...containers];		containers = [...containers]; // Trigger reactivity

	}	}



	function selectAll() {	function selectAll() {

		const allSelected = containers.every((c) => c.selected);		const allSelected = containers.every((c) => c.selected);

		containers = containers.map((c) => ({ ...c, selected: !allSelected }));		containers = containers.map((c) => ({ ...c, selected: !allSelected }));

	}	}



	$: selectedContainers = containers.filter((c) => c.selected);	$: selectedCount = containers.filter((c) => c.selected).length;

	$: selectedCount = selectedContainers.length;	$: allValid = containers

	$: allValid = selectedContainers.every((c) => c.suggested_type && c.port_to_expose > 0 && c.port_to_expose <= 65535);		.filter((c) => c.selected)

		.every((c) => c.suggested_type && c.port_to_expose > 0);

	/**

	 * WIZARD NAVIGATION	function openConfirmModal() {

	 * Smooth transitions between steps with validation		if (selectedCount === 0) {

	 */			addToast('Please select at least one container', 'warning');

	function goToStep(step: WizardStep) {			return;

		if (step === 'configuration' && selectedCount === 0) {		}

			addToast('Please select at least one container', 'warning');		if (!allValid) {

			return;			addToast('Please configure all selected containers', 'warning');

		}			return;

		if (step === 'confirmation' && !allValid) {		}

			addToast('Please configure all selected containers correctly', 'warning');		showConfirmModal = true;

			return;	}

		}

		currentStep = step;	async function confirmAdoption() {

		window.scrollTo({ top: 0, behavior: 'smooth' });		showConfirmModal = false;

	}		adopting = true;

		adoptionProgress = 0;

	/**

	 * ADOPTION EXECUTION		const selectedContainers = containers.filter((c) => c.selected);

	 * Process all selected containers with progress tracking		adoptionTotal = selectedContainers.length;

	 */

	async function confirmAdoption() {		for (const item of selectedContainers) {

		adopting = true;			try {

		adoptionProgress = 0;				const response = await api.adoptContainer({

		adoptionTotal = selectedContainers.length;					vmid: item.container.vmid,

					node_name: item.container.node,

		for (const item of selectedContainers) {					suggested_type: item.suggested_type,

			try {					port_to_expose: item.port_to_expose

				const response = await api.adoptContainer({				});

					vmid: item.container.vmid,

					node_name: item.container.node,				if (response.success) {

					suggested_type: item.suggested_type,					addToast(

					port_to_expose: item.port_to_expose						`Container "${item.container.name}" adoption started`,

				});						'success'

					);

				if (response.success) {				} else {

					addToast(`✅ "${item.container.name}" adoption started`, 'success');					addToast(

				} else {						`Failed to adopt "${item.container.name}": ${response.error}`,

					addToast(`❌ Failed to adopt "${item.container.name}": ${response.error}`, 'error');						'error'

				}					);

			} catch (error) {				}

				addToast(`💥 Error adopting "${item.container.name}"`, 'error');			} catch (error) {

			}				addToast(`Error adopting "${item.container.name}"`, 'error');

			}

			adoptionProgress++;

		}			adoptionProgress++;

		}

		adopting = false;

		adopting = false;

		// Completion message and redirect

		addToast(		// Redirect to apps page after a short delay

			`🎉 Adoption complete! ${adoptionTotal} container(s) are being imported. Redirecting...`,		addToast(

			'success'			`Adoption process started for ${adoptionTotal} container(s). Check /apps page for status.`,

		);			'info'

				);

		setTimeout(() => {		setTimeout(() => {

			goto('/apps');			goto('/apps');

		}, 2500);		}, 2000);

	}	}



	/**	function formatBytes(bytes: number): string {

	 * FORMATTING UTILITIES		if (bytes === 0) return '0 B';

	 */		const k = 1024;

	function formatBytes(bytes: number): string {		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];

		if (bytes === 0) return '0 B';		const i = Math.floor(Math.log(bytes) / Math.log(k));

		const k = 1024;		return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];

		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];	}

		const i = Math.floor(Math.log(bytes) / Math.log(k));

		return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];	function formatUptime(seconds: number): string {

	}		const days = Math.floor(seconds / 86400);

		const hours = Math.floor((seconds % 86400) / 3600);

	function formatUptime(seconds: number): string {		const minutes = Math.floor((seconds % 3600) / 60);

		const days = Math.floor(seconds / 86400);

		const hours = Math.floor((seconds % 86400) / 3600);		if (days > 0) return `${days}d ${hours}h`;

		const minutes = Math.floor((seconds % 3600) / 60);		if (hours > 0) return `${hours}h ${minutes}m`;

		return `${minutes}m`;

		if (days > 0) return `${days}d ${hours}h`;	}

		if (hours > 0) return `${hours}h ${minutes}m`;</script>

		return `${minutes}m`;

	}<div class="container mx-auto px-4 py-8 max-w-7xl">

	<!-- Header -->

	function getAppIcon(appId: string): string {	<div class="mb-8">

		const app = catalogApps.find((a) => a.id === appId);		<div class="flex items-center gap-4 mb-4">

		return app?.icon || 'mdi:package-variant';			<button

	}				on:click={() => goto('/apps')}

				class="btn btn-ghost btn-sm gap-2"

	function getAppName(appId: string): string {			>

		const app = catalogApps.find((a) => a.id === appId);				<Icon icon="mdi:arrow-left" class="w-5 h-5" />

		return app?.name || 'Custom Application';				Back to Apps

	}			</button>

</script>		</div>



<div class="min-h-screen bg-base-200">		<div class="flex items-center justify-between">

	<!-- ========== HEADER ========== -->			<div>

	<div class="bg-base-100 border-b border-base-300">				<h1 class="text-4xl font-bold mb-2">Adopt Existing Containers</h1>

		<div class="container mx-auto px-6 py-6">				<p class="text-base-content/70">

			<div class="flex items-center gap-4 mb-6">					Import existing LXC containers into Proximity management. Containers will keep their

				<button					original configuration and hostname.

					on:click={() => goto('/apps')}				</p>

					class="btn btn-ghost btn-sm gap-2"			</div>

				>

					<Icon icon="mdi:arrow-left" class="w-5 h-5" />			<button

					Back to Apps				on:click={loadData}

				</button>				class="btn btn-outline gap-2"

			</div>				disabled={loading}

			>

			<div class="flex items-center justify-between">				<Icon icon="mdi:refresh" class="w-5 h-5" class:animate-spin={loading} />

				<div>				Refresh

					<h1 class="text-4xl font-bold mb-2 flex items-center gap-3">			</button>

						<Icon icon="mdi:download-circle" class="w-10 h-10 text-primary" />		</div>

						Adoption Wizard	</div>

					</h1>

					<p class="text-base-content/70">	{#if loading}

						Import existing LXC containers into Proximity while preserving their configuration		<!-- Loading State -->

					</p>		<div class="space-y-4">

				</div>			{#each Array(3) as _}

				<div class="skeleton h-20 w-full"></div>

				{#if !loading && containers.length > 0}			{/each}

					<button		</div>

						on:click={loadData}	{:else if containers.length === 0}

						class="btn btn-outline gap-2"		<!-- Empty State -->

						disabled={loading}		<div class="card bg-base-200">

					>			<div class="card-body items-center text-center py-16">

						<Icon icon="mdi:refresh" class="w-5 h-5" class:animate-spin={loading} />				<Icon icon="mdi:inbox" class="w-24 h-24 text-base-content/30 mb-4" />

						Refresh				<h2 class="text-2xl font-bold mb-2">No Unmanaged Containers Found</h2>

					</button>				<p class="text-base-content/70 mb-6 max-w-md">

				{/if}					All containers on your Proxmox nodes are already managed by Proximity, or there are no

			</div>					containers to discover.

				</p>

			<!-- ========== STEP INDICATOR ========== -->				<div class="flex gap-3">

			{#if !loading && containers.length > 0}					<button on:click={loadData} class="btn btn-primary gap-2">

				<div class="mt-8">						<Icon icon="mdi:refresh" class="w-5 h-5" />

					<ul class="steps steps-horizontal w-full">						Refresh Discovery

						<li 					</button>

							class="step" 					<button on:click={() => goto('/apps')} class="btn btn-outline">

							class:step-primary={currentStep === 'discovery'} 						Go to Apps

							data-content={currentStep !== 'discovery' ? '✓' : '●'}					</button>

						>				</div>

							<span class="text-sm font-medium">Discovery</span>			</div>

						</li>		</div>

						<li 	{:else}

							class="step" 		<!-- Main Content -->

							class:step-primary={currentStep === 'configuration' || currentStep === 'confirmation'} 		<div class="space-y-6">

							data-content={currentStep === 'confirmation' ? '✓' : (currentStep === 'configuration' ? '●' : '')}			<!-- Selection Summary -->

						>			<div class="alert alert-info">

							<span class="text-sm font-medium">Configuration</span>				<Icon icon="mdi:information" class="w-6 h-6" />

						</li>				<div class="flex-1">

						<li 					<h3 class="font-bold">Discovery Complete</h3>

							class="step" 					<div class="text-sm">

							class:step-primary={currentStep === 'confirmation'} 						Found {containers.length} unmanaged container{containers.length !== 1 ? 's' : ''}.

							data-content={currentStep === 'confirmation' ? '●' : ''}						{#if selectedCount > 0}

						>							<span class="font-semibold">{selectedCount} selected</span> for adoption.

							<span class="text-sm font-medium">Confirmation</span>						{:else}

						</li>							Select containers below to begin adoption.

					</ul>						{/if}

				</div>					</div>

			{/if}				</div>

		</div>			</div>

	</div>

			<!-- Containers Table -->

	<!-- ========== MAIN CONTENT ========== -->			<div class="card bg-base-100 shadow-xl">

	<div class="container mx-auto px-6 py-8">				<div class="card-body p-0">

		{#if loading}					<div class="overflow-x-auto">

			<!-- Loading State -->						<table class="table table-zebra">

			<div class="card bg-base-100 shadow-xl">							<thead>

				<div class="card-body items-center py-16">								<tr>

					<Icon icon="mdi:loading" class="w-16 h-16 animate-spin text-primary mb-4" />									<th>

					<h2 class="text-2xl font-bold mb-2">Scanning Proxmox Nodes...</h2>										<label>

					<p class="text-base-content/70">											<input

						Discovering unmanaged LXC containers across your infrastructure												type="checkbox"

					</p>												class="checkbox checkbox-sm"

				</div>												checked={containers.every((c) => c.selected)}

			</div>												on:change={selectAll}

		{:else if containers.length === 0}											/>

			<!-- Empty State -->										</label>

			<div class="card bg-base-100 shadow-xl">									</th>

				<div class="card-body items-center py-20">									<th>Container</th>

					<Icon icon="mdi:check-decagram" class="w-32 h-32 text-success/30 mb-6" />									<th>Status</th>

					<h2 class="text-3xl font-bold mb-3">All Containers Managed!</h2>									<th>Resources</th>

					<p class="text-base-content/70 mb-8 max-w-lg text-center text-lg">									<th>App Type</th>

						Great news! All containers on your Proxmox nodes are already managed by Proximity.									<th>Port</th>

					</p>								</tr>

					<div class="flex gap-4">							</thead>

						<button on:click={loadData} class="btn btn-primary gap-2">							<tbody>

							<Icon icon="mdi:refresh" class="w-5 h-5" />								{#each containers as item, index}

							Refresh Discovery									<tr class:bg-primary/5={item.selected}>

						</button>										<td>

						<button on:click={() => goto('/apps')} class="btn btn-outline gap-2">											<label>

							<Icon icon="mdi:apps" class="w-5 h-5" />												<input

							Go to Apps													type="checkbox"

						</button>													class="checkbox checkbox-primary"

					</div>													bind:checked={item.selected}

				</div>													on:change={() => toggleSelection(index)}

			</div>												/>

		{:else}											</label>

			<!-- ========== STEP 1: DISCOVERY ========== -->										</td>

			{#if currentStep === 'discovery'}										<td>

				<div class="space-y-6">											<div class="flex flex-col">

					<!-- Discovery Summary -->												<div class="font-bold">{item.container.name}</div>

					<div class="alert alert-info shadow-lg">												<div class="text-sm opacity-60">

						<Icon icon="mdi:radar" class="w-6 h-6" />													VMID {item.container.vmid} · Node {item.container.node}

						<div class="flex-1">												</div>

							<h3 class="font-bold text-lg">Discovery Complete!</h3>											</div>

							<div class="text-sm mt-1">										</td>

								Found <span class="font-bold text-primary">{containers.length}</span> unmanaged container{containers.length !== 1 ? 's' : ''} ready for adoption.										<td>

								{#if selectedCount > 0}											<div class="badge badge-sm"

									<span class="ml-2 text-primary font-semibold">{selectedCount} selected</span>												class:badge-success={item.container.status === 'running'}

								{:else}												class:badge-error={item.container.status === 'stopped'}

									Select containers below to begin.											>

								{/if}												{item.container.status}

							</div>											</div>

						</div>											<div class="text-xs opacity-60 mt-1">

					</div>												{formatUptime(item.container.uptime)}

											</div>

					<!-- Containers Table -->										</td>

					<div class="card bg-base-100 shadow-xl">										<td>

						<div class="card-body p-0">											<div class="text-sm space-y-1">

							<div class="p-6 border-b border-base-300">												<div class="flex items-center gap-2">

								<div class="flex items-center justify-between">													<Icon icon="mdi:memory" class="w-4 h-4 opacity-60" />

									<h3 class="text-xl font-bold">Available Containers</h3>													<span>{formatBytes(item.container.memory)}</span>

									<button												</div>

										on:click={selectAll}												<div class="flex items-center gap-2">

										class="btn btn-sm btn-ghost gap-2"													<Icon icon="mdi:harddisk" class="w-4 h-4 opacity-60" />

									>													<span>{formatBytes(item.container.disk)}</span>

										<Icon icon="mdi:checkbox-multiple-marked" class="w-4 h-4" />												</div>

										{containers.every((c) => c.selected) ? 'Deselect All' : 'Select All'}												<div class="flex items-center gap-2">

									</button>													<Icon icon="mdi:cpu-64-bit" class="w-4 h-4 opacity-60" />

								</div>													<span>{item.container.cpus} CPU{item.container.cpus !== 1 ? 's' : ''}</span>

							</div>												</div>

											</div>

							<div class="overflow-x-auto">										</td>

								<table class="table table-zebra">										<td>

									<thead>											{#if item.selected}

										<tr>												<select

											<th class="w-12">													bind:value={item.suggested_type}

												<input													class="select select-bordered select-sm w-full max-w-xs"

													type="checkbox"												>

													class="checkbox checkbox-sm"													<option value="custom">Custom App</option>

													checked={containers.every((c) => c.selected)}													{#each catalogApps as app}

													on:change={selectAll}														<option value={app.id}>{app.name}</option>

												/>													{/each}

											</th>												</select>

											<th>Container</th>											{:else}

											<th>Status</th>												<span class="text-sm opacity-40">—</span>

											<th>Node</th>											{/if}

											<th>Resources</th>										</td>

										</tr>										<td>

									</thead>											{#if item.selected}

									<tbody>												<input

										{#each containers as item, index}													type="number"

											<tr 													bind:value={item.port_to_expose}

												class="hover transition-colors"													min="1"

												class:bg-primary={item.selected}													max="65535"

												class:bg-opacity-5={item.selected}													class="input input-bordered input-sm w-24"

											>													placeholder="80"

												<td>												/>

													<input											{:else}

														type="checkbox"												<span class="text-sm opacity-40">—</span>

														class="checkbox checkbox-primary"											{/if}

														bind:checked={item.selected}										</td>

														on:change={() => toggleSelection(index)}									</tr>

													/>								{/each}

												</td>							</tbody>

												<td>						</table>

													<div class="flex items-center gap-3">					</div>

														<div class="avatar placeholder">				</div>

															<div class="bg-neutral text-neutral-content w-10 h-10 rounded-lg">			</div>

																<Icon icon="mdi:container" class="w-6 h-6" />

															</div>			<!-- Action Bar -->

														</div>			<div class="card bg-base-200">

														<div>				<div class="card-body">

															<div class="font-bold">{item.container.name}</div>					<div class="flex items-center justify-between">

															<div class="text-xs opacity-60">VMID {item.container.vmid}</div>						<div>

														</div>							<p class="font-semibold">

													</div>								{selectedCount} container{selectedCount !== 1 ? 's' : ''} selected

												</td>							</p>

												<td>							{#if selectedCount > 0 && !allValid}

													<div class="flex flex-col gap-1">								<p class="text-sm text-warning">

														<div 									<Icon icon="mdi:alert" class="w-4 h-4 inline" />

															class="badge badge-sm"									Please configure app type and port for all selected containers

															class:badge-success={item.container.status === 'running'}								</p>

															class:badge-error={item.container.status === 'stopped'}							{/if}

														>						</div>

															<Icon 						<button

																icon={item.container.status === 'running' ? 'mdi:play-circle' : 'mdi:stop-circle'} 							on:click={openConfirmModal}

																class="w-3 h-3 mr-1"							class="btn btn-primary gap-2"

															/>							disabled={selectedCount === 0 || !allValid || adopting}

															{item.container.status}						>

														</div>							<Icon icon="mdi:check-circle" class="w-5 h-5" />

														{#if item.container.uptime > 0}							Adopt Selected Containers

															<div class="text-xs opacity-60 flex items-center gap-1">						</button>

																<Icon icon="mdi:clock" class="w-3 h-3" />					</div>

																{formatUptime(item.container.uptime)}				</div>

															</div>			</div>

														{/if}		</div>

													</div>	{/if}

												</td></div>

												<td>

													<div class="badge badge-outline">{item.container.node}</div><!-- Confirmation Modal -->

												</td>{#if showConfirmModal}

												<td>	<div class="modal modal-open">

													<div class="text-sm space-y-1">		<div class="modal-box max-w-2xl">

														<div class="flex items-center gap-2 opacity-70">			<h3 class="font-bold text-2xl mb-4">

															<Icon icon="mdi:cpu-64-bit" class="w-4 h-4" />				<Icon icon="mdi:check-circle" class="w-6 h-6 inline text-primary" />

															<span>{item.container.cpus} CPU{item.container.cpus !== 1 ? 's' : ''}</span>				Confirm Container Adoption

														</div>			</h3>

														<div class="flex items-center gap-2 opacity-70">

															<Icon icon="mdi:memory" class="w-4 h-4" />			<div class="alert alert-warning mb-6">

															<span>{formatBytes(item.container.memory)}</span>				<Icon icon="mdi:alert" class="w-6 h-6" />

														</div>				<div class="text-sm">

														<div class="flex items-center gap-2 opacity-70">					You are about to adopt <strong>{selectedCount}</strong> container{selectedCount !== 1

															<Icon icon="mdi:harddisk" class="w-4 h-4" />						? 's'

															<span>{formatBytes(item.container.disk)}</span>						: ''}. They will be imported into Proximity with their original configurations.

														</div>				</div>

													</div>			</div>

												</td>

											</tr>			<div class="space-y-3 mb-6 max-h-96 overflow-y-auto">

										{/each}				{#each containers.filter((c) => c.selected) as item}

									</tbody>					<div class="card bg-base-200">

								</table>						<div class="card-body p-4">

							</div>							<div class="flex items-start justify-between gap-4">

						</div>								<div class="flex-1">

					</div>									<div class="font-bold">{item.container.name}</div>

									<div class="text-sm opacity-60">VMID {item.container.vmid}</div>

					<!-- Navigation -->								</div>

					<div class="card bg-base-100 shadow-xl">								<div class="text-right text-sm">

						<div class="card-body">									<div class="badge badge-sm badge-outline mb-1">{item.suggested_type}</div>

							<div class="flex items-center justify-between">									<div class="opacity-60">Port: {item.port_to_expose}</div>

								<div>								</div>

									<p class="text-lg font-semibold">							</div>

										{selectedCount} container{selectedCount !== 1 ? 's' : ''} selected						</div>

									</p>					</div>

									<p class="text-sm text-base-content/70">				{/each}

										Select containers to continue to configuration			</div>

									</p>

								</div>			<div class="modal-action">

								<button				<button class="btn btn-ghost" on:click={() => (showConfirmModal = false)}>

									on:click={() => goToStep('configuration')}					Cancel

									class="btn btn-primary gap-2"				</button>

									disabled={selectedCount === 0}				<button class="btn btn-primary gap-2" on:click={confirmAdoption}>

								>					<Icon icon="mdi:check" class="w-5 h-5" />

									Continue to Configuration					Confirm Adoption

									<Icon icon="mdi:arrow-right" class="w-5 h-5" />				</button>

								</button>			</div>

							</div>		</div>

						</div>		<div class="modal-backdrop" on:click={() => (showConfirmModal = false)}></div>

					</div>	</div>

				</div>{/if}

			{/if}

<!-- Adoption Progress Modal -->

			<!-- ========== STEP 2: CONFIGURATION ========== -->{#if adopting}

			{#if currentStep === 'configuration'}	<div class="modal modal-open">

				<div class="space-y-6">		<div class="modal-box">

					<!-- Configuration Guide -->			<h3 class="font-bold text-lg mb-4">Adopting Containers...</h3>

					<div class="alert alert-info shadow-lg">			<div class="space-y-4">

						<Icon icon="mdi:cog" class="w-6 h-6" />				<progress

						<div class="flex-1">					class="progress progress-primary w-full"

							<h3 class="font-bold text-lg">Configure Selected Containers</h3>					value={adoptionProgress}

							<div class="text-sm mt-1">					max={adoptionTotal}

								Match each container to an application type and specify the primary port. 				></progress>

								<span class="font-semibold text-primary">Smart port guessing has been applied!</span>				<p class="text-center text-sm">

							</div>					Processing {adoptionProgress} of {adoptionTotal} containers

						</div>				</p>

					</div>			</div>

		</div>

					<!-- Configuration Cards -->	</div>

					<div class="grid gap-6 md:grid-cols-2">{/if}

						{#each selectedContainers as item}

							<div class="card bg-base-100 shadow-xl border-2 border-primary/20 hover:border-primary/40 transition-colors"><style>

								<div class="card-body">	.animate-spin {

									<div class="flex items-start justify-between mb-4">		animation: spin 1s linear infinite;

										<div class="flex items-center gap-3">	}

											<div class="avatar placeholder">

												<div class="bg-primary/10 text-primary w-12 h-12 rounded-lg">	@keyframes spin {

													<Icon icon={getAppIcon(item.suggested_type)} class="w-7 h-7" />		from {

												</div>			transform: rotate(0deg);

											</div>		}

											<div>		to {

												<h3 class="font-bold text-lg">{item.container.name}</h3>			transform: rotate(360deg);

												<p class="text-xs opacity-60">VMID {item.container.vmid} • {item.container.node}</p>		}

											</div>	}

										</div></style>

										<div 
											class="badge badge-sm"
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
												<span class="label-text font-semibold flex items-center gap-2">
													<Icon icon="mdi:application" class="w-4 h-4" />
													Application Type
												</span>
												<span class="label-text-alt opacity-60">What is this?</span>
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
												<span class="label-text font-semibold flex items-center gap-2">
													<Icon icon="mdi:ethernet" class="w-4 h-4" />
													Container Port
												</span>
												<span class="label-text-alt opacity-60">Main service port</span>
											</label>
											<input
												type="number"
												bind:value={item.port_to_expose}
												min="1"
												max="65535"
												placeholder="80"
												class="input input-bordered input-primary w-full"
												class:input-error={item.port_to_expose < 1 || item.port_to_expose > 65535}
											/>
											<label class="label">
												<span class="label-text-alt opacity-60 flex items-center gap-1">
													<Icon icon="mdi:lightbulb" class="w-3 h-3" />
													{#if item.port_to_expose === guessPortFromName(item.container.name)}
														Smart guess applied based on container name
													{:else}
														Custom port (range: 1-65535)
													{/if}
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
								<div class="flex items-center gap-3">
									{#if !allValid}
										<div class="alert alert-warning py-2 px-4 shadow-lg">
											<Icon icon="mdi:alert" class="w-4 h-4" />
											<span class="text-sm">Please configure all containers correctly</span>
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

			<!-- ========== STEP 3: CONFIRMATION ========== -->
			{#if currentStep === 'confirmation'}
				<div class="space-y-6">
					<!-- Confirmation Alert -->
					<div class="alert alert-warning shadow-lg">
						<Icon icon="mdi:alert-circle" class="w-6 h-6" />
						<div class="flex-1">
							<h3 class="font-bold text-lg">Ready to Adopt</h3>
							<div class="text-sm mt-1">
								You are about to adopt <span class="font-bold">{selectedCount}</span> container{selectedCount !== 1 ? 's' : ''}.
								This action will import them into Proximity with their original configurations preserved.
								<span class="font-semibold block mt-2">This operation cannot be undone from Proximity.</span>
							</div>
						</div>
					</div>

					<!-- Summary Cards -->
					<div class="grid gap-4">
						{#each selectedContainers as item}
							<div class="card bg-base-100 shadow-xl border-2 border-success/30 hover:border-success/50 transition-colors">
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
													{getAppName(item.suggested_type)}
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
					<div class="card bg-base-100 shadow-xl border-2 border-primary/30">
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
									class="btn btn-success btn-lg gap-3 shadow-lg"
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

<!-- ========== ADOPTION PROGRESS MODAL ========== -->
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

	/* Smooth transitions for step navigation */
	.card,
	.alert,
	.btn {
		transition: all 0.2s ease-in-out;
	}

	/* Enhanced hover states */
	.card:hover {
		transform: translateY(-2px);
	}

	/* Focus states for accessibility */
	.btn:focus-visible,
	.input:focus-visible,
	.select:focus-visible {
		outline: 2px solid oklch(var(--p));
		outline-offset: 2px;
	}
</style>
