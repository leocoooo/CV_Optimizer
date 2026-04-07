# CVO-101 · Socle de la nouvelle interface CV-Optimizer

Statut: Terminé

## Objectif

Refondre le shell principal de l'application pour donner à CV-Optimizer une interface plus lisible, plus produit et plus cohérente, sans déplacer la logique métier hors du backend existant.

## Ce qui a été fait

- refonte du thème global Streamlit dans `ui/utils/config.py`
- création d'un système visuel commun dans `ui/components/cards.py`
- refonte de la sidebar dans `ui/components/sidebar.py`
- simplification du point d'entrée `streamlit_app.py`
- création d'une nouvelle page cockpit `ui/pages/home.py`

## Comment cela a été fait

- définition d'une palette plus chaleureuse et moins "dashboard technique" que l'interface précédente
- ajout de composants UI réutilisables: hero, métriques, cartes d'information, tags, timeline, cartes d'offres
- passage à une navigation orientée tâches:
  - cockpit
  - matching CV
  - explorer
  - conseils IA
  - pilotage data
  - architecture
- mise en place d'un topbar léger et d'une sidebar qui rappelle explicitement la séparation `app/` / `ui/` / `doc/`

## Résultat attendu

- l'accueil devient une vue de pilotage et non plus une simple page de titre
- toutes les pages partagent le même langage visuel
- la nouvelle interface vit entièrement dans `ui/`

## Fichiers principaux

- `streamlit_app.py`
- `ui/utils/config.py`
- `ui/components/cards.py`
- `ui/components/sidebar.py`
- `ui/pages/home.py`
