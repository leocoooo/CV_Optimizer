from sqlalchemy import Column, String, Text, DateTime, Integer, func
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
    location = Column(String(100), index=True)  # Ville/lieu principal
    location_address = Column(String(500))  # Adresse complète (optionnel)
    location_country = Column(String(10))  # Code pays (optionnel)

    # ===== ENTREPRISE =====
    company = Column(String(255), index=True)
    company_size = Column(
        String(100)
    )  # "22000 collaborateurs", "20 à 49 salariés", etc.

    # ===== PROFIL DEMANDÉ =====
    required_experience = Column(String(255))  # "< 6 mois", "5 ans", etc.
    required_education = Column(String(255))  # "Bac +5 / Master", "Bac +3", etc.
    competences = Column(Text)  # Comma-separated skills list

    # ===== RÉMUNÉRATION =====
    salary = Column(String(100))  # "20K €", "Annuel de 40000 Euros", etc.

    # ===== CONTENU TEXTUEL =====
    description = Column(Text, nullable=False)  # Description complète du poste
    job_profile = Column(Text)  # Profil demandé / Qualifications

    # ===== CHAMPS SOURCE-SPÉCIFIQUES =====
    languages = Column(String(255))  # France Travail: "Anglais, Français"
    soft_skills = Column(Text)  # France Travail: "Esprit d'équipe, Rigueur"
    nb_positions = Column(Integer)  # France Travail: nombre de postes

    # ===== CONTENU BRUT =====
    raw_json = Column(
        Text
    )  # JSON brut de l'offre pour conserver toutes les infos originales

    # ===== VECTEUR D'EMBEDDING =====
    # 384 dimensions pour le modèle all-MiniLM-L6-v2
    embedding = Column(Vector(384))

    def __repr__(self):
        return f"<JobOffer(id={self.id}, title='{self.title}', company='{self.company}', source='{self.source}')>"
