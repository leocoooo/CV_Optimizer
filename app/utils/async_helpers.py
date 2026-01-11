"""
Helpers pour gérer les appels synchrones depuis des endpoints asynchrones.
Permet d'utiliser les services existants (sync) dans FastAPI (async).
"""

import asyncio
from typing import TypeVar, Callable, Any
from loguru import logger

T = TypeVar('T')


async def run_in_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Exécute une fonction synchrone dans un thread séparé.
    
    Permet d'utiliser des services synchrones (cv_reader, embedder, matcher, etc.)
    dans des endpoints asynchrones FastAPI sans bloquer l'event loop.
    
    Args:
        func: Fonction synchrone à exécuter
        *args: Arguments positionnels
        **kwargs: Arguments nommés
    
    Returns:
        Le résultat de la fonction
    
    Example:
        >>> reader = CVReader()
        >>> text = await run_in_thread(reader.extract_text, "cv.pdf")
    """
    try:
        return await asyncio.to_thread(func, *args, **kwargs)
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution en thread de {func.__name__}: {e}")
        raise

