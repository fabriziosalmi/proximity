# Proximity App Catalog

This directory contains the application catalog for Proximity - a collection of self-hosted Docker applications that can be deployed via the platform.

## Directory Structure

```
catalog/
├── apps/                   # Individual app definition files
│   ├── index.json         # Catalog index listing all apps
│   ├── wordpress.json     # WordPress app definition
│   ├── nextcloud.json     # Nextcloud app definition
│   ├── gitea.json         # Gitea app definition
│   ├── n8n.json           # n8n app definition
│   ├── portainer.json     # Portainer app definition
│   └── nginx.json         # Nginx app definition
└── catalog.json.backup    # Legacy catalog file (backup)
```

## App Definition Format

Each app is defined in its own JSON file with the following structure:

```json
{
  "id": "app-id",
  "name": "App Name",
  "description": "Brief description of the application",
  "version": "latest",
  "icon": "https://example.com/icon.png",
  "category": "Category",
  "docker_compose": {
    "version": "3.8",
    "services": {
      "app": {
        "image": "app:latest",
        "ports": ["80:80"],
        "environment": {},
        "volumes": []
      }
    },
    "volumes": {}
  },
  "ports": [80],
  "volumes": ["app_data"],
  "environment": {},
  "min_memory": 512,
  "min_cpu": 1,
  "tags": ["tag1", "tag2"],
  "author": "Author Name",
  "website": "https://example.com"
}
```

## Adding New Apps

### Method 1: Add Individual App File

1. Create a new JSON file in `catalog/apps/` directory (e.g., `myapp.json`)
2. Add the app definition following the format above
3. Update `catalog/apps/index.json` to include your new app:
   ```json
   {
     "apps": [
       "wordpress.json",
       "nextcloud.json",
       "myapp.json"
     ]
   }
   ```
4. Restart Proximity backend to reload the catalog

### Method 2: Use External Repository

You can also maintain apps in a Git repository and pull them automatically:

1. Create a Git repository with app definitions
2. Configure Proximity to sync from the repository
3. Apps will be automatically loaded on startup

## App Categories

Available categories:
- **CMS** - Content Management Systems
- **Storage** - File storage and sync platforms
- **DevOps** - Development and operations tools
- **Web Server** - HTTP servers and reverse proxies
- **Automation** - Workflow automation tools
- **Database** - Database management systems
- **Monitoring** - Monitoring and observability tools
- **Media** - Media servers and streaming platforms
- **Communication** - Chat, email, and collaboration tools
- **Security** - Security and authentication services

## Docker Compose Requirements

All apps must:
- Use Docker Compose format version 3.8 or higher
- Define all required services, volumes, and networks
- Include environment variables with default values
- Specify resource requirements (min_memory, min_cpu)
- Use official or well-maintained Docker images

## Testing Your App

Before adding an app to the catalog:

1. Test the Docker Compose file locally:
   ```bash
   docker-compose -f app-compose.yml up -d
   ```

2. Verify all services start correctly
3. Test the application functionality
4. Check resource usage (memory, CPU)
5. Document any required configuration

## Best Practices

### Security
- Use specific image versions when possible (avoid `:latest` in production)
- Set strong default passwords
- Document any security considerations
- Use secrets for sensitive data

### Resource Limits
- Specify realistic minimum requirements
- Consider multi-service applications (e.g., app + database)
- Test with minimum resources before publishing

### Documentation
- Provide clear, concise descriptions
- Include setup instructions in comments
- Document exposed ports and their purposes
- List any required post-deployment configuration

### Icons
- Use HTTPS URLs for icons
- Prefer PNG or SVG formats
- Ensure icons are publicly accessible
- Include fallback emoji in app name

## Example: Adding Grafana

Create `catalog/apps/grafana.json`:

```json
{
  "id": "grafana",
  "name": "Grafana",
  "description": "Analytics and monitoring platform with beautiful dashboards",
  "version": "latest",
  "category": "Monitoring",
  "docker_compose": {
    "version": "3.8",
    "services": {
      "grafana": {
        "image": "grafana/grafana:latest",
        "ports": ["3000:3000"],
        "environment": {
          "GF_SECURITY_ADMIN_PASSWORD": "admin",
          "GF_INSTALL_PLUGINS": ""
        },
        "volumes": ["grafana_data:/var/lib/grafana"],
        "restart": "always"
      }
    },
    "volumes": {
      "grafana_data": {}
    }
  },
  "ports": [3000],
  "volumes": ["grafana_data"],
  "environment": {
    "GF_SECURITY_ADMIN_PASSWORD": "admin"
  },
  "min_memory": 512,
  "min_cpu": 1,
  "tags": ["monitoring", "dashboard", "metrics", "visualization"],
  "author": "Grafana Labs",
  "website": "https://grafana.com"
}
```

Update `catalog/apps/index.json`:
```json
{
  "apps": [
    "wordpress.json",
    "nextcloud.json",
    "grafana.json"
  ]
}
```

Restart Proximity and Grafana will appear in the app marketplace!

## Contributing

When contributing new apps:

1. Test thoroughly in a local environment
2. Follow the app definition format exactly
3. Provide complete metadata (tags, author, website)
4. Document any special requirements
5. Submit a pull request with your app definition

## Support

For issues or questions:
- Check existing app definitions for examples
- Review Docker Compose documentation
- Test locally before deployment
- Report issues on GitHub

---

**Note**: This catalog structure supports scaling to hundreds or thousands of apps. Each app is independently versioned and can be updated without affecting others.
