"""
Script principal de test et validation du pipeline CV-Optimizer.
Usage:
    python main.py <cv_path> <keywords>

Exemple:
    python main.py "data/CVs/cv.pdf" "Data Scientist,Machine Learning"
"""

import sys
from loguru import logger
from src.services.cv_reader import CVReader
from src.services.matcher import JobMatcher
from src.services.llm_advisor import JobAdvisor
from src.services.france_travail_collector import run_collector
from src.services.processor import process_embeddings
from src.services.scrappe_hw import run_hw_scraper
from src.services.scrappe_wttj import run_wttj_scraper

# Configuration du logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
)


def collect_offers(keywords_list: list, mode: str = "quick"):
    """
    Collecte les offres via API France Travail et scraping.

    Args:
        keywords_list: Liste des mots-clés à rechercher
        mode: "quick" (2-3 offres par source) ou "full" (toutes les offres)
    """
    max_offers = 3 if mode == "quick" else 20

    logger.info("ÉTAPE 1 : Collecte des offres")

    # 1. API France Travail
    try:
        logger.info("Collecte via API France Travail...")
        run_collector(keywords_list)
    except Exception as e:
        logger.error(f"Erreur lors de la collecte API : {e}")

    # 2. Scraping HelloWork
    try:
        logger.info("Scraping HelloWork...")
        run_hw_scraper(
            keywords_to_fetch=keywords_list,
            max_offres_per_kw=max_offers,
            save_to_db=True,
            headless=True,
        )
    except Exception as e:
        logger.error(f"Erreur lors du scraping HelloWork : {e}")

    # 3. Scraping Welcome to the Jungle
    try:
        logger.info("Scraping Welcome to the Jungle...")
        run_wttj_scraper(
            keywords_to_fetch=keywords_list,
            max_offres_per_kw=max_offers,
            save_to_db=True,
            headless=True,
        )
    except Exception as e:
        logger.error(f"Erreur lors du scraping WTTJ : {e}")

    logger.success("Collecte terminée\n")


def generate_embeddings():
    """
    Génère les embeddings pour les nouvelles offres.
    """

    logger.info("ÉTAPE 2 : Génération des embeddings")

    try:
        process_embeddings()
        logger.success("Embeddings générés\n")
    except Exception as e:
        logger.error(f"Erreur lors de la génération des embeddings : {e}")


def match_cv_with_offers(cv_path: str, filters: dict | None = None):
    """
    Match le CV avec les offres en base et retourne les résultats.

    Args:
        cv_path: Chemin vers le fichier PDF du CV
        filters: Dictionnaire de filtres optionnels (location, contract_type, experience)

    Returns:
        tuple: (cv_text, results) ou (None, None) en cas d'erreur
    """

    logger.info("ÉTAPE 3 : Matching CV / Offres")

    # Initialisation des services
    reader = CVReader()
    matcher = JobMatcher()

    # Extraction du texte du CV
    logger.info(f"Lecture du CV : {cv_path}")
    cv_text = reader.extract_text(cv_path)

    if not cv_text:
        logger.error("Échec de l'extraction du texte du CV.")
        return None, None

    logger.success(f"CV extrait ({len(cv_text)} caractères)")

    # Application des filtres par défaut si non fournis
    if filters is None:
        filters = {}

    # Recherche des offres correspondantes
    logger.info("Recherche des meilleures correspondances...")
    results = matcher.find_matches(
        profile_text=cv_text,
        top_n=10,
        location=filters.get("location") if filters else None,
        contract_type=filters.get("contract_type") if filters else None,
        experience=filters.get("experience") if filters else None,
    )

    if not results:
        logger.warning("Aucune offre correspondante trouvée.")
        return cv_text, None

    logger.success(f"{len(results)} offres trouvées\n")
    return cv_text, results


def display_results(results):
    """
    Affiche les résultats du matching de manière formatée.
    """
    if not results:
        return

    print("TOP OFFRES CORRESPONDANTES ".center(80, "="))

    for i, res in enumerate(results, 1):
        score = round(res.similarity_score * 100, 2)
        print(f"{i}. [{score}%] {res.title}")
        print(f"Entreprise  : {res.company}")
        print(f"Localisation: {res.location}")
        print(f"Contrat     : {res.contract_type}")
        print(f"Expérience  : {res.required_experience}")
        print(f"Lien        : {res.url}")
        print(f"ID          : {res.id}")


def get_llm_advice(cv_text: str, results):
    """
    Permet à l'utilisateur de choisir une offre et d'obtenir des conseils LLM.
    """
    if not results:
        return

    advisor = JobAdvisor()

    print("CONSEILS LLM ".center(80, "="))

    choice = input("\nNuméro de l'offre pour des conseils (ou 'q' pour quitter) : ")

    if choice.lower() == "q":
        logger.info("Fin du programme.")
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            selected_offer = results[idx]

            logger.info(f"Analyse LLM pour : {selected_offer.title}...")
            advice = advisor.get_advice(cv_text, selected_offer.id)

            print(" RECOMMANDATIONS ".center(80, "="))
            print(advice)
            print("\n" + "=" * 80 + "\n")
        else:
            logger.warning("Numéro invalide.")
    except ValueError:
        logger.warning("Entrée invalide. Veuillez saisir un nombre.")
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse LLM : {e}")


def run_pipeline(
    cv_path: str, keywords: list, mode: str = "quick", skip_collection: bool = False
):
    """
    Exécute le pipeline complet de CV-Optimizer.

    Args:
        cv_path: Chemin vers le CV PDF
        keywords: Liste de mots-clés pour la recherche
        mode: "quick" (test rapide) ou "full" (collecte complète)
        skip_collection: Si True, saute la collecte et utilise les offres existantes
    """
    logger.info("\nDémarrage du pipeline CV-Optimizer\n")

    # Étape 1 & 2 : Collecte et vectorisation (optionnel)
    if not skip_collection:
        collect_offers(keywords, mode=mode)
        generate_embeddings()
    else:
        logger.info("Collecte ignorée, utilisation des offres existantes\n")

    # Étape 3 : Matching
    cv_text, results = match_cv_with_offers(cv_path)

    if cv_text is None:
        logger.error("Échec du pipeline.")
        return

    # Étape 4 : Affichage des résultats
    display_results(results)

    # Étape 5 : Conseils LLM (interactif)
    if results:
        get_llm_advice(cv_text, results)

    logger.success("\nPipeline terminé avec succès!")


if __name__ == "__main__":
    # Parsing des arguments
    if len(sys.argv) < 3:
        logger.error("Usage: python main.py <cv_path> <keywords>")
        logger.error(
            "Exemple: python main.py 'data/CVs/cv.pdf' 'Data Scientist,Machine Learning'"
        )
        sys.exit(1)

    cv_path = sys.argv[1]
    keywords_str = sys.argv[2]
    keywords_list = [kw.strip() for kw in keywords_str.split(",")]

    # Options additionnelles
    mode = sys.argv[3] if len(sys.argv) > 3 else "quick"  # "quick" ou "full"
    skip_collection = "--skip-collect" in sys.argv  # Pour tester uniquement le matching

    logger.info(f"CV: {cv_path}")
    logger.info(f"Mots-clés: {', '.join(keywords_list)}")
    logger.info(f"Mode: {mode}\n")

    # Lancement du pipeline
    run_pipeline(
        cv_path=cv_path,
        keywords=keywords_list,
        mode=mode,
        skip_collection=skip_collection,
    )
