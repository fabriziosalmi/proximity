<script lang="ts">
	/**
	 * EmptyRackCard - Reusable Bare Metal Rack Display
	 * Shows when no items exist (apps, hosts, etc.)
	 */
	import { Server } from 'lucide-svelte';

	export let label: string = 'NO ITEMS';
	export let buttonText: string = 'ADD ITEM';
	export let buttonHref: string = '/';
	export let icon: any = Server;
</script>

<div class="empty-rack-container">
	<!-- Mounting Ear Left -->
	<div class="mounting-ear mounting-ear-left">
		<div class="screw screw-top"></div>
		<div class="screw screw-bottom"></div>
	</div>

	<!-- Empty Rack Body -->
	<div class="empty-rack-body">
		<div class="empty-rack-content">
			<div class="rack-label">{label}</div>
			<a href={buttonHref} class="install-button">
				<svelte:component this={icon} class="h-5 w-5" />
				<span>{buttonText}</span>
			</a>
		</div>
	</div>

	<!-- Mounting Ear Right -->
	<div class="mounting-ear mounting-ear-right">
		<div class="screw screw-top"></div>
		<div class="screw screw-bottom"></div>
	</div>
</div>

<style>
	/* ============================================ */
	/* EMPTY RACK CARD - BARE METAL STYLE */
	/* ============================================ */
	.empty-rack-container {
		display: flex;
		align-items: stretch;
		width: 100%;
		min-height: 200px;
		margin-bottom: 1.5rem;
		position: relative;
	}

	/* Mounting Ears - Same as RackCard */
	.mounting-ear {
		width: 2.5rem;
		background: linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 0;
		position: relative;
		flex-shrink: 0;
	}

	.mounting-ear-left {
		border-radius: 0.5rem 0 0 0.5rem;
		border-right: none;
	}

	.mounting-ear-right {
		border-radius: 0 0.5rem 0.5rem 0;
		border-left: none;
	}

	/* Screws */
	.screw {
		width: 0.875rem;
		height: 0.875rem;
		border-radius: 50%;
		background: radial-gradient(circle at 30% 30%, #4a5568, #1a202c);
		border: 1px solid rgba(255, 255, 255, 0.15);
		position: relative;
		box-shadow:
			inset 0 1px 2px rgba(0, 0, 0, 0.5),
			0 1px 1px rgba(255, 255, 255, 0.1);
	}

	.screw::before {
		content: '';
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 60%;
		height: 2px;
		background: rgba(0, 0, 0, 0.6);
		box-shadow: 0 1px 0 rgba(255, 255, 255, 0.1);
	}

	.screw-top {
		margin-top: 0.5rem;
	}

	.screw-bottom {
		margin-bottom: 0.5rem;
	}

	/* Empty Rack Body */
	.empty-rack-body {
		flex: 1;
		background: linear-gradient(180deg, #1a1a1a 0%, #0f0f0f 100%);
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 3rem;
		position: relative;
		overflow: hidden;
	}

	/* Subtle grid pattern */
	.empty-rack-body::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-image:
			linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
			linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
		background-size: 20px 20px;
		pointer-events: none;
		opacity: 0.3;
	}

	.empty-rack-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1.5rem;
		z-index: 1;
	}

	/* Rack Label - Industrial style */
	.rack-label {
		font-family: 'Courier New', monospace;
		font-size: 1.25rem;
		font-weight: 700;
		letter-spacing: 0.15em;
		color: #4a5568;
		text-shadow:
			0 1px 2px rgba(0, 0, 0, 0.8),
			0 0 10px rgba(74, 85, 104, 0.3);
		padding: 0.5rem 1.5rem;
		border: 2px solid rgba(74, 85, 104, 0.3);
		border-radius: 0.25rem;
		background: rgba(0, 0, 0, 0.3);
	}

	/* Install Button - Rack style */
	.install-button {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.875rem 2rem;
		font-family: 'Courier New', monospace;
		font-size: 0.95rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-decoration: none;
		color: #0ea5e9;
		background: linear-gradient(180deg, rgba(14, 165, 233, 0.15) 0%, rgba(14, 165, 233, 0.05) 100%);
		border: 2px solid rgba(14, 165, 233, 0.4);
		border-radius: 0.375rem;
		transition: all 0.2s ease;
		position: relative;
		overflow: hidden;
	}

	.install-button::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.2), transparent);
		transition: left 0.5s ease;
	}

	.install-button:hover {
		border-color: rgba(14, 165, 233, 0.8);
		background: linear-gradient(180deg, rgba(14, 165, 233, 0.25) 0%, rgba(14, 165, 233, 0.15) 100%);
		box-shadow:
			0 0 20px rgba(14, 165, 233, 0.3),
			inset 0 1px 2px rgba(255, 255, 255, 0.1);
		transform: translateY(-1px);
	}

	.install-button:hover::before {
		left: 100%;
	}

	.install-button:active {
		transform: translateY(0);
		box-shadow:
			0 0 10px rgba(14, 165, 233, 0.2),
			inset 0 1px 3px rgba(0, 0, 0, 0.3);
	}
</style>
