import httpx
import hashlib
from datetime import datetime
from loguru import logger
from app.config import get_settings
from src.services.scraping_utils import clean_description


class FranceTravailAPI:
    def __init__(self):
        settings = get_settings()
        self.client_id = settings.FT_CLIENT_ID
        self.client_secret = settings.FT_CLIENT_SECRET
        self.auth_url = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
        self.base_url = (
            "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
        )
        self.access_token = None

    def _get_access_token(self):
        """Récupère le jeton OAuth2 avec les scopes obligatoires : api_offresdemploiv2 et o2dsoffre."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "api_offresdemploiv2 o2dsoffre",
        }

        response = httpx.post(self.auth_url, data=data, headers=headers, timeout=10.0)
        if response.status_code != 200:
            logger.error(f"Erreur Auth : {response.status_code}")
            logger.error(f"Détail : {response.text}")
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
            "User-Agent": "CV-Optimizer-App/1.0",
        }

        params = {"motsCles": keywords, "range": range_str}

        try:
            response = httpx.get(self.base_url, headers=headers, params=params)

            # Si le token a expiré (401), on le renouvelle et on réessaye une fois
            if response.status_code == 401:
                logger.warning("Token expiré, renouvellement en cours...")
                self._get_access_token()
                return self.fetch_offers(keywords, range_str)

            # Vérification des erreurs (403, 400, etc.)
            if response.status_code not in [200, 206]:
                logger.error(f"Erreur API {response.status_code}")
                logger.error(f"Réponse brute : {response.text[:250]}")
                return []

            # L'API renvoie un dictionnaire contenant une liste sous la clé 'resultats'
            # Si aucune offre n'est trouvée, la clé peut être absente, d'où le .get([], ...)
            data = response.json()
            return data.get("resultats", []) if data else []

        except Exception as e:
            logger.error(f"Erreur lors de la requête : {e}")
            return []


def convert_ft_offer(offer: dict) -> dict:
    """
    Convertit une offre France Travail API au format normalisé WTTJ.

    Args:
        offer: Dictionnaire d'offre provenant de l'API France Travail

    Returns:
        dict: Offre formatée au standard WTTJ interne
    """
    # Extraction des données de base
    title = offer.get("intitule", "Sans titre")
    description = offer.get("description", "")

    # Localisation
    lieu_travail = offer.get("lieuTravail", {})
    location = (
        lieu_travail.get("libelle", "N/C").split(" - ")[-1].strip()
        if lieu_travail.get("libelle")
        else "N/C"
    )

    # Entreprise
    entreprise = offer.get("entreprise", {})
    company = entreprise.get("nom", "Inconnu")

    # Type de contrat
    contract_type = offer.get("typeContratLibelle", offer.get("typeContrat", None))

    # Télétravail: extraire si "télétravail" est dans conditionsExercice
    remote_mode = None
    contexte_travail = offer.get("contexteTravail", {})
    conditions_exercice = contexte_travail.get("conditionsExercice", [])
    if conditions_exercice:
        for condition in conditions_exercice:
            if condition and "télétravail" in condition.lower():
                remote_mode = (
                    "Télétravail occasionnel"
                    if "occasion" in condition.lower()
                    else "Télétravail fréquent"
                )
                break

    # Expérience
    required_experience = offer.get("experienceLibelle", None)

    # Salaire
    salary_info = offer.get("salaire", {})
    salary = salary_info.get("libelle") if isinstance(salary_info, dict) else None

    # Compétences
    competences = None
    comp_list = offer.get("competences", [])
    if comp_list:
        comp_texts = [
            comp.get("libelle")
            for comp in comp_list
            if isinstance(comp, dict) and comp.get("libelle")
        ]
        if comp_texts:
            competences = ", ".join(
                str(text) for text in comp_texts[:10] if text
            )  # Limiter à 10

    # Langues
    languages = None
    lang_list = offer.get("langues", [])
    if lang_list:
        lang_texts = [
            lang.get("libelle")
            for lang in lang_list
            if isinstance(lang, dict) and lang.get("libelle")
        ]
        if lang_texts:
            languages = ", ".join(str(text) for text in lang_texts if text)

    # Qualités professionnelles
    soft_skills = None
    qual_list = offer.get("qualitesProfessionnelles", [])
    if qual_list:
        qual_texts = [
            qual.get("libelle")
            for qual in qual_list
            if isinstance(qual, dict) and qual.get("libelle")
        ]
        if qual_texts:
            soft_skills = ", ".join(str(text) for text in qual_texts[:5] if text)

    # Secteur
    sector = offer.get("secteurActiviteLibelle", None)

    # Nombre de postes
    nb_posts = offer.get("nombrePostes", None)

    # Génération d'ID
    company_str = str(company).lower() if company else "inconnu"
    title_str = str(title).lower() if title else "sans_titre"
    location_str = str(location).lower() if location else "n_a"
    job_id = hashlib.sha256(
        f"{company_str}|{title_str}|{location_str}".encode()
    ).hexdigest()

    # Construction de l'offre formatée
    return {
        "id": job_id,
        "url": offer.get("origineOffre", {}).get("urlOrigine", ""),
        "source": "France Travail",
        "date_publication": offer.get("dateCreation", None),
        "date_scraping": datetime.now().isoformat(),
        # POSTE
        "title": title,
        "sector": sector,
        "contract_type": contract_type,
        "remote_mode": remote_mode,
        # LOCALISATION
        "location": location,
        "location_address": None,
        "location_country": None,
        # ENTREPRISE
        "company": company,
        "company_size": None,
        # PROFIL DEMANDÉ
        "required_experience": required_experience,
        "required_education": None,
        "competences": competences,
        # RÉMUNÉRATION
        "salary": salary,
        # CONTENU
        "description": clean_description(description),
        "job_profile": None,
        # FRANCE TRAVAIL SPÉCIFIC
        "languages": languages,
        "soft_skills": soft_skills,
        "nb_positions": nb_posts,
    }


if __name__ == "__main__":
    # Test du module
    ft_api = FranceTravailAPI()
    logger.info("Test de récupération des offres...")
    offers = ft_api.fetch_offers(keywords="Data Scientist", range_str="0-19")

    logger.success(f"{len(offers)} offres récupérées.")

    if offers:
        logger.info(f"Titre de la première offre : {offers[0].get('intitule')}")
        logger.info(
            f"Entreprise : {offers[0].get('entreprise', {}).get('nom', 'Non spécifiée')}"
        )
        logger.info(offers)
