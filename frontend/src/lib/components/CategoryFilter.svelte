<script lang="ts">
	/**
	 * CategoryFilter - Minimal filter bar for app categories
	 * Simple horizontal button row, no decorative wrapper
	 */
	import { Check } from 'lucide-svelte';

	export let categories: string[] = [];
	export let selectedCategory: string | null = null;
	export let onCategorySelect: (category: string | null) => void = () => {};

	function handleCategoryClick(category: string | null) {
		selectedCategory = category;
		onCategorySelect(category);
	}
</script>

<!-- Simple horizontal filter bar -->
<div class="category-filter-bar">
	<!-- All categories option -->
	<button
		on:click={() => handleCategoryClick(null)}
		class="category-button {selectedCategory === null ? 'active' : ''}"
	>
		<span class="category-label">All Apps</span>
		{#if selectedCategory === null}
			<Check class="h-4 w-4" />
		{/if}
	</button>

	<!-- Individual categories -->
	{#each categories as category}
		<button
			on:click={() => handleCategoryClick(category)}
			class="category-button {selectedCategory === category ? 'active' : ''}"
		>
			<span class="category-label capitalize">{category}</span>
			{#if selectedCategory === category}
				<Check class="h-4 w-4" />
			{/if}
		</button>
	{/each}
</div>

<style>
	/* Filter Bar Container */
	.category-filter-bar {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		align-items: center;
		width: 100%;
	}

	/* Category Buttons - Identical to NavigationRack style */
	.category-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		border-radius: 0.25rem;
		border: 1px solid rgba(75, 85, 99, 0.3);
		background: rgba(31, 41, 55, 0.5);
		color: var(--color-text-secondary, #9ca3af);
		font-size: 0.875rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.2s ease;
		cursor: pointer;
		flex-shrink: 0;
	}

	.category-button:hover {
		background: rgba(31, 41, 55, 0.8);
		border-color: rgba(59, 130, 246, 0.5);
		color: var(--color-text-primary, #e5e7eb);
		box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
	}

	.category-button.active {
		background: rgba(0, 212, 255, 0.15);
		border-color: var(--color-accent-bright, #00d4ff);
		color: var(--color-text-primary, #e5e7eb);
		box-shadow: 0 0 12px rgba(0, 212, 255, 0.4);
	}

	.category-label {
		white-space: nowrap;
	}

	/* Mobile: Stack vertically */
	@media (max-width: 768px) {
		.category-filter-bar {
			flex-direction: column;
			align-items: stretch;
		}

		.category-button {
			width: 100%;
			justify-content: space-between;
		}
	}
</style>
