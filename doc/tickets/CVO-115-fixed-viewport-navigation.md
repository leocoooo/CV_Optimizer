# CVO-115 · Navigation fixe au viewport

Statut: Termine

## Objectif

Faire en sorte que la navigation reste toujours visible en haut de l'ecran pendant le scroll, a la maniere d'un bandeau produit type reseau professionnel.

## Ce qui a ete fait

- fusion du branding compact et de la navigation dans un seul bandeau haut
- passage a une barre sticky directement sur le conteneur Streamlit de navigation
- suppression du changement d'URL pour rester dans la meme application
- conservation d'une navigation purement intra-app via `session_state`

## Resultat attendu

- les onglets restent visibles meme en descendant dans la page
- l'utilisateur reste sur la meme application sans impression d'ouverture d'une autre page
- le bandeau haut n'ajoute plus de grand blanc parasite au-dessus du contenu

## Fichiers principaux

- `streamlit_app.py`
- `ui/components/top_nav.py`
- `ui/utils/config.py`
