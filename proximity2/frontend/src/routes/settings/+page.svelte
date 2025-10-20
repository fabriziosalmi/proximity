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

<div class="bg-rack-darker">
	<!-- STICKY HEADER: Always-Visible Control Surface -->
	<header class="sticky-header">
		<!-- Desktop Navigation Rack (visible only on lg: screens) -->
		<div class="px-6 pt-6">
			<NavigationRack />
		</div>

		<!-- Operational Control Panel -->
		<div class="px-6 pb-6">
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

				<div slot="actions" class="settings-nav-container">
					{#each tabs as tab}
						<button
							on:click={() => switchTab(tab.id)}
							data-testid="tab-{tab.id}"
							class="settings-nav-button"
							class:settings-nav-button-active={activeTab === tab.id}
						>
							<svelte:component this={tab.icon} class="h-5 w-5" />
							<span class="settings-nav-label">{tab.label}</span>
							<div class="settings-nav-indicator" class:active={activeTab === tab.id}></div>
						</button>
					{/each}
				</div>
			</OperationalRack>
		</div>
	</header>
	<!-- END: Sticky Header -->

	<!-- MAIN: Scrollable Content -->
	<main class="px-10 pt-6 pb-6">
		<!-- Settings Content Panel - Rack Unit Style -->
	<div class="settings-rack-unit">
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
	</main>
	<!-- END: Main Scrollable Content -->
</div>

<style>
	/* Settings Rack Unit - Match RackCard exact styling */
	.settings-rack-unit {
		position: relative;
		/* No width specified - fills available space naturally */
		min-height: 400px;
		/* Match RackCard exact background and border */
		background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 50%, #1a1a1a 100%);
		border: 2px solid rgba(75, 85, 99, 0.4);
		border-radius: 0.5rem;
		padding: 2rem 4rem;
		box-shadow: 
			0 4px 6px rgba(0, 0, 0, 0.3),
			0 10px 30px rgba(0, 0, 0, 0.5),
			inset 0 1px 0 rgba(255, 255, 255, 0.05),
			inset 0 -1px 0 rgba(0, 0, 0, 0.5);
		transition: all 0.3s ease;
	}

	/* Mounting Ears - Match RackCard exact styling */
	.rack-ear {
		position: absolute;
		top: 0;
		width: 2rem; /* Match RackCard width */
		height: 100%;
		/* Match RackCard exact ear gradient */
		background: linear-gradient(180deg, #3a3a3a 0%, #2a2a2a 50%, #1a1a1a 100%);
		border: 1px solid rgba(0, 0, 0, 0.8);
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 0;
		z-index: 2;
		/* Match RackCard shadow */
		box-shadow: 
			inset 1px 0 2px rgba(255, 255, 255, 0.1),
			inset -1px 0 2px rgba(0, 0, 0, 0.5);
	}

	.rack-ear-left {
		left: 0;
		border-radius: 0.5rem 0 0 0.5rem; /* Match outer border-radius */
		border-right: none;
	}

	.rack-ear-right {
		right: 0;
		border-radius: 0 0.5rem 0.5rem 0; /* Match outer border-radius */
		border-left: none;
	}

	/* Screws - Match RackCard exact screw styling */
	.screw {
		width: 0.625rem;
		height: 0.625rem;
		background: radial-gradient(circle, #4a4a4a 0%, #2a2a2a 70%);
		border-radius: 50%;
		border: 1px solid rgba(0, 0, 0, 0.8);
		box-shadow: 
			inset 0 1px 2px rgba(255, 255, 255, 0.3),
			inset 0 -1px 2px rgba(0, 0, 0, 0.5);
		position: relative;
	}

	.screw::before {
		content: '';
		position: absolute;
		width: 50%;
		height: 1px;
		background: rgba(0, 0, 0, 0.6);
		left: 25%;
		top: 50%;
		transform: translateY(-50%);
	}

	.screw-top {
		/* Remove custom margin - space-between handles it */
	}

	.screw-bottom {
		/* Remove custom margin - space-between handles it */
	}

	/* LED Strip - Match RackCard exact positioning */
	.led-strip {
		position: absolute;
		top: 0.75rem; /* Match RackCard positioning */
		right: 2.5rem;
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

	/* Settings Navigation Container - Force horizontal layout */
	.settings-nav-container {
		display: flex !important;
		flex-direction: row !important;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
	}

	/* Settings Navigation Buttons - Identical to NavigationRack */
	.settings-nav-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		border-radius: 0.25rem;
		border: 1px solid rgba(75, 85, 99, 0.3);
		background: rgba(31, 41, 55, 0.5);
		color: var(--color-text-secondary, #9ca3af);
		text-decoration: none;
		font-size: 0.875rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.2s ease;
		position: relative;
		cursor: pointer;
		flex-shrink: 0;
	}

	.settings-nav-button:hover {
		background: rgba(31, 41, 55, 0.8);
		border-color: rgba(59, 130, 246, 0.5);
		color: var(--color-text-primary, #e5e7eb);
		box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
	}

	.settings-nav-button-active {
		background: rgba(0, 212, 255, 0.15);
		border-color: var(--color-accent-bright, #00d4ff);
		color: var(--color-text-primary, #e5e7eb);
		box-shadow: 0 0 12px rgba(0, 212, 255, 0.4);
	}

	.settings-nav-label {
		white-space: nowrap;
	}

	.settings-nav-indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--color-led-inactive, #374151);
		transition: all 0.3s ease;
		margin-left: auto;
	}

	.settings-nav-indicator.active {
		background: var(--color-led-active, #4ade80);
		box-shadow: 0 0 8px var(--color-led-active, #4ade80);
		animation: pulse-led 2s ease-in-out infinite;
	}
</style>
