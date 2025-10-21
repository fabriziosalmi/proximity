<script lang="ts">
	/**
	 * My Apps - Operations Dashboard
	 * Premium hardware aesthetic with stat blocks and clean hierarchy
	 */
	import { onMount, onDestroy } from 'svelte';
	import {
		Loader2,
		Server,
		PlayCircle,
		StopCircle,
		RotateCw,
		Trash2,
		FileText,
		Copy,
		Clock,
		Wifi,
		Search,
		Filter,
		ArrowUpDown,
		PackagePlus,
		CalendarClock,
		SortAsc,
		Cpu,
		MemoryStick
	} from 'lucide-svelte';
	import { myAppsStore, hasDeployingApps } from '$lib/stores/apps';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import { toasts } from '$lib/stores/toast';
	import { startApp, stopApp, restartApp, deleteApp, cloneApp } from '$lib/stores/actions';
	import RackCard from '$lib/components/RackCard.svelte';
	import CloneModal from '$lib/components/CloneModal.svelte';
	import EmptyRackCard from '$lib/components/EmptyRackCard.svelte';
	import NavigationRack from '$lib/components/layout/NavigationRack.svelte';
	import OperationalRack from '$lib/components/layout/OperationalRack.svelte';

	let actionInProgress: Record<string, boolean> = {};
	let showCloneModal = false;
	let cloneSourceApp: any = null;

	// Filter, Search, and Sort state
	let selectedFilter: 'all' | 'running' | 'stopped' | 'error' | 'deploying' = 'all';
	let searchQuery = '';
	let sortBy: 'name' | 'created' | 'cpu' | 'memory' = 'created';

	onMount(() => {
		console.log('🏁 [AppsPage] Component mounted - onMount() executing');
		
		// Set page title
		pageTitleStore.setTitle('My Apps');

		// Start polling for real-time updates
		console.log('🚦 [AppsPage] Calling myAppsStore.startPolling(5000)');
		myAppsStore.startPolling(5000);
		
		console.log('✅ [AppsPage] onMount() complete');
	});

	onDestroy(() => {
		console.log('🛑 [AppsPage] Component unmounting - onDestroy() executing');
		
		// Stop polling when leaving the page
		myAppsStore.stopPolling();
		
		console.log('✅ [AppsPage] onDestroy() complete');
	});

	async function handleAction(appId: string, appName: string, action: 'start' | 'stop' | 'restart' | 'delete') {
		// Set action in progress
		actionInProgress[appId] = true;
		actionInProgress = { ...actionInProgress };

		// Use centralized action dispatcher (handles API, toasts, and sounds)
		switch (action) {
			case 'start':
				await startApp(appId, appName);
				break;
			case 'stop':
				await stopApp(appId, appName);
				break;
			case 'restart':
				await restartApp(appId, appName);
				break;
			case 'delete':
				await deleteApp(appId, appName);
				break;
		}

		// Clear action in progress
		actionInProgress[appId] = false;
		actionInProgress = { ...actionInProgress };
	}

	async function handleViewLogs(appId: string, appName: string) {
		toasts.info('Log viewer coming soon!', 3000);
		// TODO: Implement log viewer modal
	}

	function handleClone(app: any) {
		cloneSourceApp = app;
		showCloneModal = true;
	}

	async function handleCloneSubmit(newHostname: string) {
		console.log('Clone button clicked. Calling action dispatcher...');
		if (!cloneSourceApp) return;

		showCloneModal = false;

		// Use centralized action dispatcher (handles API, toasts, and sounds)
		const result = await cloneApp(cloneSourceApp.id, cloneSourceApp.name, newHostname);

		if (result.success) {
			cloneSourceApp = null;
		}
	}

	function handleRefresh() {
		myAppsStore.fetchApps();
		toasts.info('Refreshing apps...', 2000);
	}

	// Computed stats (based on ALL apps, not filtered)
	$: totalApps = $myAppsStore.apps.length;
	$: runningApps = $myAppsStore.apps.filter((a) => a.status === 'running').length;
	$: stoppedApps = $myAppsStore.apps.filter((a) => a.status === 'stopped').length;
	$: deployingApps = $myAppsStore.apps.filter((a) => a.status === 'deploying').length;
	$: cloningApps = $myAppsStore.apps.filter((a) => a.status === 'cloning').length;
	$: errorApps = $myAppsStore.apps.filter((a) => a.status === 'error').length;
	$: transitionalApps = deployingApps + cloningApps;

	// Filtered, searched, and sorted apps (client-side)
	$: filteredApps = (() => {
		let apps = $myAppsStore.apps;

		// 1. FILTER by status
		if (selectedFilter !== 'all') {
			apps = apps.filter((app) => app.status === selectedFilter);
		}

		// 2. SEARCH by name or hostname
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			apps = apps.filter(
				(app) =>
					app.name?.toLowerCase().includes(query) ||
					app.hostname?.toLowerCase().includes(query)
			);
		}

		// 3. SORT
		apps = [...apps]; // Create copy to avoid mutating original
		switch (sortBy) {
			case 'name':
				apps.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
				break;
			case 'created':
				apps.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
				break;
			case 'cpu':
				apps.sort((a, b) => (b.cpu_usage || 0) - (a.cpu_usage || 0));
				break;
			case 'memory':
				apps.sort((a, b) => {
					const aPercent = a.memory_used && a.memory_total ? (a.memory_used / a.memory_total) * 100 : 0;
					const bPercent = b.memory_used && b.memory_total ? (b.memory_used / b.memory_total) * 100 : 0;
					return bPercent - aPercent;
				});
				break;
		}

		return apps;
	})();

	$: filteredCount = filteredApps.length;
</script>

<svelte:head>
	<title>My Apps - Proximity</title>
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
			<OperationalRack title="Application Fleet Operations">
	<!-- ========================================== -->
	<!-- LEFT SECTION: Search, Filters & Sort -->
	<!-- ========================================== -->
	<svelte:fragment slot="stats">
		<div class="filters-group">
			<!-- 1. Search Input (primo) -->
			<div class="search-container">
				<Search class="search-icon h-4 w-4" />
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search apps..."
					class="search-input"
				/>
			</div>

			<!-- 2. Filter Section (secondo) -->
			<div class="filter-container">
				<!-- Filter Icon (senza scritta FILTER BY:) -->
				<div class="filter-label">
					<Filter class="h-3.5 w-3.5" />
				</div>

				<!-- Filter Chips -->
				<div class="filter-chips">
					<button
						class="filter-chip"
						class:filter-chip-active={selectedFilter === 'all'}
						on:click={() => (selectedFilter = 'all')}
						title="All Apps"
					>
						<Server class="h-4 w-4 text-cyan-400" />
						<span class="chip-count">{totalApps}</span>
					</button>
					<button
						class="filter-chip"
						class:filter-chip-active={selectedFilter === 'running'}
						on:click={() => (selectedFilter = 'running')}
						title="Running Apps"
					>
						<PlayCircle class="h-4 w-4 text-green-500" />
						<span class="chip-count">{runningApps}</span>
					</button>
					<button
						class="filter-chip"
						class:filter-chip-active={selectedFilter === 'stopped'}
						on:click={() => (selectedFilter = 'stopped')}
						title="Stopped Apps"
					>
						<StopCircle class="h-4 w-4 text-red-500" />
						<span class="chip-count">{stoppedApps}</span>
					</button>
					{#if transitionalApps > 0}
						<button
							class="filter-chip"
							class:filter-chip-active={selectedFilter === 'deploying'}
							on:click={() => (selectedFilter = 'deploying')}
						>
							<span>IN PROGRESS</span>
							<span class="chip-count chip-count-pulse">{transitionalApps}</span>
						</button>
					{/if}
					{#if errorApps > 0}
						<button
							class="filter-chip"
							class:filter-chip-active={selectedFilter === 'error'}
							on:click={() => (selectedFilter = 'error')}
						>
							<span>ERROR</span>
							<span class="chip-count chip-count-danger">{errorApps}</span>
						</button>
					{/if}
				</div>
			</div>

			<!-- 3. Sort Section (terzo) -->
			<div class="sort-container">
				<div class="sort-label">
					<ArrowUpDown class="h-3.5 w-3.5" />
				</div>

				<!-- Sort Buttons Horizontal -->
				<div class="sort-buttons">
					<button
						class="sort-btn"
						class:sort-btn-active={sortBy === 'created'}
						on:click={() => (sortBy = 'created')}
						title="Newest First"
					>
						<CalendarClock class="h-4 w-4" />
					</button>
					<button
						class="sort-btn"
						class:sort-btn-active={sortBy === 'name'}
						on:click={() => (sortBy = 'name')}
						title="Name (A-Z)"
					>
						<SortAsc class="h-4 w-4" />
					</button>
					<button
						class="sort-btn"
						class:sort-btn-active={sortBy === 'cpu'}
						on:click={() => (sortBy = 'cpu')}
						title="CPU Usage"
					>
						<Cpu class="h-4 w-4" />
					</button>
					<button
						class="sort-btn"
						class:sort-btn-active={sortBy === 'memory'}
						on:click={() => (sortBy = 'memory')}
						title="Memory Usage"
					>
						<MemoryStick class="h-4 w-4" />
					</button>
				</div>
			</div>
		</div>
	</svelte:fragment>		<!-- ========================================== -->
		<!-- RIGHT SECTION: System Actions -->
		<!-- ========================================== -->
		<svelte:fragment slot="actions">
			<div class="actions-group">
				<!-- Polling Indicator -->
				{#if $hasDeployingApps}
					<div class="polling-indicator" title="Real-time updates active - polling every 5 seconds">
						<Wifi class="h-3.5 w-3.5 polling-icon" />
						<span class="polling-text">Live Updates</span>
					</div>
				{/if}

				<!-- Last Updated -->
				{#if $myAppsStore.lastUpdated}
					<div class="last-updated">
						<Clock class="h-3.5 w-3.5" />
						<span>{$myAppsStore.lastUpdated.toLocaleTimeString()}</span>
					</div>
				{/if}

				<!-- Adopt Existing Button -->
				<a
					href="/adopt"
					class="filter-chip"
					title="Adopt Existing Containers"
				>
					<PackagePlus class="h-4 w-4 text-purple-400" />
				</a>

				<!-- Refresh Button -->
				<button
					on:click={handleRefresh}
					disabled={$myAppsStore.loading}
					class="refresh-button"
					title="Refresh applications"
				>
					<RotateCw class={`h-4 w-4 ${$myAppsStore.loading ? 'animate-spin' : ''}`} />
					<span>Refresh</span>
				</button>
			</div>
		</svelte:fragment>
		</OperationalRack>
		</div>
	</header>

	<!-- ============================================ -->
	<!-- SCROLLABLE CONTENT: App Racks Flow Beneath -->
	<!-- ============================================ -->
	<main class="px-10 pt-6 pb-6">
		<!-- Loading state with skeleton -->
	{#if $myAppsStore.loading && $myAppsStore.apps.length === 0}
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
	{:else if $myAppsStore.error}
		<!-- Error State -->
		<div class="flex min-h-[400px] flex-col items-center justify-center rounded-lg border-2 border-red-500/20 bg-red-500/5 p-8">
			<div class="mb-4 text-red-400">
				<Server class="h-16 w-16" />
			</div>
			<p class="mb-4 text-lg font-semibold text-red-400">{$myAppsStore.error}</p>
			<button
				on:click={handleRefresh}
				class="flex items-center gap-2 rounded-lg bg-red-500/20 px-4 py-2 text-red-400 transition-colors hover:bg-red-500/30"
			>
				<RotateCw class="h-4 w-4" />
				Try Again
			</button>
		</div>
	{:else if $myAppsStore.apps.length === 0}
		<!-- Empty State - Bare Metal Rack Card -->
		<EmptyRackCard 
			label="NO APPS INSTALLED"
			buttonText="INSTALL APP"
			buttonHref="/store"
			icon={Server}
		/>
	{:else if filteredApps.length === 0}
		<!-- No Results State (after filtering/searching) -->
		<div class="flex min-h-[400px] flex-col items-center justify-center rounded-lg border-2 border-gray-700/50 bg-gray-800/30 p-8">
			<Search class="mb-4 h-16 w-16 text-gray-600" />
			<p class="mb-2 text-xl font-semibold text-gray-400">No Apps Found</p>
			<p class="text-sm text-gray-500">
				Try adjusting your filters or search query
			</p>
			<button
				on:click={() => {
					selectedFilter = 'all';
					searchQuery = '';
				}}
				class="mt-4 rounded-lg bg-rack-primary/20 px-4 py-2 text-sm text-rack-primary transition-colors hover:bg-rack-primary/30"
			>
				Clear Filters
			</button>
		</div>
	{:else}
		<!-- Apps Rack - Vertical Stack -->
		<div class="space-y-4">
			{#each filteredApps as app (app.id)}
				<RackCard {app} variant="deployed">
					<svelte:fragment slot="actions">
						{#if app.status === 'deploying'}
							<!-- Show view logs button while deploying -->
							<button
								on:click={() => handleViewLogs(app.id, app.name)}
								disabled={actionInProgress[app.id]}
								class="action-btn action-btn-info"
								title="View Logs"
							>
								<FileText class="h-4 w-4" />
							</button>
						{:else if app.status === 'running'}
								<!-- Running: Show stop, restart, delete -->
								<button
									on:click={() => handleAction(app.id, app.name, 'stop')}
								disabled={actionInProgress[app.id]}
								class="action-btn action-btn-warning"
								title="Stop"
								>
									{#if actionInProgress[app.id]}
										<Loader2 class="h-4 w-4 animate-spin" />
									{:else}
										<StopCircle class="h-4 w-4" />
								{/if}
								</button>
								<button
									on:click={() => handleAction(app.id, app.name, 'restart')}
								disabled={actionInProgress[app.id]}
								class="action-btn action-btn-primary"
								title="Restart"
								>
									{#if actionInProgress[app.id]}
										<Loader2 class="h-4 w-4 animate-spin" />
									{:else}
										<RotateCw class="h-4 w-4" />
								{/if}
								</button>
								<button
									data-testid="clone-button"
								on:click={() => handleClone(app)}
								disabled={actionInProgress[app.id]}
								class="action-btn action-btn-info"
								title="Clone"
								>
									<Copy class="h-4 w-4" />
								</button>
							{:else if app.status === 'stopped'}
								<!-- Stopped: Show start, clone, delete -->
								<button
									on:click={() => handleAction(app.id, app.name, 'start')}
								disabled={actionInProgress[app.id]}
								class="action-btn action-btn-success"
								title="Start"
								>
									{#if actionInProgress[app.id]}
										<Loader2 class="h-4 w-4 animate-spin" />
									{:else}
										<PlayCircle class="h-4 w-4" />
								{/if}
								</button>
								<button
									data-testid="clone-button"
								on:click={() => handleClone(app)}
								disabled={actionInProgress[app.id]}
								class="action-btn action-btn-info"
								title="Clone"
								>
									<Copy class="h-4 w-4" />
								</button>
							{:else if app.status === 'error'}
								<!-- Error: Show restart, delete -->
								<button
									on:click={() => handleAction(app.id, app.name, 'restart')}
									disabled={actionInProgress[app.id]}
									class="action-btn action-btn-warning"
								>
									{#if actionInProgress[app.id]}
										<Loader2 class="h-4 w-4 animate-spin" />
									{:else}
										<RotateCw class="h-4 w-4" />
								{/if}
								</button>
							{/if}

							<!-- Delete button (always available except when deploying/deleting) -->
							{#if app.status !== 'deploying' && app.status !== 'deleting'}
								<button
									data-testid="delete-button"
									on:click={() => {
										if (
											confirm(
												`Are you sure you want to delete ${app.name}? This action cannot be undone.`
											)
										) {
											handleAction(app.id, app.name, 'delete');
										}
									}}
									disabled={actionInProgress[app.id]}
									class="action-btn action-btn-danger"
								>
									{#if actionInProgress[app.id]}
										<Loader2 class="h-4 w-4 animate-spin" />
									{:else}
										<Trash2 class="h-4 w-4" />
									{/if}
								</button>
							{/if}
						</svelte:fragment>
					</RackCard>
				{/each}
			</div>
	{/if}
	</main>
</div>

<!-- Clone Modal -->
<CloneModal
	bind:show={showCloneModal}
	sourceApp={cloneSourceApp}
	on:submit={(e) => handleCloneSubmit(e.detail)}
	on:close={() => {
		showCloneModal = false;
		cloneSourceApp = null;
	}}
/>

<style>
	/* ============================================ */
	/* IMMERSIVE COCKPIT LAYOUT */
	/* ============================================ */

	/* Sticky Header - Master Control + Operational Rack */
	.sticky-header {
		position: sticky;
		top: 0;
		z-index: 50;
		background-color: rgba(17, 24, 39, 0.95); /* Semi-transparent bg-rack-darker */
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		/* NO PADDING - handled by inner divs with px-6 pt-6 */
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
	}

	/* ============================================ */
	/* FILTER, SEARCH, AND SORT CONTROLS */
	/* ============================================ */

	/* Filters Group (Left Section) */
	.filters-group {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	/* Actions Group (Right Section) */
	.actions-group {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	/* Filter Label */
	.filter-label {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 0.625rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--color-text-secondary);
	}

	/* Filter Container - wraps icon + chips */
	.filter-container {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		height: 100%;
	}

	/* Sort Label */
	.sort-label {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 0.625rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--color-text-secondary);
	}

	/* Sort Container - Wrapper for label + buttons */
	.sort-container {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		height: 100%;
	}

	/* Sort Buttons - Horizontal layout like filter chips */
	.sort-buttons {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.sort-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0.5rem 0.75rem;
		border-radius: 0.375rem;
		border: 1px solid rgba(75, 85, 99, 0.3);
		background: rgba(0, 0, 0, 0.3);
		color: var(--color-text-secondary);
		cursor: pointer;
		transition: all 0.2s ease;
		min-width: 2.5rem;
	}

	.sort-btn:hover {
		border-color: rgba(14, 165, 233, 0.5);
		background: rgba(14, 165, 233, 0.1);
		color: var(--color-accent);
		transform: translateY(-1px);
	}

	.sort-btn-active {
		border-color: var(--color-accent);
		background: rgba(14, 165, 233, 0.2);
		color: var(--color-accent);
		box-shadow: 0 0 10px rgba(14, 165, 233, 0.3);
	}

	.sort-btn:active {
		transform: translateY(0);
	}
	.filter-chips {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.filter-chip {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.375rem 0.875rem;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-radius: 0.375rem;
		border: 1px solid rgba(75, 85, 99, 0.3);
		background: rgba(0, 0, 0, 0.3);
		color: var(--color-text-secondary);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.filter-chip:hover {
		border-color: rgba(14, 165, 233, 0.5);
		background: rgba(14, 165, 233, 0.1);
		color: #0ea5e9;
	}

	.filter-chip:hover .chip-count {
		background: rgba(14, 165, 233, 0.3);
	}

	.filter-chip-active {
		border-color: var(--color-accent);
		background: rgba(14, 165, 233, 0.2);
		color: var(--color-accent-bright);
		box-shadow: 0 0 12px rgba(14, 165, 233, 0.3);
	}

	/* Count Badge */
	.chip-count {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 1.5rem;
		height: 1.25rem;
		padding: 0.125rem 0.5rem;
		font-size: 0.75rem;
		font-weight: 700;
		line-height: 1;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 9999px; /* Pill shape */
		transition: all 0.2s ease;
	}

	/* Active chip badge */
	.filter-chip-active .chip-count {
		background: var(--color-accent);
		color: white;
		box-shadow: 0 0 8px rgba(14, 165, 233, 0.5);
	}

	/* Pulsing badge for transitional states */
	.chip-count-pulse {
		background: rgba(245, 158, 11, 0.2);
		color: #fbbf24;
		animation: badge-pulse 2s ease-in-out infinite;
	}

	.filter-chip-active .chip-count-pulse {
		background: rgba(245, 158, 11, 0.9);
		color: white;
	}

	/* Danger badge for error states */
	.chip-count-danger {
		background: rgba(239, 68, 68, 0.2);
		color: #f87171;
	}

	.filter-chip-active .chip-count-danger {
		background: rgba(239, 68, 68, 0.9);
		color: white;
	}

	@keyframes badge-pulse {
		0%, 100% {
			opacity: 1;
		}
		50% {
			opacity: 0.6;
		}
	}

	/* Search Input */
	.search-container {
		position: relative;
		display: flex;
		align-items: center;
	}

	.search-icon {
		position: absolute;
		left: 0.75rem;
		color: var(--color-text-secondary);
		pointer-events: none;
	}

	.search-input {
		width: 240px;
		padding: 0.5rem 0.75rem 0.5rem 2.5rem;
		font-size: 0.875rem;
		border-radius: 0.375rem;
		border: 1px solid rgba(75, 85, 99, 0.3);
		background: rgba(0, 0, 0, 0.3);
		color: var(--color-text-primary);
		transition: all 0.2s ease;
	}

	.search-input::placeholder {
		color: var(--color-text-secondary);
	}

	.search-input:focus {
		outline: none;
		border-color: var(--color-accent);
		box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
		background: rgba(0, 0, 0, 0.4);
	}

	/* DEPRECATED: Sort Grid 2x2 styles (replaced with horizontal layout) */
	/* .sort-grid { ... } */

	/* Sort Dropdown - DEPRECATED (kept for reference) */
	.sort-select {
		padding: 0.5rem 0.75rem;
		font-size: 0.875rem;
		font-weight: 500;
		border-radius: 0.375rem;
		border: 1px solid rgba(75, 85, 99, 0.3);
		background: rgba(0, 0, 0, 0.3);
		color: var(--color-text-primary);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.sort-select:hover {
		border-color: rgba(14, 165, 233, 0.5);
		background: rgba(14, 165, 233, 0.1);
	}

	.sort-select:focus {
		outline: none;
		border-color: var(--color-accent);
		box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
	}

	.sort-select option {
		background: var(--bg-card);
		color: var(--color-text-primary);
	}
</style>
