# CVO-108 · Refonte commerciale de l'accueil

Statut: Termine

## Objectif

Transformer l'accueil en interface plus commerciale et plus lisible:

- message produit plus clair
- suppression des formulations trop techniques
- disparition des details bruts visibles dans la vue principale
- meilleure hierarchie entre actions, indicateurs et opportunites

## Ce qui a ete fait

- refonte complete de `ui/pages/home.py` avec une structure plus produit
- simplification de la navigation et du wording dans `ui/components/sidebar.py`
- normalisation du rendu HTML dans `ui/components/cards.py` pour eviter les affichages bruts
- assainissement des libelles de statut dans `ui/utils/formatters.py`
- ajustement du theme global et des libelles de navigation dans `ui/utils/config.py`

## Decisions UX

- l'accueil parle maintenant en benefices utilisateur plutot qu'en structure technique
- les erreurs backend et base ne remontent plus sous forme brute sur les zones visibles
- les parcours principaux sont mis en avant: matching, opportunites, coach IA

## Resultat attendu

- un accueil plus vendable visuellement
- aucun HTML ou detail technique apparent dans les zones business
- une lecture plus naturelle et plus classique des contenus

## Fichiers principaux

- `ui/pages/home.py`
- `ui/components/cards.py`
- `ui/components/sidebar.py`
- `ui/utils/config.py`
- `ui/utils/formatters.py`
