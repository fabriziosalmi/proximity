<script>
	import { onMount } from 'svelte';
	import '../app.css';
	import ToastContainer from '$lib/components/ToastContainer.svelte';
	import CommandDeck from '$lib/components/layout/CommandDeck.svelte';
	import MasterControlRack from '$lib/components/layout/MasterControlRack.svelte';
	import { ThemeService } from '$lib/services/ThemeService';
	import { authStore } from '$lib/stores/auth';

	// Initialize app on startup
	onMount(async () => {
		// CRITICAL: Initialize authStore FIRST to establish single source of truth
		// This must happen before any API calls or component interactions
		authStore.init();
		
		// Then initialize other services
		await ThemeService.init();
	});
</script>

<ToastContainer />

<CommandDeck>
	<svelte:fragment slot="rack-nav">
		<!-- Mobile-only vertical navigation rack (integrated in MasterControlRack) -->
		<MasterControlRack />
	</svelte:fragment>
	<svelte:fragment slot="top-bar">
		<!-- TopBar ELIMINATED - functionality merged into MasterControlRack -->
	</svelte:fragment>
	<svelte:fragment slot="main-canvas">
		<!-- Main content area - MasterControlRack will be sticky at top -->
		<slot />
	</svelte:fragment>
</CommandDeck>
