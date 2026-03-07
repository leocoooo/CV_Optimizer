from loguru import logger
from src.database.database import SessionLocal
from src.services.france_travail_api import FranceTravailAPI, convert_ft_offer
from src.services.scraping_utils import (
    setup_logger,
    save_offers_to_db,
    get_existing_ids,
)

# Configuration de Loguru (on réutilise le setup_logger standard)
setup_logger(level="INFO")


def run_collector(keywords_to_fetch, max_offers=50):
    """
    Orchestrateur de la collecte de données France Travail.

    Utilise la nouvelle architecture harmonisée:
    - Récupère les offres brutes de l'API France Travail
    - Convertit chaque offre au format unifié avec convert_ft_offer()
    - Persiste en base avec la fonction save_offers_to_db() standard

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

    total_raw_offers = 0
    total_inserted = 0

    # Récupérer tous les IDs existants une seule fois
    existing_ids = get_existing_ids(db)

    try:
        for kw in keywords_to_fetch:
            logger.info(f"Recherche en cours pour : {kw}")

            count_for_kw = 0  # Nombre d'offres NON-doublon pour ce mot-clé
            offset = 0  # Offset pour pagination API
            batch_size = max_offers  # Nombre d'offres à récupérer par appel

            # Boucle jusqu'à avoir assez d'offres non-doublons
            while count_for_kw < max_offers:
                # Récupération des offres brutes via le service API
                range_str = f"{offset}-{offset + batch_size - 1}"
                raw_offers = api.fetch_offers(keywords=kw, range_str=range_str)

                if not raw_offers:
                    logger.warning(
                        f"Fin des résultats API pour : {kw} à offset {offset}"
                    )
                    break

                logger.debug(
                    f"API batch: {len(raw_offers)} offres trouvées (offset {offset})"
                )

                # Conversion et filtrage des doublons
                for raw_offer in raw_offers:
                    if count_for_kw >= max_offers:
                        break

                    converted_offer = convert_ft_offer(raw_offer)
                    offer_id = converted_offer.get("id")

                    # Vérifier si c'est un doublon
                    if offer_id in existing_ids:
                        logger.debug(f"Offre {offer_id} déjà en base, ignorée")
                        continue

                    # Nouvelle offre trouvée - insérer
                    count_inserted_this = save_offers_to_db(
                        db, [converted_offer], source_name="France Travail"
                    )

                    if count_inserted_this > 0:
                        count_for_kw += 1
                        total_inserted += count_inserted_this
                        existing_ids.add(
                            offer_id
                        )  # Ajouter à la liste pour éviter doublon dans le même batch
                        logger.info(f"[{count_for_kw}/{max_offers}] Offre ajoutée")

                # Si on n'a pas assez d'offres, continuer à la prochaine batch
                if count_for_kw < max_offers:
                    offset += batch_size

            total_raw_offers += count_for_kw
            if count_for_kw == 0:
                logger.info(f"Aucune nouvelle offre pour : {kw}")
            else:
                logger.info(f"Complété pour {kw}: {count_for_kw} nouvelles offres")

    except Exception as e:
        logger.critical(f"Échec du processus de collecte : {e}")
    finally:
        db.close()

        # Afficher un résumé final
        logger.info(f"Cycle complété - {total_inserted} offres ajoutées en base")


if __name__ == "__main__":
    keywords_to_fetch = ["Data Scientist"]
    run_collector(keywords_to_fetch, 3)
