from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import json
import time
import logging
import argparse

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
        """Gere la popup de cookies de maniere aggressive"""
        try:
            logging.info("Gestion de la popup de cookies...")
            time.sleep(2)
            
            try:
                self.driver.execute_script("""
                    var cookieElements = document.querySelectorAll('pe-cookies');
                    cookieElements.forEach(function(el) {
                        el.remove();
                    });
                    
                    var overlays = document.querySelectorAll('.modal-backdrop, .overlay, [class*="cookie"]');
                    overlays.forEach(function(el) {
                        el.remove();
                    });
                    
                    document.body.style.overflow = 'auto';
                    document.body.style.pointerEvents = 'auto';
                """)
                logging.info("Elements cookies supprimes")
                time.sleep(1)
                return True
            except Exception as e:
                logging.info(f"Suppression cookies echouee: {e}")
            
            return False
            
        except Exception as e:
            logging.error(f"Erreur gestion cookies: {str(e)}")
            return False
    
    def force_remove_overlays(self):
        """Force la suppression des overlays qui bloquent les clics"""
        try:
            self.driver.execute_script("""
                var overlays = document.querySelectorAll('pe-cookies, .modal-backdrop, .overlay, [style*="z-index"]');
                overlays.forEach(function(el) {
                    try {
                        var zIndex = window.getComputedStyle(el).zIndex;
                        if (zIndex && parseInt(zIndex) > 1000) {
                            el.remove();
                        }
                    } catch(e) {}
                });
                
                document.body.style.overflow = 'auto';
                document.body.style.pointerEvents = 'auto';
                document.documentElement.style.overflow = 'auto';
            """)
            logging.info("Overlays forces supprimes")
        except Exception as e:
            logging.info(f"Force remove overlays echoue: {e}")
    
    def search_profiles(self, query="Data"):
        """Effectue la recherche avec le mot-cle"""
        try:
            logging.info(f"Recherche avec le mot-cle: '{query}'")
            
            self.force_remove_overlays()
            
            search_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "token-input-champsMultitagQuoi"))
            )
            logging.info("Champ de recherche trouve")
            
            self.driver.execute_script("arguments[0].focus();", search_input)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", search_input)
            time.sleep(0.5)
            
            search_input.clear()
            time.sleep(0.3)
            
            for char in query:
                search_input.send_keys(char)
                time.sleep(0.1)
            
            logging.info(f"Mot-cle '{query}' saisi")
            time.sleep(2)
            
            clicked = False
            try:
                dropdown = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.ID, "champsMultitagQuoiDivAutocomplete"))
                )
                logging.info("Dropdown visible")
                
                time.sleep(0.5)
                
                all_li = self.driver.find_elements(By.XPATH, 
                    "//div[@id='champsMultitagQuoiDivAutocomplete']//li")
                
                logging.info(f"Nombre de suggestions: {len(all_li)}")
                
                for idx, li in enumerate(all_li):
                    try:
                        li_text = li.text
                        logging.info(f"  Suggestion {idx}: '{li_text}'")
                        
                        if 'Ajouter' in li_text and query in li_text:
                            logging.info(f"Clic sur 'Ajouter : {query}'")
                            self.driver.execute_script("arguments[0].click();", li)
                            clicked = True
                            time.sleep(2)
                            break
                    except:
                        continue
                
            except TimeoutException:
                logging.warning("Dropdown non visible")
            
            if not clicked:
                logging.warning("Utilisation de FLECHE BAS + ENTREE")
                search_input.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.3)
                search_input.send_keys(Keys.RETURN)
                time.sleep(2)
            
            try:
                search_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "lancerRechercheCv"))
                )
                
                self.driver.execute_script("arguments[0].click();", search_button)
                logging.info("Clic sur 'Rechercher'")
                time.sleep(4)
                
            except Exception as e:
                logging.error(f"Erreur clic bouton rechercher: {e}")
                return False
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.result-list li.cv-result"))
                )
                logging.info("Resultats charges")
                
                self.force_remove_overlays()
                time.sleep(2)
                return True
            except TimeoutException:
                logging.error("Timeout: aucun resultat")
                self.driver.save_screenshot("debug_no_results.png")
                return False
            
        except Exception as e:
            logging.error(f"Erreur recherche: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_text_safe(self, element, default=""):
        """Extraction securisee de texte"""
        try:
            return element.get_text(strip=True) if element else default
        except:
            return default
    
    def extract_competences(self, soup):
        """Extrait les competences du profil"""
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
        """Extrait les experiences professionnelles"""
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
        """Extrait les formations"""
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
        """Extrait les donnees d'un profil depuis la modal ouverte"""
        try:
            time.sleep(1.5)
            
            modal_html = self.driver.page_source
            soup = BeautifulSoup(modal_html, 'html.parser')
            
            modal = soup.find('div', {'id': 'PopinDetails-RecrutementCompetences'})
            if not modal:
                modal = soup.find('div', {'class': 'modal-content'})
                
            if not modal:
                logging.warning(f"Modal non trouvee pour {profile_id}")
                return None
            
            titre_elem = modal.select_one('h2.name span.text-entreprise, h2.name')
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
                if 'Disponibilite' in dispo_text:
                    profile_data['disponibilite'] = dispo_text.replace('Disponibilite', '').strip()
                else:
                    profile_data['disponibilite'] = dispo_text
            
            for tag in modal.select('.media-body-more ul.list-inline-tag li.tag'):
                point = self.extract_text_safe(tag.select_one('.tag-name'))
                if point:
                    profile_data['points_forts'].append(point)
            
            logging.info(f"Profil {profile_id} extrait: {profile_data['titre_profil']}")
            return profile_data
            
        except Exception as e:
            logging.error(f"Erreur extraction profil {profile_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def click_profile(self, profile_button):
        """Clique sur un profil avec gestion agressive des overlays"""
        try:
            self.force_remove_overlays()
            time.sleep(0.5)
            
            self.driver.execute_script("""
                arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
            """, profile_button)
            time.sleep(0.5)
            
            try:
                profile_button.click()
                logging.info("Clic normal reussi")
            except:
                logging.info("Clic JavaScript")
                self.driver.execute_script("arguments[0].click();", profile_button)
            
            modal_selectors = [
                (By.ID, "PopinDetails-RecrutementCompetences"),
                (By.CSS_SELECTOR, ".modal-content"),
                (By.CSS_SELECTOR, "div[id*='PopinDetails']")
            ]
            
            modal_opened = False
            for by_type, selector in modal_selectors:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((by_type, selector))
                    )
                    logging.info(f"Modal ouverte (selector: {selector})")
                    modal_opened = True
                    break
                except TimeoutException:
                    continue
            
            if not modal_opened:
                logging.error("Modal non ouverte")
                self.driver.save_screenshot("debug_modal_not_opened.png")
                return False
            
            time.sleep(1)
            return True
            
        except Exception as e:
            logging.error(f"Erreur clic profil: {str(e)}")
            import traceback
            traceback.print_exc()
            self.driver.save_screenshot("debug_click_error.png")
            return False
    
    def close_modal(self):
        """Ferme la modal de profil"""
        try:
            close_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.modal-details-close, button.close"))
            )
            self.driver.execute_script("arguments[0].click();", close_button)
            time.sleep(1)
            logging.info("Modal fermee")
        except Exception as e:
            logging.error(f"Erreur fermeture modal: {str(e)}")
            try:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                logging.info("Modal fermee avec ESC")
            except:
                pass
    
    def search_and_extract(self, query="Data", max_profiles=10):
        """Workflow complet: recherche et extraction des profils"""
        profiles = []
        extracted_ids = set()
        
        try:
            logging.info("Acces a la page de recherche...")
            self.driver.get(self.search_url)
            time.sleep(3)
            
            self.handle_cookie_popup()
            
            if not self.search_profiles(query):
                logging.error("Echec de la recherche")
                return profiles
            
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.lienclic-profil"))
                )
            except TimeoutException:
                logging.error("Aucun profil trouve")
                self.driver.save_screenshot("debug_no_profiles.png")
                return profiles
            
            self.force_remove_overlays()
            time.sleep(1)
            
            profile_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.lienclic-profil")
            total_found = len(profile_buttons)
            logging.info(f"{total_found} boutons trouves sur la page")
            
            if total_found == 0:
                logging.warning("Aucun profil a extraire")
                return profiles
            
            i = 0
            attempts = 0
            max_attempts = total_found
            
            while len(profiles) < max_profiles and attempts < max_attempts:
                try:
                    profile_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.lienclic-profil")
                    
                    if i >= len(profile_buttons):
                        logging.info("Plus de profils disponibles")
                        break
                    
                    button = profile_buttons[i]
                    profile_id = button.get_attribute('data-num-profil') or f"profil_{i+1}"
                    
                    if profile_id in extracted_ids:
                        logging.info(f"Profil {profile_id} deja extrait, passage au suivant")
                        i += 1
                        attempts += 1
                        continue
                    
                    profile_title = button.text.strip() or "Sans titre"
                    
                    logging.info(f"Profil {len(profiles)+1}/{max_profiles}: {profile_title[:50]}... (ID: {profile_id})")
                    
                    if self.click_profile(button):
                        profile_data = self.extract_profile_from_modal(profile_id)
                        
                        if profile_data:
                            profiles.append(profile_data)
                            extracted_ids.add(profile_id)
                            logging.info(f"Profil {profile_id} extrait avec succes")
                        else:
                            logging.warning(f"Profil {profile_id}: extraction echouee")
                        
                        self.close_modal()
                        time.sleep(1)
                        
                        self.force_remove_overlays()
                    else:
                        logging.warning(f"Impossible d'ouvrir le profil {i+1}")
                        time.sleep(2)
                    
                    i += 1
                    attempts += 1
                    
                except Exception as e:
                    logging.error(f"Erreur profil {i+1}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    i += 1
                    attempts += 1
                    continue
            
            logging.info(f"Extraction terminee: {len(profiles)} profils uniques recuperes")
            
        except Exception as e:
            logging.error(f"Erreur: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return profiles
    
    def save_to_json(self, profiles, filename="profiles_francetravail.json"):
        """Sauvegarde les profils en JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        logging.info(f"{len(profiles)} profils sauvegardes dans {filename}")
    
    def close(self):
        """Ferme le navigateur"""
        self.driver.quit()
        logging.info("Navigateur ferme")




def main():
    parser = argparse.ArgumentParser(description="Scraper de CV France Travail")
    parser.add_argument(
        "--query", 
        type=str, 
        default="Data", 
        help="Mot-clé de recherche (défaut: 'Data')"
    )
    parser.add_argument(
        "--max-profiles", 
        type=int, 
        default=5, 
        help="Nombre maximum de CV à extraire (défaut: 5)"
    )
    parser.add_argument(
        "--headless", 
        action="store_true", 
        help="Lancer Chrome en mode headless (sans interface graphique)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="profiles_francetravail.json", 
        help="Nom du fichier de sortie JSON"
    )
    args = parser.parse_args()

    scraper = FranceTravailScraper(headless=args.headless)
    
    try:
        profiles = scraper.search_and_extract(
            query=args.query, 
            max_profiles=args.max_profiles
        )
        
        if profiles:
            scraper.save_to_json(profiles, filename=args.output)
            print(f"SUCCES: {len(profiles)} profils uniques extraits")
            print(f"Mot-clé utilisé : '{args.query}'")
            print(f"Fichier de sortie : {args.output}")
            print(f"\nAperçu du premier profil:")
            print(json.dumps(profiles[0], ensure_ascii=False, indent=2)[:600] + "...")
        else:
            print("\nAucun profil extrait.")
    except KeyboardInterrupt:
        print("\nInterruption utilisateur")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
