"""
Configuration de l'application avec Pydantic Settings.
Charge les variables d'environnement depuis .env
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'API """
    # Params obligatoires à définir dans .env :

    # Database 
    DATABASE_URL: str
    # API Keys externes 
    HUGGINGFACE_API_KEY: str
    FT_CLIENT_ID: str
    FT_CLIENT_SECRET: str
    # Security 
    API_KEY_ADMIN: str    
    
    # Constantes nécessaires pour l'app (valeurs par défaut)
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]
    MAX_UPLOAD_SIZE_MB: int = 5
    LLM_TIMEOUT_SECONDS: int = 60
    
    # Matching
    DEFAULT_TOP_N: int = 10 
    MAX_TOP_N: int = 50  # Maximum autorisé
    DEFAULT_DAYS_LIMIT: int = 30
    
    # Scraping
    SCRAPING_HEADLESS: bool = True
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True    
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Instance globale de configuration
settings = Settings()


def get_settings() -> Settings:
    """
    Retourne l'instance de configuration.
    Utilisé comme dépendance FastAPI.
    """
    return settings
