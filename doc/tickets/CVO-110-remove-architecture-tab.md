# CVO-110 · Suppression de l'onglet Architecture

Statut: Termine

## Objectif

Retirer l'onglet Architecture de l'application car il n'apporte pas de valeur dans l'interface produit.

## Ce qui a ete fait

- suppression de l'entree `Architecture` dans la navigation
- suppression du routage associe dans `streamlit_app.py`
- ajout d'un fallback vers `home` si une session etait encore positionnee sur `about`

## Resultat attendu

- l'onglet n'apparait plus dans la sidebar
- l'application reste stable meme apres refresh d'une ancienne session

## Fichiers principaux

- `ui/utils/config.py`
- `ui/components/sidebar.py`
- `streamlit_app.py`
