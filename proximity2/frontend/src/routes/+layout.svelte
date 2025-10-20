<script>
	import { onMount } from 'svelte';
	import '../app.css';
	import ToastContainer from '$lib/components/ToastContainer.svelte';
	import CommandDeck from '$lib/components/layout/CommandDeck.svelte';
	import RackNav from '$lib/components/layout/RackNav.svelte';
	import TopBar from '$lib/components/layout/TopBar.svelte';
	import { ThemeService } from '$lib/services/ThemeService';

	// Initialize theme on app startup
	onMount(async () => {
		await ThemeService.init();
	});
</script>

<ToastContainer />

<CommandDeck>
	<svelte:fragment slot="rack-nav">
		<RackNav />
	</svelte:fragment>
	<svelte:fragment slot="top-bar">
		<TopBar />
	</svelte:fragment>
	<svelte:fragment slot="main-canvas">
		<slot />
	</svelte:fragment>
</CommandDeck>
