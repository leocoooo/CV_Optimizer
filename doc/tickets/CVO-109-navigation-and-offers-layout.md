# CVO-109 · Correction navigation et layout des offres

Statut: Termine

## Objectif

Corriger deux points remontes en validation visuelle:

- certains boutons de navigation ne changeaient pas correctement de page
- les cartes d'offres Explorer restaient fragiles et pouvaient afficher du HTML brut

## Ce qui a ete fait

- synchronisation explicite entre `current_page` et `sidebar_page`
- mise a jour de `go_to_page()` pour piloter aussi l'etat de la sidebar
- refonte des resultats Explorer en layout natif Streamlit
- repositionnement des actions d'offre dans une colonne droite plus lisible

## Resultat attendu

- les boutons "Analyser", "Ouvrir" et les raccourcis de navigation changent bien de vue
- les offres de la page Explorer sont affichees proprement
- plus aucun HTML brut visible dans la zone resultats

## Fichiers principaux

- `ui/utils/navigation.py`
- `ui/components/sidebar.py`
- `ui/pages/jobs.py`
