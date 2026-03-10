"""
Client API centralisé pour toutes les requêtes vers le backend.
"""

import requests
from typing import Optional, Dict, Any, List


class APIClient:
    """Client pour communiquer avec l'API CV-Optimizer."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.timeout = 30

    def check_health(self) -> bool:
        """Vérifie si l'API est accessible."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def match_cv(
        self,
        file_content: bytes,
        filename: str,
        top_n: int = 10,
        days_limit: int = 30,
        location: Optional[str] = None,
        contract_type: Optional[str] = None,
        experience: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Matche un CV avec les offres d'emploi.

        Args:
            file_content: Contenu du fichier PDF
            filename: Nom du fichier
            top_n: Nombre de résultats
            days_limit: Limiter aux N derniers jours
            location: Localisation souhaitée
            contract_type: Type de contrat
            experience: Niveau d'expérience

        Returns:
            Résultats du matching

        Raises:
            requests.HTTPError: Si la requête échoue
        """
        params: Dict[str, Any] = {"top_n": top_n, "days_limit": days_limit}
        if location:
            params["location"] = location
        if contract_type:
            params["contract_type"] = contract_type
        if experience:
            params["experience"] = experience

        files = {"file": (filename, file_content, "application/pdf")}

        response = requests.post(
            f"{self.base_url}/api/match",
            files=files,
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def search_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        contract_type: Optional[str] = None,
        experience: Optional[str] = None,
        source: Optional[str] = None,
        sector: Optional[str] = None,
        remote_mode: Optional[str] = None,
        company: Optional[str] = None,
        required_education: Optional[str] = None,
        days_limit: int = 30,
    ) -> Dict[str, Any]:
        """
        Recherche des offres d'emploi avec filtres avancés.

        Args:
            page: Numéro de page
            page_size: Taille de page
            keywords: Mots-clés de recherche
            location: Localisation
            contract_type: Type de contrat
            experience: Niveau d'expérience
            source: Source de l'offre
            sector: Secteur d'activité
            remote_mode: Mode de télétravail
            company: Entreprise
            required_education: Niveau d'études requis
            days_limit: Offres des N derniers jours

        Returns:
            Résultats de la recherche
        """
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "days_limit": days_limit,
        }

        if keywords:
            params["keywords"] = keywords
        if location:
            params["location"] = location
        if contract_type:
            params["contract_type"] = contract_type
        if experience:
            params["experience"] = experience
        if source:
            params["source"] = source
        if sector:
            params["sector"] = sector
        if remote_mode:
            params["remote_mode"] = remote_mode
        if company:
            params["company"] = company
        if required_education:
            params["required_education"] = required_education

        response = requests.get(f"{self.base_url}/api/jobs", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_advice(
        self, file_content: bytes, filename: str, job_id: str
    ) -> Dict[str, Any]:
        """
        Obtient des conseils LLM pour un CV et une offre.

        Args:
            file_content: Contenu du fichier PDF
            filename: Nom du fichier
            job_id: ID de l'offre ciblée

        Returns:
            Conseils du LLM
        """
        files = {"file": (filename, file_content, "application/pdf")}
        data = {"job_id": job_id}

        response = requests.post(
            f"{self.base_url}/api/advice", files=files, data=data, timeout=70
        )
        response.raise_for_status()
        return response.json()

    def collect_jobs(
        self,
        api_key: str,
        keywords: List[str],
        max_offers: int = 10,
        enable_scraping: bool = True,
    ) -> Dict[str, Any]:
        """
        Lance la collecte d'offres (admin).

        Args:
            api_key: Clé API admin
            keywords: Liste de mots-clés
            max_offers: Nombre max d'offres par mot-clé
            enable_scraping: Activer le scraping web

        Returns:
            Confirmation de lancement
        """
        headers = {"X-API-Key": api_key}
        payload = {
            "keywords": keywords,
            "max_offers": max_offers,
            "enable_scraping": enable_scraping,
        }

        response = requests.post(
            f"{self.base_url}/api/admin/collect",
            json=payload,
            headers=headers,
            timeout=300,
        )
        response.raise_for_status()
        return response.json()

    def reindex_embeddings(self, api_key: str) -> Dict[str, Any]:
        """
        Réindexe les embeddings (admin).

        Args:
            api_key: Clé API admin

        Returns:
            Confirmation de lancement
        """
        headers = {"X-API-Key": api_key}

        response = requests.post(
            f"{self.base_url}/api/admin/reindex", headers=headers, timeout=300
        )
        response.raise_for_status()
        return response.json()

    def get_stats(self, api_key: str) -> Dict[str, Any]:
        """
        Récupère les statistiques de la base (admin).

        Args:
            api_key: Clé API admin

        Returns:
            Statistiques détaillées
        """
        headers = {"X-API-Key": api_key}

        response = requests.get(
            f"{self.base_url}/api/admin/stats", headers=headers, timeout=10
        )
        response.raise_for_status()
        return response.json()
