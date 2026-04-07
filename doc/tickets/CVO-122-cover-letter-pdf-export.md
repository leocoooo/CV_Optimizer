# CVO-122 · Export PDF de la lettre de motivation

Statut: Termine

## Objectif

Permettre a l'utilisateur de telecharger directement la lettre de motivation au format PDF depuis l'interface.

## Ce qui a ete fait

- compilation du LaTeX en PDF via `pdflatex`
- ajout du PDF encode en base64 dans la reponse backend de generation de lettre
- ajout d'un bouton de telechargement PDF dans la page `Lettre de Motivation`
- conservation du bouton de telechargement `.tex` pour les ajustements manuels

## Resultat attendu

- l'utilisateur peut repartir avec un PDF directement exploitable
- la structure de la lettre reste celle du modele LaTeX fourni
- l'interface propose a la fois un export immediat PDF et un export source `.tex`

## Fichiers principaux

- `src/services/llm_advisor.py`
- `app/schemas/cover_letter.py`
- `app/api/endpoints/cover_letter.py`
- `ui/pages/cover_letter.py`
