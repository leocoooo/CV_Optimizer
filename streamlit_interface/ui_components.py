"""
Composants UI réutilisables pour l'interface Streamlit CV-Optimizer.
Contient tous les widgets et éléments d'interface utilisateur.
"""

import streamlit as st
from typing import List, Optional, Dict, Any
import PyPDF2
from io import BytesIO
from loguru import logger

from models import JobFilters, JobMatch, JobDetails, AdviceResponse
from config import Config


class UIComponents:
    """Composants UI réutilisables pour l'application Streamlit."""
    
    def __init__(self):
        """Initialise les composants UI."""
        self.config = Config()
    
    def render_cv_uploader(self) -> Optional[st.runtime.uploaded_file_manager.UploadedFile]:
        """
        Affiche le widget d'upload de CV avec validation.
        
        Returns:
            Fichier uploadé ou None
        """
        st.markdown("### 📄 Sélectionnez votre CV")
        
        uploaded_file = st.file_uploader(
            label="Choisissez un fichier PDF",
            type=["pdf"],
            help=f"Taille maximale : {self.config.get_file_size_mb():.1f}MB",
            key="cv_uploader"
        )
        
        if uploaded_file is not None:
            # Validation de la taille
            if not self.config.is_valid_file_size(uploaded_file.size):
                st.error(f"❌ {self.config.ERROR_MESSAGES['file_too_large']}")
                return None
            
            # Validation du contenu PDF
            if not self._validate_pdf_content(uploaded_file):
                st.error(f"❌ {self.config.ERROR_MESSAGES['invalid_pdf']}")
                return None
            
            # Affichage des informations du fichier
            st.success(f"✅ Fichier valide : {uploaded_file.name}")
            st.info(f"📊 Taille : {uploaded_file.size / 1024:.1f} KB")
            
            return uploaded_file
        
        return None
    
    def render_job_filters(self) -> JobFilters:
        """
        Affiche les contrôles de filtrage des offres.
        
        Returns:
            Filtres sélectionnés par l'utilisateur
        """
        st.markdown("### 🔍 Filtres de recherche")
        
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            location = st.text_input(
                "📍 Localisation",
                value=st.session_state.get('filter_location', ''),
                placeholder="Paris, Lyon, Remote...",
                key="filter_location"
            )
        
        with col2:
            contract_type = st.selectbox(
                "📄 Type de contrat",
                options=self.config.CONTRACT_TYPES,
                index=0,
                format_func=lambda x: "Tous les types" if x == "" else x,
                key="filter_contract_type"
            )
        
        with col3:
            experience_level = st.selectbox(
                "🎯 Niveau d'expérience",
                options=self.config.EXPERIENCE_LEVELS,
                index=0,
                format_func=lambda x: "Tous les niveaux" if x == "" else x,
                key="filter_experience_level"
            )
        
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)  # Espacement
            if st.button("🔄 Reset", help="Réinitialiser tous les filtres"):
                self._reset_filters()
                st.rerun()
        
        return JobFilters(
            location=location if location else None,
            contract_type=contract_type if contract_type else None,
            experience_level=experience_level if experience_level else None
        )
    
    def render_job_list(self, jobs: List[JobMatch]):
        """
        Affiche la liste des offres d'emploi.
        
        Args:
            jobs: Liste des offres à afficher
        """
        if not jobs:
            st.info("ℹ️ Aucune offre à afficher")
            return
        
        st.markdown(f"### 📋 {len(jobs)} offre(s) trouvée(s)")
        
        for i, job in enumerate(jobs):
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Titre et entreprise
                    st.markdown(f"**{job.title}**")
                    st.markdown(f"🏢 {job.company}")
                    
                    # Informations complémentaires
                    info_cols = st.columns(3)
                    with info_cols[0]:
                        st.markdown(f"📍 {job.location}")
                    with info_cols[1]:
                        st.markdown(f"📄 {job.contract_type}")
                    with info_cols[2]:
                        if job.match_score > 0:
                            score_color = job.score_color
                            st.markdown(f"⭐ <span style='color: {score_color}'>{job.match_percentage}%</span>", 
                                      unsafe_allow_html=True)
                    
                    # Résumé
                    if job.summary:
                        st.markdown(f"*{job.summary}*")
                
                with col2:
                    if st.button("👁️ Voir détails", key=f"view_job_{job.job_id}"):
                        st.session_state.selected_job_id = job.job_id
                        st.session_state.show_job_details = True
                        st.rerun()
                
                st.divider()
    
    def render_job_details(self, job_details: JobDetails):
        """
        Affiche les détails complets d'une offre d'emploi.
        
        Args:
            job_details: Détails de l'offre à afficher
        """
        # En-tête avec bouton retour
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Retour", key="back_to_list"):
                st.session_state.show_job_details = False
                if 'selected_job_id' in st.session_state:
                    del st.session_state.selected_job_id
                st.rerun()
        
        with col2:
            st.markdown(f"# 💼 {job_details.title}")
        
        # Informations principales
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown(f"**🏢 Entreprise :** {job_details.company}")
            st.markdown(f"**📍 Localisation :** {job_details.location}")
        
        with info_col2:
            st.markdown(f"**📄 Type de contrat :** {job_details.contract_type}")
            st.markdown(f"**🎯 Expérience requise :** {job_details.experience_level}")
        
        if job_details.salary_range:
            st.markdown(f"**💰 Salaire :** {job_details.salary_range}")
        
        st.divider()
        
        # Description
        if job_details.description:
            st.markdown("### 📝 Description du poste")
            st.markdown(job_details.description)
            st.divider()
        
        # Exigences
        if job_details.has_requirements():
            st.markdown("### ✅ Exigences")
            for req in job_details.requirements:
                st.markdown(f"• {req}")
            st.divider()
        
        # Avantages
        if job_details.has_benefits():
            st.markdown("### 🎁 Avantages")
            for benefit in job_details.benefits:
                st.markdown(f"• {benefit}")
            st.divider()
        
        # Lien vers l'offre
        if job_details.url:
            st.markdown(f"🔗 [Voir l'offre complète]({job_details.url})")
        
        # Bouton conseils (si CV uploadé)
        if st.session_state.get('session_data', {}).get('uploaded_cv'):
            st.divider()
            if st.button("🤖 Obtenir des conseils personnalisés", 
                        type="primary", 
                        key="get_advice_btn"):
                st.session_state.request_advice = job_details.job_id
                st.rerun()
    
    def render_advice_section(self, advice: AdviceResponse):
        """
        Affiche les conseils personnalisés du LLM.
        
        Args:
            advice: Conseils à afficher
        """
        st.markdown("### 🤖 Conseils personnalisés")
        
        # Score global
        if advice.overall_score > 0:
            score_color = "green" if advice.score_percentage >= 70 else "orange" if advice.score_percentage >= 50 else "red"
            st.markdown(f"**Score de correspondance :** <span style='color: {score_color}'>{advice.score_percentage}%</span>", 
                       unsafe_allow_html=True)
        
        # Zones d'amélioration
        if advice.improvement_areas:
            st.markdown("**🎯 Zones d'amélioration prioritaires :**")
            for area in advice.improvement_areas:
                st.markdown(f"• {area}")
            st.divider()
        
        # Conseils détaillés
        if advice.advice_text:
            st.markdown("**💡 Recommandations détaillées :**")
            
            # Parsing en sections si possible
            sections = advice.parse_advice_sections()
            
            for section in sections:
                with st.expander(f"{section.priority_icon} {section.section_title}", expanded=True):
                    st.markdown(section.content)
        
        # Timestamp
        if advice.generated_at:
            st.caption(f"Conseils générés le {advice.generated_at}")
    
    def render_loading_spinner(self, message: str = "Chargement..."):
        """
        Affiche un indicateur de chargement.
        
        Args:
            message: Message à afficher pendant le chargement
        """
        return st.spinner(message)
    
    def render_error_message(self, message: str, error_type: str = "error"):
        """
        Affiche un message d'erreur formaté.
        
        Args:
            message: Message d'erreur
            error_type: Type d'erreur (error, warning, info)
        """
        if error_type == "error":
            st.error(f"❌ {message}")
        elif error_type == "warning":
            st.warning(f"⚠️ {message}")
        else:
            st.info(f"ℹ️ {message}")
    
    def render_success_message(self, message: str):
        """
        Affiche un message de succès.
        
        Args:
            message: Message de succès
        """
        st.success(f"✅ {message}")
    
    def render_progress_bar(self, progress: float, message: str = ""):
        """
        Affiche une barre de progression.
        
        Args:
            progress: Progression de 0.0 à 1.0
            message: Message optionnel
        """
        if message:
            st.markdown(message)
        return st.progress(progress)
    
    def _validate_pdf_content(self, uploaded_file) -> bool:
        """
        Valide le contenu d'un fichier PDF en utilisant les fonctions de validation améliorées.
        
        Args:
            uploaded_file: Fichier uploadé
            
        Returns:
            True si le PDF est valide
        """
        try:
            # Réinitialisation du pointeur de fichier
            uploaded_file.seek(0)
            
            # Lecture du contenu
            file_data = uploaded_file.read()
            
            # Utilisation de la fonction de validation améliorée
            from utils import validate_pdf_format
            validation_result = validate_pdf_format(file_data, uploaded_file.name)
            
            if not validation_result['is_valid']:
                logger.warning(f"Validation PDF échouée: {validation_result['error_message']}")
                return False
            
            # Log des détails de validation
            details = validation_result.get('details', {})
            logger.info(f"PDF valide: {uploaded_file.name} - "
                       f"{details.get('page_count', 0)} pages, "
                       f"contenu extractible: {details.get('has_readable_content', False)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation PDF: {e}")
            return False
        finally:
            # Réinitialisation du pointeur pour utilisation ultérieure
            uploaded_file.seek(0)
    
    def _reset_filters(self):
        """Remet à zéro tous les filtres."""
        filter_keys = ['filter_location', 'filter_contract_type', 'filter_experience_level']
        
        for key in filter_keys:
            if key in st.session_state:
                if key == 'filter_location':
                    st.session_state[key] = ''
                else:
                    st.session_state[key] = self.config.CONTRACT_TYPES[0] if 'contract' in key else self.config.EXPERIENCE_LEVELS[0]
        
        logger.info("Filtres réinitialisés")
    
    def render_sidebar_info(self):
        """Affiche des informations dans la sidebar."""
        with st.sidebar:
            st.markdown("### ℹ️ Informations")
            
            # Statut de la session
            if hasattr(st.session_state, 'session_data'):
                session_data = st.session_state.session_data
                
                if session_data.has_cv():
                    st.success(f"✅ CV : {session_data.cv_filename}")
                else:
                    st.info("📄 Aucun CV uploadé")
                
                if session_data.job_matches:
                    st.info(f"📋 {len(session_data.job_matches)} offres trouvées")
            
            st.divider()
            
            # Aide
            with st.expander("❓ Aide"):
                st.markdown("""
                **Comment utiliser CV-Optimizer :**
                
                1. 📄 Uploadez votre CV au format PDF
                2. 🔍 Cliquez sur "Analyser le CV"
                3. 📋 Consultez les offres correspondantes
                4. 👁️ Cliquez sur "Voir détails" pour plus d'infos
                5. 🤖 Obtenez des conseils personnalisés
                
                **Filtres disponibles :**
                - 📍 Localisation (ville, région, remote)
                - 📄 Type de contrat (CDI, CDD, Stage...)
                - 🎯 Niveau d'expérience
                """)
            
            # Configuration
            with st.expander("⚙️ Configuration"):
                st.markdown(f"**API Backend :** {self.config.API_BASE_URL}")
                st.markdown(f"**Taille max fichier :** {self.config.get_file_size_mb():.1f}MB")
                st.markdown(f"**Timeout requêtes :** {self.config.REQUEST_TIMEOUT}s")