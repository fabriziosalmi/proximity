<script lang="ts">
	/**
	 * SystemOverviewRack - Multi-Unit System Command Panel
	 * Single large rack unit displaying all critical system metrics
	 * in an organized, high-density grid layout
	 */
	import { ShoppingBag, Layers, Server, Cpu, HardDrive, Activity } from 'lucide-svelte';
	import StatCard from '$lib/components/dashboard/StatCard.svelte';

	// Props for stats
	export let totalApps: number = 0;
	export let runningApps: number = 0;
	export let stoppedApps: number = 0;
	export let deployingApps: number = 0;
	export let availableApps: number = 0;
	export let categories: number = 0;
	export let totalHosts: number = 0;
	export let onlineHosts: number = 0;
	export let cpuUsage: string = '0%';
	export let memoryUsage: string = '0%';
</script>

<div class="system-overview-rack">
	<!-- Mounting Ears -->
	<div class="rack-ear rack-ear-left">
		<div class="screw screw-top"></div>
		<div class="screw screw-middle"></div>
		<div class="screw screw-bottom"></div>
	</div>

	<div class="rack-ear rack-ear-right">
		<div class="screw screw-top"></div>
		<div class="screw screw-middle"></div>
		<div class="screw screw-bottom"></div>
	</div>

	<!-- LED Status Strip -->
	<div class="led-strip">
		<div class="led led-active"></div>
		<div class="led led-active"></div>
		<div class="led led-active"></div>
		<div class="led"></div>
	</div>

	<!-- Main Content Area -->
	<div class="rack-content">
		<!-- Header Title -->
		<div class="rack-header">
			<div class="status-indicator"></div>
			<h2 class="rack-title">SYSTEM OVERVIEW</h2>
			<div class="rack-subtitle">PROXIMITY COMMAND DECK</div>
		</div>

		<!-- Section 1: Applications -->
		<div class="section-container">
			<h3 class="section-title">
				<Server class="section-icon" />
				Applications
			</h3>
			<div class="stats-grid grid-4">
				<StatCard
					label="Total Apps"
					value={totalApps}
					icon={Server}
					variant="compact"
				/>
				<StatCard
					label="Running"
					value={runningApps}
					icon={Activity}
					variant="compact"
					ledColor="var(--color-led-active)"
				/>
				<StatCard
					label="Stopped"
					value={stoppedApps}
					icon={Server}
					variant="compact"
					ledColor="#ef4444"
				/>
				<StatCard
					label="Deploying"
					value={deployingApps}
					icon={Activity}
					variant="compact"
					ledColor="#f59e0b"
				/>
			</div>
		</div>

		<!-- Section 2: Two-Column Layout -->
		<div class="section-row">
			<!-- App Catalog Column -->
			<div class="section-container section-half">
				<h3 class="section-title">
					<ShoppingBag class="section-icon" />
					App Catalog
				</h3>
				<div class="stats-grid grid-2">
					<StatCard
						label="Available Apps"
						value={availableApps}
						icon={ShoppingBag}
						variant="compact"
					/>
					<StatCard
						label="Categories"
						value={categories}
						icon={Layers}
						variant="compact"
					/>
				</div>
			</div>

			<!-- Infrastructure Column -->
			<div class="section-container section-half">
				<h3 class="section-title">
					<HardDrive class="section-icon" />
					Infrastructure
				</h3>
				<div class="stats-grid grid-2x2">
					<StatCard
						label="Total Hosts"
						value={totalHosts}
						icon={HardDrive}
						variant="compact"
					/>
					<StatCard
						label="Online Hosts"
						value={onlineHosts}
						icon={HardDrive}
						variant="compact"
						ledColor="var(--color-led-active)"
					/>
					<StatCard
						label="CPU Usage"
						value={cpuUsage}
						icon={Cpu}
						variant="compact"
					/>
					<StatCard
						label="Memory Usage"
						value={memoryUsage}
						icon={Activity}
						variant="compact"
					/>
				</div>
			</div>
		</div>

		<!-- Panel Footer with Serial Number -->
		<div class="rack-footer">
			<div class="serial-label">P2-SYSOVERVIEW-001</div>
			<div class="warning-strip">
				<span>⚠</span>
				<span>AUTHORIZED PERSONNEL ONLY</span>
				<span>⚠</span>
			</div>
		</div>
	</div>
</div>

<style>
	/* Main Rack Container - Match RackCard exact styling */
	.system-overview-rack {
		position: relative;
		/* No width specified - fills available space naturally */
		min-height: 42rem;
		/* Match RackCard exact background and border */
		background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 50%, #1a1a1a 100%);
		border: 2px solid rgba(75, 85, 99, 0.4);
		border-radius: 0.5rem;
		padding: 3rem 4rem;
		box-shadow:
			0 4px 6px rgba(0, 0, 0, 0.3),
			0 10px 30px rgba(0, 0, 0, 0.5),
			inset 0 1px 0 rgba(255, 255, 255, 0.05),
			inset 0 -1px 0 rgba(0, 0, 0, 0.5);
	}

	/* Mounting Ears - Match RackCard exact styling */
	.rack-ear {
		position: absolute;
		top: 0;
		width: 2rem; /* Match RackCard width */
		height: 100%;
		/* Match RackCard exact ear gradient */
		background: linear-gradient(180deg, #3a3a3a 0%, #2a2a2a 50%, #1a1a1a 100%);
		border: 1px solid rgba(0, 0, 0, 0.8);
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 0;
		z-index: 2;
		/* Match RackCard shadow */
		box-shadow:
			inset 1px 0 2px rgba(255, 255, 255, 0.1),
			inset -1px 0 2px rgba(0, 0, 0, 0.5);
	}

	.rack-ear-left {
		left: 0;
		border-radius: 0.5rem 0 0 0.5rem; /* Match outer border-radius */
		border-right: none;
	}

	.rack-ear-right {
		right: 0;
		border-radius: 0 0.5rem 0.5rem 0; /* Match outer border-radius */
		border-left: none;
	}

	/* Screws - Match RackCard exact screw styling */
	.screw {
		width: 0.625rem;
		height: 0.625rem;
		background: radial-gradient(circle, #4a4a4a 0%, #2a2a2a 70%);
		border-radius: 50%;
		border: 1px solid rgba(0, 0, 0, 0.8);
		box-shadow:
			inset 0 1px 2px rgba(255, 255, 255, 0.3),
			inset 0 -1px 2px rgba(0, 0, 0, 0.5);
		position: relative;
	}

	.screw::before {
		content: '';
		position: absolute;
		width: 50%;
		height: 1px;
		background: rgba(0, 0, 0, 0.6);
		left: 25%;
		top: 50%;
		transform: translateY(-50%);
	}

	/* LED Strip - Match RackCard exact positioning */
	.led-strip {
		position: absolute;
		top: 0.75rem; /* Match RackCard positioning */
		right: 2.5rem;
		display: flex;
		gap: 0.25rem;
		z-index: 3;
	}

	.led {
		width: 0.5rem;
		height: 0.5rem;
		background: rgba(100, 100, 100, 0.3);
		border-radius: 50%;
		border: 1px solid rgba(0, 0, 0, 0.5);
		box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
	}

	.led-active {
		background: var(--color-led-active, #22c55e);
		box-shadow:
			0 0 8px var(--color-led-active, #22c55e),
			inset 0 1px 2px rgba(255, 255, 255, 0.3);
		animation: pulse-led 2s ease-in-out infinite;
	}

	@keyframes pulse-led {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.6; }
	}

	/* Main Content */
	.rack-content {
		position: relative;
		z-index: 1;
	}

	/* Header */
	.rack-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 2rem;
		padding-bottom: 1rem;
		border-bottom: 2px solid rgba(var(--color-rack-primary-rgb, 59, 130, 246), 0.3);
	}

	.status-indicator {
		width: 1rem;
		height: 1rem;
		background: var(--color-led-active, #22c55e);
		border-radius: 50%;
		box-shadow: 0 0 12px var(--color-led-active, #22c55e);
		animation: pulse-led 2s ease-in-out infinite;
	}

	.rack-title {
		font-size: 1.75rem;
		font-weight: 700;
		color: white;
		letter-spacing: 0.1em;
		text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
		margin: 0;
	}

	.rack-subtitle {
		margin-left: auto;
		font-size: 0.75rem;
		color: var(--color-text-secondary);
		letter-spacing: 0.15em;
		text-transform: uppercase;
	}

	/* Sections */
	.section-container {
		margin-bottom: 2rem;
	}

	.section-title {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 1rem;
		font-weight: 600;
		color: var(--color-rack-primary);
		text-transform: uppercase;
		letter-spacing: 0.1em;
		margin-bottom: 1rem;
		padding-left: 0.5rem;
		border-left: 3px solid var(--color-rack-primary);
	}

	.section-icon {
		width: 1.25rem;
		height: 1.25rem;
	}

	/* Grid Layouts */
	.stats-grid {
		display: grid;
		gap: 1rem;
	}

	.grid-4 {
		grid-template-columns: repeat(4, 1fr);
	}

	.grid-2 {
		grid-template-columns: repeat(2, 1fr);
	}

	.grid-2x2 {
		grid-template-columns: repeat(2, 1fr);
	}

	/* Two-Column Section Row */
	.section-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		margin-bottom: 2rem;
	}

	.section-half {
		margin-bottom: 0;
	}

	/* Footer */
	.rack-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 2rem;
		padding-top: 1rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	.serial-label {
		font-family: 'Courier New', monospace;
		font-size: 0.75rem;
		color: var(--color-text-secondary);
		letter-spacing: 0.05em;
	}

	.warning-strip {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.25rem 0.75rem;
		background: linear-gradient(90deg, transparent, rgba(245, 158, 11, 0.1), transparent);
		border: 1px solid rgba(245, 158, 11, 0.3);
		border-radius: 0.25rem;
		font-size: 0.625rem;
		color: #f59e0b;
		letter-spacing: 0.1em;
	}

	/* Responsive */
	@media (max-width: 1400px) {
		.grid-4 {
			grid-template-columns: repeat(2, 1fr);
		}

		.section-row {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.system-overview-rack {
			padding: 2rem 3rem;
			min-height: auto;
		}

		.rack-ear {
			width: 1.5rem;
		}

		.rack-title {
			font-size: 1.25rem;
		}

		.grid-4,
		.grid-2,
		.grid-2x2 {
			grid-template-columns: 1fr;
		}

		.section-row {
			grid-template-columns: 1fr;
		}

		.rack-footer {
			flex-direction: column;
			gap: 1rem;
		}
	}
</style>
