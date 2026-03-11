"""
Helpers pour l'upload et la gestion de fichiers.
"""

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from typing import Optional
from ui.utils.config import MAX_FILE_SIZE_MB


def cv_uploader(key: Optional[str] = None) -> Optional[UploadedFile]:
    """
    Affiche un uploader de CV avec instructions.

    Args:
        key: Clé unique pour le widget

    Returns:
        Objet UploadedFile ou None
    """
    st.markdown(
        """
        <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; 
                    border: 2px dashed #667eea; margin-bottom: 1rem;'>
            <p style='margin: 0; color: #666; text-align: center;'>
                📄 Glissez-déposez votre CV ici ou cliquez pour parcourir
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choisir un fichier CV (PDF)",
        type=["pdf"],
        help="Formats acceptés: PDF uniquement (max 5MB)",
        label_visibility="collapsed",
        key=key,
    )

    if uploaded_file:
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(
                f"❌ Fichier trop volumineux: {file_size_mb:.2f} MB (max {MAX_FILE_SIZE_MB} MB)"
            )
            return None
        st.success(f"✅ Fichier chargé: {uploaded_file.name} ({file_size_mb:.2f} MB)")

    return uploaded_file
