<!-- The Living Diagram PoC - Interactive Infrastructure Schematic (Svelvet Version) -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { Svelvet, Node, Edge } from 'svelvet';
	import { pageTitleStore } from '$lib/stores/pageTitle';

	// Set page title
	onMount(() => {
		pageTitleStore.setTitle('Living Diagram PoC');
	});

	// Define nodes for the diagram
	let nodes = [
		{
			id: 'internet',
			xPos: 350,
			yPos: 50,
			label: 'Internet',
			icon: '☁️',
			type: 'internet'
		},
		{
			id: 'proxmox-opti2',
			xPos: 300,
			yPos: 200,
			label: 'Proxmox Host\n(opti2)',
			icon: '🖥️',
			type: 'infrastructure'
		},
		{
			id: 'app-adminer-clone',
			xPos: 100,
			yPos: 400,
			label: 'adminer-clone',
			icon: '📋',
			type: 'application'
		},
		{
			id: 'app-adminer-source',
			xPos: 500,
			yPos: 400,
			label: 'adminer-source',
			icon: '📋',
			type: 'application'
		}
	];

	// Define connections between nodes
	let edges = [
		{
			id: 'internet-to-proxmox',
			from: 'internet',
			to: 'proxmox-opti2'
		},
		{
			id: 'proxmox-to-adminer-clone',
			from: 'proxmox-opti2',
			to: 'app-adminer-clone'
		},
		{
			id: 'proxmox-to-adminer-source',
			from: 'proxmox-opti2',
			to: 'app-adminer-source'
		}
	];

	// Log initialization
	onMount(() => {
		console.log('🎯 Living Diagram PoC initialized');
		console.log('📊 Diagram contains:', nodes.length, 'nodes and', edges.length, 'connections');
		console.log('Click on nodes to test interactivity');
	});

	// Handle node click
	function handleNodeClick(nodeId: string) {
		const node = nodes.find(n => n.id === nodeId);
		if (node) {
			console.log(`✅ Node clicked: ${node.label}`);
			console.log('Node data:', {
				id: node.id,
				label: node.label,
				icon: node.icon,
				type: node.type
			});
			console.log('---');
		}
	}

	// Handle keyboard events for accessibility
	function handleKeydown(event: KeyboardEvent, nodeId: string) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			handleNodeClick(nodeId);
		}
	}
</script>

<svelte:head>
	<title>Living Diagram PoC - Proximity</title>
</svelte:head>

<div class="diagram-container">
	<!-- Svelvet Diagram -->
	<div class="svelvet-wrapper">
		<Svelvet bind:nodes bind:edges>
			{#each nodes as nodeData (nodeData.id)}
				<Node
					id={nodeData.id}
					xPos={nodeData.xPos}
					yPos={nodeData.yPos}
				>
					<div
						class="diagram-node"
						class:internet={nodeData.type === 'internet'}
						class:infrastructure={nodeData.type === 'infrastructure'}
						class:application={nodeData.type === 'application'}
						on:click={() => handleNodeClick(nodeData.id)}
						on:keydown={(e) => handleKeydown(e, nodeData.id)}
						role="button"
						tabindex="0"
					>
						<div class="node-icon">{nodeData.icon}</div>
						<div class="node-label">{nodeData.label}</div>
					</div>
				</Node>
			{/each}

			{#each edges as edgeData (edgeData.id)}
				<Edge id={edgeData.id} from={edgeData.from} to={edgeData.to} />
			{/each}
		</Svelvet>
	</div>

	<!-- Info Overlay -->
	<div class="info-overlay">
		<h2>The Living Diagram PoC</h2>
		<div class="info-content">
			<p><strong>🎯 Objective:</strong> Interactive infrastructure schematic</p>
			<p><strong>📊 Diagram contains:</strong></p>
			<ul>
				<li>☁️ 1 Internet node</li>
				<li>🖥️ 1 Proxmox Host (opti2)</li>
				<li>📋 2 Application nodes</li>
				<li>3 connections (edges)</li>
			</ul>
			<p><strong>🎮 Interactions:</strong></p>
			<ul>
				<li>👆 Drag nodes to reposition</li>
				<li>🔍 Scroll to zoom in/out</li>
				<li>🖱️ Hold Space + drag to pan</li>
				<li>🎯 Click nodes to log to console</li>
			</ul>
			<p style="margin-top: 1rem; font-size: 0.875rem; color: #9ca3af;">
				Open DevTools (F12) to see console logs when clicking nodes
			</p>
		</div>
	</div>

	<!-- Debug Console Output -->
	<div class="debug-overlay">
		<div class="debug-header">Console Output</div>
		<div class="debug-content">
			<p>📌 Ready - Click on any node to test</p>
			<p style="font-size: 0.75rem; color: #6b7280;">Check browser console (F12) for detailed logs</p>
		</div>
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
	}

	.diagram-container {
		position: relative;
		width: 100%;
		height: 100vh;
		background: linear-gradient(135deg, #0f172a 0%, #1a1f35 100%);
		overflow: hidden;
	}

	.svelvet-wrapper {
		width: 100%;
		height: 100%;
	}

	:global(.svelvet-container) {
		width: 100% !important;
		height: 100% !important;
		background: linear-gradient(135deg, #0f172a 0%, #1a1f35 100%) !important;
	}

	:global(.svelvet-canvas) {
		background-color: transparent !important;
	}

	:global(.svelvet-edge) {
		stroke: #4b5563;
		stroke-width: 2;
	}

	:global(.svelvet-edge.selected) {
		stroke: #3b82f6;
	}

	.diagram-node {
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
		user-select: none;
	}

	.diagram-node:hover {
		border-color: #3b82f6;
		box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
		transform: translateY(-2px);
	}

	.diagram-node:active {
		transform: translateY(0);
	}

	/* Type-specific styling */
	.diagram-node.internet {
		background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
		border-color: #60a5fa;
	}

	.diagram-node.internet:hover {
		border-color: #93c5fd;
		box-shadow: 0 0 12px rgba(147, 197, 253, 0.4);
	}

	.diagram-node.infrastructure {
		background: linear-gradient(135deg, #1f3a3a 0%, #0f2626 100%);
		border-color: #10b981;
	}

	.diagram-node.infrastructure:hover {
		border-color: #6ee7b7;
		box-shadow: 0 0 12px rgba(110, 231, 183, 0.4);
	}

	.diagram-node.application {
		background: linear-gradient(135deg, #3a2f1f 0%, #261a0f 100%);
		border-color: #f59e0b;
	}

	.diagram-node.application:hover {
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
		white-space: normal;
		line-height: 1.2;
	}

	.info-overlay {
		position: fixed;
		top: 20px;
		left: 20px;
		background: rgba(15, 23, 42, 0.95);
		border: 2px solid #4b5563;
		border-radius: 0.5rem;
		padding: 1.5rem;
		width: 320px;
		max-height: 400px;
		overflow-y: auto;
		backdrop-filter: blur(10px);
		z-index: 10;
		font-size: 0.875rem;
		color: #e5e7eb;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
	}

	.info-overlay h2 {
		margin: 0 0 1rem 0;
		font-size: 1.125rem;
		font-weight: 700;
		color: #3b82f6;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.info-content p {
		margin: 0.75rem 0;
		line-height: 1.5;
	}

	.info-content ul {
		margin: 0.75rem 0 0 0;
		padding-left: 1.25rem;
	}

	.info-content li {
		margin: 0.5rem 0;
		list-style: none;
	}

	.debug-overlay {
		position: fixed;
		bottom: 20px;
		right: 20px;
		background: rgba(15, 23, 42, 0.95);
		border: 2px solid #10b981;
		border-radius: 0.5rem;
		width: 300px;
		backdrop-filter: blur(10px);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
		z-index: 10;
		overflow: hidden;
	}

	.debug-header {
		background: linear-gradient(90deg, #10b981 0%, #059669 100%);
		color: #0f172a;
		padding: 0.75rem 1rem;
		font-weight: 700;
		font-size: 0.875rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.debug-content {
		padding: 1rem;
		font-size: 0.875rem;
		color: #d1d5db;
		font-family: 'Monaco', 'Courier New', monospace;
		max-height: 120px;
		overflow-y: auto;
	}

	.debug-content p {
		margin: 0.5rem 0;
		line-height: 1.4;
	}

	/* Scrollbar styling for overlays */
	.info-overlay::-webkit-scrollbar,
	.debug-content::-webkit-scrollbar {
		width: 6px;
	}

	.info-overlay::-webkit-scrollbar-track,
	.debug-content::-webkit-scrollbar-track {
		background: rgba(75, 85, 99, 0.2);
		border-radius: 3px;
	}

	.info-overlay::-webkit-scrollbar-thumb,
	.debug-content::-webkit-scrollbar-thumb {
		background: rgba(75, 85, 99, 0.5);
		border-radius: 3px;
	}

	.info-overlay::-webkit-scrollbar-thumb:hover,
	.debug-content::-webkit-scrollbar-thumb:hover {
		background: rgba(75, 85, 99, 0.8);
	}

	/* Responsive adjustments */
	@media (max-width: 768px) {
		.info-overlay {
			width: 280px;
			left: 10px;
			top: 10px;
			font-size: 0.8rem;
		}

		.debug-overlay {
			width: 260px;
			right: 10px;
			bottom: 10px;
			font-size: 0.8rem;
		}
	}
</style>
