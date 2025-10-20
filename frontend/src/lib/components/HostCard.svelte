<!-- HostCard.svelte - 1U Rack-Mounted Host Unit -->
<!-- Theme-ready component showing host information and status -->
<script lang="ts">
	import { Server, Cpu, HardDrive, MemoryStick, Circle } from 'lucide-svelte';

	export let host: {
		id: number;
		name: string;
		host: string;
		port: number;
		status?: string;
		node_name?: string;
		cpu_usage?: number;
		memory_usage?: number;
		disk_usage?: number;
		created_at?: string;
	};

	// Get LED color based on status
	function getLEDColor(status?: string): string {
		if (status === 'online') return 'var(--color-led-active)';
		if (status === 'offline') return 'var(--color-led-danger)';
		return 'var(--color-led-inactive)';
	}

	// Format percentage
	function formatPercent(value?: number): string {
		if (value === undefined || value === null) return '--';
		return `${Math.round(value)}%`;
	}

	// Check if LED should pulse
	function shouldPulse(status?: string): boolean {
		return status === 'online';
	}

	$: ledColor = getLEDColor(host.status);
	$: ledPulse = shouldPulse(host.status);
</script>

<div
	data-testid="host-card-{host.id}"
	class="rack-unit"
>
	<!-- Left Mounting Ear -->
	<div class="mounting-ear mounting-ear-left">
		<div class="screw"></div>
	</div>

	<!-- Main Unit Body -->
	<div class="unit-body">
		<!-- Left Section: LED and Icon -->
		<div class="unit-left">
			<!-- Status LED -->
			<div class="led-indicator" style="background-color: {ledColor};" class:led-pulse={ledPulse}></div>

			<!-- Host Icon -->
			<div class="app-icon">
				<Server class="h-6 w-6 text-gray-400" />
			</div>
		</div>

		<!-- Center Section: Host Info -->
		<div class="unit-center">
			<div class="app-name">{host.name}</div>
			<div class="app-hostname">{host.host}:{host.port}</div>
			{#if host.node_name}
				<div class="app-meta">
					<span class="meta-label">Node:</span>
					<span class="meta-value">{host.node_name}</span>
				</div>
			{/if}
		</div>

		<!-- Center-Right Section: Resource Stats -->
		<div class="unit-stats">
			<div class="stat-item">
				<Cpu size={14} class="stat-icon" />
				<span class="stat-value">{formatPercent(host.cpu_usage)}</span>
			</div>
			<div class="stat-item">
				<MemoryStick size={14} class="stat-icon" />
				<span class="stat-value">{formatPercent(host.memory_usage)}</span>
			</div>
			<div class="stat-item">
				<HardDrive size={14} class="stat-icon" />
				<span class="stat-value">{formatPercent(host.disk_usage)}</span>
			</div>
		</div>

		<!-- Right Section: Status and Actions -->
		<div class="unit-right">
			<!-- Status Badge -->
			<div class="status-display">
				<Circle size={8} fill={ledColor} color={ledColor} />
				<span class="status-text">{host.status || 'unknown'}</span>
			</div>

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

	/* Stats Section */
	.unit-stats {
		display: flex;
		gap: 1rem;
		flex-shrink: 0;
	}

	.stat-item {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.375rem 0.625rem;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.05);
		border-radius: 0.25rem;
	}

	.stat-icon {
		color: var(--color-text-secondary);
	}

	.stat-value {
		font-size: 0.75rem;
		font-weight: 600;
		font-family: 'Courier New', monospace;
		color: var(--color-text-primary);
		min-width: 2.5rem;
		text-align: right;
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

	/* Action Buttons Container */
	.unit-actions {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}
</style>
