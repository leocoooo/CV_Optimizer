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
    get_existing_urls,
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
    "Graduate program",
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


def parse_location_wttj(
    location_address: str | None, driver=None
) -> dict[str, str | None]:
    """
    Parse l'adresse complète de WTTJ au format "Rue, Code Postal Ville, Pays"
    pour extraire city, department, region.

    Si le parsing d'adresse échoue ou que city reste None, tente de récupérer
    la ville depuis la balise "lieux de travail" sur la page.

    Exemples:
        "Pont de Levallois, 92300 Levallois-Perret, France" →
        {"city": "Levallois-Perret", "department": "Hauts-de-Seine", "region": "Île-de-France"}

    Args:
        location_address: Adresse complète au format WTTJ
        driver: WebDriver Selenium (optionnel) pour chercher "lieux de travail" si parsing échoue

    Returns:
        dict: {"city": str|None, "department": str|None, "region": str|None}
    """
    result: dict[str, str | None] = {"city": None, "department": None, "region": None}

    if not location_address and not driver:
        return result

    # Mappages code postal (2 premiers chiffres = département) → nom
    dept_names = {
        "01": "Ain",
        "02": "Aisne",
        "03": "Allier",
        "04": "Alpes-de-Haute-Provence",
        "05": "Hautes-Alpes",
        "06": "Alpes-Maritimes",
        "07": "Ardèche",
        "08": "Ardennes",
        "09": "Ariège",
        "10": "Aube",
        "11": "Aude",
        "12": "Aveyron",
        "13": "Bouches-du-Rhône",
        "14": "Calvados",
        "15": "Cantal",
        "16": "Charente",
        "17": "Charente-Maritime",
        "18": "Cher",
        "19": "Corrèze",
        "2A": "Corse-du-Sud",
        "2B": "Haute-Corse",
        "21": "Côte-d'Or",
        "22": "Côtes-d'Armor",
        "23": "Creuse",
        "24": "Dordogne",
        "25": "Doubs",
        "26": "Drôme",
        "27": "Eure",
        "28": "Eure-et-Loir",
        "29": "Finistère",
        "30": "Gard",
        "31": "Haute-Garonne",
        "32": "Gers",
        "33": "Gironde",
        "34": "Hérault",
        "35": "Ille-et-Vilaine",
        "36": "Indre",
        "37": "Indre-et-Loire",
        "38": "Isère",
        "39": "Jura",
        "40": "Landes",
        "41": "Loir-et-Cher",
        "42": "Loire",
        "43": "Haute-Loire",
        "44": "Loire-Atlantique",
        "45": "Loiret",
        "46": "Lot",
        "47": "Lot-et-Garonne",
        "48": "Lozère",
        "49": "Maine-et-Loire",
        "50": "Manche",
        "51": "Marne",
        "52": "Haute-Marne",
        "53": "Mayenne",
        "54": "Meurthe-et-Moselle",
        "55": "Meuse",
        "56": "Morbihan",
        "57": "Moselle",
        "58": "Nièvre",
        "59": "Nord",
        "60": "Oise",
        "61": "Orne",
        "62": "Pas-de-Calais",
        "63": "Puy-de-Dôme",
        "64": "Pyrénées-Atlantiques",
        "65": "Hautes-Pyrénées",
        "66": "Pyrénées-Orientales",
        "67": "Bas-Rhin",
        "68": "Haut-Rhin",
        "69": "Rhône",
        "70": "Haute-Saône",
        "71": "Saône-et-Loire",
        "72": "Sarthe",
        "73": "Savoie",
        "74": "Haute-Savoie",
        "75": "Paris",
        "76": "Seine-Maritime",
        "77": "Seine-et-Marne",
        "78": "Yvelines",
        "79": "Deux-Sèvres",
        "80": "Somme",
        "81": "Tarn",
        "82": "Tarn-et-Garonne",
        "83": "Var",
        "84": "Vaucluse",
        "85": "Vendée",
        "86": "Vienne",
        "87": "Haute-Vienne",
        "88": "Vosges",
        "89": "Yonne",
        "90": "Territoire de Belfort",
        "91": "Essonne",
        "92": "Hauts-de-Seine",
        "93": "Seine-Saint-Denis",
        "94": "Val-de-Marne",
        "95": "Val-d'Oise",
    }

    # Mappages département → région
    regions = {
        "75": "Île-de-France",
        "77": "Île-de-France",
        "78": "Île-de-France",
        "91": "Île-de-France",
        "92": "Île-de-France",
        "93": "Île-de-France",
        "94": "Île-de-France",
        "95": "Île-de-France",
        "60": "Île-de-France",
        "21": "Bourgogne-Franche-Comté",
        "25": "Bourgogne-Franche-Comté",
        "39": "Bourgogne-Franche-Comté",
        "58": "Bourgogne-Franche-Comté",
        "70": "Bourgogne-Franche-Comté",
        "71": "Bourgogne-Franche-Comté",
        "89": "Bourgogne-Franche-Comté",
        "90": "Bourgogne-Franche-Comté",
        "22": "Bretagne",
        "29": "Bretagne",
        "35": "Bretagne",
        "56": "Bretagne",
        "18": "Centre-Val de Loire",
        "28": "Centre-Val de Loire",
        "36": "Centre-Val de Loire",
        "37": "Centre-Val de Loire",
        "41": "Centre-Val de Loire",
        "45": "Centre-Val de Loire",
        "2A": "Corse",
        "2B": "Corse",
        "08": "Grand Est",
        "10": "Grand Est",
        "51": "Grand Est",
        "52": "Grand Est",
        "54": "Grand Est",
        "55": "Grand Est",
        "57": "Grand Est",
        "67": "Grand Est",
        "68": "Grand Est",
        "88": "Grand Est",
        "02": "Hauts-de-France",
        "59": "Hauts-de-France",
        "62": "Hauts-de-France",
        "80": "Hauts-de-France",
        "14": "Normandie",
        "27": "Normandie",
        "50": "Normandie",
        "61": "Normandie",
        "76": "Normandie",
        "16": "Nouvelle-Aquitaine",
        "17": "Nouvelle-Aquitaine",
        "19": "Nouvelle-Aquitaine",
        "23": "Nouvelle-Aquitaine",
        "24": "Nouvelle-Aquitaine",
        "33": "Nouvelle-Aquitaine",
        "40": "Nouvelle-Aquitaine",
        "47": "Nouvelle-Aquitaine",
        "64": "Nouvelle-Aquitaine",
        "79": "Nouvelle-Aquitaine",
        "86": "Nouvelle-Aquitaine",
        "87": "Nouvelle-Aquitaine",
        "09": "Occitanie",
        "11": "Occitanie",
        "12": "Occitanie",
        "30": "Occitanie",
        "31": "Occitanie",
        "32": "Occitanie",
        "34": "Occitanie",
        "46": "Occitanie",
        "48": "Occitanie",
        "65": "Occitanie",
        "66": "Occitanie",
        "81": "Occitanie",
        "82": "Occitanie",
        "01": "Auvergne-Rhône-Alpes",
        "03": "Auvergne-Rhône-Alpes",
        "07": "Auvergne-Rhône-Alpes",
        "15": "Auvergne-Rhône-Alpes",
        "26": "Auvergne-Rhône-Alpes",
        "38": "Auvergne-Rhône-Alpes",
        "42": "Auvergne-Rhône-Alpes",
        "43": "Auvergne-Rhône-Alpes",
        "63": "Auvergne-Rhône-Alpes",
        "69": "Auvergne-Rhône-Alpes",
        "73": "Auvergne-Rhône-Alpes",
        "74": "Auvergne-Rhône-Alpes",
        "04": "Provence-Alpes-Côte d'Azur",
        "05": "Provence-Alpes-Côte d'Azur",
        "06": "Provence-Alpes-Côte d'Azur",
        "13": "Provence-Alpes-Côte d'Azur",
        "83": "Provence-Alpes-Côte d'Azur",
        "84": "Provence-Alpes-Côte d'Azur",
        "44": "Pays de la Loire",
        "49": "Pays de la Loire",
        "53": "Pays de la Loire",
        "72": "Pays de la Loire",
        "85": "Pays de la Loire",
    }

    # ÉTAPE 1: Essayer de parser l'adresse au format "Rue, Code Postal Ville, Pays"
    if location_address:
        try:
            postal_match = re.search(r"\b(\d{5})\b", location_address)
            if postal_match:
                postal_code = postal_match.group(1)
                dept_code = postal_code[:2]

                city_match = re.search(r"\d{5}\s+([^,]+)", location_address)
                if city_match:
                    result["city"] = city_match.group(1).strip()
                    result["department"] = dept_names.get(dept_code)
                    result["region"] = regions.get(dept_code)
                    return result  # Succès - on retourne
        except Exception as e:
            logger.debug(f"Erreur parsing address WTTJ: {e}")

    # ÉTAPE 2: Si le parsing a échoué ou pas d'adresse, chercher dans "lieux de travail" sur la page
    if driver and not result["city"]:
        try:
            workplace_elem = driver.find_element(
                By.XPATH,
                "//span[contains(text(), 'Lieux de travail')] | //label[contains(text(), 'Lieux de travail')] | //div[contains(text(), 'Lieux de travail')]",
            )
            # Chercher le texte qui suit - généralement dans le même parent ou suivant
            parent = workplace_elem.find_element(By.XPATH, "ancestor::div[1]")
            workplace_text = parent.text.strip()

            # Extraire la ville (première ligne de texte après "Lieux de travail")
            lines = workplace_text.split("\n")
            if len(lines) > 1:
                city_candidate = lines[1].strip()  # Deuxième ligne généralement
                if city_candidate and not any(
                    kw in city_candidate
                    for kw in ["Lieux", "travail", "de", "télétravail"]
                ):
                    result["city"] = city_candidate
                    logger.debug(f"City from workplace section: {result['city']}")

                    # Essayer d'extraire le code postal si présent
                    postal_match = re.search(r"\b(\d{5})\b", workplace_text)
                    if postal_match:
                        postal_code = postal_match.group(1)
                        dept_code = postal_code[:2]
                        result["department"] = dept_names.get(dept_code)
                        result["region"] = regions.get(dept_code)
        except Exception as e:
            logger.debug(f"Erreur recherche 'lieux de travail': {e}")

    return result


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

    # Récupération des IDs et URLs déjà scrapés (en base + run actuel)
    existing_ids = get_existing_ids(db_session) if db_session else set()
    existing_urls = get_existing_urls(db_session) if db_session else set()
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
                        # Récupérer l'adresse complète depuis le JSON-LD pour parsing robuste
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
                        # Prendre le salaire SEULEMENT s'il y a un tag "Salaire :"
                        raw_data["salary"] = None
                        try:
                            # Chercher un élément contenant "Salaire :" directement sur la page
                            salary_tag = driver.find_element(
                                By.XPATH,
                                "//span[contains(text(), 'Salaire :')] | //div[contains(text(), 'Salaire :')] | //label[contains(text(), 'Salaire :')]",
                            )
                            # Si on trouve le tag, récupérer le texte du parent ou du suivant
                            try:
                                # Chercher du texte avec € à proximité
                                parent = salary_tag.find_element(
                                    By.XPATH,
                                    "ancestor::div[1] | parent::div | parent::span",
                                )
                                salary_text = parent.text.strip()
                                match = re.search(r"([\d\s]+[KM]?\s*€)", salary_text)
                                if match:
                                    raw_data["salary"] = match.group(1).strip()
                                    logger.debug(f"Salary found: {raw_data['salary']}")
                            except Exception:
                                pass
                        except Exception:
                            # Pas de tag "Salaire :" trouvé - laisser à None
                            pass

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
                                        # Filter generic terms, company info, and percentages
                                        exclude_keywords = [
                                            "collaborateurs",
                                            "Créée en",
                                            "Âge moyen",
                                            "Chiffre d'affaires",
                                        ]
                                        # Skip if it's a percentage (e.g., "45%", "55%")
                                        if re.match(r"^\d+%$", sector_text):
                                            continue
                                        # Skip if contains excluded keywords
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
                        location_str = (
                            str(location_address).lower() if location_address else "n_a"
                        )

                        job_id = hashlib.sha256(
                            f"{company_str}|{title_str}|{location_str}".encode()
                        ).hexdigest()

                        # Vérification doublons AVANT extraction complète des détails
                        # Check both by ID and by URL to catch duplicates even if location_address changed
                        if job_id in existing_ids or link in existing_urls:
                            logger.debug(f"Skipping : {title} (Déjà en base)")
                            continue

                        # Parse location to extract city, department, region (avec fallback à "lieux de travail")
                        location_parsed = parse_location_wttj(
                            location_address, driver=driver
                        )

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
                            "city": location_parsed.get("city"),
                            "department": location_parsed.get("department"),
                            "region": location_parsed.get("region"),
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
                        existing_urls.add(link)
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
    keywords_to_test = ["Data Scientist", "Data Engineer", "Data Analyst"]
    offers = run_wttj_scraper(
        keywords_to_test, max_offres_per_kw=3, save_to_db=True, headless=True
    )

    print(f"\nRésultat : {len(offers)} offre(s) traité(es)")
    print(offers[0] if offers else "Aucune offre trouvée")
