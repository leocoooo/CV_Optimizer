# CVO-120 · Onglet lettre de motivation

Statut: Termine

## Objectif

Ajouter une vue dediee a la generation de lettre de motivation a partir d'un CV et d'une offre cible, avec une sortie exploitable en LaTeX.

## Ce qui a ete fait

- ajout d'un nouvel onglet `LM` dans la navigation principale
- creation d'un endpoint backend de generation de lettre de motivation
- extension du service LLM pour produire une lettre structuree en sortie JSON
- rendu automatique d'une version LaTeX inspiree du modele fourni
- ajout d'une page Streamlit dediee avec selection d'offre, upload CV, infos candidat, apercu et export `.tex`

## Resultat attendu

- l'utilisateur peut generer une LM contextuelle sans sortir de l'application
- la lettre reste alignee avec les experiences reelles visibles dans le CV
- un fichier LaTeX reutilisable est disponible directement dans l'interface

## Fichiers principaux

- `app/api/endpoints/cover_letter.py`
- `app/schemas/cover_letter.py`
- `src/services/llm_advisor.py`
- `ui/pages/cover_letter.py`
- `ui/utils/api_client.py`
- `ui/utils/config.py`
- `streamlit_app.py`
