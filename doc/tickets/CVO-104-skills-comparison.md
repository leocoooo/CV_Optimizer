# CVO-104 · Comparaison des compétences offre vs candidat

Statut: Terminé

## Objectif

Ajouter une lecture claire des compétences demandées par l'offre vs celles qui sont visibles dans le CV du candidat, avec une restitution simple:

- ce qui est bien
- ce qui manque
- ce qui peut aider

## Ce qui a été fait

- ajout du schéma `app/schemas/skills.py`
- ajout du service `src/services/skill_gap_analyzer.py`
- ajout de l'endpoint `POST /api/skills/compare`
- branchement de la route dans `app/api/router.py`
- ajout du client UI `compare_skills()` dans `ui/utils/api_client.py`
- intégration de la restitution dans `ui/pages/advice.py`

## Comment cela a été fait

### Backend

Un analyseur heuristique compare:

- les compétences techniques
- les soft skills
- les langues

Sources utilisées:

- champs structurés de l'offre quand ils existent (`hard_skills`, `soft_skills`, `languages`)
- fallback sur la description de l'offre avec un vocabulaire connu
- détection des occurrences dans le texte nettoyé du CV

### Restitution UI

La page de conseils IA affiche désormais:

- un score d'alignement
- un label de lecture rapide
- les signaux positifs
- les points à renforcer
- un détail par catégorie
- les compétences bonus détectées dans le CV

## Intention produit

L'idée n'est pas de dire qu'une compétence est réellement absente du candidat, mais de vérifier si elle est explicitement visible dans le CV. Cela aide à comprendre ce qui est déjà convaincant et ce qui devrait être mieux formulé.

## Fichiers principaux

- `app/schemas/skills.py`
- `app/api/endpoints/skills.py`
- `src/services/skill_gap_analyzer.py`
- `ui/utils/api_client.py`
- `ui/pages/advice.py`
