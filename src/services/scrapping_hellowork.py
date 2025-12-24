import pandas as pd
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def scrape_hellowork_safe(keywords, max_pages=29):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=service, options=options)
    all_data = []
    nom_fichier = "data_scrapping/offre_hellowork.csv" 
    processed_ids = set()

    try:
        driver.get("https://www.hellowork.com/fr-fr/")
        time.sleep(1)

        # Cookies
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Tout accepter']"))).click()
            time.sleep(1)
        except:  
            pass

        for kw in keywords:
            print(f"Keyword: {kw}")
            try:
                search_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "k")))
                search_input.clear()
                search_input.send_keys(kw)
                time.sleep(0.5)
                search_input.send_keys(Keys.ENTER)
                time.sleep(2)
            except: 
                continue

            for page in range(1, max_pages + 1):
                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-cy='offerTitle']")))
                    offer_elements = driver.find_elements(By.CSS_SELECTOR, "a[data-cy='offerTitle']")
                    links = [el.get_attribute("href") for el in offer_elements]
                except: 
                    break

                for link in links:
                    match_id = re.search(r'/(\d+)\.html', link)
                    job_id = match_id.group(1) if match_id else link
                    
                    if job_id in processed_ids: 
                        continue
                    processed_ids.add(job_id)

                    driver.get(link)
                    time.sleep(1.5)

                    row = {
                        "id": job_id,
                        "title": "N/A", 
                        "company": "N/A", 
                        "creation_date": "N/A",
                        "location": "N/A", 
                        "contract_type": "N/A", 
                        "experience": "N/A",
                        "description": "N/A", 
                        "url": link, 
                        "source": "Hellowork"
                    }

                    try:
                        row["title"] = driver.find_element(By.CSS_SELECTOR, "[data-cy='jobTitle']").text
                        try: 
                            row["company"] = driver.find_element(By.CSS_SELECTOR, "p.tw-typo-s.tw-inline").text
                        except: 
                            pass
                        
                        try:
                            date_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Publiée le')]")
                            date_text = date_element.text
                            match_date = re.search(r'(\d{2}/\d{2}/\d{4})', date_text)
                            if match_date:
                                row["creation_date"] = match_date.group(1)
                        except Exception as e:
                            row["creation_date"] = "N/A"

                        # Tags (Contract, Experience, Location)
                        tags = driver.find_elements(By.CSS_SELECTOR, "li.tw-tag-secondary-s")
                        for tag in tags:
                            val = tag.text
                            if "ans" in val.lower() or "exp." in val.lower(): 
                                row["experience"] = val
                            elif val in ["CDI", "CDD", "Alternance", "Stage", "Intérim"]: 
                                row["contract_type"] = val
                            else: 
                                if row["location"] == "N/A": row["location"] = val

                        # Description
                        try:
                            desc = driver.find_element(By.CSS_SELECTOR, "div[data-truncate-text-target='content']")
                            row["description"] = " ".join(desc.text.split())
                        except: 
                            pass

                        # Skills
                        try:
                            bouton_profil = driver.find_element(By.XPATH, "//span[contains(text(), 'Le profil recherché')]/ancestor::button")
                            driver.execute_script("arguments[0].click();", bouton_profil)
                            time.sleep(0.5)
                            profil_content = driver.find_element(By.CSS_SELECTOR, "#collapsed-content p.tw-typo-long-m")
                            competences_text = " ".join(profil_content.text.split())
    
                            if row["description"] != "N/A":
                                row["description"] = row["description"] + " " + competences_text
                            else:
                                row["description"] = competences_text
                        except: 
                            pass

                        all_data.append(row)
                        # Progressive save
                        pd.DataFrame(all_data).to_csv(nom_fichier, index=False, encoding='utf-8-sig')
                        
                    except Exception as e:
                        print(f"Extraction error: {e}")
                    
                    driver.back()
                    time.sleep(1) 

                # Pagination
                try:
                    next_page_val = str(page + 1)
                    next_btn = driver.find_element(By.CSS_SELECTOR, f"button[name='p'][value='{next_page_val}']")
                    driver.execute_script("arguments[0].click();", next_btn)
                    time.sleep(2) 
                except: 
                    break

    finally:
        driver.quit()
        print(f"Scraping completed. File: {os.path.abspath(nom_fichier)}")

if __name__ == "__main__":
    keywords_list = ["Data Scientist"]
    scrape_hellowork_safe(keywords_list)
