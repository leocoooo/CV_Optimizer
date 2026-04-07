"""
Services LLM pour conseils et chat contextualisés autour du CV.
"""

from __future__ import annotations

from typing import Any

from huggingface_hub import InferenceClient
from loguru import logger

from app.config import get_settings
from src.database.database import SessionLocal
from src.database.models import JobOffer


class JobAdvisor:
    """Couche de dialogue avec le modèle LLM."""

    def __init__(self):
        settings = get_settings()
        api_key = settings.HUGGINGFACE_API_KEY

        self.model_id = "Qwen/Qwen2.5-7B-Instruct"
        self.client = InferenceClient(model=self.model_id, token=api_key)

    def get_advice(self, cv_text: str, job_id: str) -> str:
        """Génère des conseils structurés pour un couple CV/offre."""
        db = SessionLocal()
        try:
            offer = self._get_offer(db, job_id)
            if not offer:
                return "Offre introuvable en base."

            logger.info(f"Analyse de l'offre '{offer.title}' via Hugging Face API...")

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en recrutement français. Ta mission est d'aider "
                        "un candidat à adapter son CV sans jamais inventer des compétences "
                        "ou expériences absentes du profil."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Compare mon CV avec cette offre.\n\n"
                        f"{self._build_offer_context(offer)}\n\n"
                        f"MON CV : {cv_text[:1800]}\n\n"
                        "Donne une réponse structurée :\n"
                        "1. Points forts (2-3 points).\n"
                        "2. Compétences manquantes (mots-clés ou technos).\n"
                        "3. Un conseil pour une accroche assez brève (2-3 phrases) en haut du CV "
                        "qui permet de faire fitter au maximum le CV avec l'offre, tout en respectant "
                        "les compétences réelles du candidat."
                    ),
                },
            ]

            return self._complete_chat(messages, max_tokens=800, temperature=0.7)

        except Exception as exc:
            logger.error(f"Erreur lors de l'appel Hugging Face : {exc}")
            return "Désolé, le service d'analyse est temporairement indisponible."
        finally:
            db.close()

    def chat_about_modifications(
        self,
        cv_text: str,
        job_id: str,
        user_message: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Permet de discuter avec le LLM pour modifier le CV."""
        db = SessionLocal()
        try:
            offer = self._get_offer(db, job_id)
            if not offer:
                return "Offre introuvable en base."

            logger.info(f"Chat de modification CV pour l'offre '{offer.title}'")

            system_prompt = (
                "Tu es un coach CV conversationnel et pragmatique. "
                "Tu aides le candidat a modifier son CV pour mieux repondre a une offre. "
                "Tu reponds toujours en francais. "
                "Tu n'inventes jamais une competence ou une experience qui n'apparait pas dans le CV. "
                "Quand l'utilisateur demande une modification, tu proposes si possible un texte pret a coller. "
                "Quand il manque des competences, tu distingues clairement : "
                "ce qui est deja present, ce qui doit etre mieux explicite, et ce qui manque reellement. "
                "Tu peux proposer des reformulations de titres, accroches, bullets, resumes de profil et sections competences."
            )

            messages: list[dict[str, str]] = [
                {
                    "role": "system",
                    "content": (
                        f"{system_prompt}\n\n"
                        f"CONTEXTE OFFRE:\n{self._build_offer_context(offer)}\n\n"
                        f"CONTEXTE CV:\n{cv_text[:2200]}"
                    ),
                }
            ]

            for item in (history or [])[-8:]:
                role = str(item.get("role", "")).strip().lower()
                content = str(item.get("content", "")).strip()
                if role in {"user", "assistant"} and content:
                    messages.append({"role": role, "content": content[:2000]})

            messages.append({"role": "user", "content": user_message[:2500]})

            return self._complete_chat(messages, max_tokens=900, temperature=0.6)

        except Exception as exc:
            logger.error(f"Erreur lors du chat Hugging Face : {exc}")
            return "Désolé, le coach LLM est temporairement indisponible."
        finally:
            db.close()

    def _get_offer(self, db: Any, job_id: str) -> JobOffer | None:
        """Charge une offre depuis la base."""
        return db.query(JobOffer).filter(JobOffer.id == job_id).first()

    def _build_offer_context(self, offer: JobOffer) -> str:
        """Construit un contexte compact et utile pour le LLM."""
        context_parts = [
            f"OFFRE : {offer.title}",
            f"ENTREPRISE : {offer.company}",
            f"LOCALISATION : {offer.location or 'Non precisee'}",
            f"CONTRAT : {offer.contract_type or 'Non precise'}",
            f"TELETRAVAIL : {offer.remote_mode or 'Non precise'}",
            f"COMPETENCES TECHNIQUES : {offer.hard_skills or 'Non precisees'}",
            f"SOFT SKILLS : {offer.soft_skills or 'Non precisees'}",
            f"LANGUES : {offer.languages or 'Non precisees'}",
            f"DESCRIPTION : {str(offer.description)[:1800]}",
        ]
        if offer.job_profile:
            context_parts.append(f"PROFIL DEMANDE : {str(offer.job_profile)[:1000]}")
        return "\n".join(context_parts)

    def _complete_chat(
        self, messages: list[dict[str, str]], max_tokens: int, temperature: float
    ) -> str:
        """Appel centralise au modèle de chat."""
        response = self.client.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content


if __name__ == "__main__":
    advisor = JobAdvisor()
    sample_cv = (
        "Simone HelloWorksimone@hellowork.com06XXXXXXXX2 rue de la Mabilais "
        "35000 RennesData engineerPermis BÀ PROPOSData engineer passionnée par l analyse "
        "de données. Créative, rigoureuse et autonome, je suis spécialisée dans le traitement "
        "et la modélisation des données pour des solutions informatiques innovantes."
    )
    advice = advisor.get_advice(
        sample_cv,
        "7977c3ee025ad83fc3ec878115abad521f4b58cb7a0fce70f909871693acf641",
    )
    print(advice)
