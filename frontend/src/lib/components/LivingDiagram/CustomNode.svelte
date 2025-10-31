<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';

	export let data: {
		label: string;
		icon?: string;
		type?: 'infrastructure' | 'application' | 'internet';
	};

	function handleClick() {
		logger.debug(`✅ Node clicked: ${data.label}`);
		logger.debug('Node data:', data);
		logger.debug('---');
	}
</script>

<div
	class="custom-node"
	class:infrastructure={data.type === 'infrastructure'}
	class:application={data.type === 'application'}
	class:internet={data.type === 'internet'}
	on:click={handleClick}
	role="button"
	tabindex="0"
>
	<div class="node-icon">
		{data.icon || '📦'}
	</div>
	<div class="node-label">
		{data.label}
	</div>
</div>

<!-- Connection handles (allow edges to connect from any side) -->
<Handle type="target" position={Position.Top} />
<Handle type="source" position={Position.Top} />
<Handle type="target" position={Position.Right} />
<Handle type="source" position={Position.Right} />
<Handle type="target" position={Position.Bottom} />
<Handle type="source" position={Position.Bottom} />
<Handle type="target" position={Position.Left} />
<Handle type="source" position={Position.Left} />

<style>
	.custom-node {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 1rem;
		border-radius: 0.5rem;
		border: 2px solid #4b5563;
		background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
		cursor: pointer;
		transition: all 200ms ease;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
		min-width: 120px;
		text-align: center;
	}

	.custom-node:hover {
		border-color: #3b82f6;
		box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
		transform: translateY(-2px);
	}

	.custom-node:active {
		transform: translateY(0);
	}

	/* Type-specific styling */
	.custom-node.internet {
		background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
		border-color: #60a5fa;
	}

	.custom-node.internet:hover {
		border-color: #93c5fd;
		box-shadow: 0 0 12px rgba(147, 197, 253, 0.4);
	}

	.custom-node.infrastructure {
		background: linear-gradient(135deg, #1f3a3a 0%, #0f2626 100%);
		border-color: #10b981;
	}

	.custom-node.infrastructure:hover {
		border-color: #6ee7b7;
		box-shadow: 0 0 12px rgba(110, 231, 183, 0.4);
	}

	.custom-node.application {
		background: linear-gradient(135deg, #3a2f1f 0%, #261a0f 100%);
		border-color: #f59e0b;
	}

	.custom-node.application:hover {
		border-color: #fcd34d;
		box-shadow: 0 0 12px rgba(252, 211, 77, 0.4);
	}

	.node-icon {
		font-size: 2rem;
		line-height: 1;
	}

	.node-label {
		font-size: 0.875rem;
		font-weight: 600;
		color: #e5e7eb;
		white-space: nowrap;
	}

	/* Keyboard focus styling */
	.custom-node:focus-visible {
		outline: 2px solid #3b82f6;
		outline-offset: 2px;
	}
</style>
