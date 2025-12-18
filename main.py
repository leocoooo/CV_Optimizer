from loguru import logger
from src.services.cv_reader import CVReader
from src.services.matcher import JobMatcher

def orchestrate_matching(cv_path: str):
    """
    Fonction principale qui lie la lecture du CV et le matching.
    """
    # 1. Initialisation des services
    reader = CVReader()
    matcher = JobMatcher()

    # 2. Extraction du texte du CV
    logger.info(f"Lecture du fichier : {cv_path}")
    cv_text = reader.extract_text(cv_path)
    
    if not cv_text:
        logger.error("Échec de l'extraction du texte.")
        return

    # 3. Lancement du matching sémantique avec filtres optionnels
    # Possibilité de filtrer par lieu, type de contrat, expérience, etc.
    logger.info("Recherche des meilleures offres en base...")
    results = matcher.find_matches(
        profile_text=cv_text,
        top_n=5,
        location="Paris",
        contract_type="CDI",
        experience="D"
    )

    print(f"TOP MATCHES POUR : {cv_path}")

    if not results:
        print("Aucun résultat trouvé.")

    else:
        for i, res in enumerate(results, 1):
            score = round(res.similarity_score * 100, 2)
            print(f"{i}. [{score}%] {res.title}")
            print(f"   🏢 {res.company} | 📍 {res.location}")
            print(f"   📜 {res.type_contrat} | ⏳ {res.experience_exigee}")
            print(f"   🔗 Lien : {res.url} | ID: {res.id}")

if __name__ == "__main__":  
    orchestrate_matching("data/CVs/f923c0e9e6a7ca1d2cb3c0e78a868dac.pdf") 