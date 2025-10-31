<script lang="ts">
	/**
	 * CloneModal - Modal for cloning an existing application
	 */
	import { X, Copy, AlertCircle } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';

	export let show = false;
	export let sourceApp: any = null;

	const dispatch = createEventDispatcher();

	let newHostname = '';
	let error = '';
	let initializedHostname = false;

	$: if (sourceApp && show && !initializedHostname) {
		// Auto-suggest a hostname based on source app (only once when modal opens)
		newHostname = `${sourceApp.hostname}-clone`;
		error = '';
		initializedHostname = true;
	}

	$: if (!show) {
		// Reset initialization flag when modal closes
		initializedHostname = false;
	}

	function validateHostname(hostname: string): boolean {
		if (!hostname || hostname.length < 1) {
			error = 'Hostname is required';
			return false;
		}
		if (hostname.length > 63) {
			error = 'Hostname cannot exceed 63 characters';
			return false;
		}
		// 🔐 RFC 952/1123 hostname validation (lowercase only)
		const hostnameRegex = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$/;
		if (!hostnameRegex.test(hostname)) {
			error = 'Hostname must start and end with alphanumeric, contain only lowercase letters, numbers, and hyphens';
			return false;
		}
		error = '';
		return true;
	}

	function handleSubmit() {
		if (!validateHostname(newHostname)) {
			return;
		}
		dispatch('submit', newHostname);
		close();
	}

	function close() {
		show = false;
		newHostname = '';
		error = '';
		dispatch('close');
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			close();
		} else if (event.key === 'Enter' && !error && newHostname.length >= 3) {
			handleSubmit();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if show && sourceApp}
	<!-- Modal overlay -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
		on:click={close}
		on:keydown={handleKeydown}
		role="presentation"
	>
		<!-- Modal content -->
		<div
			class="w-full max-w-lg rounded-lg border-2 border-blue-500/50 bg-rack-darker p-6 shadow-2xl"
			on:click|stopPropagation
			on:keydown|stopPropagation
			role="dialog"
			aria-modal="true"
			aria-labelledby="clone-modal-title"
		>
			<!-- Header -->
			<div class="mb-6 flex items-start justify-between">
				<div class="flex items-center gap-3">
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400"
					>
						<Copy class="h-6 w-6" />
					</div>
					<div>
						<h2 id="clone-modal-title" class="text-2xl font-bold text-white">Clone Application</h2>
						<p class="text-sm text-gray-400">Create a duplicate of {sourceApp.name}</p>
					</div>
				</div>
				<button
					on:click={close}
					class="rounded-lg p-2 text-gray-400 transition-colors hover:bg-rack-light hover:text-white"
					aria-label="Close modal"
				>
					<X class="h-5 w-5" />
				</button>
			</div>

			<!-- Source app info -->
			<div class="mb-6 rounded-lg border border-rack-primary/30 bg-rack-light p-4">
				<p class="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">
					Cloning From
				</p>
				<div class="flex items-center justify-between">
					<div>
						<p class="font-semibold text-white">{sourceApp.name}</p>
						<p class="text-sm text-gray-400">{sourceApp.hostname}</p>
					</div>
					<div class="rounded-full px-3 py-1 text-xs font-medium {sourceApp.status === 'running' ? 'bg-green-500/10 text-green-400' : 'bg-gray-500/10 text-gray-400'}">
						{sourceApp.status}
					</div>
				</div>
			</div>

			<!-- Hostname input -->
			<div class="mb-6">
				<label for="new-hostname" class="mb-2 block text-sm font-medium text-gray-300">
					New Hostname
				</label>
				<input
					id="new-hostname"
					type="text"
					bind:value={newHostname}
					on:input={() => validateHostname(newHostname)}
					placeholder="e.g., my-app-clone"
					class="w-full rounded-lg border bg-rack-light px-4 py-3 text-white transition-colors focus:outline-none focus:ring-2"
					class:border-rack-primary={!error && newHostname.length > 0}
					class:focus:ring-rack-primary={!error}
					class:border-red-500={error}
					class:focus:ring-red-500={error}
					autocomplete="off"
					autofocus
				/>
				{#if error}
					<div class="mt-2 flex items-center gap-2 text-sm text-red-400">
						<AlertCircle class="h-4 w-4" />
						<span>{error}</span>
					</div>
				{/if}
				<p class="mt-2 text-xs text-gray-500">
					The cloned application will have the same configuration as the source.
				</p>
			</div>

			<!-- Actions -->
			<div class="flex gap-3">
				<button
					on:click={close}
					class="flex-1 rounded-lg border border-gray-500/30 bg-rack-light px-4 py-3 font-medium text-gray-300 transition-colors hover:bg-rack-light/80"
				>
					Cancel
				</button>
				<button
					on:click={handleSubmit}
					disabled={!!error || newHostname.length < 3}
					class="flex-1 rounded-lg bg-blue-500 px-4 py-3 font-medium text-white transition-colors hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
				>
					<div class="flex items-center justify-center gap-2">
						<Copy class="h-4 w-4" />
						<span>Clone Application</span>
					</div>
				</button>
			</div>
		</div>
	</div>
{/if}
