# 🔔 Toast Notification System

## Overview
Sistema di notifiche toast professionale implementato per Proximity, fornendo feedback utente non intrusivo per tutte le operazioni asincrone.

---

## ✨ Features

### 1. **4 Tipi di Notifiche**
- **Success** (verde): Operazioni completate con successo
- **Error** (rosso): Errori e fallimenti (no auto-dismiss)
- **Warning** (arancione): Avvisi importanti
- **Info** (cyan): Informazioni generali

### 2. **Design Professionale**
- Glassmorphism con backdrop blur
- Animazioni smooth (slide-in/slide-out)
- Progress bar per auto-dismiss
- Icone Lucide dinamiche
- Responsive mobile/desktop
- Posizione: top-right (desktop), top-center (mobile)

### 3. **Audio Integration**
- Integrato con SoundService
- Suoni diversi per ogni tipo di notifica
- Success → `success` sound
- Error → `error` sound
- Warning/Info → `notification` sound

### 4. **Auto-Dismiss Configurabile**
- Success: 5 secondi (default)
- Error: NO auto-dismiss (richiede chiusura manuale)
- Warning: 7 secondi
- Info: 5 secondi
- Durata personalizzabile per chiamata

---

## 📦 Implementazione

### Files Modificati/Creati

#### **index.html**
```html
<!-- Toast Container -->
<div id="toast-container" class="toast-container"></div>

<!-- Toast Notifications Script -->
<script src="/js/notifications-global.js?v=20251010-01"></script>
```

#### **styles.css** (righe 6274-6551)
- `.toast-container`: Fixed position container
- `.toast`: Base toast styling
- `.toast-success`, `.toast-error`, `.toast-warning`, `.toast-info`: Type-specific styles
- `.toast-progress`: Progress bar animation
- Responsive breakpoints per mobile

#### **js/notifications-global.js** (NEW)
Implementazione globale non-module per compatibilità con app.js

#### **js/utils/notifications.js** (UPDATED)
Versione ES6 module per uso futuro con import/export

#### **app.js**
Rimossa vecchia implementazione `showNotification()`, ora usa versione globale

---

## 🚀 Usage API

### Global Functions

```javascript
// Basic notification
showNotification(message, type, duration, title)

// Helper shortcuts
showSuccess(message, duration = 5000)
showError(message, duration = 0)  // No auto-dismiss!
showWarning(message, duration = 7000)
showInfo(message, duration = 5000)

// Clear all toasts
clearAllToasts()
```

### Examples

```javascript
// Success message (auto-dismiss in 5s)
showSuccess('Application deployed successfully!');

// Error (requires manual close)
showError('Failed to connect to Proxmox server');

// Warning with custom duration (10s)
showWarning('Low disk space on node', 10000);

// Info with custom title
showNotification('Server restart scheduled', 'info', 5000, 'Maintenance');

// Custom duration (3 seconds)
showSuccess('Settings saved', 3000);
```

---

## 🎨 Design Specs

### Colors
- **Success**: `#10b981` (green)
- **Error**: `#ef4444` (red)
- **Warning**: `#f59e0b` (amber)
- **Info**: `#06b6d4` (cyan)

### Typography
- **Title**: Inter 600, 0.9375rem
- **Message**: Inter 400, 0.875rem

### Spacing
- **Container**: `top: 80px, right: 1.5rem`
- **Gap**: `0.75rem` between toasts
- **Padding**: `1rem 1.25rem`

### Animations
- **Entry**: `toastSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)`
- **Exit**: `toastSlideOut 0.2s cubic-bezier(0.5, 0, 1, 1)`
- **Progress**: `toastProgress Xms linear` (X = duration)

### Icons (Lucide)
- Success: `check-circle`
- Error: `alert-circle`
- Warning: `alert-triangle`
- Info: `info`

---

## 📱 Responsive Behavior

### Desktop (>768px)
- Position: Fixed top-right
- Max-width: 420px
- Animation: Slide from right

### Mobile (≤768px)
- Position: Fixed top-center (full width with margins)
- Animation: Slide from top
- Touch-optimized close button

---

## 🔧 Technical Details

### Z-Index Hierarchy
```
toast-container: 9999 (top of everything)
modal: 1000-2000
top-nav: 100
```

### Container Behavior
- `pointer-events: none` on container (click-through)
- `pointer-events: all` on individual toasts (clickable)

### DOM Structure
```html
<div class="toast toast-{type}">
    <div class="toast-icon">
        <i data-lucide="{icon}"></i>
    </div>
    <div class="toast-content">
        <div class="toast-title">{Title}</div>
        <div class="toast-message">{Message}</div>
    </div>
    <button class="toast-close">×</button>
    <div class="toast-progress"></div> <!-- if duration > 0 -->
</div>
```

### Event Listeners
- Close button: Click → removeToast()
- Auto-dismiss: setTimeout() → removeToast()
- Exit animation: 200ms delay before DOM removal

---

## ✅ Integration Checklist

- [x] HTML container aggiunto
- [x] CSS completo con animazioni
- [x] JavaScript service creato (global + module)
- [x] Script caricato in index.html
- [x] Vecchia implementazione rimossa da app.js
- [x] Audio integration funzionante
- [x] Responsive design implementato
- [x] Progress bar animation
- [x] Lucide icons integration
- [x] Error notifications no auto-dismiss
- [x] Manual close button
- [x] Multiple toasts stacking

---

## 🎯 Current Usage in App

Il sistema è già integrato in **68 punti** dell'applicazione:

### Deploy Operations
- `deployApp()`: Success/Error notifications
- Deployment progress modal con feedback

### App Management
- Start/Stop/Restart actions
- Delete confirmations
- Backup/Restore operations

### Settings
- Form validations
- Connection tests
- Save confirmations

### Auth
- Login/Logout feedback
- Registration errors

### System
- Network appliance operations
- Infrastructure status updates

---

## 🔄 Migration Notes

### Old Implementation → New
```javascript
// OLD (removed from app.js)
function showNotification(message, type) {
    // Basic emoji icons
    // Fixed 5s auto-dismiss
    // No progress bar
    // No sound integration parameter
}

// NEW (global)
function showNotification(message, type, duration, title) {
    // Lucide icons
    // Configurable duration
    // Progress bar animation
    // Integrated with SoundService
    // Custom title support
    // Better error handling
}
```

### Breaking Changes
**None** - API è backward compatible. Le chiamate esistenti `showNotification(msg, type)` continuano a funzionare.

---

## 📊 Benefits

### User Experience
✅ Feedback immediato e visibile
✅ Non intrusivo (no blocco interazione)
✅ Audio feedback opzionale
✅ Chiusura manuale per errori critici

### Developer Experience
✅ API semplice e consistente
✅ Helper functions per quick usage
✅ Type safety con JSDoc
✅ Logging automatico in console

### Performance
✅ Gestione DOM ottimizzata
✅ Animazioni CSS hardware-accelerated
✅ No memory leaks (proper cleanup)
✅ Lazy icon initialization

---

## 🚧 Future Enhancements (Backlog v1.1)

- [ ] Toast stacking limit (max 5 visible)
- [ ] Queuing system per troppi toast simultanei
- [ ] Action buttons in toast (Undo, Retry, etc.)
- [ ] Rich content support (HTML formatting)
- [ ] Position configuration (top-left, bottom-right, etc.)
- [ ] Custom animation types
- [ ] Toast grouping per categoria
- [ ] Persistence across page reload (sessionStorage)

---

**Version**: 1.0.0
**Date**: 2025-10-10
**Cache Versions**:
- CSS: v20251010-76
- notifications-global.js: v20251010-01
- app.js: v20251010-76
