<script lang="ts">
	/**
	 * Application Detail Page
	 * View app details and manage backups
	 */
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		Loader2,
		Server,
		PlayCircle,
		StopCircle,
		RotateCw,
		Trash2,
		ArrowLeft,
		Info,
		Activity
	} from 'lucide-svelte';
	import { api } from '$lib/api';
	import { toasts } from '$lib/stores/toast';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import BackupManager from '$lib/components/backups/BackupManager.svelte';

	// Get app ID from URL params
	$: appId = $page.params.id;

	// State
	let loading = true;
	let app: any = null;
	let pollingInterval: any = null;
	let actionInProgress = false;

	async function loadApp() {
		if (!appId) return;

		loading = true;

		try {
			const response = await api.getApp(appId);

			if (response.success && response.data) {
				app = response.data;
				pageTitleStore.setTitle(app.name || 'App Details');

				// Start polling if app is in a transitional state
				if (
					app.status === 'deploying' ||
					app.status === 'cloning' ||
					app.status === 'starting' ||
					app.status === 'stopping'
				) {
					startPolling();
				}
			} else {
				toasts.error(response.error || 'Failed to load app details', 7000);
				goto('/apps');
			}
		} catch (err) {
			console.error('Error loading app:', err);
			toasts.error('An error occurred while loading app', 7000);
			goto('/apps');
		} finally {
			loading = false;
		}
	}

	async function performAction(action: 'start' | 'stop' | 'restart' | 'delete') {
		if (!app) return;

		const actionLabels = {
			start: 'Starting',
			stop: 'Stopping',
			restart: 'Restarting',
			delete: 'Deleting'
		};

		// Confirmation for delete
		if (action === 'delete') {
			const confirmed = confirm(
				`Are you sure you want to delete ${app.name}? This action cannot be undone.`
			);
			if (!confirmed) return;
		}

		actionInProgress = true;
		toasts.info(`${actionLabels[action]} ${app.name}...`, 2000);

		try {
			const response = await api.performAppAction(appId, action);

			if (response.success) {
				if (action === 'delete') {
					toasts.success(`${app.name} deleted successfully`, 5000);
					goto('/apps');
				} else {
					toasts.success(`${app.name} ${action} command sent`, 5000);
					// Reload app to get updated status
					await loadApp();
				}
			} else {
				toasts.error(response.error || `Failed to ${action} ${app.name}`, 7000);
			}
		} catch (err) {
			console.error(`${action} error:`, err);
			toasts.error(`An error occurred during ${action}`, 7000);
		} finally {
			actionInProgress = false;
		}
	}

	function startPolling() {
		if (pollingInterval) return;

		pollingInterval = setInterval(async () => {
			if (!app) return;

			const response = await api.getApp(appId);
			if (response.success && response.data) {
				app = response.data;

				// Stop polling if app reached a stable state
				if (
					app.status !== 'deploying' &&
					app.status !== 'cloning' &&
					app.status !== 'starting' &&
					app.status !== 'stopping'
				) {
					stopPolling();
				}
			}
		}, 5000);
	}

	function stopPolling() {
		if (pollingInterval) {
			clearInterval(pollingInterval);
			pollingInterval = null;
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'running':
				return 'text-green-400';
			case 'stopped':
				return 'text-gray-400';
			case 'deploying':
			case 'cloning':
			case 'starting':
			case 'stopping':
				return 'text-blue-400';
			case 'error':
			case 'failed':
				return 'text-red-400';
			default:
				return 'text-gray-400';
		}
	}

	onMount(() => {
		loadApp();
	});

	onDestroy(() => {
		stopPolling();
	});
</script>

<svelte:head>
	<title>{app?.name || 'App Details'} - Proximity</title>
</svelte:head>

<div class="bg-rack-darker">
	{#if loading}
		<!-- Loading State -->
		<div class="flex items-center justify-center py-12 px-6">
			<Loader2 class="h-8 w-8 animate-spin text-blue-400" />
			<span class="ml-3 text-gray-400">Loading application details...</span>
		</div>
	{:else if app}
		<!-- ============================================ -->
		<!-- STICKY HEADER: Back Navigation -->
		<!-- ============================================ -->
		<header class="sticky-header">
			<div class="px-6 pt-6 pb-6">
				<!-- Back Button -->
				<div class="mb-0">
					<a
						href="/apps"
						class="inline-flex items-center gap-2 text-sm text-gray-400 transition-colors hover:text-white"
					>
						<ArrowLeft class="h-4 w-4" />
						Back to Apps
					</a>
				</div>
			</div>
		</header>

		<!-- ============================================ -->
		<!-- SCROLLABLE CONTENT: App Details -->
		<!-- ============================================ -->
		<main class="px-10 pt-6 pb-6">

		<!-- App Header -->
		<div class="app-header">
			<div class="header-content">
				<div class="app-icon">
					<Server class="h-8 w-8" />
				</div>
				<div class="app-info">
					<h1 class="app-name">{app.name}</h1>
					<div class="app-meta">
						<span class="status-badge {getStatusColor(app.status)}">
							<Activity class="h-4 w-4" />
							{app.status}
						</span>
						{#if app.hostname}
							<span class="meta-item">
								<Info class="h-4 w-4" />
								{app.hostname}
							</span>
						{/if}
					</div>
				</div>
			</div>

			<!-- Action Buttons -->
			<div class="header-actions">
				{#if app.status === 'running'}
					<button
						on:click={() => performAction('stop')}
						disabled={actionInProgress}
						class="btn-action btn-stop"
					>
						{#if actionInProgress}
							<Loader2 class="h-4 w-4 animate-spin" />
						{:else}
							<StopCircle class="h-4 w-4" />
						{/if}
						Stop
					</button>
					<button
						on:click={() => performAction('restart')}
						disabled={actionInProgress}
						class="btn-action btn-restart"
					>
						{#if actionInProgress}
							<Loader2 class="h-4 w-4 animate-spin" />
						{:else}
							<RotateCw class="h-4 w-4" />
						{/if}
						Restart
					</button>
				{:else if app.status === 'stopped'}
					<button
						on:click={() => performAction('start')}
						disabled={actionInProgress}
						class="btn-action btn-start"
					>
						{#if actionInProgress}
							<Loader2 class="h-4 w-4 animate-spin" />
						{:else}
							<PlayCircle class="h-4 w-4" />
						{/if}
						Start
					</button>
				{:else if app.status === 'error'}
					<button
						on:click={() => performAction('restart')}
						disabled={actionInProgress}
						class="btn-action btn-restart"
					>
						{#if actionInProgress}
							<Loader2 class="h-4 w-4 animate-spin" />
						{:else}
							<RotateCw class="h-4 w-4" />
						{/if}
						Retry
					</button>
				{/if}

				{#if app.status !== 'deploying' && app.status !== 'deleting'}
					<button
						on:click={() => performAction('delete')}
						disabled={actionInProgress}
						class="btn-action btn-delete"
					>
						{#if actionInProgress}
							<Loader2 class="h-4 w-4 animate-spin" />
						{:else}
							<Trash2 class="h-4 w-4" />
						{/if}
						Delete
					</button>
				{/if}
			</div>
		</div>

		<!-- App Details Card -->
		<div class="details-card">
			<h2 class="section-title">Application Details</h2>
			<div class="details-grid">
				<div class="detail-item">
					<span class="detail-label">ID</span>
					<span class="detail-value">{app.id}</span>
				</div>
				<div class="detail-item">
					<span class="detail-label">Hostname</span>
					<span class="detail-value">{app.hostname || 'N/A'}</span>
				</div>
				<div class="detail-item">
					<span class="detail-label">Status</span>
					<span class="detail-value {getStatusColor(app.status)}">{app.status}</span>
				</div>
				{#if app.vmid}
					<div class="detail-item">
						<span class="detail-label">VMID</span>
						<span class="detail-value">{app.vmid}</span>
					</div>
				{/if}
				{#if app.node}
					<div class="detail-item">
						<span class="detail-label">Node</span>
						<span class="detail-value">{app.node}</span>
					</div>
				{/if}
				{#if app.created_at}
					<div class="detail-item">
						<span class="detail-label">Created</span>
						<span class="detail-value">{new Date(app.created_at).toLocaleString()}</span>
					</div>
				{/if}
			</div>
		</div>

		<!-- Backup Manager -->
		<BackupManager appId={app.id} appName={app.name} />
		</main>
		<!-- END: Main Scrollable Content -->
	{/if}
</div>

<style>
	.app-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1.5rem;
		padding: 2rem;
		background: var(--bg-card, #1f2937);
		border: 1px solid var(--border-color-primary, #4b5563);
		border-radius: 0.75rem;
		margin-bottom: 2rem;
	}

	.header-content {
		display: flex;
		gap: 1.5rem;
		align-items: flex-start;
		flex: 1;
	}

	.app-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 64px;
		height: 64px;
		background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
		border-radius: 0.75rem;
		color: white;
		flex-shrink: 0;
	}

	.app-info {
		flex: 1;
		min-width: 0;
	}

	.app-name {
		font-size: 2rem;
		font-weight: 700;
		color: var(--color-text-primary, #e5e7eb);
		margin: 0 0 0.75rem 0;
	}

	.app-meta {
		display: flex;
		gap: 1rem;
		align-items: center;
		flex-wrap: wrap;
	}

	.status-badge {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.375rem 0.75rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.meta-item {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 0.875rem;
		color: var(--color-text-secondary, #9ca3af);
	}

	.header-actions {
		display: flex;
		gap: 0.75rem;
		flex-shrink: 0;
	}

	.btn-action {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 1.25rem;
		font-size: 0.875rem;
		font-weight: 600;
		border-radius: 0.375rem;
		cursor: pointer;
		transition: all 0.2s ease;
		border: 1px solid transparent;
		white-space: nowrap;
	}

	.btn-action:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-start {
		background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
		color: white;
		box-shadow: 0 2px 4px rgba(34, 197, 94, 0.3);
	}

	.btn-start:hover:not(:disabled) {
		background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
		box-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
	}

	.btn-stop {
		background: rgba(234, 179, 8, 0.1);
		color: #eab308;
		border-color: rgba(234, 179, 8, 0.3);
	}

	.btn-stop:hover:not(:disabled) {
		background: rgba(234, 179, 8, 0.2);
		border-color: #eab308;
	}

	.btn-restart {
		background: rgba(59, 130, 246, 0.1);
		color: #3b82f6;
		border-color: rgba(59, 130, 246, 0.3);
	}

	.btn-restart:hover:not(:disabled) {
		background: rgba(59, 130, 246, 0.2);
		border-color: #3b82f6;
	}

	.btn-delete {
		background: rgba(239, 68, 68, 0.1);
		color: #ef4444;
		border-color: rgba(239, 68, 68, 0.3);
	}

	.btn-delete:hover:not(:disabled) {
		background: rgba(239, 68, 68, 0.2);
		border-color: #ef4444;
	}

	.details-card {
		background: var(--bg-card, #1f2937);
		border: 1px solid var(--border-color-primary, #4b5563);
		border-radius: 0.75rem;
		padding: 2rem;
	}

	.section-title {
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--color-text-primary, #e5e7eb);
		margin: 0 0 1.5rem 0;
		padding-bottom: 1rem;
		border-bottom: 1px solid var(--border-color-secondary, #374151);
	}

	.details-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
	}

	.detail-item {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.detail-label {
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-secondary, #9ca3af);
	}

	.detail-value {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--color-text-primary, #e5e7eb);
	}

	@media (max-width: 768px) {
		.app-header {
			flex-direction: column;
		}

		.header-actions {
			width: 100%;
			flex-wrap: wrap;
		}

		.btn-action {
			flex: 1;
			justify-content: center;
		}

		.details-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
