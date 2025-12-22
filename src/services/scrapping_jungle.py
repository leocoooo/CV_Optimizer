import pandas as pd
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.services.utils import get_job_id


def scrape_wttj_json_strategy(keywords):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    # utilisation d'un agent pour pas se faire bloquer
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=service, options=options)
    all_data = []

    try:
        for kw in keywords:
            print(f"Recherche WTTJ : {kw}")
            url_search = f"https://www.welcometothejungle.com/fr/jobs?query={kw.replace(' ', '%20')}&page=1"
            driver.get(url_search)
            
            # Attente de la liste des offres
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-testid='search-results-list-item-wrapper']"))
            )
            links = [c.find_element(By.TAG_NAME, "a").get_attribute("href") for c in driver.find_elements(By.CSS_SELECTOR, "li[data-testid='search-results-list-item-wrapper']")]

            for link in links:
                try:
                    driver.get(link)
                    # Attente que la page soit stabilisée
                    time.sleep(3)
                    driver.execute_script("window.scrollTo(0, 500);") # Scroll pour activer le JS

                    # --- STRATÉGIE JSON-LD (La plus stable) ---
                    # On récupère le bloc script que tu as montré dans ton message
                    script_element = driver.find_element(By.XPATH, "//script[@type='application/ld+json']")
                    job_data = json.loads(script_element.get_attribute("innerHTML"))

                    # Extraction sécurisée des variables
                    company = job_data.get("hiringOrganization", {}).get("name") or "Inconnu"
                    title = job_data.get("title") or "Sans titre"
                    locations = job_data.get("jobLocation", [])
                    location_city = "N/C"
                    if locations and isinstance(locations, list):
                        location_city = locations[0].get("address", {}).get("addressLocality") or "N/C"

                    # Initialisation de la ligne avec tes colonnes
                    row = {
                        "id": get_job_id(company, title, location_city), # ID déterministe
                        "title": title,
                        "company": company,
                        "location": location_city,
                        "description": job_data.get("description"),
                        "date_creation": job_data.get("datePosted"),
                        "date_actualisation": None, # à trouver si possible
                        "type_contrat": job_data.get("employmentType"),
                        "experience_exigee": None,
                        "contact": None, # à trouver si possible
                        "source": "Welcome to the Jungle",
                        "url": link,
                        "created_at" : pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                    }

                    # --- COMPLÉMENT POUR LES COMPÉTENCES (Via les badges) ---
                    try:
                        skills = driver.find_elements(By.CSS_SELECTOR, "div.sc-fibHhp.jdfMTT span")
                        row["competences"] = ", ".join([s.text for s in skills]) if skills else None
                    except Exception as e:
                        print(f" Erreur lors de la récupération des compétences : {e}")
                        row["competences"] = None

                    all_data.append(row)
                    print(f"Succès : {row['titre']} chez {row['entreprise']}")

                except Exception as e:
                    print(f"Échec sur {link.split('/')[-1]} : Structure non détectée. Erreur : {e}")
                    continue

    finally:
        driver.quit()

    return pd.DataFrame(all_data)

if __name__ == "__main__":

    keywords = ["Data Scientist",
                "Data Analyst"]
    
    df = scrape_wttj_json_strategy(keywords)
    if not df.empty:
        print(df[['titre', 'entreprise', 'type_contrat']].head())
        df.to_csv("data_scrapping/main_offres_welcome_to_jungle.csv", index=False)