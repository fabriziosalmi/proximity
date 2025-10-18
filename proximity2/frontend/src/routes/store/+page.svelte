<script lang="ts">
	/**
	 * App Store - Browse and deploy applications from the catalog
	 */
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { Search, Loader2, Package, RefreshCw } from 'lucide-svelte';
	import { api } from '$lib/api';
	import { myAppsStore } from '$lib/stores/apps';
	import { toasts } from '$lib/stores/toast';
	import RackCard from '$lib/components/RackCard.svelte';
	import CategoryFilter from '$lib/components/CategoryFilter.svelte';
	import DeploymentModal from '$lib/components/DeploymentModal.svelte';

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

		// Close modal
		isModalOpen = false;

		// Show deploying toast
		toasts.info(`Deploying ${selectedApp.name}...`, 3000);

		// Perform deployment
		const result = await myAppsStore.deployApp(deploymentData);

		if (result.success) {
			toasts.success(`${selectedApp.name} deployment started!`, 5000);
			// Navigate to My Apps page
			goto('/apps');
		} else {
			toasts.error(result.error || `Failed to deploy ${selectedApp.name}`, 7000);
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
</script>

<svelte:head>
	<title>App Store - Proximity</title>
</svelte:head>

<div class="min-h-screen bg-rack-darker p-6">
	<!-- Header -->
	<div class="mb-8">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="mb-2 text-4xl font-bold text-white">App Store</h1>
				<p class="text-gray-400">
					Browse and deploy applications from the catalog
				</p>
			</div>
			<button
				on:click={handleReload}
				disabled={loading}
				class="flex items-center gap-2 rounded-lg bg-rack-primary/10 px-4 py-2 text-rack-primary transition-colors hover:bg-rack-primary/20 disabled:opacity-50"
			>
				<RefreshCw class="h-4 w-4" />
				Reload Catalog
			</button>
		</div>

		<!-- Search bar -->
		<div class="mt-6">
			<div class="relative">
				<Search class="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search applications..."
					class="w-full rounded-lg border border-rack-primary/30 bg-rack-light py-3 pl-12 pr-4 text-white placeholder-gray-500 focus:border-rack-primary focus:outline-none focus:ring-2 focus:ring-rack-primary/20"
				/>
			</div>
		</div>
	</div>

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
		<!-- Main content: Two-column layout -->
		<div class="flex gap-6">
			<!-- Left sidebar: Category filter -->
			<div class="w-64 flex-shrink-0">
				<div class="sticky top-6">
					<CategoryFilter
						{categories}
						{selectedCategory}
						onCategorySelect={handleCategorySelect}
					/>
				</div>
			</div>

			<!-- Right content: App grid -->
			<div class="flex-1">
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
					<!-- Results count -->
					<div class="mb-4 text-sm text-gray-400">
						{filteredApps.length}
						{filteredApps.length === 1 ? 'app' : 'apps'} found
						{#if selectedCategory}
							<span class="text-rack-primary">
								in {selectedCategory}
							</span>
						{/if}
					</div>

					<!-- App grid -->
					<div class="grid gap-6 sm:grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
						{#each filteredApps as app (app.id)}
							<RackCard {app} variant="catalog">
								<div slot="actions" class="w-full">
									<button
										on:click={() => handleDeployClick(app)}
										class="w-full rounded-lg bg-rack-primary px-4 py-2 font-medium text-white transition-colors hover:bg-rack-primary/90"
									>
										Deploy
									</button>
								</div>
							</RackCard>
						{/each}
					</div>
				{/if}
			</div>
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
