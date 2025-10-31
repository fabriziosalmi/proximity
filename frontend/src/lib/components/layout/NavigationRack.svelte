<script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Home, Server, Store, HardDrive, Settings, Plus, User, LogOut } from 'lucide-svelte';
	import SystemStatusLCD from './SystemStatusLCD.svelte';
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

	// Reactive declaration for current pathname - SAFE for SSR
	$: currentPath = $page.url.pathname;

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
<!-- DESKTOP: HORIZONTAL NAVIGATION RACK (lg:) -->
<!-- ============================================ -->
<div class="hidden lg:block w-full mb-6">
	<div class="horizontal-nav-rack">
		<!-- Decorative mounting ears -->
		<div class="mounting-ear-left">
			<div class="screw"></div>
		</div>
		
		<!-- Navigation content -->
		<div class="nav-rack-body">
			<!-- LED strip decoration -->
			<div class="led-strip">
				{#each navItems as item}
					<div class="nav-led" class:active={isActive(item.href, currentPath)}></div>
				{/each}
			</div>
			
			<!-- Navigation buttons -->
			<div class="nav-buttons-container">
				{#each navItems as item}
					<a
						href={item.href}
						class="nav-button"
						class:nav-button-active={isActive(item.href, currentPath)}
						title={item.label}
					>
						<svelte:component this={item.icon} class="h-5 w-5" />
						<span class="nav-label">{item.label}</span>
						<div class="nav-indicator" class:active={isActive(item.href, currentPath)}></div>
					</a>
				{/each}
			</div>
			
			<!-- System Status LCD Display -->
			<div class="status-display">
				<SystemStatusLCD />
			</div>
			
			<!-- Action Buttons -->
			<div class="action-buttons">
				<!-- Deploy Button -->
				<button class="deploy-btn" on:click={handleDeploy} title="Deploy New App">
					<Plus class="h-4 w-4" />
					<span>Deploy</span>
				</button>

				<!-- Admin Menu -->
				<div class="user-menu-container">
					<button class="user-btn" on:click|stopPropagation={toggleUserMenu} title="Admin Menu">
						<User class="h-4 w-4" />
						<span>Admin</span>
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
			
			<!-- Title label -->
			<div class="rack-title">COMMAND DECK</div>
		</div>
		
		<!-- Right mounting ear -->
		<div class="mounting-ear-right">
			<div class="screw"></div>
		</div>
	</div>
</div>

<!-- ============================================ -->
<!-- MOBILE: VERTICAL NAVIGATION RACK (<lg:) -->
<!-- ============================================ -->
<nav class="flex lg:hidden flex-col h-full w-full bg-gradient-to-b from-gray-700 to-gray-800 border-r border-gray-600 relative">
	<!-- Decorative screws -->
	<div class="screw screw-tl"></div>
	<div class="screw screw-tr"></div>

	<!-- Logo Section -->
	<div class="px-3 py-4 border-b border-gray-600">
		<div class="flex flex-col items-center gap-1">
			<div class="text-cyan-400 text-xl font-bold tracking-wider">P2</div>
			<div class="h-1 w-8 bg-gradient-to-r from-transparent via-cyan-400 to-transparent rounded-full"></div>
		</div>
	</div>

	<!-- Navigation Items -->
	<ul class="flex-1 py-4 space-y-1">
		{#each navItems as item}
			<li>
				<a
					href={item.href}
					class="mobile-nav-link"
					class:mobile-nav-link-active={isActive(item.href, currentPath)}
					title={item.label}
				>
					<svelte:component this={item.icon} class="h-5 w-5" />
					<div class="mobile-led" class:mobile-led-active={isActive(item.href, currentPath)}></div>
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
	
	/* Ensure mobile nav is hidden on desktop */
	@media (min-width: 1024px) {
		nav.flex {
			display: none !important;
		}
	}
	
	/* Ensure desktop nav is hidden on mobile */
	@media (max-width: 1023px) {
		.horizontal-nav-rack {
			display: none !important;
		}
	}
	
	/* ============================================ */
	/* DESKTOP HORIZONTAL NAVIGATION RACK */
	/* ============================================ */
	
	.horizontal-nav-rack {
		display: flex;
		align-items: stretch;
		height: 60px; /* 1U height */
		background: linear-gradient(to bottom, #374151, #1f2937);
		border: 1px solid var(--border-rack, #4b5563);
		border-radius: 0.25rem;
		position: relative;
		box-shadow: 
			0 2px 4px rgba(0, 0, 0, 0.3),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
	}
	
	.mounting-ear-left,
	.mounting-ear-right {
		width: 32px;
		background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
		border-right: 1px solid #1f2937;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}
	
	.mounting-ear-right {
		border-right: none;
		border-left: 1px solid #1f2937;
	}
	
	.nav-rack-body {
		flex: 1;
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0 1.5rem;
		position: relative;
	}
	
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
	}
	
	.nav-buttons-container {
		display: flex;
		gap: 0.5rem;
		flex: 1;
	}
	
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

	/* Status Display */
	.status-display {
		display: flex;
		align-items: center;
		margin-left: auto;
	}

	/* Action Buttons */
	.action-buttons {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding-left: 1rem;
		border-left: 1px solid rgba(75, 85, 99, 0.3);
	}

	.deploy-btn {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 0.875rem;
		background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
		color: white;
		border: none;
		border-radius: 0.25rem;
		font-size: 0.875rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.deploy-btn:hover {
		background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
		box-shadow: 0 0 12px rgba(14, 165, 233, 0.5);
	}

	.user-menu-container {
		position: relative;
	}

	.user-btn {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 0.875rem;
		background: rgba(255, 255, 255, 0.05);
		color: var(--color-text-primary, #e5e7eb);
		border: 1px solid rgba(75, 85, 99, 0.3);
		border-radius: 0.25rem;
		font-size: 0.875rem;
		font-weight: 600;
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
		min-width: 160px;
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
		padding: 0.5rem 0.75rem;
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
	/* DECORATIVE HARDWARE ELEMENTS */
	/* ============================================ */

	.screw {
		position: absolute;
		width: 8px;
		height: 8px;
		background: radial-gradient(circle, #4b5563 0%, #1f2937 70%);
		border-radius: 50%;
		border: 1px solid #0f172a;
		box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
		z-index: 10;
	}

	.screw::after {
		content: '';
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 50%;
		height: 1px;
		background: #0f172a;
	}

	.screw-tl {
		top: 0.5rem;
		left: 50%;
		transform: translateX(-50%);
	}
	.screw-tr {
		top: 0.5rem;
		right: 0.5rem;
	}
	.screw-bl {
		bottom: 0.5rem;
		left: 50%;
		transform: translateX(-50%);
	}
	.screw-br {
		bottom: 0.5rem;
		right: 0.5rem;
	}
</style>
