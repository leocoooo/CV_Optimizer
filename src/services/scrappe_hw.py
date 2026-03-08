import time
import re
from datetime import datetime
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
    parse_location_hellowork,
)

# Configuration du logger
setup_logger(level="DEBUG")

# ===== TAGS HELLOWORK CODÉS EN DUR =====
# Source: spec.md

# Types de contrat possibles
CONTRACT_TYPES = {
    "CDI",
    "CDD",
    "Alternance",
    "Stage",
    "Intérim",
    "Freelance",
    "Indépendant",
    "Fonctionnaire",
    "Franchise",
    "Associé",
    "Stage de lycée",
}

# Niveaux d'éducation (Bac + X)
EDUCATION_LEVELS = {
    "Bac +2",
    "Bac +3",
    "Bac +4",
    "Bac +5",
    "CAP",
    "BEP",
    "Bac",
    "Bac +0",
    "Bac +1",
}

# Modes télétravail possibles
REMOTE_MODES = {
    "Télétravail total",
    "Télétravail partiel",
    "Partiel possible",
    "Sans télétravail",
    "À distance",
    "Sur site",
}

# FONCTIONS (à inclure dans sector)
FUNCTIONS = {
    "Achat • Logistique",
    "Achat",
    "Logistique • Métiers du Transport",
    "Administration",
    "Assistanat • Adm.ventes • Accueil",
    "Compta • Gestion • Finance • Audit",
    "Direction • Resp. Co. et Centre de Profit",
    "Juridique • Droit",
    "Métiers de la Fonction Publique",
    "RH • Personnel • Formation",
    "BTP • Bureau d'études",
    "BTP • Gros Oeuvre • Second Oeuvre",
    "Bureau d'Etudes • R&D • BTP archi • conception",
    "Commerce",
    "Commercial • Technico • Commercial",
    "Commercial auprès des particuliers",
    "Commercial auprès des professionnels",
    "Commercial • Vendeur en magasin",
    "Import • Export • International",
    "Métiers de la distribution • Management • Resp.",
    "Négociation • Gestion immobilière",
    "Informatique",
    "Informatique • Dével. Hardware",
    "Informatique • Développement",
    "Informatique • Systèmes d'Information",
    "Informatique • Systèmes • Réseaux",
    "Ingénierie industrielle",
    "Ingénierie • Agro • Agri",
    "Ingénierie • Chimie • Pharmacie • Bio.",
    "Ingénierie • Electro • tech. • Automat.",
    "Ingénierie • Mécanique • Aéron.",
    "Ingénierie • Telecoms • Electronique",
    "Marketing • Communication • Graphisme",
    "Production",
    "Production • Gestion • Maintenance",
    "Production • Opérateur • Manoeuvre",
    "Qualité • Hygiène • Sécurité • Environnement",
    "Restauration • Tourisme • Hôtellerie • Loisirs",
    "Santé • Social",
    "Support (SAV • Hotline)",
    "SAV • Hotline • Téléconseiller",
}

# SECTEURS D'ACTIVITÉ (à inclure dans sector)
ACTIVITY_SECTORS = {
    "Agriculture • Pêche",
    "BTP",
    "Banque • Assurance • Finance",
    "Distribution • Commerce de gros",
    "Enseignement • Formation",
    "Immobilier",
    "Industrie Agro • alimentaire",
    "Industrie Auto • Meca • Navale",
    "Industrie Aéronautique • Aérospatial",
    "Industrie Manufacturière",
    "Industrie Pharmaceutique • Biotechn. • Chimie",
    "Industrie Pétrolière • Pétrochimie",
    "Industrie high • tech • Telecom",
    "Média • Internet • Communication",
    "Restauration",
    "Santé • Social • Association",
    "Secteur Energie • Environnement",
    "Secteur informatique • ESN",
    "Service public autres",
    "Service public d'état",
    "Service public des collectivités territoriales",
    "Service public hospitalier",
    "Services aux Entreprises",
    "Services aux Personnes • Particuliers",
    "Tourisme • Hôtellerie • Loisirs",
    "Transport • Logistique",
}

# Ensemble combiné pour matching
SECTORS_AND_FUNCTIONS = FUNCTIONS | ACTIVITY_SECTORS

# Pattern pour expérience (chercher "X ans" ou "Exp. X")
EXPERIENCE_PATTERN = r"(?:Exp\.|\d+)\s*(?:à|à|-|–)?\s*\d+\s*ans"


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

        logger.debug(
            f"Keywords dans scrape_hellowork : {keywords} (type: {type(keywords)})"
        )

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
                        # ========== EXTRACTION DES DONNÉES ==========
                        raw_data = {
                            "url": link,
                            "source": "HelloWork",
                            "date_scraping": datetime.now().isoformat(),
                        }

                        # ===== POSTE =====
                        # Titre de l'offre
                        try:
                            raw_data["title"] = driver.find_element(
                                By.CSS_SELECTOR, "[data-cy='jobTitle']"
                            ).text
                        except Exception:
                            raw_data["title"] = "Sans titre"

                        # Entreprise
                        raw_data["company"] = "Non spécifié"
                        try:
                            # L'entreprise est dans un <a> tag qui est dans le même <h1> que le titre
                            # Chercher : <h1 id="main-content"> → <a> (deuxième enfant span contenant l'a)
                            company_link = driver.find_element(
                                By.XPATH,
                                "//h1[@id='main-content']//a[contains(@href, '/entreprises/')]",
                            )
                            raw_data["company"] = company_link.text.strip()
                        except Exception as e:
                            logger.debug(f"Erreur extraction company: {e}")

                        # Extraction des tags (contrat, expérience, localisation, éducation, secteur, télétravail)
                        raw_data["contract_type"] = None
                        raw_data["required_experience"] = None
                        raw_data["location"] = None
                        raw_data["required_education"] = None
                        raw_data[
                            "sector"
                        ] = []  # Liste pour accumuler tous les secteurs/fonctions
                        raw_data["remote_mode"] = None
                        raw_data["salary"] = None

                        # Extraction du salaire depuis le bouton
                        try:
                            salary_btn = driver.find_element(
                                By.CSS_SELECTOR, "button[data-cy='salary-tag-button']"
                            )
                            salary_text = salary_btn.text.strip()
                            if "€" in salary_text:
                                # Extraire juste la partie salaire (après la flèche)
                                salary_match = re.search(
                                    r"→\s*(.+?)(?:\s*/\s*an)?$", salary_text
                                )
                                if salary_match:
                                    salary_clean = salary_match.group(1).strip()
                                    # Nettoyer les espaces insécables (\u202f) et autres caractères spéciaux
                                    salary_clean = salary_clean.replace("\u202f", " ")
                                    raw_data["salary"] = salary_clean
                                else:
                                    salary_clean = salary_text.replace("\u202f", " ")
                                    raw_data["salary"] = salary_clean
                        except Exception:
                            pass

                        tags = driver.find_elements(
                            By.CSS_SELECTOR, "li.tw-tag-secondary-s"
                        )
                        uncategorized_tags = []

                        for tag in tags:
                            val = tag.text.strip()

                            # Type de contrat (matching exact pour robustesse)
                            if val in CONTRACT_TYPES:
                                raw_data["contract_type"] = val
                            # Éducation (Bac + X)
                            elif any(x in val.lower() for x in ["bac", "cap", "bep"]):
                                raw_data["required_education"] = val
                            # Télétravail (matching pour les modes définis)
                            elif val in REMOTE_MODES or any(
                                x in val.lower()
                                for x in ["télétravail", "télé", "remote", "distance"]
                            ):
                                raw_data["remote_mode"] = val
                            # Salaire (contient €)
                            elif "€" in val:
                                # Nettoyer les espaces insécables
                                salary_clean = val.replace("\u202f", " ")
                                raw_data["salary"] = salary_clean
                            # Expérience (pattern spécifique: "X ans" ou "Exp. X")
                            elif re.search(EXPERIENCE_PATTERN, val, re.IGNORECASE):
                                raw_data["required_experience"] = val
                            # Secteur et Fonctions (mapping exact pour robustesse) - accumuler tous
                            elif val in SECTORS_AND_FUNCTIONS:
                                raw_data["sector"].append(val)
                            else:
                                uncategorized_tags.append(val)

                        # Classification des tags non catégorisés: location vs secteur
                        for tag in uncategorized_tags:
                            # Location: contient code postal (5 chiffres) ou département (- XX)
                            if re.search(r"\d{5}", tag) or re.search(
                                r"-\s*\d{1,2}", tag
                            ):
                                raw_data["location"] = tag
                            # Secteur: reste (pas de pattern location) - ajouter à la liste
                            elif len(raw_data["sector"]) == 0:
                                raw_data["sector"].append(tag)
                            elif raw_data["location"] is None:
                                raw_data["location"] = tag

                        # ===== CONTENU (AVANT de changer d'onglet) =====
                        # Description principale - EXTRAIRE AVANT de cliquer sur L'entreprise
                        description_text = ""
                        try:
                            # Essayer de cliquer sur "Voir plus" si le bouton existe
                            try:
                                show_more_btn = driver.find_element(
                                    By.XPATH,
                                    "//button[contains(text(), 'Voir plus') and ancestor::section]",
                                )
                                driver.execute_script(
                                    "arguments[0].click();", show_more_btn
                                )
                                time.sleep(0.5)
                            except Exception:
                                pass

                            # Extraire la description
                            desc_elements = driver.find_elements(
                                By.XPATH,
                                "//div[@data-truncate-text-target='content']//p | //section//div[@class]//p[contains(@class, 'tw-typo-long-m')]",
                            )
                            if desc_elements:
                                description_text = desc_elements[0].text.strip()
                        except Exception:
                            pass

                        # Missions et profil
                        job_mission = ""
                        job_profile = ""

                        # Extraction des sections "Le profil recherché" - format BUTTON (ancien)
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
                            job_profile = profil_content.text
                        except Exception:
                            # Format DETAILS (nouveau) - balise HTML5 <details>
                            try:
                                profile_details = driver.find_element(
                                    By.XPATH,
                                    "//summary[contains(., 'Le profil recherché')]/ancestor::details",
                                )
                                # Cliquer sur la balise summary pour dérouler
                                summary = profile_details.find_element(
                                    By.CSS_SELECTOR, "summary"
                                )
                                driver.execute_script("arguments[0].click();", summary)
                                time.sleep(0.5)

                                # Extraire le contenu du profil
                                profil_content = profile_details.find_element(
                                    By.CSS_SELECTOR, "p.tw-typo-long-m"
                                )
                                job_profile = profil_content.text
                            except Exception:
                                pass

                        # Agrégation de la description
                        raw_data["description"] = description_text
                        raw_data["job_mission"] = job_mission if job_mission else None
                        raw_data["job_profile"] = job_profile if job_profile else None

                        # ===== COMPÉTENCES =====
                        # Note: job_profile contient le profil complet, competences reste None
                        raw_data["competences"] = None

                        # ===== DATE DE PUBLICATION =====
                        raw_data["date_publication"] = None
                        try:
                            # Chercher le span contenant "Publiée le JJ/MM/YYYY"
                            date_span = driver.find_element(
                                By.XPATH,
                                "//span[contains(@class, 'tw-typo-xs') and contains(text(), 'Publiée le')]",
                            )
                            date_text = date_span.text.strip()
                            # Exemple: "Publiée le 06/03/2026 - Réf : 3863559/27848310 DSF/44N"
                            match = re.search(
                                r"Publiée le (\d{2}/\d{2}/\d{4})", date_text
                            )
                            if match:
                                date_str = match.group(1)  # "06/03/2026"
                                # Convertir JJ/MM/YYYY en ISO format YYYY-MM-DDTHH:MM:SSZ
                                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                                raw_data["date_publication"] = (
                                    date_obj.isoformat() + "Z"
                                )
                        except Exception as e:
                            logger.debug(f"Erreur extraction date publication: {e}")

                        # ===== CONVERSION DES LISTES EN STRINGS =====
                        # Convertir la liste de secteurs/fonctions en string avec séparateur
                        if raw_data["sector"]:
                            raw_data["sector"] = " - ".join(raw_data["sector"])
                        else:
                            raw_data["sector"] = None

                        # ===== ENTREPRISE =====
                        raw_data["company_size"] = None

                        # Extraction des données compagnie depuis l'onglet "L'entreprise" (optionnel)
                        try:
                            company_tab_btn = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable(
                                    (
                                        By.CSS_SELECTOR,
                                        "button[data-cy='companyTabButton']",
                                    )
                                )
                            )
                            driver.execute_script(
                                "arguments[0].click();", company_tab_btn
                            )
                            time.sleep(1)

                            # Attendre le chargement du contenu de l'onglet
                            WebDriverWait(driver, 3).until(
                                EC.visibility_of_element_located(
                                    (By.CSS_SELECTOR, "div[id='company-panel']")
                                )
                            )
                            time.sleep(0.5)

                            # Extraction de la taille de l'entreprise
                            try:
                                size_span = driver.find_element(
                                    By.XPATH,
                                    "//span[contains(text(), 'Salariés')]/following-sibling::span[contains(@class, 'tw-typo-m-bold')]",
                                )
                                raw_data["company_size"] = size_span.text.strip()
                            except Exception:
                                pass

                            # Extraction de la politique de télétravail
                            try:
                                remote_span = driver.find_element(
                                    By.XPATH,
                                    "//span[contains(text(), 'Politique de télétravail')]/following-sibling::span[contains(@class, 'tw-typo-m-bold')]",
                                )
                                remote_text = remote_span.text.strip()
                                if raw_data["remote_mode"] is None:
                                    raw_data["remote_mode"] = remote_text
                            except Exception:
                                pass

                        except TimeoutException:
                            # Le bouton "L'entreprise" n'existe pas sur cette offre (c'est normal)
                            pass
                        except Exception:
                            pass

                        # ========== CONSTRUCTION DE LA ROW FINALE ==========
                        # Merge job_mission into job_profile for unified output
                        job_profile_text = clean_description(
                            raw_data.get("job_profile", "")
                        )
                        job_mission_text = clean_description(
                            raw_data.get("job_mission", "")
                        )

                        # Combine job_profile and job_mission (if both exist)
                        if job_mission_text and job_profile_text:
                            combined_profile = (
                                f"{job_mission_text}\n\n{job_profile_text}"
                            )
                        elif job_mission_text:
                            combined_profile = job_mission_text
                        else:
                            combined_profile = job_profile_text

                        # Parse location format "Ville - Code" to extract city, department, region
                        location_parsed = parse_location_hellowork(
                            raw_data.get("location")
                        )

                        row = {
                            # IDENTIFIANTS
                            "id": job_id,
                            "url": link,
                            "source": "HelloWork",
                            "date_publication": raw_data.get("date_publication"),
                            "date_scraping": raw_data.get("date_scraping"),
                            # POSTE
                            "title": raw_data.get("title", "Sans titre"),
                            "sector": raw_data.get("sector"),
                            "contract_type": raw_data.get("contract_type"),
                            "remote_mode": raw_data.get("remote_mode"),
                            # LOCALISATION
                            "city": location_parsed.get("city"),
                            "department": location_parsed.get("department"),
                            "region": location_parsed.get("region"),
                            # ENTREPRISE
                            "company": raw_data.get("company", "Non spécifié"),
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
                            "job_profile": combined_profile,
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
        logger.debug(
            f"Keywords reçus par run_hw_scraper : {keywords_to_fetch} (type: {type(keywords_to_fetch)})"
        )
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
    keywords_to_test = ["Data Scientist", "Data Engineer", "Data Analyst"]
    offers = run_hw_scraper(
        keywords_to_test, max_offres_per_kw=3, save_to_db=True, headless=True
    )

    print(f"\nRésultat : {len(offers)} offre(s) traité(es)")
    print(offers[0] if offers else "Aucune offre trouvée")
