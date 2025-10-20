<script>
	import { onMount } from 'svelte';
	import '../app.css';
	import ToastContainer from '$lib/components/ToastContainer.svelte';
	import CommandDeck from '$lib/components/layout/CommandDeck.svelte';
	import MasterControlRack from '$lib/components/layout/MasterControlRack.svelte';
	import { ThemeService } from '$lib/services/ThemeService';

	// Initialize theme on app startup
	onMount(async () => {
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
