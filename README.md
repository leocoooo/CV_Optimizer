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

# DATA QUALITY - Homogénisation des données
just homogenize-db         # Normaliser les colonnes (cleaned_*)

# AI ENRICHMENT - Deep Learning NLP extraction
just enrich-ai             # Enrichir toutes offres non traitées (ai_*)
just enrich-ai-test ID     # Tester enrichissement sur 1 offre
just enrich-ai-force       # Force re-enrichir toutes offres
just enrich-ai-retry       # Réessayer les offres en erreur
just enrich-ai-limit N     # Enrichir max N offres

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

# COLLECTE DE DONNÉES
uv run python -m src.services.france_travail_collector  # France Travail
uv run python -m src.services.scrappe_wttj              # Welcome to the Jungle
uv run python -m src.services.scrappe_hw                # HelloWork

# DATA QUALITY - Homogénisation
uv run python -m src.services.homogenize_database       # Colonnes cleaned_*

# AI ENRICHMENT - Deep Learning NLP
uv run python -m src.services.ai_enrich_database        # Colonnes ai_*
uv run python -m src.services.ai_enrich_database --test-id "job_id"  # Test 1 offre
uv run python -m src.services.ai_enrich_database --retry           # Réessayer erreurs
uv run python -m src.services.ai_enrich_database --limit 100       # Max 100 offres

# VECTORISATION & MATCHING
uv run python -m src.services.processor                 # Vectoriser offres
uv run python -m src.services.matcher                   # Matcher CV/offres

# UTILITAIRES
uv run python -m src.services.cv_reader                 # Extraire texte CV
uv run python -m src.services.llm_advisor               # Recommandations LLM
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
│       ├── homogenize_database.py     # 🆕 Normalisation colonnes
│       ├── ai_enrich_database.py      # 🆕 AI enrichment NLP
│       ├── scraping_utils.py          # Utilitaires scraping
│       └── ...
│
├── models/                            # 🆕 Modèles DL locaux (843 MB)
│   ├── ner/                          # NER CamemBERT (420 MB)
│   └── classifier/                   # Classification CamemBERT (423 MB)
│
├── ui/                            # Interface Streamlit
│   ├── components/               # Composants réutilisables
│   ├── pages/                    # Pages Streamlit
│   └── utils/                    # Utilitaires UI
│
├── data/                          # Données
│   ├── CVs/                      # Fichiers CV
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

## 🧹 Services de qualité de données

### 1️⃣ Homogénéisation des données (`cleaned_*` colonnes)

Le service **homogenize_database** normalise les données existantes pour permettre un matching et un filtrage cohérent.

#### Colonnes créées

| Colonne | Source | Transformation |
|---------|--------|-----------------|
| `cleaned_title` | `title` | Fuzzy match contre titres standardisés + nettoyage H/F |
| `cleaned_contract_type` | `contract_type` | 9 types mappés (CDI, CDD, Stage, Interim, etc.) |
| `cleaned_remote_mode` | `remote_mode` | 3 modes (Pas de télétravail / Possible / Complet) |
| `cleaned_required_experience` | `required_experience` | Années extraites ou 0/2 (débutant/expérience) |
| `cleaned_required_education` | `required_education` | 5 niveaux (Doctorat / Master / Bac+3/4 / Bac+2 / Bac et moins) |

#### Usage

```bash
# Normaliser toutes les offres
just homogenize-db

# Directement
uv run python -m src.services.homogenize_database
```

**Bénéfices** :
- Matching CV ↔ offres plus fiable
- Filtres cohérents sur les offres
- Fusion de données multi-sources

---

### 2️⃣ AI Enrichment - Extraction Deep Learning (`ai_*` colonnes)

Le service **ai_enrich_database** utilise deux modèles CamemBERT français pré-entraînés pour extraire des informations structurées des offres.

#### Modèles utilisés

| Modèle | Tâche | Entités |
|--------|-------|---------|
| **leocooo/v2-camembert-ner-job-ads** | NER (Token Classification) | SKILL, SOFT, LOC, JOB, COMPANY, SECTOR, CONTRACT, LANG, EXP, EDUC, REMOTE |
| **leocooo/camembert-job-classifier** | Classification (Sequence) | MISSION (phrases de missions), OTHER |

#### Colonnes créées

**Résultats bruts** (traçabilité) :
- `output_ner` (JSON) - Entités brutes extraites par le NER
- `output_missions` (TEXT) - Phrases classifiées comme "MISSION"

**Résultats nettoyés** (15 colonnes) :
```
ai_location, ai_job_title, ai_company_name, 
ai_sector, ai_contract_type, ai_languages,
ai_experience_phrase, ai_education_phrase,
ai_hard_skills, ai_soft_skills,
ai_missions,  ← Fusion de output_missions
ai_enrichment_date, ai_enrichment_status
```

#### Configuration initiale

⚠️ **Première exécution** : Les modèles sont téléchargés et stockés localement dans `./models/` (843 MB)

```bash
# Télécharger & initialiser les modèles (5 min)
uv run python << 'EOF'
import os
from huggingface_hub import snapshot_download

os.makedirs('./models/ner', exist_ok=True)
os.makedirs('./models/classifier', exist_ok=True)

print("Téléchargement NER...")
snapshot_download('leocooo/v2-camembert-ner-job-ads',
                 local_dir='./models/ner',
                 local_dir_use_symlinks=False)

print("Téléchargement Classifier...")
snapshot_download('leocooo/camembert-job-classifier',
                 local_dir='./models/classifier',
                 local_dir_use_symlinks=False)
print("✓ Modèles téléchargés!")
EOF
```

#### Usage

```bash
# Première tranche d'enrichissement (offres jamais traitées)
just enrich-ai

# Tester sur une offre
just enrich-ai-test "202XLSC"

# Traiter seulement 100 offres
just enrich-ai-limit 100

# Réessayer les offres en erreur
just enrich-ai-retry

# Force recalcul sur toutes offres
just enrich-ai-force

# Directement
uv run python -m src.services.ai_enrich_database [--retry | --limit N | --force]
```

#### Suivi du statut

```python
from src.database.database import SessionLocal
from src.database.models import JobOffer
from sqlalchemy import func

session = SessionLocal()
stats = session.query(
    JobOffer.ai_enrichment_status,
    func.count(JobOffer.id)
).group_by(JobOffer.ai_enrichment_status).all()

for status, count in stats:
    print(f"{status}: {count}")
# None: 2100  (not yet enriched)
# SUCCESS: 370 (enriched)
# ERROR: 19    (failed - can retry)
```

#### Extraction d'exemple

```json
{
  "ai_job_title": "Développeur-se Python / Linux",
  "ai_hard_skills": "Python, Linux, Docker, FastAPI, Machine Learning, ...",
  "ai_soft_skills": "Autonomie, Rigueur, Collaboration",
  "ai_missions": "Tes missions :\n- Développement backend Python\n- Optimisation pipelines IA\n- Architecture Linux on-prem",
  "ai_enrichment_status": "SUCCESS"
}
```

#### Performance

- **Capacité** : CPU-only (~2-3 sec/offre)
- **Précision** : NER ~92%, Classification ~94% (CamemBERT français)
- **Scalabilité** : Batch de 16 offres, idempotent

**Note** : Les modèles restent locaux. Aucun upload vers Hugging Face. Stockage dans `./models/` qui doit être cloné/téléchargé par les nouveaux utilisateurs.

---

## 📥 Setup pour nouveau développeur

Après avoir cloné le projet :

```bash
# 1. Environnement Python
uv install --all-groups

# 2. Database
docker-compose up -d
uv run python -m src.database.init_db

# 3. Modèles NLP (une seule fois, très important!)
# Option A: Script automatisé (recommandé)
python setup_models.py

# Option B: Manuel
uv run python << 'EOF'
import os
from huggingface_hub import snapshot_download
os.makedirs('./models/ner', exist_ok=True)
os.makedirs('./models/classifier', exist_ok=True)
snapshot_download('leocooo/v2-camembert-ner-job-ads', local_dir='./models/ner', local_dir_use_symlinks=False)
snapshot_download('leocooo/camembert-job-classifier', local_dir='./models/classifier', local_dir_use_symlinks=False)
print("✓ Modèles prêts!")
EOF

# 4. Pre-commit hooks
pre-commit install

# 5. Test!
just backend  # Terminal 1
just frontend # Terminal 2
```

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

### Workflow 2 : Remplir la base avec des offres **enrichies**

```bash
just docker-up              # PostgreSQL
just collect-all            # Collecter toutes sources

# OPTIONNEL mais recommandé : normalisation
just homogenize-db          # Colonnes cleaned_*

# AI Enrichment
just enrich-ai              # Colonnes ai_*

just process                # Vectorisation pour matching
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

CV-Optimizer
