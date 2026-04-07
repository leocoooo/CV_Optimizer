"""
Helpers pour l'upload et la gestion de fichiers.
"""

from typing import Optional

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

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
        <div class="upload-shell">
            <p class="upload-title">Déposez un CV PDF</p>
            <p class="upload-copy">
                Le fichier est analysé localement par l'API pour extraire le texte,
                lancer le matching et générer des conseils ciblés.
            </p>
            <p class="small-note">Format accepté : PDF · Taille max : 5 MB</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choisir un CV PDF",
        type=["pdf"],
        help="Formats acceptés : PDF uniquement",
        label_visibility="collapsed",
        key=key,
    )

    if not uploaded_file:
        return None

    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(
            f"Fichier trop volumineux : {file_size_mb:.2f} MB (max {MAX_FILE_SIZE_MB} MB)."
        )
        return None

    st.success(f"{uploaded_file.name} chargé ({file_size_mb:.2f} MB).")
    return uploaded_file
