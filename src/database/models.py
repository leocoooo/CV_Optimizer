from sqlalchemy import Column, String, Text, DateTime, func
from pgvector.sqlalchemy import Vector
from src.database.database import Base


class JobOffer(Base):  # type: ignore[misc,valid-type]
    """
    Modèle unifié pour les offres d'emploi de toutes les sources.
    Tous les champs sont NULL autoriés pour permettre les variations entre sources.
    """

    __tablename__ = "job_offers"

    # ===== IDENTIFIANTS =====
    id = Column(String(64), primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    source = Column(
        String(50), nullable=False, index=True
    )  # 'Welcome to the Jungle', 'HelloWork', 'France Travail'

    # ===== DATES =====
    date_publication = Column(DateTime)  # Date de parution de l'offre
    date_scraping = Column(
        DateTime, server_default=func.now()
    )  # Date de scraping (par le system)

    # ===== POSTE =====
    title = Column(String(255), nullable=False, index=True)
    sector = Column(String(255))  # Secteur d'activité
    contract_type = Column(String(100))  # CDI, CDD, Stage, Alternance, etc.
    remote_mode = Column(String(100))  # Télétravail total, occasionnel, etc.

    # ===== LOCALISATION =====
    city = Column(String(100), index=True)  # Ville
    department = Column(String(50))  # Département (ex: "Île-de-France")
    region = Column(String(100))  # Région
    location_address = Column(String(500))  # Adresse complète (optionnel)

    # ===== ENTREPRISE =====
    company = Column(String(255), index=True)
    company_size = Column(
        String(500)
    )  # "22000 collaborateurs", "0 salarié (n'ayant pas d'effectif au 31/12...)", etc.

    # ===== PROFIL DEMANDÉ =====
    required_experience = Column(String(255))  # "< 6 mois", "5 ans", etc.
    required_education = Column(String(255))  # "Bac +5 / Master", "Bac +3", etc.
    competences = Column(Text)  # Comma-separated skills list

    # ===== RÉMUNÉRATION =====
    salary = Column(
        String(255)
    )  # "20K €", "Annuel de 40000 Euros", "Mensuel de 810.0 Euros à 1801.0 Euros sur 12.0 mois", etc.

    # ===== CONTENU TEXTUEL =====
    description = Column(Text, nullable=False)  # Description complète du poste
    job_profile = Column(Text)  # Profil demandé / Qualifications

    # ===== CHAMPS SOURCE-SPÉCIFIQUES =====
    languages = Column(String(255))  # France Travail: "Anglais, Français"
    soft_skills = Column(Text)  # France Travail: "Esprit d'équipe, Rigueur"

    # ===== VECTEUR D'EMBEDDING =====
    # 384 dimensions pour le modèle all-MiniLM-L6-v2
    embedding = Column(Vector(384))

    def __repr__(self):
        return f"<JobOffer(id={self.id}, title='{self.title}', company='{self.company}', source='{self.source}')>"
