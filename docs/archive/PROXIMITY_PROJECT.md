# Proximity 2.0 - Project Genesis: Scope, Architecture & Workflow

**Document Version:** 1.0
**Last Updated:** October 20, 2025
**Status:** Post-EPIC 3 ("Operazione Gioiellino"), Pre-Genesis Release

---

## 1. PROJECT SCOPE & VISION (THE "WHY")

Proximity 2.0 is an open-source, immersive management layer for personal cloud infrastructure, starting with Proxmox VE. It is engineered from the ground up to transform server management from a chore into a delightful, "gamified" experience.

### 1.1. The Four Pillars:
1.  **"Casa Digitale" (Digital Homestead):** An immersive, skeuomorphic "Command Deck" UI. We are building a virtual data center, not a web form. The "All-is-Rack" design paradigm is central.
2.  **"Divertimento" (Fun):** A "gamified" UX with tactile interactions, animations (3D flips), and audio feedback. The goal is to create an emotional connection with the product.
3.  **"Tranquillità by Default" (Peace of Mind):** Proactive system design.
    *   **Self-Healing Backend:** Automated services (`ReconciliationService`, `StuckTaskJanitor`) ensure system consistency.
    *   **Zero-Downtime Operations:** Critical actions (like `clone`) are designed to be non-disruptive.
    *   **Safety First:** Destructive actions are protected by clear confirmation modals.
4.  **"Ecosistema Aperto" (Open Ecosystem):** The architecture is designed for future extensibility through themes, widgets, and plugins contributed by the community.

---

## 2. SYSTEM ARCHITECTURE (THE "HOW")

Proximity 2.0 is a containerized, multi-service application orchestrated by Docker Compose. It follows a modern, decoupled architecture.

### 2.1. Core Technology Stack (Non-Negotiable):
*   **Backend:** Django + Django Ninja (for a robust, type-safe API)
*   **Frontend:** SvelteKit + Tailwind CSS (for a reactive, beautifully styled UI)
*   **Async Tasks:** Celery + Redis (for offloading all long-running operations)
*   **Database:** PostgreSQL (for reliable, relational data persistence)
*   **Real-time (Future):** Django Channels

### 2.2. Backend Architecture:
*   **Modular `apps` Structure:** Each domain (applications, backups, core, proxmox) is a self-contained Django app.
*   **Service Layer Pattern:** Business logic is encapsulated in `services.py` files (e.g., `AppService`, `ProxmoxService`), keeping API views thin.
*   **Asynchronous by Default:** All interactions with Proxmox (deploy, clone, stop, etc.) are executed as non-blocking Celery tasks. The API always returns `202 Accepted` immediately.
*   **Self-Healing Services:**
    *   `ReconciliationService` (Celery Beat, hourly): Compares the DB state with Proxmox reality and purges orphan records.
    *   `StuckTaskJanitor` (Celery Beat, every 6 hours): Marks applications stuck in transitional states as `error`.

### 2.3. Frontend Architecture:
*   **"Command Deck" Layout:** A unified, responsive layout (`MasterControlRack`, `OperationalRack`, `MainCanvas`) that enforces the "All-is-Rack" design language.
*   **Component-Driven:** Built with reusable Svelte components (`RackCard`, `StatBlock`, etc.).
*   **Centralized State Management:** Svelte Stores (`myAppsStore`) are the single source of truth for UI state.
*   **Optimistic Updates & Polling:** The UI provides immediate feedback and then uses intelligent polling to synchronize with the backend's asynchronous tasks.
*   **Action Dispatcher (`actions.ts`):** A centralized store for user-initiated actions, bundling API calls, toasts, and sounds for clean, DRY components.
*   **Theming Engine:** Based on CSS Custom Properties defined in `app.css`, allowing for easy "skinning".

---

## 3. WORKFLOW: "THE ARCHITECT & EXECUTOR" (THE "PROCESS")

Our collaboration is a structured dialogue between two roles: the **Comandante** (Product Architect) and the **Maestro** (AI Principal Architect).

1.  **Visione (Comandante):** Proposes a high-level goal or feature.
2.  **Strategia (Maestro & Comandante):** We discuss, challenge, and refine the goal into a strategic plan.
3.  **Specifica (Maestro):** I create a detailed, technical "Super Prompt" for the implementation.
4.  **Esecuzione (Comandante -> AI Coders):** The Comandante feeds the Super Prompt to a team of AI Coders.
5.  **Analisi (Comandante -> Maestro):** The Comandante provides the output (code, logs, reports). I analyze it critically to define the next strategic step.

---

## 4. PROJECT STATUS & PROGRESS

We have successfully completed the foundational EPICs and are in the final polishing phase.

### 4.1. Completed Milestones:
*   **EPIC 1: Architecture & Technology Stack:** Foundational setup is complete and stable.
*   **EPIC 2: Core Feature Re-implementation:** All critical functionalities from v1 are implemented and superior in v2 (Deploy, Manage, Clone, Backup, Settings). This is **100% complete and validated**.
*   **"Operazione Stabilità Totale":** A full E2E test suite (`test_full_app_lifecycle`) has been built and is **passing**, guaranteeing the stability of the core user flow.
*   **EPIC 3: "Operazione Gioiellino" (Phase 1):** The "Command Deck" UI is implemented. The application has a unique, coherent, and polished visual identity.

### 4.2. Current State:
The application is considered **"Feature-Complete" for the "Genesis Release"**. It is stable, robust, and aesthetically refined. We are in the final "pre-flight" phase before a potential v2.0.0 launch.

---

## 5. FUTURE ROADMAP (THE "WHAT'S NEXT")

This is a living list of potential future EPICs, to be prioritized.

*   **EPIC 4: The Immersive Canvas (Project Unity):**
    *   **Vision:** Replace the static Dashboard with a real-time, 3D visualization of the entire infrastructure, built with Unity or a similar 3D engine (e.g., Three.js).
    *   **Tasks:** Research integration, build 3D models for racks/servers, stream real-time data (status, metrics) to the 3D environment.

*   **EPIC 5: The Open Ecosystem:**
    *   **Vision:** Transform Proximity from a product into a platform.
    *   **Tasks:**
        *   Finalize the **Theme Switcher** UI.
        *   Build a **Widget Engine** for a customizable dashboard.
        *   Implement **Custom Catalog Repositories** (allow users to add app stores from Git).

*   **EPIC 6: The Distributed Cloud:**
    *   **Vision:** Transcend a single Proxmox installation.
    *   **Tasks:**
        *   Finalize **Multi-Host Management** UI in Settings.
        *   Implement **Live Migration** actions.
        *   Build a **Cluster Load Balancer** service.

*   **EPIC 7: The Intelligent Agent:**
    *   **Vision:** Make Proximity a proactive, conversational partner.
    *   **Tasks:**
        *   Integrate a local LLM for a natural language "Omni-Prompt".
        *   Build an AI "Model-Control-Plane" (MCP) allowing the AI to execute safe actions.
        *   Implement AI-driven proactive alerts ("Your 'plex' container is running low on disk space. Shall I expand it by 10GB?").