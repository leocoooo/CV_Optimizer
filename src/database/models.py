from sqlalchemy import Column, String, Text, DateTime, func
from pgvector.sqlalchemy import Vector
from src.database.database import Base
from datetime import datetime


class JobOffer(Base):  # type: ignore[misc,valid-type]
    """
    Modèle unifié pour les offres d'emploi de toutes les sources.
    Tous les champs sont NULL autorisés pour permettre les variations entre sources.
    """

    __tablename__ = "job_offers"

    # ===== IDENTIFIANTS =====
    id = Column(String(64), primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=True, index=True)
    source = Column(
        String(50), nullable=False, index=True
    )  # 'Welcome to the Jungle', 'HelloWork', 'France Travail'

    # ===== DATES =====
    date_publication = Column(DateTime)  # Date de parution de l'offre
    date_scraping = Column(
        DateTime, server_default=func.now()
    )  # Date de scraping/insertion (par le système)

    # ===== POSTE =====
    title = Column(String(255), nullable=False, index=True)
    sector = Column(String(255))  # Secteur d'activité
    contract_type = Column(String(100))  # CDI, CDD, Stage, Alternance, etc.
    remote_mode = Column(String(100))  # Télétravail total, occasionnel, etc.
    salary = Column(
        String(255)
    )  # "20K €", "Annuel de 40000 Euros", "Mensuel de 810.0 Euros à 1801.0 Euros sur 12.0 mois", etc.

    # ===== LOCALISATION =====
    city = Column(String(100), index=True)  # Ville
    department = Column(
        String(50)
    )  # Département (ex: "Hauts-de-Seine" ou "Loire-Atlantique")
    region = Column(String(100))  # Région

    # ===== ENTREPRISE =====
    company = Column(String(255), index=True)
    company_size = Column(
        String(500)
    )  # "22000 collaborateurs", "0 salarié (n'ayant pas d'effectif au 31/12...)", etc.

    # ===== PROFIL DEMANDÉ =====
    required_experience = Column(String(255))  # "< 6 mois", "5 ans", etc.
    required_education = Column(String(255))  # "Bac +5 / Master", "Bac +3", etc.
    hard_skills = Column(Text)  # Comma-separated skills list
    soft_skills = Column(Text)  # France Travail: "Esprit d'équipe, Rigueur"
    languages = Column(String(255))  # France Travail: "Anglais, Français"

    # ===== CONTENU TEXTUEL =====
    description = Column(Text, nullable=False)  # Description complète du poste
    job_profile = Column(Text)  # Profil demandé / Qualifications

    # ===== CONTENU À VECTORISER =====
    # Concaténation intelligente pour l'embedding (sans bruit)
    # Title x3 + ai_hard_skills x2 + ai_sector + ai_missions + ai_soft_skills + job_profile
    content_to_vectorize = Column(Text, nullable=True)

    # ===== VECTEUR D'EMBEDDING =====
    # 384 dimensions pour le modèle all-MiniLM-L6-v2
    embedding = Column(Vector(384))

    # ===== COLONNES HOMOGÉNÉISÉES =====
    cleaned_title = Column(String(255), nullable=True)  # Titre homogénéisé
    cleaned_contract_type = Column(
        String(100), nullable=True
    )  # Type de contrat homogénéisé
    cleaned_remote_mode = Column(
        String(100), nullable=True
    )  # Mode télétravail homogénéisé
    cleaned_required_experience = Column(
        String(50), nullable=True
    )  # Expérience requise homogénéisée
    cleaned_required_education = Column(
        String(100), nullable=True
    )  # Éducation requise homogénéisée

    # ===== COLONNES ENRICHIES PAR IA =====
    # Résultats bruts des modèles (traçabilité)
    output_ner = Column(Text, nullable=True)  # Résultats bruts NER (JSON)
    output_missions = Column(Text, nullable=True)  # Phrases classifiées "MISSIONS"

    # Résultats nettoyés et agrégés
    ai_location = Column(String(255), nullable=True)  # LOC extraits
    ai_job_title = Column(String(255), nullable=True)  # JOB extraits
    ai_company_name = Column(String(255), nullable=True)  # COMPANY extraits
    ai_sector = Column(String(255), nullable=True)  # SECTOR extraits
    ai_contract_type = Column(String(100), nullable=True)  # CONTRACT extraits
    ai_languages = Column(String(255), nullable=True)  # LANG extraits
    ai_remote_phrase = Column(Text, nullable=True)  # REMOTE extraits
    ai_experience_phrase = Column(Text, nullable=True)  # EXP extraits
    ai_education_phrase = Column(Text, nullable=True)  # EDUC extraits
    ai_hard_skills = Column(Text, nullable=True)  # Fusion SKILL + hard_skills existant
    ai_soft_skills = Column(Text, nullable=True)  # Fusion SOFT + soft_skills existant
    ai_missions = Column(
        Text, nullable=True
    )  # Phrases classifiées "MISSIONS" (nettoyées)
    ai_enrichment_date = Column(DateTime, nullable=True)  # Timestamp du traitement IA
    ai_enrichment_status = Column(
        String(50), nullable=True
    )  # "SUCCESS", "ERROR", "SKIPPED"

    # ===== PROPRIÉTÉS CALCULÉES (pour compatibilité API) =====
    @property
    def created_at(self) -> datetime | None:
        """Alias de date_scraping pour compatibilité API."""
        return self.date_scraping  # type: ignore[return-value]

    @property
    def location(self) -> str | None:
        """Construit une chaîne de localisation à partir de city, department, region."""
        parts: list[str] = [
            str(p).strip() for p in [self.city, self.department, self.region] if p
        ]
        return " - ".join(parts) if parts else None

    def __repr__(self):
        return f"<JobOffer(id={self.id}, title='{self.title}', company='{self.company}', source='{self.source}')>"
