<script lang="ts">
	/**
	 * RackCard - 1U Rack-Mounted Server Unit with 3D Flip
	 * Skeuomorphic design resembling physical rack hardware
	 */
	import { onMount } from 'svelte';
	import { Package, Server, AlertCircle, Info, X, Cpu, MemoryStick, HardDrive } from 'lucide-svelte';
	import { SoundService } from '$lib/services/SoundService';
	import { flipCard } from '$lib/stores/actions';

	export let app: any;
	export let variant: 'catalog' | 'deployed' = 'catalog';

	// Flip state
	let isFlipped = false;

	function toggleFlip() {
		isFlipped = !isFlipped;
		flipCard(); // Use centralized action for sound feedback
	}

	// Initialize sound service on mount
	onMount(() => {
		SoundService.init();
	});

	// Determine LED color based on status
	function getLEDColor(status: string): string {
		const colors: Record<string, string> = {
			deploying: 'var(--color-led-warning)',
			cloning: 'var(--color-accent)',
			running: 'var(--color-led-active)',
			stopped: 'var(--color-led-inactive)',
			error: 'var(--color-led-danger)',
			deleting: '#ef4444'
		};
		return colors[status] || 'var(--color-led-inactive)';
	}

	// Determine if LED should pulse
	function shouldPulse(status: string): boolean {
		return status === 'deploying' || status === 'cloning' || status === 'running';
	}

	// Get box-shadow for status
	function getStatusGlow(status: string): string {
		if (status === 'deploying') {
			return 'pulse-yellow-glow 2s ease-in-out infinite';
		} else if (status === 'cloning') {
			return 'pulse-blue-glow 2s ease-in-out infinite';
		}
		return '';
	}

	// Calculate percentage
	function calculatePercent(used?: number, total?: number): number {
		if (!used || !total) return 0;
		return Math.round((used / total) * 100);
	}

	// Format percentage for display
	function formatPercent(value?: number): string {
		if (value === undefined || value === null) return '--';
		return `${Math.round(value)}%`;
	}

	$: ledColor = variant === 'deployed' ? getLEDColor(app.status) : '#4b5563';
	$: ledPulse = variant === 'deployed' ? shouldPulse(app.status) : false;
	$: statusGlow = variant === 'deployed' ? getStatusGlow(app.status) : '';
	$: cpuPercent = app.cpu_usage || 0;
	$: memoryPercent = calculatePercent(app.memory_used, app.memory_total);
	$: diskPercent = calculatePercent(app.disk_used, app.disk_total);
</script>

<div
	data-testid={variant === 'deployed' ? `rack-card-${app.hostname}` : `catalog-card-${app.id}`}
	data-hostname={variant === 'deployed' ? app.hostname : undefined}
	data-app-id={app.id}
	data-status={variant === 'deployed' ? app.status : undefined}
	class="card-container"
	class:is-flipped={isFlipped}
	style="animation: {statusGlow};"
>
	<div class="card-inner">
		<!-- FRONT FACE -->
		<div class="card-front">
			<div class="rack-unit">
				<!-- Left Mounting Ear -->
				<div class="mounting-ear mounting-ear-left">
					<div class="screw"></div>
				</div>

				<!-- Main Unit Body -->
				<div class="unit-body">
					<!-- Left Section: LED and Icon -->
					<div class="unit-left">
						<!-- Status LED -->
						<div
							class="led-indicator"
							style="background-color: {ledColor};"
							class:led-pulse={ledPulse}
						></div>

						<!-- App Icon -->
						<div class="app-icon">
							{#if app.icon}
								<img src={app.icon} alt="{app.name} icon" class="h-8 w-8" />
							{:else if variant === 'deployed'}
								<Server class="h-6 w-6 text-gray-400" />
							{:else}
								<Package class="h-6 w-6 text-gray-400" />
							{/if}
						</div>
					</div>

					<!-- Center Section: App Info -->
					<div class="unit-center">
						<div class="app-name" data-testid="app-name">{app.name}</div>
						{#if variant === 'deployed' && app.hostname}
							<div class="app-hostname" data-testid="app-hostname">{app.hostname}</div>
						{/if}
						{#if app.category}
							<div class="app-category">{app.category}</div>
						{/if}
						{#if variant === 'catalog' && app.description}
							<div class="app-description">{app.description}</div>
						{/if}
						{#if variant === 'deployed' && app.node_name}
							<div class="app-meta">
								<span class="meta-label">Node:</span>
								<span class="meta-value">{app.node_name}</span>
							</div>
						{/if}
					</div>

					<!-- Center-Right Section: Resource Gauges (only for running deployed apps) -->
					{#if variant === 'deployed' && app.status === 'running'}
						<div class="unit-stats">
							<!-- CPU Usage -->
							<div class="stat-gauge">
								<div class="stat-header">
									<Cpu size={14} class="stat-icon" />
									<span class="stat-label">CPU</span>
								</div>
								<div class="progress-bar">
									<div
										class="progress-fill"
										class:progress-warn={cpuPercent >= 70 && cpuPercent < 90}
										class:progress-danger={cpuPercent >= 90}
										style="width: {cpuPercent}%"
									></div>
								</div>
								<span class="stat-value">{formatPercent(cpuPercent)}</span>
							</div>

							<!-- Memory Usage -->
							<div class="stat-gauge">
								<div class="stat-header">
									<MemoryStick size={14} class="stat-icon" />
									<span class="stat-label">RAM</span>
								</div>
								<div class="progress-bar">
									<div
										class="progress-fill"
										class:progress-warn={memoryPercent >= 70 && memoryPercent < 90}
										class:progress-danger={memoryPercent >= 90}
										style="width: {memoryPercent}%"
									></div>
								</div>
								<span class="stat-value">{formatPercent(memoryPercent)}</span>
							</div>

							<!-- Disk Usage -->
							<div class="stat-gauge">
								<div class="stat-header">
									<HardDrive size={14} class="stat-icon" />
									<span class="stat-label">DISK</span>
								</div>
								<div class="progress-bar">
									<div
										class="progress-fill"
										class:progress-warn={diskPercent >= 70 && diskPercent < 90}
										class:progress-danger={diskPercent >= 90}
										style="width: {diskPercent}%"
									></div>
								</div>
								<span class="stat-value">{formatPercent(diskPercent)}</span>
							</div>
						</div>
					{/if}

					<!-- Right Section: Status Badge, Fans, and Actions -->
					<div class="unit-right">
						<!-- Status Badge for Deployed Apps -->
						{#if variant === 'deployed' && app.status}
							<div class="status-display" data-testid="app-status-badge" data-status={app.status}>
								{#if app.status === 'deploying'}
									<div class="status-icon status-spinning"></div>
								{:else if app.status === 'cloning'}
									<div
										class="status-icon status-spinning"
										style="border-color: var(--color-accent);"
									></div>
								{:else if app.status === 'running'}
									<div class="status-dot" style="background-color: var(--color-led-active);"></div>
								{:else if app.status === 'error'}
									<AlertCircle class="h-4 w-4 text-red-400" />
								{/if}
								<span class="status-text">{app.status}</span>
							</div>
						{/if}

						<!-- Decorative Cooling Fans (only for running apps) -->
						{#if variant === 'deployed' && app.status === 'running'}
							<div class="cooling-fans">
								<div class="fan"></div>
								<div class="fan"></div>
							</div>
						{/if}

						<!-- Flip Button (for deployed apps only) -->
						{#if variant === 'deployed'}
							<button
								class="flip-button"
								on:click={toggleFlip}
								data-testid="flip-button"
								aria-label="Show technical details"
							>
								<Info size={16} />
							</button>
						{/if}

						<!-- Action Buttons -->
						<div class="unit-actions">
							<slot name="actions" />
						</div>
					</div>
				</div>

				<!-- Right Mounting Ear -->
				<div class="mounting-ear mounting-ear-right">
					<div class="screw"></div>
				</div>
			</div>
		</div>

		<!-- BACK FACE -->
		<div class="card-back">
			<div class="rack-unit rack-unit-back">
				<!-- Left Mounting Ear -->
				<div class="mounting-ear mounting-ear-left">
					<div class="screw"></div>
				</div>

				<!-- Main Unit Body - Back Side -->
				<div class="unit-body">
					<!-- Back Header -->
					<div class="back-header">
						<div class="back-title">Technical Specifications</div>
						<button
							class="back-close-button"
							on:click={toggleFlip}
							data-testid="close-flip-button"
							aria-label="Return to front view"
						>
							<X size={16} />
						</button>
					</div>

					<!-- Technical Details Grid -->
					<div class="tech-details">
						{#if app.vmid}
							<div class="tech-item">
								<span class="tech-label">VMID:</span>
								<span class="tech-value">{app.vmid}</span>
							</div>
						{/if}
						{#if app.node_name}
							<div class="tech-item">
								<span class="tech-label">Node:</span>
								<span class="tech-value">{app.node_name}</span>
							</div>
						{/if}
						{#if app.internal_ip}
							<div class="tech-item">
								<span class="tech-label">Internal IP:</span>
								<span class="tech-value">{app.internal_ip}</span>
							</div>
						{/if}
						{#if app.config?.cores}
							<div class="tech-item">
								<span class="tech-label">CPU Cores:</span>
								<span class="tech-value">{app.config.cores}</span>
							</div>
						{/if}
						{#if app.config?.memory}
							<div class="tech-item">
								<span class="tech-label">Memory:</span>
								<span class="tech-value">{app.config.memory} MB</span>
							</div>
						{/if}
						{#if app.config?.disk}
							<div class="tech-item">
								<span class="tech-label">Disk Size:</span>
								<span class="tech-value">{app.config.disk} GB</span>
							</div>
						{/if}
						{#if app.catalog_app_id}
							<div class="tech-item">
								<span class="tech-label">Catalog ID:</span>
								<span class="tech-value">{app.catalog_app_id}</span>
							</div>
						{/if}
						{#if app.created_at}
							<div class="tech-item">
								<span class="tech-label">Created:</span>
								<span class="tech-value">{new Date(app.created_at).toLocaleDateString()}</span>
							</div>
						{/if}

						<!-- Ports Mapping -->
						{#if app.ports && Object.keys(app.ports).length > 0}
							<div class="tech-section">
								<span class="tech-label">Ports:</span>
								<div class="tech-mappings">
									{#each Object.entries(app.ports) as [key, value]}
										<div class="mapping-item">
											<span class="mapping-key">{key}:</span>
											<span class="mapping-value">{value}</span>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Environment Variables -->
						{#if app.environment && Object.keys(app.environment).length > 0}
							<div class="tech-section">
								<span class="tech-label">Environment:</span>
								<div class="tech-mappings">
									{#each Object.entries(app.environment) as [key, value]}
										<div class="mapping-item">
											<span class="mapping-key">{key}:</span>
											<span class="mapping-value">{value}</span>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Volumes -->
						{#if app.volumes && Object.keys(app.volumes).length > 0}
							<div class="tech-section">
								<span class="tech-label">Volumes:</span>
								<div class="tech-mappings">
									{#each Object.entries(app.volumes) as [key, value]}
										<div class="mapping-item">
											<span class="mapping-key">{key}:</span>
											<span class="mapping-value">{value}</span>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<!-- View Details Button (deployed apps only) -->
						{#if variant === 'deployed'}
							<div class="view-details-container">
								<a href="/apps/{app.id}" class="view-details-button">
									View Full Details & Backups
								</a>
							</div>
						{/if}
					</div>
				</div>

				<!-- Right Mounting Ear -->
				<div class="mounting-ear mounting-ear-right">
					<div class="screw"></div>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	/* ====== 3D FLIP ANIMATION ====== */
	.card-container {
		perspective: 1500px;
		width: 100%;
		position: relative;
	}

	.card-inner {
		position: relative;
		width: 100%;
		transition: transform 0.7s cubic-bezier(0.4, 0.0, 0.2, 1);
		transform-style: preserve-3d;
	}

	.card-container.is-flipped .card-inner {
		transform: rotateY(180deg);
	}

	.card-front,
	.card-back {
		width: 100%;
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
	}

	.card-front {
		position: relative;
		z-index: 2;
		transform: rotateY(0deg);
	}

	.card-back {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		transform: rotateY(180deg);
	}

	/* ====== SMOOTH STATE TRANSITIONS ====== */

	/* Main Rack Unit Container */
	.rack-unit {
		position: relative;
		display: flex;
		align-items: center;
		width: 100%;
		height: 7rem; /* 1U height */
		background: var(--bg-rack-nav, linear-gradient(to bottom, #374151, #1f2937));
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		border-bottom: 1px solid rgba(0, 0, 0, 0.3);
		transition: all 0.3s ease;
	}

	.rack-unit:hover {
		background: linear-gradient(to bottom, #3f4b5c, #242f3d);
	}

	.rack-unit-back {
		background: linear-gradient(to bottom, #1a202c, #0f1419);
	}

	.rack-unit-back:hover {
		background: linear-gradient(to bottom, #1f2937, #111827);
	}

	/* Mounting Ears (Rack Brackets) */
	.mounting-ear {
		position: relative;
		width: 2rem;
		height: 100%;
		background: linear-gradient(to right, #2d3748, #1a202c);
		border-right: 1px solid rgba(0, 0, 0, 0.3);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.mounting-ear-right {
		border-right: none;
		border-left: 1px solid rgba(0, 0, 0, 0.3);
		background: linear-gradient(to left, #2d3748, #1a202c);
	}

	/* Mounting Screws */
	.screw {
		width: 10px;
		height: 10px;
		background: radial-gradient(circle, #4b5563 0%, #1f2937 70%);
		border-radius: 50%;
		border: 1px solid #0f172a;
		box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
		position: relative;
	}

	.screw::after {
		content: '';
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 60%;
		height: 1px;
		background: #0f172a;
	}

	/* Main Unit Body */
	.unit-body {
		flex: 1;
		height: 100%;
		display: flex;
		align-items: center;
		padding: 0 1rem;
		gap: 1rem;
	}

	/* Left Section: LED and Icon */
	.unit-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-shrink: 0;
	}

	.led-indicator {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		box-shadow: 0 0 8px currentColor;
		/* Smooth LED color fade */
		transition: background-color 0.6s ease, box-shadow 0.6s ease;
	}

	.led-pulse {
		animation: pulse-green 2s ease-in-out infinite;
	}

	/* Smooth glow effects with fade in/out */
	@keyframes pulse-yellow-glow {
		0%,
		100% {
			box-shadow: 0 0 15px rgba(234, 179, 8, 0.4);
			opacity: 1;
		}
		50% {
			box-shadow: 0 0 30px rgba(234, 179, 8, 0.7);
			opacity: 0.95;
		}
	}

	@keyframes pulse-blue-glow {
		0%,
		100% {
			box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
			opacity: 1;
		}
		50% {
			box-shadow: 0 0 30px rgba(59, 130, 246, 0.7);
			opacity: 0.95;
		}
	}

	/* Smooth LED pulse animation */
	@keyframes pulse-green {
		0%,
		100% {
			opacity: 1;
			box-shadow: 0 0 8px currentColor;
		}
		50% {
			opacity: 0.6;
			box-shadow: 0 0 4px currentColor;
		}
	}

	.app-icon {
		width: 2.5rem;
		height: 2.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 0.375rem;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	/* Center Section: App Info */
	.unit-center {
		flex: 1;
		min-width: 0; /* Allow text truncation */
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.app-name {
		font-size: 1rem;
		font-weight: 600;
		color: var(--color-text-primary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.app-hostname {
		font-size: 0.75rem;
		font-family: 'Courier New', monospace;
		color: var(--color-accent-bright);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.app-category {
		font-size: 0.625rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-secondary);
	}

	.app-description {
		font-size: 0.75rem;
		color: var(--color-text-secondary);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		line-height: 1.3;
	}

	.app-meta {
		font-size: 0.625rem;
		color: var(--color-text-secondary);
		display: flex;
		gap: 0.5rem;
	}

	.meta-label {
		font-weight: 600;
	}

	.meta-value {
		font-family: 'Courier New', monospace;
		color: var(--color-text-primary);
	}

	/* Resource Stats Section */
	.unit-stats {
		flex: 1;
		display: flex;
		gap: 1.5rem;
		align-items: center;
		padding: 0 1rem;
	}

	.stat-gauge {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		min-width: 0;
	}

	.stat-header {
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}

	.stat-icon {
		color: var(--color-text-secondary);
		flex-shrink: 0;
	}

	.stat-label {
		font-size: 0.625rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-secondary);
	}

	.progress-bar {
		height: 4px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 2px;
		overflow: hidden;
		border: 1px solid rgba(255, 255, 255, 0.05);
	}

	.progress-fill {
		height: 100%;
		background: var(--color-led-active);
		transition: width 0.3s ease, background-color 0.3s ease;
		box-shadow: 0 0 8px var(--color-led-active);
	}

	.progress-fill.progress-warn {
		background: var(--color-led-warning);
		box-shadow: 0 0 8px var(--color-led-warning);
	}

	.progress-fill.progress-danger {
		background: var(--color-led-danger);
		box-shadow: 0 0 8px var(--color-led-danger);
	}

	.stat-value {
		font-size: 0.625rem;
		font-family: 'Courier New', monospace;
		color: var(--color-accent-bright);
		font-weight: 600;
	}

	/* Right Section: Status and Actions */
	.unit-right {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-shrink: 0;
	}

	.status-display {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.25rem 0.625rem;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 0.25rem;
	}

	.status-text {
		font-size: 0.625rem;
		text-transform: uppercase;
		font-weight: 600;
		letter-spacing: 0.05em;
		color: var(--color-text-secondary);
	}

	.status-icon {
		width: 12px;
		height: 12px;
	}

	.status-spinning {
		border: 2px solid var(--color-led-warning);
		border-top-color: transparent;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: pulse 2s ease-in-out infinite;
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}

	/* Cooling Fans */
	.cooling-fans {
		display: flex;
		gap: 0.25rem;
	}

	.fan {
		width: 16px;
		height: 16px;
		border: 2px solid rgba(74, 222, 128, 0.3);
		border-radius: 50%;
		animation: spin 2s linear infinite;
		position: relative;
	}

	.fan::before,
	.fan::after {
		content: '';
		position: absolute;
		background: rgba(74, 222, 128, 0.2);
	}

	.fan::before {
		width: 100%;
		height: 2px;
		top: 50%;
		left: 0;
		transform: translateY(-50%);
	}

	.fan::after {
		width: 2px;
		height: 100%;
		left: 50%;
		top: 0;
		transform: translateX(-50%);
	}

	/* Flip Button */
	.flip-button {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2rem;
		height: 2rem;
		background: rgba(59, 130, 246, 0.1);
		border: 1px solid rgba(59, 130, 246, 0.3);
		border-radius: 0.25rem;
		color: var(--color-accent);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.flip-button:hover {
		background: rgba(59, 130, 246, 0.2);
		border-color: var(--color-accent);
		box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
	}

	/* Action Buttons Container */
	.unit-actions {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	/* ====== BACK FACE STYLES ====== */

	.back-header {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding-right: 1rem;
	}

	.back-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--color-accent-bright);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.back-close-button {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2rem;
		height: 2rem;
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.3);
		border-radius: 0.25rem;
		color: #ef4444;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.back-close-button:hover {
		background: rgba(239, 68, 68, 0.2);
		border-color: #ef4444;
		box-shadow: 0 0 12px rgba(239, 68, 68, 0.4);
	}

	.tech-details {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 0.75rem;
		flex: 2;
	}

	.tech-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 255, 255, 0.05);
		border-radius: 0.25rem;
	}

	.tech-label {
		font-size: 0.625rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-secondary);
		font-weight: 600;
	}

	.tech-value {
		font-size: 0.875rem;
		font-family: 'Courier New', monospace;
		color: var(--color-accent-bright);
		font-weight: 600;
	}

	/* Tech Sections for Complex Data (Ports, Environment, Volumes) */
	.tech-section {
		grid-column: 1 / -1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 0.75rem;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 255, 255, 0.05);
		border-radius: 0.25rem;
	}

	.tech-mappings {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	.mapping-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.75rem;
		padding: 0.375rem;
		font-size: 0.75rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 0.125rem;
		border-left: 2px solid var(--color-accent);
	}

	.mapping-key {
		font-family: 'Courier New', monospace;
		color: var(--color-text-secondary);
		font-weight: 600;
		text-transform: uppercase;
		flex-shrink: 0;
	}

	.mapping-value {
		font-family: 'Courier New', monospace;
		color: var(--color-accent-bright);
		word-break: break-all;
		flex: 1;
		text-align: right;
	}

	.view-details-container {
		grid-column: 1 / -1;
		margin-top: 0.5rem;
	}

	.view-details-button {
		display: block;
		width: 100%;
		padding: 0.75rem 1rem;
		background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
		color: white;
		text-align: center;
		text-decoration: none;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 600;
		transition: all 0.2s ease;
		box-shadow: 0 2px 4px rgba(14, 165, 233, 0.3);
	}

	.view-details-button:hover {
		background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
		box-shadow: 0 0 20px rgba(14, 165, 233, 0.5);
		transform: translateY(-1px);
	}
</style>
