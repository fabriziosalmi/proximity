# 5. Usage Guide

This guide covers the main features of the Proximity interface, from deploying your first application to managing your infrastructure.

## The Interface

Proximity's interface is designed to feel like a physical data center rack, organized into several key views accessible from the main navigation:

*   **Dashboard:** The main landing page.
*   **My Apps:** Manage all your deployed applications.
*   **Catalog:** Browse and deploy new applications from the App Store.
*   **Health:** Monitor your Proxmox infrastructure.
*   **Settings:** Configure Proximity.

## Deploying an Application

Deploying a new application is a simple, three-step process.

1.  **Navigate to the Catalog:**
    Click on the **Catalog** icon in the main navigation to browse the list of available applications.

2.  **Choose an App and Configure:**
    Find the application you want to deploy and click its card. A deployment modal will appear where you can:
    *   Confirm or change the **Hostname**.
    *   Select the target **Proxmox Node**.
    *   Adjust resource allocations like **Memory**, **CPU Cores**, and **Disk Size**.
    *   Set any application-specific **Environment Variables**.

3.  **Deploy and Monitor:**
    Click the **"Deploy Application"** button. A progress modal will show you the real-time status of the deployment, from creating the container to starting the application services. Once complete, your new application will appear in the **My Apps** view.

## Managing Applications ("My Apps")

The **My Apps** view is where you will manage the lifecycle of your applications. Each application is represented by a `RackCard` that provides at-a-glance information and a full suite of management actions.

### The "Living" App Card

Each card displays:

*   **Status:** A color-coded indicator shows if the app is `running`, `stopped`, or in a transitional state.
*   **Access URL:** A direct link to open the application in a new tab.
*   **Live Metrics:** Real-time CPU, Memory, and Disk usage, updated automatically.
*   **Action Bar:** A set of quick actions to manage the application.

### Key Actions

*   **Start / Stop:** Power the container on or off.
*   **Restart:** Gracefully restart the application's services within the container.
*   **Open Console:** Access a full, web-based terminal for the container for debugging or manual operations.
*   **View Logs:** See the real-time logs from the application's services.
*   **Manage Backups:** Create new backups or restore from existing ones.
*   **Clone (PRO Mode):** Create an identical copy of the application, including its data.
*   **Delete:** Permanently destroy the application and its container.

## Adopting Existing Containers

If you have existing LXC containers on your Proxmox host, you can bring them under Proximity's management using the **Adoption Wizard**.

1.  **Navigate to the Adoption Wizard:**
    From the **My Apps** view, click the "Adopt Existing Container" button.

2.  **Step 1: Discovery:**
    Proximity will scan your Proxmox host(s) and display a list of all unmanaged containers. Select the ones you wish to adopt.

3.  **Step 2: Configuration:**
    For each selected container, match it to an application from the **Catalog**. Proximity's **Smart Port Guessing** will attempt to automatically detect the correct application type and internal port based on the container's name (e.g., a container named `nginx-proxy` will be correctly guessed as an `nginx` app on port `80`). You can confirm or override these settings.

4.  **Step 3: Confirmation:**
    Review your selections and confirm the adoption. The containers will now appear in your **My Apps** list, ready to be managed by Proximity.

**Important:** When you "delete" an adopted container from Proximity, it is only **un-managed**. The container itself is **not** destroyed on the Proxmox host, ensuring the safety of your existing infrastructure.

## Next Steps

*   **[Development Guide &rarr;](6-development.md)**
