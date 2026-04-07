# CVO-107 · Correction de mise en page accueil et cartes

Statut: Terminé

## Objectif

Corriger les problèmes de rendu visibles sur l'interface:

- HTML brut affiché dans certaines zones
- timeline cassée
- cartes d'offres avec layout instable
- textes empilés verticalement ou mal placés

## Ce qui a été fait

- ajout d'un helper de rendu HTML déindenté dans `ui/components/cards.py`
- correction du rendu de la timeline
- correction du rendu des job cards
- ajout de classes CSS dédiées pour stabiliser l'alignement

## Cause du bug

Plusieurs composants injectaient du HTML avec de l'indentation dans `st.markdown`. Selon le parsing Streamlit/Markdown, ce HTML pouvait être traité comme du texte brut ou comme un bloc de code, d'où l'affichage cassé.

## Résultat attendu

- timeline lisible et propre
- cartes d'offres normales
- disparition du HTML visible à l'écran
- meilleure stabilité du layout général

## Fichiers principaux

- `ui/components/cards.py`
- `ui/utils/config.py`
