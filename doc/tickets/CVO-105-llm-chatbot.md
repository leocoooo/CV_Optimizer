# CVO-105 · Chatbot LLM de modification du CV

Statut: Terminé

## Objectif

Permettre à l'utilisateur de discuter directement avec le LLM pour demander des modifications précises sur son CV, en gardant le contexte:

- de l'offre ciblée
- du CV uploadé
- de l'historique récent de la conversation

## Ce qui a été fait

- ajout des schémas `app/schemas/chat.py`
- ajout de l'endpoint `POST /api/chat`
- extension du service `src/services/llm_advisor.py`
- ajout du client `chat_with_llm()` dans `ui/utils/api_client.py`
- intégration d'un vrai module chat dans `ui/pages/advice.py`

## Comment cela a été fait

### Backend

Le backend:

- reçoit un CV PDF
- extrait le texte
- charge l'offre ciblée
- reconstruit un historique court user/assistant
- interroge le LLM avec un prompt de coach CV

Le prompt impose plusieurs règles:

- répondre en français
- ne pas inventer de compétences ni d'expériences
- proposer du texte prêt à coller quand l'utilisateur demande une modification
- distinguer ce qui est présent, ce qui doit être mieux formulé et ce qui manque réellement

### UI

La page de conseils IA propose maintenant:

- trois prompts rapides
- un historique de discussion
- une saisie libre avec `chat_input`
- un envoi contextualisé avec le CV et l'offre sélectionnée

## Intentions produit

Ce chat sert à passer de l'analyse à l'action. L'utilisateur peut par exemple demander:

- une nouvelle accroche
- une reformulation de bullets
- une meilleure mise en avant des compétences
- une version plus orientée pour une offre donnée

## Fichiers principaux

- `app/schemas/chat.py`
- `app/api/endpoints/chat.py`
- `src/services/llm_advisor.py`
- `ui/utils/api_client.py`
- `ui/pages/advice.py`
