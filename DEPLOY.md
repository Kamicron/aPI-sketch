# Déploiement — Optiplex

Cible : `kamicron_admin@192.168.1.51`, dépôt cloné dans `/opt/apisketch`.
Back : service systemd `apisketch-back` (uvicorn sur `127.0.0.1:8091`).
Front : statique dans `/var/www/apisketch`. nginx sert les deux domaines.

## Première installation (une seule fois)

Raccourci : `bash deploy/first-install.sh` sur l'Optiplex fait les étapes 3, 4 et 5 (hors
HTTPS) ; la base (étape 2) doit déjà exister. Le détail ci-dessous reste la référence.

### 1. DNS

`api-sketch.pi-cto.top` et `api-sketch-back.pi-cto.top` doivent pointer vers la même IP
publique que les autres sous-domaines `pi-cto.top`.

### 2. Base MySQL

```sql
CREATE DATABASE apisketch CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'apisketch'@'localhost' IDENTIFIED BY 'mot_de_passe';
GRANT ALL PRIVILEGES ON apisketch.* TO 'apisketch'@'localhost';
FLUSH PRIVILEGES;
```

La base reste vide : Alembic crée les tables au premier démarrage du service.

### 3. Code et utilisateur système

```bash
sudo mkdir -p /opt/apisketch && sudo chown $USER:$USER /opt/apisketch
git clone <url-du-dépôt> /opt/apisketch
sudo useradd -r -s /usr/sbin/nologin apisketch-svc
sudo mkdir -p /var/lib/apisketch/media && sudo chown apisketch-svc: /var/lib/apisketch/media
```

### 4. Configuration

```bash
sudo mkdir -p /etc/apisketch
sudo cp /opt/apisketch/back/.env.example /etc/apisketch/apisketch.env
sudo nano /etc/apisketch/apisketch.env
#   DB_PASSWORD=…, JWT_SECRET=<python3 -c "import secrets;print(secrets.token_hex(32))">
#   CORS_ALLOWED_ORIGINS=https://api-sketch.pi-cto.top
#   MEDIA_DIR=/var/lib/apisketch/media
#   (laisser DATABASE_URL vide)
sudo chown root:apisketch-svc /etc/apisketch/apisketch.env
sudo chmod 640 /etc/apisketch/apisketch.env
```

### 5. Premier déploiement puis HTTPS

```bash
cd /opt/apisketch && bash deploy.sh all
sudo systemctl enable apisketch-back
sudo certbot --nginx -d api-sketch.pi-cto.top -d api-sketch-back.pi-cto.top
```

Certbot modifie `/etc/nginx/sites-available/…` : reporter ses lignes
`# managed by Certbot` dans `deploy/nginx/*` (comme pour InsPI), sinon le prochain
`deploy.sh` les écrase.

### 6. Compte admin

```bash
bash /opt/apisketch/deploy/manage.sh create-admin moi@exemple.fr ludovic
```

### 7. PI-peline et PI-ng

- PI-peline : coller `deploy/pi-peline.project.json` dans la liste `projects` de
  `%USERPROFILE%\.pi-peline\projects.json`, puis ⟳.
- PI-ng : ajouter le bloc de `deploy/pi-ng.service.yaml` à la config de l'agent, puis
  `sudo systemctl restart optiplex-agent`.

## Mises à jour

```powershell
.\deploy.ps1          # back + front
.\deploy.ps1 back
.\deploy.ps1 front
```

`deploy.ps1` fait `git push`, puis en SSH : `git pull` → `bash deploy.sh <cible>`
(venv + pip, migrations Alembic au redémarrage, build Vite, nginx, vérification HTTP).
