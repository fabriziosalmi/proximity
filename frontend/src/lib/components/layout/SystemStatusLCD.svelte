<script>
	import { myAppsStore } from '$lib/stores/apps';

	let statusMessage = 'SYSTEM: NOMINAL';
	let statusColor = '#4ade80'; // Green for nominal

	$: {
		// Find deploying or cloning apps
		const deployingApps = $myAppsStore.apps.filter(
			(app) => app.status === 'deploying' || app.status === 'cloning'
		);

		if (deployingApps.length > 0) {
			const app = deployingApps[0];
			const action = app.status === 'deploying' ? 'DEPLOYING' : 'CLONING';
			statusMessage = `${action}: ${app.hostname.toUpperCase()}...`;
			statusColor = '#fbbf24'; // Yellow/amber for activity
		} else {
			statusMessage = 'SYSTEM: NOMINAL';
			statusColor = '#4ade80'; // Green for nominal
		}
	}
</script>

<div class="lcd-container">
	<div class="lcd" style="color: {statusColor}">
		{statusMessage}
	</div>
	<div class="scanline"></div>
</div>

<style>
	.lcd-container {
		position: relative;
		overflow: hidden;
		border-radius: 0.25rem;
	}

	.lcd {
		background-color: #000000;
		font-family: 'Courier New', 'Consolas', monospace;
		font-size: 0.75rem;
		padding: 0.5rem 1rem;
		border-radius: 0.25rem;
		border: 1px solid #1f2937;
		box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.6);
		animation: lcd-flicker 3s ease-in-out infinite;
		transition: color 0.3s ease;
		position: relative;
		z-index: 1;
	}

	/* CRT Scanline Effect */
	.scanline {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 2px;
		background: linear-gradient(
			to bottom,
			transparent 0%,
			rgba(255, 255, 255, 0.1) 50%,
			transparent 100%
		);
		animation: scanline-move 4s linear infinite;
		pointer-events: none;
		z-index: 2;
	}

	@keyframes scanline-move {
		0% {
			transform: translateY(-100%);
			opacity: 0;
		}
		10% {
			opacity: 0.3;
		}
		90% {
			opacity: 0.3;
		}
		100% {
			transform: translateY(calc(100vh));
			opacity: 0;
		}
	}

	@keyframes lcd-flicker {
		0%,
		100% {
			opacity: 1;
		}
		98% {
			opacity: 1;
		}
		99% {
			opacity: 0.95;
		}
	}
</style>
