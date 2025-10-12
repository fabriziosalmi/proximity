/**
 * Icons Utility Module
 * 
 * Provides icon management and initialization functions.
 * Extracted from app.js as part of final modularization.
 * 
 * @module utils/icons
 */

/**
 * Initialize Lucide icons in the DOM
 * Call this after dynamically adding new elements with data-lucide attributes
 */
export function initLucideIcons() {
    if (typeof lucide !== 'undefined') {
        setTimeout(() => lucide.createIcons(), 0);
    }
}

/**
 * App icon mapping by name
 * Returns emoji icon for known applications
 * @param {string} name - Application name
 * @returns {string} Emoji icon
 */
export function getAppIcon(name) {
    if (!name) return '📦';
    
    const lowerName = name.toLowerCase();
    const iconMap = {
        // Web servers & proxies
        'nginx': '🌐',
        'apache': '🪶',
        'caddy': '🔷',
        'traefik': '🔀',
        'haproxy': '⚖️',
        
        // Databases
        'postgresql': '🐘',
        'postgres': '🐘',
        'mysql': '🐬',
        'mariadb': '🦭',
        'mongodb': '🍃',
        'redis': '📮',
        'elasticsearch': '🔍',
        
        // Development
        'nodejs': '💚',
        'node': '💚',
        'python': '🐍',
        'django': '💚',
        'flask': '🌶️',
        'ruby': '💎',
        'php': '🐘',
        'go': '🐹',
        'rust': '🦀',
        
        // DevOps & CI/CD
        'jenkins': '👷',
        'gitlab': '🦊',
        'gitea': '🍵',
        'drone': '🚁',
        'docker': '🐋',
        'portainer': '📦',
        
        // Monitoring & Observability
        'grafana': '📊',
        'prometheus': '🔥',
        'influxdb': '📈',
        'elk': '🦌',
        'kibana': '🔍',
        'logstash': '📝',
        
        // Communication
        'mattermost': '💬',
        'rocketchat': '🚀',
        'matrix': '🔐',
        
        // Storage & Backup
        'nextcloud': '☁️',
        'owncloud': '☁️',
        'minio': '🗄️',
        'restic': '💾',
        
        // Security
        'vault': '🔐',
        'keycloak': '🔑',
        
        // CMS & Wikis
        'wordpress': '📰',
        'ghost': '👻',
        'wiki': '📚',
        'confluence': '📖',
        
        // Automation
        'ansible': '⚙️',
        'terraform': '🏗️',
        'n8n': '🔗',
        
        // Media
        'plex': '🎬',
        'jellyfin': '🍿',
        'emby': '📺',
        
        // Games
        'minecraft': '⛏️',
        'factorio': '⚙️',
        'valheim': '⚔️'
    };
    
    return iconMap[lowerName] || '📦';
}

/**
 * Get status icon HTML for backup/deployment status
 * @param {string} status - Status string
 * @returns {string} HTML string with Lucide icon
 */
export function getStatusIcon(status) {
    const icons = {
        'creating': '<i data-lucide="loader" class="spin"></i>',
        'available': '<i data-lucide="check-circle"></i>',
        'failed': '<i data-lucide="x-circle"></i>',
        'restoring': '<i data-lucide="rotate-cw" class="spin"></i>',
        'running': '<i data-lucide="play-circle"></i>',
        'stopped': '<i data-lucide="stop-circle"></i>',
        'paused': '<i data-lucide="pause-circle"></i>',
        'pending': '<i data-lucide="clock"></i>',
        'error': '<i data-lucide="alert-circle"></i>',
        'success': '<i data-lucide="check-circle-2"></i>',
        'warning': '<i data-lucide="alert-triangle"></i>'
    };
    return icons[status] || '<i data-lucide="circle"></i>';
}

/**
 * Get status CSS class based on status string
 * @param {string} status - Status string
 * @returns {string} CSS class name
 */
export function getStatusClass(status) {
    const statusMap = {
        'running': 'status-running',
        'stopped': 'status-stopped',
        'error': 'status-error',
        'failed': 'status-error',
        'pending': 'status-pending',
        'creating': 'status-pending',
        'success': 'status-success',
        'available': 'status-success',
        'warning': 'status-warning',
        'restoring': 'status-pending'
    };
    return statusMap[status] || 'status-unknown';
}

/**
 * Create status badge HTML
 * @param {string} status - Status string
 * @param {string} label - Optional custom label
 * @returns {string} HTML string for status badge
 */
export function createStatusBadge(status, label = null) {
    const displayLabel = label || status;
    const statusClass = getStatusClass(status);
    const icon = getStatusIcon(status);
    
    return `
        <span class="status-badge ${statusClass}">
            ${icon}
            <span class="status-label">${displayLabel}</span>
        </span>
    `;
}

/**
 * Get icon for resource type
 * @param {string} type - Resource type (cpu, ram, disk, network)
 * @returns {string} Lucide icon name
 */
export function getResourceIcon(type) {
    const icons = {
        'cpu': 'cpu',
        'ram': 'memory-stick',
        'memory': 'memory-stick',
        'disk': 'hard-drive',
        'storage': 'hard-drive',
        'network': 'network',
        'net': 'network'
    };
    return icons[type.toLowerCase()] || 'activity';
}
