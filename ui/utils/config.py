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

# CSS personnalisé pour améliorer le design
CUSTOM_CSS = """
<style>
    /* Amélioration générale */
    .main {
        padding: 2rem;
    }
    
    /* Cards avec ombres */
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Boutons améliorés */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Métriques stylisées */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
    }
    
    /* Messages d'alerte améliorés */
    .stAlert {
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Sidebar améliorée */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Titres sans bordure */
    h1, h2, h3 {
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Input fields améliorés */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #1f77b4;
        box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.1);
    }
    
    /* File uploader stylisé */
    [data-testid="stFileUploader"] {
        border: 2px dashed #1f77b4;
        border-radius: 8px;
        padding: 2rem;
        background: #f8f9fa;
    }
    
    /* Badges de statut */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-success {
        background: #d4edda;
        color: #155724;
    }
    
    .status-error {
        background: #f8d7da;
        color: #721c24;
    }
    
    .status-warning {
        background: #fff3cd;
        color: #856404;
    }
    
    /* Score indicators */
    .score-high {
        color: #28a745;
        font-weight: 600;
    }
    
    .score-medium {
        color: #ffc107;
        font-weight: 600;
    }
    
    .score-low {
        color: #dc3545;
        font-weight: 600;
    }
</style>
"""
