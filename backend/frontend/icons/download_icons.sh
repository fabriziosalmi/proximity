#!/bin/bash

# Script to download common app icons locally
# This eliminates external requests and CORS issues

ICON_DIR="$(dirname "$0")"
cd "$ICON_DIR" || exit 1

echo "📥 Downloading app icons..."

# Function to download icon with fallback
download_icon() {
    local name="$1"
    local url="$2"
    local output="${name}.svg"
    
    if [ -f "$output" ]; then
        echo "✓ $output already exists, skipping..."
        return
    fi
    
    echo "  Downloading $name..."
    if curl -L -f -s "$url" -o "$output" 2>/dev/null; then
        echo "  ✓ Downloaded $output"
    else
        echo "  ✗ Failed to download $output"
        rm -f "$output"
    fi
}

# Download common app icons
# Format: download_icon "app-id" "url"

download_icon "docker" "https://cdn.simpleicons.org/docker/2496ED"
download_icon "nginx" "https://cdn.simpleicons.org/nginx/009639"
download_icon "nextcloud" "https://cdn.simpleicons.org/nextcloud/0082C9"
download_icon "wordpress" "https://cdn.simpleicons.org/wordpress/21759B"
download_icon "gitlab" "https://cdn.simpleicons.org/gitlab/FC6D26"
download_icon "grafana" "https://cdn.simpleicons.org/grafana/F46800"
download_icon "prometheus" "https://cdn.simpleicons.org/prometheus/E6522C"
download_icon "portainer" "https://cdn.simpleicons.org/portainer/13BEF9"
download_icon "traefik" "https://cdn.simpleicons.org/traefik/24A1C1"
download_icon "postgres" "https://cdn.simpleicons.org/postgresql/4169E1"
download_icon "mysql" "https://cdn.simpleicons.org/mysql/4479A1"
download_icon "mariadb" "https://cdn.simpleicons.org/mariadb/003545"
download_icon "mongodb" "https://cdn.simpleicons.org/mongodb/47A248"
download_icon "redis" "https://cdn.simpleicons.org/redis/DC382D"
download_icon "elasticsearch" "https://cdn.simpleicons.org/elasticsearch/005571"
download_icon "jenkins" "https://cdn.simpleicons.org/jenkins/D24939"
download_icon "sonarqube" "https://cdn.simpleicons.org/sonarqube/4E9BCD"
download_icon "minio" "https://cdn.simpleicons.org/minio/C72E49"
download_icon "plex" "https://cdn.simpleicons.org/plex/E5A00D"
download_icon "emby" "https://cdn.simpleicons.org/emby/52B54B"
download_icon "jellyfin" "https://cdn.simpleicons.org/jellyfin/00A4DC"
download_icon "homeassistant" "https://cdn.simpleicons.org/homeassistant/18BCF2"
download_icon "openvpn" "https://cdn.simpleicons.org/openvpn/EA7E20"
download_icon "wireguard" "https://cdn.simpleicons.org/wireguard/88171A"
download_icon "pihole" "https://cdn.simpleicons.org/pihole/96060C"
download_icon "bitwarden" "https://cdn.simpleicons.org/bitwarden/175DDC"
download_icon "vaultwarden" "https://cdn.simpleicons.org/bitwarden/175DDC"
download_icon "photoprism" "https://cdn.simpleicons.org/photoprism/18BAB3"
download_icon "radarr" "https://cdn.simpleicons.org/radarr/FFC230"
download_icon "sonarr" "https://cdn.simpleicons.org/sonarr/35C5F4"
download_icon "lidarr" "https://cdn.simpleicons.org/lidarr/159552"
download_icon "bazarr" "https://cdn.simpleicons.org/bazarr"
download_icon "prowlarr" "https://cdn.simpleicons.org/prowlarr"
download_icon "readarr" "https://cdn.simpleicons.org/readarr"
download_icon "transmission" "https://cdn.simpleicons.org/transmission/B8001F"
download_icon "qbittorrent" "https://cdn.simpleicons.org/qbittorrent/3D85C6"
download_icon "syncthing" "https://cdn.simpleicons.org/syncthing/0891D1"
download_icon "code-server" "https://cdn.simpleicons.org/visualstudiocode/007ACC"
download_icon "vscode" "https://cdn.simpleicons.org/visualstudiocode/007ACC"
download_icon "mattermost" "https://cdn.simpleicons.org/mattermost/0058CC"
download_icon "rocketchat" "https://cdn.simpleicons.org/rocketdotchat/F5455C"
download_icon "ghost" "https://cdn.simpleicons.org/ghost/15171A"
download_icon "wikijs" "https://cdn.simpleicons.org/wikidotjs/1976D2"
download_icon "bookstack" "https://cdn.simpleicons.org/bookstack/0288D1"
download_icon "outline" "https://cdn.simpleicons.org/outline/0E1318"
download_icon "gitea" "https://cdn.simpleicons.org/gitea/609926"
download_icon "gogs" "https://cdn.simpleicons.org/gogs/625432"
download_icon "matomo" "https://cdn.simpleicons.org/matomo/3152A0"
download_icon "plausible" "https://cdn.simpleicons.org/plausible/5850EC"
download_icon "umami" "https://cdn.simpleicons.org/umami/000000"
download_icon "n8n" "https://cdn.simpleicons.org/n8n/EA4B71"
download_icon "nodered" "https://cdn.simpleicons.org/noderedge/8F0000"
download_icon "huginn" "https://cdn.simpleicons.org/huginn/1C4E80"
download_icon "nocodb" "https://cdn.simpleicons.org/nocodb/0060A9"
download_icon "baserow" "https://cdn.simpleicons.org/baserow/4B85F3"
download_icon "appsmith" "https://cdn.simpleicons.org/appsmith/FD784B"
download_icon "tooljet" "https://cdn.simpleicons.org/tooljet/3F51B5"
download_icon "budibase" "https://cdn.simpleicons.org/budibase/FF6D42"
download_icon "strapi" "https://cdn.simpleicons.org/strapi/2F2E8B"
download_icon "directus" "https://cdn.simpleicons.org/directus/263238"
download_icon "supabase" "https://cdn.simpleicons.org/supabase/3ECF8E"
download_icon "hasura" "https://cdn.simpleicons.org/hasura/1EB4D4"
download_icon "metabase" "https://cdn.simpleicons.org/metabase/509EE3"
download_icon "redash" "https://cdn.simpleicons.org/redash/FF7964"
download_icon "superset" "https://cdn.simpleicons.org/apachesuperset/20A6C9"
download_icon "excalidraw" "https://cdn.simpleicons.org/excalidraw/6965DB"
download_icon "drawio" "https://cdn.simpleicons.org/diagramsdotnet/F08705"
download_icon "mermaid" "https://cdn.simpleicons.org/mermaid/FF3670"
download_icon "docusaurus" "https://cdn.simpleicons.org/docusaurus/3ECC5F"
download_icon "hugo" "https://cdn.simpleicons.org/hugo/FF4088"
download_icon "jekyll" "https://cdn.simpleicons.org/jekyll/CC0000"
download_icon "vitepress" "https://cdn.simpleicons.org/vite/646CFF"

echo ""
echo "✅ Icon download complete!"
echo "📁 Icons saved to: $ICON_DIR"
echo ""
echo "Note: Some icons may have failed due to network issues or invalid URLs."
echo "You can manually add missing icons to this directory."
