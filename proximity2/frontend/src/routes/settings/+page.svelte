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

	<!-- Settings Content Panel - Rack Unit Style -->
	<div class="mt-6 settings-rack-unit">
		<!-- Mounting Ears -->
		<div class="rack-ear rack-ear-left">
			<div class="screw screw-top"></div>
			<div class="screw screw-bottom"></div>
		</div>

		<div class="rack-ear rack-ear-right">
			<div class="screw screw-top"></div>
			<div class="screw screw-bottom"></div>
		</div>

		<!-- LED Strip -->
		<div class="led-strip">
			<div class="led led-active"></div>
			<div class="led led-active"></div>
			<div class="led"></div>
		</div>

		<!-- Content -->
		<div class="rack-content">
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
	/* Settings Rack Unit - Dynamic Height */
	.settings-rack-unit {
		position: relative;
		background: linear-gradient(180deg, var(--bg-rack-nav) 0%, var(--bg-card) 100%);
		border-radius: 0.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		border-bottom: 2px solid rgba(0, 0, 0, 0.2);
		box-shadow: 
			0 4px 6px rgba(0, 0, 0, 0.3),
			inset 0 1px 0 rgba(255, 255, 255, 0.1),
			inset 0 -1px 0 rgba(0, 0, 0, 0.2);
		padding: 2rem 4rem;
		min-height: 400px;
		transition: all 0.3s ease;
	}

	/* Mounting Ears - Identical to RackCard */
	.rack-ear {
		position: absolute;
		top: 1.5rem;
		width: 2rem;
		height: calc(100% - 3rem);
		background: linear-gradient(90deg, #2a2a2a 0%, #1a1a1a 50%, #2a2a2a 100%);
		border: 1px solid rgba(0, 0, 0, 0.5);
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 0;
		z-index: 2;
	}

	.rack-ear-left {
		left: 0;
		border-radius: 0.25rem 0 0 0.25rem;
		border-right: none;
	}

	.rack-ear-right {
		right: 0;
		border-radius: 0 0.25rem 0.25rem 0;
		border-left: none;
	}

	/* Screws - Identical to RackCard */
	.screw {
		width: 0.625rem;
		height: 0.625rem;
		background: radial-gradient(circle, #4a4a4a 0%, #2a2a2a 70%);
		border-radius: 50%;
		border: 1px solid rgba(0, 0, 0, 0.8);
		position: relative;
		box-shadow: 
			inset 0 1px 2px rgba(255, 255, 255, 0.3),
			inset 0 -1px 2px rgba(0, 0, 0, 0.5);
	}

	.screw::before {
		content: '';
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 50%;
		height: 1px;
		background: rgba(0, 0, 0, 0.6);
	}

	.screw-top {
		margin-top: 0.5rem;
	}

	.screw-bottom {
		margin-bottom: 0.5rem;
	}

	/* LED Strip - Identical to RackCard */
	.led-strip {
		position: absolute;
		top: 1rem;
		right: 3rem;
		display: flex;
		gap: 0.25rem;
		z-index: 3;
	}

	.led {
		width: 0.5rem;
		height: 0.5rem;
		background: rgba(100, 100, 100, 0.3);
		border-radius: 50%;
		border: 1px solid rgba(0, 0, 0, 0.5);
		box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
	}

	.led-active {
		background: var(--color-led-active, #22c55e);
		box-shadow: 
			0 0 8px var(--color-led-active, #22c55e),
			inset 0 1px 2px rgba(255, 255, 255, 0.3);
		animation: pulse-led 2s ease-in-out infinite;
	}

	@keyframes pulse-led {
		0%, 100% {
			opacity: 1;
		}
		50% {
			opacity: 0.6;
		}
	}

	/* Content Area */
	.rack-content {
		position: relative;
		z-index: 1;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.settings-rack-unit {
			padding: 1.5rem 3rem;
		}

		.rack-ear {
			width: 1.5rem;
			padding: 0.75rem 0;
		}

		.led-strip {
			right: 2rem;
		}
	}
</style>
