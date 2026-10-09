#!/usr/bin/env bash
# Première installation sur l'Optiplex (à lancer UNE fois, sur le serveur, en tant
# que kamicron_admin — pas en root : le script appelle sudo lui-même).
#
#   curl -fsSL https://raw.githubusercontent.com/Kamicron/aPI-sketch/main/deploy/first-install.sh -o first-install.sh
#   less first-install.sh          # à relire avant de lancer
#   bash first-install.sh
#
# Ne touche pas à MySQL : la base `aPI-sketch` et l'utilisateur `api-sketch` doivent
# déjà exister (Alembic crée seulement les tables au premier démarrage du service).
# Ne touche pas aux autres sites nginx. Idempotent : relançable sans casse.
set -euo pipefail

REPO_URL="https://github.com/Kamicron/aPI-sketch.git"
REPO="/opt/apisketch"
ENV_FILE="/etc/apisketch/apisketch.env"
MEDIA_DIR="/var/lib/apisketch/media"
SVC_USER="apisketch-svc"
PORT=8091
FRONT_HOST="api-sketch.pi-cto.top"
API_HOST="api-sketch-back.pi-cto.top"

log() { printf '\n\033[36m== %s ==\033[0m\n' "$*"; }
die() { printf '\033[31m!! %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" -ne 0 ] || die "Ne pas lancer en root : lance-le avec ton utilisateur (sudo est appelé au besoin)."

log "Vérifications préalables"
for c in git python3 node npm curl sudo; do
    command -v "$c" >/dev/null || die "$c est absent."
done
[ -x /usr/sbin/nginx ] || sudo test -x /usr/sbin/nginx || die "nginx est absent."
node_major=$(node -p 'process.versions.node.split(".")[0]')
[ "$node_major" -ge 20 ] || die "Node $(node -v) trop ancien (>= 20 requis)."
python3 -c "import venv, ensurepip" 2>/dev/null || die "python3-venv manquant (sudo apt install python3-venv)."
if ss -ltn | awk '{print $4}' | grep -qE "[:.]$PORT\$"; then
    # Tolérer le cas où c'est déjà notre propre service (relance du script).
    systemctl is-active --quiet apisketch-back 2>/dev/null \
        || die "Le port $PORT est déjà utilisé par autre chose."
fi
echo "  ok"

log "Code dans $REPO"
if [ -d "$REPO/.git" ]; then
    echo "  déjà cloné"
else
    sudo mkdir -p "$REPO"
    sudo chown "$USER:$USER" "$REPO"
    git clone "$REPO_URL" "$REPO"
fi

log "Utilisateur système et dossier des médias"
id "$SVC_USER" >/dev/null 2>&1 || sudo useradd -r -s /usr/sbin/nologin "$SVC_USER"
sudo mkdir -p "$MEDIA_DIR"
sudo chown "$SVC_USER": "$MEDIA_DIR"

log "Configuration $ENV_FILE"
if sudo test -f "$ENV_FILE"; then
    echo "  existe déjà — conservé tel quel (supprime-le pour le régénérer)"
else
    read -r -s -p "  Mot de passe MySQL de l'utilisateur api-sketch : " DB_PASSWORD
    echo
    [ -n "$DB_PASSWORD" ] || die "Mot de passe vide."
    JWT_SECRET=$(python3 -c 'import secrets;print(secrets.token_hex(32))')
    sudo mkdir -p /etc/apisketch
    # umask restrictif : le fichier n'est jamais lisible par les autres, même un instant.
    (
        umask 077
        sudo tee "$ENV_FILE" >/dev/null <<EOF
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aPI-sketch
DB_USERNAME=api-sketch
DB_PASSWORD=$DB_PASSWORD
DATABASE_URL=
SERVER_PORT=$PORT
JWT_SECRET=$JWT_SECRET
JWT_TTL_DAYS=30
INVITE_TTL_DAYS=14
CORS_ALLOWED_ORIGINS=https://$FRONT_HOST
MEDIA_DIR=$MEDIA_DIR
EOF
    )
    unset DB_PASSWORD JWT_SECRET
    sudo chown root:"$SVC_USER" "$ENV_FILE"
    sudo chmod 640 "$ENV_FILE"
    echo "  créé (640 root:$SVC_USER)"
fi

log "Déploiement (venv, migrations, build du front, nginx)"
# SKIP_VERIFY : le HTTPS n'existe pas encore, la vérification finale échouerait.
SKIP_VERIFY=1 bash "$REPO/deploy.sh" all

log "Activation du service au démarrage"
sudo systemctl enable apisketch-back

log "Test local de l'API"
curl -fsS "http://127.0.0.1:$PORT/api/health" && echo

cat <<EOF

\033[32mInstallation terminée.\033[0m Restent deux étapes manuelles :

1. HTTPS (les deux domaines doivent déjà pointer vers l'Optiplex) :
     sudo certbot --nginx -d $FRONT_HOST -d $API_HOST
   puis reporter les lignes "# managed by Certbot" dans deploy/nginx/* (sinon le
   prochain deploy.sh les écrase) et vérifier avec :  bash $REPO/deploy.sh all

2. Premier compte admin :
     bash $REPO/deploy/manage.sh create-admin <email> <pseudo>
EOF
