<script>
	import { page } from '$app/stores';
	import { Home, Server, Store, HardDrive, Settings } from 'lucide-svelte';

	const navItems = [
		{ href: '/', label: 'Home', icon: Home },
		{ href: '/apps', label: 'Apps', icon: Server },
		{ href: '/store', label: 'Store', icon: Store },
		{ href: '/hosts', label: 'Hosts', icon: HardDrive },
		{ href: '/settings', label: 'Settings', icon: Settings }
	];

	function isActive(href, pathname) {
		return pathname === href || (href !== '/' && pathname.startsWith(href));
	}
</script>

<nav class="rack-nav">
	<!-- Decorative screws -->
	<div class="screw screw-tl"></div>
	<div class="screw screw-tr"></div>

	<ul class="nav-list">
		{#each navItems as item}
			<li class="nav-item">
				<a href={item.href} class="nav-link" class:active={isActive(item.href, $page.url.pathname)}>
					<div class="icon">
						<svelte:component this={item.icon} size={20} />
					</div>
					<span class="label">{item.label}</span>
					<div class="led" class:led-active={isActive(item.href, $page.url.pathname)}></div>
				</a>
			</li>
		{/each}
	</ul>

	<!-- Bottom decorative screws -->
	<div class="screw screw-bl"></div>
	<div class="screw screw-br"></div>
</nav>

<style>
	.rack-nav {
		position: relative;
		width: 100%;
		height: 100%;
		background: var(--bg-rack-nav, linear-gradient(to bottom, #374151, #1f2937));
		border-right: 1px solid var(--border-rack, #4b5563);
		display: flex;
		flex-direction: column;
		padding: 1rem 0;
	}

	/* Decorative screws */
	.screw {
		position: absolute;
		width: 8px;
		height: 8px;
		background: radial-gradient(circle, #4b5563 0%, #1f2937 70%);
		border-radius: 50%;
		border: 1px solid #0f172a;
		box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
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
		left: 0.5rem;
	}
	.screw-tr {
		top: 0.5rem;
		right: 0.5rem;
	}
	.screw-bl {
		bottom: 0.5rem;
		left: 0.5rem;
	}
	.screw-br {
		bottom: 0.5rem;
		right: 0.5rem;
	}

	.nav-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.nav-item {
		margin: 0;
	}

	.nav-link {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		padding: 0.75rem 0;
		text-decoration: none;
		color: var(--color-text-secondary, #9ca3af);
		transition: all 0.2s;
		position: relative;
	}

	.nav-link:hover {
		background: rgba(255, 255, 255, 0.05);
		color: var(--color-text-primary, #e5e7eb);
	}

	.nav-link.active {
		color: var(--color-text-primary, #e5e7eb);
		background: rgba(0, 212, 255, 0.1);
		border-left: 2px solid var(--color-accent-bright, #00d4ff);
	}

	.icon {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.label {
		font-size: 0.625rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.led {
		width: 5px;
		height: 5px;
		border-radius: 50%;
		background: var(--color-led-inactive, #374151);
		transition: all 0.3s;
	}

	.led-active {
		background: var(--color-led-active, #4ade80);
		animation: pulse-green 2s ease-in-out infinite;
	}
</style>
