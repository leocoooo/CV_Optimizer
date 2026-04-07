# CVO-102 · Parcours candidat et parcours opérateur

Statut: Terminé

## Objectif

Transformer les vues existantes en vrais parcours d'usage pour CV-Optimizer:

- matching CV
- exploration des offres
- conseils IA
- pilotage data

## Ce qui a été fait

- refonte complète de `ui/pages/matching.py`
- refonte complète de `ui/pages/jobs.py`
- refonte complète de `ui/pages/advice.py`
- refonte complète de `ui/pages/admin.py`
- mise à jour de `ui/pages/about.py` pour expliquer l'architecture

## Comment cela a été fait

### Matching

- conservation du workflow backend existant
- amélioration de l'entrée utilisateur avec une zone d'upload plus claire
- restitution des résultats sous forme de shortlist hiérarchisée
- ajout d'un pont direct vers la page de conseils IA avec présélection du job

### Explorer

- ajout d'un formulaire de filtres plus structuré
- affichage de métriques de recherche en haut de page
- cartes de résultats plus lisibles
- possibilité d'envoyer une offre directement vers la page de conseils IA

### Conseils IA

- suppression de la dépendance exclusive à une saisie manuelle d'ID
- ajout d'une recherche d'offres cible depuis l'interface
- chargement d'un job présélectionné depuis le matching ou l'exploration
- conservation d'une saisie manuelle d'ID comme fallback

### Pilotage Data

- regroupement des actions de collecte et de réindexation dans une seule vue opérateur
- lecture plus claire des prévisions de volume avant collecte
- mise en valeur des statistiques de base après chargement

## Résultat attendu

- l'utilisateur peut enchaîner les tâches sans perdre de contexte
- le produit paraît plus structuré et moins fragmenté
- les pages racontent davantage ce qu'elles font et pourquoi

## Fichiers principaux

- `ui/pages/matching.py`
- `ui/pages/jobs.py`
- `ui/pages/advice.py`
- `ui/pages/admin.py`
- `ui/pages/about.py`
