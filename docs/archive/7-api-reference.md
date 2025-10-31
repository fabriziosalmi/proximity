# 7. API Reference

Proximity exposes a RESTful API for managing all aspects of the platform. The backend is built with Django and [Django Ninja](https://django-ninja.rest-framework.com/), which provides automatic OpenAPI documentation.

## Interactive API Documentation

For a complete and interactive list of all available endpoints, you can access the automatically generated Swagger UI or ReDoc interfaces:

*   **Swagger UI:** [https://localhost:8000/api/docs](https://localhost:8000/api/docs)
*   **ReDoc:** [https://localhost:8000/api/redoc](https://localhost:8000/api/redoc)

## Authentication

Authentication is handled via JSON Web Tokens (JWT). To access protected endpoints, you must first authenticate and then include the received access token in the `Authorization` header of your requests.

**Header Format:** `Authorization: Bearer <your_access_token>`

### Key Auth Endpoints

*   `POST /api/auth/register`: Create a new user account.
*   `POST /api/auth/login`: Authenticate and receive a JWT access token.
*   `GET /api/auth/me`: Get information about the currently authenticated user.

## Core Endpoints

This is a summary of the most important resource endpoints.

### Applications

*   `GET /api/apps`: List all deployed applications.
*   `POST /api/apps`: Deploy a new application from the catalog.
*   `GET /api/apps/{app_id}`: Get detailed information about a specific application.
*   `DELETE /api/apps/{app_id}`: Delete an application.
*   `GET /api/apps/{app_id}/status`: Get the current status of an application. This is the unified endpoint for checking deployment progress or the running/stopped state.
*   `POST /api/apps/{app_id}/action`: Perform an action on an application (e.g., `start`, `stop`, `restart`).

### Catalog

*   `GET /api/catalog`: Get the list of all available applications in the App Store.

### Container Adoption

*   `GET /api/apps/discover`: Discover all unmanaged LXC containers on the Proxmox host(s).
*   `POST /api/apps/adopt`: Adopt an existing, unmanaged container and bring it under Proximity's management.

### Backups

Backup endpoints are nested under their parent application.

*   `GET /api/apps/{app_id}/backups`: List all backups for a specific application.
*   `POST /api/apps/{app_id}/backups`: Create a new backup for an application.
*   `POST /api/apps/{app_id}/backups/{backup_id}/restore`: Restore an application from a specific backup.
*   `DELETE /api/apps/{app_id}/backups/{backup_id}`: Delete a specific backup.

### System & Health

*   `GET /api/health`: A simple health check endpoint.
*   `GET /api/system/info`: Get system-wide information.
*   `GET /api/system/nodes`: Get information about the connected Proxmox nodes.

## Unified Status Endpoint

The `GET /api/apps/{app_id}/status` endpoint intelligently provides different levels of detail based on the application's state:

*   **For stable apps (`running` or `stopped`):** It returns a simple status response.
*   **For transient apps (`deploying`, `cloning`, etc.):** It returns a rich status response including the current progress percentage and step description.

This allows the frontend to use a single endpoint for all status polling.
