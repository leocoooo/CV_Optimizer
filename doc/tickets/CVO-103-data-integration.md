# CVO-103 · Intégration des données depuis `app`

Statut: Terminé

## Objectif

Faire en sorte que la nouvelle interface consomme proprement les données du backend `app` au lieu de bricoler des affichages uniquement côté Streamlit.

## Ce qui a été fait

- ajout d'un endpoint public agrégé `GET /api/dashboard`
- création des schémas dédiés dans `app/schemas/dashboard.py`
- branchement de la route dans `app/api/router.py`
- enrichissement du client `ui/utils/api_client.py`
- correction de l'envoi des paramètres de matching au format attendu par FastAPI

## Comment cela a été fait

### Endpoint dashboard

Le nouveau endpoint agrège:

- le nombre total d'offres
- le nombre d'offres vectorisées
- le taux d'indexation
- le nombre de sources actives
- la dernière date d'ingestion connue
- des répartitions par source, contrat et région
- une sélection d'offres récentes pour le cockpit

### Client UI

Le client API expose maintenant:

- `get_status()`
- `get_dashboard()`
- `get_job_details()`
- `match_cv()` corrigé

### Point technique important

L'ancienne implémentation envoyait certains paramètres du matching en query string alors que l'endpoint FastAPI les attend en `Form(...)`. La nouvelle version envoie bien ces champs dans `data=...`, ce qui réaligne l'UI avec le backend.

## Validation prévue

- vérification de syntaxe Python sur `app/`, `ui/` et `streamlit_app.py`
- vérification manuelle du chargement des pages Streamlit
- contrôle du statut git pour confirmer les fichiers touchés

## Fichiers principaux

- `app/api/endpoints/dashboard.py`
- `app/schemas/dashboard.py`
- `app/api/router.py`
- `ui/utils/api_client.py`
