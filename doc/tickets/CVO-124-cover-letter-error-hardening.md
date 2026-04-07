# CVO-124 · Robustesse generation LM et erreurs backend

Statut: Termine

## Objectif

Eviter les erreurs 500 opaques lors de la generation de lettre de motivation et rendre la compilation PDF plus robuste.

## Ce qui a ete fait

- ajout d'un handler global pour les exceptions metier API
- propagation d'un message backend plus lisible vers l'interface Streamlit
- nettoyage des caracteres typographiques sensibles avant rendu LaTeX
- passage a un template LaTeX compatible PDFTeX et moteurs Unicode
- fallback de compilation sur `lualatex`, `xelatex`, puis `pdflatex`

## Resultat attendu

- les erreurs de generation remontent avec un message comprehensible
- la compilation PDF supporte mieux les contenus reels du CV et de la lettre
- l'onglet lettre devient plus stable en usage reel

## Fichiers principaux

- `app/main.py`
- `src/services/llm_advisor.py`
- `ui/utils/api_client.py`
