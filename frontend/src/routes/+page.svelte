<!-- Dashboard - System Overview Command Deck -->
<!-- Single unified rack panel displaying all critical system metrics -->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import { myAppsStore } from '$lib/stores/apps';
	import { api } from '$lib/api';
	import NavigationRack from '$lib/components/layout/NavigationRack.svelte';
	import SystemOverviewRack from '$lib/components/dashboard/SystemOverviewRack.svelte';

	// Dashboard stats
	let catalogStats = { total: 0, categories: 0 };
	let hostsStats = { total: 0, online: 0, cpuUsage: '0%', memoryUsage: '0%' };
	let loading = true;

	onMount(async () => {
		// Set page title
		pageTitleStore.setTitle('Dashboard');

		// Start polling for apps
		myAppsStore.startPolling(10000);

		// Load catalog stats
		const catalogResponse = await api.getCatalogStats();
		if (catalogResponse.success && catalogResponse.data) {
			catalogStats = {
				total: catalogResponse.data.total_apps || 0,
				categories: catalogResponse.data.total_categories || 0
			};
		}

		// Load hosts stats
		const hostsResponse = await api.listHosts();
		if (hostsResponse.success && hostsResponse.data) {
			const hosts = Array.isArray(hostsResponse.data) ? hostsResponse.data : [];
			hostsStats = {
				total: hosts.length,
				online: hosts.filter((h: any) => h.is_active === true).length,
				cpuUsage: '0%', // TODO: Calculate from hosts data
				memoryUsage: '0%' // TODO: Calculate from hosts data
			};
		}

		loading = false;
	});

	onDestroy(() => {
		myAppsStore.stopPolling();
	});

	// Reactive stats from apps store
	$: totalApps = $myAppsStore.apps.length;
	$: runningApps = $myAppsStore.apps.filter((app) => app.status === 'running').length;
	$: stoppedApps = $myAppsStore.apps.filter((app) => app.status === 'stopped').length;
	$: deployingApps = $myAppsStore.apps.filter((app) => app.status === 'deploying' || app.status === 'cloning').length;
</script>

<svelte:head>
	<title>Dashboard - Proximity</title>
</svelte:head>

<div class="bg-rack-darker">
	<!-- STICKY HEADER: Always-Visible Control Surface -->
	<header class="sticky-header">
		<!-- Desktop Navigation Rack (visible only on lg: screens) -->
		<div class="px-6 pt-6">
			<NavigationRack />
		</div>

		<!-- Main Dashboard Panel -->
		<div class="px-6 pb-6">
			<SystemOverviewRack
				{totalApps}
				{runningApps}
				{stoppedApps}
				{deployingApps}
				availableApps={catalogStats.total}
				categories={catalogStats.categories}
				totalHosts={hostsStats.total}
				onlineHosts={hostsStats.online}
				cpuUsage={hostsStats.cpuUsage}
				memoryUsage={hostsStats.memoryUsage}
			/>
		</div>
	</header>
	<!-- END: Sticky Header -->
	
	<!-- Note: Dashboard is a single-screen overview with no additional scrollable content -->
</div>
