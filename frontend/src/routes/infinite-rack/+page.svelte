<!-- Infinite Rack PoC - 3D Scrollable Rack Visualization -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import InfiniteRack from '$lib/components/dashboard/InfiniteRack.svelte';

	onMount(() => {
		pageTitleStore.setTitle('Infinite Rack - PoC');
	});
</script>

<svelte:head>
	<title>Infinite Rack PoC - Proximity</title>
</svelte:head>

<div class="w-full h-screen bg-slate-950">
	<InfiniteRack />
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		overflow: hidden;
	}
</style>
