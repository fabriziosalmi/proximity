<script lang="ts">
	import { onMount } from 'svelte';
	import { ThemeService, type Theme } from '$lib/services/ThemeService';

	let themes: Theme[] = [];
	let currentTheme: string = 'dark';
	let isChanging = false;

	onMount(() => {
		themes = ThemeService.getThemes();
		currentTheme = ThemeService.getCurrentTheme();

		// Listen for theme changes from other components
		const handleThemeChange = (event: CustomEvent) => {
			currentTheme = event.detail.themeId;
		};

		window.addEventListener('theme-changed', handleThemeChange as EventListener);

		return () => {
			window.removeEventListener('theme-changed', handleThemeChange as EventListener);
		};
	});

	async function handleThemeChange(themeId: string) {
		if (isChanging || themeId === currentTheme) return;

		isChanging = true;
		try {
			await ThemeService.setTheme(themeId);
			currentTheme = themeId;
		} catch (error) {
			logger.error('Failed to change theme:', error);
		} finally {
			isChanging = false;
		}
	}
</script>

<div class="theme-switcher-card">
	<div class="card-header">
		<h3>🎨 Appearance</h3>
		<p class="subtitle">Choose your visual experience</p>
	</div>

	<div class="theme-grid">
		{#each themes as theme}
			<button
				class="theme-option"
				class:active={currentTheme === theme.id}
				class:changing={isChanging}
				disabled={isChanging}
				on:click={() => handleThemeChange(theme.id)}
			>
				<div class="theme-icon">{theme.id === 'dark' ? '🌙' : theme.id === 'light' ? '☀️' : '💚'}</div>
				<div class="theme-info">
					<div class="theme-name">{theme.name}</div>
					<div class="theme-description">{theme.description}</div>
				</div>
				{#if currentTheme === theme.id}
					<div class="active-indicator">✓</div>
				{/if}
			</button>
		{/each}
	</div>

	{#if isChanging}
		<div class="loading-indicator">
			<div class="spinner"></div>
			Applying theme...
		</div>
	{/if}
</div>

<style>
	.theme-switcher-card {
		background: var(--bg-card, #1f2937);
		border: 1px solid var(--border-color-primary, #4b5563);
		border-radius: 8px;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.card-header {
		margin-bottom: 1.5rem;
	}

	.card-header h3 {
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--color-text-primary, #e5e7eb);
		margin: 0 0 0.5rem 0;
	}

	.subtitle {
		font-size: 0.875rem;
		color: var(--color-text-secondary, #9ca3af);
		margin: 0;
	}

	.theme-grid {
		display: grid;
		gap: 1rem;
		grid-template-columns: 1fr;
	}

	@media (min-width: 768px) {
		.theme-grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}

	.theme-option {
		position: relative;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.75rem;
		padding: 1.5rem;
		background: var(--bg-card-hover, #374151);
		border: 2px solid var(--border-color-secondary, #374151);
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.theme-option:hover:not(:disabled) {
		border-color: var(--color-accent, #3b82f6);
		box-shadow: var(--card-hover-shadow, 0 0 20px rgba(0, 212, 255, 0.3));
		transform: translateY(-2px);
	}

	.theme-option.active {
		border-color: var(--color-accent-bright, #00d4ff);
		background: var(--bg-card, #1f2937);
		box-shadow: 0 0 15px var(--color-accent-bright, #00d4ff);
	}

	.theme-option:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.theme-icon {
		font-size: 3rem;
		line-height: 1;
	}

	.theme-info {
		text-align: center;
	}

	.theme-name {
		font-size: 1rem;
		font-weight: 600;
		color: var(--color-text-primary, #e5e7eb);
		margin-bottom: 0.25rem;
	}

	.theme-description {
		font-size: 0.75rem;
		color: var(--color-text-secondary, #9ca3af);
		line-height: 1.4;
	}

	.active-indicator {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		width: 1.5rem;
		height: 1.5rem;
		background: var(--color-accent-bright, #00d4ff);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
		color: #000;
		font-weight: bold;
	}

	.loading-indicator {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		justify-content: center;
		margin-top: 1rem;
		padding: 1rem;
		background: var(--bg-card, #1f2937);
		border-radius: 6px;
		font-size: 0.875rem;
		color: var(--color-text-secondary, #9ca3af);
	}

	.spinner {
		width: 1rem;
		height: 1rem;
		border: 2px solid var(--border-color-primary, #4b5563);
		border-top-color: var(--color-accent-bright, #00d4ff);
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>
