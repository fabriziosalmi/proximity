<script>
	/**
	 * MasterControlRack - 2U Supreme Command Center
	 * The ultimate navigation, status, and action control panel
	 * Replaces TopBar and enhances NavigationRack with integrated SystemStatusLCD
	 */
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Home, Server, Store, HardDrive, Settings, Plus, User, LogOut } from 'lucide-svelte';
	import { myAppsStore } from '$lib/stores/apps';
	import { authStore } from '$lib/stores/auth';
	import { api } from '$lib/api';

	const navItems = [
		{ href: '/', label: 'Home', icon: Home },
		{ href: '/apps', label: 'Apps', icon: Server },
		{ href: '/store', label: 'Store', icon: Store },
		{ href: '/hosts', label: 'Hosts', icon: HardDrive },
		{ href: '/settings', label: 'Settings', icon: Settings }
	];

	let showUserMenu = false;

	// System Status LCD logic (integrated from SystemStatusLCD)
	let statusMessage = 'SYSTEM: NOMINAL';
	let statusColor = '#4ade80';

	$: {
		const deployingApps = $myAppsStore.apps.filter(
			(app) => app.status === 'deploying' || app.status === 'cloning'
		);

		if (deployingApps.length > 0) {
			const app = deployingApps[0];
			const action = app.status === 'deploying' ? 'DEPLOYING' : 'CLONING';
			statusMessage = `${action}: ${app.hostname.toUpperCase()}...`;
			statusColor = '#fbbf24';
		} else {
			statusMessage = 'SYSTEM: NOMINAL';
			statusColor = '#4ade80';
		}
	}

	function isActive(href, pathname) {
		return pathname === href || (href !== '/' && pathname.startsWith(href));
	}

	function toggleUserMenu() {
		showUserMenu = !showUserMenu;
	}

	function handleClickOutside(event) {
		if (!event.target.closest('.user-menu-container')) {
			showUserMenu = false;
		}
	}

	async function handleLogout() {
		// Clear auth state through authStore (single source of truth)
		// This will automatically update ApiClient via subscription
		authStore.logout();
		api.logout(); // This just clears Sentry context
		
		// Navigate to login
		await goto('/login');
		showUserMenu = false;
	}

	function handleDeploy() {
		goto('/store');
	}
</script>

<svelte:window on:click={handleClickOutside} />

<!-- ============================================ -->
<!-- DESKTOP: 2U MASTER CONTROL RACK (lg:) -->
<!-- ============================================ -->
<div class="hidden lg:block w-full">
	<div class="master-control-rack">
		<!-- Left Mounting Ear -->
		<div class="mounting-ear mounting-ear-left">
			<div class="screw screw-top"></div>
			<div class="screw screw-middle"></div>
			<div class="screw screw-bottom"></div>
		</div>

		<!-- Master Control Body - 2U Height -->
		<div class="rack-body">
			<!-- Top Row: Navigation + Status -->
			<div class="control-row control-row-top">
				<!-- LED Status Strip -->
				<div class="led-strip">
					{#each navItems as item}
						<div
							class="nav-led"
							class:active={isActive(item.href, $page.url.pathname)}
						></div>
					{/each}
				</div>

				<!-- Navigation Buttons -->
				<div class="nav-buttons-container">
					{#each navItems as item}
						<a
							href={item.href}
							class="nav-button"
							class:nav-button-active={isActive(item.href, $page.url.pathname)}
							title={item.label}
						>
							<svelte:component this={item.icon} class="h-5 w-5" />
							<span class="nav-label">{item.label}</span>
							<div
								class="nav-indicator"
								class:active={isActive(item.href, $page.url.pathname)}
							></div>
						</a>
					{/each}
				</div>

				<!-- Rack Title Badge -->
				<div class="rack-title">MASTER CONTROL</div>
			</div>

			<!-- Bottom Row: System Status LCD + Actions -->
			<div class="control-row control-row-bottom">
				<!-- Large Integrated LCD Display -->
				<div class="integrated-lcd-container">
					<div class="lcd-display" style="color: {statusColor}">
						{statusMessage}
					</div>
					<div class="lcd-scanline"></div>
				</div>

				<!-- Action Buttons Panel -->
				<div class="action-panel">
					<!-- Deploy Button -->
					<button class="deploy-btn" on:click={handleDeploy} title="Deploy New App">
						<Plus class="h-5 w-5" />
						<span>DEPLOY</span>
					</button>

					<!-- Admin Menu -->
					<div class="user-menu-container">
						<button
							class="user-btn"
							on:click|stopPropagation={toggleUserMenu}
							title="Admin Menu"
						>
							<User class="h-5 w-5" />
							<span>ADMIN</span>
						</button>

						{#if showUserMenu}
							<div class="user-menu">
								<a href="/settings" class="menu-item">
									<Settings class="h-4 w-4" />
									Settings
								</a>
								<button class="menu-item" on:click={handleLogout}>
									<LogOut class="h-4 w-4" />
									Logout
								</button>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>

		<!-- Right Mounting Ear -->
		<div class="mounting-ear mounting-ear-right">
			<div class="screw screw-top"></div>
			<div class="screw screw-middle"></div>
			<div class="screw screw-bottom"></div>
		</div>
	</div>
</div>

<!-- ============================================ -->
<!-- MOBILE: VERTICAL NAVIGATION RACK (<lg:) -->
<!-- ============================================ -->
<nav
	class="flex lg:hidden flex-col h-full w-full bg-gradient-to-b from-gray-700 to-gray-800 border-r border-gray-600 relative"
>
	<!-- Decorative screws -->
	<div class="screw screw-tl"></div>
	<div class="screw screw-tr"></div>

	<!-- Logo Section -->
	<div class="px-3 py-4 border-b border-gray-600">
		<div class="flex flex-col items-center gap-1">
			<div class="text-cyan-400 text-xl font-bold tracking-wider">P2</div>
			<div
				class="h-1 w-8 bg-gradient-to-r from-transparent via-cyan-400 to-transparent rounded-full"
			></div>
		</div>
	</div>

	<!-- Navigation Items -->
	<ul class="flex-1 py-4 space-y-1">
		{#each navItems as item}
			<li>
				<a
					href={item.href}
					class="mobile-nav-link"
					class:mobile-nav-link-active={isActive(item.href, $page.url.pathname)}
					title={item.label}
				>
					<svelte:component this={item.icon} class="h-5 w-5" />
					<div
						class="mobile-led"
						class:mobile-led-active={isActive(item.href, $page.url.pathname)}
					></div>
				</a>
			</li>
		{/each}
	</ul>

	<!-- Bottom decorative screws -->
	<div class="screw screw-bl"></div>
	<div class="screw screw-br"></div>
</nav>

<style>
	/* ============================================ */
	/* RESPONSIVE VISIBILITY CONTROL */
	/* ============================================ */

	@media (min-width: 1024px) {
		nav.flex {
			display: none !important;
		}
	}

	@media (max-width: 1023px) {
		.master-control-rack {
			display: none !important;
		}
	}

	/* ============================================ */
	/* DESKTOP: 2U MASTER CONTROL RACK */
	/* ============================================ */

	.master-control-rack {
		display: flex;
		align-items: stretch;
		height: 120px; /* 2U height (60px * 2) */
		background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 50%, #1a1a1a 100%);
		border: 2px solid rgba(75, 85, 99, 0.4);
		border-radius: 0.5rem;
		position: relative;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3), 0 10px 30px rgba(0, 0, 0, 0.5),
			inset 0 1px 0 rgba(255, 255, 255, 0.05), inset 0 -1px 0 rgba(0, 0, 0, 0.5);
	}

	/* Mounting Ears - Match SystemOverviewRack */
	.mounting-ear {
		position: absolute;
		top: 0;
		width: 2rem;
		height: 100%;
		background: linear-gradient(180deg, #3a3a3a 0%, #2a2a2a 50%, #1a1a1a 100%);
		border: 1px solid rgba(0, 0, 0, 0.8);
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 0;
		z-index: 2;
		box-shadow: inset 1px 0 2px rgba(255, 255, 255, 0.1), inset -1px 0 2px rgba(0, 0, 0, 0.5);
	}

	.mounting-ear-left {
		left: 0;
		border-radius: 0.5rem 0 0 0.5rem;
		border-right: none;
	}

	.mounting-ear-right {
		right: 0;
		border-radius: 0 0.5rem 0.5rem 0;
		border-left: none;
	}

	/* Screws - 3 per ear for 2U unit */
	.screw {
		width: 0.625rem;
		height: 0.625rem;
		background: radial-gradient(circle, #4a4a4a 0%, #2a2a2a 70%);
		border-radius: 50%;
		border: 1px solid rgba(0, 0, 0, 0.8);
		box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.3), inset 0 -1px 2px rgba(0, 0, 0, 0.5);
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

	/* Rack Body - 2 Rows */
	.rack-body {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 0 2rem;
		position: relative;
	}

	.control-row {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.75rem 0;
	}

	.control-row-top {
		border-bottom: 1px solid rgba(75, 85, 99, 0.3);
	}

	/* LED Status Strip */
	.led-strip {
		display: flex;
		gap: 0.25rem;
		padding: 0.25rem 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 0.25rem;
		border: 1px solid rgba(0, 0, 0, 0.5);
	}

	.nav-led {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--color-led-inactive, #374151);
		transition: all 0.3s ease;
	}

	.nav-led.active {
		background: var(--color-led-active, #4ade80);
		box-shadow: 0 0 8px var(--color-led-active, #4ade80);
		animation: pulse-led 2s ease-in-out infinite;
	}

	@keyframes pulse-led {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.6;
		}
	}

	/* Navigation Buttons */
	.nav-buttons-container {
		display: flex;
		gap: 0.5rem;
		flex: 1;
	}

	.nav-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		border-radius: 0.25rem;
		border: 1px solid rgba(75, 85, 99, 0.3);
		background: rgba(31, 41, 55, 0.5);
		color: var(--color-text-secondary, #9ca3af);
		text-decoration: none;
		font-size: 0.875rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.2s ease;
		position: relative;
		cursor: pointer;
	}

	.nav-button:hover {
		background: rgba(31, 41, 55, 0.8);
		border-color: rgba(59, 130, 246, 0.5);
		color: var(--color-text-primary, #e5e7eb);
		box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
	}

	.nav-button-active {
		background: rgba(0, 212, 255, 0.15);
		border-color: var(--color-accent-bright, #00d4ff);
		color: var(--color-text-primary, #e5e7eb);
		box-shadow: 0 0 12px rgba(0, 212, 255, 0.4);
	}

	.nav-label {
		white-space: nowrap;
	}

	.nav-indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--color-led-inactive, #374151);
		transition: all 0.3s ease;
		margin-left: auto;
	}

	.nav-indicator.active {
		background: var(--color-led-active, #4ade80);
		box-shadow: 0 0 8px var(--color-led-active, #4ade80);
	}

	/* Rack Title Badge */
	.rack-title {
		font-size: 0.625rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		color: var(--color-text-secondary, #9ca3af);
		text-transform: uppercase;
		padding: 0.25rem 0.75rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 0.25rem;
		border: 1px solid rgba(0, 0, 0, 0.5);
	}

	/* ============================================ */
	/* INTEGRATED LCD DISPLAY - LARGER & PROMINENT */
	/* ============================================ */

	.integrated-lcd-container {
		position: relative;
		flex: 1;
		overflow: hidden;
		border-radius: 0.375rem;
		height: 40px;
	}

	.lcd-display {
		width: 100%;
		height: 100%;
		background-color: #000000;
		font-family: 'Courier New', 'Consolas', monospace;
		font-size: 1rem; /* Larger font for 2U */
		font-weight: 600;
		padding: 0.75rem 1.5rem;
		display: flex;
		align-items: center;
		border-radius: 0.375rem;
		border: 2px solid #1f2937;
		box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 0, 0, 0.5);
		animation: lcd-flicker 3s ease-in-out infinite;
		transition: color 0.3s ease;
		position: relative;
		z-index: 1;
		text-shadow: 0 0 8px currentColor;
	}

	.lcd-scanline {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 2px;
		background: linear-gradient(to bottom, transparent 0%, rgba(255, 255, 255, 0.1) 50%, transparent 100%);
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
			transform: translateY(100%);
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

	/* ============================================ */
	/* ACTION PANEL */
	/* ============================================ */

	.action-panel {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding-left: 1rem;
		border-left: 2px solid rgba(75, 85, 99, 0.3);
	}

	.deploy-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 1.25rem;
		background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
		color: white;
		border: none;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 700;
		cursor: pointer;
		transition: all 0.2s ease;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		box-shadow: 0 0 15px rgba(14, 165, 233, 0.3);
	}

	.deploy-btn:hover {
		background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
		box-shadow: 0 0 20px rgba(14, 165, 233, 0.6);
		transform: translateY(-1px);
	}

	.user-menu-container {
		position: relative;
	}

	.user-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 1.25rem;
		background: rgba(255, 255, 255, 0.05);
		color: var(--color-text-primary, #e5e7eb);
		border: 1px solid rgba(75, 85, 99, 0.3);
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 700;
		cursor: pointer;
		transition: all 0.2s ease;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.user-btn:hover {
		background: rgba(255, 255, 255, 0.1);
		border-color: rgba(59, 130, 246, 0.5);
		box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
	}

	.user-menu {
		position: absolute;
		top: calc(100% + 0.5rem);
		right: 0;
		min-width: 180px;
		background: var(--bg-card, #1f2937);
		border: 1px solid var(--border-color-primary, #4b5563);
		border-radius: 0.375rem;
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
		padding: 0.5rem;
		z-index: 1000;
	}

	.menu-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.625rem 0.875rem;
		background: transparent;
		color: var(--color-text-secondary, #9ca3af);
		border: none;
		border-radius: 0.25rem;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s ease;
		text-align: left;
		text-decoration: none;
	}

	.menu-item:hover {
		background: rgba(255, 255, 255, 0.05);
		color: var(--color-text-primary, #e5e7eb);
	}

	/* ============================================ */
	/* MOBILE VERTICAL RACK STYLES */
	/* ============================================ */

	.mobile-nav-link {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.375rem;
		padding: 0.75rem 0;
		color: var(--color-text-secondary, #9ca3af);
		text-decoration: none;
		transition: all 0.2s ease;
		position: relative;
		cursor: pointer;
	}

	.mobile-nav-link:hover {
		background: rgba(255, 255, 255, 0.05);
		color: var(--color-text-primary, #e5e7eb);
	}

	.mobile-nav-link-active {
		color: var(--color-text-primary, #e5e7eb);
		background: rgba(0, 212, 255, 0.15);
		border-left: 3px solid var(--color-accent-bright, #00d4ff);
	}

	.mobile-led {
		width: 5px;
		height: 5px;
		border-radius: 50%;
		background: var(--color-led-inactive, #374151);
		transition: all 0.3s ease;
	}

	.mobile-led-active {
		background: var(--color-led-active, #4ade80);
		box-shadow: 0 0 8px var(--color-led-active, #4ade80);
	}

	/* ============================================ */
	/* DECORATIVE HARDWARE ELEMENTS (Mobile) */
	/* ============================================ */

	.screw-tl {
		position: absolute;
		top: 0.5rem;
		left: 50%;
		transform: translateX(-50%);
		width: 8px;
		height: 8px;
		background: radial-gradient(circle, #4b5563 0%, #1f2937 70%);
		border-radius: 50%;
		border: 1px solid #0f172a;
		box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
		z-index: 10;
	}

	.screw-tl::after,
	.screw-tr::after,
	.screw-bl::after,
	.screw-br::after {
		content: '';
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 50%;
		height: 1px;
		background: #0f172a;
	}

	.screw-tr {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		width: 8px;
		height: 8px;
		background: radial-gradient(circle, #4b5563 0%, #1f2937 70%);
		border-radius: 50%;
		border: 1px solid #0f172a;
		box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
		z-index: 10;
	}

	.screw-bl {
		position: absolute;
		bottom: 0.5rem;
		left: 50%;
		transform: translateX(-50%);
		width: 8px;
		height: 8px;
		background: radial-gradient(circle, #4b5563 0%, #1f2937 70%);
		border-radius: 50%;
		border: 1px solid #0f172a;
		box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
		z-index: 10;
	}

	.screw-br {
		position: absolute;
		bottom: 0.5rem;
		right: 0.5rem;
		width: 8px;
		height: 8px;
		background: radial-gradient(circle, #4b5563 0%, #1f2937 70%);
		border-radius: 50%;
		border: 1px solid #0f172a;
		box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
		z-index: 10;
	}
</style>
