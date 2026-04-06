from sentence_transformers import SentenceTransformer
from loguru import logger


class Embedder:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        logger.info(f"Chargement du modèle NLP : {model_name}")
        # Le modèle est téléchargé lors de la première initialisation
        self.model = SentenceTransformer(model_name)
        logger.success("Modèle chargé avec succès.")

    def get_embedding(self, text: str, max_tokens: int = 128):
        """
        Génère un vecteur numérique à partir d'un texte.

        Args:
            text: Le texte à vectoriser
            max_tokens: Limite maximale de tokens (défaut: 128)

        Returns:
            Liste de nombres représentant le vecteur, ou None si texte vide

        Note:
            Le modèle paraphrase-multilingual-MiniLM-L12-v2 a une limite de 128 tokens.
            Les textes plus longs sont tronqués automatiquement avec un warning.
        """
        if not text:
            return None

        # Estimation approximative: ~4 caractères par token
        max_chars = max_tokens * 4

        if len(text) > max_chars:
            original_length = len(text)
            text = text[:max_chars]
            logger.warning(
                f"Contenu tronqué pour embedding: {original_length} → {max_chars} caractères "
                f"(limite: {max_tokens} tokens). "
                f"Information perdue: {original_length - max_chars} caractères."
            )

        # Transformation du texte en liste de nombres
        return self.model.encode(text).tolist()
