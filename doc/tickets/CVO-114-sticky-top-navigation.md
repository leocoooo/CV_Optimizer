# CVO-114 · Barre de navigation sticky en haut

Statut: Termine

## Objectif

Installer une navigation principale fixe en haut de l'application, plus stable et plus lisible pour un usage professionnel.

## Ce qui a ete fait

- passage du routage principal sur `query_params`
- synchronisation de la vue active via `current_page`
- remplacement de la navigation haute par des liens HTML plus stables
- ajout d'un header compact sticky avec branding et contexte de vue
- ajout d'une barre de navigation sticky juste sous le header

## Resultat attendu

- la barre de navigation reste visible en haut pendant le scroll
- la vue active reste cohérente meme apres refresh
- les boutons internes continuent de naviguer vers les bonnes vues

## Fichiers principaux

- `streamlit_app.py`
- `ui/utils/navigation.py`
- `ui/components/top_nav.py`
- `ui/components/cards.py`
- `ui/utils/config.py`
