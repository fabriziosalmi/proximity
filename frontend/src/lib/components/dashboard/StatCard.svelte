<!-- StatCard.svelte - Reusable metric display card -->
<!-- Theme-ready component for displaying statistics -->
<script lang="ts">
	import type { ComponentType } from 'svelte';

	export let label: string = '';
	export let title: string = ''; // Legacy support
	export let value: string | number;
	export let icon: ComponentType;
	export let variant: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'compact' = 'default';
	export let ledColor: string | undefined = undefined;
	export let testId: string | undefined = undefined;

	// Use label if provided, otherwise fallback to title
	$: displayLabel = label || title;
</script>

<div
	class="stat-card stat-card-{variant}"
	data-testid={testId || `stat-card-${displayLabel.toLowerCase().replace(/\s+/g, '-')}`}
>
	{#if variant === 'compact'}
		<!-- Compact variant for SystemOverviewRack -->
		<div class="stat-card-compact-content">
			<div class="stat-card-compact-header">
				<svelte:component this={icon} size={16} class="stat-card-compact-icon" />
				{#if ledColor}
					<div class="stat-card-led" style="background: {ledColor}; box-shadow: 0 0 8px {ledColor};"></div>
				{/if}
			</div>
			<div class="stat-card-compact-value">{value}</div>
			<div class="stat-card-compact-label">{displayLabel}</div>
		</div>
	{:else}
		<!-- Default variant -->
		<div class="stat-card-icon">
			<svelte:component this={icon} size={24} strokeWidth={2} />
		</div>
		<div class="stat-card-content">
			<div class="stat-card-title">{displayLabel}</div>
			<div class="stat-card-value">{value}</div>
		</div>
	{/if}
</div>

<style>
	/* Base StatCard Structure */
	.stat-card {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1.25rem 1.5rem;
		background: var(--card-bg-color);
		border: 1px solid var(--card-border-color);
		border-radius: 0.5rem;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.stat-card:hover {
		border-color: var(--border-color-primary);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		transform: translateY(-2px);
	}

	/* Icon Container */
	.stat-card-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 48px;
		height: 48px;
		border-radius: 0.5rem;
		background: rgba(255, 255, 255, 0.05);
		color: var(--text-color-primary);
		flex-shrink: 0;
	}

	/* Content Area */
	.stat-card-content {
		flex: 1;
		min-width: 0;
	}

	.stat-card-title {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text-color-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.25rem;
	}

	.stat-card-value {
		font-size: 1.875rem;
		font-weight: 700;
		color: var(--text-color-primary);
		line-height: 1.2;
	}

	/* Compact Variant Styles */
	.stat-card-compact {
		padding: 1rem;
		background: rgba(31, 41, 55, 0.5);
		border: 1px solid rgba(75, 85, 99, 0.3);
		min-height: 100px;
	}

	.stat-card-compact:hover {
		background: rgba(31, 41, 55, 0.8);
		border-color: rgba(59, 130, 246, 0.5);
	}

	.stat-card-compact-content {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.stat-card-compact-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.5rem;
	}

	.stat-card-compact-icon {
		color: var(--color-rack-primary, #3b82f6);
	}

	.stat-card-led {
		width: 0.5rem;
		height: 0.5rem;
		border-radius: 50%;
		animation: pulse-led 2s ease-in-out infinite;
	}

	.stat-card-compact-value {
		font-size: 2rem;
		font-weight: 700;
		color: white;
		line-height: 1;
		margin-bottom: 0.5rem;
	}

	.stat-card-compact-label {
		font-size: 0.75rem;
		font-weight: 500;
		color: var(--color-text-secondary, #9ca3af);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	/* Variant Styles */
	.stat-card-success .stat-card-icon {
		background: rgba(16, 185, 129, 0.1);
		color: #10b981;
	}

	.stat-card-warning .stat-card-icon {
		background: rgba(251, 191, 36, 0.1);
		color: #fbbf24;
	}

	.stat-card-danger .stat-card-icon {
		background: rgba(239, 68, 68, 0.1);
		color: #ef4444;
	}

	.stat-card-info .stat-card-icon {
		background: rgba(59, 130, 246, 0.1);
		color: #3b82f6;
	}
</style>
