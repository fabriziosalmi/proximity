# EmptyRackCard Component - Documentation

## 🎯 Purpose

Reusable bare metal rack card component for displaying empty states across the application.

## 📦 Component Location

`/frontend/src/lib/components/EmptyRackCard.svelte`

## 🔧 Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | string | `'NO ITEMS'` | Main label text displayed in the rack |
| `buttonText` | string | `'ADD ITEM'` | Text for the action button |
| `buttonHref` | string | `'/'` | URL the button links to |
| `icon` | Component | `Server` | Lucide icon component to display |

## 💡 Usage Examples

### Apps Page (No Apps)
```svelte
<EmptyRackCard
  label="NO APPS INSTALLED"
  buttonText="INSTALL APP"
  buttonHref="/store"
  icon={Server}
/>
```

### Hosts Page (No Proxmox Hosts)
```svelte
<EmptyRackCard
  label="NO PROXMOX HOSTS"
  buttonText="ADD HOST"
  buttonHref="/settings"
  icon={HardDrive}
/>
```

### Custom Usage
```svelte
<EmptyRackCard
  label="NO DATA FOUND"
  buttonText="REFRESH"
  buttonHref="/refresh"
  icon={RotateCw}
/>
```

## 🎨 Visual Features

- **Mounting Ears**: Left and right rack ears with realistic screws
- **Bare Metal Design**: Dark metallic gradient background
- **Grid Pattern**: Subtle background grid for industrial feel
- **Industrial Label**: Monospace font with embossed effect
- **Animated Button**:
  - Cyan glow on hover
  - Light sweep animation on hover
  - Press-down effect on click
  - Smooth transitions

## 📐 Dimensions

- **Height**: 200px minimum
- **Width**: 100% of container
- **Mounting Ears**: 2.5rem width each
- **Screws**: 0.875rem diameter

## 🎬 Animations

1. **Hover Sweep**: Light sweeps from left to right on button hover
2. **Glow Effect**: Cyan shadow appears on button hover
3. **Button Lift**: Button translates up 1px on hover
4. **Press Down**: Button returns to normal position on click

## 🔄 Integration Status

### ✅ Implemented
- `/apps` page - Shows when no apps are deployed

### 🔜 To Implement
- `/hosts` page - Shows when no Proxmox hosts configured
- Other empty states as needed

## 🚀 SSR Safe

This component is fully SSR-compatible and doesn't use any client-side only APIs.

## 📝 Notes

- Maintains visual consistency with `RackCard` component
- Same screw and mounting ear design as app racks
- Fully responsive (future: add mobile optimizations if needed)
- Accessible with proper semantic HTML structure

---

**Created**: 2025-10-21
**Last Updated**: 2025-10-21
