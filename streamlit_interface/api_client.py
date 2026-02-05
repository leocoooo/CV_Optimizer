"""
Client API pour la communication avec le backend FastAPI CV-Optimizer.
Gère tous les appels aux endpoints du backend avec retry et gestion d'erreurs.
"""

import requests
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import time
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import Config
from models import JobFilters, JobMatch, JobDetails, AdviceResponse, JobsResponse


class APIClient:
    """Client pour les communications avec l'API CV-Optimizer."""
    
    def __init__(self, base_url: str = None):
        """
        Initialise le client API.
        
        Args:
            base_url: URL de base de l'API (par défaut depuis config)
        """
        self.config = Config()
        self.base_url = base_url or self.config.API_BASE_URL
        self.session = requests.Session()
        
        # Configuration des timeouts et headers
        self.session.timeout = self.config.REQUEST_TIMEOUT
        self.session.headers.update({
            "User-Agent": "CV-Optimizer-Streamlit/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        logger.info(f"Client API initialisé pour {self.base_url}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, 
                                     requests.exceptions.Timeout,
                                     requests.exceptions.HTTPError))
    )
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Effectue une requête HTTP avec retry automatique.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Endpoint de l'API
            **kwargs: Arguments additionnels pour requests
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: En cas d'erreur de requête
        """
        url = f"{self.base_url}{endpoint}"
        
        logger.debug(f"Requête {method} vers {url}")
        
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        
        return response
    
    def health_check(self) -> bool:
        """
        Vérifie la santé du backend via l'endpoint /health.
        
        Returns:
            True si le backend est accessible, False sinon
        """
        try:
            response = self._make_request("GET", "/health")
            data = response.json()
            
            # Vérification que le statut est "healthy"
            is_healthy = data.get("status") == "healthy"
            
            if is_healthy:
                logger.info("Backend accessible et en bonne santé")
            else:
                logger.warning(f"Backend accessible mais statut: {data.get('status')}")
                
            return is_healthy
            
        except Exception as e:
            logger.error(f"Erreur lors du health check: {e}")
            return False
    
    def match_cv(self, cv_file: bytes, filename: str = "cv.pdf") -> List[JobMatch]:
        """
        Envoie un CV pour matching avec les offres d'emploi.
        
        Args:
            cv_file: Contenu binaire du fichier PDF
            filename: Nom du fichier (optionnel)
            
        Returns:
            Liste des offres correspondantes
            
        Raises:
            requests.exceptions.RequestException: En cas d'erreur API
            ValueError: Si les données du CV sont invalides
        """
        # Validation des paramètres d'entrée
        if not cv_file:
            raise ValueError("Le contenu du CV ne peut pas être vide")
        
        if len(cv_file) == 0:
            raise ValueError("Le fichier CV est vide")
        
        if len(cv_file) > self.config.MAX_FILE_SIZE:
            raise ValueError(f"Le fichier CV est trop volumineux ({len(cv_file)} bytes > {self.config.MAX_FILE_SIZE} bytes)")
        
        try:
            # Préparation du fichier pour l'upload
            files = {
                "file": (filename, cv_file, "application/pdf")
            }
            
            # Suppression du Content-Type header pour multipart/form-data
            headers = {k: v for k, v in self.session.headers.items() 
                      if k.lower() != "content-type"}
            
            logger.debug(f"Envoi du CV pour matching: {filename} ({len(cv_file)} bytes)")
            
            response = self._make_request(
                "POST", 
                "/api/match",
                files=files,
                headers=headers
            )
            
            data = response.json()
            
            # Validation de la structure de réponse
            if not isinstance(data, dict):
                raise ValueError("Réponse API invalide: format non reconnu")
            
            matches_data = data.get("matches", [])
            if not isinstance(matches_data, list):
                raise ValueError("Réponse API invalide: 'matches' doit être une liste")
            
            # Conversion en objets JobMatch
            matches = []
            for i, match_data in enumerate(matches_data):
                try:
                    # Validation des champs requis
                    required_fields = ["job_id", "title", "company", "location", "contract_type", "similarity_score"]
                    for field in required_fields:
                        if field not in match_data:
                            logger.warning(f"Champ manquant '{field}' dans le match {i}, ignoré")
                            continue
                    
                    # Validation du score de similarité
                    similarity_score = match_data.get("similarity_score", 0.0)
                    if not isinstance(similarity_score, (int, float)) or similarity_score < 0 or similarity_score > 1:
                        logger.warning(f"Score de similarité invalide pour le match {i}: {similarity_score}, défini à 0.0")
                        similarity_score = 0.0
                    
                    match = JobMatch(
                        job_id=str(match_data["job_id"]),
                        title=str(match_data["title"]),
                        company=str(match_data["company"]),
                        location=str(match_data["location"]),
                        contract_type=str(match_data["contract_type"]),
                        match_score=float(similarity_score),
                        summary=str(match_data.get("description", ""))[:200] + ("..." if len(str(match_data.get("description", ""))) > 200 else "")
                    )
                    matches.append(match)
                    
                except (KeyError, TypeError, ValueError) as e:
                    logger.warning(f"Erreur lors du parsing du match {i}: {e}, match ignoré")
                    continue
            
            logger.info(f"Matching réussi: {len(matches)} offres trouvées sur {len(matches_data)} reçues")
            return matches
            
        except Exception as e:
            logger.error(f"Erreur lors du matching CV: {e}")
            raise
    
    def get_jobs(self, filters: JobFilters) -> JobsResponse:
        """
        Récupère les offres d'emploi avec filtres optionnels.
        
        Args:
            filters: Filtres à appliquer
            
        Returns:
            Réponse contenant les offres filtrées
            
        Raises:
            requests.exceptions.RequestException: En cas d'erreur API
            ValueError: Si les filtres sont invalides
        """
        # Validation des filtres
        if not isinstance(filters, JobFilters):
            raise ValueError("Les filtres doivent être une instance de JobFilters")
        
        try:
            # Construction des paramètres de requête
            params = {}
            
            if filters.location:
                params["location"] = str(filters.location).strip()
            if filters.contract_type:
                params["contract_type"] = str(filters.contract_type).strip()
            if filters.experience_level:
                params["experience_level"] = str(filters.experience_level).strip()
            
            # Validation et ajout des paramètres de pagination
            page = max(1, int(filters.page)) if filters.page else 1
            page_size = max(1, min(100, int(filters.page_size))) if filters.page_size else 20
            
            params["page"] = page
            params["page_size"] = page_size
            
            logger.debug(f"Recherche d'offres avec filtres: {params}")
            
            response = self._make_request("GET", "/api/jobs", params=params)
            data = response.json()
            
            # Validation de la structure de réponse
            if not isinstance(data, dict):
                raise ValueError("Réponse API invalide: format non reconnu")
            
            jobs_data = data.get("jobs", [])
            if not isinstance(jobs_data, list):
                raise ValueError("Réponse API invalide: 'jobs' doit être une liste")
            
            # Conversion en objets JobMatch
            jobs = []
            for i, job_data in enumerate(jobs_data):
                try:
                    # Validation des champs requis
                    required_fields = ["id", "title", "company", "location", "contract_type"]
                    for field in required_fields:
                        if field not in job_data:
                            logger.warning(f"Champ manquant '{field}' dans l'offre {i}, ignorée")
                            continue
                    
                    job = JobMatch(
                        job_id=str(job_data["id"]),
                        title=str(job_data["title"]),
                        company=str(job_data["company"]),
                        location=str(job_data["location"]),
                        contract_type=str(job_data["contract_type"]),
                        match_score=0.0,  # Pas de score pour les recherches filtrées
                        summary=str(job_data.get("description", ""))[:200] + ("..." if len(str(job_data.get("description", ""))) > 200 else "")
                    )
                    jobs.append(job)
                    
                except (KeyError, TypeError, ValueError) as e:
                    logger.warning(f"Erreur lors du parsing de l'offre {i}: {e}, offre ignorée")
                    continue
            
            # Construction de la réponse avec validation
            total = max(0, int(data.get("total", len(jobs))))
            current_page = max(1, int(data.get("page", page)))
            current_page_size = max(1, int(data.get("page_size", page_size)))
            has_next = bool(data.get("has_next", False))
            
            jobs_response = JobsResponse(
                jobs=jobs,
                total=total,
                page=current_page,
                page_size=current_page_size,
                has_next=has_next
            )
            
            logger.info(f"Recherche avec filtres réussie: {len(jobs)} offres trouvées sur {total} total")
            return jobs_response
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche avec filtres: {e}")
            raise
    
    def get_job_details(self, job_id: str) -> JobDetails:
        """
        Récupère les détails complets d'une offre d'emploi.
        
        Args:
            job_id: Identifiant de l'offre
            
        Returns:
            Détails complets de l'offre
            
        Raises:
            requests.exceptions.RequestException: En cas d'erreur API
            ValueError: Si l'ID de l'offre est invalide
        """
        # Validation de l'ID
        if not job_id or not str(job_id).strip():
            raise ValueError("L'identifiant de l'offre ne peut pas être vide")
        
        job_id = str(job_id).strip()
        
        try:
            logger.debug(f"Récupération des détails pour l'offre {job_id}")
            
            response = self._make_request("GET", f"/api/jobs/{job_id}")
            data = response.json()
            
            # Validation de la structure de réponse
            if not isinstance(data, dict):
                raise ValueError("Réponse API invalide: format non reconnu")
            
            # Validation des champs requis
            required_fields = ["id", "title", "company", "location", "contract_type"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Champ requis manquant dans la réponse: {field}")
            
            # Construction de l'objet JobDetails avec validation
            try:
                requirements = data.get("requirements", [])
                if not isinstance(requirements, list):
                    logger.warning("Le champ 'requirements' n'est pas une liste, converti en liste vide")
                    requirements = []
                
                benefits = data.get("benefits", [])
                if not isinstance(benefits, list):
                    logger.warning("Le champ 'benefits' n'est pas une liste, converti en liste vide")
                    benefits = []
                
                job_details = JobDetails(
                    job_id=str(data["id"]),
                    title=str(data["title"]),
                    company=str(data["company"]),
                    location=str(data["location"]),
                    contract_type=str(data["contract_type"]),
                    experience_level=str(data.get("required_experience", "Non spécifié")),
                    description=str(data.get("description", "")),
                    requirements=[str(req) for req in requirements],
                    benefits=[str(benefit) for benefit in benefits],
                    salary_range=str(data["salary_range"]) if data.get("salary_range") else None,
                    url=str(data["url"]) if data.get("url") else None
                )
                
                logger.info(f"Détails récupérés pour l'offre {job_id}")
                return job_details
                
            except (KeyError, TypeError, ValueError) as e:
                logger.error(f"Erreur lors de la construction des détails de l'offre: {e}")
                raise ValueError(f"Données d'offre invalides: {e}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails pour {job_id}: {e}")
            raise
    
    def get_advice(self, cv_file: bytes, job_id: str, filename: str = "cv.pdf") -> AdviceResponse:
        """
        Obtient des conseils personnalisés pour une candidature.
        
        Args:
            cv_file: Contenu binaire du fichier PDF
            job_id: Identifiant de l'offre d'emploi
            filename: Nom du fichier (optionnel)
            
        Returns:
            Conseils personnalisés du LLM
            
        Raises:
            requests.exceptions.RequestException: En cas d'erreur API
            ValueError: Si les paramètres sont invalides
        """
        # Validation des paramètres
        if not cv_file:
            raise ValueError("Le contenu du CV ne peut pas être vide")
        
        if len(cv_file) == 0:
            raise ValueError("Le fichier CV est vide")
        
        if not job_id or not str(job_id).strip():
            raise ValueError("L'identifiant de l'offre ne peut pas être vide")
        
        if len(cv_file) > self.config.MAX_FILE_SIZE:
            raise ValueError(f"Le fichier CV est trop volumineux ({len(cv_file)} bytes > {self.config.MAX_FILE_SIZE} bytes)")
        
        job_id = str(job_id).strip()
        
        try:
            # Préparation des données
            files = {
                "file": (filename, cv_file, "application/pdf")
            }
            data = {
                "job_id": job_id
            }
            
            # Suppression du Content-Type header pour multipart/form-data
            headers = {k: v for k, v in self.session.headers.items() 
                      if k.lower() != "content-type"}
            
            logger.debug(f"Génération de conseils pour l'offre {job_id} avec CV {filename} ({len(cv_file)} bytes)")
            
            response = self._make_request(
                "POST",
                "/api/advice",
                files=files,
                data=data,
                headers=headers
            )
            
            response_data = response.json()
            
            # Validation de la structure de réponse
            if not isinstance(response_data, dict):
                raise ValueError("Réponse API invalide: format non reconnu")
            
            # Validation et extraction des données avec valeurs par défaut
            advice_text = str(response_data.get("advice", ""))
            if not advice_text.strip():
                logger.warning("Aucun conseil reçu de l'API")
                advice_text = "Aucun conseil spécifique disponible pour cette offre."
            
            # Validation du score
            match_score = response_data.get("match_score", 0.0)
            if not isinstance(match_score, (int, float)) or match_score < 0 or match_score > 1:
                logger.warning(f"Score de correspondance invalide: {match_score}, défini à 0.0")
                match_score = 0.0
            
            # Validation des zones d'amélioration
            improvement_areas = response_data.get("improvement_areas", [])
            if not isinstance(improvement_areas, list):
                logger.warning("Les zones d'amélioration ne sont pas une liste, converti en liste vide")
                improvement_areas = []
            else:
                improvement_areas = [str(area) for area in improvement_areas if area]
            
            # Date de génération
            generated_at = str(response_data.get("generated_at", ""))
            
            # Construction de l'objet AdviceResponse
            advice_response = AdviceResponse(
                job_id=job_id,
                advice_text=advice_text,
                overall_score=float(match_score),
                improvement_areas=improvement_areas,
                generated_at=generated_at
            )
            
            logger.info(f"Conseils générés pour l'offre {job_id} (score: {match_score:.2f})")
            return advice_response
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de conseils pour {job_id}: {e}")
            raise
    
    def close(self):
        """Ferme la session HTTP."""
        self.session.close()
        logger.info("Session API fermée")
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Retourne les informations de configuration de l'API client.
        
        Returns:
            Dictionnaire avec les informations de configuration
        """
        return {
            "base_url": self.base_url,
            "timeout": self.session.timeout,
            "max_file_size": self.config.MAX_FILE_SIZE,
            "max_file_size_mb": self.config.get_file_size_mb(),
            "max_retries": self.config.MAX_RETRIES,
            "retry_delay": self.config.RETRY_DELAY,
            "user_agent": self.session.headers.get("User-Agent", "Unknown")
        }
    
    def validate_configuration(self) -> Dict[str, bool]:
        """
        Valide la configuration de l'API client.
        
        Returns:
            Dictionnaire avec les résultats de validation
        """
        validation_results = {
            "base_url_valid": bool(self.base_url and self.base_url.startswith(("http://", "https://"))),
            "timeout_valid": isinstance(self.session.timeout, (int, float)) and self.session.timeout > 0,
            "max_file_size_valid": isinstance(self.config.MAX_FILE_SIZE, int) and self.config.MAX_FILE_SIZE > 0,
            "max_retries_valid": isinstance(self.config.MAX_RETRIES, int) and self.config.MAX_RETRIES >= 0,
            "retry_delay_valid": isinstance(self.config.RETRY_DELAY, (int, float)) and self.config.RETRY_DELAY >= 0
        }
        
        all_valid = all(validation_results.values())
        validation_results["all_valid"] = all_valid
        
        if not all_valid:
            logger.warning(f"Configuration invalide détectée: {validation_results}")
        else:
            logger.debug("Configuration de l'API client validée avec succès")
        
        return validation_results