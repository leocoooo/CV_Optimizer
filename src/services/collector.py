import sys
from loguru import logger
from sqlalchemy.orm import Session
from src.database.database import SessionLocal
from src.database.models import JobOffer
from src.services.france_travail_api import FranceTravailAPI
from bs4 import BeautifulSoup

# Configuration optionnelle de Loguru
# On définit un format clair et on s'assure que les logs s'affichent dans la console
logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="INFO")

def clean_description(html_text: str) -> str:
    """
    Supprime les balises HTML et nettoie les espaces blancs.
    """
    if not html_text:
        return ""
    
    # 1. Suppression du HTML avec BeautifulSoup
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator=" ") # On remplace les balises par un espace
    
    # 2. Nettoyage des espaces multiples et des retours à la ligne
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned_text = " ".join(lines)
    
    # 3. Suppression des espaces doubles résiduels
    return " ".join(cleaned_text.split())

def save_offers_to_db(db: Session, offers_json: list):
    """
    Transforme les données JSON en objets JobOffer et les persiste en base.
    Vérifie l'existence de l'ID pour éviter les doublons.
    """
    new_offers_count = 0
    
    for offer_data in offers_json:
        # Vérification de l'ID unique France Travail
        offer_id = offer_data.get("id")
        existing_offer = db.query(JobOffer).filter(JobOffer.id == offer_id).first()
        
        if not existing_offer:
            # new_offer = JobOffer(
            #     id=offer_id,
            #     title=offer_data.get("intitule"),
            #     description=clean_description(offer_data.get("description")),
            #     company=offer_data.get("entreprise", {}).get("nom", "Non spécifiée"),
            #     location=offer_data.get("lieuTravail", {}).get("libelle", "Non spécifiée"),
            #     embedding=None 
            # )

            new_offer = JobOffer(
                id=offer_data.get("id"),
                title=offer_data.get("intitule"),
                company=offer_data.get("entreprise", {}).get("nom", "Non spécifié"),
                location=offer_data.get("lieuTravail", {}).get("libelle"),
                description=clean_description(offer_data.get("description")),
                url=offer_data.get("origineOffre", {}).get("urlOrigine"),
                date_creation=offer_data.get("dateCreation"),
                date_actualisation=offer_data.get("dateActualisation"),
                type_contrat=offer_data.get("typeContrat"),
                experience_exigee=offer_data.get("experienceExige"),
                contact=str(offer_data.get("contact", {})), 
                source="france_travail"
            )

            db.add(new_offer)
            new_offers_count += 1
            
    try:
        db.commit()
        if new_offers_count > 0:
            logger.success(f"Insertion : {new_offers_count} nouvelles offres ajoutées en base.")
        else:
            logger.info("Aucune nouvelle offre à ajouter (doublons ignorés).")
    except Exception as e:
        db.rollback()
        logger.exception(f"Erreur critique lors de l'insertion en base : {e}")

def run_collector():
    """
    Orchestrateur de la collecte de données.
    """
    api = FranceTravailAPI()
    db = SessionLocal()
    
    keywords_to_fetch = [
        "Data Scientist", "Data Analyst", "Data Engineer", 
        "Machine Learning Engineer", "Architecte Big Data", 
        "Business Intelligence", "Data Manager", "Développeur Python", 
        "Développeur Fullstack", "Développeur Backend", "Développeur Frontend", 
        "Software Engineer", "DevOps", "Cloud Engineer", 
        "Architecte Cloud", "Site Reliability Engineer", 
        "Spark", "Kubernetes", "AWS", "Azure", "SQL", "GCP", "NoSQL"
    ]

    logger.info("Démarrage du cycle de collecte CV-Optimizer")

    try:
        for kw in keywords_to_fetch:
            logger.info(f"Recherche en cours pour : {kw}")
            
            # Récupération des offres via le service API
            offers = api.fetch_offers(keywords=kw, range_str="0-49")
            
            if offers:
                save_offers_to_db(db, offers)
            else:
                logger.warning(f"L'API n'a retourné aucun résultat pour : {kw}")
                
    except Exception as e:
        logger.critical(f"Échec du processus de collecte : {e}")
    finally:
        db.close()
        logger.info("Session de base de données fermée. Fin du programme.")

if __name__ == "__main__":
    run_collector()