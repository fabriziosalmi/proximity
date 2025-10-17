/**
 * Infrastructure Diagram Component
 * 
 * Displays a visual representation of the infrastructure:
 * - Proxmox Host
 * - LXC Containers (Apps)
 * - Network connections
 * - Resource usage
 * 
 * @module components/InfrastructureDiagram
 */

export class InfrastructureDiagram {
    constructor() {
        this.containerId = 'infrastructure-diagram';
        this.animationFrameId = null;
    }

    /**
     * Generate the infrastructure diagram HTML
     * @param {Object} systemStatus - System status data
     * @param {Array} apps - Array of deployed apps
     * @returns {string} HTML diagram
     */
    generateDiagram(systemStatus, apps) {
        const proxmoxHost = systemStatus?.proxmox_host || 'Proxmox Host';
        const nodeCount = systemStatus?.nodes?.length || 0;
        const activeApps = apps?.filter(app => app.status === 'running').length || 0;
        const totalApps = apps?.length || 0;

        // Calculate optimal dimensions based on number of apps
        let viewBoxHeight = 600;
        let scale = 1;
        
        if (totalApps > 0) {
            // Calculate grid dimensions
            const appsPerColumn = 3;
            const cols = Math.ceil(totalApps / appsPerColumn);
            const spacing = 120;
            
            // Adjust viewBox height based on rows
            const rows = Math.ceil(totalApps / appsPerColumn);
            viewBoxHeight = Math.max(600, 300 + rows * spacing + 100);
            
            // Calculate scale to fit on screen
            // Screen height - header - padding - stats
            const availableHeight = window.innerHeight - 200;
            scale = Math.min(1, availableHeight / viewBoxHeight);
            
            // Ensure scale is at least 0.5 for readability
            scale = Math.max(0.5, scale);
        }

        return `
            <div class="infrastructure-diagram" style="--diagram-scale: ${scale};">
                <!-- Title -->
                <div class="diagram-header">
                    <h3>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"></path>
                            <polyline points="10 17 14 13 10 9"></polyline>
                            <line x1="8" y1="13" x2="16" y2="13"></line>
                        </svg>
                        Infrastructure Overview
                    </h3>
                    <div class="diagram-stats">
                        <span class="stat"><strong>${nodeCount}</strong> Node${nodeCount !== 1 ? 's' : ''}</span>
                        <span class="stat"><strong>${totalApps}</strong> App${totalApps !== 1 ? 's' : ''}</span>
                        <span class="stat running"><strong>${activeApps}</strong> Running</span>
                    </div>
                </div>

                <!-- SVG Canvas -->
                <svg id="diagram-canvas" class="diagram-canvas" preserveAspectRatio="xMidYMid meet" viewBox="0 0 1000 ${viewBoxHeight}">
                    <defs>
                        <linearGradient id="grad-proxmox" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#00f5ff;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#00d4ff;stop-opacity:1" />
                        </linearGradient>
                        <linearGradient id="grad-app-running" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#4ade80;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#22c55e;stop-opacity:1" />
                        </linearGradient>
                        <linearGradient id="grad-app-stopped" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#6b7280;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#4b5563;stop-opacity:1" />
                        </linearGradient>
                        <filter id="glow">
                            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                            <feMerge>
                                <feMergeNode in="coloredBlur"/>
                                <feMergeNode in="SourceGraphic"/>
                            </feMerge>
                        </filter>
                        <filter id="shadow">
                            <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.3"/>
                        </filter>
                    </defs>

                    <!-- Background -->
                    <rect width="1000" height="${viewBoxHeight}" fill="#0f1419" opacity="0.5" rx="8"/>

                    <!-- Grid -->
                    <g class="grid" opacity="0.1">
                        <line x1="0" y1="0" x2="1000" y2="0" stroke="#00f5ff"/>
                        <line x1="0" y1="${viewBoxHeight}" x2="1000" y2="${viewBoxHeight}" stroke="#00f5ff"/>
                        <line x1="0" y1="0" x2="0" y2="${viewBoxHeight}" stroke="#00f5ff"/>
                        <line x1="1000" y1="0" x2="1000" y2="${viewBoxHeight}" stroke="#00f5ff"/>
                    </g>

                    <!-- Proxmox Host (Center) -->
                    <g id="proxmox-host" class="proxmox-host" filter="url(#shadow)">
                        <rect x="350" y="200" width="300" height="200" rx="12" fill="url(#grad-proxmox)" opacity="0.2" stroke="url(#grad-proxmox)" stroke-width="2"/>
                        <text x="500" y="250" text-anchor="middle" fill="#00f5ff" font-size="24" font-weight="bold">${proxmoxHost}</text>
                        <text x="500" y="280" text-anchor="middle" fill="#00f5ff" font-size="14" opacity="0.8">Hypervisor</text>
                        <text x="500" y="310" text-anchor="middle" fill="#00f5ff" font-size="12" opacity="0.6">${nodeCount} ${nodeCount === 1 ? 'Node' : 'Nodes'}</text>
                    </g>

                    <!-- Apps Container (Right side) -->
                    <g id="apps-container" class="apps-container">
                        <!-- Apps will be rendered here -->
                    </g>

                    <!-- Network Lines -->
                    <g id="network-lines" class="network-lines">
                        <!-- Connection lines will be rendered here -->
                    </g>
                </svg>

                <!-- Legend -->
                <div class="diagram-legend">
                    <div class="legend-item">
                        <div class="legend-box running"></div>
                        <span>Running</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-box stopped"></div>
                        <span>Stopped</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-box error"></div>
                        <span>Error</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render apps on the diagram
     * @param {Array} apps - Array of app data
     */
    renderApps(apps) {
        const canvas = document.getElementById('diagram-canvas');
        if (!canvas) return;

        const appsContainer = canvas.querySelector('#apps-container');
        const networkLines = canvas.querySelector('#network-lines');
        
        if (!appsContainer || !networkLines) return;

        // Clear existing apps
        appsContainer.innerHTML = '';
        networkLines.innerHTML = '';

        if (!apps || apps.length === 0) {
            appsContainer.innerHTML = `
                <text x="800" y="300" text-anchor="middle" fill="#6b7280" font-size="14">
                    No applications deployed
                </text>
            `;
            return;
        }

        // Calculate grid layout for apps
        const appsPerColumn = 3;
        const startX = 700;
        const startY = 150;
        const boxWidth = 220;
        const boxHeight = 100;
        const spacing = 120;

        apps.forEach((app, index) => {
            const row = index % appsPerColumn;
            const col = Math.floor(index / appsPerColumn);
            const x = startX + col * spacing;
            const y = startY + row * spacing;

            const statusColor = this.getStatusColor(app.status);
            const gradient = this.getStatusGradient(app.status);

            // Connection line from Proxmox to App
            networkLines.innerHTML += `
                <line x1="650" y1="300" x2="${x}" y2="${y + boxHeight / 2}" 
                      stroke="${statusColor}" stroke-width="2" opacity="0.5" class="connection-line"/>
            `;

            // App box
            appsContainer.innerHTML += `
                <g class="app-node" data-app-id="${app.id}">
                    <!-- Box -->
                    <rect x="${x}" y="${y}" width="${boxWidth}" height="${boxHeight}" 
                          rx="8" fill="url(${gradient})" opacity="0.15" 
                          stroke="${statusColor}" stroke-width="2" filter="url(#shadow)"/>
                    
                    <!-- Status indicator -->
                    <circle cx="${x + boxWidth - 15}" cy="${y + 12}" r="6" fill="${statusColor}" opacity="0.8"/>
                    
                    <!-- App name -->
                    <text x="${x + boxWidth / 2}" y="${y + 30}" text-anchor="middle" 
                          fill="#e0e7ff" font-size="13" font-weight="bold" class="truncate">
                        ${this.truncateText(app.hostname || app.name, 20)}
                    </text>
                    
                    <!-- Status badge -->
                    <rect x="${x + 8}" y="${y + 40}" width="${boxWidth - 16}" height="18" 
                          rx="3" fill="${statusColor}" opacity="0.2"/>
                    <text x="${x + boxWidth / 2}" y="${y + 52}" text-anchor="middle" 
                          fill="${statusColor}" font-size="11" font-weight="600">
                        ${this.formatStatus(app.status)}
                    </text>
                    
                    <!-- LXC ID -->
                    <text x="${x + 8}" y="${y + boxHeight - 8}" fill="#9ca3af" font-size="10">
                        LXC #${app.lxc_id}
                    </text>
                </g>
            `;
        });
    }

    /**
     * Get color for status
     * @param {string} status - App status
     * @returns {string} Color hex
     */
    getStatusColor(status) {
        const colors = {
            'running': '#4ade80',
            'stopped': '#6b7280',
            'error': '#ef4444',
            'deploying': '#f59e0b',
            'updating': '#3b82f6'
        };
        return colors[status] || '#6b7280';
    }

    /**
     * Get gradient ID for status
     * @param {string} status - App status
     * @returns {string} Gradient ID
     */
    getStatusGradient(status) {
        if (status === 'running') return '#grad-app-running';
        if (status === 'stopped') return '#grad-app-stopped';
        return '#grad-app-stopped';
    }

    /**
     * Format status text
     * @param {string} status - Status string
     * @returns {string} Formatted status
     */
    formatStatus(status) {
        return status.charAt(0).toUpperCase() + status.slice(1);
    }

    /**
     * Truncate text to max length
     * @param {string} text - Text to truncate
     * @param {number} max - Max length
     * @returns {string} Truncated text
     */
    truncateText(text, max) {
        return text.length > max ? text.substring(0, max - 3) + '...' : text;
    }

    /**
     * Initialize diagram with data
     * @param {Object} systemStatus - System status
     * @param {Array} apps - Apps array
     */
    init(systemStatus, apps) {
        try {
            const html = this.generateDiagram(systemStatus, apps);
            const container = document.getElementById(this.containerId);
            if (!container) {
                console.warn('⚠️  Infrastructure diagram container not found');
                return;
            }
            
            container.innerHTML = html;
            this.renderApps(apps || []);
            this.attachEventListeners();
            console.log('✅ Infrastructure diagram initialized');
        } catch (error) {
            console.error('❌ Error initializing infrastructure diagram:', error);
            const container = document.getElementById(this.containerId);
            if (container) {
                container.innerHTML = `
                    <div class="infrastructure-diagram">
                        <div class="diagram-header">
                            <h3>Infrastructure Overview</h3>
                        </div>
                        <div style="padding: 20px; text-align: center; color: #9ca3af;">
                            <p>Unable to load infrastructure diagram</p>
                            <p style="font-size: 12px; opacity: 0.7; margin-top: 10px;">
                                Check browser console for details
                            </p>
                        </div>
                    </div>
                `;
            }
        }
    }

    /**
     * Attach interactive event listeners
     */
    attachEventListeners() {
        const appNodes = document.querySelectorAll('.app-node');
        appNodes.forEach(node => {
            node.addEventListener('click', () => {
                const appId = node.dataset.appId;
                if (appId) {
                    // Could navigate to app details or trigger action
                    console.log('Clicked app:', appId);
                }
            });

            node.addEventListener('mouseenter', () => {
                node.style.opacity = '1';
            });

            node.addEventListener('mouseleave', () => {
                node.style.opacity = '0.8';
            });
        });
    }
}
