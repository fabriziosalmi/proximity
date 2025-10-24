<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import { toasts } from '$lib/stores/toast';
	
	let username = '';
	let password = '';
	let isLoading = false;
	let errorMessage = '';

	async function handleLogin() {
		if (!username || !password) {
			errorMessage = 'Please enter both username and password';
			return;
		}

		isLoading = true;
		errorMessage = '';

		try {
			console.log('🔐 Attempting login...', { username });
			const response = await api.login(username, password);
			console.log('📥 Login response:', response);

			if (response.success && response.data) {
				// Extract user info - HttpOnly cookies are set automatically by the browser
				const { user } = response.data;
				console.log('✅ Login successful, redirecting...', { user });
				
				// Update auth store (no token needed - using HttpOnly cookies)
				authStore.login(user);
				
				// Show success message
				toasts.success(`Welcome back, ${user.username}!`, 3000);
				
				// Redirect to home page
				goto('/');
			} else {
				console.error('❌ Login failed:', response.error);
				errorMessage = response.error || 'Login failed. Please try again.';
				toasts.error(errorMessage, 5000);
			}
		} catch (error) {
			console.error('💥 Login exception:', error);
			errorMessage = 'An unexpected error occurred. Please try again.';
			toasts.error(errorMessage, 5000);
			console.error('Login error:', error);
		} finally {
			isLoading = false;
		}
	}

	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter' && !isLoading) {
			handleLogin();
		}
	}
</script>

<svelte:head>
	<title>Login - Proximity 2.0</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center p-8 bg-gradient-to-br from-rack-darker via-rack-dark to-rack-darker">
	<div class="w-full max-w-md">
		<!-- Logo/Header -->
		<div class="text-center mb-8">
			<h1 class="text-4xl font-bold bg-gradient-to-r from-rack-primary via-rack-accent to-rack-secondary bg-clip-text text-transparent mb-2">
				Proximity 2.0
			</h1>
			<p class="text-rack-light text-sm">
				Sign in to your account
			</p>
		</div>

		<!-- Login Card -->
		<div class="bg-rack-light rounded-lg border border-rack-primary/20 p-8 shadow-lg hover:shadow-glow transition-all">
			<div class="space-y-6">
				<!-- Username Field -->
				<div>
					<label for="username" class="block text-sm font-medium text-rack-primary mb-2">
						Username or Email
					</label>
					<input
						id="username"
						name="username"
						type="text"
						autocomplete="username"
						required
						bind:value={username}
						on:keypress={handleKeyPress}
						disabled={isLoading}
						class="w-full px-4 py-3 bg-rack-darker border border-rack-primary/30 rounded-lg 
						       text-white placeholder-gray-500 
						       focus:outline-none focus:ring-2 focus:ring-rack-primary focus:border-transparent
						       disabled:opacity-50 disabled:cursor-not-allowed
						       transition-all"
						placeholder="Enter your username or email"
					/>
				</div>

				<!-- Password Field -->
				<div>
					<label for="password" class="block text-sm font-medium text-rack-primary mb-2">
						Password
					</label>
					<input
						id="password"
						name="password"
						type="password"
						autocomplete="current-password"
						required
						bind:value={password}
						on:keypress={handleKeyPress}
						disabled={isLoading}
						class="w-full px-4 py-3 bg-rack-darker border border-rack-primary/30 rounded-lg 
						       text-white placeholder-gray-500 
						       focus:outline-none focus:ring-2 focus:ring-rack-primary focus:border-transparent
						       disabled:opacity-50 disabled:cursor-not-allowed
						       transition-all"
						placeholder="Enter your password"
					/>
				</div>

				<!-- Error Message -->
				{#if errorMessage}
					<div class="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm">
						{errorMessage}
					</div>
				{/if}

				<!-- Submit Button -->
				<button
					type="button"
					on:click={handleLogin}
					disabled={isLoading}
					class="w-full px-4 py-3 bg-rack-primary text-white rounded-lg font-semibold
					       hover:shadow-glow hover:bg-rack-primary/90
					       disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none
					       transition-all duration-200
					       flex items-center justify-center gap-2"
				>
					{#if isLoading}
						<svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Signing in...
					{:else}
						Sign In
					{/if}
				</button>
			</div>

			<!-- Register Link -->
			<div class="mt-6 text-center">
				<p class="text-sm text-gray-400">
					Don't have an account?
					<a href="/register" class="text-rack-primary hover:text-rack-accent font-medium transition-colors">
						Create one now
					</a>
				</p>
			</div>

			<!-- Back to Home -->
			<div class="mt-4 text-center">
				<a href="/" class="text-sm text-gray-500 hover:text-rack-primary transition-colors">
					← Back to home
				</a>
			</div>
		</div>
	</div>
</div>
