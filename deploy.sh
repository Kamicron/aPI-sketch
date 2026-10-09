#!/usr/bin/env bash
# Déploiement back / front sur l'Optiplex. À lancer SUR le serveur (ou via
# deploy.ps1 depuis le PC). Idempotent.
#
#   bash deploy.sh            # back + front
#   bash deploy.sh back
#   bash deploy.sh front
set -euo pipefail
[ -f "$HOME/.profile" ] && . "$HOME/.profile"

TARGET="${1:-all}"
REPO="/opt/apisketch"
WEBROOT="/var/www/apisketch"
SERVICE="apisketch-back"
FRONT_HOST="api-sketch.pi-cto.top"
API_HOST="api-sketch-back.pi-cto.top"

log() { printf '\n\033[36m== %s ==\033[0m\n' "$*"; }

# nvm : en SSH non-interactif le PATH ne contient que le node système.
load_node() {
    set +eu
    for d in "$NVM_DIR" "$HOME/.config/nvm" "$HOME/.nvm"; do
        if [ -n "$d" ] && [ -s "$d/nvm.sh" ]; then
            export NVM_DIR="$d"
            . "$d/nvm.sh"
            nvm use --lts >/dev/null 2>&1 || nvm use node >/dev/null 2>&1
            break
        fi
    done
    set -eu
}

log "git pull"
git -C "$REPO" pull --ff-only

deploy_back() {
    log "Backend — dépendances"
    cd "$REPO/back"
    [ -d .venv ] || python3 -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -q -r requirements.txt
    log "Backend — service systemd"
    sudo cp "$REPO/deploy/systemd/$SERVICE.service" "/etc/systemd/system/$SERVICE.service"
    sudo systemctl daemon-reload
    log "Backend — restart $SERVICE (migrations Alembic au démarrage)"
    sudo systemctl restart "$SERVICE"
    sleep 3
    if systemctl is-active --quiet "$SERVICE"; then
        echo "  $SERVICE actif"
    else
        echo "  $SERVICE inactif — 40 dernières lignes :"
        journalctl -u "$SERVICE" -n 40 --no-pager
        exit 1
    fi
}

deploy_front() {
    log "Front — build"
    cd "$REPO/front"
    load_node
    node_major=$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)
    if [ "$node_major" -lt 20 ]; then
        echo "!! Node $(node -v 2>/dev/null) trop ancien — le front exige Node >= 20 (nvm install --lts)."
        exit 1
    fi
    npm ci
    npm run build
    log "Front — publication (préserve apk/)"
    sudo mkdir -p "$WEBROOT"
    sudo find "$WEBROOT" -mindepth 1 -maxdepth 1 ! -name apk -exec rm -rf {} +
    sudo cp -r dist/. "$WEBROOT/"
}

deploy_nginx() {
    log "nginx — config"
    for site in "$FRONT_HOST" "$API_HOST"; do
        sudo cp "$REPO/deploy/nginx/$site" "/etc/nginx/sites-available/$site"
        sudo ln -sf "/etc/nginx/sites-available/$site" "/etc/nginx/sites-enabled/$site"
    done
    sudo nginx -t
    sudo systemctl reload nginx
}

case "$TARGET" in
    back)  deploy_back; deploy_nginx ;;
    front) deploy_front; deploy_nginx ;;
    all)   deploy_back; deploy_front; deploy_nginx ;;
    *) echo "usage: bash deploy.sh [all|back|front]"; exit 1 ;;
esac

log "Vérification"
code_front=$(curl -s -o /dev/null -w '%{http_code}' "https://$FRONT_HOST/")
echo "  front  $code_front   https://$FRONT_HOST/"
code_api=""
for _ in $(seq 1 12); do
    code_api=$(curl -s -o /dev/null -w '%{http_code}' "https://$API_HOST/api/health")
    [ "$code_api" = "200" ] && break
    sleep 2
done
echo "  api    $code_api   https://$API_HOST/api/health"

if [ "$code_front" = "200" ] && [ "$code_api" = "200" ]; then
    echo "OK"
else
    echo "!! codes HTTP inattendus"
    exit 1
fi
