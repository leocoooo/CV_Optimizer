import time
import json
import re
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from src.database.database import SessionLocal
from src.services.scraping_utils import (
    setup_logger,
    get_existing_ids,
    clean_description,
    save_offers_to_db,
)

# Configuration du logger
setup_logger(level="DEBUG")


def scrape_hellowork(keywords, max_offres_per_kw=10, db_session=None, headless=None):
    """
    Scrape les offres HelloWork pour les mots-clés donnés.

    Args:
        keywords: Liste des mots-clés à rechercher
        max_offres_per_kw: Nombre max d'offres par mot-clé
        db_session: Session SQLAlchemy pour vérifier les doublons
        headless: Si True, le navigateur est invisible

    Returns:
        Liste des offres scrapées (dictionnaires)
    """
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(service=service, options=options)

    # Récupération des IDs déjà scrapés (en base + run actuel)
    existing_ids = get_existing_ids(db_session) if db_session else set()
    all_data = []

    try:
        driver.get("https://www.hellowork.com/fr-fr/")
        time.sleep(1)

        # Accepter les cookies
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Tout accepter']"))
            ).click()
            time.sleep(1)
        except TimeoutException:
            pass

        for kw in keywords:
            logger.info(f"Recherche HelloWork : {kw}")
            count_for_kw = 0
            page = 1

            # Recherche du mot-clé
            try:
                search_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "k"))
                )
                search_input.clear()
                search_input.send_keys(kw)
                time.sleep(0.5)
                search_input.send_keys(Keys.ENTER)
                time.sleep(2)
            except TimeoutException:
                logger.warning(f"Impossible de lancer la recherche pour : {kw}")
                continue

            # Pagination
            while count_for_kw < max_offres_per_kw:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "a[data-cy='offerTitle']")
                        )
                    )
                    offer_elements = driver.find_elements(
                        By.CSS_SELECTOR, "a[data-cy='offerTitle']"
                    )
                    links = [el.get_attribute("href") for el in offer_elements]
                except TimeoutException:
                    logger.info(f"Fin des résultats pour {kw} à la page {page}.")
                    break

                # Scraping des détails de chaque offre
                for link in links:
                    if count_for_kw >= max_offres_per_kw:
                        break

                    # Extraction de l'ID depuis l'URL (ex: /12345678.html)
                    match_id = re.search(r"/(\d+)\.html", link)
                    job_id = match_id.group(1) if match_id else link

                    # Vérification doublons AVANT d'aller sur la page
                    if job_id in existing_ids:
                        logger.info(f"Skipping ID {job_id} (Déjà en base)")
                        continue

                    driver.get(link)
                    time.sleep(1.5)

                    try:
                        # Extraction des données brutes
                        raw_data = {"url": link, "source": "HelloWork"}

                        # Titre
                        try:
                            raw_data["title"] = driver.find_element(
                                By.CSS_SELECTOR, "[data-cy='jobTitle']"
                            ).text
                        except Exception:
                            raw_data["title"] = "Sans titre"

                        # Entreprise
                        try:
                            raw_data["company"] = driver.find_element(
                                By.CSS_SELECTOR, "p.tw-typo-s.tw-inline"
                            ).text
                        except Exception:
                            raw_data["company"] = "Non spécifié"

                        # Date de création
                        try:
                            date_element = driver.find_element(
                                By.XPATH, "//span[contains(text(), 'Publiée le')]"
                            )
                            date_text = date_element.text
                            match_date = re.search(r"(\d{2}/\d{2}/\d{4})", date_text)
                            raw_data["creation_date"] = (
                                match_date.group(1) if match_date else None
                            )
                        except Exception:
                            raw_data["creation_date"] = None

                        # Tags (Contract, Experience, Location)
                        raw_data["contract_type"] = None
                        raw_data["required_experience"] = None
                        raw_data["location"] = None

                        tags = driver.find_elements(
                            By.CSS_SELECTOR, "li.tw-tag-secondary-s"
                        )
                        for tag in tags:
                            val = tag.text
                            if "ans" in val.lower() or "exp." in val.lower():
                                raw_data["required_experience"] = val
                            elif val in [
                                "CDI",
                                "CDD",
                                "Alternance",
                                "Stage",
                                "Intérim",
                            ]:
                                raw_data["contract_type"] = val
                            elif raw_data["location"] is None:
                                raw_data["location"] = val

                        # Description
                        description_text = ""
                        try:
                            desc = driver.find_element(
                                By.CSS_SELECTOR,
                                "div[data-truncate-text-target='content']",
                            )
                            description_text = desc.text
                        except Exception:
                            pass

                        # Profil recherché (compétences)
                        try:
                            bouton_profil = driver.find_element(
                                By.XPATH,
                                "//span[contains(text(), 'Le profil recherché')]/ancestor::button",
                            )
                            driver.execute_script(
                                "arguments[0].click();", bouton_profil
                            )
                            time.sleep(0.5)
                            profil_content = driver.find_element(
                                By.CSS_SELECTOR, "#collapsed-content p.tw-typo-long-m"
                            )
                            description_text += " " + profil_content.text
                        except Exception:
                            pass

                        raw_data["description"] = description_text

                        # Construction de la row finale (l'ID est déjà extrait de l'URL)
                        row = {
                            "id": job_id,
                            "title": raw_data.get("title", "Sans titre"),
                            "company": raw_data.get("company", "Non spécifié"),
                            "location": raw_data.get("location"),
                            "url": link,
                            "source": "HelloWork",
                            "description": clean_description(
                                raw_data.get("description")
                            ),
                            "creation_date": raw_data.get("creation_date"),
                            "contract_type": raw_data.get("contract_type"),
                            "required_experience": raw_data.get("required_experience"),
                            "contact": None,
                            "actualisation_date": None,
                            "raw_json": json.dumps(raw_data, ensure_ascii=False),
                        }

                        all_data.append(row)
                        existing_ids.add(job_id)
                        count_for_kw += 1
                        logger.info(
                            f"[{count_for_kw}/{max_offres_per_kw}] Scrapé : {row['title']}"
                        )

                    except Exception as e:
                        logger.warning(f"Erreur sur {link}: {e}")

                    driver.back()
                    time.sleep(1)

                # Pagination vers la page suivante
                page += 1
                try:
                    next_btn = driver.find_element(
                        By.CSS_SELECTOR, f"button[name='p'][value='{page}']"
                    )
                    driver.execute_script("arguments[0].click();", next_btn)
                    time.sleep(2)
                except Exception:
                    logger.info(f"Fin de la pagination pour {kw} à la page {page - 1}.")
                    break

    finally:
        driver.quit()

    return all_data


def run_hw_scraper(
    keywords_to_fetch, max_offres_per_kw=10, save_to_db=False, headless=None
):
    """
    Orchestrateur du scraping HelloWork - même pattern que run_wttj_scraper().

    Args:
        keywords_to_fetch: Liste des mots-clés à rechercher
        max_offres_per_kw: Nombre max d'offres par mot-clé
        save_to_db: Si True, insère les offres en base de données
        headless: Si True, le navigateur est invisible. Si False, on voit le scraping en temps réel.

    Returns:
        Liste des offres scrapées
    """
    if not keywords_to_fetch:
        logger.error("La liste des mots-clés est vide.")
        return []

    db = SessionLocal()
    logger.info("Démarrage du scraping HelloWork")
    scraped_offers = []

    try:
        # 1. Lancement du scraping
        scraped_offers = scrape_hellowork(
            keywords=keywords_to_fetch,
            max_offres_per_kw=max_offres_per_kw,
            db_session=db,
            headless=headless,
        )

        # 2. Synthèse
        if scraped_offers:
            logger.success(
                f"Scraping terminé : {len(scraped_offers)} nouvelles offres trouvées."
            )
            for offer in scraped_offers[:3]:  # Affiche les 3 premières
                logger.info(f"  → {offer['title']} chez {offer['company']}")

            # 3. Insertion en BDD si demandé
            if save_to_db:
                save_offers_to_db(db, scraped_offers, source_name="HelloWork")
        else:
            logger.info("Aucune nouvelle offre à traiter.")

    except Exception as e:
        logger.critical(f"Échec du scraping HelloWork : {e}")
    finally:
        db.close()
        logger.info("Session de base de données fermée.")

    return scraped_offers


if __name__ == "__main__":
    # Test avec insertion en base de données
    # headless=False permet de voir le navigateur en action
    keywords_to_test = ["Data Scientist credit agricole"]
    offers = run_hw_scraper(
        keywords_to_test, max_offres_per_kw=3, save_to_db=True, headless=False
    )

    print(f"\nRésultat : {len(offers)} offres traitées")
