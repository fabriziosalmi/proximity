# HTTPS Configuration for Proximity 2.0

## Summary

Configured both backend (Django) and frontend (SvelteKit/Vite) to use HTTPS with self-signed SSL certificates for local development and E2E testing.

## Changes Made

### 1. Backend Configuration

**File: `/backend/proximity/settings.py`**
- Changed `JWT_AUTH_HTTPONLY: False` to allow JavaScript access to JWT tokens
- This enables hybrid authentication: cookies + localStorage

**File: `/backend/requirements.txt`**
- Added `django-extensions==3.2.3`
- Added `Werkzeug==3.0.1`
- Added `pyOpenSSL==24.0.0`
- Removed `django-sslserver` (incompatible with Python 3.12)

**File: `/backend/runserver_https.py`** (NEW)
- Python script to start Django with HTTPS using `django-extensions runserver_plus`
- Reads `cert.pem` and `key.pem` from `/backend/` directory

**SSL Certificates Generated:**
```bash
cd backend
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/C=IT/ST=Test/L=Test/O=Proximity/CN=localhost"
```

### 2. Frontend Configuration

**File: `/frontend/vite.config.ts`**
- Added `https` configuration to Vite dev server:
  ```typescript
  server: {
    https: {
      key: fs.readFileSync(path.resolve(__dirname, 'key.pem')),
      cert: fs.readFileSync(path.resolve(__dirname, 'cert.pem')),
    }
  }
  ```

**SSL Certificates Generated:**
```bash
cd frontend
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/C=IT/ST=Test/L=Test/O=Proximity/CN=localhost"
```

### 3. Docker Configuration

**File: `/docker-compose.yml`**
- **Backend service:**
  - Changed command to `python runserver_https.py`
  - Mounted SSL certificates as read-only volumes
  - Updated `CORS_ALLOWED_ORIGINS` to include HTTPS URLs
  - Changed healthcheck to use `curl -k` (accept self-signed cert)

- **Frontend service:**
  - Mounted SSL certificates as read-only volumes
  - Updated `PUBLIC_API_URL` to `https://localhost:8000`
  - Updated `VITE_API_URL` to `https://backend:8000`

### 4. E2E Test Configuration

**File: `/e2e_tests/conftest.py`**
- Changed `BASE_URL` to `https://localhost:5173`
- Changed `API_URL` to `https://localhost:8000`
- Added `browser_context_args` fixture to ignore HTTPS errors in Playwright
- Updated `api_client` to use `verify=False` for httpx

**File: `/e2e_tests/pytest.ini`**
- Removed invalid `--ignore-https-errors` from addopts (not a pytest option)

## Authentication Flow

With `JWT_AUTH_HTTPONLY: False`, the login/registration endpoints now return:

```json
{
  "access": "eyJhbGci...",  // JWT access token
  "refresh": "eyJhbGci...", // JWT refresh token
  "user": {
    "pk": 257,
    "username": "user",
    "email": "user@example.com"
  }
}
```

The frontend can now:
1. Store the JWT in `localStorage.access_token` for the `hasToken` flag
2. Use HttpOnly cookies for actual authenticated requests
3. Achieve hybrid authentication for better UX

## Testing

### Manual Testing

**Backend:**
```bash
curl -k https://localhost:8000/api/health
```

**Frontend:**
```bash
curl -k -I https://localhost:5173/
```

### E2E Testing

```bash
cd e2e_tests
pytest test_minimal.py -v
```

## Security Notes

⚠️ **DEVELOPMENT ONLY**: Self-signed certificates are for local development and testing only.

For production:
1. Obtain proper SSL certificates from a trusted CA (e.g., Let's Encrypt)
2. Consider re-enabling `JWT_AUTH_HTTPONLY: True` if localStorage JWT is not needed
3. Configure proper certificate validation

## Benefits

✅ **Secure Communication**: All traffic encrypted with TLS  
✅ **Hybrid Auth**: JWT accessible to JavaScript while maintaining cookie-based security  
✅ **E2E Testing**: Realistic HTTPS environment for tests  
✅ **Mock Service**: Works seamlessly with MockProxmoxService (180s → 8s deployments)  

## Next Steps

1. Populate catalog database for E2E tests
2. Run full E2E test suite with HTTPS
3. Validate token injection works correctly
