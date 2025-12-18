import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class FranceTravailAPI:
    def __init__(self):
        self.client_id = os.getenv("FT_CLIENT_ID")
        self.client_secret = os.getenv("FT_CLIENT_SECRET")
        self.auth_url = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
        self.base_url = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
        self.access_token = None

    def _get_access_token(self):
        """Récupère le jeton OAuth2 avec les scopes obligatoires : api_offresdemploiv2 et o2dsoffre."""
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'api_offresdemploiv2 o2dsoffre' 
        }
        
        response = httpx.post(self.auth_url, data=data, headers=headers, timeout=10.0)        
        if response.status_code != 200:
            print(f"Erreur Auth : {response.status_code}")
            print(f"Détail : {response.text}")
            response.raise_for_status()
            
        self.access_token = response.json().get("access_token")
        return self.access_token

    def fetch_offers(self, keywords: str = "Python", range_str: str = "0-9"):
        """Récupère les offres d'emploi selon des mots-clés."""
        if not self.access_token:
            self._get_access_token()

        # Le User-Agent est parfois requis pour éviter les blocages 403
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "User-Agent": "CV-Optimizer-App/1.0" 
        }
        
        params = {
            "motsCles": keywords,
            "range": range_str
        }

        try:
            response = httpx.get(self.base_url, headers=headers, params=params)
            
            # Si le token a expiré (401), on le renouvelle et on réessaye une fois
            if response.status_code == 401:
                print("Token expiré, renouvellement en cours...")
                self._get_access_token()
                return self.fetch_offers(keywords, range_str)

            # Vérification des erreurs (403, 400, etc.)
            if response.status_code not in [200, 206]:
                print(f"Erreur API {response.status_code}")
                print(f"Réponse brute : {response.text[:250]}")
                return []

            # L'API renvoie un dictionnaire contenant une liste sous la clé 'resultats'
            # Si aucune offre n'est trouvée, la clé peut être absente, d'où le .get([], ...)
            data = response.json()
            return data.get("resultats", []) if data else []
        
        except Exception as e:
            print(f"Erreur lors de la requête : {e}")
            return []

if __name__ == "__main__":
    # Test du module
    ft_api = FranceTravailAPI()
    print("Test de récupération des offres...")
    offers = ft_api.fetch_offers(keywords="Data", range_str="0-19")
    
    print(f"{len(offers)} offres récupérées.")
    
    if offers:
        print(f"Titre de la première offre : {offers[0].get('intitule')}")
        print(f"Entreprise : {offers[0].get('entreprise', {}).get('nom', 'Non spécifiée')}")