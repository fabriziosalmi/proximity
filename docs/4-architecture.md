# 4. Architecture

Proximity is a containerized, multi-service application orchestrated by Docker Compose. It follows a modern, decoupled architecture with a distinct backend, frontend, and asynchronous task processing system.

## Technology Stack

*   **Backend:** Django + Django Ninja (for a robust, type-safe API)
*   **Frontend:** SvelteKit + Tailwind CSS (for a reactive, beautifully styled UI)
*   **Database:** PostgreSQL (for reliable, relational data persistence)
*   **Async Tasks:** Celery + Redis (for offloading all long-running operations)
*   **Orchestration:** Docker Compose

## System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Browser (Client)                      │
│                SvelteKit + Tailwind CSS                 │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS/JSON (Port 5173)
┌────────────────────┴────────────────────────────────────┐
│                Proximity Services (Docker)               │
│                                                         │
│ ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐  │
│ │ Frontend  │  │  Backend  │  │  Celery   │  │  Redis  │  │
│ │ (Svelte)  │  │ (Django)  │  │ (Worker)  │  │ (Cache) │  │
│ └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └────┬────┘  │
│       │              │              │             │       │
│       └──────────────┼──────────────┼─────────────┘       │
│                      │              │                     │
│                      │ API (HTTPS)  │ Celery Tasks        │
│                      ▼              ▼                     │
│               ┌───────────┐  ┌───────────┐                │
│               │ Proxmox VE│  │ PostgreSQL│                │
│               │  (Host)   │  │  (DB)     │                │
│               └───────────┘  └───────────┘                │
└─────────────────────────────────────────────────────────┘
```

## Service Breakdown

The `docker-compose.yml` file defines the following core services:

*   **`db` (PostgreSQL):** The primary database for storing all application state, including users, applications, and settings.
*   **`redis` (Redis):** Acts as the message broker for Celery and can be used for caching.
*   **`backend` (Django):** The main API server. It handles all business logic, communicates with the Proxmox host, and serves the API that the frontend consumes.
*   **`celery_worker` (Celery):** Executes long-running, asynchronous tasks such as deploying applications, creating backups, or cloning containers. This ensures the API remains responsive.
*   **`celery_beat` (Celery):** A scheduler for periodic tasks, such as the `ReconciliationService` which ensures the database state is consistent with the Proxmox host.
*   **`frontend` (SvelteKit):** The web server that serves the SvelteKit user interface to the client.

## Backend Architecture

The Django backend follows a clean, service-oriented design.

*   **Modular `apps` Structure:** The project is divided into self-contained Django apps for each domain (e.g., `applications`, `proxmox`, `core`).
*   **Service Layer Pattern:** Business logic is encapsulated in `services.py` files, keeping API views (`api.py`) thin and focused on request/response handling.
*   **Asynchronous by Default:** All interactions with Proxmox (deploying, cloning, etc.) are executed as non-blocking Celery tasks. The API immediately returns a `202 Accepted` response, and the frontend polls for status updates.
*   **Self-Healing Services:**
    *   `ReconciliationService` (via Celery Beat): Periodically compares the database state with the reality on the Proxmox host and cleans up any orphaned records.
    *   `StuckTaskJanitor` (via Celery Beat): Marks applications that are stuck in a transitional state (e.g., "deploying") for too long as `error`.

## Frontend Architecture

The SvelteKit frontend is designed to be a highly reactive and immersive "Command Deck."

*   **Component-Driven:** The UI is built from a library of reusable Svelte components (e.g., `RackCard`, `StatBlock`, `OperationalRack`).
*   **Centralized State Management:** Svelte Stores are used as the single source of truth for UI state, particularly for authentication (`auth.ts`) and the list of applications (`apps.ts`).
*   **Optimistic Updates & Polling:** The UI provides immediate feedback for user actions and then uses intelligent polling to synchronize with the backend's asynchronous tasks.
*   **Auth-Aware Stores:** Data stores that require authentication are designed to wait for the `authStore` to be initialized before making API calls, preventing race conditions.

## Next Steps

*   **[Usage Guide &rarr;](5-usage-guide.md)**
