"""
Exceptions personnalisées pour l'API CV-Optimizer.
Permet une gestion fine des erreurs avec codes HTTP appropriés.
"""

from typing import Optional, Dict, Any


class CVOptimizerException(Exception):
    """Exception de base pour toutes les erreurs de l'API."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


class CVExtractionError(CVOptimizerException):
    """Erreur lors de l'extraction du texte du CV."""

    def __init__(
        self,
        message: str = "Impossible d'extraire le texte du CV",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, status_code=400, detail=detail)


class InvalidFileError(CVOptimizerException):
    """Fichier invalide (format, taille, etc.)."""

    def __init__(
        self, message: str = "Fichier invalide", detail: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=400, detail=detail)


class NoMatchFoundError(CVOptimizerException):
    """Aucune offre correspondante trouvée."""

    def __init__(
        self,
        message: str = "Aucune offre correspondante trouvée",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, status_code=404, detail=detail)


class JobNotFoundError(CVOptimizerException):
    """Offre d'emploi introuvable."""

    def __init__(self, job_id: str, detail: Optional[Dict[str, Any]] = None):
        message = f"Offre '{job_id}' introuvable en base de données"
        super().__init__(message=message, status_code=404, detail=detail)


class LLMServiceError(CVOptimizerException):
    """Erreur lors de l'appel au service LLM (Hugging Face)."""

    def __init__(
        self,
        message: str = "Le service LLM est temporairement indisponible",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, status_code=503, detail=detail)


class DatabaseError(CVOptimizerException):
    """Erreur de connexion ou de requête base de données."""

    def __init__(
        self,
        message: str = "Erreur de base de données",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, status_code=500, detail=detail)


class AuthenticationError(CVOptimizerException):
    """Erreur d'authentification (API key invalide)."""

    def __init__(
        self,
        message: str = "Authentification requise ou invalide",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, status_code=401, detail=detail)


class RateLimitExceededError(CVOptimizerException):
    """Limite de taux dépassée."""

    def __init__(
        self,
        message: str = "Trop de requêtes, veuillez réessayer plus tard",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, status_code=429, detail=detail)
