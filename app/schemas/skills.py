"""
Schémas pour la comparaison de compétences CV vs offre.
"""

from pydantic import BaseModel, Field


class SkillComparisonGroup(BaseModel):
    """Comparaison groupée pour une catégorie de compétences."""

    label: str = Field(..., description="Nom de la catégorie")
    required: list[str] = Field(
        default_factory=list, description="Compétences attendues dans l'offre"
    )
    matched: list[str] = Field(
        default_factory=list, description="Compétences visibles dans le CV"
    )
    missing: list[str] = Field(
        default_factory=list, description="Compétences attendues mais absentes du CV"
    )


class SkillComparisonResponse(BaseModel):
    """Réponse structurée de comparaison de compétences."""

    job_id: str = Field(..., description="ID de l'offre comparée")
    job_title: str = Field(..., description="Titre de l'offre")
    company: str = Field(..., description="Entreprise")
    overall_score: float = Field(
        ..., ge=0, le=100, description="Score global d'alignement"
    )
    fit_label: str = Field(..., description="Lecture synthétique du niveau d'alignement")
    summary: str = Field(..., description="Résumé humain de la comparaison")
    matched_count: int = Field(..., ge=0, description="Nombre de compétences alignées")
    missing_count: int = Field(..., ge=0, description="Nombre de compétences manquantes")
    bonus_count: int = Field(
        ..., ge=0, description="Nombre de compétences additionnelles détectées"
    )
    positive_signals: list[str] = Field(
        default_factory=list, description="Éléments qui jouent en faveur du candidat"
    )
    watchouts: list[str] = Field(
        default_factory=list, description="Éléments à renforcer ou expliciter"
    )
    groups: list[SkillComparisonGroup] = Field(
        default_factory=list, description="Détail par catégorie"
    )
    bonus_skills: list[str] = Field(
        default_factory=list, description="Compétences additionnelles présentes dans le CV"
    )
    detected_candidate_skills: list[str] = Field(
        default_factory=list,
        description="Compétences détectées dans le CV à partir du vocabulaire connu",
    )
