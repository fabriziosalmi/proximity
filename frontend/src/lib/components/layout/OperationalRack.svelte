<script lang="ts">
	/**
	 * OperationalRack - 1U Operational Control Panel
	 * Contextual stats and actions for each page view
	 * Styled identically to RackCard for seamless visual integration
	 */
	import { onMount } from 'svelte';
	
	// Optional title prop for accessibility
	export let title: string = 'Operations';
</script>

<div class="operational-rack-container" data-testid="operational-rack">
	<div class="rack-unit">
		<!-- Left Mounting Ear -->
		<div class="mounting-ear mounting-ear-left">
			<div class="screw"></div>
		</div>

		<!-- Main Unit Body -->
		<div class="unit-body">
			<!-- Left Section: Stats Display -->
			<div class="stats-section">
				<slot name="stats" />
			</div>

			<!-- Right Section: Actions & Controls -->
			<div class="actions-section">
				<slot name="actions" />
			</div>
		</div>

		<!-- Right Mounting Ear -->
		<div class="mounting-ear mounting-ear-right">
			<div class="screw"></div>
		</div>
	</div>
</div>

<style>
	/* Main Container */
	.operational-rack-container {
		width: 100%;
		margin-bottom: 1rem;
	}

	/* Main Rack Unit - Identical to RackCard */
	.rack-unit {
		position: relative;
		display: flex;
		align-items: center;
		width: 100%;
		min-height: 7rem; /* 1U height */
		background: var(--bg-rack-nav, linear-gradient(to bottom, #374151, #1f2937));
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		border-bottom: 1px solid rgba(0, 0, 0, 0.3);
		box-shadow: 
			0 2px 4px rgba(0, 0, 0, 0.3),
			inset 0 1px 0 rgba(255, 255, 255, 0.05);
		transition: all 0.3s ease;
	}

	.rack-unit:hover {
		background: linear-gradient(to bottom, #3f4b5c, #242f3d);
	}

	/* Mounting Ears (Left & Right) */
	.mounting-ear {
		flex-shrink: 0;
		width: 1.5rem;
		height: 100%;
		background: linear-gradient(135deg, #2d3748, #1a202c);
		border: 1px solid rgba(0, 0, 0, 0.5);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		box-shadow: 
			inset 0 1px 2px rgba(255, 255, 255, 0.1),
			inset 0 -1px 2px rgba(0, 0, 0, 0.3);
	}

	.mounting-ear-left {
		border-radius: 0.25rem 0 0 0.25rem;
	}

	.mounting-ear-right {
		border-radius: 0 0.25rem 0.25rem 0;
	}

	/* Mounting Screws */
	.screw {
		width: 0.625rem;
		height: 0.625rem;
		border-radius: 50%;
		background: radial-gradient(circle at 30% 30%, #4a5568, #1a202c);
		border: 1px solid rgba(0, 0, 0, 0.4);
		box-shadow: 
			inset 0 1px 2px rgba(0, 0, 0, 0.5),
			0 1px 1px rgba(255, 255, 255, 0.1);
		position: relative;
	}

	.screw::before {
		content: '';
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 60%;
		height: 2px;
		background: rgba(0, 0, 0, 0.3);
	}

	/* Unit Body - Flexible content area */
	.unit-body {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 1.5rem;
		gap: 2rem;
		min-height: 7rem;
	}

	/* Stats Section (Left) */
	.stats-section {
		flex: 1;
		display: flex;
		align-items: center;
		gap: 1.5rem;
		min-width: 0; /* Allow flex shrinking */
	}

	/* Actions Section (Right) */
	.actions-section {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	/* Responsive: Stack on mobile */
	@media (max-width: 1024px) {
		.unit-body {
			flex-direction: column;
			align-items: stretch;
			padding: 1rem 1.5rem;
			gap: 1rem;
		}

		.stats-section {
			flex-wrap: wrap;
			justify-content: center;
		}

		.actions-section {
			justify-content: center;
			width: 100%;
		}
	}

	/* Match existing rack aesthetics */
	:global(.operational-rack-container) {
		/* Ensure proper spacing with other rack units */
		position: relative;
	}

	/* LED Strip Effect (optional accent) */
	.rack-unit::before {
		content: '';
		position: absolute;
		left: 1.5rem;
		top: 0.25rem;
		width: calc(100% - 3rem);
		height: 2px;
		background: linear-gradient(
			to right,
			transparent,
			var(--color-accent, #3b82f6) 20%,
			var(--color-accent, #3b82f6) 80%,
			transparent
		);
		opacity: 0.3;
	}
</style>
