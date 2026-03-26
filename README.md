# CV-Optimizer

CV-Optimizer est une **plateforme complète** pour collecter, vectoriser et matcher des offres d'emploi avec des profils de CV, combinant une API REST FastAPI, une interface utilisateur Streamlit, et des modèles NLP avancés.

## ✨ Fonctionnalités principales

- 🔍 **Collecte multi-sources** : France Travail (API), Welcome to the Jungle, HelloWork (scraping)
- 📊 **Vectorisation sémantique** : Embeddings pour matching intelligent CV ↔ offres
- 🔗 **API REST complète** : Orchestration de toutes les fonctionnalités
- 🎨 **Interface Streamlit** : Dashboard pour visualiser les offres et matchings
- 🤖 **Recommandations LLM** : Conseils personnalisés basés sur les profils
- 💾 **Base de données PostgreSQL** : Stockage vectoriel avec pgvector

---

## 📋 Prérequis

- **Docker & Docker Compose** : Pour la base de données PostgreSQL (en local)
- **Python 3.13+** : Version requise du projet
- **UV** : Gestionnaire de dépendances (`uv install`)
- **Git** : Contrôle de version

---

## 🚀 Installation complète

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd CV-Optimizer
```

### 2. Configuration de l'environnement Python

```bash
# Créer et activer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
```

### 3. Installer les dépendances

```bash
# Installation complète (dépendances + dev)
uv install --all-groups
```

### 4. Initialiser les pre-commit hooks

```bash
# Important pour la qualité du code (linting, formatage, type checking)
pre-commit install
```

### 5. Démarrer la base de données (pour du local)

```bash
# Lancer le conteneur PostgreSQL en arrière-plan 
docker-compose up -d

# Initialiser les tables
uv run python -m src.database.init_db
```

### 6. Démarrer l'API et l'interface

```bash
# Terminal 1 - API FastAPI
just backend

# Terminal 2 - Interface Streamlit
just frontend
```

---

## 🎯 Utilisation rapide

### Commandes avec `just` (recommandé)

```bash
# DOCKER
just docker-up              # Démarrer la base PostgreSQL
just docker-down            # Arrêter la base
just docker-reset-db        # Réinitialiser la base de données

# COLLECTE DE DONNÉES
just collect-france-travail # API France Travail
just scrape-wttj           # Web Scraping Welcome to the Jungle
just scrape-hw             # Web Scraping HelloWork
just collect-all           # Tous les sources

# TRAITEMENT
just process               # Vectoriser les offres
just match                 # Matcher CVs et offres
just read-cv               # Extraire texte CV
just advise                # Recommandations LLM

# API & UI
just backend               # Démarrer FastAPI
just frontend              # Démarrer Streamlit

# QUALITÉ DU CODE
just format                # Formater le code (Ruff)
just lint                  # Vérifier le code (Ruff)
just typecheck             # Vérification des types (Mypy)
just pre-commit            # Exécuter tous les hooks pre-commit

# WORKFLOWS COMPLETS
just dev                   # Démarrer Docker + afficher instructions API/UI
just dev-full              # Docker + collecter + vectoriser toutes offres
```

### Commandes directes (sans `just`)

```bash
# Lancer l'API
uvicorn app.main:app --reload

# Lancer l'UI Streamlit
streamlit run streamlit_app.py

# Collecter offres France Travail
uv run python -m src.services.france_travail_collector

# Scraper Welcome to the Jungle
uv run python -m src.services.scrappe_wttj

# Scraper HelloWork
uv run python -m src.services.scrappe_hw

# Vectoriser les offres
uv run python -m src.services.processor

# Matcher un CV
uv run python -m src.services.matcher

# Extraire texte d'un CV PDF
uv run python -m src.services.cv_reader

# Obtenir recommandations LLM
uv run python -m src.services.llm_advisor
```

---

## 📁 Structure du projet

```
CV-Optimizer/
├── app/                           # API FastAPI
│   ├── api/
│   │   ├── endpoints/            # Endpoints métier
│   │   │   ├── admin.py
│   │   │   ├── advice.py         # Recommandations LLM
│   │   │   ├── health.py         # Status API
│   │   │   ├── jobs.py           # Gestion offres
│   │   │   ├── match.py          # Matching CVs/offres
│   │   └── router.py
│   ├── core/                      # Logique centrale
│   │   ├── exceptions.py
│   │   ├── middleware.py
│   │   └── security.py
│   ├── schemas/                   # Modèles Pydantic
│   ├── utils/                     # Utilitaires
│   ├── config.py                  # Configuration
│   └── main.py                    # App FastAPI
│
├── src/                           # Services métier
│   ├── database/
│   │   ├── models.py             # Modèles SQLAlchemy
│   │   ├── database.py           # Connexion BD
│   │   └── init_db.py            # Initialisation
│   └── services/
│       ├── france_travail_api.py      # API France Travail
│       ├── france_travail_collector.py # Collecteur
│       ├── scrappe_wttj.py            # Scraper WTTJ
│       ├── scrappe_hw.py              # Scraper HelloWork
│       ├── processor.py               # Vectorisation
│       ├── matcher.py                 # Matching semantic
│       ├── cv_reader.py               # Extraction PDF
│       ├── llm_advisor.py             # Recommandations
│       ├── embedder.py                # Embeddings
│       └── scraping_utils.py          # Utilitaires scraping
│
├── ui/                            # Interface Streamlit
│   ├── components/               # Composants réutilisables
│   ├── pages/                    # Pages Streamlit
│   └── utils/                    # Utilitaires UI
│
├── data/                          # Données
│   ├── CVs/                      # Fichiers CV
│   └── scrapping/                # Données scrappées
│
├── docker-compose.yml             # PostgreSQL + pgvector
├── pyproject.toml                 # Dépendances Python
├── justfile                       # Scripts utilitaires
└── .pre-commit-config.yaml        # Hooks qualité du code
```

---

## ⚙️ Configuration

### Variables d'environnement

Créer un fichier `.env` à la racine (exemple fourni dans `.env_example`) :

```env
# Base de données PostgreSQL
DATABASE_URL=postgresql://admin:secret@localhost:5432/job_db

# APIs externes (si besoin)
FRANCE_TRAVAIL_API_KEY=votre_clé_api
```

### Qualité du code

Le projet utilise des hooks pre-commit automatiques :
- **Ruff** : Linting et formatage
- **Mypy** : Vérification des types Python

Les hooks s'exécutent automatiquement avant chaque commit si initialisés avec `pre-commit install`.

---

## 📝 Workflows typiques

### Workflow 1 : Configuration complète du développement

```bash
just dev                    # Démarrer Docker
# Dans Terminal 2:
just backend                # API
# Dans Terminal 3:
just frontend               # UI
```

### Workflow 2 : Remplir la base avec des offres

```bash
just docker-up              # Démarrer PostgreSQL
just collect-all            # Collecter toutes sources
just process                # Vectoriser les offres
```

### Workflow 3 : Développement complet (collect → process → run)

```bash
just dev-full               # Tout en une commande
```

### Workflow 4 : Vérifier la qualité du code avant commit

```bash
just format                 # Auto-formatter
just lint                   # Vérifier les erreurs
just typecheck              # Vérifier les types
just pre-commit             # Tous les hooks
```

---

## 🔑 Endpoints API principaux

Une fois l'API lancée (`just backend`), accédez à :

- **Documentation interactive** : `http://localhost:8000/docs` (Swagger UI)
- **Documentation alternative** : `http://localhost:8000/redoc` (ReDoc)
- **Status API** : `GET /api/health`
- **Récupérer offres** : `GET /api/jobs`
- **Matcher CV** : `POST /api/match`
- **Recommandations** : `POST /api/advice`

---

## 🐛 Troubleshooting

### Docker ne démarre pas
```bash
# Vérifier les conteneurs
docker ps

# Voir les logs PostgreSQL
docker-compose logs -f db

# Redémarrer
docker-compose restart
```

### Erreur "module not found"
```bash
# Réinstaller les dépendances
uv install --all-groups

# Vérifier l'environnement actif
which python  # Linux/macOS
where python  # Windows
```

### Pre-commit échoue
```bash
# Voir l'erreur complète
just pre-commit

# Fixer automatiquement
just format
```

### Problèmes de connexion PostgreSQL
```bash
# Vérifier la BD
just docker-check-db

# Voir un échantillon de données
just docker-view-data
```

---

## 🤝 Notes importantes

- **Première utilisation** : La base de données est vide. Exécutez `just collect-all` puis `just process` pour remplir avec des offres.
- **Scrapers** : Selenium + Beautiful Soup pour le web scraping. Peuvent être lents selon les sources.
- **Embeddings** : Les modèles sont téléchargés automatiquement la première fois (plusieurs GB).
- **LLM** : Nécessite API keys externes si recommandations LLM activées.
- **Environnement de développement** : Utilisez `just dev-full` pour un setup complet.

---

## 📄 Licence

CV-Optimizer - Projet académique M2 MOSEF
