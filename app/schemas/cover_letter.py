"""
Schémas pour la génération de lettre de motivation.
"""

from typing import Optional

from pydantic import BaseModel, Field


class CoverLetterRequest(BaseModel):
    """Requête de génération d'une lettre de motivation."""

    job_id: str = Field(..., description="Identifiant de l'offre ciblée")
    applicant_name: str = Field(..., description="Nom complet du candidat")
    city: str = Field("", description="Ville du candidat")
    email: str = Field("", description="Email du candidat")
    phone: str = Field("", description="Téléphone du candidat")
    letter_language: str = Field(
        "english", description="Langue de la lettre: english ou french"
    )
    focus_note: Optional[str] = Field(
        None, description="Point à mettre en avant dans la lettre"
    )


class CoverLetterResponse(BaseModel):
    """Réponse contenant la lettre de motivation générée."""

    job_id: str = Field(..., description="ID de l'offre analysée")
    job_title: str = Field(..., description="Titre du poste")
    company: str = Field(..., description="Entreprise cible")
    language: str = Field(..., description="Langue utilisée")
    subject: str = Field(..., description="Objet de la lettre")
    greeting: str = Field(..., description="Formule d'appel")
    paragraphs: list[str] = Field(
        ..., description="Paragraphes principaux de la lettre"
    )
    closing: str = Field(..., description="Formule de conclusion")
    signature: str = Field(..., description="Nom affiché en signature")
    latex_source: str = Field(..., description="Version LaTeX prête à exporter")
    pdf_base64: str = Field(..., description="Version PDF encodée en base64")
    cv_length: int = Field(..., description="Nombre de caractères du CV analysé")
    execution_time: float = Field(..., description="Temps d'exécution en secondes")
    llm_model: Optional[str] = Field(None, description="Modèle LLM utilisé")
