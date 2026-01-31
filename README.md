# CV-Optimizer

CV-Optimizer est une API et un ensemble d’outils pour collecter, vectoriser et matcher des offres d’emploi avec des profils de CV, en utilisant FastAPI, PostgreSQL, le scraping et des modèles NLP.

## Fonctionnalités principales

- Collecte d’offres d’emploi depuis plusieurs sources (France Travail, Welcome to the Jungle, HelloWork) via appel API ou scrapping
- Vectorisation des offres et des CV pour le matching sémantique
- API REST pour orchestrer toutes les features
- Orchestration de toutes les étapes (collecte, vectorisation, matching, recommandation LLM)
- Gestion de la base de données PostgreSQL via Docker

## Installation

1. **Prérequis**
	 - Docker et Docker Desktop installés
	 - Python 3.13 ou supérieur
	 - Un environnement virtuel Python

2. **Cloner le projet**
	 ```bash
	 git clone <url-du-repo>
	 cd CV-Optimizer
	 ```

3. **Installer les dépendances Python**
	```bash
	python -m venv .venv
	.venv\Scripts\activate
	uv install
	```

4. **Lancer la base de données**
	 - Démarrer Docker Desktop
	 - Lancer le conteneur PostgreSQL :
		 ```bash
		 docker-compose up -d
		 ```

5. **Initialiser la base de données**
	 ```bash
	 uv run python -m src.database.init_db
	 ```

6. **Lancer l’API**
	 ```bash
	 uvicorn app.main:app --reload
	 ```

## Commandes utiles

- Collecter des offres France Travail :
	```
	uv run python -m src.services.collector
	```
- Scraper Welcome to the Jungle :
	```
	uv run python -m src.services.scrappe_wttj
	```
- Scraper HelloWork :
	```
	uv run python -m src.services.scrappe_hw
	```
- Vectoriser les offres :
	```
	uv run python -m src.services.processor
	```
- Matcher un texte à une offre :
	```
	uv run python -m src.services.matcher
	```
- Lire un CV PDF :
	```
	uv run python -m src.services.cv_reader
	```
- Demander une recommandation à un LLM :
	```
	uv run python -m src.services.llm_advisor
	```
- Orchestration complète sans appel à l'API vous vérifier que tout fonctionne (exemple avec un CV et des mots clés) :
	```
	uv run python -m main "data/CVs/Exemple de CV Data engineer.pdf" "Data Scientist,Data Engineer"
	```

## Structure du projet

- `app/` : code de l’API FastAPI (endpoints, schémas, core, utils)
- `src/` : services de scraping, vectorisation, matching, etc.
- `data/` : dossiers pour les CVs
- `docker-compose.yml` : configuration de la base PostgreSQL

## Remarques

- La première utilisation nécessite de remplir la base avec des offres (Appel API France Travail ou scraping + vectorisation).
- Les endpoints de l’API sont accessibles sur `/api/...` une fois uvicorn lancé.