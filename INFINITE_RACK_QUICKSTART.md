# Infinite Rack PoC - Quick Start Guide

## Access the Demo

The Infinite Rack PoC is currently running on the development server:

```
http://localhost:5174/infinite-rack
```

## What You'll See

1. **3D Canvas**: A dark 3D viewport showing 20 colored cube units stacked vertically
2. **Scrollbar**: A native browser scrollbar on the right side
3. **Debug Info**: Real-time camera position and scroll progress (top-right corner)
4. **Color-Coded Units**: Blue, Green, Yellow, Red, Purple (cycling pattern)

## How to Interact

### Primary Interaction: Scroll Control
```
1. Move your mouse over the viewport
2. Scroll up/down using:
   - Mouse wheel
   - Trackpad scroll
   - Scrollbar drag
3. Watch the camera smoothly move through the rack
4. Observe the 3D perspective changing in real-time
```

### Visual Feedback
- **Camera Y value**: Shows current vertical position in 3D space
- **Scroll Progress**: Percentage (0-100%) indicating position in scroll range
- **Unit Highlighting**: Each cube is individually colored for easy identification

## Key Features

✅ **Smooth Animation**: 300ms easing between camera positions
✅ **Real-time Rendering**: 60 FPS (target)
✅ **Native Scrollbar**: Uses browser's built-in scrollbar
✅ **Dark Theme**: Slate-950 background with proper lighting
✅ **Debug Overlay**: Live telemetry for development

## Component Architecture

```
InfiniteRack.svelte
├── Canvas (Three.js Scene)
│   ├── PerspectiveCamera (Scroll-controlled)
│   ├── AmbientLight (Base illumination)
│   ├── DirectionalLight x2 (Main and secondary)
│   └── Mesh x40 (20 units × 2 layers each)
│       ├── Main unit cube (1.5 × 1 × 0.3)
│       └── Glow layer (emissive effect)
├── Scroll Container
│   └── Scrollable area (4000px height)
└── Debug Overlay (fixed position)
```

## Performance Tips

### For Optimal Experience
- Use a modern browser (Chrome 90+, Firefox 88+, Safari 14+)
- Ensure hardware acceleration is enabled
- Close other CPU-intensive applications
- Use Chrome DevTools Performance tab to monitor frame rate

### Monitoring Performance
```
1. Open Chrome DevTools (F12)
2. Go to Performance tab
3. Record while scrolling
4. Look for frame time < 16.6ms (60 FPS target)
```

## Customization Options

### To Change Number of Units
Edit `src/lib/components/dashboard/InfiniteRack.svelte`:
```typescript
const mockApps = Array.from({ length: 20 }, (_, i) => ({  // Change 20 to desired count
  id: i,
  name: `App ${i + 1}`,
  status: i % 2 === 0 ? 'running' : 'idle'
}));
```

### To Adjust Camera Sensitivity
Edit the scroll mapping in `handleScroll()`:
```typescript
const minCameraY = -15;  // Lower = more range
const maxCameraY = 5;    // Higher = more range
```

### To Change Color Palette
Edit `getUnitColor()` function:
```typescript
const colors = [0x3b82f6, 0x10b981, 0xf59e0b, 0xef4444, 0x8b5cf6];
// Replace with your desired hex color values
```

### To Adjust Lighting
Edit light properties in Canvas:
```svelte
<AmbientLight intensity={0.6} />  {/* Change intensity 0-1 */}
<DirectionalLight position={[10, 15, 10]} intensity={0.8} />
```

## Troubleshooting

### Issue: Black Screen
- **Solution**: Wait 2-3 seconds for WebGL initialization
- **Alternative**: Refresh the page (Cmd+R / Ctrl+R)
- **Check**: Browser console for WebGL errors

### Issue: No Scrollbar Visible
- **Solution**: Ensure window height is set to 100vh
- **Check**: Browser zoom level (Ctrl+0 to reset)
- **Try**: Scrolling anyway (scrollbar might be hidden but functional)

### Issue: Laggy Scrolling
- **Solution**: Close other browser tabs
- **Check**: GPU acceleration in browser settings
- **Try**: Using Chrome instead of Safari (better WebGL performance)

### Issue: Units Not Rendering
- **Solution**: Clear browser cache (Ctrl+Shift+Delete)
- **Check**: Ensure Three.js and svelte-cubed are installed
- **Run**: `npm install three @types/three svelte-cubed`

## Development Workflow

### Watch Mode
```bash
npm run dev
# Changes auto-reload at http://localhost:5174/infinite-rack
```

### Type Checking
```bash
npm run check
# Validates TypeScript without building
```

### Production Build
```bash
npm run build
# Creates optimized build in `build/` directory
```

## Testing Checklist

Before considering the PoC complete, verify:

- [ ] Scrollbar appears on the right side
- [ ] Scrolling moves the camera up/down smoothly
- [ ] All 20 units are visible
- [ ] Colors cycle through 5 different shades
- [ ] Debug info updates while scrolling
- [ ] No console errors (F12 → Console)
- [ ] Frame rate stays consistent while scrolling
- [ ] Camera smooth easing (not jerky)

## Next Phase Integration

To integrate into the main dashboard:

```svelte
<!-- In /src/routes/+page.svelte -->
<script>
  import InfiniteRack from '$lib/components/dashboard/InfiniteRack.svelte';
</script>

<!-- Replace or supplement current app list -->
<InfiniteRack />
```

## Resources

- **Three.js Docs**: https://threejs.org/docs
- **Svelte Cubed**: https://github.com/Rich-Harris/svelte-cubed
- **SvelteKit**: https://kit.svelte.dev/

## Support

For issues or questions:
1. Check browser console (F12) for errors
2. Review component source: `src/lib/components/dashboard/InfiniteRack.svelte`
3. Check route definition: `src/routes/infinite-rack/+page.svelte`

---

**Status**: ✅ Ready for testing and feedback
**Version**: 1.0.0-poc
**Date**: October 21, 2024
