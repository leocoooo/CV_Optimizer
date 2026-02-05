"""
Configuration de l'application Streamlit CV-Optimizer.
Centralise toutes les constantes et paramètres de configuration.
"""

import os
from typing import List


class Config:
    """Classe de configuration pour l'interface Streamlit."""
    
    # Configuration API Backend
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # Configuration des fichiers
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB en bytes
    ALLOWED_FILE_TYPES: List[str] = ["pdf"]
    
    # Configuration des requêtes
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))  # 30 secondes
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))  # 1 seconde
    
    # Configuration du cache
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
    
    # Configuration de la pagination
    PAGE_SIZE: int = int(os.getenv("PAGE_SIZE", "20"))
    MAX_RESULTS_DISPLAY: int = int(os.getenv("MAX_RESULTS_DISPLAY", "50"))
    
    # Configuration UI
    DEFAULT_LOCATION: str = os.getenv("DEFAULT_LOCATION", "")
    DEFAULT_CONTRACT_TYPE: str = os.getenv("DEFAULT_CONTRACT_TYPE", "")
    DEFAULT_EXPERIENCE_LEVEL: str = os.getenv("DEFAULT_EXPERIENCE_LEVEL", "")
    
    # Messages d'erreur en français
    ERROR_MESSAGES = {
        "connection_error": "Impossible de se connecter au serveur. Vérifiez votre connexion.",
        "invalid_pdf": "Le fichier doit être au format PDF.",
        "file_too_large": f"Le fichier est trop volumineux (maximum {MAX_FILE_SIZE // 1024 // 1024}MB).",
        "file_empty": "Le fichier est vide.",
        "no_cv_uploaded": "Veuillez d'abord uploader un CV.",
        "api_timeout": "La requête a pris trop de temps. Veuillez réessayer.",
        "server_error": "Erreur serveur. Veuillez réessayer plus tard.",
        "invalid_response": "Réponse invalide du serveur.",
        "network_error": "Erreur de réseau. Vérifiez votre connexion internet.",
        "file_read_error": "Erreur lors de la lecture du fichier.",
        "validation_error": "Erreur de validation des données.",
        "not_found": "Ressource non trouvée.",
        "unauthorized": "Accès non autorisé.",
        "rate_limit": "Trop de requêtes. Veuillez patienter.",
        "unknown_error": "Une erreur inattendue s'est produite."
    }
    
    # Messages de succès
    SUCCESS_MESSAGES = {
        "cv_uploaded": "CV uploadé avec succès",
        "matches_found": "Offres correspondantes trouvées",
        "filters_applied": "Filtres appliqués avec succès",
        "advice_generated": "Conseils générés avec succès",
        "connection_established": "Connexion au serveur établie"
    }
    
    # Messages d'information
    INFO_MESSAGES = {
        "no_matches": "Aucune offre correspondante trouvée",
        "loading": "Chargement en cours...",
        "analyzing": "Analyse du CV en cours...",
        "generating_advice": "Génération des conseils en cours...",
        "applying_filters": "Application des filtres...",
        "checking_connection": "Vérification de la connexion..."
    }
    
    # Options de filtres
    CONTRACT_TYPES = [
        "",  # Option vide pour "Tous"
        "CDI",
        "CDD", 
        "Stage",
        "Freelance",
        "Alternance",
        "Intérim"
    ]
    
    EXPERIENCE_LEVELS = [
        "",  # Option vide pour "Tous"
        "Débutant",
        "Junior (1-3 ans)",
        "Confirmé (3-7 ans)",
        "Senior (7+ ans)",
        "Expert (10+ ans)"
    ]
    
    # Configuration Streamlit
    STREAMLIT_CONFIG = {
        "page_title": "CV-Optimizer",
        "page_icon": "🎯",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
    
    @classmethod
    def get_file_size_mb(cls) -> float:
        """Retourne la taille maximale de fichier en MB."""
        return cls.MAX_FILE_SIZE / 1024 / 1024
    
    @classmethod
    def is_valid_file_size(cls, file_size: int) -> bool:
        """Vérifie si la taille du fichier est valide."""
        return 0 < file_size <= cls.MAX_FILE_SIZE
    
    @classmethod
    def is_valid_file_type(cls, filename: str) -> bool:
        """Vérifie si le type de fichier est valide."""
        if not filename:
            return False
        extension = filename.lower().split('.')[-1]
        return extension in cls.ALLOWED_FILE_TYPES


# Instance globale de configuration
config = Config()