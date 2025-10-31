<script lang="ts">
	/**
	 * BackupManager Component
	 * Comprehensive backup management UI for applications
	 */
	import { onMount, onDestroy } from 'svelte';
	import {
		Loader2,
		Download,
		Plus,
		RotateCcw,
		Trash2,
		HardDrive,
		AlertTriangle,
		CheckCircle,
		Clock
	} from 'lucide-svelte';
	import { api } from '$lib/api';
	import { createBackup as createBackupAction, restoreBackup as restoreBackupAction, deleteBackup as deleteBackupAction } from '$lib/stores/actions';

	// Props
	export let appId: string;
	export let appName: string = '';

	// State
	let loading = true;
	let backups: any[] = [];
	let creatingBackup = false;
	let pollingInterval: any = null;

	// Confirmation modals
	let showRestoreModal = false;
	let showDeleteModal = false;
	let selectedBackup: any = null;

	// Action states
	let actionInProgress: Record<number, boolean> = {};

	async function loadBackups() {
		try {
			const response = await api.listAppBackups(appId);

			if (response.success && response.data) {
				backups = response.data.backups || [];
			} else {
				logger.error('Failed to load backups:', response.error);
			}
		} catch (err) {
			logger.error('Exception loading backups:', err);
		} finally {
			loading = false;
		}
	}

	async function createBackup() {
		creatingBackup = true;

		// Use centralized action dispatcher (handles API, toasts, and sounds)
		const result = await createBackupAction(appId);

		if (result.success && result.data) {
			// Optimistic update - add new backup to list
			const newBackup = {
				id: result.data.id,
				status: 'creating',
				created_at: new Date().toISOString(),
				file_name: 'creating...',
				size_gb: 0,
				is_in_progress: true
			};
			backups = [newBackup, ...backups];

			// Start polling if not already active
			startPolling();
		}

		creatingBackup = false;
	}

	function openRestoreModal(backup: any) {
		selectedBackup = backup;
		showRestoreModal = true;
	}

	function openDeleteModal(backup: any) {
		selectedBackup = backup;
		showDeleteModal = true;
	}

	async function confirmRestore() {
		if (!selectedBackup) return;

		const backupId = selectedBackup.id;
		const backupFilename = selectedBackup.file_name;
		showRestoreModal = false;
		actionInProgress[backupId] = true;
		actionInProgress = { ...actionInProgress };

		// Use centralized action dispatcher (handles API, toasts, and sounds)
		const result = await restoreBackupAction(appId, backupId, backupFilename);

		if (result.success) {
			// Update backup status to restoring
			backups = backups.map((b) =>
				b.id === backupId ? { ...b, status: 'restoring', is_in_progress: true } : b
			);

			// Start polling
			startPolling();
		}

		actionInProgress[backupId] = false;
		actionInProgress = { ...actionInProgress };
		selectedBackup = null;
	}

	async function confirmDelete() {
		if (!selectedBackup) return;

		const backupId = selectedBackup.id;
		showDeleteModal = false;
		actionInProgress[backupId] = true;
		actionInProgress = { ...actionInProgress };

		// Use centralized action dispatcher (handles API, toasts, and sounds)
		const result = await deleteBackupAction(appId, backupId);

		if (result.success) {
			// Remove backup from list
			backups = backups.filter((b) => b.id !== backupId);
		}

		actionInProgress[backupId] = false;
		actionInProgress = { ...actionInProgress };
		selectedBackup = null;
	}

	function startPolling() {
		if (pollingInterval) return; // Already polling

		pollingInterval = setInterval(async () => {
			const inProgressBackups = backups.filter(
				(b) => b.status === 'creating' || b.status === 'restoring' || b.status === 'deleting'
			);

			if (inProgressBackups.length === 0) {
				stopPolling();
				return;
			}

			// Refresh all backups to get latest status
			await loadBackups();
		}, 5000); // Poll every 5 seconds
	}

	function stopPolling() {
		if (pollingInterval) {
			clearInterval(pollingInterval);
			pollingInterval = null;
		}
	}

	function getStatusBadgeClass(status: string) {
		switch (status) {
			case 'completed':
				return 'status-completed';
			case 'creating':
			case 'restoring':
				return 'status-in-progress';
			case 'failed':
				return 'status-failed';
			default:
				return 'status-default';
		}
	}

	function getStatusIcon(status: string) {
		switch (status) {
			case 'completed':
				return CheckCircle;
			case 'creating':
			case 'restoring':
				return Clock;
			case 'failed':
				return AlertTriangle;
			default:
				return HardDrive;
		}
	}

	function formatDate(dateString: string) {
		const date = new Date(dateString);
		return date.toLocaleString();
	}

	function formatSize(sizeGb: number) {
		if (sizeGb < 1) {
			return `${Math.round(sizeGb * 1024)} MB`;
		}
		return `${sizeGb.toFixed(2)} GB`;
	}

	onMount(() => {
		loadBackups();

		// Check if we need to start polling immediately
		if (backups.some((b) => b.is_in_progress)) {
			startPolling();
		}
	});

	onDestroy(() => {
		stopPolling();
	});
</script>

<div class="backup-manager">
	<!-- Header -->
	<div class="backup-header">
		<div class="header-left">
			<HardDrive class="h-6 w-6 text-blue-400" />
			<h2 class="backup-title">Backups</h2>
		</div>
		<button
			on:click={createBackup}
			disabled={creatingBackup}
			class="btn-create-backup"
			data-testid="create-backup-button"
		>
			{#if creatingBackup}
				<Loader2 class="h-4 w-4 animate-spin" />
			{:else}
				<Plus class="h-4 w-4" />
			{/if}
			Create Backup
		</button>
	</div>

	<!-- Loading State -->
	{#if loading}
		<div class="flex items-center justify-center py-12">
			<Loader2 class="h-8 w-8 animate-spin text-blue-400" />
			<span class="ml-3 text-gray-400">Loading backups...</span>
		</div>
	{:else if backups.length === 0}
		<!-- Empty State -->
		<div class="empty-state">
			<HardDrive class="h-16 w-16 text-gray-500" />
			<p class="mt-4 text-lg text-gray-400">No backups yet</p>
			<p class="mt-2 text-sm text-gray-500">Create your first backup to protect your data</p>
		</div>
	{:else}
		<!-- Backup List -->
		<div class="backup-list">
			{#each backups as backup (backup.id)}
				<div
					class="backup-card"
					class:backup-in-progress={backup.is_in_progress}
					data-testid="backup-card-{backup.id}"
				>
					<!-- Status Badge -->
					<div class="backup-status">
						<div class="status-badge {getStatusBadgeClass(backup.status)}">
							<svelte:component this={getStatusIcon(backup.status)} class="h-4 w-4" />
							<span>{backup.status}</span>
						</div>
					</div>

					<!-- Backup Info -->
					<div class="backup-info">
						<div class="backup-filename">{backup.file_name}</div>
						<div class="backup-meta">
							<span class="meta-item">
								<Clock class="h-3 w-3" />
								{formatDate(backup.created_at)}
							</span>
							{#if backup.size_gb}
								<span class="meta-item">
									<Download class="h-3 w-3" />
									{formatSize(backup.size_gb)}
								</span>
							{/if}
						</div>
					</div>

					<!-- Actions -->
					<div class="backup-actions">
						{#if backup.status === 'completed'}
							<button
								on:click={() => openRestoreModal(backup)}
								disabled={actionInProgress[backup.id]}
								class="btn-action btn-restore"
								title="Restore from backup"
								data-testid="restore-button-{backup.id}"
							>
								{#if actionInProgress[backup.id]}
									<Loader2 class="h-4 w-4 animate-spin" />
								{:else}
									<RotateCcw class="h-4 w-4" />
								{/if}
							</button>
							<button
								on:click={() => openDeleteModal(backup)}
								disabled={actionInProgress[backup.id]}
								class="btn-action btn-delete"
								title="Delete backup"
								data-testid="delete-button-{backup.id}"
							>
								{#if actionInProgress[backup.id]}
									<Loader2 class="h-4 w-4 animate-spin" />
								{:else}
									<Trash2 class="h-4 w-4" />
								{/if}
							</button>
						{:else if backup.is_in_progress}
							<span class="text-xs text-gray-500">In progress...</span>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Restore Confirmation Modal -->
{#if showRestoreModal && selectedBackup}
	<div class="modal-overlay" on:click={() => (showRestoreModal = false)}>
		<div class="modal-content" on:click|stopPropagation data-testid="restore-modal">
			<div class="modal-header">
				<AlertTriangle class="h-6 w-6 text-yellow-400" />
				<h3 class="modal-title">Restore from Backup?</h3>
			</div>
			<div class="modal-body">
				<p class="modal-warning">
					<strong>Warning:</strong> This action will permanently overwrite the current application
					state with the backup data.
				</p>
				<p class="modal-details">
					Backup: <code>{selectedBackup.file_name}</code><br />
					Created: {formatDate(selectedBackup.created_at)}
				</p>
				<p class="modal-question">Are you sure you want to continue?</p>
			</div>
			<div class="modal-actions">
				<button
					on:click={() => (showRestoreModal = false)}
					class="btn-modal btn-cancel"
					data-testid="restore-cancel-button"
				>
					Cancel
				</button>
				<button
					on:click={confirmRestore}
					class="btn-modal btn-confirm-restore"
					data-testid="restore-confirm-button"
				>
					<RotateCcw class="h-4 w-4" />
					Restore Backup
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Delete Confirmation Modal -->
{#if showDeleteModal && selectedBackup}
	<div class="modal-overlay" on:click={() => (showDeleteModal = false)}>
		<div class="modal-content" on:click|stopPropagation data-testid="delete-modal">
			<div class="modal-header">
				<AlertTriangle class="h-6 w-6 text-red-400" />
				<h3 class="modal-title">Delete Backup?</h3>
			</div>
			<div class="modal-body">
				<p class="modal-warning">
					<strong>Warning:</strong> This action cannot be undone. The backup file will be permanently
					deleted from storage.
				</p>
				<p class="modal-details">
					Backup: <code>{selectedBackup.file_name}</code><br />
					Size: {formatSize(selectedBackup.size_gb || 0)}
				</p>
				<p class="modal-question">Are you sure you want to delete this backup?</p>
			</div>
			<div class="modal-actions">
				<button
					on:click={() => (showDeleteModal = false)}
					class="btn-modal btn-cancel"
					data-testid="delete-cancel-button"
				>
					Cancel
				</button>
				<button
					on:click={confirmDelete}
					class="btn-modal btn-confirm-delete"
					data-testid="delete-confirm-button"
				>
					<Trash2 class="h-4 w-4" />
					Delete Permanently
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.backup-manager {
		background: var(--bg-card, #1f2937);
		border: 1px solid var(--border-color-primary, #4b5563);
		border-radius: 0.75rem;
		padding: 2rem;
		margin-top: 2rem;
	}

	.backup-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid var(--border-color-secondary, #374151);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.backup-title {
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--color-text-primary, #e5e7eb);
		margin: 0;
	}

	.btn-create-backup {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 1.25rem;
		background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
		color: white;
		border: none;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
		box-shadow: 0 2px 4px rgba(14, 165, 233, 0.3);
	}

	.btn-create-backup:hover:not(:disabled) {
		background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
		box-shadow: 0 0 20px rgba(14, 165, 233, 0.4);
	}

	.btn-create-backup:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 4rem 2rem;
		text-align: center;
	}

	.backup-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.backup-card {
		display: grid;
		grid-template-columns: auto 1fr auto;
		gap: 1rem;
		align-items: center;
		padding: 1rem;
		background: rgba(0, 0, 0, 0.2);
		border: 1px solid var(--border-color-secondary, #374151);
		border-radius: 0.5rem;
		transition: all 0.2s ease;
	}

	.backup-card:hover {
		border-color: var(--color-accent, #3b82f6);
		background: rgba(0, 0, 0, 0.3);
	}

	.backup-in-progress {
		animation: pulse-glow 2s ease-in-out infinite;
		border-color: rgba(59, 130, 246, 0.5);
	}

	@keyframes pulse-glow {
		0%,
		100% {
			box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
		}
		50% {
			box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
		}
	}

	.backup-status {
		flex-shrink: 0;
	}

	.status-badge {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.375rem 0.75rem;
		border-radius: 0.375rem;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.status-completed {
		background: rgba(34, 197, 94, 0.1);
		color: #22c55e;
		border: 1px solid rgba(34, 197, 94, 0.3);
	}

	.status-in-progress {
		background: rgba(59, 130, 246, 0.1);
		color: #3b82f6;
		border: 1px solid rgba(59, 130, 246, 0.3);
		animation: pulse-text 2s ease-in-out infinite;
	}

	@keyframes pulse-text {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.7;
		}
	}

	.status-failed {
		background: rgba(239, 68, 68, 0.1);
		color: #ef4444;
		border: 1px solid rgba(239, 68, 68, 0.3);
	}

	.status-default {
		background: rgba(156, 163, 175, 0.1);
		color: #9ca3af;
		border: 1px solid rgba(156, 163, 175, 0.3);
	}

	.backup-info {
		flex: 1;
		min-width: 0;
	}

	.backup-filename {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--color-text-primary, #e5e7eb);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.backup-meta {
		display: flex;
		gap: 1rem;
		margin-top: 0.25rem;
	}

	.meta-item {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.75rem;
		color: var(--color-text-secondary, #9ca3af);
	}

	.backup-actions {
		display: flex;
		gap: 0.5rem;
		flex-shrink: 0;
	}

	.btn-action {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		border-radius: 0.375rem;
		border: 1px solid transparent;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.btn-action:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-restore {
		background: rgba(59, 130, 246, 0.1);
		color: #3b82f6;
		border-color: rgba(59, 130, 246, 0.3);
	}

	.btn-restore:hover:not(:disabled) {
		background: rgba(59, 130, 246, 0.2);
		border-color: #3b82f6;
	}

	.btn-delete {
		background: rgba(239, 68, 68, 0.1);
		color: #ef4444;
		border-color: rgba(239, 68, 68, 0.3);
	}

	.btn-delete:hover:not(:disabled) {
		background: rgba(239, 68, 68, 0.2);
		border-color: #ef4444;
	}

	/* Modal Styles */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.75);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		backdrop-filter: blur(4px);
	}

	.modal-content {
		background: var(--bg-card, #1f2937);
		border: 1px solid var(--border-color-primary, #4b5563);
		border-radius: 0.75rem;
		max-width: 500px;
		width: 90%;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
	}

	.modal-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1.5rem;
		border-bottom: 1px solid var(--border-color-secondary, #374151);
	}

	.modal-title {
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--color-text-primary, #e5e7eb);
		margin: 0;
	}

	.modal-body {
		padding: 1.5rem;
	}

	.modal-warning {
		padding: 1rem;
		background: rgba(234, 179, 8, 0.1);
		border: 1px solid rgba(234, 179, 8, 0.3);
		border-radius: 0.375rem;
		color: #fbbf24;
		font-size: 0.875rem;
		line-height: 1.5;
		margin-bottom: 1rem;
	}

	.modal-details {
		font-size: 0.875rem;
		color: var(--color-text-secondary, #9ca3af);
		line-height: 1.6;
		margin-bottom: 1rem;
	}

	.modal-details code {
		background: rgba(0, 0, 0, 0.3);
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-family: monospace;
		color: var(--color-text-primary, #e5e7eb);
	}

	.modal-question {
		font-size: 0.875rem;
		color: var(--color-text-primary, #e5e7eb);
		font-weight: 500;
	}

	.modal-actions {
		display: flex;
		gap: 0.75rem;
		justify-content: flex-end;
		padding: 1.5rem;
		border-top: 1px solid var(--border-color-secondary, #374151);
	}

	.btn-modal {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 1.25rem;
		border: none;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.btn-cancel {
		background: var(--bg-card, #1f2937);
		color: var(--color-text-primary, #e5e7eb);
		border: 1px solid var(--border-color-primary, #4b5563);
	}

	.btn-cancel:hover {
		border-color: var(--color-accent, #3b82f6);
		background: rgba(59, 130, 246, 0.1);
	}

	.btn-confirm-restore {
		background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
		color: white;
		box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
	}

	.btn-confirm-restore:hover {
		background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
		box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
	}

	.btn-confirm-delete {
		background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
		color: white;
		box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
	}

	.btn-confirm-delete:hover {
		background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
		box-shadow: 0 0 20px rgba(239, 68, 68, 0.4);
	}

	@media (max-width: 768px) {
		.backup-card {
			grid-template-columns: 1fr;
			gap: 0.75rem;
		}

		.backup-actions {
			justify-content: flex-end;
		}
	}
</style>
