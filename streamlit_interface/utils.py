"""
Utilitaires pour l'interface Streamlit CV-Optimizer.
Fonctions helper et utilitaires divers.
"""

import hashlib
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import validators
from loguru import logger

from config import Config


def generate_cache_key(endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
    """
    Génère une clé de cache unique pour une requête API.
    
    Args:
        endpoint: Endpoint de l'API
        params: Paramètres de la requête
        
    Returns:
        Clé de cache MD5
    """
    cache_data = f"{endpoint}_{params or {}}"
    return hashlib.md5(cache_data.encode()).hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Formate une taille de fichier en unités lisibles.
    
    Args:
        size_bytes: Taille en bytes
        
    Returns:
        Taille formatée (ex: "2.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_timestamp(timestamp: Union[str, float, datetime]) -> str:
    """
    Formate un timestamp en chaîne lisible.
    
    Args:
        timestamp: Timestamp à formater
        
    Returns:
        Timestamp formaté en français
    """
    try:
        if isinstance(timestamp, str):
            # Tentative de parsing ISO format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, float):
            dt = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            return "Date inconnue"
        
        # Format français
        return dt.strftime("%d/%m/%Y à %H:%M")
        
    except Exception as e:
        logger.warning(f"Erreur lors du formatage de timestamp: {e}")
        return "Date invalide"


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale.
    
    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        suffix: Suffixe à ajouter si tronqué
        
    Returns:
        Texte tronqué
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)].rstrip() + suffix


def validate_url(url: str) -> bool:
    """
    Valide une URL.
    
    Args:
        url: URL à valider
        
    Returns:
        True si l'URL est valide
    """
    if not url:
        return False
    
    return validators.url(url) is True


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour le rendre sûr.
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier nettoyé
    """
    if not filename:
        return "fichier_sans_nom"
    
    # Caractères interdits
    forbidden_chars = '<>:"/\\|?*'
    
    # Remplacement des caractères interdits
    clean_name = filename
    for char in forbidden_chars:
        clean_name = clean_name.replace(char, '_')
    
    # Limitation de la longueur
    if len(clean_name) > 255:
        name, ext = clean_name.rsplit('.', 1) if '.' in clean_name else (clean_name, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        clean_name = name[:max_name_length] + ('.' + ext if ext else '')
    
    return clean_name


def extract_keywords_from_text(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extrait des mots-clés simples d'un texte.
    
    Args:
        text: Texte à analyser
        max_keywords: Nombre maximum de mots-clés
        
    Returns:
        Liste de mots-clés
    """
    if not text:
        return []
    
    # Mots vides français courants
    stop_words = {
        'le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour',
        'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus',
        'par', 'grand', 'en', 'une', 'être', 'et', 'de', 'il', 'avoir', 'ne', 'je',
        'son', 'que', 'se', 'qui', 'ce', 'dans', 'en', 'du', 'elle', 'au', 'de',
        'le', 'tout', 'et', 'y', 'mais', 'd', 'lui', 'nous', 'comme', 'ou', 'si'
    }
    
    # Nettoyage et tokenisation simple
    import re
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', text.lower())
    
    # Filtrage des mots vides et comptage
    word_count = {}
    for word in words:
        if word not in stop_words and len(word) >= 3:
            word_count[word] = word_count.get(word, 0) + 1
    
    # Tri par fréquence et limitation
    keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in keywords[:max_keywords]]


def calculate_match_score_color(score: float) -> str:
    """
    Détermine la couleur d'affichage selon un score de correspondance.
    
    Args:
        score: Score de 0.0 à 1.0
        
    Returns:
        Couleur CSS
    """
    if score >= 0.8:
        return "#28a745"  # Vert
    elif score >= 0.6:
        return "#fd7e14"  # Orange
    elif score >= 0.4:
        return "#ffc107"  # Jaune
    else:
        return "#dc3545"  # Rouge


def format_contract_type(contract_type: str) -> str:
    """
    Formate et normalise un type de contrat.
    
    Args:
        contract_type: Type de contrat brut
        
    Returns:
        Type de contrat formaté
    """
    if not contract_type:
        return "Non spécifié"
    
    # Normalisation des types courants
    contract_mapping = {
        'cdi': 'CDI',
        'cdd': 'CDD',
        'stage': 'Stage',
        'freelance': 'Freelance',
        'alternance': 'Alternance',
        'interim': 'Intérim',
        'temps_plein': 'Temps plein',
        'temps_partiel': 'Temps partiel'
    }
    
    normalized = contract_type.lower().replace(' ', '_').replace('-', '_')
    return contract_mapping.get(normalized, contract_type.title())


def format_experience_level(experience: str) -> str:
    """
    Formate et normalise un niveau d'expérience.
    
    Args:
        experience: Niveau d'expérience brut
        
    Returns:
        Niveau d'expérience formaté
    """
    if not experience:
        return "Non spécifié"
    
    # Normalisation des niveaux courants
    experience_mapping = {
        'debutant': 'Débutant',
        'junior': 'Junior (1-3 ans)',
        'confirme': 'Confirmé (3-7 ans)',
        'senior': 'Senior (7+ ans)',
        'expert': 'Expert (10+ ans)',
        '0': 'Débutant',
        '1': 'Junior (1-3 ans)',
        '2': 'Junior (1-3 ans)',
        '3': 'Confirmé (3-7 ans)',
        '5': 'Confirmé (3-7 ans)',
        '7': 'Senior (7+ ans)',
        '10': 'Expert (10+ ans)'
    }
    
    # Extraction des années d'expérience si format numérique
    import re
    years_match = re.search(r'(\d+)', experience)
    if years_match:
        years = int(years_match.group(1))
        if years == 0:
            return 'Débutant'
        elif years <= 3:
            return 'Junior (1-3 ans)'
        elif years <= 7:
            return 'Confirmé (3-7 ans)'
        elif years <= 10:
            return 'Senior (7+ ans)'
        else:
            return 'Expert (10+ ans)'
    
    normalized = experience.lower().replace(' ', '').replace('-', '')
    return experience_mapping.get(normalized, experience.title())


def is_cache_expired(timestamp: float, ttl: int) -> bool:
    """
    Vérifie si un cache est expiré.
    
    Args:
        timestamp: Timestamp de création du cache
        ttl: Time To Live en secondes
        
    Returns:
        True si le cache est expiré
    """
    return time.time() - timestamp > ttl


def get_session_duration(start_time: float) -> str:
    """
    Calcule la durée d'une session.
    
    Args:
        start_time: Timestamp de début de session
        
    Returns:
        Durée formatée
    """
    duration = time.time() - start_time
    
    if duration < 60:
        return f"{int(duration)}s"
    elif duration < 3600:
        return f"{int(duration // 60)}m {int(duration % 60)}s"
    else:
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        return f"{hours}h {minutes}m"


def clean_html_tags(text: str) -> str:
    """
    Supprime les balises HTML d'un texte.
    
    Args:
        text: Texte avec balises HTML
        
    Returns:
        Texte nettoyé
    """
    if not text:
        return ""
    
    import re
    # Suppression des balises HTML
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Nettoyage des entités HTML courantes
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' '
    }
    
    for entity, replacement in html_entities.items():
        clean_text = clean_text.replace(entity, replacement)
    
    return clean_text.strip()


def validate_job_id(job_id: str) -> bool:
    """
    Valide un identifiant d'offre d'emploi.
    
    Args:
        job_id: Identifiant à valider
        
    Returns:
        True si l'identifiant est valide
    """
    if not job_id or not isinstance(job_id, str):
        return False
    
    # Vérification de la longueur et des caractères
    if len(job_id) < 3 or len(job_id) > 100:
        return False
    
    # Caractères autorisés : lettres, chiffres, tirets, underscores
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', job_id))


def log_user_action(action: str, details: Optional[Dict[str, Any]] = None):
    """
    Log une action utilisateur pour le debugging.
    
    Args:
        action: Type d'action
        details: Détails additionnels
    """
    log_data = {
        'action': action,
        'timestamp': time.time(),
        'details': details or {}
    }
    
    logger.info(f"Action utilisateur: {action}", extra=log_data)


class PerformanceTimer:
    """Utilitaire pour mesurer les performances."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.debug(f"Début de l'opération: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        logger.info(f"Opération '{self.operation_name}' terminée en {duration:.2f}s")


def get_config_summary() -> Dict[str, Any]:
    """
    Retourne un résumé de la configuration actuelle.
    
    Returns:
        Dictionnaire avec les paramètres de configuration
    """
    config = Config()
    
    return {
        'api_base_url': config.API_BASE_URL,
        'max_file_size_mb': config.get_file_size_mb(),
        'request_timeout': config.REQUEST_TIMEOUT,
        'cache_ttl': config.CACHE_TTL,
        'page_size': config.PAGE_SIZE,
        'max_retries': config.MAX_RETRIES
    }


# ============================================================================
# FILE VALIDATION FUNCTIONS
# ============================================================================

def validate_pdf_format(file_data: bytes, filename: str) -> Dict[str, Any]:
    """
    Valide qu'un fichier est au format PDF valide.
    
    Args:
        file_data: Contenu binaire du fichier
        filename: Nom du fichier
        
    Returns:
        Dictionnaire avec les résultats de validation
    """
    validation_result = {
        'is_valid': False,
        'error_message': '',
        'details': {
            'has_pdf_extension': False,
            'has_pdf_signature': False,
            'has_readable_content': False,
            'page_count': 0,
            'file_size': len(file_data) if file_data else 0
        }
    }
    
    try:
        # Vérification de l'extension
        if not filename or not isinstance(filename, str):
            validation_result['error_message'] = "Nom de fichier invalide"
            return validation_result
            
        if not filename.lower().endswith('.pdf'):
            validation_result['error_message'] = "Le fichier doit avoir l'extension .pdf"
            return validation_result
            
        validation_result['details']['has_pdf_extension'] = True
        
        # Vérification du contenu
        if not file_data or len(file_data) == 0:
            validation_result['error_message'] = "Le fichier est vide"
            return validation_result
        
        # Vérification de la signature PDF
        if not file_data.startswith(b'%PDF-'):
            validation_result['error_message'] = "Le fichier ne contient pas la signature PDF valide"
            return validation_result
            
        validation_result['details']['has_pdf_signature'] = True
        
        # Tentative de lecture avec PyPDF2
        try:
            import PyPDF2
            from io import BytesIO
            
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_data))
            page_count = len(pdf_reader.pages)
            
            if page_count == 0:
                validation_result['error_message'] = "Le PDF ne contient aucune page"
                return validation_result
                
            validation_result['details']['page_count'] = page_count
            
            # Tentative d'extraction de texte de la première page
            try:
                first_page = pdf_reader.pages[0]
                text = first_page.extract_text()
                
                if text and len(text.strip()) >= 10:
                    validation_result['details']['has_readable_content'] = True
                else:
                    logger.warning("PDF avec peu ou pas de texte extractible")
                    
            except Exception as e:
                logger.warning(f"Impossible d'extraire le texte du PDF: {e}")
                
        except Exception as e:
            validation_result['error_message'] = f"Erreur lors de la lecture du PDF: {str(e)}"
            return validation_result
        
        # Si on arrive ici, le PDF est valide
        validation_result['is_valid'] = True
        validation_result['error_message'] = ""
        
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la validation PDF: {e}")
        validation_result['error_message'] = f"Erreur de validation: {str(e)}"
    
    return validation_result


def validate_file_size(file_data: bytes, max_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Valide la taille d'un fichier.
    
    Args:
        file_data: Contenu binaire du fichier
        max_size: Taille maximale en bytes (utilise Config.MAX_FILE_SIZE par défaut)
        
    Returns:
        Dictionnaire avec les résultats de validation
    """
    if max_size is None:
        max_size = Config.MAX_FILE_SIZE
    
    validation_result = {
        'is_valid': False,
        'error_message': '',
        'details': {
            'file_size': len(file_data) if file_data else 0,
            'max_size': max_size,
            'size_mb': 0.0,
            'max_size_mb': max_size / 1024 / 1024
        }
    }
    
    try:
        if not file_data:
            validation_result['error_message'] = "Aucun contenu de fichier fourni"
            return validation_result
        
        file_size = len(file_data)
        validation_result['details']['file_size'] = file_size
        validation_result['details']['size_mb'] = file_size / 1024 / 1024
        
        if file_size == 0:
            validation_result['error_message'] = "Le fichier est vide"
            return validation_result
        
        if file_size > max_size:
            validation_result['error_message'] = (
                f"Le fichier est trop volumineux "
                f"({validation_result['details']['size_mb']:.1f}MB > "
                f"{validation_result['details']['max_size_mb']:.1f}MB)"
            )
            return validation_result
        
        # Validation réussie
        validation_result['is_valid'] = True
        validation_result['error_message'] = ""
        
    except Exception as e:
        logger.error(f"Erreur lors de la validation de taille: {e}")
        validation_result['error_message'] = f"Erreur de validation de taille: {str(e)}"
    
    return validation_result


def validate_uploaded_file(file_data: bytes, filename: str, max_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Validation complète d'un fichier uploadé (format PDF + taille).
    
    Args:
        file_data: Contenu binaire du fichier
        filename: Nom du fichier
        max_size: Taille maximale en bytes (optionnel)
        
    Returns:
        Dictionnaire avec les résultats de validation complète
    """
    validation_result = {
        'is_valid': False,
        'error_message': '',
        'details': {
            'pdf_validation': {},
            'size_validation': {},
            'filename': filename,
            'overall_status': 'failed'
        }
    }
    
    try:
        # Validation de la taille en premier (plus rapide)
        size_validation = validate_file_size(file_data, max_size)
        validation_result['details']['size_validation'] = size_validation
        
        if not size_validation['is_valid']:
            validation_result['error_message'] = size_validation['error_message']
            return validation_result
        
        # Validation du format PDF
        pdf_validation = validate_pdf_format(file_data, filename)
        validation_result['details']['pdf_validation'] = pdf_validation
        
        if not pdf_validation['is_valid']:
            validation_result['error_message'] = pdf_validation['error_message']
            return validation_result
        
        # Toutes les validations ont réussi
        validation_result['is_valid'] = True
        validation_result['error_message'] = ""
        validation_result['details']['overall_status'] = 'success'
        
        logger.info(f"Fichier validé avec succès: {filename} "
                   f"({size_validation['details']['size_mb']:.1f}MB, "
                   f"{pdf_validation['details']['page_count']} pages)")
        
    except Exception as e:
        logger.error(f"Erreur lors de la validation complète du fichier: {e}")
        validation_result['error_message'] = f"Erreur de validation: {str(e)}"
    
    return validation_result


def get_file_validation_summary(validation_result: Dict[str, Any]) -> str:
    """
    Génère un résumé lisible des résultats de validation.
    
    Args:
        validation_result: Résultat de validate_uploaded_file
        
    Returns:
        Résumé formaté en français
    """
    if not validation_result.get('details'):
        return "Résultats de validation non disponibles"
    
    details = validation_result['details']
    
    if validation_result['is_valid']:
        size_mb = details.get('size_validation', {}).get('details', {}).get('size_mb', 0)
        page_count = details.get('pdf_validation', {}).get('details', {}).get('page_count', 0)
        
        return f"✅ Fichier valide: {details.get('filename', 'fichier')} ({size_mb:.1f}MB, {page_count} pages)"
    else:
        return f"❌ {validation_result.get('error_message', 'Erreur de validation')}"


def is_valid_pdf(file_data: bytes) -> bool:
    """
    Vérification rapide si un fichier est un PDF valide.
    
    Args:
        file_data: Contenu binaire du fichier
        
    Returns:
        True si le fichier est un PDF valide
    """
    if not file_data or len(file_data) < 5:
        return False
    
    return file_data.startswith(b'%PDF-')