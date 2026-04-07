"""
Schémas pour le chatbot LLM contextualisé CV/offre.
"""

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    """Message d'une conversation utilisateur/assistant."""

    role: str = Field(..., description="Role du message: user ou assistant")
    content: str = Field(..., description="Contenu textuel du message")


class ChatResponse(BaseModel):
    """Réponse du chatbot LLM."""

    job_id: str = Field(..., description="ID de l'offre utilisée comme contexte")
    job_title: str = Field(..., description="Titre de l'offre")
    company: str = Field(..., description="Entreprise cible")
    reply: str = Field(..., description="Réponse du chatbot")
    execution_time: float = Field(..., description="Temps de réponse en secondes")
    llm_model: str | None = Field(None, description="Modèle LLM utilisé")
