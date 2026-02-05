# Interface Streamlit CV-Optimizer

Interface utilisateur Streamlit pour le système CV-Optimizer, permettant l'upload de CV, le matching avec des offres d'emploi, et l'obtention de conseils personnalisés.

## 🎯 Fonctionnalités

- **Upload de CV** : Upload et validation de fichiers PDF
- **Matching intelligent** : Correspondance CV/offres via recherche vectorielle
- **Filtrage avancé** : Filtres par localisation, type de contrat, expérience
- **Détails d'offres** : Consultation complète des offres d'emploi
- **Conseils LLM** : Recommandations personnalisées pour améliorer les candidatures
- **Interface responsive** : Optimisée pour différentes tailles d'écran

## 🏗️ Architecture

```
streamlit_interface/
├── main.py              # Point d'entrée Streamlit
├── config.py            # Configuration et constantes
├── api_client.py        # Client pour l'API backend
├── state_manager.py     # Gestion d'état Streamlit
├── ui_components.py     # Composants UI réutilisables
├── error_handler.py     # Gestion centralisée des erreurs
├── models.py            # Modèles de données
├── utils.py             # Utilitaires divers
├── requirements.txt     # Dépendances Python
└── README.md           # Documentation
```

## 🚀 Installation

### Prérequis

- Python 3.8+
- Backend FastAPI CV-Optimizer en fonctionnement
- Dépendances listées dans `requirements.txt`

### Installation des dépendances

```bash
cd streamlit_interface
pip install -r requirements.txt
```

### Configuration

Créez un fichier `.env` dans le répertoire racine (optionnel) :

```env
# Configuration API
API_BASE_URL=http://localhost:8000

# Configuration des fichiers
MAX_FILE_SIZE=10485760  # 10MB en bytes

# Configuration des requêtes
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=1.0

# Configuration du cache
CACHE_TTL=300  # 5 minutes

# Configuration UI
PAGE_SIZE=20
DEFAULT_LOCATION=
DEFAULT_CONTRACT_TYPE=
DEFAULT_EXPERIENCE_LEVEL=
```

## 🎮 Utilisation

### Démarrage de l'application

```bash
cd streamlit_interface
streamlit run main.py
```

L'application sera accessible à l'adresse : `http://localhost:8501`

### Workflow utilisateur

1. **Upload du CV** : Sélectionnez un fichier PDF contenant votre CV
2. **Analyse** : Cliquez sur "Analyser le CV" pour lancer le matching
3. **Résultats** : Consultez les offres correspondantes avec leurs scores
4. **Filtrage** : Utilisez les filtres pour affiner les résultats
5. **Détails** : Cliquez sur "Voir détails" pour consulter une offre
6. **Conseils** : Obtenez des recommandations personnalisées

## 🔧 Configuration avancée

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `API_BASE_URL` | URL du backend FastAPI | `http://localhost:8000` |
| `MAX_FILE_SIZE` | Taille max des fichiers (bytes) | `10485760` (10MB) |
| `REQUEST_TIMEOUT` | Timeout des requêtes (secondes) | `30` |
| `MAX_RETRIES` | Nombre max de tentatives | `3` |
| `CACHE_TTL` | Durée de vie du cache (secondes) | `300` |
| `PAGE_SIZE` | Nombre d'offres par page | `20` |

### Personnalisation de l'interface

Les composants UI peuvent être personnalisés dans `ui_components.py` :

- Couleurs et styles
- Messages d'interface
- Validation des fichiers
- Format d'affichage

## 🔌 API Backend

L'interface communique avec les endpoints suivants du backend FastAPI :

- `GET /health` : Vérification de santé
- `POST /api/match` : Matching CV/offres
- `GET /api/jobs` : Recherche d'offres avec filtres
- `GET /api/jobs/{job_id}` : Détails d'une offre
- `POST /api/advice` : Génération de conseils LLM

## 🐛 Gestion d'erreurs

L'application gère automatiquement :

- **Erreurs de connexion** : Retry automatique avec backoff
- **Erreurs de validation** : Messages d'aide contextuelle
- **Erreurs API** : Traduction en français des messages
- **Timeouts** : Gestion des requêtes longues

### Messages d'erreur courants

- **"Impossible de se connecter au serveur"** : Backend non accessible
- **"Le fichier doit être au format PDF"** : Format de fichier invalide
- **"Fichier trop volumineux"** : Dépasse la taille maximale
- **"La requête a pris trop de temps"** : Timeout de requête

## 📊 Performance

### Optimisations implémentées

- **Cache de session** : Conservation des données utilisateur
- **Cache API** : Évite les requêtes répétées (TTL: 5 min)
- **Validation côté client** : Réduit les appels API inutiles
- **Chargement lazy** : Détails d'offres chargés à la demande

### Métriques cibles

- Temps de chargement initial : < 3 secondes
- Temps de réponse API : < 5 secondes
- Taille maximale fichier : 10MB
- Cache TTL : 5 minutes

## 🧪 Tests

### Tests unitaires

```bash
# Installation des dépendances de test
pip install pytest pytest-streamlit

# Exécution des tests
pytest tests/
```

### Tests d'intégration

```bash
# Test avec backend local
python -m pytest tests/integration/ --backend-url=http://localhost:8000
```

## 🔒 Sécurité

### Mesures de sécurité

- **Validation des fichiers** : Vérification format et taille
- **Sanitisation des entrées** : Nettoyage des données utilisateur
- **Gestion des sessions** : Données sensibles en mémoire uniquement
- **HTTPS recommandé** : Pour la production

### Bonnes pratiques

- Ne jamais stocker les CV sur disque
- Limiter la taille des uploads
- Valider tous les inputs utilisateur
- Logger les erreurs sans exposer de données sensibles

## 🚀 Déploiement

### Déploiement local

```bash
streamlit run main.py --server.port 8501 --server.address 0.0.0.0
```

### Déploiement avec Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Déploiement Streamlit Cloud

1. Push du code sur GitHub
2. Connexion à [share.streamlit.io](https://share.streamlit.io)
3. Sélection du repository et de la branche
4. Configuration des variables d'environnement

## 📝 Logs

### Configuration des logs

Les logs sont gérés par `loguru` avec les niveaux :

- **DEBUG** : Détails techniques
- **INFO** : Actions utilisateur et opérations
- **WARNING** : Problèmes non critiques
- **ERROR** : Erreurs nécessitant attention

### Exemple de logs

```
15:30:45 | INFO     | Session Streamlit initialisée
15:30:47 | INFO     | CV stocké en session: cv_exemple.pdf (245760 bytes)
15:30:50 | INFO     | Matching réussi: 8 offres trouvées
15:30:52 | WARNING  | Cache expiré pour endpoint_jobs_filter_paris
```

## 🤝 Contribution

### Structure du code

- **main.py** : Application principale et navigation
- **api_client.py** : Communication avec le backend
- **ui_components.py** : Composants d'interface
- **state_manager.py** : Gestion de l'état Streamlit
- **error_handler.py** : Traitement des erreurs
- **models.py** : Structures de données
- **utils.py** : Fonctions utilitaires

### Guidelines

1. Respecter la structure modulaire
2. Documenter toutes les fonctions
3. Gérer les erreurs de manière appropriée
4. Tester les nouvelles fonctionnalités
5. Maintenir la compatibilité avec l'API backend

## 📞 Support

Pour toute question ou problème :

1. Vérifiez que le backend FastAPI est démarré
2. Consultez les logs pour identifier l'erreur
3. Vérifiez la configuration des variables d'environnement
4. Testez la connectivité réseau

## 📄 Licence

Ce projet fait partie du système CV-Optimizer. Voir le fichier LICENSE du projet principal pour les détails de licence.