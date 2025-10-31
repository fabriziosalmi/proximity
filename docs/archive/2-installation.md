# 2. Installation Guide

This guide provides comprehensive instructions for installing and configuring Proximity.

## Prerequisites

Before you begin, ensure you have the following:

*   **Hardware:**
    *   A server running Proxmox VE (v7.0 or higher).
    *   Minimum 2 CPU cores and 4 GB RAM.
    *   Recommended 4+ CPU cores and 8+ GB RAM.
*   **Software:**
    *   `git` installed on your local machine.
    *   `Docker` and `docker-compose` installed on your local machine or a machine that will run Proximity.
*   **Network:**
    *   Your Proxmox host must be accessible over the network.

## Quick Start with Docker Compose

This is the recommended method for getting Proximity up and running quickly.

### Step 1: Clone the Repository

Clone the Proximity repository to your local machine:

```bash
git clone https://github.com/your-username/proximity.git
cd proximity
```

### Step 2: Configure Your Environment

Proximity is configured using a `.env` file. A sample file is provided to get you started.

1.  **Copy the example file:**
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file:**
    Open the `.env` file in your favorite text editor (`nano .env`, `vim .env`, etc.) and update the following required variables:

    ```dotenv
    # ==> Proxmox Host Connection
    PROXMOX_HOST=192.168.1.100       # IP address of your Proxmox host
    PROXMOX_USER=root@pam            # Proxmox user (e.g., root@pam)
    PROXMOX_PASSWORD=your-proxmox-password # Your Proxmox user's password

    # ==> Application Security
    # Generate a new, strong secret key. You can use: openssl rand -hex 32
    SECRET_KEY=your-super-secret-and-long-random-string
    ```

    For a full list of configuration options, see the [Configuration Guide](3-configuration.md).

### Step 3: Launch the Application Stack

With your configuration in place, start all the Proximity services using Docker Compose:

```bash
docker-compose up -d --build
```

This command will build the container images and start the following services in the background (`-d`):

*   `db`: PostgreSQL database
*   `redis`: Redis for caching and task queuing
*   `backend`: The Django API server (accessible on port 8000)
*   `celery_worker`: For handling asynchronous tasks
*   `celery_beat`: For scheduled tasks
*   `frontend`: The SvelteKit web interface (accessible on port 5173)

### Step 4: Initialize the Database

After the containers have started, you need to prepare the database and create an administrator account.

1.  **Run database migrations:**
    ```bash
    docker-compose exec backend python manage.py migrate
    ```

2.  **Create a superuser:**
    ```bash
    docker-compose exec backend python manage.py createsuperuser
    ```
    You will be prompted to enter a username, email, and password for your admin account.

### Step 5: Access Proximity

Congratulations! Proximity is now running. Because the services use self-signed SSL certificates for local development, you will need to use `https` and may need to accept a browser security warning.

*   **Frontend:** [https://localhost:5173](https://localhost:5173)
*   **Backend API Docs:** [https://localhost:8000/api/docs](https://localhost:8000/api/docs)
*   **Django Admin:** [https://localhost:8000/admin](https://localhost:8000/admin)

Log in with the superuser credentials you created in the previous step.

## Production Deployment

For production environments, it is recommended to run the backend as a `systemd` service for better reliability and process management. The frontend should be built into static assets and served by a dedicated web server like Nginx or Caddy.

*(A detailed guide for production deployment will be provided in a future update. For now, the Docker Compose setup is suitable for most single-server use cases.)*

## Troubleshooting

*   **`docker-compose up` fails:**
    *   Ensure Docker and Docker Compose are correctly installed and the Docker daemon is running.
    *   Check for port conflicts on your machine (e.g., if you already have services on ports 8000, 5173, 5432, or 6379).

*   **Backend container won't start:**
    *   Check the logs: `docker-compose logs backend`.
    *   Verify your `.env` file has the correct `PROXMOX_HOST` and credentials.
    *   Ensure the `db` and `redis` containers are healthy: `docker-compose ps`.

*   **Cannot access the frontend at `https://localhost:5173`:**
    *   Check the logs: `docker-compose logs frontend`.
    *   Ensure you are using `https://`.
    *   Try clearing your browser cache.

## Next Steps

*   **[Configuration Guide &rarr;](3-configuration.md)**
