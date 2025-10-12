/**
 * UI Helper Utilities
 * Shared helper functions for rendering icons, formatting data, and UI elements
 */

/**
 * Get app icon configuration based on app name
 * @param {string} name - App name
 * @returns {string} - HTML string for icon (emoji or SVG img tag)
 */
export function getAppIcon(name) {
    // Comprehensive icon mapping with SVG support
    const iconMap = {
        // Popular Apps
        'wordpress': { svg: 'wordpress', emoji: '📝', color: '#21759b' },
        'nextcloud': { svg: 'nextcloud', emoji: '☁️', color: '#0082c9' },
        'portainer': { svg: 'portainer', emoji: '🐳', color: '#13bef9' },
        'nginx': { svg: 'nginx', emoji: '🌐', color: '#009639' },
        'apache': { svg: 'apache', emoji: '🪶', color: '#d22128' },
        
        // Databases
        'mysql': { svg: 'mysql', emoji: '🗄️', color: '#4479a1' },
        'mariadb': { svg: 'mariadb', emoji: '🗄️', color: '#003545' },
        'postgresql': { svg: 'postgresql', emoji: '🐘', color: '#4169e1' },
        'postgres': { svg: 'postgresql', emoji: '🐘', color: '#4169e1' },
        'redis': { svg: 'redis', emoji: '🔴', color: '#dc382d' },
        'mongodb': { svg: 'mongodb', emoji: '🍃', color: '#47a248' },
        
        // Development
        'git': { svg: 'git', emoji: '🔀', color: '#f05032' },
        'gitlab': { svg: 'gitlab', emoji: '🦊', color: '#fc6d26' },
        'github': { svg: 'github', emoji: '🐙', color: '#181717' },
        'jenkins': { svg: 'jenkins', emoji: '👨‍🔧', color: '#d24939' },
        'docker': { svg: 'docker', emoji: '🐳', color: '#2496ed' },
        
        // Monitoring & Analytics
        'grafana': { svg: 'grafana', emoji: '📊', color: '#f46800' },
        'prometheus': { svg: 'prometheus', emoji: '🔥', color: '#e6522c' },
        'elasticsearch': { svg: 'elasticsearch', emoji: '🔍', color: '#005571' },
        'kibana': { svg: 'kibana', emoji: '🔍', color: '#005571' },
        
        // Communication
        'rocketchat': { svg: 'rocketdotchat', emoji: '💬', color: '#f5455c' },
        'mattermost': { svg: 'mattermost', emoji: '💬', color: '#0058cc' },
        'jitsi': { svg: 'jitsi', emoji: '📹', color: '#1d76ba' },
        
        // Media
        'plex': { svg: 'plex', emoji: '🎬', color: '#ebaf00' },
        'jellyfin': { svg: 'jellyfin', emoji: '🎬', color: '#00a4dc' },
        'emby': { svg: null, emoji: '🎬', color: '#52b54b' },
        
        // Productivity
        'bitwarden': { svg: 'bitwarden', emoji: '🔐', color: '#175ddc' },
        'vaultwarden': { svg: 'bitwarden', emoji: '🔐', color: '#175ddc' },
        'bookstack': { svg: 'bookstack', emoji: '📚', color: '#0288d1' },
        'wikijs': { svg: 'wikidotjs', emoji: '📖', color: '#1976d2' },
        
        // File Management
        'syncthing': { svg: 'syncthing', emoji: '🔄', color: '#0891d1' },
        'filebrowser': { svg: null, emoji: '📁', color: '#3f51b5' },
        
        // Security
        'traefik': { svg: 'traefikproxy', emoji: '🔀', color: '#24a1c1' },
        'certbot': { svg: 'letsencrypt', emoji: '🔒', color: '#003a70' },
        'fail2ban': { svg: null, emoji: '🛡️', color: '#d32f2f' },
        
        // CMS & E-commerce
        'drupal': { svg: 'drupal', emoji: '💧', color: '#0678be' },
        'joomla': { svg: 'joomla', emoji: '🌟', color: '#5091cd' },
        'magento': { svg: 'magento', emoji: '🛒', color: '#ee672f' },
        'prestashop': { svg: 'prestashop', emoji: '🛒', color: '#df0067' },
        
        // Others
        'pihole': { svg: 'pihole', emoji: '🕳️', color: '#96060c' },
        'homeassistant': { svg: 'homeassistant', emoji: '🏠', color: '#18bcf2' },
        'node-red': { svg: 'nodered', emoji: '🔴', color: '#8f0000' },
    };
    
    const nameLower = (name || '').toLowerCase();
    
    // Find matching icon
    for (const [key, config] of Object.entries(iconMap)) {
        if (nameLower.includes(key)) {
            return createIconElement(config, name);
        }
    }
    
    // Default fallback
    return createIconElement({ svg: null, emoji: '📦', color: '#6366f1' }, name);
}

/**
 * Create icon element HTML (SVG or emoji)
 * @param {Object} config - Icon configuration {svg, emoji, color}
 * @param {string} appName - App name for alt text
 * @returns {string} - HTML string
 */
function createIconElement(config, appName) {
    // For now, return emoji (SVG implementation can be added later)
    // When implementing SVG: use Simple Icons CDN or local SVG files
    // Example: https://cdn.simpleicons.org/${config.svg}/${config.color.replace('#', '')}
    
    if (config.svg) {
        // Return SVG icon with fallback to emoji
        const escapedEmoji = config.emoji.replace(/'/g, "&#39;").replace(/"/g, "&quot;");
        return `<img 
            src="https://cdn.simpleicons.org/${config.svg}" 
            alt="${appName}" 
            style="width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));"
            onerror="this.style.display='none'; this.insertAdjacentHTML('afterend', '${escapedEmoji}');"
        />`;
    }
    
    // Fallback to emoji
    return config.emoji;
}

/**
 * Render app icon into container element
 * @param {HTMLElement} iconContainer - Container element for icon
 * @param {Object} app - App data with name/id and optional icon URL
 */
export function renderAppIcon(iconContainer, app) {
    // Clear existing content
    iconContainer.innerHTML = '';

    // Get fallback icon (emoji or SVG)
    const fallbackIcon = getAppIcon(app.name || app.id);

    // If app has custom icon URL from catalog
    if (app.icon) {
        const img = document.createElement('img');
        img.src = app.icon;
        img.alt = app.name || app.id;
        img.style.width = '75%';
        img.style.height = '75%';
        img.style.objectFit = 'contain';

        // Fallback to emoji/SVG on error
        img.onerror = function() {
            this.style.display = 'none';
            if (typeof fallbackIcon === 'string') {
                iconContainer.insertAdjacentHTML('beforeend', fallbackIcon);
            }
        };

        iconContainer.appendChild(img);
    } else {
        // Use fallback icon directly
        if (typeof fallbackIcon === 'string') {
            iconContainer.innerHTML = fallbackIcon;
        }
    }
}

/**
 * Get Lucide icon name for a category
 * @param {string} category - Category name
 * @returns {string} - Lucide icon name
 */
export function getCategoryIcon(category) {
    const icons = {
        'Development': 'code',
        'Database': 'database',
        'Web Server': 'globe',
        'Monitoring': 'activity',
        'CMS': 'file-text',
        'E-Commerce': 'shopping-cart',
        'Communication': 'message-circle',
        'Media': 'play-circle',
        'Storage': 'hard-drive',
        'Security': 'shield',
        'Networking': 'network',
        'Automation': 'zap'
    };
    return icons[category] || 'box';
}

/**
 * Format date string to relative or absolute format
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date string
 */
export function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    return date.toLocaleDateString();
}

/**
 * Format bytes to human-readable size
 * @param {number} bytes - Size in bytes
 * @returns {string} - Formatted size string (e.g., "1.5 GB")
 */
export function formatSize(bytes) {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
}

/**
 * Format uptime seconds to human-readable string
 * @param {number} seconds - Uptime in seconds
 * @returns {string} - Formatted uptime string (e.g., "2d 5h")
 */
export function formatUptime(seconds) {
    if (!seconds || seconds < 0) return '--';

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
        return `${days}d ${hours}h`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

/**
 * Get status icon HTML
 * @param {string} status - Status string
 * @returns {string} - HTML string for Lucide icon
 */
export function getStatusIcon(status) {
    const icons = {
        'creating': '<i data-lucide="loader" class="spin"></i>',
        'available': '<i data-lucide="check-circle"></i>',
        'failed': '<i data-lucide="x-circle"></i>',
        'restoring': '<i data-lucide="rotate-cw" class="spin"></i>'
    };
    return icons[status] || '';
}
