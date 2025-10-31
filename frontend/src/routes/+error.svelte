<script>
	import { page } from '$app/stores';
	import { logger } from '$lib/logger';

	// Log error for debugging
	$: if ($page.error) {
		logger.error('Page error caught by error boundary:', $page.error);
	}

	// Check if this is a 404 or other HTTP error
	const status = $page.status || 500;
	const message = $page.error?.message || 'An unexpected error occurred';

	const getErrorDetails = (code) => {
		const errors = {
			404: {
				title: 'Page Not Found',
				description: 'The page you are looking for does not exist.',
				icon: '🔍'
			},
			403: {
				title: 'Access Denied',
				description: 'You do not have permission to access this resource.',
				icon: '🔒'
			},
			500: {
				title: 'Server Error',
				description: 'Something went wrong on the server. Please try again later.',
				icon: '⚠️'
			},
			503: {
				title: 'Service Unavailable',
				description: 'The service is temporarily unavailable. Please try again later.',
				icon: '🛠️'
			},
			default: {
				title: 'Error',
				description: message || 'An unexpected error occurred.',
				icon: '❌'
			}
		};

		return errors[code] || errors.default;
	};

	const errorDetails = getErrorDetails(status);

	function goHome() {
		window.location.href = '/';
	}

	function goBack() {
		window.history.back();
	}
</script>

<svelte:head>
	<title>Error {status} - Proximity</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center px-4">
	<div class="max-w-md w-full text-center">
		<!-- Error Icon -->
		<div class="text-6xl mb-6">{errorDetails.icon}</div>

		<!-- Error Code and Title -->
		<h1 class="text-4xl font-bold text-white mb-2">{status}</h1>
		<h2 class="text-2xl font-semibold text-gray-300 mb-4">{errorDetails.title}</h2>

		<!-- Error Description -->
		<p class="text-gray-400 mb-6">{errorDetails.description}</p>

		<!-- Error Details (if available) -->
		{#if message && status >= 500}
			<div class="bg-red-900/20 border border-red-600 rounded px-4 py-2 mb-6 text-left">
				<p class="text-red-200 text-sm font-mono">{message}</p>
			</div>
		{/if}

		<!-- Action Buttons -->
		<div class="flex gap-4 justify-center">
			<button
				on:click={goHome}
				class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold transition-colors"
			>
				Go Home
			</button>
			{#if status !== 404}
				<button
					on:click={goBack}
					class="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded font-semibold transition-colors"
				>
					Go Back
				</button>
			{/if}
		</div>

		<!-- Help Text -->
		<div class="mt-8 pt-8 border-t border-gray-700">
			<p class="text-gray-500 text-sm">
				If the problem persists, please contact support or check the console for more details.
			</p>
		</div>
	</div>
</div>

<style>
	:global(body) {
		background-color: #111827;
		color: #f3f4f6;
	}
</style>
