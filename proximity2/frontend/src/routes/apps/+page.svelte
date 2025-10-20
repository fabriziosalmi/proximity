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
		Activity,
		CheckCircle2,
		XCircle,
		Clock,
		Wifi
	} from 'lucide-svelte';
	import { myAppsStore, hasDeployingApps } from '$lib/stores/apps';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import { toasts } from '$lib/stores/toast';
	import { startApp, stopApp, restartApp, deleteApp, cloneApp } from '$lib/stores/actions';
	import RackCard from '$lib/components/RackCard.svelte';
	import CloneModal from '$lib/components/CloneModal.svelte';
	import StatBlock from '$lib/components/dashboard/StatBlock.svelte';
	import NavigationRack from '$lib/components/layout/NavigationRack.svelte';
	import OperationalRack from '$lib/components/layout/OperationalRack.svelte';

	let actionInProgress: Record<string, boolean> = {};
	let showCloneModal = false;
	let cloneSourceApp: any = null;

	onMount(() => {
		// Set page title
		pageTitleStore.setTitle('My Apps');

		// Start polling for real-time updates
		myAppsStore.startPolling(5000);
	});

	onDestroy(() => {
		// Stop polling when leaving the page
		myAppsStore.stopPolling();
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

	// Computed stats
	$: totalApps = $myAppsStore.apps.length;
	$: runningApps = $myAppsStore.apps.filter((a) => a.status === 'running').length;
	$: stoppedApps = $myAppsStore.apps.filter((a) => a.status === 'stopped').length;
	$: deployingApps = $myAppsStore.apps.filter((a) => a.status === 'deploying').length;
	$: cloningApps = $myAppsStore.apps.filter((a) => a.status === 'cloning').length;
	$: transitionalApps = deployingApps + cloningApps;
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
		<!-- Stats Slot -->
		<svelte:fragment slot="stats">
			<StatBlock 
				label="Total" 
				value={totalApps} 
				icon={Server}
				ledColor="var(--color-accent)"
				borderColor="var(--color-accent)"
			/>
			
			<StatBlock 
				label="Running" 
				value={runningApps} 
				icon={CheckCircle2}
				ledColor="var(--color-led-active)"
				borderColor="rgba(16, 185, 129, 0.3)"
				pulse={runningApps > 0}
			/>
			
			<StatBlock 
				label="Stopped" 
				value={stoppedApps} 
				icon={XCircle}
				ledColor="var(--color-led-inactive)"
				borderColor="var(--border-color-secondary)"
			/>
			
			{#if transitionalApps > 0}
				<StatBlock 
					label="In Progress" 
					value={transitionalApps} 
					icon={Clock}
					ledColor="var(--color-led-warning)"
					borderColor="rgba(245, 158, 11, 0.3)"
					pulse={true}
				/>
			{/if}
		</svelte:fragment>

		<!-- Actions Slot -->
		<svelte:fragment slot="actions">
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
		<!-- Empty State -->
		<div class="flex min-h-[400px] flex-col items-center justify-center rounded-lg border-2 border-gray-700/50 bg-gray-800/30 p-8">
			<Server class="mb-4 h-16 w-16 text-gray-600" />
			<p class="mb-2 text-xl font-semibold text-gray-400">No Deployed Apps</p>
			<p class="text-sm text-gray-500">
				Visit the <a href="/store" class="text-cyan-400 hover:underline">App Store</a> to deploy your first application
			</p>
		</div>
	{:else}
		<!-- Apps Rack - Vertical Stack -->
		<div class="space-y-4">
			{#each $myAppsStore.apps as app (app.id)}
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
	
	.main-canvas {
		min-height: 100vh;
		background-color: var(--bg-rack-darker);
	}

	/* Sticky Header - Master Control + Operational Rack */
	.sticky-header {
		position: sticky;
		top: 0;
		z-index: 50;
		background-color: rgba(17, 24, 39, 0.95); /* Semi-transparent bg-rack-darker */
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		padding: 1.5rem 2rem 0 2rem;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
	}

	.master-control-wrapper {
		margin-bottom: 1.5rem;
	}

	.operational-rack-wrapper {
		/* No extra margin - OperationalRack has its own spacing */
	}

	/* Content Rack - Scrollable Area */
	.content-rack {
		padding: 2rem;
	}

	/* Responsive adjustments */
	@media (max-width: 1024px) {
		.sticky-header {
			padding: 1rem;
		}
		
		.content-rack {
			padding: 1rem;
		}
	}
</style>
