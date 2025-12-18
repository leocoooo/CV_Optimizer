import fitz  # PyMuPDF
import re
import unicodedata
from loguru import logger

class CVReader:
    def clean_text(self, text: str) -> str:
        """
        Nettoie le texte extrait pour ne garder que le contenu utile.
        """
        # 1. Normalisation Unicode (pour gérer les accents et caractères spéciaux)
        text = unicodedata.normalize("NFKC", text)
        
        # 2. Suppression des caractères de contrôle et non-imprimables
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
        
        # 3. Remplacement des caractères spéciaux/icônes par des espaces
        # On ne garde que les lettres, chiffres, ponctuation de base et espaces
        text = re.sub(r'[^a-zA-Z0-9àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ\s\.,;:\-\(\)@]', ' ', text)
        
        # 4. Nettoyage des espaces multiples et retours à la ligne
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def extract_text(self, pdf_path: str) -> str:
        """
        Lit le PDF, extrait et nettoie le texte.
        """
        try:
            logger.info(f"Analyse du CV : {pdf_path}")
            doc = fitz.open(pdf_path)
            raw_text = ""
            
            for page in doc:
                raw_text += page.get_text("text") + " "
            
            doc.close()
            
            # Application du nettoyage
            cleaned_text = self.clean_text(raw_text)
            
            if len(cleaned_text) < 50:
                logger.warning("Le texte extrait est très court. Le PDF est peut-être une image.")
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du CV : {e}")
            return ""

if __name__ == "__main__":
    reader = CVReader()
    text = reader.extract_text("data\CVs\CV WECKER.pdf")
    print(text[:500])  