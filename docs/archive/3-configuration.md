# 3. Configuration Reference

Proximity is configured primarily through environment variables defined in the `.env` file in the project's root directory. This file provides a comprehensive reference for all available options.

## Main Application Settings

These variables control the core behavior of the Proximity backend.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | `dev-secret-key` | **Required.** A long, random string used for cryptographic signing. **Must be changed in production.** |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,backend` | A comma-separated list of hostnames the Django app can serve. |
| `DEBUG` | `True` | Django's debug mode. Should be `False` in production. |
| `USE_MOCK_PROXMOX` | `1` | If `1`, uses a mock Proxmox service for testing without a real Proxmox host. Set to `0` for live environments. |
| `TESTING_MODE` | `False` | Set to `True` when running automated tests. |

## Proxmox Connection

Credentials for connecting to your Proxmox VE host.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PROXMOX_HOST` | `192.168.100.102` | The IP address or hostname of your Proxmox server. |
| `PROXMOX_PORT` | `8006` | The port for the Proxmox API. |
| `PROXMOX_USER` | `root@pam` | The user for Proxmox API authentication (e.g., `root@pam`). |
| `PROXMOX_PASSWORD` | `invaders` | The password for the Proxmox user. |
| `PROXMOX_VERIFY_SSL` | `False` | Whether to verify the SSL certificate of the Proxmox host. Set to `True` in production if you have a valid certificate. |

## Database & Cache

Configuration for the PostgreSQL database and Redis cache.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://...` | The full connection URL for the PostgreSQL database. |
| `REDIS_URL` | `redis://redis:6379/0` | The connection URL for the Redis server. |

## Celery (Asynchronous Tasks)

Configuration for the Celery worker and beat services.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | URL for the message broker (Redis). |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | URL for storing task results (Redis). |

## Frontend Settings

These variables are used by the SvelteKit frontend service.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PUBLIC_API_URL` | `https://localhost:8000` | The public-facing URL of the backend API that the browser will connect to. |
| `VITE_API_URL` | `https://backend:8000` | The internal URL of the backend API for server-to-server communication within the Docker network. |

## Sentry (Error Monitoring)

Optional configuration for integrating with Sentry for error and performance monitoring.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `SENTRY_DSN` | `(empty)` | Your Sentry DSN. If empty, Sentry is disabled. |
| `SENTRY_ENVIRONMENT` | `development` | The application environment (e.g., `development`, `production`). |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | The percentage of transactions to sample for performance monitoring (0.0 to 1.0). |
| `SENTRY_PROFILES_SAMPLE_RATE` | `0.05` | The percentage of transactions to profile (0.0 to 1.0). |
| `SENTRY_RELEASE` | `proximity@2.0.0` | The current release version of the application. |
| `SENTRY_DEBUG` | `True` | Enable Sentry's debug mode for verbose logging. |

## CORS (Cross-Origin Resource Sharing)

Controls which frontend origins are allowed to make requests to the backend API.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,...` | A comma-separated list of allowed origins. |

## LXC Container Defaults

These settings control the default passwords and resources for newly created LXC containers.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LXC_ROOT_PASSWORD` | `invaders` | The default root password for new LXC containers. |
| `LXC_PASSWORD_RANDOM` | `false` | If `true`, generates a unique, secure random password for each new container, ignoring `LXC_ROOT_PASSWORD`. **Recommended for production.** |
| `LXC_PASSWORD_LENGTH` | `16` | The length of the password to generate if `LXC_PASSWORD_RANDOM` is true. |

## Next Steps

*   **[Architecture Deep-Dive &rarr;](4-architecture.md)**
