import httpx
from datetime import datetime
from loguru import logger
from app.config import get_settings
from src.services.scraping_utils import clean_description, parse_date


class FranceTravailAPI:
    def __init__(self):
        settings = get_settings()
        self.client_id = settings.FT_CLIENT_ID
        self.client_secret = settings.FT_CLIENT_SECRET
        self.auth_url = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
        self.base_url = (
            "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
        )
        self.referentiel_url = (
            "https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel"
        )
        self.access_token = None
        self._communes_cache = {}  # Cache pour les communes

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

    def get_location_details(
        self, commune_code: str | None, libelle: str | None
    ) -> dict:
        """
        Récupère les détails de localité (city, department, region).

        Args:
            commune_code: Code INSEE de la commune (ex: "91228")
            libelle: Libellé complet (ex: "75 - Paris (Dept.)" ou "91 - EVRY COURCOURONNES")

        Returns:
            dict: {"city": "...", "department": "...", "region": "..."}
        """
        result: dict[str, str | None] = {
            "city": None,
            "department": None,
            "region": None,
        }

        if not libelle and not commune_code:
            return result

        # Extraire city et department du libelle
        # Format typique: "75 - Paris (Dept.)" ou "91 - EVRY COURCOURONNES"
        if libelle:
            try:
                parts = libelle.split(" - ", 1)
                dept_code = parts[0].strip()  # Ex: "75", "91"
                city_part = parts[1].strip() if len(parts) > 1 else ""
                # Nettoyer les annotations comme "(Dept.)"
                city = city_part.replace("(Dept.)", "").strip()
                result["city"] = city if city else None

                # Utiliser le code du département pour obtenir la région
                result["department"] = self._get_department_name(dept_code)
                result["region"] = self._get_region_from_dept_code(dept_code)
            except Exception as e:
                logger.debug(f"Erreur parsing libelle {libelle}: {e}")

        return result

    def _get_department_name(self, dept_code: str) -> str | None:
        """Convertit un code département en nom (optionnel - retourne le code si pas trouvé)."""
        # Mapping complet des codes département → noms (métropole + DOM-TOM)
        departments = {
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
            "971": "Guadeloupe",
            "972": "Martinique",
            "973": "Guyane",
            "974": "Réunion",
            "976": "Mayotte",
        }
        return departments.get(dept_code, dept_code)

    def _get_region_from_dept_code(self, dept_code: str) -> str | None:
        """Retourne la région à partir du code département."""
        # Mapping complet département → région
        regions_map = {
            # Île-de-France
            "75": "Île-de-France",
            "77": "Île-de-France",
            "78": "Île-de-France",
            "91": "Île-de-France",
            "92": "Île-de-France",
            "93": "Île-de-France",
            "94": "Île-de-France",
            "95": "Île-de-France",
            "60": "Île-de-France",
            # Bourgogne-Franche-Comté
            "21": "Bourgogne-Franche-Comté",
            "25": "Bourgogne-Franche-Comté",
            "39": "Bourgogne-Franche-Comté",
            "58": "Bourgogne-Franche-Comté",
            "70": "Bourgogne-Franche-Comté",
            "71": "Bourgogne-Franche-Comté",
            "89": "Bourgogne-Franche-Comté",
            "90": "Bourgogne-Franche-Comté",
            # Bretagne
            "22": "Bretagne",
            "29": "Bretagne",
            "35": "Bretagne",
            "56": "Bretagne",
            # Centre-Val de Loire
            "18": "Centre-Val de Loire",
            "28": "Centre-Val de Loire",
            "36": "Centre-Val de Loire",
            "37": "Centre-Val de Loire",
            "41": "Centre-Val de Loire",
            "45": "Centre-Val de Loire",
            # Corse
            "2A": "Corse",
            "2B": "Corse",
            # Grand Est
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
            # Hauts-de-France
            "02": "Hauts-de-France",
            "59": "Hauts-de-France",
            "62": "Hauts-de-France",
            "80": "Hauts-de-France",
            # Normandie
            "14": "Normandie",
            "27": "Normandie",
            "50": "Normandie",
            "61": "Normandie",
            "76": "Normandie",
            # Nouvelle-Aquitaine
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
            # Occitanie
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
            # Auvergne-Rhône-Alpes
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
            # Provence-Alpes-Côte d'Azur
            "04": "Provence-Alpes-Côte d'Azur",
            "05": "Provence-Alpes-Côte d'Azur",
            "06": "Provence-Alpes-Côte d'Azur",
            "13": "Provence-Alpes-Côte d'Azur",
            "83": "Provence-Alpes-Côte d'Azur",
            "84": "Provence-Alpes-Côte d'Azur",
            # Pays de la Loire
            "44": "Pays de la Loire",
            "49": "Pays de la Loire",
            "53": "Pays de la Loire",
            "72": "Pays de la Loire",
            "85": "Pays de la Loire",
            # DOM-TOM
            "971": "Guadeloupe",
            "972": "Martinique",
            "973": "Guyane",
            "974": "Réunion",
            "976": "Mayotte",
        }
        return regions_map.get(dept_code)


def convert_ft_offer(offer: dict, ft_api: "FranceTravailAPI | None" = None) -> dict:
    """
    Convertit une offre France Travail API au format normalisé.

    Args:
        offer: Dictionnaire d'offre provenant de l'API France Travail
        ft_api: Instance FranceTravailAPI pour l'extraction de localisation (optionnel)

    Returns:
        dict: Offre formatée au standard unifié
    """
    # Extraction des données de base
    ft_id = offer.get("id", "")  # ID de France Travail (plus robuste)
    title = offer.get("intitule", "Sans titre")
    description = offer.get("description", "")

    # Localisation - extraire city, department, region
    lieu_travail = offer.get("lieuTravail", {})
    libelle = lieu_travail.get("libelle", None)
    commune_code = lieu_travail.get("commune", None)

    if ft_api:
        location_details = ft_api.get_location_details(commune_code, libelle)
    else:
        # Logique par défaut si pas d'instance API
        location_details = {"city": None, "department": None, "region": None}
        if libelle:
            parts = libelle.split(" - ", 1)
            city_part = parts[1].strip() if len(parts) > 1 else ""
            location_details["city"] = city_part.replace("(Dept.)", "").strip() or None

    # Entreprise
    entreprise = offer.get("entreprise", {})
    company = entreprise.get("nom", "Inconnu")
    company_size = offer.get("trancheEffectifEtab", None)  # "500 à 999 salariés", etc.

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

    # Niveau d'étude requis - extraire du tableau formations
    required_education = None
    formations = offer.get("formations", [])
    if formations:
        # Chercher le premier niveau de formation exigé (exigence='E')
        for formation in formations:
            if isinstance(formation, dict):
                if formation.get("exigence") == "E":
                    # Exigé: prioriser celui-ci
                    required_education = formation.get("niveauLibelle")
                    break
        # Si aucun exigé, prendre le premier souhaité (exigence='S')
        if not required_education:
            for formation in formations:
                if isinstance(formation, dict):
                    if formation.get("exigence") == "S":
                        required_education = formation.get("niveauLibelle")
                        break
        # Sinon, prendre le premier avec niveauLibelle
        if not required_education:
            for formation in formations:
                if isinstance(formation, dict) and formation.get("niveauLibelle"):
                    required_education = formation.get("niveauLibelle")
                    break

    # Salaire
    salary_info = offer.get("salaire", {})
    salary = salary_info.get("libelle") if isinstance(salary_info, dict) else None

    # Compétences techniques/métier
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

    # Compétences transversales/soft skills (ex: "Communication", "Esprit d'équipe")
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

    # Parse de la date de création (dateCreation vient au format ISO avec millisecondes)
    date_creation_str = offer.get("dateCreation", None)
    date_publication = parse_date(date_creation_str) if date_creation_str else None

    # Construction de l'offre formatée avec l'ID FT original
    return {
        "id": ft_id,  # Utiliser l'ID de France Travail directement
        "url": offer.get("origineOffre", {}).get("urlOrigine") or None,
        "source": "France Travail",
        "date_publication": date_publication,
        "date_scraping": datetime.now().isoformat(),
        # POSTE
        "title": title,
        "sector": sector,
        "contract_type": contract_type,
        "remote_mode": remote_mode,
        # LOCALISATION
        "city": location_details.get("city"),
        "department": location_details.get("department"),
        "region": location_details.get("region"),
        # ENTREPRISE
        "company": company,
        "company_size": company_size,  # Taille entreprise de FT
        # PROFIL DEMANDÉ
        "required_experience": required_experience,
        "required_education": required_education,  # Maintenant récupéré de FT
        "competences": competences,  # Techniques/métier
        # RÉMUNÉRATION
        "salary": salary,
        # CONTENU
        "description": clean_description(description),
        "job_profile": None,
        # CHAMPS SOURCE-SPÉCIFIQUES
        "languages": languages,
        "soft_skills": soft_skills,  # Compétences transversales
        # NOTE: nb_positions supprimé (pas robuste)
    }


if __name__ == "__main__":
    # Test du module (sans convertir l'offre, on ne récupère que les données brutes de l'API)
    ft_api = FranceTravailAPI()
    logger.info("Test de récupération des offres...")
    offers = ft_api.fetch_offers(keywords="Data Engineer", range_str="0-9")

    logger.success(f"{len(offers)} offres récupérées.")

    if offers:
        logger.info(f"Titre de la première offre : {offers[0].get('intitule')}")
        logger.info(
            f"Entreprise : {offers[0].get('entreprise', {}).get('nom', 'Non spécifiée')}"
        )
        logger.info(offers[:9])
