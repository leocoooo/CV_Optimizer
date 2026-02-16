"""
Configuration de l'interface utilisateur.
"""

# Couleurs
PRIMARY_COLOR = "#1f77b4"
SUCCESS_COLOR = "#28a745"
ERROR_COLOR = "#dc3545"
WARNING_COLOR = "#ffc107"
INFO_COLOR = "#17a2b8"

# Limites
MAX_FILE_SIZE_MB = 5
DEFAULT_PAGE_SIZE = 20
DEFAULT_TOP_N = 10
MAX_TOP_N = 50
DEFAULT_DAYS_LIMIT = 30

# Messages
ERROR_MESSAGES = {
    "api_unavailable": "⚠️ L'API n'est pas accessible. Vérifiez que le serveur est démarré.",
    "invalid_api_key": "❌ API Key invalide",
    "file_required": "📄 Veuillez uploader un fichier",
    "keywords_required": "🔑 Veuillez entrer au moins un mot-clé",
}

SUCCESS_MESSAGES = {
    "collection_started": "✅ Collecte lancée avec succès",
    "reindex_started": "✅ Réindexation lancée",
    "stats_loaded": "✅ Statistiques chargées",
}

# Configuration Streamlit
PAGE_CONFIG = {
    "page_title": "CV-Optimizer",
    "page_icon": "📄",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Navigation
PAGES = {
    "🎯 Matching CV": "matching",
    "💼 Recherche d'offres": "jobs",
    "💡 Conseils LLM": "advice",
    "🔧 Admin": "admin",
    "ℹ️ À propos": "about",
}
