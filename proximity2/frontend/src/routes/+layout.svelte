<script lang="ts">
	import { onMount } from 'svelte';
	import '../app.css';
	import ToastContainer from '$lib/components/ToastContainer.svelte';

	onMount(() => {
		console.log('[Layout] SvelteKit hydration complete, marking body as interactive');
		document.body.setAttribute('data-sveltekit-interactive', 'true');
	});
</script>

<ToastContainer />

<slot />
