<script lang="ts">
	/**
	 * HostRackCard - 1U Rack-Mounted Host/Node Unit with 3D Flip
	 * Specialized version of RackCard for Proxmox nodes
	 */
	import { Server, Cpu, MemoryStick, HardDrive, Info, X, Activity } from 'lucide-svelte';

	export let host: {
		id: number;
		name: string;
		host: string;
		port?: number;
		user?: string;
		is_active?: boolean;
		is_default?: boolean;
		last_seen?: string | null;
		// Optional stats
		status?: string;
		cpu_count?: number;
		cpu_usage?: number;
		memory_total?: number;
		memory_used?: number;
		storage_total?: number;
		storage_used?: number;
		uptime?: number;
		pve_version?: string;
	};

	// Flip state
	let isFlipped = false;

	function toggleFlip() {
		isFlipped = !isFlipped;
	}

	// Determine LED color based on status
	function getLEDColor(status?: string, isActive?: boolean): string {
		// Use is_active if status is not provided
		const effectiveStatus = status || (isActive ? 'online' : 'offline');
		const colors: Record<string, string> = {
			online: 'var(--color-led-active)',
			offline: 'var(--color-led-danger)',
			unknown: 'var(--color-led-inactive)'
		};
		return colors[effectiveStatus] || 'var(--color-led-inactive)';
	}

	// Determine if LED should pulse
	function shouldPulse(status?: string, isActive?: boolean): boolean {
		const effectiveStatus = status || (isActive ? 'online' : 'offline');
		return effectiveStatus === 'online';
	}

	// Format uptime in human-readable format
	function formatUptime(seconds?: number): string {
		if (!seconds) return '--';
		const days = Math.floor(seconds / 86400);
		const hours = Math.floor((seconds % 86400) / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);
		
		if (days > 0) return `${days}d ${hours}h`;
		if (hours > 0) return `${hours}h ${minutes}m`;
		return `${minutes}m`;
	}

	// Format bytes to GB
	function formatGB(bytes?: number): string {
		if (!bytes) return '--';
		return (bytes / (1024 * 1024 * 1024)).toFixed(2);
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

	$: ledColor = getLEDColor(host.status, host.is_active);
	$: ledPulse = shouldPulse(host.status, host.is_active);
	$: cpuPercent = host.cpu_usage || 0;
	$: memoryPercent = calculatePercent(host.memory_used, host.memory_total);
	$: diskPercent = calculatePercent(host.storage_used, host.storage_total);
	$: effectiveStatus = host.status || (host.is_active ? 'online' : 'offline');
</script>

<div
	data-testid="host-rack-card-{host.id}"
	data-host-id={host.id}
	data-node-name={host.name}
	data-status={effectiveStatus}
	class="card-container"
	class:is-flipped={isFlipped}
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
							data-testid="host-led"
						></div>

						<!-- Host Icon -->
						<div class="app-icon">
							<Server class="h-6 w-6 text-gray-400" />
						</div>
					</div>

				<!-- Center Section: Host Info -->
				<div class="unit-center">
					<div class="app-name" data-testid="host-name">{host.name}</div>
					<div class="app-hostname" data-testid="host-hostname">{host.host}</div>
					{#if host.port}
						<div class="app-meta">
							<span class="meta-label">Port:</span>
							<span class="meta-value">{host.port}</span>
						</div>
					{/if}
				</div>					<!-- Center-Right Section: Resource Gauges -->
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
									class:progress-warn={cpuPercent > 80}
									class:progress-danger={cpuPercent > 90}
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
									class:progress-warn={memoryPercent > 80}
									class:progress-danger={memoryPercent > 90}
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
									class:progress-warn={diskPercent > 80}
									class:progress-danger={diskPercent > 90}
									style="width: {diskPercent}%"
								></div>
							</div>
							<span class="stat-value">{formatPercent(diskPercent)}</span>
						</div>
					</div>

				<!-- Right Section: Status Badge and Actions -->
				<div class="unit-right">
					<!-- Status Badge -->
					<div class="status-display" data-testid="host-status-badge" data-status={effectiveStatus}>
						{#if effectiveStatus === 'online'}
							<Activity class="h-4 w-4 text-green-400" />
						{:else if effectiveStatus === 'offline'}
							<div class="status-dot" style="background-color: var(--color-led-danger);"></div>
						{/if}
						<span class="status-text">{effectiveStatus}</span>
					</div>

					<!-- Uptime Display (for online hosts) -->
					{#if effectiveStatus === 'online' && host.uptime}
						<div class="uptime-display">
							<span class="uptime-label">UP</span>
							<span class="uptime-value">{formatUptime(host.uptime)}</span>
						</div>
					{/if}						<!-- Flip Button -->
						<button
							class="flip-button"
							on:click={toggleFlip}
							data-testid="host-flip-button"
							aria-label="Show technical details"
						>
							<Info size={16} />
						</button>

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
						<div class="back-title">Node Technical Specifications</div>
						<button
							class="back-close-button"
							on:click={toggleFlip}
							data-testid="host-close-flip-button"
							aria-label="Return to front view"
						>
							<X size={16} />
						</button>
					</div>

					<!-- Technical Details Grid -->
					<div class="tech-details">
						<div class="tech-item">
							<span class="tech-label">Node ID:</span>
							<span class="tech-value">{host.id}</span>
						</div>
						<div class="tech-item">
							<span class="tech-label">Node Name:</span>
							<span class="tech-value">{host.name}</span>
					</div>
					{#if host.host}
						<div class="tech-item">
							<span class="tech-label">Host:</span>
							<span class="tech-value">{host.host}</span>
						</div>
					{/if}
					<div class="tech-item">
						<span class="tech-label">Status:</span>
						<span class="tech-value" class:text-green-400={effectiveStatus === 'online'} class:text-red-400={effectiveStatus === 'offline'}>
							{effectiveStatus.toUpperCase()}
						</span>
					</div>
						{#if host.pve_version}
							<div class="tech-item">
								<span class="tech-label">PVE Version:</span>
								<span class="tech-value">{host.pve_version}</span>
							</div>
						{/if}
						{#if host.cpu_count}
							<div class="tech-item">
								<span class="tech-label">CPU Cores:</span>
								<span class="tech-value">{host.cpu_count}</span>
							</div>
						{/if}
						{#if host.cpu_usage !== undefined}
							<div class="tech-item">
								<span class="tech-label">CPU Usage:</span>
								<span class="tech-value">{formatPercent(host.cpu_usage)}</span>
							</div>
						{/if}
						{#if host.memory_total}
							<div class="tech-item">
								<span class="tech-label">Memory Total:</span>
								<span class="tech-value">{formatGB(host.memory_total)} GB</span>
							</div>
						{/if}
						{#if host.memory_used}
							<div class="tech-item">
								<span class="tech-label">Memory Used:</span>
								<span class="tech-value">{formatGB(host.memory_used)} GB</span>
							</div>
						{/if}
						{#if host.memory_total && host.memory_used}
							<div class="tech-item">
								<span class="tech-label">Memory Usage:</span>
								<span class="tech-value">{formatPercent(memoryPercent)}</span>
							</div>
						{/if}
						{#if host.storage_total}
							<div class="tech-item">
								<span class="tech-label">Storage Total:</span>
								<span class="tech-value">{formatGB(host.storage_total)} GB</span>
							</div>
						{/if}
						{#if host.storage_used}
							<div class="tech-item">
								<span class="tech-label">Storage Used:</span>
								<span class="tech-value">{formatGB(host.storage_used)} GB</span>
							</div>
						{/if}
						{#if host.storage_total && host.storage_used}
							<div class="tech-item">
								<span class="tech-label">Storage Usage:</span>
								<span class="tech-value">{formatPercent(diskPercent)}</span>
							</div>
						{/if}
						{#if host.uptime}
							<div class="tech-item">
								<span class="tech-label">Uptime:</span>
								<span class="tech-value">{formatUptime(host.uptime)}</span>
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
		transition: all 0.3s ease;
	}

	.led-pulse {
		animation: pulse-green 2s ease-in-out infinite;
	}

	@keyframes pulse-green {
		0%, 100% {
			opacity: 1;
			box-shadow: 0 0 8px var(--color-led-active), 0 0 16px var(--color-led-active);
		}
		50% {
			opacity: 0.7;
			box-shadow: 0 0 4px var(--color-led-active);
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

	/* Center Section: Host Info */
	.unit-center {
		flex: 0 0 200px;
		min-width: 0;
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
		gap: 0.75rem;
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

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.uptime-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0.25rem 0.5rem;
		background: rgba(74, 222, 128, 0.1);
		border: 1px solid rgba(74, 222, 128, 0.2);
		border-radius: 0.25rem;
	}

	.uptime-label {
		font-size: 0.5rem;
		text-transform: uppercase;
		font-weight: 600;
		letter-spacing: 0.05em;
		color: var(--color-led-active);
	}

	.uptime-value {
		font-size: 0.625rem;
		font-family: 'Courier New', monospace;
		color: var(--color-led-active);
		font-weight: 600;
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

	.text-green-400 {
		color: #4ade80;
	}

	.text-red-400 {
		color: #f87171;
	}
</style>
