from huggingface_hub import InferenceClient
from src.database.database import SessionLocal
from src.database.models import JobOffer
from app.config import get_settings
from loguru import logger


class JobAdvisor:
    def __init__(self):
        # On récupère le token API depuis la configuration
        settings = get_settings()
        api_key = settings.HUGGINGFACE_API_KEY

        self.model_id = "Qwen/Qwen2.5-7B-Instruct"

        self.client = InferenceClient(model=self.model_id, token=api_key)

    def get_advice(self, cv_text: str, job_id: str):
        db = SessionLocal()
        try:
            offer = db.query(JobOffer).filter(JobOffer.id == job_id).first()
            if not offer:
                return "Offre introuvable en base."

            logger.info(f"Analyse de l'offre '{offer.title}' via Hugging Face API...")

            # 1. On prépare les messages au format Chat
            messages = [
                {
                    "role": "system",
                    "content": "Tu es un expert en recrutement français. Ta mission est d'aider un candidat à adapter son CV.",
                },
                {
                    "role": "user",
                    "content": f"""Compare mon CV avec cette offre. 
                        
                        OFFRE : {offer.title}
                        DESCRIPTION : {str(offer.description)[:1500]}
                        
                        MON CV : {cv_text[:1500]}
                        
                        Donne une réponse structurée :
                        1. Points forts (2-3 points).
                        2. Compétences manquantes (mots-clés ou technos).
                        3. Un conseil pour une accroche assez brêve (2-3 phrases) en haut du 
                        CV qui permet de faire fitter au maximum le CV avec l'offre, 
                        tout en respectant les compétences du candidat.""",
                },
            ]

            # 2. Utilisation de chat_completion au lieu de text_generation
            response = self.client.chat_completion(
                messages=messages, max_tokens=800, temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Erreur lors de l'appel Hugging Face : {e}")
            return "Désolé, le service d'analyse est temporairement indisponible."
        finally:
            db.close()


if __name__ == "__main__":
    advisor = JobAdvisor()
    # Exemple avec le texte extrait du cv test data engineer et l'offre qui lui est la plus proche dans notre base
    sample_cv = "Simone HelloWorksimone@hellowork.com06XXXXXXXX2 rue de la Mabilais 35000 RennesData engineerPermis BÀ PROPOSData engineer passionnée par l analyse de données. Créative, rigoureuse et autonome, je suis spécialisée dans le traitement et la modélisation des données pour des solutions informatiques innovantes.EXPÉRIENCESData engineer - Entreprise Anonyme - Paris2018-09 - 2021-12 Conception et développement de pipelines de données Optimisation des performances et de la qualité des données Collaboration avec les équipes métier pour répondre aux besoins spécifiquesIngénieur BI - Entreprise Anonyme - Lyon2016-03 - 2018-08 Création de tableaux de bord et rapports d analyse Maintenance et évolution des solutions de Business Intelligence Formation des utilisateurs aux outils de BIStagiaire Data scientist - Entreprise Anonyme - Montpellier2015-06 - 2015-12 Analyse exploratoire de données Développement d algorithmes de machine learning Rédaction de rapports et présentation des résultatsÉTUDES DIPLÔMESMaster Informatique - ParisOBTENU EN 2015-09 Approfondissement des concepts de Data Science Projets de modélisation et d analyse de données Stage de fin d études en entrepriseLicence Mathématiques Appliquées - ToulouseOBTENU EN 2012-09 Acquisition des bases en statistiques et probabilités Cours de programmation en Python et R Projet de fin d études sur la modélisation prédictiveCOMPÉTENCES Python SQL Big Data Machine Learning Data VisualizationLANGUES Anglais EspagnolCENTRES D INTÉRÊT Photographie Voyages Cuisine Yoga Lecture"
    advice = advisor.get_advice(sample_cv, "6896146")
    print(advice)
