"""
Gestionnaire d'état pour l'application Streamlit CV-Optimizer.
Gère la persistance des données dans la session Streamlit.
"""

import streamlit as st
from typing import Optional, Tuple, List
from loguru import logger

from models import JobFilters, JobMatch, JobDetails, AdviceResponse, SessionData, NavigationState
from config import Config


class StateManager:
    """Gestionnaire d'état de session pour l'application Streamlit."""
    
    def __init__(self):
        """Initialise le gestionnaire d'état."""
        self.config = Config()
        
    def init_session_state(self):
        """Initialise les variables de session Streamlit si elles n'existent pas."""
        
        # Données de session principales
        if 'session_data' not in st.session_state:
            st.session_state.session_data = SessionData()
            logger.info("Session Streamlit initialisée")
        
        # État de santé du backend
        if 'health_checked' not in st.session_state:
            st.session_state.health_checked = False
        
        # Cache des requêtes API
        if 'api_cache' not in st.session_state:
            st.session_state.api_cache = {}
        
        # Timestamp de dernière activité
        if 'last_activity' not in st.session_state:
            import time
            st.session_state.last_activity = time.time()
    
    def set_uploaded_cv(self, cv_data: bytes, filename: str):
        """
        Stocke le CV uploadé en session.
        
        Args:
            cv_data: Contenu binaire du fichier PDF
            filename: Nom du fichier
        """
        if not cv_data or not filename:
            logger.warning("Tentative de stockage d'un CV vide")
            return
        
        st.session_state.session_data.uploaded_cv = cv_data
        st.session_state.session_data.cv_filename = filename
        
        # Réinitialisation des résultats précédents
        st.session_state.session_data.job_matches = []
        st.session_state.session_data.current_advice = None
        
        logger.info(f"CV stocké en session: {filename} ({len(cv_data)} bytes)")
    
    def get_uploaded_cv(self) -> Optional[Tuple[bytes, str]]:
        """
        Récupère le CV de la session.
        
        Returns:
            Tuple (contenu, nom_fichier) ou None si aucun CV
        """
        session_data = st.session_state.session_data
        
        if session_data.has_cv():
            return session_data.uploaded_cv, session_data.cv_filename
        
        return None
    
    def has_uploaded_cv(self) -> bool:
        """
        Vérifie si un CV est uploadé.
        
        Returns:
            True si un CV est présent en session
        """
        return st.session_state.session_data.has_cv()
    
    def set_job_matches(self, matches: List[JobMatch]):
        """
        Stocke les résultats de matching en session.
        
        Args:
            matches: Liste des offres correspondantes
        """
        st.session_state.session_data.job_matches = matches
        logger.info(f"Résultats de matching stockés: {len(matches)} offres")
    
    def get_job_matches(self) -> List[JobMatch]:
        """
        Récupère les résultats de matching de la session.
        
        Returns:
            Liste des offres correspondantes
        """
        return st.session_state.session_data.job_matches or []
    
    def set_current_filters(self, filters: JobFilters):
        """
        Stocke les filtres actuels en session.
        
        Args:
            filters: Filtres à appliquer
        """
        st.session_state.session_data.current_filters = filters
        logger.debug(f"Filtres mis à jour: {filters}")
    
    def get_current_filters(self) -> JobFilters:
        """
        Récupère les filtres actuels de la session.
        
        Returns:
            Filtres actuellement appliqués
        """
        return st.session_state.session_data.current_filters or JobFilters()
    
    def set_selected_job_details(self, job_details: JobDetails):
        """
        Stocke les détails de l'offre sélectionnée.
        
        Args:
            job_details: Détails complets de l'offre
        """
        st.session_state.session_data.selected_job_details = job_details
        st.session_state.session_data.navigation.selected_job_id = job_details.job_id
        logger.info(f"Détails d'offre stockés: {job_details.title}")
    
    def get_selected_job_details(self) -> Optional[JobDetails]:
        """
        Récupère les détails de l'offre sélectionnée.
        
        Returns:
            Détails de l'offre ou None
        """
        return st.session_state.session_data.selected_job_details
    
    def set_current_advice(self, advice: AdviceResponse):
        """
        Stocke les conseils LLM actuels.
        
        Args:
            advice: Conseils personnalisés
        """
        st.session_state.session_data.current_advice = advice
        logger.info(f"Conseils stockés pour l'offre {advice.job_id}")
    
    def get_current_advice(self) -> Optional[AdviceResponse]:
        """
        Récupère les conseils LLM actuels.
        
        Returns:
            Conseils personnalisés ou None
        """
        return st.session_state.session_data.current_advice
    
    def set_navigation_page(self, page: str, job_id: Optional[str] = None):
        """
        Met à jour l'état de navigation.
        
        Args:
            page: Page courante ("home", "job_details", "advice")
            job_id: ID de l'offre sélectionnée (optionnel)
        """
        navigation = st.session_state.session_data.navigation
        navigation.current_page = page
        
        if job_id:
            navigation.selected_job_id = job_id
        
        logger.debug(f"Navigation mise à jour: {page} (job_id: {job_id})")
    
    def get_navigation_state(self) -> NavigationState:
        """
        Récupère l'état de navigation actuel.
        
        Returns:
            État de navigation
        """
        return st.session_state.session_data.navigation
    
    def clear_cv_data(self):
        """Supprime toutes les données liées au CV."""
        st.session_state.session_data.clear_cv()
        logger.info("Données CV supprimées de la session")
    
    def clear_search_results(self):
        """Supprime les résultats de recherche."""
        st.session_state.session_data.clear_results()
        logger.info("Résultats de recherche supprimés")
    
    def clear_session(self):
        """Réinitialise complètement la session."""
        st.session_state.session_data = SessionData()
        st.session_state.health_checked = False
        st.session_state.api_cache = {}
        
        logger.info("Session complètement réinitialisée")
    
    def update_activity_timestamp(self):
        """Met à jour le timestamp de dernière activité."""
        import time
        st.session_state.last_activity = time.time()
    
    def get_cache_key(self, endpoint: str, params: dict = None) -> str:
        """
        Génère une clé de cache pour les requêtes API.
        
        Args:
            endpoint: Endpoint de l'API
            params: Paramètres de la requête
            
        Returns:
            Clé de cache unique
        """
        import hashlib
        
        cache_data = f"{endpoint}_{params or {}}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def get_cached_response(self, cache_key: str) -> Optional[dict]:
        """
        Récupère une réponse du cache si elle est encore valide.
        
        Args:
            cache_key: Clé de cache
            
        Returns:
            Réponse cachée ou None si expirée/inexistante
        """
        import time
        
        cache = st.session_state.api_cache.get(cache_key)
        
        if cache:
            # Vérification de l'expiration
            if time.time() - cache['timestamp'] < self.config.CACHE_TTL:
                logger.debug(f"Cache hit pour {cache_key}")
                return cache['data']
            else:
                # Suppression du cache expiré
                del st.session_state.api_cache[cache_key]
                logger.debug(f"Cache expiré pour {cache_key}")
        
        return None
    
    def set_cached_response(self, cache_key: str, data: dict):
        """
        Stocke une réponse dans le cache.
        
        Args:
            cache_key: Clé de cache
            data: Données à cacher
        """
        import time
        
        st.session_state.api_cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        
        logger.debug(f"Réponse mise en cache pour {cache_key}")
    
    def clear_cache(self):
        """Vide le cache des requêtes API."""
        st.session_state.api_cache = {}
        logger.info("Cache API vidé")
    
    def get_session_info(self) -> dict:
        """
        Retourne des informations sur la session courante.
        
        Returns:
            Dictionnaire avec les informations de session
        """
        session_data = st.session_state.session_data
        
        return {
            "has_cv": session_data.has_cv(),
            "cv_filename": session_data.cv_filename,
            "job_matches_count": len(session_data.job_matches or []),
            "current_page": session_data.navigation.current_page,
            "selected_job_id": session_data.navigation.selected_job_id,
            "has_advice": session_data.current_advice is not None,
            "cache_entries": len(st.session_state.api_cache),
            "last_activity": st.session_state.get('last_activity', 0)
        }