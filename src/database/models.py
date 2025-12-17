from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector 

Base = declarative_base()

class JobOffer(Base):
    __tablename__ = 'job_offers'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False) 
    company = Column(String(255))
    location = Column(String(100))
    description = Column(Text, nullable=False)
    
    # Métadonnées pour le tracking
    source = Column(String(50)) # 'france_travail' ou 'web_scraping' 
    url = Column(String(500), unique=True) # Pour éviter les doublons
    created_at = Column(DateTime, server_default=func.now())

    # La colonne embedding : vecteur de 384 dimensions 
    # taille standard pour le modèle all-MiniLM-L6-v2
    embedding = Column(Vector(384)) 

    def __repr__(self):
        return f"<JobOffer(title='{self.title}', company='{self.company}')>"