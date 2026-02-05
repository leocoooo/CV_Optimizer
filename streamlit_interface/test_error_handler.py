"""
Tests basiques pour le gestionnaire d'erreurs.
Vérifie que les fonctionnalités principales fonctionnent correctement.
"""

import requests
from unittest.mock import Mock

from error_handler import ErrorHandler
from config import Config


def test_error_handler_initialization():
    """Test l'initialisation du gestionnaire d'erreurs."""
    handler = ErrorHandler()
    
    assert handler.config is not None
    assert isinstance(handler.retry_counts, dict)
    assert isinstance(handler.error_history, list)
    assert len(handler.error_history) == 0


def test_connection_error_handling():
    """Test la gestion des erreurs de connexion."""
    handler = ErrorHandler()
    error = requests.exceptions.ConnectionError("Connection failed")
    
    message = handler.handle_api_error(error, "/api/test")
    
    assert "connexion" in message.lower()
    assert len(handler.error_history) == 1
    assert handler.error_history[0]["error_type"] == "ConnectionError"


def test_http_error_handling():
    """Test la gestion des erreurs HTTP."""
    handler = ErrorHandler()
    
    # Mock d'une réponse HTTP 404
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"detail": "Not found"}
    
    error = requests.exceptions.HTTPError(response=mock_response)
    
    message = handler.handle_api_error(error, "/api/jobs/123")
    
    assert "trouvée" in message.lower() or "not found" in message.lower()


def test_cv_upload_error_handling():
    """Test la gestion spécifique des erreurs d'upload CV."""
    handler = ErrorHandler()
    
    # Test erreur fichier trop volumineux
    error = ValueError("Le fichier est trop volumineux")
    message, error_type = handler.handle_cv_upload_error(error, "test.pdf")
    
    assert "volumineux" in message.lower()
    assert error_type == "error"
    
    # Test fichier vide
    error = ValueError("Le fichier est vide")
    message, error_type = handler.handle_cv_upload_error(error, "empty.pdf")
    
    assert "vide" in message.lower()
    assert error_type == "error"


def test_job_details_error_handling():
    """Test la gestion des erreurs de détails d'offre."""
    handler = ErrorHandler()
    
    # Mock d'une erreur 404
    mock_response = Mock()
    mock_response.status_code = 404
    
    error = requests.exceptions.HTTPError(response=mock_response)
    message, error_type = handler.handle_job_details_error(error, "job123")
    
    assert "existe plus" in message.lower() or "supprimée" in message.lower()
    assert error_type == "warning"


def test_advice_generation_error_handling():
    """Test la gestion des erreurs de génération de conseils."""
    handler = ErrorHandler()
    
    # Test erreur de service indisponible
    mock_response = Mock()
    mock_response.status_code = 503
    
    error = requests.exceptions.HTTPError(response=mock_response)
    message, error_type = handler.handle_advice_generation_error(error, "job123")
    
    assert "indisponible" in message.lower()
    assert error_type == "warning"


def test_api_message_translation():
    """Test la traduction des messages d'erreur API."""
    handler = ErrorHandler()
    
    # Test traduction exacte
    translated = handler._translate_api_message("File too large")
    assert translated == "Fichier trop volumineux", f"Expected 'Fichier trop volumineux', got '{translated}'"
    
    # Test traduction partielle (case insensitive)
    translated = handler._translate_api_message("Error: file too large")
    assert translated == "Fichier trop volumineux", f"Expected 'Fichier trop volumineux', got '{translated}'"
    
    # Test message non traduit
    translated = handler._translate_api_message("Unknown error message")
    assert translated is None, f"Expected None, got '{translated}'"


def test_recovery_suggestions():
    """Test les suggestions de récupération."""
    handler = ErrorHandler()
    
    suggestions = handler.get_recovery_suggestions("connection_error")
    assert len(suggestions) > 0
    assert any("connexion" in s.lower() for s in suggestions)
    
    suggestions = handler.get_recovery_suggestions("file_too_large")
    assert len(suggestions) > 0
    assert any("réduisez" in s.lower() for s in suggestions)


def test_error_statistics():
    """Test les statistiques d'erreurs."""
    handler = ErrorHandler()
    
    # Ajout de quelques erreurs
    handler.handle_api_error(requests.exceptions.ConnectionError(), "/api/test1")
    handler.handle_api_error(requests.exceptions.Timeout(), "/api/test2")
    handler.handle_api_error(requests.exceptions.ConnectionError(), "/api/test1")
    
    stats = handler.get_error_statistics()
    
    assert stats["total_errors"] == 3
    assert stats["error_types"]["ConnectionError"] == 2
    assert stats["error_types"]["Timeout"] == 1
    assert stats["endpoints"]["/api/test1"] == 2
    assert stats["endpoints"]["/api/test2"] == 1


def test_retry_logic():
    """Test la logique de retry."""
    handler = ErrorHandler()
    
    # Test retry pour erreur de connexion
    error = requests.exceptions.ConnectionError()
    should_retry = handler.should_retry(error, "/api/test")
    assert should_retry is True
    assert handler.retry_counts["/api/test"] == 1
    
    # Test limite de retry
    handler.retry_counts["/api/test"] = handler.config.MAX_RETRIES
    should_retry = handler.should_retry(error, "/api/test")
    assert should_retry is False


if __name__ == "__main__":
    # Exécution des tests basiques
    print("Testing error handler initialization...")
    test_error_handler_initialization()
    print("✅ Initialization test passed")
    
    print("Testing connection error handling...")
    test_connection_error_handling()
    print("✅ Connection error test passed")
    
    print("Testing CV upload error handling...")
    test_cv_upload_error_handling()
    print("✅ CV upload error test passed")
    
    print("Testing API message translation...")
    try:
        test_api_message_translation()
        print("✅ API message translation test passed")
    except AssertionError as e:
        print(f"❌ API message translation test failed: {e}")
    
    print("Testing recovery suggestions...")
    test_recovery_suggestions()
    print("✅ Recovery suggestions test passed")
    
    print("Testing error statistics...")
    test_error_statistics()
    print("✅ Error statistics test passed")
    
    print("Testing retry logic...")
    test_retry_logic()
    print("✅ Retry logic test passed")
    
    print("\n🎉 Error handler tests completed!")