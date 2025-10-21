<!-- The Living Diagram PoC - Interactive Infrastructure Schematic -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { SvelteFlow, Controls, Background, MiniMap } from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';
	import { pageTitleStore } from '$lib/stores/pageTitle';
	import CustomNode from '$lib/components/LivingDiagram/CustomNode.svelte';

	// Type definitions
	interface Node {
		id: string;
		position: { x: number; y: number };
		data: {
			label: string;
			icon: string;
			type: 'internet' | 'infrastructure' | 'application';
		};
	}

	interface Edge {
		id: string;
		source: string;
		target: string;
		animated?: boolean;
	}

	// Set page title
	onMount(() => {
		pageTitleStore.setTitle('Living Diagram PoC');
	});

	// Define the diagram: 4 nodes (Internet, Proxmox Host, 2 Apps) with connections
	const nodes: Node[] = [
		{
			id: 'internet',
			position: { x: 250, y: 0 },
			data: {
				label: 'Internet',
				icon: '☁️',
				type: 'internet'
			}
		},
		{
			id: 'proxmox-opti2',
			position: { x: 200, y: 150 },
			data: {
				label: 'Proxmox Host\n(opti2)',
				icon: '🖥️',
				type: 'infrastructure'
			}
		},
		{
			id: 'app-adminer-clone',
			position: { x: 50, y: 320 },
			data: {
				label: 'adminer-clone',
				icon: '📋',
				type: 'application'
			}
		},
		{
			id: 'app-adminer-source',
			position: { x: 350, y: 320 },
			data: {
				label: 'adminer-source',
				icon: '📋',
				type: 'application'
			}
		}
	];

	// Define connections between nodes
	const edges: Edge[] = [
		{
			id: 'internet-to-proxmox',
			source: 'internet',
			target: 'proxmox-opti2',
			animated: true
		},
		{
			id: 'proxmox-to-adminer-clone',
			source: 'proxmox-opti2',
			target: 'app-adminer-clone'
		},
		{
			id: 'proxmox-to-adminer-source',
			source: 'proxmox-opti2',
			target: 'app-adminer-source'
		}
	];

	let nodeTypes = {
		default: CustomNode
	};

	// Log initialization
	onMount(() => {
		console.log('🎯 Living Diagram PoC initialized');
		console.log('📊 Diagram contains:', nodes.length, 'nodes and', edges.length, 'connections');
		console.log('Click on nodes to test interactivity');
	});
</script>

<svelte:head>
	<title>Living Diagram PoC - Proximity</title>
</svelte:head>

<div class="diagram-container">
	<!-- SvelteFlow Diagram -->
	<SvelteFlow {nodes} {edges} {nodeTypes} fitView>
		<!-- Background grid -->
		<Background color="#1f2937" gap={16} />

		<!-- Control buttons (zoom, fit view, etc.) -->
		<Controls />

		<!-- Minimap for navigation -->
		<MiniMap pannable zoomable />
	</SvelteFlow>

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
				<li>🖱️ Middle-click + drag to pan</li>
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
	.diagram-container {
		position: relative;
		width: 100%;
		height: 100vh;
		background: linear-gradient(135deg, #0f172a 0%, #1a1f35 100%);
		overflow: hidden;
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
