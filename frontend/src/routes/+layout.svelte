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
		console.log('🎪 [RootLayout] Root +layout.svelte mounted - initializing app');
		
		// CRITICAL: Initialize authStore FIRST and WAIT for it to complete
		// This ensures the authentication state is fully resolved before any components
		// or stores make API calls, preventing race conditions and 401/422 errors
		console.log('🔐 [RootLayout] Calling authStore.init()...');
		await authStore.init(); // ⚠️ AWAIT is critical - don't proceed until auth is ready
		console.log('✅ [RootLayout] authStore.init() completed - auth state is now reliable');
		
		// Then initialize other services
		console.log('🎨 [RootLayout] Initializing ThemeService...');
		await ThemeService.init();
		console.log('✅ [RootLayout] ThemeService initialized');
		
		console.log('🎉 [RootLayout] All initialization complete');
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
