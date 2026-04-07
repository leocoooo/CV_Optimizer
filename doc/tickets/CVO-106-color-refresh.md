# CVO-106 · Palette plus conviviale

Statut: Terminé

## Objectif

Rendre l'interface plus chaleureuse et plus conviviale, dans un esprit proche de l'autre projet:

- fond crème lumineux
- orange doux pour les actions
- vert sauge pour les états calmes et les cartes de soutien

## Ce qui a été fait

- refonte de la palette CSS globale dans `ui/utils/config.py`
- éclaircissement de la sidebar
- refonte du hero principal
- mise à jour des boutons, onglets, badges et cartes
- harmonisation de la sidebar dans `ui/components/sidebar.py`

## Comment cela a été fait

Les couleurs trop sombres ou trop "dashboard technique" ont été remplacées par:

- une base crème plus lumineuse
- un accent orange plus accueillant
- un vert sauge plus doux
- des ombres plus chaudes et plus légères

## Résultat attendu

- une interface plus accueillante dès l'ouverture
- une sensation plus produit, moins outil interne
- une cohérence visuelle plus proche du brief chaleureux demandé

## Fichiers principaux

- `ui/utils/config.py`
- `ui/components/sidebar.py`
