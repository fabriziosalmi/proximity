<script>
	import { pageTitleStore } from '$lib/stores/pageTitle';
</script>

<header class="top-bar">
	<div class="left">
		<h1 class="page-title">{$pageTitleStore}</h1>
	</div>
</header>

<style>
	.top-bar {
		display: flex;
		align-items: center;
		background-color: var(--bg-top-bar, #1f2937);
		border-bottom: 1px solid var(--border-color-primary, #4b5563);
		padding: 0 1.5rem;
		height: 100%;
	}

	.left {
		display: flex;
		align-items: center;
		flex: 1;
	}

	.page-title {
		margin: 0;
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--color-text-primary, #e5e7eb);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
</style>
