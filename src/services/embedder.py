from sentence_transformers import SentenceTransformer
from loguru import logger


class Embedder:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        logger.info(f"Chargement du modèle NLP : {model_name}")
        # Le modèle est téléchargé lors de la première initialisation
        self.model = SentenceTransformer(model_name)
        logger.success("Modèle chargé avec succès.")

    def get_embedding(self, text: str):
        """
        Génère un vecteur numérique à partir d'un texte.
        """
        if not text:
            return None
        # Transformation du texte en liste de nombres
        return self.model.encode(text).tolist()
