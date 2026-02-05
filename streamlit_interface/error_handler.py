"""
Gestionnaire d'erreurs pour l'interface Streamlit CV-Optimizer.
Centralise le traitement des erreurs et la génération de messages utilisateur.

Ce module implémente:
- Mappings d'erreurs HTTP vers messages français (Exigences 6.1, 6.2)
- Logique de retry et recovery (Exigence 6.3)
- Messages d'aide contextuelle (Exigence 6.5)
- Gestion d'erreurs pour upload CV (Exigence 1.4)
- Gestion d'erreurs pour détails d'offre (Exigence 3.4)
- Gestion d'erreurs pour conseils LLM (Exigence 4.5)
"""

import requests
from typing import Optional, Dict, Any, Tuple, List
from loguru import logger
import time
import streamlit as st

from config import Config


class ErrorHandler:
    """Gestionnaire centralisé des erreurs pour l'application Streamlit."""
    
    def __init__(self):
        """Initialise le gestionnaire d'erreurs."""
        self.config = Config()
        self.retry_counts = {}  # Compteur de tentatives par endpoint
        self.error_history = []  # Historique des erreurs pour debugging
        
    def handle_api_error(self, error: Exception, endpoint: str = "", context: Dict[str, Any] = None) -> str:
        """
        Traite les erreurs d'API et retourne un message utilisateur approprié.
        
        Args:
            error: Exception levée
            endpoint: Endpoint concerné (pour le logging)
            context: Contexte additionnel pour le debugging
            
        Returns:
            Message d'erreur en français pour l'utilisateur
        """
        # Enregistrement de l'erreur dans l'historique
        error_entry = {
            "timestamp": time.time(),
            "endpoint": endpoint,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        self.error_history.append(error_entry)
        
        # Limitation de l'historique à 100 entrées
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        logger.error(f"Erreur API sur {endpoint}: {error}", extra={"context": context})
        
        if isinstance(error, requests.exceptions.ConnectionError):
            return self.handle_connection_error()
        
        elif isinstance(error, requests.exceptions.Timeout):
            return self.handle_timeout_error()
        
        elif isinstance(error, requests.exceptions.HTTPError):
            return self.handle_http_error(error)
        
        elif isinstance(error, requests.exceptions.RequestException):
            return self.handle_request_error(error)
        
        elif isinstance(error, ValueError):
            return self.handle_validation_error("validation_error", str(error))
        
        else:
            return self.handle_unknown_error(error)
    
    def handle_connection_error(self) -> str:
        """
        Traite les erreurs de connexion.
        
        Returns:
            Message d'erreur de connexion
        """
        logger.warning("Erreur de connexion au backend")
        return self.config.ERROR_MESSAGES["connection_error"]
    
    def handle_timeout_error(self) -> str:
        """
        Traite les erreurs de timeout.
        
        Returns:
            Message d'erreur de timeout
        """
        logger.warning("Timeout de requête API")
        return self.config.ERROR_MESSAGES["api_timeout"]
    
    def handle_http_error(self, error: requests.exceptions.HTTPError) -> str:
        """
        Traite les erreurs HTTP spécifiques.
        
        Args:
            error: Erreur HTTP
            
        Returns:
            Message d'erreur approprié selon le code de statut
        """
        if not hasattr(error, 'response') or error.response is None:
            return self.config.ERROR_MESSAGES["server_error"]
        
        status_code = error.response.status_code
        
        # Mapping étendu des codes d'erreur HTTP vers des messages français
        error_mapping = {
            # Erreurs client (4xx)
            400: "Requête invalide. Vérifiez les données envoyées.",
            401: self.config.ERROR_MESSAGES["unauthorized"],
            403: "Accès interdit. Vérifiez vos permissions.",
            404: self.config.ERROR_MESSAGES["not_found"],
            405: "Méthode non autorisée pour cette ressource.",
            408: "Délai d'attente de la requête dépassé.",
            409: "Conflit avec l'état actuel de la ressource.",
            410: "Ressource définitivement supprimée.",
            413: "Fichier trop volumineux. Réduisez la taille de votre CV.",
            415: "Type de média non supporté. Utilisez un fichier PDF.",
            422: "Données invalides. Vérifiez le format de votre fichier.",
            429: self.config.ERROR_MESSAGES["rate_limit"],
            
            # Erreurs serveur (5xx)
            500: self.config.ERROR_MESSAGES["server_error"],
            501: "Fonctionnalité non implémentée sur le serveur.",
            502: "Service temporairement indisponible. Réessayez dans quelques minutes.",
            503: "Service en maintenance. Réessayez plus tard.",
            504: "Délai d'attente dépassé. Le serveur met trop de temps à répondre.",
            507: "Espace de stockage insuffisant sur le serveur.",
            511: "Authentification réseau requise."
        }
        
        message = error_mapping.get(status_code, self.config.ERROR_MESSAGES["server_error"])
        
        # Tentative d'extraction du message d'erreur de l'API
        try:
            if error.response.headers.get('content-type', '').startswith('application/json'):
                error_data = error.response.json()
                api_message = error_data.get('detail', error_data.get('message', ''))
                
                if api_message and isinstance(api_message, str):
                    # Traduction de certains messages d'erreur courants
                    translated_message = self._translate_api_message(api_message)
                    if translated_message:
                        message = translated_message
                        
        except Exception as e:
            logger.debug(f"Impossible de parser la réponse d'erreur: {e}")
        
        logger.warning(f"Erreur HTTP {status_code}: {message}")
        return message
    
    def handle_request_error(self, error: requests.exceptions.RequestException) -> str:
        """
        Traite les erreurs de requête génériques.
        
        Args:
            error: Erreur de requête
            
        Returns:
            Message d'erreur réseau
        """
        logger.warning(f"Erreur de requête: {error}")
        return self.config.ERROR_MESSAGES["network_error"]
    
    def handle_unknown_error(self, error: Exception) -> str:
        """
        Traite les erreurs inconnues.
        
        Args:
            error: Exception inconnue
            
        Returns:
            Message d'erreur générique
        """
        logger.error(f"Erreur inconnue: {error}")
        return self.config.ERROR_MESSAGES["unknown_error"]
    
    def handle_validation_error(self, error_type: str, details: str = "") -> str:
        """
        Traite les erreurs de validation côté client.
        
        Args:
            error_type: Type d'erreur de validation
            details: Détails additionnels
            
        Returns:
            Message d'erreur avec conseils de correction
        """
        base_message = self.config.ERROR_MESSAGES.get(error_type, 
                                                     self.config.ERROR_MESSAGES["validation_error"])
        
        # Messages d'aide contextuelle selon le type d'erreur
        help_messages = {
            "invalid_pdf": "Assurez-vous que votre fichier est un PDF valide et non corrompu.",
            "file_too_large": f"Réduisez la taille de votre fichier ou utilisez un PDF plus léger (max {self.config.get_file_size_mb():.1f}MB).",
            "file_empty": "Sélectionnez un fichier PDF contenant votre CV.",
            "no_cv_uploaded": "Utilisez le bouton 'Parcourir' pour sélectionner votre CV au format PDF."
        }
        
        help_text = help_messages.get(error_type, "")
        
        if help_text:
            message = f"{base_message}\n\n💡 **Conseil :** {help_text}"
        else:
            message = base_message
        
        if details:
            message += f"\n\n**Détails :** {details}"
        
        logger.info(f"Erreur de validation: {error_type} - {details}")
        return message
    
    def _translate_api_message(self, api_message: str) -> Optional[str]:
        """
        Traduit les messages d'erreur de l'API en français.
        
        Args:
            api_message: Message d'erreur de l'API
            
        Returns:
            Message traduit ou None si pas de traduction
        """
        # Dictionnaire étendu de traduction des messages courants
        translations = {
            # Erreurs de fichier
            "File too large": "Fichier trop volumineux",
            "Invalid file format": "Format de fichier invalide",
            "PDF parsing failed": "Échec de l'analyse du PDF",
            "No text found in PDF": "Aucun texte trouvé dans le PDF",
            "Corrupted PDF file": "Fichier PDF corrompu",
            "Empty file": "Fichier vide",
            "File not readable": "Fichier illisible",
            
            # Erreurs d'offres d'emploi
            "Job not found": "Offre d'emploi non trouvée",
            "Invalid job ID": "Identifiant d'offre invalide",
            "Job expired": "Cette offre d'emploi a expiré",
            "Job no longer available": "Cette offre n'est plus disponible",
            
            # Erreurs de service LLM
            "LLM service unavailable": "Service de conseils temporairement indisponible",
            "AI service timeout": "Le service d'intelligence artificielle ne répond pas",
            "Content generation failed": "Échec de la génération de contenu",
            "Model overloaded": "Service temporairement surchargé, réessayez plus tard",
            
            # Erreurs de réseau et serveur
            "Rate limit exceeded": "Trop de requêtes, veuillez patienter",
            "Internal server error": "Erreur interne du serveur",
            "Database connection failed": "Problème de connexion à la base de données",
            "Service temporarily unavailable": "Service temporairement indisponible",
            
            # Erreurs de validation
            "Invalid request format": "Format de requête invalide",
            "Missing required field": "Champ obligatoire manquant",
            "Invalid parameter value": "Valeur de paramètre invalide",
            "Request too large": "Requête trop volumineuse",
            
            # Erreurs d'authentification
            "Authentication failed": "Échec de l'authentification",
            "Token expired": "Jeton d'accès expiré",
            "Insufficient permissions": "Permissions insuffisantes"
        }
        
        # Recherche de correspondances exactes d'abord
        if api_message in translations:
            return translations[api_message]
        
        # Recherche de correspondances partielles
        for english, french in translations.items():
            if english.lower() in api_message.lower():
                return french
        
        return None
    
    def should_retry(self, error: Exception, endpoint: str) -> bool:
        """
        Détermine si une requête doit être retentée.
        
        Args:
            error: Exception levée
            endpoint: Endpoint concerné
            
        Returns:
            True si la requête doit être retentée
        """
        # Initialisation du compteur pour cet endpoint
        if endpoint not in self.retry_counts:
            self.retry_counts[endpoint] = 0
        
        # Vérification du nombre maximum de tentatives
        if self.retry_counts[endpoint] >= self.config.MAX_RETRIES:
            logger.warning(f"Nombre maximum de tentatives atteint pour {endpoint}")
            return False
        
        # Types d'erreurs qui justifient un retry
        retryable_errors = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        )
        
        # Codes HTTP qui justifient un retry
        retryable_status_codes = [502, 503, 504]
        
        should_retry = False
        
        if isinstance(error, retryable_errors):
            should_retry = True
        elif isinstance(error, requests.exceptions.HTTPError):
            if hasattr(error, 'response') and error.response:
                should_retry = error.response.status_code in retryable_status_codes
        
        if should_retry:
            self.retry_counts[endpoint] += 1
            wait_time = self.config.RETRY_DELAY * (2 ** (self.retry_counts[endpoint] - 1))
            logger.info(f"Retry {self.retry_counts[endpoint]}/{self.config.MAX_RETRIES} pour {endpoint} dans {wait_time}s")
            time.sleep(wait_time)
        
        return should_retry
    
    def reset_retry_count(self, endpoint: str):
        """
        Remet à zéro le compteur de tentatives pour un endpoint.
        
        Args:
            endpoint: Endpoint à réinitialiser
        """
        if endpoint in self.retry_counts:
            del self.retry_counts[endpoint]
    
    def get_error_context(self, error: Exception) -> Dict[str, Any]:
        """
        Extrait le contexte d'une erreur pour le debugging.
        
        Args:
            error: Exception à analyser
            
        Returns:
            Dictionnaire avec le contexte d'erreur
        """
        context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": time.time()
        }
        
        if isinstance(error, requests.exceptions.HTTPError):
            if hasattr(error, 'response') and error.response:
                context.update({
                    "status_code": error.response.status_code,
                    "response_headers": dict(error.response.headers),
                    "request_url": error.response.url
                })
                
                try:
                    context["response_body"] = error.response.text[:500]  # Limité à 500 chars
                except:
                    context["response_body"] = "Unable to read response body"
        
        return context
    
    def handle_cv_upload_error(self, error: Exception, filename: str = "") -> Tuple[str, str]:
        """
        Gère spécifiquement les erreurs d'upload de CV (Exigence 1.4).
        
        Args:
            error: Exception levée lors de l'upload
            filename: Nom du fichier uploadé
            
        Returns:
            Tuple (message_erreur, type_erreur) pour l'affichage Streamlit
        """
        logger.error(f"Erreur upload CV {filename}: {error}")
        
        if isinstance(error, ValueError):
            error_msg = str(error)
            if "trop volumineux" in error_msg.lower():
                return self.handle_validation_error("file_too_large", f"Fichier: {filename}"), "error"
            elif "vide" in error_msg.lower():
                return self.handle_validation_error("file_empty", f"Fichier: {filename}"), "error"
            elif "format" in error_msg.lower():
                return self.handle_validation_error("invalid_pdf", f"Fichier: {filename}"), "error"
            else:
                return self.handle_validation_error("validation_error", error_msg), "error"
        
        elif isinstance(error, requests.exceptions.RequestException):
            return self.handle_api_error(error, "/api/match"), "error"
        
        else:
            return f"Erreur inattendue lors de l'upload de {filename}: {str(error)}", "error"
    
    def handle_job_details_error(self, error: Exception, job_id: str) -> Tuple[str, str]:
        """
        Gère spécifiquement les erreurs de récupération des détails d'offre (Exigence 3.4).
        
        Args:
            error: Exception levée
            job_id: Identifiant de l'offre
            
        Returns:
            Tuple (message_erreur, type_erreur) pour l'affichage Streamlit
        """
        logger.error(f"Erreur détails offre {job_id}: {error}")
        
        if isinstance(error, requests.exceptions.HTTPError):
            if hasattr(error, 'response') and error.response:
                if error.response.status_code == 404:
                    return "Cette offre d'emploi n'existe plus ou a été supprimée.", "warning"
                elif error.response.status_code == 403:
                    return "Vous n'avez pas l'autorisation d'accéder à cette offre.", "error"
        
        elif isinstance(error, requests.exceptions.ConnectionError):
            return "Impossible de récupérer les détails de l'offre. Vérifiez votre connexion.", "error"
        
        elif isinstance(error, requests.exceptions.Timeout):
            return "La récupération des détails prend trop de temps. Réessayez.", "warning"
        
        return self.handle_api_error(error, f"/api/jobs/{job_id}"), "error"
    
    def handle_advice_generation_error(self, error: Exception, job_id: str) -> Tuple[str, str]:
        """
        Gère spécifiquement les erreurs de génération de conseils LLM (Exigence 4.5).
        
        Args:
            error: Exception levée
            job_id: Identifiant de l'offre
            
        Returns:
            Tuple (message_erreur, type_erreur) pour l'affichage Streamlit
        """
        logger.error(f"Erreur génération conseils pour {job_id}: {error}")
        
        if isinstance(error, requests.exceptions.HTTPError):
            if hasattr(error, 'response') and error.response:
                if error.response.status_code == 503:
                    return ("Le service de génération de conseils est temporairement indisponible. "
                           "Réessayez dans quelques minutes."), "warning"
                elif error.response.status_code == 429:
                    return ("Trop de demandes de conseils en cours. "
                           "Patientez quelques instants avant de réessayer."), "info"
                elif error.response.status_code == 422:
                    return ("Impossible de générer des conseils pour cette combinaison CV/offre. "
                           "Vérifiez que votre CV contient suffisamment d'informations."), "warning"
        
        elif isinstance(error, requests.exceptions.Timeout):
            return ("La génération de conseils prend plus de temps que prévu. "
                   "Cela peut arriver pour des analyses complexes. Réessayez."), "warning"
        
        elif isinstance(error, ValueError):
            if "cv" in str(error).lower():
                return "Veuillez d'abord uploader un CV valide avant de demander des conseils.", "info"
            elif "job_id" in str(error).lower():
                return "Identifiant d'offre invalide pour la génération de conseils.", "error"
        
        return self.handle_api_error(error, "/api/advice"), "error"
    
    def display_error_in_streamlit(self, message: str, error_type: str = "error"):
        """
        Affiche une erreur dans l'interface Streamlit avec le bon niveau de gravité.
        
        Args:
            message: Message d'erreur à afficher
            error_type: Type d'erreur ("error", "warning", "info")
        """
        if error_type == "error":
            st.error(message)
        elif error_type == "warning":
            st.warning(message)
        elif error_type == "info":
            st.info(message)
        else:
            st.error(message)  # Par défaut, traiter comme une erreur
    
    def get_recovery_suggestions(self, error_type: str, context: Dict[str, Any] = None) -> List[str]:
        """
        Fournit des suggestions de récupération selon le type d'erreur (Exigence 6.5).
        
        Args:
            error_type: Type d'erreur rencontrée
            context: Contexte additionnel
            
        Returns:
            Liste de suggestions pour résoudre le problème
        """
        context = context or {}
        
        suggestions = {
            "connection_error": [
                "Vérifiez votre connexion internet",
                "Assurez-vous que le serveur CV-Optimizer est démarré",
                "Contactez l'administrateur si le problème persiste"
            ],
            "file_too_large": [
                f"Réduisez la taille de votre PDF (maximum {self.config.get_file_size_mb():.1f}MB)",
                "Compressez votre PDF avec un outil en ligne",
                "Supprimez les images haute résolution du document"
            ],
            "invalid_pdf": [
                "Vérifiez que votre fichier est un PDF valide",
                "Essayez d'ouvrir le fichier avec un lecteur PDF",
                "Reconvertissez votre document en PDF si nécessaire"
            ],
            "no_cv_uploaded": [
                "Utilisez le bouton 'Parcourir' pour sélectionner votre CV",
                "Assurez-vous que le fichier est au format PDF",
                "Vérifiez que l'upload s'est terminé avec succès"
            ],
            "api_timeout": [
                "Réessayez dans quelques instants",
                "Vérifiez votre connexion internet",
                "Le serveur peut être temporairement surchargé"
            ],
            "rate_limit": [
                "Patientez quelques minutes avant de réessayer",
                "Évitez de faire trop de requêtes simultanées",
                "Contactez l'administrateur si vous avez des besoins spécifiques"
            ],
            "llm_unavailable": [
                "Le service d'IA est temporairement indisponible",
                "Réessayez dans quelques minutes",
                "Consultez les détails de l'offre en attendant"
            ]
        }
        
        return suggestions.get(error_type, [
            "Réessayez l'opération",
            "Vérifiez votre connexion",
            "Contactez le support si le problème persiste"
        ])
    
    def clear_error_history(self):
        """Vide l'historique des erreurs."""
        self.error_history.clear()
        logger.info("Historique des erreurs vidé")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur les erreurs rencontrées.
        
        Returns:
            Dictionnaire avec les statistiques d'erreurs
        """
        if not self.error_history:
            return {"total_errors": 0, "error_types": {}, "endpoints": {}}
        
        error_types = {}
        endpoints = {}
        
        for error in self.error_history:
            error_type = error["error_type"]
            endpoint = error["endpoint"]
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            if endpoint:
                endpoints[endpoint] = endpoints.get(endpoint, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "endpoints": endpoints,
            "last_error_time": max(error["timestamp"] for error in self.error_history) if self.error_history else None
        }