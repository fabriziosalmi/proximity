<script lang="ts">
	import { onMount } from 'svelte';
	import { tweened } from 'svelte/motion';
	import { cubicOut } from 'svelte/easing';
	import * as THREE from 'three';
	import {
		Canvas,
		PerspectiveCamera,
		AmbientLight,
		DirectionalLight,
		Mesh
	} from 'svelte-cubed';

	// Mock data: 20 application rack units
	const mockApps = Array.from({ length: 20 }, (_, i) => ({
		id: i,
		name: `App ${i + 1}`,
		status: i % 2 === 0 ? 'running' : 'idle'
	}));

	// Pre-create geometries, materials, and background
	const boxGeometry = new THREE.BoxGeometry(1.5, 1, 0.3);
	const glowGeometry = new THREE.BoxGeometry(1, 1, 1);
	const backgroundColor = new THREE.Color(0x0f172a);

	// Scroll-controlled camera position
	let cameraY = tweened(-5, {
		duration: 300,
		easing: cubicOut
	});

	let targetCameraY = -5;
	let containerElement: HTMLDivElement;
	let canvasContainer: HTMLDivElement;

	// Handle scroll events
	function handleScroll() {
		if (!containerElement) return;

		const totalHeight = containerElement.scrollHeight;
		const visibleHeight = containerElement.clientHeight;
		const scrollableHeight = totalHeight - visibleHeight;
		const scrollPercentage = containerElement.scrollTop / scrollableHeight;

		// Map scroll percentage to camera Y position
		// The rack extends from y=0 to y=-24 (20 units * 1.2 gap + padding)
		const minCameraY = -15;
		const maxCameraY = 5;
		targetCameraY = maxCameraY + (minCameraY - maxCameraY) * scrollPercentage;

		cameraY.set(targetCameraY);
	}

	onMount(() => {
		if (containerElement) {
			containerElement.addEventListener('scroll', handleScroll);

			return () => {
				containerElement.removeEventListener('scroll', handleScroll);
			};
		}
	});

	// Color palette for rack units
	function getUnitColor(index: number): THREE.Color {
		const colors = [0x3b82f6, 0x10b981, 0xf59e0b, 0xef4444, 0x8b5cf6];
		return new THREE.Color(colors[index % colors.length]);
	}

	// Subscribe to the camera Y position for reactivity
	let currentCameraY = -5;
	cameraY.subscribe((value) => {
		currentCameraY = value;
	});
</script>

<div class="relative w-full h-full" style="height: 100vh;">
	<!-- Canvas Container with scrollbar -->
	<div
		bind:this={containerElement}
		class="w-full h-full overflow-y-scroll bg-slate-950"
		style="height: 100vh; overflow-x: hidden; position: relative;"
	>
		<!-- Canvas (sticky) -->
		<div
			bind:this={canvasContainer}
			class="sticky top-0 w-full h-screen bg-slate-950"
			style="height: 100vh; flex-shrink: 0;"
		>
			<Canvas background={backgroundColor}>
				<!-- Camera controlled by scroll -->
				<PerspectiveCamera position={[0, currentCameraY, 8]} />

				<!-- Lighting -->
				<AmbientLight intensity={0.6} />
				<DirectionalLight position={[10, 15, 10]} intensity={0.8} />
				<DirectionalLight position={[-10, -5, -10]} intensity={0.3} />

				<!-- Rack Units (Cubes) -->
				{#each mockApps as app, index (app.id)}
					{@const color = getUnitColor(index)}
					{@const material = new THREE.MeshStandardMaterial({
						color,
						metalness: 0.6,
						roughness: 0.4
					})}
					{@const glowMaterial = new THREE.MeshStandardMaterial({
						color,
						emissive: color,
						emissiveIntensity: 0.2,
						transparent: true,
						opacity: 0.1
					})}

					<!-- Main rack unit cube -->
					<Mesh
						geometry={boxGeometry}
						{material}
						position={[0, -(index * 1.2), 0]}
					/>

					<!-- Subtle glow/emissive effect layer -->
					<Mesh
						geometry={glowGeometry}
						material={glowMaterial}
						position={[0, -(index * 1.2), 0.15]}
						scale={[1.55, 1.05, 0.31]}
					/>
				{/each}
			</Canvas>
		</div>

		<!-- Scrollable content area to trigger scrollbar -->
		<div class="w-full" style="height: 4000px; pointer-events: none;">
			<!-- This div enables vertical scrolling -->
		</div>
	</div>

	<!-- Debug info overlay -->
	<div class="fixed top-4 right-4 bg-slate-900 bg-opacity-75 p-3 rounded text-xs text-slate-300 font-mono z-10">
		<div>Camera Y: {currentCameraY.toFixed(2)}</div>
		<div>Scroll Progress: {((targetCameraY + 15) / 20 * 100).toFixed(1)}%</div>
		<div class="mt-2 text-slate-400 text-xs">Scroll to control camera</div>
	</div>
</div>

<style>
	:global(canvas) {
		display: block;
		width: 100%;
		height: 100%;
	}

	/* Custom scrollbar styling */
	div ::-webkit-scrollbar {
		width: 10px;
	}

	div ::-webkit-scrollbar-track {
		background: rgba(15, 23, 42, 0.5);
	}

	div ::-webkit-scrollbar-thumb {
		background: rgba(100, 116, 139, 0.6);
		border-radius: 5px;
	}

	div ::-webkit-scrollbar-thumb:hover {
		background: rgba(100, 116, 139, 0.9);
	}
</style>
