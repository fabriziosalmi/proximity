# Proximity Usage Guide

Complete guide to using every feature of Proximity, from browsing the App Store to managing deployed applications.

---

## Table of Contents

- [Interface Overview](#interface-overview)
- [Dashboard](#dashboard)
- [App Store (Catalog)](#app-store-catalog)
- [My Apps](#my-apps)
- [Health & Infrastructure](#health--infrastructure)
- [Settings](#settings)
- [User Account](#user-account)

---

## Interface Overview

Proximity's interface is organized into **five main sections**, accessible via the left sidebar:

| Icon | Section | Purpose |
|------|---------|---------|
| 📊 | **Dashboard** | Overview and quick actions |
| 📦 | **My Apps** | Manage deployed applications |
| 🚀 | **Catalog** | Browse and deploy new apps |
| 🏥 | **Health** | Infrastructure monitoring |
| ⚙️ | **Settings** | System configuration |

### Navigation

- **Click** any sidebar icon to switch views
- Current section is **highlighted** in blue
- **Notifications** appear in top-right corner
- **User menu** in top-right for account and logout

---

## Dashboard

The landing page with hero section and quick actions.

### What You'll See

- **Hero Section**: Welcome message and Proximity overview
- **Quick Action Buttons**:
  - **My Applications** → Jump to My Apps view
  - **Deploy New App** → Jump to Catalog view
- **App Card Preview**: Example of what deployed apps look like

### Purpose

The Dashboard provides a **clean introduction** to Proximity. It's intentionally simple—real application management happens in the **My Apps** and **Catalog** sections.

---

## App Store (Catalog)

Browse available applications and deploy them with one click.

### Features

#### 1. **Search & Filter**

- **Search Bar**: Filter apps by name or description
- **Category Filter**: Filter by category (All, Web, Database, Development, etc.)
- **Real-Time Filtering**: Results update as you type

#### 2. **App Cards**

Each catalog card shows:

- **Icon**: Visual identifier
- **Name**: Application name
- **Description**: What the app does
- **Version**: Current version in catalog
- **Category**: App category tag
- **Requirements**: Minimum resources (CPU, RAM)

#### 3. **Deploy Workflow**

**Step 1: Click "Deploy"**

Click the **Deploy** button on any app card.

**Step 2: Configure Deployment**

A modal appears with:

- **Hostname**: Unique identifier (auto-generated, editable)
  - Format: `app-name-xyz123`
  - Used for container naming
  - Must be unique across all apps

- **Target Node**: Proxmox node selection
  - Auto-selected based on available resources
  - Can manually choose if you have multiple nodes

- **Resources** (Optional):
  - **Memory**: RAM allocation (default: 2048 MB)
  - **CPU Cores**: Number of cores (default: 2)
  - **Disk Size**: Storage allocation (default: 8 GB)

- **Environment Variables** (App-Specific):
  - Some apps require configuration (e.g., admin password)
  - Default values provided where possible
  - Hover over field labels for help text

**Step 3: Start Deployment**

Click **"Deploy Application"** to begin.

**Step 4: Watch Progress**

A **progress modal** shows deployment in real-time:

```
✓ Creating LXC container
✓ Starting container
✓ Installing Docker
✓ Deploying application
✓ Configuring networking
✓ Application deployed successfully!
```

Each step updates with:
- ✓ Success (green)
- ⏳ In progress (blue)
- ✗ Error (red)

**Deployment typically takes 60-90 seconds.**

**Step 5: Access Your App**

Once complete:
- App appears in **My Apps**
- Click **"Open App"** or **"Go to My Apps"** from modal

---

## My Apps

The heart of Proximity—manage all your deployed applications.

### App Cards ("Living Cards")

Each app is represented by a **rich, interactive card** showing:

#### Header Section

- **App Icon**: Large visual identifier with gradient
- **App Name**: Display name
- **Quick Actions Bar**: 12 action buttons (explained below)

#### Connection Info

- **Status Indicator**: 🟢 Running / 🔴 Stopped / 🟡 Deploying
- **Access URL**: Click to open app in new tab
- **Node**: Which Proxmox node hosts the container
- **Container ID**: LXC ID (e.g., `100`)
- **Deployed**: Creation timestamp

#### Resource Metrics (Live)

Real-time monitoring updated every 10 seconds:

- **CPU Usage**: Percentage and usage bar (0-100%)
- **RAM Usage**: Used / Total (e.g., `512 MB / 2048 MB`) with bar

#### Footer

- **Actions**: Full menu of management options

### Quick Actions

The **12-button action bar** provides instant access to common operations:

| Icon | Action | Description | Mode |
|------|--------|-------------|------|
| ⏸️ / ▶️ | **Start/Stop** | Toggle container on/off | Both |
| 🔗 | **Open in New Tab** | Open app URL in browser | Both |
| 📄 | **View Logs** | Show Docker Compose logs | Both |
| 💻 | **Open Console** | Web-based terminal access | Both |
| 💾 | **Manage Backups** | Create/restore/delete backups | Both |
| ⬆️ | **Update App** | Check for and apply updates | Both |
| 📦 | **View Volumes** | List Docker volumes | Both |
| 📊 | **Monitoring** | Detailed resource metrics | Both |
| 🔄 | **Restart** | Restart Docker Compose stack | Both |
| 📋 | **Clone** | Duplicate running app | PRO Only |
| ⚙️ | **Edit Resources** | Adjust CPU/RAM/disk | PRO Only |
| 🗑️ | **Delete** | Remove app and container | Both |

### Detailed Actions

#### 1. **Start / Stop**

**Purpose**: Control container power state

**Usage:**
1. Click pause icon (⏸️) to **Stop**
2. Click play icon (▶️) to **Start**
3. Status indicator updates in real-time

**Notes:**
- Stopping gracefully shuts down Docker containers
- Starting boots the LXC and restarts Docker Compose

#### 2. **Open in New Tab**

**Purpose**: Access your app in a new browser window

**Usage:**
1. Click external link icon (🔗)
2. App opens in new tab at its access URL

**Notes:**
- URL format: `http://<node-ip>:<public-port>`
- Port is automatically allocated during deployment

#### 3. **View Logs**

**Purpose**: View Docker Compose application logs

**Usage:**
1. Click logs icon (📄)
2. Modal opens with scrollable log view
3. Logs auto-refresh (can toggle)
4. Use filters to show/hide log levels

**Useful For:**
- Debugging app issues
- Checking startup messages
- Monitoring runtime behavior

#### 4. **Open Console**

**Purpose**: Full terminal access to container

**Usage:**
1. Click terminal icon (💻)
2. Web-based terminal opens in modal
3. Type commands as you would in SSH
4. Full root access to container

**Common Commands:**
- `docker ps` - List running containers
- `docker-compose logs` - View logs
- `docker-compose restart` - Restart services
- `htop` - View resource usage
- `df -h` - Check disk space

**Security**: Console sessions are sandboxed and logged.

#### 5. **Manage Backups**

**Purpose**: Create, restore, and manage backups

**Usage:**

**Create Backup:**
1. Click backup icon (💾)
2. Modal shows existing backups
3. Click **"Create Backup"**
4. Choose:
   - **Storage**: Proxmox storage backend
   - **Compression**: zstd (fast) / gzip (compatible) / none
   - **Mode**: snapshot (fast) / stop (safer)
5. Watch progress
6. Backup appears in list

**Restore Backup:**
1. Open Backup Manager
2. Find backup in list
3. Click **"Restore"** button
4. Confirm action
5. Container is restored to backup state

**Delete Backup:**
1. Open Backup Manager
2. Click **"Delete"** on unwanted backup
3. Confirm removal

**Notes:**
- Backups are stored in Proxmox vzdump format
- Can be managed from Proxmox UI as well
- AUTO mode creates daily backups automatically at 2:00 AM

#### 6. **Update Application**

**Purpose**: Update app to latest version

**Usage:**
1. Click update icon (⬆️)
2. Proximity checks for updates
3. If available, shows version comparison
4. Click **"Update Now"**
5. Backup is automatically created first
6. Docker images are pulled
7. Containers are recreated with new version
8. Old version can be restored from backup if needed

**Notes:**
- AUTO mode checks for updates weekly
- PRO mode requires manual initiation
- Updates are non-destructive (data preserved)

#### 7. **View Volumes**

**Purpose**: List and manage Docker volumes

**Usage:**
1. Click volumes icon (📦)
2. Modal shows all volumes for app
3. See volume names, mount points, and sizes

**Useful For:**
- Understanding data persistence
- Troubleshooting storage issues
- Planning backups

#### 8. **Monitoring**

**Purpose**: Detailed resource metrics and graphs

**Usage:**
1. Click activity icon (📊)
2. Modal shows detailed statistics:
   - **CPU**: Real-time percentage and history
   - **Memory**: RAM usage breakdown
   - **Disk**: I/O operations
   - **Network**: Bytes in/out
   - **Uptime**: How long container has been running

**Auto-Refresh**: Updates every 5 seconds

#### 9. **Restart**

**Purpose**: Restart Docker Compose stack

**Usage:**
1. Click restart icon (🔄)
2. Confirm action
3. Proximity runs `docker-compose restart`
4. All containers restart in place

**Notes:**
- Faster than Stop → Start
- Preserves container state
- Use when app is unresponsive

#### 10. **Clone** (PRO Mode Only)

**Purpose**: Duplicate a running application

**Usage:**
1. Click clone icon (📋)
2. Modal appears with configuration:
   - **New Hostname**: Auto-generated, editable
   - **Target Node**: Can deploy to different node
   - **Copy Data**: Option to include volumes (slower)
3. Click **"Clone Application"**
4. Progress shows cloning steps
5. New app appears in My Apps with suffix (e.g., `app-clone-1`)

**Use Cases:**
- Create staging environment
- Duplicate production setup
- Test configuration changes

#### 11. **Edit Resources** (PRO Mode Only)

**Purpose**: Adjust CPU, RAM, and disk on-the-fly

**Usage:**
1. Click sliders icon (⚙️)
2. Modal shows current allocations
3. Adjust sliders:
   - **Memory**: 512 MB - 16 GB
   - **CPU Cores**: 1 - 16
   - **Disk Size**: Cannot be reduced (can only grow)
4. Click **"Apply Changes"**
5. Container is updated (requires restart)

**Notes:**
- Disk changes require filesystem resize
- Memory/CPU changes take effect on next start
- Proxmox node must have resources available

#### 12. **Delete**

**Purpose**: Permanently remove app and container

**Usage:**
1. Click delete icon (🗑️) (red button)
2. Modal asks for confirmation
3. Type app name to confirm
4. Click **"Delete Application"**
5. Progress shows cleanup:
   - Stopping containers
   - Removing volumes (optional)
   - Deleting LXC container
   - Releasing ports
   - Removing proxy config

**Warning**: This action is **permanent**. Create a backup first if you want to preserve the app.

---

## Health & Infrastructure

Monitor your Proxmox infrastructure and network appliance.

### Sections

#### 1. **Proxmox Nodes**

Shows all nodes in your cluster:

- **Node Name**: Hostname
- **Status**: Online / Offline
- **CPU**: Usage percentage
- **Memory**: Used / Total
- **Uptime**: Days since last reboot
- **Version**: Proxmox VE version
- **Containers**: Number of LXC containers on node

**Actions:**
- Click node card for detailed view
- See which apps are deployed on each node

#### 2. **Network Appliance** (If configured)

Shows status of Platinum Edition network appliance:

- **Status**: Running / Stopped
- **WAN IP**: Management network IP
- **LAN IP**: App network gateway (10.20.0.1)
- **Services**:
  - DHCP Server status
  - DNS Server status
  - Caddy Proxy status
  - NAT/Routing status

**Actions:**
- Restart Appliance
- View Logs
- Test NAT Configuration

#### 3. **System Statistics**

Global metrics across all infrastructure:

- **Total Apps**: Deployed applications
- **Running Apps**: Currently active
- **Total Containers**: All LXC containers
- **Resource Usage**: Aggregate CPU/RAM across cluster

---

## Settings

Configure Proximity behavior and manage system settings.

### Settings Sections

#### 1. **Proxmox Connection**

Manage connection to your Proxmox cluster.

**Fields:**
- **Host**: Proxmox IP or hostname
- **Port**: API port (default: 8006)
- **Username**: Proxmox user (format: `user@realm`)
- **Password**: User password (stored encrypted)
- **Verify SSL**: Enable for production with valid certs

**Actions:**
- **Test Connection**: Verify settings before saving
- **Save**: Apply changes
- **Logs**: View connection logs

#### 2. **Network Configuration**

Choose network architecture mode.

**Options:**
- **Simple Mode** (Default): vmbr0 + DHCP
- **Advanced Mode**: Network Appliance with NAT

**Simple Mode Settings:**
- Bridge: `vmbr0`
- IP Assignment: DHCP
- Port Ranges: Configurable

**Advanced Mode Settings:**
- LAN Subnet: `10.20.0.0/24`
- Gateway: `10.20.0.1`
- DHCP Range: `10.20.0.100-250`
- DNS Domain: `.prox.local`

#### 3. **Default Resources**

Set default allocations for new deployments.

**Fields:**
- **Memory**: Default RAM (MB)
- **CPU Cores**: Default CPU count
- **Disk Size**: Default storage (GB)
- **Storage Backend**: Proxmox storage (e.g., `local-lvm`)

**Notes:**
- Users can override during deployment
- Affects catalog app defaults

#### 4. **Proximity Mode**

Choose operating mode: AUTO or PRO.

**AUTO Mode** (Recommended for most users):
- ✅ Daily automated backups (2:00 AM)
- ✅ Weekly update checks (Sunday 3:00 AM)
- ✅ Automatic cleanup of stale resources
- ✅ Simplified interface

**PRO Mode** (For power users):
- ✅ Manual backup control
- ✅ App cloning capability
- ✅ Live resource editing
- ✅ Advanced configuration access
- ✅ Full feature set

**Switch**: Toggle between modes anytime—takes effect immediately.

#### 5. **Backup Schedule** (AUTO Mode Only)

Configure automated backup behavior.

**Settings:**
- **Enable Backups**: Toggle automation
- **Backup Time**: When to run (default: 2:00 AM)
- **Retention**: How many backups to keep
- **Storage**: Where to store backups
- **Compression**: zstd / gzip / none

#### 6. **Update Schedule** (AUTO Mode Only)

Configure automated update checks.

**Settings:**
- **Enable Update Checks**: Toggle automation
- **Check Day**: Day of week (default: Sunday)
- **Check Time**: When to check (default: 3:00 AM)
- **Auto-Update**: Automatically apply updates (use with caution)

#### 7. **Security**

Manage authentication and access control.

**Options:**
- **Change Password**: Update your password
- **Session Timeout**: Auto-logout after inactivity
- **API Keys**: Generate tokens for automation (future feature)
- **Audit Log**: View all administrative actions

#### 8. **Advanced**

Low-level system configuration.

**Options:**
- **Debug Mode**: Enable verbose logging
- **Sentry**: Error reporting configuration
- **Cleanup Interval**: How often to clean stale records
- **Database**: Backup and restore settings database

---

## User Account

Manage your Proximity user account.

### User Menu (Top-Right)

Click your username to reveal:

**Options:**
- **Profile**: View account details
- **Change Password**: Update password
- **Logout**: End session

### Profile

View your account information:

- **Username**: Your login name
- **Email**: Account email
- **Role**: Admin / User
- **Created**: Account creation date
- **Last Login**: Last successful login timestamp

### Change Password

Update your password:

1. **Current Password**: Verify identity
2. **New Password**: Choose new password (min 8 characters)
3. **Confirm Password**: Verify new password
4. Click **"Update Password"**

**Security Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one number
- At least one special character

### Logout

End your Proximity session:

1. Click **"Logout"** in user menu
2. Confirm action
3. Return to login screen
4. JWT token is invalidated

---

## Tips & Best Practices

### 🎯 **Deployment**

- **Start Small**: Deploy simple apps (nginx, hello-world) first to test your setup
- **Resource Planning**: Leave some resources free on Proxmox for system operations
- **Naming Convention**: Use descriptive hostnames (e.g., `prod-wordpress`, `dev-nextcloud`)

### 💾 **Backups**

- **Before Updates**: Always backup before applying updates
- **Regular Schedule**: Use AUTO mode for worry-free daily backups
- **Test Restores**: Periodically restore a backup to verify it works

### 🔒 **Security**

- **Change Defaults**: Update default container root passwords
- **Least Privilege**: Don't run all apps as root inside containers
- **Network Isolation**: Use Advanced Mode if running untrusted applications
- **Keep Updated**: Apply Proxmox and app updates regularly

### 📊 **Monitoring**

- **Watch Metrics**: CPU/RAM spikes may indicate issues
- **Check Logs**: Review app logs when troubleshooting
- **Disk Space**: Monitor storage usage to prevent full disks

### 🛠️ **Troubleshooting**

- **Console First**: Use integrated console to investigate issues
- **Restart Often**: Many issues resolve with a simple restart
- **Backup Before Changes**: Create backup before making major config changes
- **Community Help**: Check GitHub Discussions for similar issues

---

## Next Steps

✅ **You're now a Proximity power user!**

Continue learning:
- **[Architecture Guide](4_ARCHITECTURE.md)** - Understand how Proximity works internally
- **[Development Guide](5_DEVELOPMENT.md)** - Contribute features or fixes

---

<div align="center">

[← Back: Deployment](2_DEPLOYMENT.md) • [Next: Architecture →](4_ARCHITECTURE.md)

</div>
