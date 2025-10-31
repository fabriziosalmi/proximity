# Sentry Quick Start - Proximity 2.0

## 🚀 Quick Setup (Development)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Add your Sentry DSN (optional for dev)
# SENTRY_DSN=https://your-dsn@sentry.io/project
# Or use the default test DSN already configured

# 3. Start the application
docker-compose up --build

# 4. Test backend Sentry
curl http://localhost:8000/api/core/sentry-debug/

# 5. Test frontend Sentry
# Visit http://localhost:5173 and click "🐛 Test Sentry" button
```

## 🔍 Verify Integration

**✅ Backend working if you see:**
```bash
🔴 [Sentry Server] Error captured (not sent in dev): ZeroDivisionError
```

**✅ Frontend working if you see:**
```bash
🔴 [Sentry Client] Error captured (not sent in dev): Error: Sentry test error
```

## 🎛️ Control Sentry Behavior

**Send events in development mode:**
```bash
# Backend
SENTRY_DEBUG=True

# Frontend
VITE_SENTRY_DEBUG=true
```

**Adjust sampling rate (0.0 to 1.0):**
```bash
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
```

## 📍 Key Endpoints

- **Backend Debug:** `http://localhost:8000/api/core/sentry-debug/`
- **Frontend Test:** Home page → "🐛 Test Sentry" button
- **Sentry Dashboard:** https://sentry.io/organizations/fabriziosalmi/projects/proximity/

## 🆘 Troubleshooting

**Errors not appearing in Sentry?**
1. Check DSN is set correctly
2. Verify `SENTRY_DEBUG=True` for dev mode
3. Check Sentry dashboard project settings
4. Look for console logs showing captures

**Want to disable Sentry completely?**
```bash
# Just remove or comment out SENTRY_DSN
# SENTRY_DSN=
```

## 📚 Full Documentation

See `docs/SENTRY_INTEGRATION_GUIDE.md` for complete details.
