from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FranceTravailScraper:
    def __init__(self, headless=False):
        self.base_url = "https://pro.francetravail.fr"
        self.search_url = f"{self.base_url}/recherche-profil/rechercheprofil"
        
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        
    def handle_cookie_popup(self):
        try:
            accept_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tout accepter') or contains(text(), 'accepter')]"))
            )
            accept_button.click()
            logging.info("Cookies acceptés")
            time.sleep(1)
        except TimeoutException:
            try:
                continue_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continuer sans accepter')]")
                continue_button.click()
                logging.info("Continué sans accepter les cookies")
                time.sleep(1)
            except:
                logging.info("Pas de popup de cookies détectée")
    
    def extract_text_safe(self, element, default=""):
        try:
            return element.get_text(strip=True) if element else default
        except:
            return default
    
    def extract_competences(self, soup):
        competences = {
            'savoirs_savoir_faire': [],
            'savoir_etre': [],
            'langues': [],
            'permis': []
        }
        
        for tag in soup.select('ul.list-inline-tag li.tag.competence'):
            name = self.extract_text_safe(tag.select_one('.tag-name'))
            level = self.extract_text_safe(tag.select_one('.tag-level'))
            if name:
                competences['savoirs_savoir_faire'].append({
                    'nom': name,
                    'niveau': level.strip('()')
                })
        
        for tag in soup.select('ul.list-inline-tag li.tag.qualite'):
            name = self.extract_text_safe(tag.select_one('.tag-name'))
            if name:
                competences['savoir_etre'].append(name)
        
        for tag in soup.select('ul.list-inline-tag li.tag.langue'):
            name = self.extract_text_safe(tag.select_one('.tag-name'))
            level = self.extract_text_safe(tag.select_one('.tag-level'))
            if name:
                competences['langues'].append({
                    'langue': name,
                    'niveau': level.strip('()')
                })
        
        for tag in soup.select('ul.list-inline-tag li.tag.permis'):
            name = self.extract_text_safe(tag.select_one('.tag-name'))
            if name:
                competences['permis'].append(name)
        
        return competences
    
    def extract_experiences(self, soup):
        experiences = []
        for exp in soup.select('li.event.experience'):
            title_elem = exp.select_one('h4.title')
            date_elem = exp.select_one('.date')
            place_elem = exp.select_one('.place')
            
            description = ""
            desc_paragraphs = exp.select('.collapse-container > p')
            if desc_paragraphs:
                description = ' '.join([self.extract_text_safe(p) for p in desc_paragraphs])
            
            exp_data = {
                'titre': self.extract_text_safe(title_elem),
                'periode': self.extract_text_safe(date_elem),
                'entreprise': self.extract_text_safe(place_elem),
                'description': description,
                'competences': []
            }
            
            for comp in exp.select('.collapse-container ul.list-inline-tag li.tag'):
                name = self.extract_text_safe(comp.select_one('.tag-name'))
                level = self.extract_text_safe(comp.select_one('.tag-level'))
                if name:
                    exp_data['competences'].append({
                        'nom': name,
                        'niveau': level.strip('()')
                    })
            
            if exp_data['titre'] or exp_data['description']:
                experiences.append(exp_data)
        
        return experiences
    
    def extract_formations(self, soup):
        formations = []
        for form in soup.select('li.event.formation'):
            title_elem = form.select_one('h4.title')
            date_elem = form.select_one('.date')
            place_elem = form.select_one('.place')
            
            description = ""
            desc_paragraphs = form.select('.collapse-container > p')
            if desc_paragraphs:
                description = ' '.join([self.extract_text_safe(p) for p in desc_paragraphs])
            
            form_data = {
                'titre': self.extract_text_safe(title_elem),
                'annee': self.extract_text_safe(date_elem),
                'niveau': self.extract_text_safe(place_elem),
                'description': description
            }
            
            if form_data['titre'] or form_data['description']:
                formations.append(form_data)
        
        return formations
    
    def extract_profile_from_modal(self, profile_id):
        try:
            modal_html = self.driver.page_source
            soup = BeautifulSoup(modal_html, 'html.parser')
            
            modal = soup.find('div', {'id': 'PopinDetails-RecrutementCompetences'})
            if not modal:
                logging.warning(f"Modal non trouvée pour le profil {profile_id}")
                return None
            
            titre_elem = modal.select_one('h2.name span.text-entreprise')
            dispo_elem = modal.select_one('.media-body > p')
            date_elem = modal.select_one('.state p.italic .emphasis')
            presentation_elem = modal.select_one('blockquote')
            
            profile_data = {
                'id': profile_id,
                'titre_profil': self.extract_text_safe(titre_elem),
                'disponibilite': '',
                'date_maj': self.extract_text_safe(date_elem),
                'presentation': self.extract_text_safe(presentation_elem),
                'points_forts': [],
                'experiences': self.extract_experiences(modal),
                'formations': self.extract_formations(modal),
                'competences': self.extract_competences(modal)
            }
            
            if dispo_elem:
                dispo_text = self.extract_text_safe(dispo_elem)
                if 'Disponibilité' in dispo_text:
                    profile_data['disponibilite'] = dispo_text.replace('Disponibilité', '').strip()
            
            for tag in modal.select('.media-body-more ul.list-inline-tag li.tag'):
                point = self.extract_text_safe(tag.select_one('.tag-name'))
                if point:
                    profile_data['points_forts'].append(point)
            
            return profile_data
            
        except Exception as e:
            logging.error(f"Erreur extraction profil {profile_id}: {str(e)}")
            return None
    
    def click_profile(self, profile_button):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", profile_button)
            time.sleep(0.5)
            
            self.driver.execute_script("arguments[0].click();", profile_button)
            
            self.wait.until(
                EC.visibility_of_element_located((By.ID, "PopinDetails-RecrutementCompetences"))
            )
            time.sleep(1.5)
            
            return True
        except Exception as e:
            logging.error(f"Erreur lors du clic sur le profil: {str(e)}")
            return False
    
    def close_modal(self):
        try:
            close_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.modal-details-close"))
            )
            self.driver.execute_script("arguments[0].click();", close_button)
            time.sleep(1)
        except Exception as e:
            logging.error(f"Erreur fermeture modal: {str(e)}")
    
    def search_and_extract(self, query="Data", max_profiles=10):
        profiles = []
        
        try:
            logging.info(f"Accès à la page de recherche")
            self.driver.get(self.search_url)
            
            self.handle_cookie_popup()
            
            time.sleep(2)
            
            logging.info(f"Recherche avec le mot-clé: {query}")
            
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='keywords'], input[name*='motsCles']"))
            )
            search_input.clear()
            search_input.send_keys(query)
            search_input.send_keys(Keys.RETURN)
            
            time.sleep(3)
            
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.lienclic-profil"))
            )
            
            profile_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.lienclic-profil")
            total_found = len(profile_buttons)
            logging.info(f"{total_found} profils trouvés sur la page")
            
            for i in range(min(max_profiles, total_found)):
                try:
                    profile_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.lienclic-profil")
                    button = profile_buttons[i]
                    
                    profile_id = button.get_attribute('data-num-profil')
                    profile_title = button.text.strip()
                    
                    logging.info(f"Traitement profil {i+1}/{min(max_profiles, total_found)}: {profile_title} (ID: {profile_id})")
                    
                    if self.click_profile(button):
                        profile_data = self.extract_profile_from_modal(profile_id)
                        
                        if profile_data:
                            profiles.append(profile_data)
                            logging.info(f"Profil {profile_id} extrait avec succès")
                        
                        self.close_modal()
                        time.sleep(1)
                    
                except Exception as e:
                    logging.error(f"Erreur lors du traitement du profil {i+1}: {str(e)}")
                    continue
            
        except Exception as e:
            logging.error(f"Erreur lors de la recherche: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return profiles
    
    def save_to_json(self, profiles, filename="profiles_francetravail.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        logging.info(f"{len(profiles)} profils sauvegardés dans {filename}")
    
    def close(self):
        self.driver.quit()

def main():
    scraper = FranceTravailScraper(headless=False)
    
    try:
        profiles = scraper.search_and_extract(query="Data", max_profiles=5)
        
        if profiles:
            scraper.save_to_json(profiles)
            print(f"\n{len(profiles)} profils extraits avec succès")
            print(f"\nAperçu du premier profil:")
            print(json.dumps(profiles[0], ensure_ascii=False, indent=2))
        else:
            print("Aucun profil extrait")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()