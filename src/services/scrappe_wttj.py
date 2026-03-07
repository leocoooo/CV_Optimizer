import time
import json
import hashlib
import re
from datetime import datetime, timedelta
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.database.database import SessionLocal
from src.services.scraping_utils import (
    setup_logger,
    get_existing_ids,
    clean_description,
    save_offers_to_db,
)

# ===== HARDCODED TAG REFERENCES FOR WTTJ =====
# Type de job (contrats)
CONTRACT_TYPES_WTTJ = {
    "CDI",
    "Stage",
    "Alternance",
    "CDD / Temporaire",
    "Autres",
    "Freelance",
    "Temps partiel",
    "Graduate Program",
    "VIE",
    "Bénévolat / Service Civique",
}

# Professions/Fonctions WTTJ
PROFESSIONS_WTTJ = {
    "Accueil",
    "Affaires et finance",
    "Agriculture et agroalimentaire",
    "Artisanat et travail manuel",
    "Communication, marketing et publicité",
    "Conseil et stratégie",
    "Construction",
    "Culture et arts",
    "Enseignement",
    "Entretien et réparation",
    "Gestion de projets/de produits",
    "Juridique",
    "Mode",
    "RH/Personnel",
    "Recherche et développement",
    "Santé",
    "Sécurité et défense",
    "Technologie et ingénierie",
    "Transport et logistique",
    "Vente et service à la clientèle",
}

# Secteurs WTTJ
SECTORS_WTTJ = {
    "Architecture",
    "Association / ONG",
    "Banques / Assurances / Finance",
    "Conseil / Audit",
    "Culture / Médias / Divertissement",
    "Distribution",
    "Education / Formation / Recrutement",
    "Food et boissons",
    "Hôtellerie / Tourisme / Loisirs",
    "Immobilier",
    "Industrie",
    "Ingénierie",
    "Légal / Justice",
    "Mobilité / Transport",
    "Mode / Luxe / Beauté / Art de vivre",
    "Publicité / Marketing / Agence",
    "Santé / Social / Environnement",
    "Secteur public et administration",
    "Services aux entreprises",
    "Tech",
}

# Modes télétravail
REMOTE_MODES_WTTJ = {
    "Inconnu",
    "Télétravail non autorisé",
    "Télétravail occasionnel",
    "Télétravail fréquent",
    "Télétravail total",
}

# Combined for validation
PROFESSIONS_AND_SECTORS_WTTJ = PROFESSIONS_WTTJ | SECTORS_WTTJ

# Configuration du logger
setup_logger(level="DEBUG")


def scrape_wttj_json_strategy(
    keywords, max_offres_per_kw=1, db_session=None, headless=None
):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")  # Mode sans interface pour la prod
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

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
                        EC.presence_of_all_elements_located(
                            (
                                By.CSS_SELECTOR,
                                "li[data-testid='search-results-list-item-wrapper']",
                            )
                        )
                    )
                except TimeoutException:
                    logger.info(f"Fin des résultats pour {kw} à la page {page}.")
                    break

                # Récupération de toutes les cartes de la page
                cards = driver.find_elements(
                    By.CSS_SELECTOR,
                    "li[data-testid='search-results-list-item-wrapper']",
                )

                page_links = []
                for card in cards:
                    # Extraction rapide du lien pour identifier l'offre
                    try:
                        link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                        # Note : Idéalement, on génère l'ID ici si les infos (titre/entreprise)
                        # sont visibles dans la carte pour éviter le driver.get(link)
                        page_links.append(link)
                    except Exception as e:
                        logger.warning(
                            f"Erreur lors de l'extraction du lien dans la carte : {e}"
                        )
                        continue

                # Scraping des détails
                for link in page_links:
                    if count_for_kw >= max_offres_per_kw:
                        break

                    try:
                        driver.get(link)
                        time.sleep(2)  # Temps de chargement JSON-LD
                        driver.execute_script(
                            "window.scrollTo(0, 500);"
                        )  # Scroll pour charger les éléments

                        # ========== CLIQUER SUR "VOIR PLUS" POUR CHARGER LE TEXTE COMPLET ==========
                        try:
                            # Find and click all "Voir plus" buttons/links
                            # The button can be either <button> or <a> with data-testid="view-more-btn"
                            show_more_buttons = driver.find_elements(
                                By.XPATH,
                                "//a[@data-testid='view-more-btn'] | //button[@data-testid='view-more-btn'] | //button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'voir plus')] | //button[contains(text(), 'Show more')]",
                            )

                            for button in show_more_buttons:
                                try:
                                    # Scroll the button into view
                                    driver.execute_script(
                                        "arguments[0].scrollIntoView(true);", button
                                    )
                                    time.sleep(0.5)
                                    # Click the button - try JavaScript click if regular click fails
                                    try:
                                        button.click()
                                    except Exception:
                                        # Fallback to JavaScript click
                                        driver.execute_script(
                                            "arguments[0].click();", button
                                        )
                                    time.sleep(1)  # Wait for content to load
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        # ========== EXTRACTION DU JSON-LD ==========
                        script_element = driver.find_element(
                            By.XPATH, "//script[@type='application/ld+json']"
                        )
                        job_data = json.loads(script_element.get_attribute("innerHTML"))

                        # ========== EXTRACTION DES DONNÉES ==========
                        raw_data = {
                            "url": link,
                            "source": "Welcome to the Jungle",
                            "date_scraping": datetime.now().isoformat(),
                        }

                        # ===== POSTE =====
                        title = job_data.get("title", "Sans titre")
                        raw_data["title"] = title

                        # ===== ENTREPRISE =====
                        hiring_org = job_data.get("hiringOrganization", {})
                        company = hiring_org.get("name", "Inconnu")
                        raw_data["company"] = company
                        raw_data["company_size"] = hiring_org.get("numberOfEmployees")

                        # ===== LOCALISATION =====
                        location = (
                            job_data.get("jobLocation", [{}])[0]
                            .get("address", {})
                            .get("addressLocality", "N/C")
                        )
                        raw_data["location"] = location

                        # Adresse complète si disponible
                        location_obj = job_data.get("jobLocation", [{}])[0].get(
                            "address", {}
                        )
                        location_address = None
                        if location_obj:
                            address_parts = [
                                location_obj.get("streetAddress"),
                                location_obj.get("postalCode"),
                                location_obj.get("addressLocality"),
                                location_obj.get("addressCountry"),
                            ]
                            location_address = ", ".join(p for p in address_parts if p)
                        raw_data["location_address"] = (
                            location_address if location_address else None
                        )
                        raw_data["location_country"] = (
                            job_data.get("jobLocation", [{}])[0]
                            .get("address", {})
                            .get("addressCountry", "France")
                        )

                        # ===== CONTRAT & CONDITIONS =====
                        # Extract contract type from page HTML
                        raw_data["contract_type"] = None
                        try:
                            # Method 1: Search for known contract types as direct text on page
                            for contract_option in CONTRACT_TYPES_WTTJ:
                                try:
                                    driver.find_element(
                                        By.XPATH,
                                        f"//span[contains(text(), '{contract_option}')] | //div[text()='{contract_option}']",
                                    )
                                    raw_data["contract_type"] = contract_option
                                    break
                                except Exception:
                                    continue
                        except Exception:
                            pass

                        if not raw_data["contract_type"]:
                            # Method 2: Fallback to JSON-LD
                            try:
                                json_ld = job_data.get("employmentType")
                                if json_ld in CONTRACT_TYPES_WTTJ:
                                    raw_data["contract_type"] = json_ld
                                    logger.debug(
                                        f"Contract type from JSON-LD: {json_ld}"
                                    )
                            except Exception:
                                pass

                        # Date publication avec extraction du format "il y a X jours"
                        raw_data["date_publication"] = None
                        try:
                            # Chercher l'élément avec "il y a X jours"
                            time_elem = driver.find_element(
                                By.XPATH, "//time[@datetime]"
                            )
                            datetime_attr = time_elem.get_attribute("datetime")
                            span_elem = time_elem.find_element(By.TAG_NAME, "span")
                            days_text = span_elem.text  # Format: "il y a X jours"

                            # Parser "il y a X jours" pour calculer la date
                            if "il y a" in days_text:
                                match = re.search(r"il y a\s+(\d+)\s+jours", days_text)
                                if match:
                                    days = int(match.group(1))
                                    calc_date = datetime.now() - timedelta(days=days)
                                    raw_data["date_publication"] = calc_date.isoformat()
                                else:
                                    # Fallback to datetime attribute
                                    raw_data["date_publication"] = datetime_attr
                            else:
                                raw_data["date_publication"] = datetime_attr
                        except Exception:
                            # Fallback to JSON-LD datePosted if available
                            raw_data["date_publication"] = job_data.get("datePosted")

                        # Télétravail
                        raw_data["remote_mode"] = None
                        try:
                            # Method 1: Search for known remote modes as direct text on page
                            for mode in REMOTE_MODES_WTTJ:
                                try:
                                    driver.find_element(
                                        By.XPATH,
                                        f"//span[contains(text(), '{mode}')] | //div[text()='{mode}']",
                                    )
                                    raw_data["remote_mode"] = mode
                                    break
                                except Exception:
                                    continue
                        except Exception:
                            pass

                        if not raw_data["remote_mode"]:
                            # Method 2: Look for remote work icon patterns
                            try:
                                remote_element = driver.find_element(
                                    By.XPATH,
                                    "//svg[@aria-label*='remote' or @aria-label*='Remote'] | //i[@class*='remote' or @aria-label*='remote']",
                                )
                                # Get following sibling text
                                remote_mode_text = remote_element.find_element(
                                    By.XPATH,
                                    "following-sibling::span | following-sibling::div",
                                ).text.strip()
                                if remote_mode_text in REMOTE_MODES_WTTJ:
                                    raw_data["remote_mode"] = remote_mode_text
                                    logger.debug(
                                        f"Remote mode extracted: {remote_mode_text}"
                                    )
                            except Exception:
                                pass

                        # ===== PROFIL & COMPÉTENCES =====
                        # Expérience requise
                        raw_data["required_experience"] = None
                        try:
                            exp_element = driver.find_element(
                                By.XPATH,
                                "//span[contains(text(), 'Expérience :')]/parent::div",
                            )
                            exp_text = exp_element.text
                            if "Expérience :" in exp_text:
                                raw_data["required_experience"] = exp_text.split(
                                    "Expérience :"
                                )[1].strip()
                            else:
                                raw_data["required_experience"] = exp_text.strip()
                        except Exception:
                            pass

                        # Éducation requise
                        raw_data["required_education"] = None
                        try:
                            edu_element = driver.find_element(
                                By.XPATH,
                                "//span[contains(text(), 'Éducation :')]/parent::div",
                            )
                            edu_text = edu_element.text
                            if "Éducation :" in edu_text:
                                raw_data["required_education"] = edu_text.split(
                                    "Éducation :"
                                )[1].strip()
                            else:
                                raw_data["required_education"] = edu_text.strip()
                        except Exception:
                            pass

                        # Competences requises - extract from dedicated section
                        raw_data["competences"] = None
                        try:
                            # Find the skills section with the specific div structure
                            # Look for divs with length attribute and variant="default" containing skill spans
                            skill_divs = driver.find_elements(
                                By.XPATH, "//div[@length and @variant='default']//span"
                            )
                            skills = []

                            for skill_span in skill_divs:
                                try:
                                    skill_text = skill_span.text.strip()
                                    if skill_text and 1 < len(skill_text) < 50:
                                        # Filter out noise (generic terms, buttons, navigation)
                                        exclude_keywords = [
                                            "sauvegarder",
                                            "suivre",
                                            "retour",
                                            "postuler",
                                            "cookie",
                                            "france",
                                            "voir",
                                            "découvrir",
                                            "explorer",
                                        ]
                                        if not any(
                                            kw.lower() in skill_text.lower()
                                            for kw in exclude_keywords
                                        ):
                                            if skill_text not in skills:
                                                skills.append(skill_text)
                                except Exception:
                                    pass

                            if skills and len(skills) >= 2:
                                raw_data["competences"] = ", ".join(
                                    skills[:8]
                                )  # Limit to 8 skills
                                logger.debug(
                                    f"Competences found: {raw_data['competences']}"
                                )
                        except Exception as e:
                            logger.debug(f"Competences extraction failed: {e}")

                        # ===== RÉMUNÉRATION & AVANTAGES =====
                        raw_data["salary"] = None
                        try:
                            # Find salary in metadata - look for the pattern near "Salaire"
                            salary_found = False
                            try:
                                # Method 1: Find "Salaire :" text and extract adjacent content
                                all_content = driver.page_source
                                # Search for salary pattern in page source (handles &nbsp; entities)
                                salary_match = re.search(
                                    r"Salaire\s*:\s*([\d]+[KM]?\s*€)",
                                    all_content,
                                    re.IGNORECASE,
                                )
                                if salary_match:
                                    raw_data["salary"] = salary_match.group(1).strip()
                                    salary_found = True
                                    logger.debug(
                                        f"Salary found via regex: {raw_data['salary']}"
                                    )
                            except Exception:
                                pass

                            if not salary_found:
                                # Method 2: Find elements containing salary icon and get text
                                try:
                                    salary_spans = driver.find_elements(
                                        By.XPATH,
                                        "//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'salaire')]",
                                    )
                                    for span in salary_spans:
                                        try:
                                            parent = span.find_element(
                                                By.XPATH, "parent::div | parent::span"
                                            )
                                            parent_text = parent.text.strip()
                                            match = re.search(
                                                r"([\d]+[KM]?\s*€)", parent_text
                                            )
                                            if match:
                                                raw_data["salary"] = match.group(
                                                    1
                                                ).strip()
                                                salary_found = True
                                                break
                                        except Exception:
                                            pass
                                except Exception:
                                    pass

                            if not salary_found:
                                # Method 3: Look for € in page and find the shortest digit pattern
                                try:
                                    salary_pattern = re.search(
                                        r"([\d]+[KM]?\s*€)", driver.page_source
                                    )
                                    if salary_pattern:
                                        raw_data["salary"] = salary_pattern.group(
                                            1
                                        ).strip()
                                        logger.debug(
                                            f"Salary found via pattern: {raw_data['salary']}"
                                        )
                                except Exception:
                                    pass
                        except Exception as e:
                            logger.debug(f"Salary extraction failed: {e}")

                        # ===== CONTENU & DESCRIPTIONS =====
                        # "Le poste" = description
                        raw_data["description"] = None
                        try:
                            # Get the description container directly without relying on unstable CSS class
                            desc_elem = driver.find_element(
                                By.XPATH,
                                "//div[@data-testid='job-section-description']",
                            )
                            desc_text = desc_elem.text.strip()
                            # Remove trailing "Voir plus" if present
                            if desc_text.endswith("Voir plus"):
                                desc_text = desc_text.replace("Voir plus", "").strip()
                            raw_data["description"] = desc_text if desc_text else None
                        except Exception:
                            try:
                                # Alternative: try to get from JSON-LD
                                raw_data["description"] = job_data.get("description")
                            except Exception:
                                pass

                        # "Profil recherché" = job_profile
                        raw_data["job_profile"] = None
                        try:
                            # Look for the "Profil recherché" section
                            # Try different heading levels and get the text content after it
                            profile_elems = driver.find_elements(
                                By.XPATH, "//h2 | //h3 | //h4"
                            )

                            for elem in profile_elems:
                                try:
                                    text = elem.text.lower()
                                    if "profil" in text:
                                        # Found a heading with "profil"
                                        # Try to get the sibling div/p/section with content
                                        following_div = elem.find_element(
                                            By.XPATH,
                                            "following-sibling::div[1] | following-sibling::p[1] | following-sibling::section[1]",
                                        )
                                        profile_content = following_div.text.strip()

                                        # Remove "Voir plus" button text if present
                                        if profile_content.endswith("Voir plus"):
                                            profile_content = profile_content.replace(
                                                "Voir plus", ""
                                            ).strip()

                                        if profile_content:
                                            raw_data["job_profile"] = profile_content
                                            break
                                except Exception:
                                    # This heading doesn't have the content we need, try next
                                    continue

                            # If section not found, job_profile remains None (that's OK)

                        except Exception:
                            # job_profile remains None - that's OK, not all offers have this section
                            pass

                        # Secteur/Fonction - extract from company info section (data-testid="job-company-tag")
                        raw_data["sector"] = None
                        try:
                            # Find all job-company-tag divs which contain sector/profession info
                            # They have an icon (icon alt="Tag") and a span with the text
                            sector_tags = driver.find_elements(
                                By.XPATH,
                                "//div[@data-testid='job-company-tag']//span[text()]",
                            )

                            sectors = []
                            for tag_span in sector_tags:
                                try:
                                    sector_text = tag_span.text.strip()
                                    if sector_text and len(sector_text) > 2:
                                        # Filter generic terms and company info (e.g., "400 collaborateurs")
                                        exclude_keywords = [
                                            "collaborateurs",
                                            "Créée en",
                                            "Âge moyen",
                                            "Chiffre d'affaires",
                                        ]
                                        if not any(
                                            kw.lower() in sector_text.lower()
                                            for kw in exclude_keywords
                                        ):
                                            sectors.append(sector_text)
                                except Exception:
                                    pass

                            if sectors:
                                # Join with separator (use first one or all if comma-separated)
                                raw_data["sector"] = " - ".join(
                                    sectors[:2]
                                )  # Limit to 2 tags
                        except Exception as e:
                            logger.debug(f"Sector extraction failed: {e}")

                        # ===== COMPANY SECTOR & SIZE =====
                        # Extract company size from "L'entreprise" tab
                        if not raw_data["company_size"]:
                            try:
                                size_tag = driver.find_element(
                                    By.XPATH,
                                    "//div[@id='the-company-section']//span[contains(text(), 'collaborateurs')]",
                                )
                                raw_data["company_size"] = size_tag.text.strip()
                            except Exception:
                                pass

                        # ========== GÉNÉRATION DE L'ID ==========
                        # Ensure company, title, location are strings before processing
                        company_str = str(company).lower() if company else "inconnu"
                        title_str = str(title).lower() if title else "sans_titre"
                        location_str = str(location).lower() if location else "n_a"

                        job_id = hashlib.sha256(
                            f"{company_str}|{title_str}|{location_str}".encode()
                        ).hexdigest()

                        # Vérification doublons AVANT extraction compl des détails
                        if job_id in existing_ids:
                            logger.debug(f"Skipping : {title} (Déjà en base)")
                            continue

                        # ========== CONSTRUCTION DE LA ROW FINALE ==========
                        row = {
                            # IDENTIFIANTS
                            "id": job_id,
                            "url": link,
                            "source": "Welcome to the Jungle",
                            "date_publication": raw_data.get("date_publication"),
                            "date_scraping": raw_data.get("date_scraping"),
                            # POSTE
                            "title": title,
                            "sector": raw_data.get("sector"),
                            "contract_type": raw_data.get("contract_type"),
                            "remote_mode": raw_data.get("remote_mode"),
                            # LOCALISATION
                            "location": location,
                            "location_address": raw_data.get("location_address"),
                            "location_country": raw_data.get("location_country"),
                            # ENTREPRISE
                            "company": company,
                            "company_size": raw_data.get("company_size"),
                            # PROFIL DEMANDÉ
                            "required_experience": raw_data.get("required_experience"),
                            "required_education": raw_data.get("required_education"),
                            "competences": raw_data.get("competences"),
                            # RÉMUNÉRATION & AVANTAGES
                            "salary": raw_data.get("salary"),
                            # CONTENU
                            "description": clean_description(
                                raw_data.get("description")
                            ),
                            "job_profile": clean_description(
                                raw_data.get("job_profile")
                            ),
                        }

                        all_data.append(row)
                        existing_ids.add(job_id)
                        logger.info(
                            f"[{count_for_kw + 1}/{max_offres_per_kw}] Scrapé : {title}"
                        )
                        count_for_kw += 1
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'extraction de {link}: {e}")
                        # Continue to next link - this error shouldn't prevent processing others

                page += 1  # Incrémenter la page de recherche si on n'a pas atteint le quota d'offres souhaitées

    finally:
        driver.quit()

    return all_data


def run_wttj_scraper(
    keywords_to_fetch, max_offres_per_kw=1, save_to_db=False, headless=None
):
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
        logger.debug(
            f"Keywords reçus par run_wttj_scraper : {keywords_to_fetch} (type: {type(keywords_to_fetch)})"
        )
        scraped_offers = scrape_wttj_json_strategy(
            keywords=keywords_to_fetch,
            max_offres_per_kw=max_offres_per_kw,
            db_session=db,
            headless=headless,
        )

        # Synthèse
        if scraped_offers:
            logger.success(
                f"Scraping terminé : {len(scraped_offers)} nouvelles offres trouvées."
            )
            for offer in scraped_offers[:3]:  # Affiche les 3 premières
                logger.info(f"  → {offer['title']} chez {offer['company']}")

            # Insertion éventuelle en BDD
            if save_to_db:
                save_offers_to_db(db, scraped_offers, source_name="WTTJ")
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
    keywords_to_test = ["Data Scientist"]
    offers = run_wttj_scraper(
        keywords_to_test, max_offres_per_kw=3, save_to_db=True, headless=True
    )

    print(f"\nRésultat : {len(offers)} offre(s) traité(es)")
    print(offers[0] if offers else "Aucune offre trouvée")
