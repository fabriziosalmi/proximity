# 🚀 Frontend Quick Start Guide

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

## Setup (First Time)

```bash
# Navigate to frontend directory
cd /Users/fab/GitHub/proximity/proximity2/frontend

# Install dependencies
npm install

# Create environment file
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Development Workflow

### Running the Dev Server

```bash
npm run dev
```

Access the application:
- **Home**: http://localhost:5173/
- **App Store**: http://localhost:5173/store
- **My Apps**: http://localhost:5173/apps

### Building for Production

```bash
npm run build
npm run preview  # Preview the production build
```

## Testing the Implementation

### Manual Test Flow

1. **App Store Test**
   ```
   → Open http://localhost:5173/store
   → Verify catalog loads
   → Test search functionality
   → Test category filtering
   → Click "Deploy" on an app
   → Fill in deployment form
   → Submit deployment
   → Verify navigation to My Apps
   → Check toast notification appears
   ```

2. **My Apps Test**
   ```
   → Open http://localhost:5173/apps
   → Verify apps list loads
   → Check status dashboard shows correct counts
   → Wait 5 seconds and verify auto-refresh
   → Click "Start" on a stopped app
   → Click "Stop" on a running app
   → Click "Restart" on a running app
   → Click "Delete" on an app (confirm dialog should appear)
   → Verify action buttons disable during operation
   → Check toast notifications for each action
   ```

## Common Issues & Solutions

### Issue: API calls fail with CORS error

**Solution**: Ensure backend allows CORS from `http://localhost:5173`

In Django settings.py:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
```

### Issue: Icons don't show

**Solution**: Install lucide-svelte if missing
```bash
npm install lucide-svelte
```

### Issue: Tailwind classes don't work

**Solution**: Verify tailwind.config.js includes all source files
```javascript
content: ['./src/**/*.{html,js,svelte,ts}']
```

### Issue: Store not updating

**Solution**: Check if polling is started on page mount
```typescript
onMount(() => myAppsStore.startPolling(5000));
```

## Project Structure Quick Reference

```
src/
├── lib/
│   ├── api.ts                    # API client
│   ├── components/               # Reusable components
│   │   ├── RackCard.svelte       # App card component
│   │   ├── CategoryFilter.svelte # Category filter
│   │   ├── DeploymentModal.svelte# Deployment dialog
│   │   └── ToastContainer.svelte # Notifications
│   └── stores/                   # State management
│       ├── apps.ts               # Deployed apps store
│       └── toast.ts              # Toast notifications
└── routes/
    ├── store/+page.svelte        # App Store view
    └── apps/+page.svelte         # My Apps view
```

## Useful Commands

```bash
# Development
npm run dev                # Start dev server
npm run check              # Type check
npm run lint               # Lint code

# Building
npm run build              # Production build
npm run preview            # Preview build

# Formatting
npm run format             # Format code with prettier
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
# Backend API URL
VITE_API_URL=http://localhost:8000

# Optional: Enable debug mode
VITE_DEBUG=true
```

## API Integration

The frontend expects these endpoints to be available:

### ✅ Already Implemented in Backend
- `GET /api/catalog/` - List catalog apps
- `GET /api/catalog/categories` - List categories
- `GET /api/catalog/search?q=query` - Search catalog
- `POST /api/catalog/reload` - Reload catalog

### ⏳ TODO in Backend
- `GET /api/apps/` - List deployed apps
- `POST /api/apps/` - Deploy new app
- `POST /api/apps/{id}/action` - App actions (start/stop/restart/delete)
- `GET /api/apps/{id}/logs` - Get deployment logs
- `GET /api/proxmox/hosts` - List Proxmox hosts
- `POST /api/proxmox/hosts/{id}/sync-nodes` - Sync nodes

## Example API Responses

### GET /api/catalog/
```json
[
  {
    "id": "adminer",
    "name": "Adminer",
    "description": "Database management tool",
    "category": "database",
    "icon": "https://...",
    "tags": ["database", "mysql", "postgresql"]
  }
]
```

### GET /api/apps/
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "catalog_app_id": "adminer",
    "name": "Adminer",
    "hostname": "my-adminer",
    "status": "running",
    "host_id": 1,
    "node_name": "pve",
    "vmid": 101,
    "created_at": "2025-10-18T10:00:00Z",
    "updated_at": "2025-10-18T10:05:00Z"
  }
]
```

## Theming

To create a custom theme, override CSS variables in `app.css`:

```css
/* Example: Dark Purple Theme */
[data-theme="purple"] {
  --card-bg-color: #2d1b4e;
  --card-border-color: rgba(139, 92, 246, 0.3);
  --card-title-color: #c4b5fd;
  --card-text-color: #a78bfa;
  --glow-color: rgba(139, 92, 246, 0.4);
}
```

Then apply the theme:
```html
<div data-theme="purple">
  <!-- Your content -->
</div>
```

## Component Usage Examples

### Using RackCard

```svelte
<script>
  import RackCard from '$lib/components/RackCard.svelte';

  const app = {
    id: 'adminer',
    name: 'Adminer',
    description: 'Database tool',
    category: 'database'
  };
</script>

<RackCard {app} variant="catalog">
  <div slot="actions">
    <button>Deploy</button>
  </div>
</RackCard>
```

### Using Stores

```svelte
<script>
  import { myAppsStore } from '$lib/stores/apps';
  import { toasts } from '$lib/stores/toast';

  // Start polling
  onMount(() => myAppsStore.startPolling(5000));

  // Stop polling
  onDestroy(() => myAppsStore.stopPolling());

  // Show toast
  toasts.success('App started!');
</script>

{#each $myAppsStore.apps as app}
  <p>{app.name}: {app.status}</p>
{/each}
```

## Debugging Tips

### Enable console logging

In `src/lib/api.ts`, add logging:
```typescript
async function request(endpoint, options) {
  console.log('API Request:', endpoint, options);
  const response = await fetch(...);
  console.log('API Response:', response);
  return response;
}
```

### Check store state

In any component:
```svelte
<script>
  import { myAppsStore } from '$lib/stores/apps';

  $: console.log('Store state:', $myAppsStore);
</script>
```

### Monitor polling

```svelte
<script>
  import { myAppsStore } from '$lib/stores/apps';

  myAppsStore.subscribe(state => {
    console.log('Store updated:', state.lastUpdated);
  });
</script>
```

## Performance Tips

1. **Optimize polling interval**: Adjust from 5s to longer if needed
   ```typescript
   myAppsStore.startPolling(10000); // 10 seconds
   ```

2. **Disable polling when page hidden**: Add visibility detection
   ```typescript
   document.addEventListener('visibilitychange', () => {
     if (document.hidden) {
       myAppsStore.stopPolling();
     } else {
       myAppsStore.startPolling(5000);
     }
   });
   ```

3. **Use derived stores**: For computed values
   ```typescript
   const runningApps = derived(myAppsStore, $store =>
     $store.apps.filter(app => app.status === 'running')
   );
   ```

## Accessibility Checklist

- [x] All buttons have aria-labels
- [x] Modal has aria-modal and role="dialog"
- [x] Focus management in modal
- [x] Keyboard navigation support
- [x] Color contrast meets WCAG AA
- [x] Loading states announced to screen readers

## Browser Support

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Getting Help

1. Check `FRONTEND_IMPLEMENTATION.md` for detailed docs
2. Check `FILE_STRUCTURE.md` for project organization
3. Look at component source code for inline documentation
4. Check browser console for errors
5. Verify backend API is running and accessible

## Next Steps After Setup

1. ✅ Install dependencies
2. ✅ Configure environment
3. ✅ Start dev server
4. ⏳ Implement backend app management endpoints
5. ⏳ Test integration
6. ⏳ Deploy to production

---

**Last Updated**: October 18, 2025
**Status**: Ready for integration testing
**Support**: Check documentation or component source code

Happy coding! 🚀
