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
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
)


def clean_description(html_text: str) -> str:
    """
    Supprime les balises HTML et nettoie les espaces blancs.
    """
    if not html_text:
        return ""

    # Suppression du HTML avec BeautifulSoup
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator=" ")  # On remplace les balises par un espace

    # Nettoyage des espaces multiples et des retours à la ligne
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned_text = " ".join(lines)

    # Suppression des espaces doubles résiduels
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
            new_offer = JobOffer(
                id=offer_data.get("id"),
                title=offer_data.get("intitule"),
                company=offer_data.get("entreprise", {}).get("nom", "Non spécifié"),
                location=offer_data.get("lieuTravail", {}).get("libelle"),
                description=clean_description(offer_data.get("description")),
                url=offer_data.get("origineOffre", {}).get("urlOrigine"),
                creation_date=offer_data.get("dateCreation"),
                actualisation_date=offer_data.get("dateActualisation"),
                contract_type=offer_data.get("typeContrat"),
                required_experience=offer_data.get("experienceExige"),
                contact=str(offer_data.get("contact", {})),
                source="france_travail",
            )

            db.add(new_offer)
            new_offers_count += 1

    try:
        db.commit()
        if new_offers_count > 0:
            logger.success(
                f"Insertion : {new_offers_count} nouvelles offres ajoutées en base."
            )
        else:
            logger.info("Aucune nouvelle offre à ajouter (doublons ignorés).")
    except Exception as e:
        db.rollback()
        logger.exception(f"Erreur critique lors de l'insertion en base : {e}")


def run_collector(keywords_to_fetch, max_offers=50):
    """
    Orchestrateur de la collecte de données.

    Args:
        keywords_to_fetch: Liste de mots-clés
        max_offers: Nombre maximum d'offres par mot-clé (défaut: 50)
    """

    if not keywords_to_fetch:
        logger.error(
            "La liste des mots-clés est vide. Veuillez fournir des mots-clés pour la recherche API."
        )
        return

    api = FranceTravailAPI()
    db = SessionLocal()

    logger.info("Démarrage du cycle de collecte CV-Optimizer")
    logger.info(f"Max {max_offers} offres par mot-clé")

    try:
        for kw in keywords_to_fetch:
            logger.info(f"Recherche en cours pour : {kw}")

            # Récupération des offres via le service API avec limite dynamique
            range_end = max_offers - 1
            offers = api.fetch_offers(keywords=kw, range_str=f"0-{range_end}")

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
    keywords_to_fetch = ["Data Scientist"]
    run_collector(keywords_to_fetch)
