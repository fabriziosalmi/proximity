<script lang="ts">
	/**
	 * LogViewerModal - Modal for viewing application deployment logs
	 */
	import { X, FileText, RefreshCw, Download, Copy, CheckCircle2, AlertCircle } from 'lucide-svelte';
	import { api } from '$lib/api';
	import { toasts } from '$lib/stores/toast';
	import { onMount } from 'svelte';

	export let show = false;
	export let appId: string | null = null;
	export let appName: string = '';

	let logs: any[] = [];
	let isLoading = false;
	let error: string | null = null;
	let logsContainer: HTMLDivElement;
	let autoRefresh = false;
	let refreshInterval: number | null = null;

	onMount(() => {
		return () => {
			// Clean up interval on component destroy
			if (refreshInterval) {
				clearInterval(refreshInterval);
			}
		};
	});

	async function loadLogs() {
		if (!appId) return;

		isLoading = true;
		error = null;

		try {
			const response = await api.getAppLogs(appId, 100);

			if (response.success && response.data) {
				// Ensure logs is an array
				logs = Array.isArray(response.data) ? response.data : response.data.logs || [];

				// Auto-scroll to bottom
				setTimeout(() => {
					if (logsContainer) {
						logsContainer.scrollTop = logsContainer.scrollHeight;
					}
				}, 50);
			} else {
				error = response.error || 'Failed to load logs';
			}
		} catch (err: any) {
			error = err.message || 'Failed to load logs';
			console.error('Error loading logs:', err);
		} finally {
			isLoading = false;
		}
	}

	function toggleAutoRefresh() {
		autoRefresh = !autoRefresh;

		if (autoRefresh) {
			// Refresh every 3 seconds when auto-refresh is on
			refreshInterval = setInterval(() => {
				loadLogs();
			}, 3000);
			toasts.info('Auto-refresh enabled (3 second interval)', 2000);
		} else {
			if (refreshInterval) {
				clearInterval(refreshInterval);
				refreshInterval = null;
			}
			toasts.info('Auto-refresh disabled', 2000);
		}
	}

	function copyLogsToClipboard() {
		try {
			const logsText = logs
				.map((log: any) => {
					const timestamp = log.timestamp ? `[${log.timestamp}] ` : '';
					const level = log.level ? `${log.level}: ` : '';
					return timestamp + level + log.message;
				})
				.join('\n');

			navigator.clipboard.writeText(logsText);
			toasts.success('Logs copied to clipboard!', 2000);
		} catch (err) {
			toasts.error('Failed to copy logs', 2000);
		}
	}

	function downloadLogs() {
		try {
			const logsText = logs
				.map((log: any) => {
					const timestamp = log.timestamp ? `[${log.timestamp}] ` : '';
					const level = log.level ? `${log.level}: ` : '';
					return timestamp + level + log.message;
				})
				.join('\n');

			const element = document.createElement('a');
			element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(logsText));
			element.setAttribute('download', `${appName || 'app'}-logs.txt`);
			element.style.display = 'none';
			document.body.appendChild(element);
			element.click();
			document.body.removeChild(element);

			toasts.success('Logs downloaded!', 2000);
		} catch (err) {
			toasts.error('Failed to download logs', 2000);
		}
	}

	function close() {
		show = false;
		error = null;
		logs = [];
		autoRefresh = false;
		if (refreshInterval) {
			clearInterval(refreshInterval);
			refreshInterval = null;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			close();
		}
	}

	$: if (show && appId) {
		// Load logs when modal opens
		loadLogs();
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if show && appId}
	<!-- Modal overlay -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
		on:click={close}
		on:keydown={handleKeydown}
		role="presentation"
	>
		<!-- Modal content -->
		<div
			class="h-5/6 w-11/12 max-w-4xl rounded-lg border-2 border-yellow-500/50 bg-rack-darker p-6 shadow-2xl flex flex-col"
			on:click|stopPropagation
			on:keydown|stopPropagation
			role="dialog"
			aria-modal="true"
			aria-labelledby="logs-modal-title"
		>
			<!-- Header -->
			<div class="mb-6 flex items-start justify-between">
				<div class="flex items-center gap-3">
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-yellow-500/20 text-yellow-400"
					>
						<FileText class="h-6 w-6" />
					</div>
					<div>
						<h2 id="logs-modal-title" class="text-2xl font-bold text-white">
							Deployment Logs
						</h2>
						<p class="text-sm text-gray-400">{appName}</p>
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

			<!-- Control bar -->
			<div class="mb-4 flex flex-wrap gap-2">
				<button
					on:click={loadLogs}
					disabled={isLoading}
					class="flex items-center gap-2 rounded-lg bg-yellow-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-yellow-700 disabled:cursor-not-allowed disabled:opacity-50"
				>
					<RefreshCw class="h-4 w-4 {isLoading ? 'animate-spin' : ''}" />
					Refresh
				</button>

				<button
					on:click={toggleAutoRefresh}
					class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors {autoRefresh
						? 'bg-yellow-500/20 text-yellow-400'
						: 'bg-rack-light text-gray-300 hover:bg-rack-light/80'}"
				>
					<RefreshCw class="h-4 w-4 {autoRefresh ? 'animate-spin' : ''}" />
					Auto-Refresh
				</button>

				<button
					on:click={copyLogsToClipboard}
					disabled={logs.length === 0}
					class="flex items-center gap-2 rounded-lg bg-rack-light px-3 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-rack-light/80 disabled:cursor-not-allowed disabled:opacity-50"
				>
					<Copy class="h-4 w-4" />
					Copy
				</button>

				<button
					on:click={downloadLogs}
					disabled={logs.length === 0}
					class="flex items-center gap-2 rounded-lg bg-rack-light px-3 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-rack-light/80 disabled:cursor-not-allowed disabled:opacity-50"
				>
					<Download class="h-4 w-4" />
					Download
				</button>
			</div>

			<!-- Logs container -->
			<div
				bind:this={logsContainer}
				class="flex-1 overflow-y-auto rounded-lg border border-rack-primary/30 bg-black/50 p-4 font-mono text-sm"
			>
				{#if isLoading}
					<div class="flex items-center justify-center py-8">
						<div class="flex flex-col items-center gap-2">
							<RefreshCw class="h-8 w-8 animate-spin text-yellow-500" />
							<p class="text-gray-400">Loading logs...</p>
						</div>
					</div>
				{:else if error}
					<div class="flex items-start gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
						<AlertCircle class="h-5 w-5 flex-shrink-0 text-red-400" />
						<div>
							<p class="font-medium text-red-400">Error loading logs</p>
							<p class="text-sm text-red-300">{error}</p>
						</div>
					</div>
				{:else if logs.length === 0}
					<div class="flex items-center justify-center py-8">
						<p class="text-gray-500">No logs available yet. Check back after deployment starts.</p>
					</div>
				{:else}
					<div class="space-y-1">
						{#each logs as log (log.id || logs.indexOf(log))}
							<div class="text-gray-300 hover:bg-white/5 px-2 py-1 rounded transition-colors">
								{#if log.timestamp}
									<span class="text-gray-600">[{log.timestamp}]</span>
									<span class="ml-2"></span>
								{/if}
								{#if log.level}
									<span
										class="font-medium {log.level === 'ERROR'
											? 'text-red-400'
											: log.level === 'WARNING'
												? 'text-yellow-400'
												: log.level === 'SUCCESS'
													? 'text-green-400'
													: 'text-blue-400'}"
									>
										{log.level}:
									</span>
									<span class="ml-2"></span>
								{/if}
								<span>{log.message}</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="mt-4 flex items-center justify-between border-t border-rack-primary/30 pt-4">
				<div class="text-xs text-gray-500">
					{#if logs.length > 0}
						<span>{logs.length} log entries</span>
					{:else}
						<span>No logs</span>
					{/if}
				</div>
				<button
					on:click={close}
					class="rounded-lg border border-gray-500/30 bg-rack-light px-4 py-2 font-medium text-gray-300 transition-colors hover:bg-rack-light/80"
				>
					Close
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Ensure logs container scrolls smoothly */
	:global(.log-line) {
		white-space: pre-wrap;
		word-break: break-all;
	}
</style>
