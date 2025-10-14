# Sentry Error Tracking - Quick Start

## 🎯 What's Integrated

Sentry è ora attivo nel frontend di Proximity per:

✅ **Tracking automatico degli errori JavaScript**  
✅ **Monitoraggio delle performance**  
✅ **Session replay (10% sessioni normali, 100% con errori)**  
✅ **Breadcrumb navigation e user actions**

## 🚀 Quick Start

### Per Sviluppatori

**In development (localhost):**
- Sentry è **disabilitato** di default per non inquinare i dati
- Per abilitarlo temporaneamente:
  ```javascript
  localStorage.setItem('sentry_debug_enabled', 'true');
  ```

**In production:**
- Sentry è **sempre attivo**
- Gli errori vengono inviati automaticamente

### Dashboard Sentry

🔗 **URL:** https://proximity.sentry.io

**Credenziali:** Contatta l'admin per l'accesso

## 📊 Cosa Viene Tracciato

### Automaticamente
- ❌ Errori JavaScript non gestiti
- ❌ Promise rejection
- 🔄 Navigazione tra le view
- 🎯 Mounting/unmounting dei componenti
- ⚡ Performance delle transizioni

### Manualmente (usa le helper functions)

```javascript
// Cattura un errore con contesto
window.reportToSentry(error, {
    context: 'deployment',
    app_name: 'wordpress',
});

// Traccia un evento importante
window.captureAppEvent('deployment_success', {
    app_name: 'wordpress',
    duration: 120,
});

// Aggiungi breadcrumb per debugging
window.addDebugBreadcrumb('User clicked deploy', {
    app_id: 123,
});
```

## 🧪 Test di Integrazione

Apri la console del browser e prova:

```javascript
// 1. Abilita Sentry in development
localStorage.setItem('sentry_debug_enabled', 'true');

// 2. Ricarica la pagina

// 3. Genera un errore di test
throw new Error('Sentry integration test');

// 4. Verifica nella dashboard Sentry (Issues tab)
```

## 📁 File Modificati

```
backend/frontend/
├── index.html                 # ✅ Sentry SDK loader aggiunto
├── js/
│   ├── sentry-config.js      # ✅ NUOVO - Configurazione Sentry
│   └── core/
│       └── Router.js          # ✅ Integrazione errori routing
└── docs/
    └── SENTRY_INTEGRATION_GUIDE.md  # ✅ Guida completa
```

## 🔐 Privacy & Sicurezza

### Dati Mascherati Automaticamente
- ✅ Tutto il testo nelle session replay
- ✅ Tutti i media nelle replay
- ✅ Password fields
- ✅ Token JWT

### Best Practice
```javascript
// ❌ MAI inviare dati sensibili
window.reportToSentry(error, {
    password: user.password,  // NO!
    token: auth.token,        // NO!
});

// ✅ Solo metadata non sensibili
window.reportToSentry(error, {
    user_id: user.id,         // OK
    has_auth: !!auth.token,   // OK
});
```

## 📖 Documentazione Completa

Per dettagli completi su:
- Configurazione avanzata
- Integration patterns
- Best practices
- Monitoring setup

Vedi: [`docs/SENTRY_INTEGRATION_GUIDE.md`](./SENTRY_INTEGRATION_GUIDE.md)

## 🐛 Debug

### Sentry non funziona?

1. **Verifica SDK caricato:**
   ```javascript
   console.log(typeof Sentry); // Deve essere 'object'
   ```

2. **Verifica filtri development:**
   ```javascript
   console.log(window.location.hostname);
   console.log(localStorage.getItem('sentry_debug_enabled'));
   ```

3. **Controlla console per messaggi Sentry:**
   - `✅ Sentry initialized` = OK
   - `⚠️ Sentry SDK not loaded` = SDK non caricato
   - `🔍 [Sentry Debug] Event blocked` = Filtrato in dev

## 🎓 Training

### Workshop Suggeriti

1. **Sentry Basics** (30 min)
   - Dashboard navigation
   - Issue triage
   - Alert setup

2. **Advanced Integration** (1h)
   - Custom instrumentation
   - Performance monitoring
   - Session replay analysis

3. **Production Monitoring** (1h)
   - Alert configuration
   - Error patterns
   - Performance optimization

---

**Status:** ✅ Active  
**Version:** Browser SDK 7.x  
**Last Updated:** 2025-10-14
