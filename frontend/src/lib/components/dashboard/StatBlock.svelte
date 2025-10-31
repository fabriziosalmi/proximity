<script lang="ts">
	/**
	 * StatBlock - Mini display per statistiche dashboard
	 * Design premium hardware con LED e bordi metallici
	 */
	import type { ComponentType } from 'svelte';

	export let label: string;
	export let value: number | string;
	export let icon: ComponentType;
	export let ledColor: string = 'var(--color-led-inactive)';
	export let borderColor: string = 'var(--border-color-primary)';
	export let pulse: boolean = false;
</script>

<div
	class="stat-block"
	style="--stat-border: {borderColor}; --stat-led: {ledColor};"
	data-testid="stat-block-{label.toLowerCase().replace(/\s+/g, '-')}"
>
	<!-- LED Indicator -->
	<div class="stat-led" class:led-pulse={pulse}></div>

	<!-- Icon -->
	<div class="stat-icon">
		<svelte:component this={icon} size={20} />
	</div>

	<!-- Content -->
	<div class="stat-content">
		<div class="stat-label">{label}</div>
		<div class="stat-value">{value}</div>
	</div>
</div>

<style>
	.stat-block {
		position: relative;
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1rem;
		background: var(--bg-card, #1f2937);
		border: 1px solid var(--stat-border);
		border-radius: 0.5rem;
		transition: all 0.2s ease;
		min-width: 140px;
	}

	.stat-block:hover {
		background: var(--bg-hover, #374151);
		border-color: var(--color-accent, #0ea5e9);
		box-shadow: 0 0 15px rgba(14, 165, 233, 0.15);
	}

	/* LED Indicator */
	.stat-led {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background-color: var(--stat-led);
		box-shadow: 0 0 8px var(--stat-led);
	}

	.stat-led.led-pulse {
		animation: pulse-glow 2s ease-in-out infinite;
	}

	@keyframes pulse-glow {
		0%, 100% {
			opacity: 1;
			box-shadow: 0 0 8px var(--stat-led);
		}
		50% {
			opacity: 0.6;
			box-shadow: 0 0 15px var(--stat-led);
		}
	}

	/* Icon */
	.stat-icon {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		border-radius: 0.375rem;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid var(--border-color-secondary, #374151);
		color: var(--color-accent, #0ea5e9);
	}

	/* Content */
	.stat-content {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
		flex: 1;
		min-width: 0;
	}

	.stat-label {
		font-size: 0.75rem;
		font-weight: 500;
		color: var(--color-text-secondary, #9ca3af);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--color-text-primary, #e5e7eb);
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}

	/* Responsive */
	@media (max-width: 640px) {
		.stat-block {
			min-width: 120px;
			padding: 0.75rem;
			gap: 0.5rem;
		}

		.stat-icon {
			width: 32px;
			height: 32px;
		}

		.stat-label {
			font-size: 0.625rem;
		}

		.stat-value {
			font-size: 1.25rem;
		}
	}
</style>
