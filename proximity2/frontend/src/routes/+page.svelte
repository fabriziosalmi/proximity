<!-- Dashboard - Home View -->
<!-- Main overview page showing system statistics and quick access -->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Server, Package, Play, Square, Loader2, HardDrive, Cpu, MemoryStick } from 'lucide-svelte';
	import StatCard from '$lib/components/dashboard/StatCard.svelte';
	import { myAppsStore } from '$lib/stores/apps';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import { api } from '$lib/api';

	// Dashboard stats
	let catalogStats = { total: 0, categories: 0 };
	let hostsStats = { total: 0, online: 0 };
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
				categories: catalogResponse.data.categories_count || 0
			};
		}

		// Load hosts stats
		const hostsResponse = await api.listHosts();
		if (hostsResponse.success && hostsResponse.data) {
			const hosts = hostsResponse.data.hosts || [];
			hostsStats = {
				total: hosts.length,
				online: hosts.filter((h: any) => h.status === 'online').length
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

<div class="dashboard-container">
	<!-- Header -->
	<div class="dashboard-header">
		<div>
			<h1 class="dashboard-title">Dashboard</h1>
			<p class="dashboard-subtitle">System overview and statistics</p>
		</div>
	</div>

	{#if loading && $myAppsStore.apps.length === 0}
		<!-- Loading State -->
		<div class="dashboard-loading">
			<Loader2 size={48} class="animate-spin" style="color: var(--text-color-secondary)" />
			<p style="color: var(--text-color-secondary); margin-top: 1rem;">Loading dashboard...</p>
		</div>
	{:else}
		<!-- Stats Grid -->
		<div class="dashboard-stats-grid">
			<!-- Applications Section -->
			<div class="dashboard-section">
				<h2 class="dashboard-section-title">Applications</h2>
				<div class="stats-row">
					<StatCard
						title="Total Apps"
						value={totalApps}
						icon={Server}
						variant="default"
					/>
					<StatCard
						title="Running"
						value={runningApps}
						icon={Play}
						variant="success"
					/>
					<StatCard
						title="Stopped"
						value={stoppedApps}
						icon={Square}
						variant="default"
					/>
					{#if deployingApps > 0}
						<StatCard
							title="Deploying"
							value={deployingApps}
							icon={Loader2}
							variant="warning"
						/>
					{/if}
				</div>
			</div>

			<!-- Catalog Section -->
			<div class="dashboard-section">
				<h2 class="dashboard-section-title">App Catalog</h2>
				<div class="stats-row">
					<StatCard
						title="Available Apps"
						value={catalogStats.total}
						icon={Package}
						variant="info"
					/>
					<StatCard
						title="Categories"
						value={catalogStats.categories}
						icon={Package}
						variant="default"
					/>
				</div>
			</div>

			<!-- Infrastructure Section -->
			<div class="dashboard-section">
				<h2 class="dashboard-section-title">Infrastructure</h2>
				<div class="stats-row">
					<StatCard
						title="Total Hosts"
						value={hostsStats.total}
						icon={HardDrive}
						variant="default"
					/>
					<StatCard
						title="Online Hosts"
						value={hostsStats.online}
						icon={HardDrive}
						variant={hostsStats.online === hostsStats.total ? 'success' : 'warning'}
					/>
					<StatCard
						title="CPU Usage"
						value="--"
						icon={Cpu}
						variant="default"
					/>
					<StatCard
						title="Memory Usage"
						value="--"
						icon={MemoryStick}
						variant="default"
					/>
				</div>
			</div>
		</div>

		<!-- Quick Actions -->
		<div class="dashboard-section">
			<h2 class="dashboard-section-title">Quick Actions</h2>
			<div class="quick-actions-grid">
				<a href="/store" class="quick-action-card">
					<Package size={32} />
					<div class="quick-action-title">Browse App Store</div>
					<div class="quick-action-description">Deploy new applications</div>
				</a>
				<a href="/apps" class="quick-action-card">
					<Server size={32} />
					<div class="quick-action-title">Manage Apps</div>
					<div class="quick-action-description">View and control your apps</div>
				</a>
				<a href="/hosts" class="quick-action-card">
					<HardDrive size={32} />
					<div class="quick-action-title">View Hosts</div>
					<div class="quick-action-description">Monitor infrastructure</div>
				</a>
			</div>
		</div>
	{/if}
</div>

<style>
	/* Dashboard Container */
	.dashboard-container {
		padding: 2rem;
		max-width: 1400px;
		margin: 0 auto;
	}

	/* Header */
	.dashboard-header {
		margin-bottom: 2rem;
	}

	.dashboard-title {
		font-size: 2rem;
		font-weight: 700;
		color: var(--text-color-primary);
		margin: 0 0 0.5rem 0;
	}

	.dashboard-subtitle {
		font-size: 1rem;
		color: var(--text-color-secondary);
		margin: 0;
	}

	/* Loading State */
	.dashboard-loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
	}

	/* Stats Grid */
	.dashboard-stats-grid {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	/* Section */
	.dashboard-section {
		margin-bottom: 2rem;
	}

	.dashboard-section-title {
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--text-color-primary);
		margin: 0 0 1rem 0;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid var(--border-color-primary);
	}

	/* Stats Row */
	.stats-row {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 1rem;
	}

	/* Quick Actions */
	.quick-actions-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
	}

	.quick-action-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		padding: 2rem;
		background: var(--card-bg-color);
		border: 1px solid var(--card-border-color);
		border-radius: 0.5rem;
		text-decoration: none;
		color: var(--text-color-primary);
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		gap: 0.75rem;
	}

	.quick-action-card:hover {
		border-color: var(--border-color-primary);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		transform: translateY(-2px);
	}

	.quick-action-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-color-primary);
	}

	.quick-action-description {
		font-size: 0.875rem;
		color: var(--text-color-secondary);
	}

	/* Responsive */
	@media (max-width: 768px) {
		.dashboard-container {
			padding: 1rem;
		}

		.stats-row {
			grid-template-columns: 1fr;
		}

		.quick-actions-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
