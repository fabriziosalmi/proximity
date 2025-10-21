<!-- The Living Diagram PoC - Interactive Infrastructure Schematic (Simplified Version) -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { pageTitleStore } from '$lib/stores/pageTitle';

	// Set page title
	onMount(() => {
		pageTitleStore.setTitle('Living Diagram PoC');
	});

	// Define nodes for the diagram
	interface DiagramNode {
		id: string;
		x: number;
		y: number;
		label: string;
		icon: string;
		type: 'internet' | 'infrastructure' | 'application';
	}

	interface DiagramEdge {
		from: string;
		to: string;
	}

	let nodes: DiagramNode[] = [
		{
			id: 'internet',
			x: 50,
			y: 10,
			label: 'Internet',
			icon: '☁️',
			type: 'internet'
		},
		{
			id: 'proxmox-opti2',
			x: 50,
			y: 35,
			label: 'Proxmox Host (opti2)',
			icon: '🖥️',
			type: 'infrastructure'
		},
		{
			id: 'app-adminer-clone',
			x: 25,
			y: 70,
			label: 'adminer-clone',
			icon: '📋',
			type: 'application'
		},
		{
			id: 'app-adminer-source',
			x: 75,
			y: 70,
			label: 'adminer-source',
			icon: '📋',
			type: 'application'
		}
	];

	let edges: DiagramEdge[] = [
		{ from: 'internet', to: 'proxmox-opti2' },
		{ from: 'proxmox-opti2', to: 'app-adminer-clone' },
		{ from: 'proxmox-opti2', to: 'app-adminer-source' }
	];

	let selectedNode: string | null = null;
	let isDragging = false;
	let dragNodeId: string | null = null;
	let dragOffsetX = 0;
	let dragOffsetY = 0;

	// Log initialization
	onMount(() => {
		console.log('🎯 Living Diagram PoC initialized (Simplified SVG version)');
		console.log('📊 Diagram contains:', nodes.length, 'nodes and', edges.length, 'connections');
		console.log('Click and drag nodes to reposition them');
	});

	// Handle node click
	function handleNodeClick(nodeId: string) {
		selectedNode = nodeId;
		const node = nodes.find(n => n.id === nodeId);
		if (node) {
			console.log(`✅ Node clicked: ${node.label}`);
			console.log('Node data:', node);
			console.log('---');
		}
	}

	// Drag handlers
	function handleMouseDown(event: MouseEvent, nodeId: string) {
		const node = nodes.find(n => n.id === nodeId);
		if (!node) return;

		isDragging = true;
		dragNodeId = nodeId;
		
		const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
		dragOffsetX = event.clientX - rect.left - rect.width / 2;
		dragOffsetY = event.clientY - rect.top - rect.height / 2;
	}

	function handleMouseMove(event: MouseEvent) {
		if (!isDragging || !dragNodeId) return;

		const container = document.querySelector('.svg-container') as HTMLElement;
		if (!container) return;

		const rect = container.getBoundingClientRect();
		const x = ((event.clientX - rect.left - dragOffsetX) / rect.width) * 100;
		const y = ((event.clientY - rect.top - dragOffsetY) / rect.height) * 100;

		nodes = nodes.map(n => 
			n.id === dragNodeId 
				? { ...n, x: Math.max(0, Math.min(100, x)), y: Math.max(0, Math.min(100, y)) }
				: n
		);
	}

	function handleMouseUp() {
		isDragging = false;
		dragNodeId = null;
	}

	// Get node position
	function getNode(id: string) {
		return nodes.find(n => n.id === id);
	}
</script>

<svelte:head>
	<title>Living Diagram PoC - Proximity</title>
</svelte:head>

<svelte:window on:mousemove={handleMouseMove} on:mouseup={handleMouseUp} />

<div class="diagram-container">
	<!-- SVG Diagram -->
	<div class="svg-container">
		<svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
			<!-- Draw edges first (behind nodes) -->
			{#each edges as edge}
				{@const fromNode = getNode(edge.from)}
				{@const toNode = getNode(edge.to)}
				{#if fromNode && toNode}
					<line
						x1={fromNode.x}
						y1={fromNode.y}
						x2={toNode.x}
						y2={toNode.y}
						class="edge"
					/>
				{/if}
			{/each}
		</svg>

		<!-- Nodes overlay (HTML for better styling) -->
		{#each nodes as node (node.id)}
			<div
				class="diagram-node"
				class:internet={node.type === 'internet'}
				class:infrastructure={node.type === 'infrastructure'}
				class:application={node.type === 'application'}
				class:selected={selectedNode === node.id}
				class:dragging={isDragging && dragNodeId === node.id}
				style="left: {node.x}%; top: {node.y}%;"
				on:click={() => handleNodeClick(node.id)}
				on:mousedown={(e) => handleMouseDown(e, node.id)}
				role="button"
				tabindex="0"
			>
				<div class="node-icon">{node.icon}</div>
				<div class="node-label">{node.label}</div>
			</div>
		{/each}
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

	.svg-container {
		position: relative;
		width: 100%;
		height: 100%;
	}

	svg {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		z-index: 1;
	}

	.edge {
		stroke: #4b5563;
		stroke-width: 0.5;
		fill: none;
		pointer-events: none;
	}

	.diagram-node {
		position: absolute;
		transform: translate(-50%, -50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 1rem;
		border-radius: 0.5rem;
		border: 2px solid #4b5563;
		background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
		cursor: move;
		transition: all 200ms ease;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
		min-width: 120px;
		text-align: center;
		user-select: none;
		z-index: 10;
	}

	.diagram-node.dragging {
		cursor: grabbing;
		box-shadow: 0 8px 16px rgba(0, 0, 0, 0.5);
		transform: translate(-50%, -50%) scale(1.05);
	}

	.diagram-node.selected {
		border-width: 3px;
		box-shadow: 0 0 20px rgba(59, 130, 246, 0.6);
	}

	.diagram-node:hover {
		border-color: #3b82f6;
		box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
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
