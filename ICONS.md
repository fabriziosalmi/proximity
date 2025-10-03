# Icon System Documentation

## Overview

Proximity uses a multi-tier icon system with automatic detection and fallbacks to ensure every application has a proper visual representation.

## Icon Sources

### 1. **Simple Icons CDN** (Primary)
- **URL**: `https://cdn.simpleicons.org/{icon_name}`
- **Coverage**: 2,500+ popular brands and technologies
- **Format**: SVG
- **Self-hosted**: Yes (CDN operated by Simple Icons project)
- **Fallback**: Emoji icons

### 2. **Custom Catalog Icons** (Override)
- Specified in `catalog/catalog.json`
- Can use any external URL or local path
- Takes precedence over auto-detection

### 3. **Emoji Fallbacks** (Always Available)
- Works offline
- Universal support
- Used when SVG fails to load

## Supported Applications

### Content Management
- **WordPress**: SVG icon with blue theme
- **Drupal**: SVG icon with blue drop
- **Joomla**: SVG icon with star

### Databases
- **MySQL**: Official blue logo
- **MariaDB**: Dark teal logo
- **PostgreSQL**: Elephant logo
- **Redis**: Red logo
- **MongoDB**: Green leaf logo

### Development Tools
- **Docker**: Whale logo
- **Git**: Orange logo
- **GitLab**: Fox logo
- **GitHub**: Octocat logo
- **Jenkins**: Butler logo

### Web Servers
- **Nginx**: Green logo
- **Apache**: Feather logo
- **Traefik**: Blue proxy logo

### Monitoring & Analytics
- **Grafana**: Orange dashboard icon
- **Prometheus**: Fire icon
- **Elasticsearch**: Yellow search icon
- **Kibana**: Search visualization icon

### Communication
- **Rocket.Chat**: Red chat icon
- **Mattermost**: Blue chat icon
- **Jitsi**: Video conference icon

### Media Servers
- **Plex**: Yellow media icon
- **Jellyfin**: Blue media icon
- **Emby**: Green media icon

### Security & Networking
- **Bitwarden**: Blue shield icon
- **Pi-hole**: Red hole icon
- **Traefik**: Blue proxy icon
- **Certbot/Let's Encrypt**: Blue lock icon

### File Management
- **Nextcloud**: Blue cloud icon
- **Syncthing**: Sync arrows icon

### Home Automation
- **Home Assistant**: Blue home icon
- **Node-RED**: Red flow icon

## Adding New Icons

### Method 1: Auto-Detection (Recommended)
Add to the `iconMap` in `app.js`:

```javascript
'appname': { 
    svg: 'simpleicons-slug',  // Find at https://simpleicons.org
    emoji: '🎯',               // Fallback emoji
    color: '#FF6B6B'           // Brand color
}
```

### Method 2: Catalog Override
Add icon URL to app definition in `catalog.json`:

```json
{
  "id": "myapp",
  "name": "My App",
  "icon": "https://example.com/icon.png",
  ...
}
```

### Method 3: Custom SVG
Place SVG file in `backend/static/icons/` and reference:

```json
{
  "icon": "/static/icons/myapp.svg"
}
```

## Icon Resolution Flow

```
1. Check if app.icon exists (catalog override)
   ↓ YES → Use custom icon with fallback
   ↓ NO
2. Match app name in iconMap
   ↓ FOUND → Use Simple Icons CDN with emoji fallback
   ↓ NOT FOUND
3. Use default 📦 emoji
```

## Simple Icons Integration

### Finding Icon Slugs
1. Visit https://simpleicons.org
2. Search for your brand/technology
3. Copy the slug (lowercase, hyphenated name)
4. Add to `iconMap` in app.js

### Example Usage
```javascript
// For "Visual Studio Code"
'vscode': { 
    svg: 'visualstudiocode',  // Slug from Simple Icons
    emoji: '💻', 
    color: '#007acc' 
}
```

### CDN URL Format
```
https://cdn.simpleicons.org/{slug}
https://cdn.simpleicons.org/{slug}/{hex-color}
```

## Best Practices

1. **Always provide emoji fallback**: Ensures icons work offline
2. **Use official brand colors**: Maintains consistency
3. **Test SVG loading**: Verify CDN availability
4. **Case-insensitive matching**: App names match regardless of case
5. **Substring matching**: "PostgreSQL" matches "postgres"

## Troubleshooting

### Icon Not Loading?
- Check browser console for CORS errors
- Verify Simple Icons slug is correct
- Ensure fallback emoji is set
- Test icon URL manually: `https://cdn.simpleicons.org/wordpress`

### Wrong Icon Displayed?
- Check iconMap order (first match wins)
- Use more specific app name matching
- Override with catalog icon

### Performance Issues?
- SVG icons are cached by browser
- Emoji icons have zero overhead
- Consider self-hosting for high-traffic deployments

## Self-Hosting Icons (Optional)

To fully self-host icons:

1. Download Simple Icons package:
```bash
npm install simple-icons
```

2. Copy SVG files to `backend/static/icons/`:
```bash
cp node_modules/simple-icons/icons/* backend/static/icons/
```

3. Update icon URLs in code:
```javascript
src="/static/icons/${config.svg}.svg"
```

## Resources

- **Simple Icons**: https://simpleicons.org
- **Icon Guidelines**: https://github.com/simple-icons/simple-icons/blob/develop/CONTRIBUTING.md
- **CDN Status**: https://www.jsdelivr.com/package/npm/simple-icons

## Future Enhancements

- [ ] Local SVG icon cache
- [ ] Custom icon upload per app
- [ ] Icon color theming
- [ ] Animated icons for status
- [ ] Icon search in UI
- [ ] Multi-size icon variants (favicon, card, full)
