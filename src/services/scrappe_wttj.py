import sys
import time
import json
import hashlib
import re
import unicodedata
from loguru import logger
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.database.database import SessionLocal
from src.database.models import JobOffer

logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="DEBUG")

def get_existing_ids(db_session):
    """Récupère les IDs déjà présents en base pour éviter le double scrap."""
    return {offer.id for offer in db_session.query(JobOffer.id).all()}


def clean_description(html_text: str) -> str:
    """
    Nettoie la description HTML pour ne garder que le contenu textuel utile.
    Combine la suppression HTML (BeautifulSoup) + nettoyage Unicode (comme cv_reader).
    """
    if not html_text:
        return ""
    
    # Suppression des balises HTML
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator=" ")
    
    # Normalisation Unicode (accents, caractères spéciaux)
    text = unicodedata.normalize("NFKC", text)
    
    # Suppression des caractères de contrôle et non-imprimables
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    
    # Garde lettres, chiffres, ponctuations de base et espaces
    text = re.sub(r'[^\w\s\.,;:\-\(\)@\'"&]', ' ', text, flags=re.UNICODE)
    
    # Nettoyage des espaces multiples
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def scrape_wttj_json_strategy(keywords, max_offres_per_kw=10, db_session=None, headless=True):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless") # Mode sans interface pour la prod
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Récupération des IDs déjà scrapés (en base + run actuel)
    existing_ids = get_existing_ids(db_session) if db_session else set()
    all_data = []

    try:
        for kw in keywords:
            logger.info(f"Recherche WTTJ : {kw}")
            count_for_kw = 0
            page = 1
            
            while count_for_kw < max_offres_per_kw:
                url_search = f"https://www.welcometothejungle.com/fr/jobs?query={kw.replace(' ', '%20')}&page={page}"
                driver.get(url_search)
                
                # Attente des cartes d'offres
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-testid='search-results-list-item-wrapper']"))
                    )
                except TimeoutException:
                    logger.info(f"Fin des résultats pour {kw} à la page {page}.")
                    break

                # Récupération de toutes les cartes de la page
                cards = driver.find_elements(By.CSS_SELECTOR, "li[data-testid='search-results-list-item-wrapper']")
                
                page_links = []
                for card in cards:
                    # Extraction rapide du lien pour identifier l'offre
                    try:
                        link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                        # Note : Idéalement, on génère l'ID ici si les infos (titre/entreprise) 
                        # sont visibles dans la carte pour éviter le driver.get(link)
                        page_links.append(link)
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'extraction du lien dans la carte : {e}")
                        continue

                # Scraping des détails
                for link in page_links:
                    if count_for_kw >= max_offres_per_kw:
                        break
                    
                    try:
                        driver.get(link)
                        time.sleep(2) # Temps de chargement JSON-LD
                        
                        script_element = driver.find_element(By.XPATH, "//script[@type='application/ld+json']")
                        job_data = json.loads(script_element.get_attribute("innerHTML"))
                        
                        # Génération d'un ID déterministe
                        company = job_data.get("hiringOrganization", {}).get("name", "Inconnu")
                        title = job_data.get("title", "Sans titre")
                        location = job_data.get("jobLocation", [{}])[0].get("address", {}).get("addressLocality", "N/C")
                        
                        job_id = hashlib.sha256(f"{company.lower()}|{title.lower()}|{location.lower()}".encode()).hexdigest()

                        # Vérification doublons 
                        if job_id in existing_ids:
                            logger.debug(f"Skipping : {title} (Déjà en base)")
                            continue

                        row = {
                            "id": job_id,
                            "title": title,
                            "company": company,
                            "location": location,
                            "url": link,
                            "source": "Welcome to the Jungle",
                            "description": clean_description(job_data.get("description")),
                            "creation_date": job_data.get("datePosted"),
                            "contract_type": job_data.get("employmentType"),
                            "required_experience": None,
                            "contact": None,
                            "actualisation_date": None,
                            "raw_json": json.dumps(job_data, ensure_ascii=False),  # JSON brut complet
                        }

                        all_data.append(row)
                        existing_ids.add(job_id) # Ajout au set pour éviter les doublons inter-mots-clés
                        count_for_kw += 1
                        logger.info(f"[{count_for_kw}/{max_offres_per_kw}] Scrapé : {title}")

                    except Exception as e:
                        logger.warning(f"Erreur sur {link}: {e}")

                page += 1 # Incrémenter la page de recherche si on n'a pas atteint le quota d'offres souhaitées 

    finally:
        driver.quit()

    return all_data


def save_wttj_offers_to_db(db_session, offers: list):
    """
    Persiste les offres scrapées en base de données.
    Pattern identique à save_offers_to_db() dans collector.py.
    """
    if not offers:
        logger.info("Aucune offre à insérer.")
        return 0
    
    new_offers_count = 0
    
    for offer_data in offers:
        try:
            new_offer = JobOffer(
                id=offer_data["id"],
                title=offer_data["title"],
                company=offer_data["company"],
                location=offer_data["location"],
                description=offer_data["description"],
                url=offer_data["url"],
                source=offer_data["source"],
                creation_date=offer_data.get("creation_date"),
                actualisation_date=offer_data.get("actualisation_date"),
                contract_type=offer_data.get("contract_type"),
                required_experience=offer_data.get("required_experience"),
                contact=offer_data.get("contact"),
                raw_json=offer_data.get("raw_json"),
            )
            db_session.add(new_offer)
            new_offers_count += 1
        except Exception as e:
            logger.warning(f"Erreur lors de la préparation de l'offre {offer_data.get('title')}: {e}")
    
    try:
        db_session.commit()
        if new_offers_count > 0:
            logger.success(f"Insertion : {new_offers_count} nouvelles offres WTTJ ajoutées en base.")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Erreur lors de l'insertion en base : {e}")
        return 0
    
    return new_offers_count


def run_wttj_scraper(keywords_to_fetch, max_offres_per_kw=10, save_to_db=False, headless=True):
    """
    Orchestrateur du scraping WTTJ - même pattern que run_collector().
    
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
    logger.info("Démarrage du scraping Welcome to the Jungle")
    scraped_offers = []

    try:
        # Lancement du scraping
        scraped_offers = scrape_wttj_json_strategy(
            keywords=keywords_to_fetch,
            max_offres_per_kw=max_offres_per_kw,
            db_session=db,
            headless=headless
        )

        # Synthèse
        if scraped_offers:
            logger.success(f"Scraping terminé : {len(scraped_offers)} nouvelles offres trouvées.")
            for offer in scraped_offers[:3]:  # Affiche les 3 premières
                logger.info(f"  → {offer['title']} chez {offer['company']}")
            
            # Insertion éventuelle en BDD 
            if save_to_db:
                save_wttj_offers_to_db(db, scraped_offers)
        else:
            logger.info("Aucune nouvelle offre à traiter.")

    except Exception as e:
        logger.critical(f"Échec du scraping WTTJ : {e}")
    finally:
        db.close()
        logger.info("Session de base de données fermée.")

    return scraped_offers


if __name__ == "__main__":
    
    # Test avec insertion en base de données
    # headless=False permet de voir le navigateur en action
    keywords_to_test = ["data scientist back market"]
    offers = run_wttj_scraper(
        keywords_to_test, 
        max_offres_per_kw=3, 
        save_to_db=True, 
        headless=False  
    )
    
    print(f"\nRésultat : {len(offers)} offres traitées")