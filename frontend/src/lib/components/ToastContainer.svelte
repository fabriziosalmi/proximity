<script lang="ts">
	/**
	 * ToastContainer - DEPRECATED in favor of MasterControlRack LED notifications
	 *
	 * All notifications are now displayed on the Master Control Rack LCD/LED system
	 * to prevent layout shift and maintain the skeuomorphic design consistency.
	 *
	 * This component is kept for backward compatibility but is hidden by default.
	 * Remove this component import from +layout.svelte when ready.
	 */
	import { toasts } from '$lib/stores/toast';
	import { CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-svelte';
	import { fly, fade } from 'svelte/transition';

	function getIcon(type: string) {
		const icons = {
			success: CheckCircle,
			error: XCircle,
			info: Info,
			warning: AlertTriangle
		};
		return icons[type as keyof typeof icons] || Info;
	}

	function getColorClasses(type: string): string {
		const classes = {
			success: 'bg-green-500/10 border-green-500/50 text-green-400',
			error: 'bg-red-500/10 border-red-500/50 text-red-400',
			info: 'bg-blue-500/10 border-blue-500/50 text-blue-400',
			warning: 'bg-yellow-500/10 border-yellow-500/50 text-yellow-400'
		};
		return classes[type as keyof typeof classes] || classes.info;
	}
</script>

<!-- HIDDEN: Notifications now show on Master Control Rack LCD -->
<div class="toast-container fixed right-4 top-4 z-50 flex flex-col gap-2 hidden">
	{#each $toasts as toast (toast.id)}
		<div
			in:fly={{ x: 300, duration: 300 }}
			out:fade={{ duration: 200 }}
			class="flex min-w-[300px] max-w-md items-start gap-3 rounded-lg border-2 p-4 shadow-glow {getColorClasses(
				toast.type
			)}"
		>
			<svelte:component this={getIcon(toast.type)} class="h-5 w-5 flex-shrink-0" />
			<p class="flex-1 text-sm">{toast.message}</p>
			<button
				on:click={() => toasts.remove(toast.id)}
				class="flex-shrink-0 text-current opacity-70 transition-opacity hover:opacity-100"
				aria-label="Close notification"
			>
				<X class="h-4 w-4" />
			</button>
		</div>
	{/each}
</div>

<style>
	.toast-container {
		pointer-events: none;
	}

	.toast-container > * {
		pointer-events: auto;
	}
</style>
