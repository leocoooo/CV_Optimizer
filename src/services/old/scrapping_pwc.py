import pandas as pd
import time
import uuid
import json
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def extract_json_stricte(text):
    """Extrait le JSON en coupant les caractères parasites à la fin."""
    start_idx = text.find('{')
    if start_idx == -1: 
        return None
    text = text[start_idx:]
    for i in range(len(text), 0, -1):
        try:
            candidate = text[:i]
            if candidate.endswith('}'):
                return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None

def scrape_pwc_massive(keywords):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=service, options=options)
    all_data = []
    # Set pour garder une trace globale des offres déjà scrapées (évite les doublons entre mots-clés)
    scraped_job_ids = set()
    nom_fichier = "offre_pwc.csv"

    try:
        for kw in keywords:
            print(f"\n--- 🔎 Recherche PwC : {kw} ---")
            driver.get("https://carrieres.pwc.fr/fr/jeunes-diplomes-offres.html")
            
            # Cookies (attente courte si déjà accepté)
            try:
                WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "axeptio_btn_acceptAll"))).click()
            except Exception: 
                pass

            # Formulaire
            try:
                search_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "input-job-search")))
                search_input.clear()
                search_input.send_keys(kw)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", search_input)
                
                search_btn = driver.find_element(By.NAME, "submitCriteriaSearch")
                driver.execute_script("arguments[0].click();", search_btn)
                time.sleep(5)
            except Exception as e:
                print(f"❌ Erreur formulaire pour {kw}: {e}")
                continue

            # Identification des liens uniques sur la page
            raw_links = [a.get_attribute("href") for a in driver.find_elements(By.XPATH, "//a[contains(@href, 'presentation.html')]")]
            
            links_to_process = []
            for link in raw_links:
                match_id = re.search(r'wdjobreqid=([A-Z0-9]+)', link)
                if match_id:
                    job_id = match_id.group(1)
                    # Si l'ID n'a jamais été vu (ni sur ce mot-clé, ni sur les précédents)
                    if job_id not in scraped_job_ids:
                        scraped_job_ids.add(job_id)
                        links_to_process.append(link)

            print(f"✅ {len(links_to_process)} nouvelles offres uniques trouvées.")

            for i, link in enumerate(links_to_process):
                print(f"📖 [{i+1}/{len(links_to_process)}] Extraction : {link.split('jobtitle=')[-1][:30]}...")
                driver.get(link)
                time.sleep(3)

                try:
                    source = driver.page_source
                    match = re.search(r'var jsondata = (\{.*)', source, re.DOTALL)
                    
                    if match:
                        data = extract_json_stricte(match.group(1))
                        if data:
                            titre_complet = data.get("title", "")
                            parties = [p.strip() for p in titre_complet.split('|')]
                            
                            # Logique demandée : 1er = Titre, 3ème = Contrat
                            titre_propre = parties[0] if len(parties) >= 1 else titre_complet
                            type_contrat = parties[2] if len(parties) >= 3 else "N/A"

                            row = {
                                "id": str(uuid.uuid4()),
                                "titre": titre_propre,
                                "entreprise": "PwC",
                                "date_recuperation": time.strftime("%d/%m/%Y"),
                                "location": data.get("location"),
                                "description": BeautifulSoup(data.get("desc", ""), "html.parser").get_text(separator=' ').strip(),
                                "type_contrat": type_contrat,
                                "url": link,
                                "source": "PwC",
                                "mot_cle_origine": kw 
                            }
                            
                            all_data.append(row)
                            
                            pd.DataFrame(all_data).to_csv(nom_fichier, index=False, encoding='utf-8-sig')
                except Exception as e:
                    print(f"   ∟ Erreur : {e}")

    finally:
        driver.quit()
        print(f"\nScraping terminé ! Total d'offres uniques PwC : {len(all_data)}")
        print(f" Fichier disponible : {os.path.abspath(nom_fichier)}")

if __name__ == "__main__":
    keywords_list = [
        "Data Scientist", "Data Analyst", "Data Engineer", "Machine Learning Engineer",
        "Architecte Big Data", "Business Intelligence", "Data Manager",
        "Développeur Python", "Développeur Fullstack", "Développeur Backend",
        "Développeur Frontend", "Software Engineer", "DevOps", "Cloud Engineer",
        "Architecte Cloud", "Site Reliability Engineer", "Spark", "Kubernetes",
        "AWS", "Azure", "SQL", "NoSQL"
    ]
    
    scrape_pwc_massive(keywords_list)