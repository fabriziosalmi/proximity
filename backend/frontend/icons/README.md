# App Icons Directory

This directory contains local copies of application icons to avoid external requests and CORS issues.

## Structure

- SVG files are preferred for scalability
- PNG files should be at least 512x512px
- Icon filenames should match the app ID from the catalog (lowercase, no spaces)

## Naming Convention

- Use the app `id` from the catalog JSON files
- Example: `nextcloud.svg`, `wordpress.png`, `docker.svg`
- For apps without specific icons, a category-based icon will be used

## Fallback Strategy

1. Check for app-specific icon: `/icons/{app-id}.{svg|png}`
2. Use category-based Lucide icon
3. Use generic emoji fallback

## Adding New Icons

1. Download the icon (SVG preferred)
2. Name it with the app ID
3. Place it in this directory
4. Update the catalog JSON to use the local path: `/icons/{app-id}.svg`
