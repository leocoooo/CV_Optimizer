"""
Tests pour la validation de fichiers dans l'interface Streamlit CV-Optimizer.
Tests unitaires et tests basés sur les propriétés pour la validation PDF et de taille.
"""

import pytest
from hypothesis import given, strategies as st, assume
from io import BytesIO
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from utils import (
    validate_pdf_format, 
    validate_file_size, 
    validate_uploaded_file,
    get_file_validation_summary,
    is_valid_pdf
)
from models import validate_file_upload
from config import Config


# ============================================================================
# HELPER FUNCTIONS FOR TESTS
# ============================================================================

def create_valid_pdf_bytes(content: str = "Test CV Content") -> bytes:
    """Crée un PDF valide avec du contenu textuel."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, content)
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.read()


def create_invalid_pdf_bytes() -> bytes:
    """Crée des données qui ne sont pas un PDF valide."""
    return b"This is not a PDF file content"


def create_empty_pdf_bytes() -> bytes:
    """Crée un PDF vide (sans pages)."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.save()  # Sauvegarde sans ajouter de pages
    buffer.seek(0)
    return buffer.read()


def create_large_pdf_bytes(size_mb: float) -> bytes:
    """Crée un PDF de taille spécifiée."""
    content = "A" * int(size_mb * 1024 * 1024 / 100)  # Approximation
    return create_valid_pdf_bytes(content)


# ============================================================================
# UNIT TESTS - SPECIFIC EXAMPLES AND EDGE CASES
# ============================================================================

class TestPDFValidation:
    """Tests unitaires pour la validation PDF."""
    
    def test_valid_pdf_file(self):
        """Test avec un PDF valide."""
        pdf_data = create_valid_pdf_bytes("Test CV Content")
        result = validate_pdf_format(pdf_data, "test_cv.pdf")
        
        assert result['is_valid'] is True
        assert result['error_message'] == ""
        assert result['details']['has_pdf_extension'] is True
        assert result['details']['has_pdf_signature'] is True
        assert result['details']['page_count'] > 0
    
    def test_invalid_extension(self):
        """Test avec une extension non-PDF."""
        pdf_data = create_valid_pdf_bytes()
        result = validate_pdf_format(pdf_data, "test_cv.txt")
        
        assert result['is_valid'] is False
        assert "extension" in result['error_message'].lower()
        assert result['details']['has_pdf_extension'] is False
    
    def test_empty_filename(self):
        """Test avec un nom de fichier vide."""
        pdf_data = create_valid_pdf_bytes()
        result = validate_pdf_format(pdf_data, "")
        
        assert result['is_valid'] is False
        assert "nom de fichier" in result['error_message'].lower()
    
    def test_none_filename(self):
        """Test avec un nom de fichier None."""
        pdf_data = create_valid_pdf_bytes()
        result = validate_pdf_format(pdf_data, None)
        
        assert result['is_valid'] is False
        assert "nom de fichier" in result['error_message'].lower()
    
    def test_empty_file_data(self):
        """Test avec des données de fichier vides."""
        result = validate_pdf_format(b"", "test.pdf")
        
        assert result['is_valid'] is False
        assert "vide" in result['error_message'].lower()
    
    def test_none_file_data(self):
        """Test avec des données de fichier None."""
        result = validate_pdf_format(None, "test.pdf")
        
        assert result['is_valid'] is False
        assert "vide" in result['error_message'].lower()
    
    def test_invalid_pdf_signature(self):
        """Test avec des données sans signature PDF."""
        invalid_data = b"Not a PDF file"
        result = validate_pdf_format(invalid_data, "test.pdf")
        
        assert result['is_valid'] is False
        assert "signature" in result['error_message'].lower()
        assert result['details']['has_pdf_signature'] is False
    
    def test_corrupted_pdf(self):
        """Test avec un PDF corrompu."""
        corrupted_data = b"%PDF-1.4\nCorrupted content"
        result = validate_pdf_format(corrupted_data, "test.pdf")
        
        assert result['is_valid'] is False
        assert "lecture" in result['error_message'].lower()


class TestFileSizeValidation:
    """Tests unitaires pour la validation de taille de fichier."""
    
    def test_valid_file_size(self):
        """Test avec une taille de fichier valide."""
        data = b"A" * 1000  # 1KB
        result = validate_file_size(data, max_size=10000)
        
        assert result['is_valid'] is True
        assert result['error_message'] == ""
        assert result['details']['file_size'] == 1000
    
    def test_file_too_large(self):
        """Test avec un fichier trop volumineux."""
        data = b"A" * 2000  # 2KB
        result = validate_file_size(data, max_size=1000)  # Max 1KB
        
        assert result['is_valid'] is False
        assert "volumineux" in result['error_message'].lower()
        assert result['details']['file_size'] == 2000
    
    def test_empty_file_data(self):
        """Test avec des données vides."""
        result = validate_file_size(b"")
        
        assert result['is_valid'] is False
        assert "vide" in result['error_message'].lower()
    
    def test_none_file_data(self):
        """Test avec des données None."""
        result = validate_file_size(None)
        
        assert result['is_valid'] is False
        assert "contenu" in result['error_message'].lower()
    
    def test_default_max_size(self):
        """Test avec la taille maximale par défaut."""
        data = b"A" * 1000
        result = validate_file_size(data)  # Utilise Config.MAX_FILE_SIZE
        
        assert result['is_valid'] is True
        assert result['details']['max_size'] == Config.MAX_FILE_SIZE


class TestCompleteFileValidation:
    """Tests unitaires pour la validation complète de fichier."""
    
    def test_valid_pdf_file_complete(self):
        """Test complet avec un PDF valide."""
        pdf_data = create_valid_pdf_bytes("Test CV")
        result = validate_uploaded_file(pdf_data, "cv.pdf")
        
        assert result['is_valid'] is True
        assert result['error_message'] == ""
        assert result['details']['overall_status'] == 'success'
        assert result['details']['pdf_validation']['is_valid'] is True
        assert result['details']['size_validation']['is_valid'] is True
    
    def test_invalid_pdf_format(self):
        """Test avec un format PDF invalide."""
        invalid_data = b"Not a PDF"
        result = validate_uploaded_file(invalid_data, "test.pdf")
        
        assert result['is_valid'] is False
        assert result['details']['overall_status'] == 'failed'
    
    def test_file_too_large_complete(self):
        """Test avec un fichier trop volumineux."""
        large_data = b"A" * 1000
        result = validate_uploaded_file(large_data, "test.pdf", max_size=500)
        
        assert result['is_valid'] is False
        assert "volumineux" in result['error_message'].lower()
    
    def test_legacy_compatibility(self):
        """Test de compatibilité avec l'ancienne fonction."""
        pdf_data = create_valid_pdf_bytes()
        result = validate_file_upload(pdf_data, "test.pdf")
        
        # Vérification du format de retour compatible
        assert 'is_valid' in result
        assert 'error_message' in result
        assert 'file_size' in result
        assert 'is_pdf' in result
        assert 'size_valid' in result
        assert 'name_valid' in result


class TestUtilityFunctions:
    """Tests pour les fonctions utilitaires."""
    
    def test_validation_summary_valid(self):
        """Test du résumé pour un fichier valide."""
        pdf_data = create_valid_pdf_bytes()
        validation_result = validate_uploaded_file(pdf_data, "test.pdf")
        summary = get_file_validation_summary(validation_result)
        
        assert "✅" in summary
        assert "test.pdf" in summary
        assert "valide" in summary.lower()
    
    def test_validation_summary_invalid(self):
        """Test du résumé pour un fichier invalide."""
        validation_result = {
            'is_valid': False,
            'error_message': 'Fichier invalide',
            'details': {'filename': 'test.txt'}
        }
        summary = get_file_validation_summary(validation_result)
        
        assert "❌" in summary
        assert "invalide" in summary.lower()
    
    def test_is_valid_pdf_true(self):
        """Test de vérification rapide PDF valide."""
        pdf_data = create_valid_pdf_bytes()
        assert is_valid_pdf(pdf_data) is True
    
    def test_is_valid_pdf_false(self):
        """Test de vérification rapide PDF invalide."""
        invalid_data = b"Not a PDF"
        assert is_valid_pdf(invalid_data) is False
    
    def test_is_valid_pdf_empty(self):
        """Test de vérification rapide avec données vides."""
        assert is_valid_pdf(b"") is False
        assert is_valid_pdf(None) is False


# ============================================================================
# PROPERTY-BASED TESTS - UNIVERSAL PROPERTIES
# ============================================================================

class TestFileValidationProperties:
    """Tests basés sur les propriétés pour la validation de fichiers."""
    
    @given(
        filename=st.text(min_size=1, max_size=100),
        file_data=st.binary(min_size=1, max_size=1000)
    )
    def test_property_pdf_validation_rejects_non_pdf_extensions(self, filename, file_data):
        """
        **Propriété 1: Validation de fichiers PDF**
        Pour tout fichier uploadé, la validation doit accepter uniquement 
        les fichiers au format PDF valide et rejeter tous les autres formats.
        **Valide: Exigences 1.1**
        """
        assume(not filename.lower().endswith('.pdf'))
        
        result = validate_pdf_format(file_data, filename)
        
        # La validation doit échouer pour les extensions non-PDF
        assert result['is_valid'] is False
        assert result['details']['has_pdf_extension'] is False
    
    @given(
        file_data=st.binary(min_size=1, max_size=1000)
    )
    def test_property_pdf_validation_requires_pdf_signature(self, file_data):
        """
        **Propriété 1: Validation de fichiers PDF (signature)**
        Pour tout fichier avec extension PDF, la validation doit vérifier 
        la signature PDF dans le contenu.
        **Valide: Exigences 1.1**
        """
        assume(not file_data.startswith(b'%PDF-'))
        
        result = validate_pdf_format(file_data, "test.pdf")
        
        # La validation doit échouer sans signature PDF valide
        assert result['is_valid'] is False
        assert result['details']['has_pdf_signature'] is False
    
    @given(
        file_size=st.integers(min_value=1, max_value=50 * 1024 * 1024),  # 1B à 50MB
        max_size=st.integers(min_value=1024, max_value=20 * 1024 * 1024)  # 1KB à 20MB
    )
    def test_property_file_size_validation_respects_limits(self, file_size, max_size):
        """
        **Propriété 20: Limitation de taille de fichier**
        Pour tout fichier uploadé, l'interface doit rejeter les fichiers 
        dépassant la taille maximale configurée.
        **Valide: Exigences 7.4**
        """
        file_data = b"A" * file_size
        result = validate_file_size(file_data, max_size)
        
        if file_size <= max_size:
            assert result['is_valid'] is True
        else:
            assert result['is_valid'] is False
            assert "volumineux" in result['error_message'].lower()
    
    @given(
        filename=st.text(min_size=1, max_size=100).filter(lambda x: x.lower().endswith('.pdf')),
        content_size=st.integers(min_value=1, max_value=1000)
    )
    def test_property_complete_validation_consistency(self, filename, content_size):
        """
        **Propriété 1: Validation de fichiers PDF (cohérence)**
        Pour tout fichier PDF valide, la validation complète doit être cohérente 
        avec les validations individuelles.
        **Valide: Exigences 1.1, 7.4**
        """
        # Création d'un PDF valide
        pdf_data = create_valid_pdf_bytes("A" * content_size)
        
        # Validation complète
        complete_result = validate_uploaded_file(pdf_data, filename)
        
        # Validations individuelles
        pdf_result = validate_pdf_format(pdf_data, filename)
        size_result = validate_file_size(pdf_data)
        
        # Cohérence: validation complète = toutes les validations individuelles
        expected_valid = pdf_result['is_valid'] and size_result['is_valid']
        assert complete_result['is_valid'] == expected_valid
    
    @given(
        file_data=st.one_of(
            st.just(b""),  # Fichier vide
            st.just(None),  # Données None
            st.binary(min_size=1, max_size=10)  # Données non-vides
        ),
        filename=st.one_of(
            st.just(""),  # Nom vide
            st.just(None),  # Nom None
            st.text(min_size=1, max_size=50)  # Nom valide
        )
    )
    def test_property_validation_handles_edge_cases(self, file_data, filename):
        """
        **Propriété 1: Validation de fichiers PDF (cas limites)**
        Pour tout cas limite (fichiers vides, noms invalides), 
        la validation doit échouer gracieusement avec un message d'erreur approprié.
        **Valide: Exigences 1.1**
        """
        result = validate_uploaded_file(file_data, filename)
        
        # Les cas limites doivent toujours échouer
        if (not file_data or 
            not filename or 
            not isinstance(filename, str) or 
            not filename.lower().endswith('.pdf')):
            assert result['is_valid'] is False
            assert result['error_message'] != ""
    
    @given(
        valid_pdf_content=st.just(create_valid_pdf_bytes("Test content"))
    )
    def test_property_valid_pdf_always_passes_format_validation(self, valid_pdf_content):
        """
        **Propriété 1: Validation de fichiers PDF (PDF valides)**
        Pour tout PDF correctement formé avec extension .pdf, 
        la validation de format doit réussir.
        **Valide: Exigences 1.1**
        """
        result = validate_pdf_format(valid_pdf_content, "test.pdf")
        
        assert result['is_valid'] is True
        assert result['details']['has_pdf_extension'] is True
        assert result['details']['has_pdf_signature'] is True
        assert result['details']['page_count'] > 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFileValidationIntegration:
    """Tests d'intégration pour la validation de fichiers."""
    
    def test_streamlit_ui_integration(self):
        """Test d'intégration avec les composants UI Streamlit."""
        from ui_components import UIComponents
        
        # Simulation d'un fichier uploadé valide
        pdf_data = create_valid_pdf_bytes("CV Test Content")
        
        # Mock d'un objet uploaded_file Streamlit
        class MockUploadedFile:
            def __init__(self, data, name, size):
                self.data = data
                self.name = name
                self.size = size
                self.position = 0
            
            def read(self):
                return self.data
            
            def seek(self, position):
                self.position = position
        
        mock_file = MockUploadedFile(pdf_data, "test_cv.pdf", len(pdf_data))
        
        ui_components = UIComponents()
        
        # Test de validation via UI
        is_valid = ui_components._validate_pdf_content(mock_file)
        assert is_valid is True
    
    def test_config_integration(self):
        """Test d'intégration avec la configuration."""
        from config import Config
        
        # Test avec la taille maximale de la configuration
        large_data = b"A" * (Config.MAX_FILE_SIZE + 1)
        result = validate_file_size(large_data)
        
        assert result['is_valid'] is False
        assert result['details']['max_size'] == Config.MAX_FILE_SIZE


if __name__ == "__main__":
    # Exécution des tests
    pytest.main([__file__, "-v"])