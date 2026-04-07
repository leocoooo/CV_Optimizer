# CVO-123 · Analyse de marche et top competences techniques

Statut: Termine

## Objectif

Ajouter dans la colonne de droite de l'accueil une lecture rapide du marche centree sur les competences techniques les plus visibles dans les offres.

## Ce qui a ete fait

- extension du dashboard backend avec une aggregation des `hard_skills`
- normalisation simple des listes de competences pour compter les occurrences par offre
- ajout d'un bloc `Analyse de marche sur les offres d'emploi` dans l'accueil
- affichage des competences techniques les plus frequentes sous forme de tags avec volume

## Resultat attendu

- la page d'accueil donne une lecture plus metier du contenu de la base
- l'utilisateur voit rapidement les technologies qui ressortent le plus
- la zone de droite devient plus utile pour comprendre le marche cible

## Fichiers principaux

- `app/api/endpoints/dashboard.py`
- `app/schemas/dashboard.py`
- `ui/pages/home.py`
