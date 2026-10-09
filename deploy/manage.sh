#!/usr/bin/env bash
# Lance une commande d'admin du back (app.cli) avec la config de prod, sur le serveur.
#   bash deploy/manage.sh create-admin moi@exemple.fr ludovic
#   bash deploy/manage.sh invite [email]
set -euo pipefail
exec sudo -u apisketch-svc bash -c '
  set -a; . /etc/apisketch/apisketch.env; set +a
  cd /opt/apisketch/back && exec .venv/bin/python -m app.cli "$@"
' _ "$@"
