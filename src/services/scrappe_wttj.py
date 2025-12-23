import pandas as pd
import time
import json
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

def get_existing_ids(conn):
    """Récupère les IDs déjà présents en base pour éviter le double scrap."""
    query = "SELECT id FROM jobs_france_travail" # Adapte le nom de ta table
    return set(pd.read_sql(query, conn)['id'].tolist())

def scrape_wttj_json_strategy(keywords, max_offres_per_kw=10, db_connection=None):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # Mode sans interface pour la prod
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Récupération des IDs déjà scrapés (en base + run actuel)
    existing_ids = get_existing_ids(db_connection) if db_connection else set()
    all_data = []

    try:
        for kw in keywords:
            print(f"\n--- Recherche WTTJ : {kw} ---")
            count_for_kw = 0
            page = 1
            
            while count_for_kw < max_offres_per_kw:
                url_search = f"https://www.welcometothejungle.com/fr/jobs?query={kw.replace(' ', '%20')}&page={page}"
                driver.get(url_search)
                
                # 1. Attente des cartes d'offres
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-testid='search-results-list-item-wrapper']"))
                    )
                except:
                    print(f"Fin des résultats pour {kw} à la page {page}.")
                    break

                # 2. On récupère toutes les cartes de la page
                cards = driver.find_elements(By.CSS_SELECTOR, "li[data-testid='search-results-list-item-wrapper']")
                
                page_links = []
                for card in cards:
                    # Extraction rapide du lien pour identifier l'offre
                    try:
                        link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                        # Note : Idéalement, on génère l'ID ici si les infos (titre/entreprise) 
                        # sont visibles dans la carte pour éviter le driver.get(link)
                        page_links.append(link)
                    except:
                        continue

                # 3. Scraping des détails
                for link in page_links:
                    if count_for_kw >= max_offres_per_kw:
                        break
                    
                    try:
                        driver.get(link)
                        time.sleep(2) # Temps de chargement JSON-LD
                        
                        script_element = driver.find_element(By.XPATH, "//script[@type='application/ld+json']")
                        job_data = json.loads(script_element.get_attribute("innerHTML"))
                        
                        # Génération de l'ID déterministe
                        company = job_data.get("hiringOrganization", {}).get("name", "Inconnu")
                        title = job_data.get("title", "Sans titre")
                        location = job_data.get("jobLocation", [{}])[0].get("address", {}).get("addressLocality", "N/C")
                        
                        job_id = hashlib.sha256(f"{company.lower()}|{title.lower()}|{location.lower()}".encode()).hexdigest()

                        # --- VÉRIFICATION DÉDOUBLONNAGE ---
                        if job_id in existing_ids:
                            print(f"Skipping : {title} (Déjà en base)")
                            continue

                        # Extraction du reste des données (ta logique précédente...)
                        row = {
                            "id": job_id,
                            "title": title,
                            "company": company,
                            "location": location,
                            "url": link,
                            "source": "Welcome to the Jungle",
                            "description": job_data.get("description"),
                            "creation_date": job_data.get("datePosted"),
                            "contract_type": job_data.get("employmentType"),
                            "required_experience": None,
                            "contact": None,
                            "actualisation_date": None,
                        }

                        all_data.append(row)
                        existing_ids.add(job_id) # Ajout au set pour éviter les doublons inter-mots-clés
                        count_for_kw += 1
                        print(f"[{count_for_kw}/{max_offres_per_kw}] Scrapé : {title}")

                    except Exception as e:
                        print(f"Erreur sur {link}: {e}")

                page += 1 # Incrémenter la page de recherche si on n'a pas atteint le quota

    finally:
        driver.quit()

    return pd.DataFrame(all_data)

if __name__ == "__main__":

    load_dotenv()

    # 1. Récupération de l'URL de la base de données
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("Erreur : DATABASE_URL non trouvée dans le fichier .env")
    else:
        # Correction de l'URL si nécessaire (compatibilité SQLAlchemy)
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        try:
            # 2. Création de l'engine
            engine = create_engine(db_url)
            print("Connexion à PostgreSQL (via DATABASE_URL) établie.")
            
            # 3. Paramètres de recherche
            keywords_to_test = ["Data Engineer", "Machine Learning"]
            limit_per_keyword = 3 # Test rapide
            
            # 4. Lancement du scrap
            # On passe l'engine à ta fonction pour qu'elle puisse vérifier les IDs
            print("Lancement du test sur WTTJ...")
            df_results = scrape_wttj_json_strategy(
                keywords=keywords_to_test, 
                max_offres_per_kw=limit_per_keyword, 
                db_connection=engine
            )

            # 5. Synthèse
            if not df_results.empty:
                print(f"\nScraping terminé : {len(df_results)} nouvelles offres trouvées.")
                print(df_results[['title', 'company', 'id']].head())
                
            else:
                print("\nAucune nouvelle offre à traiter.")

        except Exception as e:
            print(f"Erreur lors de l'exécution : {e}")