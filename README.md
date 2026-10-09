# aPI-sketch

App perso de sketchs façon Spotify : on s'abonne à des humoristes, on découvre de
nouveaux sketchs, les comptes se créent uniquement sur invitation. Les sketchs sont
récupérés avec **yt-dlp**.

| Dossier    | Rôle                                   | Stack                                   |
|------------|----------------------------------------|-----------------------------------------|
| `back/`    | API REST                               | Python 3.10+, FastAPI, SQLAlchemy 2, Alembic, MySQL |
| `front/`   | Application web                        | React 19 + Vite + TypeScript (comme InsPI) |
| `android/` | Application Android (étape 4)          | Kotlin + Jetpack Compose, minSdk 28 (Android 9) |
| `deploy/`  | nginx, systemd, PI-peline, PI-ng       |                                         |

Pourquoi FastAPI plutôt que Spring Boot (InsPI) : yt-dlp est une bibliothèque Python,
le back l'appelle directement (métadonnées, téléchargements en tâche de fond) sans
passer par un sous-processus ; le serveur fait déjà tourner du Python (agent PI-ng).
Le front et l'app Android reprennent la structure d'InsPI.

## Domaines (Optiplex, `kamicron_admin@192.168.1.51`)

| Domaine                       | Sert                                  |
|-------------------------------|---------------------------------------|
| `api-sketch.pi-cto.top`       | front (statique, nginx)               |
| `api-sketch-back.pi-cto.top`  | API (nginx → uvicorn `127.0.0.1:8090`) |

## Plan

1. **Socle** (fait) : back + front, comptes sur invitation, config de déploiement,
   intégration PI-peline et PI-ng.
2. **Catalogue** : humoristes, sketchs, import via yt-dlp (chaîne/playlist YouTube →
   métadonnées + miniature), stockage local des fichiers, page admin d'import.
3. **Écoute** : lecteur audio/vidéo (streaming HTTP avec Range), abonnements,
   fil « nouveautés de mes abonnements », découverte, favoris, historique.
4. **Android** : app Kotlin/Compose (Android 9+), lecture en arrière-plan
   (Media3), publication en test interne Google Play.
5. **Finitions** : synchro périodique des humoristes suivis (timer systemd),
   notifications, recherche.

## Développement local

```bash
# Back
cd back
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt     # Linux : .venv/bin/pip
cp .env.example .env                                  # puis renseigner DB_* et JWT_SECRET
.venv/Scripts/alembic upgrade head
.venv/Scripts/python -m app.cli create-admin moi@exemple.fr ludovic
.venv/Scripts/uvicorn app.main:app --reload --port 8090
```

Sans MySQL local, `DATABASE_URL=sqlite:///./dev.db` dans `back/.env` suffit pour
développer. Documentation interactive de l'API : http://localhost:8090/docs.

```bash
# Front
cd front
cp .env.example .env
npm install
npm run dev          # http://localhost:5173
```

Tests back : `.venv/Scripts/python -m pytest -q` (SQLite jetable).

## Comptes et invitations

- Le premier compte (admin) se crée en ligne de commande : `python -m app.cli create-admin`.
- Tout membre connecté peut créer une invitation (page **Invitations**) : un lien
  `/register?code=…` à usage unique, valable 14 jours, éventuellement réservé à un email.
- Authentification par jeton JWT (`Authorization: Bearer …`), valable 30 jours.

| Méthode | Chemin                          | Auth   |
|---------|---------------------------------|--------|
| GET     | `/api/health`                   | —      |
| POST    | `/api/auth/login`               | —      |
| GET     | `/api/auth/invitations/{code}`  | —      |
| POST    | `/api/auth/register`            | —      |
| GET     | `/api/auth/me`                  | Bearer |
| GET     | `/api/invitations`              | Bearer |
| POST    | `/api/invitations`              | Bearer |
| DELETE  | `/api/invitations/{id}`         | Bearer |

## Déploiement

Voir [DEPLOY.md](DEPLOY.md). Ensuite : `.\deploy.ps1` (ou le bouton PI-peline).
