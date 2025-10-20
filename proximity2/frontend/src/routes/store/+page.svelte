<script lang="ts">
	/**
	 * App Store - Browse and deploy applications from the catalog
	 */
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { Search, Loader2, Package, RefreshCw, ShoppingBag, Layers, Grid } from 'lucide-svelte';
	import { api } from '$lib/api';
	import { myAppsStore } from '$lib/stores/apps';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import { toasts } from '$lib/stores/toast';
	import RackCard from '$lib/components/RackCard.svelte';
	import CategoryFilter from '$lib/components/CategoryFilter.svelte';
	import DeploymentModal from '$lib/components/DeploymentModal.svelte';
	import StatBlock from '$lib/components/dashboard/StatBlock.svelte';
	import NavigationRack from '$lib/components/layout/NavigationRack.svelte';
	import OperationalRack from '$lib/components/layout/OperationalRack.svelte';

	let catalogApps: any[] = [];
	let categories: string[] = [];
	let loading = true;
	let error = '';
	let searchQuery = '';
	let selectedCategory: string | null = null;
	let filteredApps: any[] = [];

	// Deployment modal
	let isModalOpen = false;
	let selectedApp: any = null;

	onMount(() => {
		// Set page title
		pageTitleStore.setTitle('App Store');

		loadCatalog();
	});

	async function loadCatalog() {
		loading = true;
		error = '';

		try {
			const [appsResponse, categoriesResponse] = await Promise.all([
				api.getCatalogApps(),
				api.getCatalogCategories()
			]);

			if (appsResponse.success && appsResponse.data) {
				// Extract applications array from response
				catalogApps = appsResponse.data.applications || [];
			} else {
				error = appsResponse.error || 'Failed to load catalog';
			}

			if (categoriesResponse.success && categoriesResponse.data) {
				// Extract categories array from response
				categories = categoriesResponse.data.categories || [];
			}
		} catch (err) {
			error = 'An unexpected error occurred';
			console.error(err);
		} finally {
			loading = false;
			filterApps();
		}
	}

	function filterApps() {
		let result = [...catalogApps];

		// Filter by category
		if (selectedCategory) {
			result = result.filter(
				(app) => app.category && app.category.toLowerCase() === selectedCategory.toLowerCase()
			);
		}

		// Filter by search query
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			result = result.filter(
				(app) =>
					app.name.toLowerCase().includes(query) ||
					app.description?.toLowerCase().includes(query) ||
					app.tags?.some((tag: string) => tag.toLowerCase().includes(query))
			);
		}

		filteredApps = result;
	}

	$: {
		// Reactive filtering when search or category changes
		searchQuery;
		selectedCategory;
		filterApps();
	}

	function handleCategorySelect(category: string | null) {
		selectedCategory = category;
	}

	function handleDeployClick(app: any) {
		selectedApp = app;
		isModalOpen = true;
	}

	async function handleDeploy(event: CustomEvent) {
		const deploymentData = event.detail;
		
		// Save app reference before closing modal
		const appToDeploy = selectedApp;

		// Close modal
		isModalOpen = false;

		// Show deploying toast
		toasts.info(`Deploying ${appToDeploy.name}...`, 3000);

		// Perform deployment
		const result = await myAppsStore.deployApp(deploymentData);

		if (result.success) {
			toasts.success(`${appToDeploy.name} deployment started!`, 5000);
			// Navigate to My Apps page
			goto('/apps');
		} else {
			toasts.error(result.error || `Failed to deploy ${appToDeploy.name}`, 7000);
		}
	}

	async function handleReload() {
		toasts.info('Reloading catalog...', 2000);
		const response = await api.reloadCatalog();

		if (response.success) {
			toasts.success('Catalog reloaded successfully!', 3000);
			await loadCatalog();
		} else {
			toasts.error(response.error || 'Failed to reload catalog', 5000);
		}
	}

	// Computed stats
	$: availableApps = catalogApps.length;
	$: uniqueCategories = categories.length;
</script>

<svelte:head>
	<title>App Store - Proximity</title>
</svelte:head>

<!-- Desktop Navigation Rack (visible only on lg: screens) -->
<NavigationRack />

<div class="min-h-screen bg-rack-darker p-6">
	<!-- Operational Control Panel Rack -->
	<OperationalRack title="Application Catalog">
		<!-- Stats Slot -->
		<svelte:fragment slot="stats">
			<StatBlock 
				label="Available Apps" 
				value={availableApps} 
				icon={ShoppingBag}
				ledColor="var(--color-accent)"
				borderColor="var(--color-accent)"
			/>
			
			<StatBlock 
				label="Categories" 
				value={uniqueCategories} 
				icon={Layers}
				ledColor="var(--color-led-active)"
				borderColor="rgba(16, 185, 129, 0.3)"
			/>
			
			<StatBlock 
				label="Filtered" 
				value={filteredApps.length} 
				icon={Grid}
				ledColor="var(--color-accent)"
				borderColor="var(--border-color-secondary)"
			/>
		</svelte:fragment>

		<!-- Actions Slot -->
		<svelte:fragment slot="actions">
			<!-- Search Input -->
			<div class="relative w-80">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search apps..."
					class="w-full rounded-lg border border-rack-primary/30 bg-rack-light py-2 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:border-rack-primary focus:outline-none focus:ring-2 focus:ring-rack-primary/20"
				/>
			</div>

			<!-- Reload Button -->
			<button
				on:click={handleReload}
				disabled={loading}
				class="refresh-button"
				title="Reload catalog from repository"
			>
				<RefreshCw class={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
				<span>Reload Catalog</span>
			</button>
		</svelte:fragment>
	</OperationalRack>

	<!-- Loading state -->
	{#if loading}
		<div class="flex h-64 items-center justify-center">
			<div class="text-center">
				<Loader2 class="mx-auto h-12 w-12 animate-spin text-rack-primary" />
				<p class="mt-4 text-gray-400">Loading catalog...</p>
			</div>
		</div>
	{:else if error}
		<!-- Error state -->
		<div
			class="rounded-lg border border-red-500/50 bg-red-500/10 p-8 text-center text-red-400"
		>
			<p class="mb-4">{error}</p>
			<button
				on:click={loadCatalog}
				class="rounded-lg bg-red-500/20 px-6 py-2 transition-colors hover:bg-red-500/30"
			>
				Try Again
			</button>
		</div>
	{:else}
		<!-- Category Filter Bar - Full Width -->
		<div class="mb-6">
			<CategoryFilter
				{categories}
				{selectedCategory}
				onCategorySelect={handleCategorySelect}
			/>
		</div>

		<!-- App Catalog Content -->
		<div class="w-full">
			{#if filteredApps.length === 0}
				<div class="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-rack-primary/30 bg-rack-light/50">
					<div class="text-center">
						<Package class="mx-auto h-16 w-16 text-gray-500" />
						<p class="mt-4 text-gray-400">
							{searchQuery || selectedCategory
								? 'No apps match your filters'
								: 'No apps available'}
						</p>
					</div>
				</div>
			{:else}
				<!-- App Catalog Rack - Full Width Grid -->
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pb-20">
					{#each filteredApps as app (app.id)}
						<RackCard {app} variant="catalog">
							<div slot="actions" class="flex gap-2">
								<button
									on:click={() => handleDeployClick(app)}
									data-testid="deploy-button-{app.id}"
									class="rounded-lg bg-rack-primary px-4 py-2 text-sm font-semibold text-white transition-all hover:bg-rack-primary/90"
								>
									Deploy
								</button>
							</div>
						</RackCard>
					{/each}
				</div>
			{/if}
		</div>
	{/if}
</div>

<!-- Deployment Modal -->
<DeploymentModal
	bind:isOpen={isModalOpen}
	app={selectedApp}
	on:deploy={handleDeploy}
	on:close={() => (isModalOpen = false)}
/>
