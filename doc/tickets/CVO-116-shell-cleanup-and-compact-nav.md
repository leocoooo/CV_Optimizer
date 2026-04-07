# CVO-116 · Nettoyage du shell et navigation compacte

Statut: Termine

## Objectif

Corriger les problemes visibles sur le shell principal: barre haute trop volumineuse, labels d'onglets qui cassent, et alertes systeme trop envahissantes.

## Ce qui a ete fait

- simplification de la barre haute en supprimant le bloc descriptif a droite
- raccourcissement des labels de navigation pour eviter les retours a la ligne
- conservation d'une navigation intra-app basee sur `session_state`
- resserrement du CSS sticky pour garder un bandeau plus discret pendant le scroll
- transformation de l'alerte API indisponible en simple banniere compacte
- leger nettoyage du texte dans le panneau lateral

## Resultat attendu

- les onglets restent lisibles et alignes sur une seule ligne
- la navigation fixe prend moins de hauteur et ressemble davantage a un produit professionnel
- l'etat hors ligne reste visible sans dupliquer de gros blocs de message dans le contenu

## Fichiers principaux

- `streamlit_app.py`
- `ui/components/top_nav.py`
- `ui/components/api_status.py`
- `ui/components/sidebar.py`
- `ui/utils/config.py`
