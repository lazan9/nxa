#!/bin/bash
# Deploy scraper API to Hetzner server for shopmind.app
# Usage: ./deploy.sh [server-ip] [api-key]
#
# Prerequisites on server:
#   - Docker & Docker Compose installed
#   - Nginx/Caddy as reverse proxy (optional, for HTTPS)
#
# This script:
#   1. Copies the project to the server
#   2. Builds and starts the API container
#   3. Sets up the cron scraper for scheduled runs
#   4. Configures nginx reverse proxy for scraper.shopmind.app

set -euo pipefail

SERVER="${1:?Usage: ./deploy.sh <server-ip> [api-key]}"
API_KEY="${2:-$(openssl rand -hex 24)}"
REMOTE_DIR="/opt/shopmind/scraper"
SSH_USER="${SSH_USER:-root}"

echo "=== ShopMind Scraper Deployment ==="
echo "Server: $SERVER"
echo "Remote: $REMOTE_DIR"
echo "API Key: $API_KEY"
echo ""

# 1. Create remote directory
echo "[1/5] Creating remote directory..."
ssh "$SSH_USER@$SERVER" "mkdir -p $REMOTE_DIR"

# 2. Sync project files
echo "[2/5] Syncing project files..."
rsync -avz --exclude='data/' --exclude='.git/' --exclude='__pycache__/' \
    ./ "$SSH_USER@$SERVER:$REMOTE_DIR/"

# 3. Create .env file on server
echo "[3/5] Writing .env config..."
ssh "$SSH_USER@$SERVER" "cat > $REMOTE_DIR/.env << 'ENVEOF'
SCRAPER_API_KEY=$API_KEY
ENVEOF"

# 4. Build and start containers
echo "[4/5] Building and starting containers..."
ssh "$SSH_USER@$SERVER" "cd $REMOTE_DIR && docker compose up -d --build api"

# 5. Set up nginx config (if nginx exists)
echo "[5/5] Configuring reverse proxy..."
ssh "$SSH_USER@$SERVER" "
if command -v nginx &>/dev/null; then
    cat > /etc/nginx/sites-available/scraper.shopmind.app << 'NGINXEOF'
server {
    listen 80;
    server_name scraper.shopmind.app;

    location / {
        proxy_pass http://127.0.0.1:8066;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_read_timeout 120s;
    }
}
NGINXEOF
    ln -sf /etc/nginx/sites-available/scraper.shopmind.app /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    echo 'Nginx configured for scraper.shopmind.app'
    echo 'Run: certbot --nginx -d scraper.shopmind.app  (for HTTPS)'
else
    echo 'Nginx not found - API available at http://$SERVER:8066'
fi
"

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "API endpoint:  http://$SERVER:8066"
echo "Health check:  curl http://$SERVER:8066/health"
echo "API docs:      http://$SERVER:8066/docs"
echo "API Key:       $API_KEY"
echo ""
echo "Test commands:"
echo "  curl -H 'X-API-Key: $API_KEY' http://$SERVER:8066/products?demo=true"
echo "  curl -H 'X-API-Key: $API_KEY' http://$SERVER:8066/products?countries=hu,de&brand=minn+kota"
echo "  curl -H 'X-API-Key: $API_KEY' -X POST 'http://$SERVER:8066/scrape?demo=true'"
echo ""
echo "To enable scheduled scraping (every 6 hours):"
echo "  ssh $SSH_USER@$SERVER 'cd $REMOTE_DIR && docker compose --profile cron up -d scraper-cron'"
