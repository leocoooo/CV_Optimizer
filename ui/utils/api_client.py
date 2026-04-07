"""
Client API centralisé pour toutes les requêtes vers le backend.
"""

import json
from typing import Any, Dict, List, Optional

import requests


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

    def get_status(self) -> Dict[str, Any]:
        """Récupère le statut détaillé de l'API."""
        response = requests.get(f"{self.base_url}/api/status", timeout=10)
        response.raise_for_status()
        return response.json()

    def get_dashboard(self) -> Dict[str, Any]:
        """Récupère les métriques agrégées du cockpit."""
        response = requests.get(f"{self.base_url}/api/dashboard", timeout=10)
        response.raise_for_status()
        return response.json()

    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Récupère la fiche complète d'une offre."""
        response = requests.get(f"{self.base_url}/api/jobs/{job_id}", timeout=10)
        response.raise_for_status()
        return response.json()

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

        Les paramètres sont envoyés dans le formulaire multipart pour correspondre
        aux champs FastAPI déclarés en `Form(...)`.
        """
        payload: Dict[str, Any] = {"top_n": top_n, "days_limit": days_limit}
        if location:
            payload["location"] = location
        if contract_type:
            payload["contract_type"] = contract_type
        if experience:
            payload["experience"] = experience

        files = {"file": (filename, file_content, "application/pdf")}

        response = requests.post(
            f"{self.base_url}/api/match",
            files=files,
            data=payload,
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
        """Recherche des offres d'emploi avec filtres avancés."""
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
        """Obtient des conseils LLM pour un CV et une offre."""
        files = {"file": (filename, file_content, "application/pdf")}
        data = {"job_id": job_id}

        response = requests.post(
            f"{self.base_url}/api/advice", files=files, data=data, timeout=70
        )
        response.raise_for_status()
        return response.json()

    def compare_skills(
        self, file_content: bytes, filename: str, job_id: str
    ) -> Dict[str, Any]:
        """Compare les compétences visibles dans un CV avec celles d'une offre."""
        files = {"file": (filename, file_content, "application/pdf")}
        data = {"job_id": job_id}

        response = requests.post(
            f"{self.base_url}/api/skills/compare", files=files, data=data, timeout=45
        )
        response.raise_for_status()
        return response.json()

    def chat_with_llm(
        self,
        file_content: bytes,
        filename: str,
        job_id: str,
        message: str,
        history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        """Ouvre une discussion avec le coach LLM contextualisé."""
        files = {"file": (filename, file_content, "application/pdf")}
        data = {
            "job_id": job_id,
            "message": message,
            "history": json.dumps(history or [], ensure_ascii=False),
        }

        response = requests.post(
            f"{self.base_url}/api/chat",
            files=files,
            data=data,
            timeout=90,
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
        """Lance la collecte d'offres (admin)."""
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
        """Réindexe les embeddings (admin)."""
        headers = {"X-API-Key": api_key}

        response = requests.post(
            f"{self.base_url}/api/admin/reindex", headers=headers, timeout=300
        )
        response.raise_for_status()
        return response.json()

    def get_stats(self, api_key: str) -> Dict[str, Any]:
        """Récupère les statistiques de la base (admin)."""
        headers = {"X-API-Key": api_key}

        response = requests.get(
            f"{self.base_url}/api/admin/stats", headers=headers, timeout=10
        )
        response.raise_for_status()
        return response.json()
