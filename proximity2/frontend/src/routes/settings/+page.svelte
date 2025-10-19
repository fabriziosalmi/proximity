<script lang="ts">
	/**
	 * Settings Page - Comprehensive Configuration Management
	 * Tabbed interface for Proxmox, Resources, Network, and System settings
	 */
	import { onMount } from 'svelte';
	import { Server, Cpu, Network, Settings as SettingsIcon } from 'lucide-svelte';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import ProxmoxSettings from '$lib/components/settings/ProxmoxSettings.svelte';
	import ResourceSettings from '$lib/components/settings/ResourceSettings.svelte';
	import NetworkSettings from '$lib/components/settings/NetworkSettings.svelte';
	import SystemSettings from '$lib/components/settings/SystemSettings.svelte';

	type Tab = 'proxmox' | 'resources' | 'network' | 'system';

	let activeTab: Tab = 'proxmox';

	const tabs = [
		{
			id: 'proxmox' as Tab,
			label: 'Proxmox',
			icon: Server,
			description: 'Configure Proxmox VE host connection'
		},
		{
			id: 'resources' as Tab,
			label: 'Resources',
			icon: Cpu,
			description: 'Default resource allocations'
		},
		{
			id: 'network' as Tab,
			label: 'Network',
			icon: Network,
			description: 'Network configuration defaults'
		},
		{
			id: 'system' as Tab,
			label: 'System',
			icon: SettingsIcon,
			description: 'System-wide preferences'
		}
	];

	function switchTab(tabId: Tab) {
		const tab = tabs.find((t) => t.id === tabId);
		if (tab && !tab.disabled) {
			activeTab = tabId;
		}
	}

	onMount(() => {
		pageTitleStore.setTitle('Settings');
	});
</script>

<svelte:head>
	<title>Settings - Proximity</title>
</svelte:head>

<div class="min-h-screen bg-rack-darker p-6">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="mb-2 text-4xl font-bold text-white">Settings</h1>
		<p class="text-gray-400">Configure your Proximity installation</p>
	</div>

	<!-- Tabs Navigation -->
	<div class="settings-container">
		<div class="tabs-nav">
			{#each tabs as tab}
				<button
					on:click={() => switchTab(tab.id)}
					disabled={tab.disabled}
					class="tab-button"
					class:active={activeTab === tab.id}
					class:disabled={tab.disabled}
					data-testid="tab-{tab.id}"
				>
					<div class="tab-icon">
						<svelte:component this={tab.icon} size={20} />
					</div>
					<div class="tab-content">
						<div class="tab-label">{tab.label}</div>
						<div class="tab-description">{tab.description}</div>
					</div>
					{#if tab.disabled}
						<span class="tab-badge">Coming Soon</span>
					{/if}
				</button>
			{/each}
		</div>

		<!-- Tab Content -->
		<div class="tab-panel">
			{#if activeTab === 'proxmox'}
				<ProxmoxSettings />
			{:else if activeTab === 'resources'}
				<ResourceSettings />
			{:else if activeTab === 'network'}
				<NetworkSettings />
			{:else if activeTab === 'system'}
				<SystemSettings />
			{/if}
		</div>
	</div>
</div>

<style>
	.settings-container {
		display: grid;
		grid-template-columns: 300px 1fr;
		gap: 2rem;
		max-width: 1400px;
	}

	/* Tab Navigation */
	.tabs-nav {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.tab-button {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		padding: 1rem;
		background: var(--bg-card, #1f2937);
		border: 2px solid transparent;
		border-radius: 0.75rem;
		cursor: pointer;
		transition: all 0.2s ease;
		text-align: left;
		position: relative;
	}

	.tab-button:not(.disabled):hover {
		border-color: var(--color-accent, #3b82f6);
		background: rgba(59, 130, 246, 0.05);
	}

	.tab-button.active {
		border-color: var(--color-accent, #3b82f6);
		background: rgba(59, 130, 246, 0.1);
		box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
	}

	.tab-button.disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.tab-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		background: rgba(59, 130, 246, 0.1);
		border-radius: 0.5rem;
		color: var(--color-accent, #3b82f6);
		flex-shrink: 0;
	}

	.tab-button.active .tab-icon {
		background: rgba(59, 130, 246, 0.2);
	}

	.tab-content {
		flex: 1;
		min-width: 0;
	}

	.tab-label {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--color-text-primary, #e5e7eb);
		margin-bottom: 0.25rem;
	}

	.tab-description {
		font-size: 0.75rem;
		color: var(--color-text-secondary, #9ca3af);
		line-height: 1.4;
	}

	.tab-badge {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		font-size: 0.625rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 0.25rem 0.5rem;
		background: rgba(251, 191, 36, 0.2);
		color: #fbbf24;
		border-radius: 0.25rem;
	}

	/* Tab Panel */
	.tab-panel {
		min-height: 500px;
	}

	/* Placeholder Panel */
	.placeholder-panel {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		padding: 3rem;
		background: var(--bg-card, #1f2937);
		border: 2px dashed var(--border-color-secondary, #374151);
		border-radius: 0.75rem;
		text-align: center;
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.settings-container {
			grid-template-columns: 250px 1fr;
			gap: 1.5rem;
		}
	}

	@media (max-width: 768px) {
		.settings-container {
			grid-template-columns: 1fr;
			gap: 1rem;
		}

		.tabs-nav {
			flex-direction: row;
			overflow-x: auto;
			padding-bottom: 0.5rem;
		}

		.tab-button {
			min-width: 200px;
		}

		.tab-badge {
			position: static;
			margin-left: auto;
		}
	}
</style>
