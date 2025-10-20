<script lang="ts">
	/**
	 * Settings Page - Comprehensive Configuration Management
	 * OperationalRack-based interface for Proxmox, Resources, Network, and System settings
	 */
	import { onMount } from 'svelte';
	import { Server, Cpu, Network, Settings as SettingsIcon, Save } from 'lucide-svelte';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import { switchTab as switchTabAction } from '$lib/stores/actions';
	import ProxmoxSettings from '$lib/components/settings/ProxmoxSettings.svelte';
	import ResourceSettings from '$lib/components/settings/ResourceSettings.svelte';
	import NetworkSettings from '$lib/components/settings/NetworkSettings.svelte';
	import SystemSettings from '$lib/components/settings/SystemSettings.svelte';
	import NavigationRack from '$lib/components/layout/NavigationRack.svelte';
	import OperationalRack from '$lib/components/layout/OperationalRack.svelte';

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
		if (tab) {
			activeTab = tabId;
			switchTabAction(tabId); // Use centralized action for sound feedback
		}
	}

	// Get current tab info for display
	$: currentTab = tabs.find((t) => t.id === activeTab);

	onMount(() => {
		pageTitleStore.setTitle('Settings');
	});
</script>

<svelte:head>
	<title>Settings - Proximity</title>
</svelte:head>

<!-- Desktop Navigation Rack (visible only on lg: screens) -->
<NavigationRack />

<div class="min-h-screen bg-rack-darker p-6">
	<!-- Operational Control Panel -->
	<OperationalRack>
		<div slot="stats" class="flex items-center gap-3">
			<div class="flex items-center gap-2">
				<svelte:component this={currentTab?.icon} class="h-5 w-5 text-rack-primary" />
				<span class="text-sm font-semibold text-white">{currentTab?.label}</span>
			</div>
			<div class="hidden md:block text-xs text-gray-400">
				{currentTab?.description}
			</div>
		</div>

		<div slot="actions" class="flex flex-wrap items-center gap-2">
			{#each tabs as tab}
				<button
					on:click={() => switchTab(tab.id)}
					data-testid="tab-{tab.id}"
					class="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all
						{activeTab === tab.id
							? 'bg-rack-primary text-white shadow-lg shadow-rack-primary/30'
							: 'bg-rack-light/50 text-gray-300 hover:bg-rack-light hover:text-white'}"
				>
					<svelte:component this={tab.icon} class="h-4 w-4" />
					<span class="hidden sm:inline">{tab.label}</span>
				</button>
			{/each}
		</div>
	</OperationalRack>

	<!-- Settings Content Panel -->
	<div class="mt-6">
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
