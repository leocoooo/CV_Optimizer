# CVO-111 · Barre d'onglets en haut

Statut: Termine

## Objectif

Ajouter une navigation principale visible en haut de l'application, en plus de la sidebar.

## Ce qui a ete fait

- ajout d'un composant `ui/components/top_nav.py`
- integration de la barre d'onglets dans `streamlit_app.py`
- synchronisation des etats `current_page`, `sidebar_page` et `top_nav_page`
- ajout d'un style dedie dans `ui/utils/config.py`

## Resultat attendu

- les vues principales sont accessibles dans une barre d'onglets en haut
- la navigation reste coherente entre sidebar, boutons d'action et onglets

## Fichiers principaux

- `ui/components/top_nav.py`
- `ui/utils/navigation.py`
- `streamlit_app.py`
- `ui/utils/config.py`
