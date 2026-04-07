"""
Services LLM pour conseils et chat contextualisés autour du CV.
"""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
import tempfile
import unicodedata
from textwrap import dedent
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

    def generate_cover_letter(
        self,
        cv_text: str,
        job_id: str,
        applicant_profile: dict[str, str] | None = None,
        language: str = "english",
        focus_note: str | None = None,
    ) -> dict[str, Any]:
        """Génère une lettre de motivation structurée et sa version LaTeX."""
        db = SessionLocal()
        applicant_profile = applicant_profile or {}
        language = self._normalize_letter_language(language)

        try:
            offer = self._get_offer(db, job_id)
            if not offer:
                raise ValueError("Offre introuvable en base.")

            logger.info(f"Génération LM pour l'offre '{offer.title}'")

            language_label = "anglais" if language == "english" else "français"
            focus_block = (
                f"\nPOINT A METTRE EN AVANT PRIORITAIRE : {focus_note.strip()}\n"
                if focus_note and focus_note.strip()
                else ""
            )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en rédaction de lettres de motivation pour des candidatures sélectives. "
                        "Tu n'inventes jamais d'expérience, de compétence ou de résultat absent du CV. "
                        "Tu rédiges une lettre convaincante, précise et crédible.\n\n"
                        "Réponds STRICTEMENT sous forme de JSON valide sans markdown ni commentaire.\n"
                        "Le JSON doit contenir exactement les clés suivantes :\n"
                        "subject, greeting, introduction, academic_background, academic_projects, "
                        "professional_experience, extra_background, motivation, closing.\n"
                        "Chaque valeur doit être une chaîne de caractères.\n"
                        "La lettre doit être rédigée en "
                        f"{language_label}.\n"
                        "Le ton doit rester professionnel, fluide et personnalisé à l'offre."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Rédige une lettre de motivation structurée en suivant cette logique :\n"
                        "1. introduction ciblée\n"
                        "2. parcours académique pertinent\n"
                        "3. projets académiques ou quantitatifs utiles\n"
                        "4. expérience professionnelle\n"
                        "5. éléments complémentaires de profil\n"
                        "6. motivation explicite pour le poste et l'entreprise\n\n"
                        f"{self._build_offer_context(offer)}\n\n"
                        f"PROFIL CANDIDAT : {self._build_applicant_context(applicant_profile)}\n"
                        f"{focus_block}\n"
                        f"CV CANDIDAT : {cv_text[:5000]}"
                    ),
                },
            ]

            raw_response = self._complete_chat(messages, max_tokens=1400, temperature=0.55)
            payload = self._normalize_cover_letter_payload(
                raw_response=raw_response,
                offer=offer,
                applicant_profile=applicant_profile,
                language=language,
            )
            payload["latex_source"] = self.build_cover_letter_latex(
                payload=payload,
                applicant_profile=applicant_profile,
            )
            payload["pdf_base64"] = base64.b64encode(
                self.compile_latex_to_pdf(payload["latex_source"])
            ).decode("ascii")
            return payload

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

    def _build_applicant_context(self, applicant_profile: dict[str, str]) -> str:
        """Construit le contexte candidat hors CV pour la lettre."""
        profile_parts = [
            f"NOM : {applicant_profile.get('full_name') or 'Non precise'}",
            f"VILLE : {applicant_profile.get('city') or 'Non precisee'}",
            f"EMAIL : {applicant_profile.get('email') or 'Non precise'}",
            f"TELEPHONE : {applicant_profile.get('phone') or 'Non precise'}",
        ]
        return "\n".join(profile_parts)

    def _normalize_letter_language(self, language: str | None) -> str:
        """Normalise la langue de génération de la LM."""
        if str(language).strip().lower() in {"fr", "francais", "français", "french"}:
            return "french"
        return "english"

    def _extract_json_payload(self, raw_response: str) -> dict[str, Any]:
        """Extrait un objet JSON d'une réponse LLM, même avec du bruit autour."""
        candidates: list[str] = []
        cleaned = str(raw_response or "").strip()
        if cleaned:
            candidates.append(cleaned)
            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()
                candidates.append(cleaned)

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidates.append(cleaned[start : end + 1])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return {}

    def _normalize_cover_letter_payload(
        self,
        raw_response: str,
        offer: JobOffer,
        applicant_profile: dict[str, str],
        language: str,
    ) -> dict[str, Any]:
        """Normalise la sortie LLM en structure stable pour l'UI et LaTeX."""
        parsed = self._extract_json_payload(raw_response)

        subject = str(parsed.get("subject") or "").strip()
        greeting = str(parsed.get("greeting") or "").strip()
        closing = str(parsed.get("closing") or "").strip()
        signature = str(
            applicant_profile.get("full_name")
            or parsed.get("signature_name")
            or "Nom Prénom"
        ).strip()

        ordered_fields = [
            "introduction",
            "academic_background",
            "academic_projects",
            "professional_experience",
            "extra_background",
            "motivation",
        ]

        paragraphs = [
            str(parsed.get(field, "")).strip()
            for field in ordered_fields
            if str(parsed.get(field, "")).strip()
        ]

        if not subject:
            if language == "french":
                subject = (
                    f"Candidature au poste de {offer.title} - {offer.company}"
                )
            else:
                subject = (
                    f"Application for the {offer.title} position - {offer.company}"
                )

        if not greeting:
            greeting = "Madame, Monsieur," if language == "french" else "Dear Hiring Manager,"

        if not closing:
            closing = (
                "Je reste à votre disposition pour tout échange complémentaire et vous remercie pour votre attention."
                if language == "french"
                else "I remain at your disposal for any further information and look forward to hearing from you."
            )

        if not paragraphs:
            fallback_body = str(raw_response or "").strip()
            if fallback_body:
                paragraphs = [fallback_body]
            else:
                paragraphs = [
                    "Profil à préciser: aucune restitution exploitable n'a été générée."
                    if language == "french"
                    else "Profile to be refined: no usable cover letter draft was generated."
                ]

        return {
            "language": language,
            "subject": subject,
            "greeting": greeting,
            "paragraphs": paragraphs[:6],
            "closing": closing,
            "signature": signature,
        }

    def _latex_escape(self, value: str) -> str:
        """Échappe les caractères spéciaux pour un rendu LaTeX stable."""
        normalized = unicodedata.normalize("NFKC", str(value or ""))
        unicode_replacements = {
            "\u00a0": " ",
            "\u2007": " ",
            "\u2009": " ",
            "\u202f": " ",
            "\u2060": "",
            "\ufeff": "",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2013": "--",
            "\u2014": "---",
            "\u2212": "-",
            "\u2022": "-",
            "\u25cf": "-",
            "\u2026": "...",
            "\u20ac": "EUR",
            "\u2122": "TM",
            "\u00ae": "(R)",
        }
        for source, target in unicode_replacements.items():
            normalized = normalized.replace(source, target)

        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        escaped = normalized
        for source, target in replacements.items():
            escaped = escaped.replace(source, target)
        return escaped

    def build_cover_letter_latex(
        self,
        payload: dict[str, Any],
        applicant_profile: dict[str, str] | None = None,
    ) -> str:
        """Construit une version LaTeX à partir de la lettre générée."""
        applicant_profile = applicant_profile or {}
        full_name = applicant_profile.get("full_name") or payload.get("signature") or "Nom Prénom"
        city = applicant_profile.get("city") or ""
        email = applicant_profile.get("email") or ""
        phone = applicant_profile.get("phone") or ""

        contact_lines = [self._latex_escape(full_name)]
        if city:
            contact_lines.append(self._latex_escape(city))
        if email:
            escaped_email = self._latex_escape(email)
            contact_lines.append(
                f"\\href{{mailto:{escaped_email}}}{{{escaped_email}}}"
            )
        if phone:
            contact_lines.append(self._latex_escape(phone))

        subject_label = "Objet :" if payload.get("language") == "french" else "Subject:"
        babel_language = "french" if payload.get("language") == "french" else "english"
        paragraph_blocks = []
        for paragraph in payload.get("paragraphs", []):
            paragraph_blocks.append(self._latex_escape(paragraph))

        body = "\n\n\\vspace{0.2cm}\n\n".join(paragraph_blocks)

        return dedent(
            f"""
            \\documentclass[10pt,a4paper]{{article}}
            \\usepackage{{iftex}}
            \\ifPDFTeX
            \\usepackage[utf8]{{inputenc}}
            \\usepackage[T1]{{fontenc}}
            \\else
            \\usepackage{{fontspec}}
            \\fi
            \\usepackage[provide=*,{babel_language}]{{babel}}
            \\usepackage{{geometry}}
            \\usepackage{{parskip}}
            \\usepackage{{hyperref}}
            \\usepackage[normalem]{{ulem}}

            \\geometry{{
                top=1.3cm,
                bottom=1.3cm,
                left=1.6cm,
                right=1.6cm
            }}
            \\setlength{{\\parskip}}{{6pt}}
            \\pagestyle{{empty}}

            \\begin{{document}}

            \\noindent
            \\begin{{minipage}}[t]{{0.49\\textwidth}}
            {" \\\\\n".join(contact_lines)}
            \\end{{minipage}}
            \\hfill
            \\begin{{minipage}}[t]{{0.48\\textwidth}}
            \\raggedleft



            \\end{{minipage}}

            \\setlength{{\\parindent}}{{15pt}}

            \\vspace{{0.1cm}}
            \\begin{{flushright}}

            \\end{{flushright}}
            \\vspace{{0.3cm}}
            \\noindent\\textbf{{\\uline{{{subject_label} {self._latex_escape(payload.get("subject", ""))}}}}}

            \\vspace{{0.2cm}}

            {self._latex_escape(payload.get("greeting", ""))}
            \\vspace{{0.2cm}}

            {body}

            \\vspace{{0.2cm}}
            {self._latex_escape(payload.get("closing", ""))}

            \\vspace{{0.6cm}}
            \\begin{{flushright}}
            {self._latex_escape(payload.get("signature", full_name))}
            \\end{{flushright}}

            \\end{{document}}
            """
        ).strip()

    def compile_latex_to_pdf(self, latex_source: str) -> bytes:
        """Compile une source LaTeX en PDF via pdflatex."""
        engine_candidates = [
            engine
            for engine in ("lualatex", "xelatex", "pdflatex")
            if shutil.which(engine)
        ]
        if not engine_candidates:
            raise RuntimeError("Aucun moteur LaTeX n'est disponible sur cette machine.")

        with tempfile.TemporaryDirectory(prefix="cover_letter_pdf_") as tmp_dir:
            tex_path = f"{tmp_dir}/cover_letter.tex"
            with open(tex_path, "w", encoding="utf-8") as tex_file:
                tex_file.write(latex_source)

            engine_errors: list[str] = []
            for engine in engine_candidates:
                command = [
                    shutil.which(engine) or engine,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "cover_letter.tex",
                ]

                completed = subprocess.run(
                    command,
                    cwd=tmp_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode == 0:
                    pdf_path = f"{tmp_dir}/cover_letter.pdf"
                    with open(pdf_path, "rb") as pdf_file:
                        return pdf_file.read()

                engine_errors.append(
                    f"{engine}: {(completed.stderr or completed.stdout)[-600:]}"
                )

            raise RuntimeError(
                "Compilation LaTeX impossible. "
                + " | ".join(engine_errors)
            )

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
