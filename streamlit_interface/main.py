"""
Point d'entrée principal de l'interface Streamlit CV-Optimizer.
Configure l'application Streamlit et gère la navigation principale.
"""

import streamlit as st
from loguru import logger
import sys

from config import Config
from api_client import APIClient
from state_manager import StateManager
from ui_components import UIComponents
from error_handler import ErrorHandler

# Configuration du logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)


class StreamlitApp:
    """Application principale Streamlit CV-Optimizer."""
    
    def __init__(self):
        """Initialise l'application avec ses composants principaux."""
        self.config = Config()
        self.api_client = APIClient(base_url=self.config.API_BASE_URL)
        self.state_manager = StateManager()
        self.ui_components = UIComponents()
        self.error_handler = ErrorHandler()
        
    def configure_page(self):
        """Configure la page Streamlit avec titre, icône et layout."""
        st.set_page_config(
            page_title="CV-Optimizer",
            page_icon="🎯",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': None,
                'Report a bug': None,
                'About': "CV-Optimizer - Interface Streamlit pour le matching de CV et la recherche d'emploi"
            }
        )
        
    def check_backend_health(self):
        """Vérifie la connectivité au backend au démarrage."""
        if not st.session_state.get('health_checked', False):
            with st.spinner("Vérification de la connexion au serveur..."):
                try:
                    if self.api_client.health_check():
                        st.session_state.health_checked = True
                        logger.info("Connexion au backend établie")
                    else:
                        st.error("❌ Impossible de se connecter au serveur backend")
                        st.info("Vérifiez que le serveur FastAPI est démarré sur " + self.config.API_BASE_URL)
                        st.stop()
                except Exception as e:
                    error_msg = self.error_handler.handle_connection_error()
                    st.error(f"❌ {error_msg}")
                    st.info("Vérifiez que le serveur FastAPI est démarré sur " + self.config.API_BASE_URL)
                    st.stop()
    
    def render_header(self):
        """Affiche l'en-tête de l'application."""
        st.title("🎯 CV-Optimizer")
        st.markdown("**Interface Streamlit pour le matching de CV et la recherche d'emploi**")
        st.divider()
    
    def render_main_interface(self):
        """Affiche l'interface principale avec upload et résultats."""
        # Section upload de CV
        st.header("📄 Upload de CV")
        uploaded_cv = self.ui_components.render_cv_uploader()
        
        if uploaded_cv:
            self.state_manager.set_uploaded_cv(uploaded_cv.read(), uploaded_cv.name)
            st.success(f"✅ CV uploadé : {uploaded_cv.name}")
            
            # Bouton d'analyse
            if st.button("🔍 Analyser le CV", type="primary"):
                self.analyze_cv()
        
        # Affichage des résultats si disponibles
        if st.session_state.get('job_matches'):
            st.divider()
            self.render_job_results()
    
    def analyze_cv(self):
        """Analyse le CV uploadé et récupère les offres correspondantes."""
        cv_data, cv_filename = self.state_manager.get_uploaded_cv()
        
        if not cv_data:
            st.error("❌ Aucun CV uploadé")
            return
        
        with st.spinner("Analyse du CV en cours..."):
            try:
                # Appel API pour le matching
                results = self.api_client.match_cv(cv_data)
                
                if results:
                    st.session_state.job_matches = results
                    st.success(f"✅ {len(results)} offres trouvées")
                    st.rerun()
                else:
                    st.warning("⚠️ Aucune offre correspondante trouvée")
                    
            except Exception as e:
                error_msg = self.error_handler.handle_api_error(e)
                st.error(f"❌ {error_msg}")
    
    def render_job_results(self):
        """Affiche les résultats des offres d'emploi."""
        st.header("📋 Offres d'Emploi Correspondantes")
        
        # Filtres
        filters = self.ui_components.render_job_filters()
        
        # Application des filtres si modifiés
        if filters != st.session_state.get('current_filters', {}):
            st.session_state.current_filters = filters
            self.apply_filters(filters)
        
        # Affichage de la liste des offres
        job_matches = st.session_state.get('job_matches', [])
        if job_matches:
            self.ui_components.render_job_list(job_matches)
    
    def apply_filters(self, filters):
        """Applique les filtres aux offres d'emploi."""
        with st.spinner("Application des filtres..."):
            try:
                # Appel API avec filtres
                filtered_results = self.api_client.get_jobs(filters)
                
                if filtered_results and filtered_results.jobs:
                    st.session_state.job_matches = filtered_results.jobs
                    st.rerun()
                else:
                    st.session_state.job_matches = []
                    st.rerun()
                    
            except Exception as e:
                error_msg = self.error_handler.handle_api_error(e)
                st.error(f"❌ {error_msg}")
    
    def run(self):
        """Point d'entrée principal de l'application."""
        # Configuration de la page
        self.configure_page()
        
        # Initialisation de l'état
        self.state_manager.init_session_state()
        
        # Vérification de la santé du backend
        self.check_backend_health()
        
        # Affichage de l'interface
        self.render_header()
        self.render_main_interface()


def main():
    """Fonction principale pour lancer l'application Streamlit."""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()