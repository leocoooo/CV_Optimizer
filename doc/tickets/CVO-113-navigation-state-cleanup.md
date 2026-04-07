# CVO-113 · Nettoyage des etats de navigation Streamlit

Statut: Termine

## Objectif

Supprimer le conflit entre les anciens widgets de navigation et les nouveaux mecanismes de routage.

## Ce qui a ete fait

- suppression des usages de `sidebar_page` et `top_nav_page`
- conservation d'une seule source de verite: `current_page`
- nettoyage des anciennes cles de session au demarrage de l'application

## Resultat attendu

- plus d'erreur `StreamlitAPIException` sur les clics de navigation
- navigation stable depuis les boutons du haut et les actions internes aux pages

## Fichiers principaux

- `streamlit_app.py`
- `ui/utils/navigation.py`
- `ui/components/top_nav.py`
- `ui/components/sidebar.py`
