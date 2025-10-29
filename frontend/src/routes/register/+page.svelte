<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import { toasts } from '$lib/stores/toast';
	
	let username = '';
	let email = '';
	let password = '';
	let confirmPassword = '';
	let isLoading = false;
	let errorMessage = '';
	let validationErrors: Record<string, string> = {};

	function validateForm(): boolean {
		validationErrors = {};

		// Username validation
		if (!username) {
			validationErrors.username = 'Username is required';
		} else if (username.length < 3) {
			validationErrors.username = 'Username must be at least 3 characters';
		}

		// Email validation
		if (!email) {
			validationErrors.email = 'Email is required';
		} else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
			validationErrors.email = 'Please enter a valid email address';
		}

		// Password validation
		if (!password) {
			validationErrors.password = 'Password is required';
		} else if (password.length < 8) {
			validationErrors.password = 'Password must be at least 8 characters';
		}

		// Confirm password validation
		if (!confirmPassword) {
			validationErrors.confirmPassword = 'Please confirm your password';
		} else if (password !== confirmPassword) {
			validationErrors.confirmPassword = 'Passwords do not match';
		}

		return Object.keys(validationErrors).length === 0;
	}

	async function handleRegister() {
		errorMessage = '';

		if (!validateForm()) {
			return;
		}

		isLoading = true;

		try {
			const response = await api.register(username, email, password);

			if (response.success && response.data) {
				// Show success message
				toasts.success('Account created successfully! Please log in.', 5000);
				
				// Redirect to login
				goto('/login');
			} else {
				// Handle API errors
				if (response.error) {
					// Try to parse validation errors from backend
					try {
						const errorData = JSON.parse(response.error);
						if (Array.isArray(errorData.detail)) {
							errorData.detail.forEach((err: any) => {
								const field = err.loc[err.loc.length - 1];
								validationErrors[field] = err.msg;
							});
						} else {
							errorMessage = response.error;
						}
					} catch {
						errorMessage = response.error;
					}
				} else {
					errorMessage = 'Registration failed. Please try again.';
				}
				
				toasts.error(errorMessage || 'Registration failed', 5000);
			}
		} catch (error) {
			errorMessage = 'An unexpected error occurred. Please try again.';
			toasts.error(errorMessage, 5000);
			console.error('Registration error:', error);
		} finally {
			isLoading = false;
		}
	}

	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter' && !isLoading) {
			handleRegister();
		}
	}
</script>

<svelte:head>
	<title>Register - Proximity 2.0</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center p-8 bg-gradient-to-br from-rack-darker via-rack-dark to-rack-darker">
	<div class="w-full max-w-md">
		<!-- Logo/Header -->
		<div class="text-center mb-8">
			<h1 class="text-4xl font-bold bg-gradient-to-r from-rack-primary via-rack-accent to-rack-secondary bg-clip-text text-transparent mb-2">
				Proximity 2.0
			</h1>
			<p class="text-rack-light text-sm">
				Create your account
			</p>
		</div>

		<!-- Register Card -->
		<div class="bg-rack-light rounded-lg border border-rack-primary/20 p-8 shadow-lg hover:shadow-glow transition-all">
			<form on:submit|preventDefault={handleRegister} class="space-y-5">
				<!-- Username Field -->
				<div>
					<label for="username" class="block text-sm font-medium text-rack-primary mb-2">
						Username
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
						       {validationErrors.username ? 'border-red-500' : ''}
						       transition-all"
						placeholder="Choose a username"
					/>
					{#if validationErrors.username}
						<p class="mt-1 text-sm text-red-400">{validationErrors.username}</p>
					{/if}
				</div>

				<!-- Email Field -->
				<div>
					<label for="email" class="block text-sm font-medium text-rack-primary mb-2">
						Email Address
					</label>
					<input
						id="email"
						name="email"
						type="email"
						autocomplete="email"
						required
						bind:value={email}
						on:keypress={handleKeyPress}
						disabled={isLoading}
						class="w-full px-4 py-3 bg-rack-darker border border-rack-primary/30 rounded-lg 
						       text-white placeholder-gray-500 
						       focus:outline-none focus:ring-2 focus:ring-rack-primary focus:border-transparent
						       disabled:opacity-50 disabled:cursor-not-allowed
						       {validationErrors.email ? 'border-red-500' : ''}
						       transition-all"
						placeholder="your.email@example.com"
					/>
					{#if validationErrors.email}
						<p class="mt-1 text-sm text-red-400">{validationErrors.email}</p>
					{/if}
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
						autocomplete="new-password"
						required
						bind:value={password}
						on:keypress={handleKeyPress}
						disabled={isLoading}
						class="w-full px-4 py-3 bg-rack-darker border border-rack-primary/30 rounded-lg 
						       text-white placeholder-gray-500 
						       focus:outline-none focus:ring-2 focus:ring-rack-primary focus:border-transparent
						       disabled:opacity-50 disabled:cursor-not-allowed
						       {validationErrors.password ? 'border-red-500' : ''}
						       transition-all"
						placeholder="Create a strong password"
					/>
					{#if validationErrors.password}
						<p class="mt-1 text-sm text-red-400">{validationErrors.password}</p>
					{/if}
					<p class="mt-1 text-xs text-gray-400">At least 8 characters</p>
				</div>

				<!-- Confirm Password Field -->
				<div>
					<label for="confirmPassword" class="block text-sm font-medium text-rack-primary mb-2">
						Confirm Password
					</label>
					<input
						id="confirmPassword"
						name="confirmPassword"
						type="password"
						autocomplete="new-password"
						required
						bind:value={confirmPassword}
						on:keypress={handleKeyPress}
						disabled={isLoading}
						class="w-full px-4 py-3 bg-rack-darker border border-rack-primary/30 rounded-lg 
						       text-white placeholder-gray-500 
						       focus:outline-none focus:ring-2 focus:ring-rack-primary focus:border-transparent
						       disabled:opacity-50 disabled:cursor-not-allowed
						       {validationErrors.confirmPassword ? 'border-red-500' : ''}
						       transition-all"
						placeholder="Re-enter your password"
					/>
					{#if validationErrors.confirmPassword}
						<p class="mt-1 text-sm text-red-400">{validationErrors.confirmPassword}</p>
					{/if}
				</div>

				<!-- Error Message -->
				{#if errorMessage}
					<div class="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm">
						{errorMessage}
					</div>
				{/if}

				<!-- Submit Button -->
				<button
					type="submit"
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
						Creating account...
					{:else}
						Create Account
					{/if}
				</button>
			</form>

			<!-- Login Link -->
			<div class="mt-6 text-center">
				<p class="text-sm text-gray-400">
					Already have an account?
					<a href="/login" class="text-rack-primary hover:text-rack-accent font-medium transition-colors">
						Sign in
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
