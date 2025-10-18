<script lang="ts">
	// Proximity 2.0 - Landing Page
	const features = [
		{
			title: 'Divertimento',
			description: 'Transform infrastructure management into an engaging, gamified experience.',
			icon: '🎮'
		},
		{
			title: 'Casa Digitale',
			description: 'Your unified command center for both work and play.',
			icon: '🏠'
		},
		{
			title: 'Tranquillità by Default',
			description: 'Security, backups, and reliability built-in from day one.',
			icon: '🛡️'
		}
	];
</script>

<svelte:head>
	<title>Proximity 2.0 - Welcome</title>
</svelte:head>

<div class="min-h-screen flex flex-col items-center justify-center p-8">
	<!-- Hero Section -->
	<div class="text-center mb-16 space-y-6">
		<h1 class="text-6xl font-bold bg-gradient-to-r from-rack-primary via-rack-accent to-rack-secondary bg-clip-text text-transparent">
			Proximity 2.0
		</h1>
		<p class="text-2xl text-rack-light max-w-2xl mx-auto">
			The definitive application-centric delivery platform for Proxmox
		</p>
		<div class="flex gap-4 justify-center mt-8">
			<a
				href="/store"
				class="px-8 py-3 bg-rack-primary text-white rounded-lg font-semibold hover:shadow-glow transition-all"
			>
				App Store
			</a>
			<a
				href="/apps"
				class="px-8 py-3 border border-rack-primary text-rack-primary rounded-lg font-semibold hover:bg-rack-primary hover:text-white transition-all"
			>
				My Apps
			</a>
		</div>
	</div>

	<!-- Features Grid -->
	<div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl">
		{#each features as feature}
			<div class="bg-rack-light p-8 rounded-lg border border-rack-primary/20 hover:border-rack-primary/50 transition-all hover:shadow-glow">
				<div class="text-5xl mb-4">{feature.icon}</div>
				<h3 class="text-2xl font-bold text-rack-primary mb-3">
					{feature.title}
				</h3>
				<p class="text-gray-300">
					{feature.description}
				</p>
			</div>
		{/each}
	</div>

	<!-- Tech Stack -->
	<div class="mt-16 text-center">
		<p class="text-sm text-gray-400 mb-4">Powered by</p>
		<div class="flex gap-6 items-center justify-center text-gray-500">
			<span>Django</span>
			<span>•</span>
			<span>Django Ninja</span>
			<span>•</span>
			<span>SvelteKit</span>
			<span>•</span>
			<span>Celery</span>
			<span>•</span>
			<span>Tailwind CSS</span>
		</div>
	</div>
</div>
