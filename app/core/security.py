"""
Gestion de la sécurité de l'API.
Authentification par API key pour les endpoints admin.
"""

from fastapi import Header
from typing import Optional

from app.config import settings
from app.core.exceptions import AuthenticationError


async def verify_api_key(x_api_key: str = Header(..., description="Clé API admin")) -> str:
    """
    Vérifie la validité de l'API key pour les endpoints admin.
    
    Args:
        x_api_key: Clé API fournie dans le header X-API-Key
    
    Returns:
        La clé API si valide
    
    Raises:
        AuthenticationError: Si la clé est absente ou invalide
    
    Usage dans un endpoint:
        @app.post("/admin/collect")
        async def collect(api_key: str = Depends(verify_api_key)):
            # Endpoint protégé
            ...
    """
    if x_api_key != settings.API_KEY_ADMIN:
        raise AuthenticationError(
            message="API key invalide",
            detail={"provided_key": x_api_key[:8] + "..." if len(x_api_key) > 8 else "***"}
        )
    
    return x_api_key


def validate_file_upload(
    filename: str,
    file_size: int,
    content_type: Optional[str] = None
) -> None:
    """
    Valide un fichier uploadé (extension, taille, type MIME).
    
    Args:
        filename: Nom du fichier
        file_size: Taille en octets
        content_type: Type MIME (ex: 'application/pdf')
    
    Raises:
        InvalidFileError: Si le fichier ne respecte pas les contraintes
    
    Usage:
        validate_file_upload(
            filename=file.filename,
            file_size=len(await file.read()),
            content_type=file.content_type
        )
    """
    from app.core.exceptions import InvalidFileError
    
    # Vérification de l'extension
    file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise InvalidFileError(
            message=f"Format de fichier non autorisé: {file_ext}",
            detail={
                "allowed_extensions": settings.ALLOWED_EXTENSIONS,
                "provided": file_ext
            }
        )
    
    # Vérification de la taille (conversion MB en bytes)
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise InvalidFileError(
            message=f"Fichier trop volumineux ({file_size / 1024 / 1024:.2f} MB)",
            detail={
                "max_size_mb": settings.MAX_UPLOAD_SIZE_MB,
                "file_size_mb": round(file_size / 1024 / 1024, 2)
            }
        )
    
    # Vérification optionnelle du type MIME
    if content_type and content_type not in ["application/pdf"]:
        raise InvalidFileError(
            message=f"Type MIME non autorisé: {content_type}",
            detail={"allowed": ["application/pdf"], "provided": content_type}
        )


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour éviter les injections de path.
    
    Args:
        filename: Nom de fichier à nettoyer
    
    Returns:
        Nom de fichier sécurisé
    
    Example:
        >>> sanitize_filename("../../etc/passwd")
        'passwd'
        >>> sanitize_filename("mon CV (2024).pdf")
        'mon_CV_2024.pdf'
    """
    import re
    
    # Récupère uniquement le nom du fichier (pas le path)
    filename = filename.split("/")[-1].split("\\")[-1]
    
    # Remplace les caractères dangereux
    filename = re.sub(r'[^\w\s\-\.]', '_', filename)
    
    # Collapse les underscores multiples
    filename = re.sub(r'_+', '_', filename)
    
    return filename.strip("_")
