# Proximity: Your Personal Cloud's Command Deck

<p align="center">
  <img src="https://raw.githubusercontent.com/your-username/proximity/main/docs/assets/proximity-banner.png" alt="Proximity Banner" width="800"/>
</p>

<p align="center">
  <strong>Proximity is an open-source, immersive management layer for personal cloud infrastructure, starting with Proxmox VE.</strong>
  <br />
  It transforms server management from a chore into a delightful, "gamified" experience.
</p>

<p align="center">
  <a href="https://github.com/your-username/proximity/blob/main/LICENSE"><img src="https://img.shields.io/github/license/your-username/proximity" alt="License"></a>
  <a href="https://github.com/your-username/proximity/releases"><img src="https://img.shields.io/github/v/release/your-username/proximity" alt="Release"></a>
  <a href="https://github.com/your-username/proximity/actions"><img src="https://img.shields.io/github/actions/workflow/status/your-username/proximity/ci.yml?branch=main" alt="CI Status"></a>
</p>

---

## ✨ Key Features

*   **"Casa Digitale" (Digital Homestead):** An immersive, skeuomorphic "Command Deck" UI. We are building a virtual data center, not a web form.
*   **"Divertimento" (Fun):** A "gamified" UX with tactile interactions, animations, and audio feedback.
*   **"Tranquillità by Default" (Peace of Mind):** Self-healing backend, zero-downtime operations, and safety-first design.
*   **One-Click App Deployment:** Deploy from a curated catalog of applications in seconds.
*   **Container Adoption:** Discover and manage existing LXC containers on your Proxmox host.
*   **Real-time Monitoring:** Live metrics for CPU, RAM, and disk usage integrated directly into the UI.
*   **Automated Backups:** Configure and forget with scheduled, automatic backups.

## 🚀 Quick Start

Get Proximity up and running in under 5 minutes.

### Prerequisites

*   Docker & Docker Compose
*   Git
*   A running Proxmox VE host (v7.0+)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/proximity.git
    cd proximity
    ```

2.  **Configure your environment:**
    ```bash
    cp .env.example .env
    nano .env
    ```
    Update the `.env` file with your Proxmox host credentials and a new `SECRET_KEY`.

3.  **Launch the stack:**
    ```bash
    docker-compose up -d --build
    ```

4.  **Initialize the database:**
    ```bash
    docker-compose exec backend python manage.py migrate
    docker-compose exec backend python manage.py createsuperuser
    ```

5.  **Access Proximity:**
    *   **Frontend:** `https://localhost:5173`
    *   **Backend API:** `https://localhost:8000/api/docs`

For more detailed instructions, see the [Installation Guide](docs/2-installation.md).

## 📚 Documentation

*   [**Introduction**](docs/1-introduction.md): What is Proximity?
*   [**Installation**](docs/2-installation.md): Detailed setup instructions.
*   [**Configuration**](docs/3-configuration.md): Environment variable reference.
*   [**Architecture**](docs/4-architecture.md): A look under the hood.
*   [**Usage Guide**](docs/5-usage-guide.md): How to use Proximity.
*   [**Development**](docs/6-development.md): How to contribute.
*   [**API Reference**](docs/7-api-reference.md): Guide to the backend API.

## 🤝 Contributing

Proximity is built by the community, for the community. We welcome contributions of all kinds! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.