from loguru import logger
from src.services.cv_reader import CVReader
from src.services.matcher import JobMatcher
from src.services.llm_advisor import JobAdvisor  # Nouveau service

def orchestrate_matching(cv_path: str):
    """
    Flux complet : Lecture CV -> Matching -> Choix utilisateur -> Conseil LLM
    """
    # 1. Initialisation des services
    reader = CVReader()
    matcher = JobMatcher()
    advisor = JobAdvisor()  # On initialise le conseiller LLM

    # 2. Extraction du texte du CV
    logger.info(f"Lecture du fichier : {cv_path}")
    cv_text = reader.extract_text(cv_path)
    
    if not cv_text:
        logger.error("Échec de l'extraction du texte.")
        return

    # 3. Lancement du matching sémantique
    logger.info("Recherche des meilleures offres en base...")
    results = matcher.find_matches(
        profile_text=cv_text,
        top_n=5,
        location="Paris",
        contract_type="CDI",
        experience="D"
    )

    print(f"\n--- TOP MATCHES POUR : {cv_path} ---")

    if not results:
        print("Aucun résultat trouvé.")
        return

    # 4. Affichage des résultats
    for i, res in enumerate(results, 1):
        score = round(res.similarity_score * 100, 2)
        print(f"{i}. [{score}%] {res.title}")
        print(f"   🏢 {res.company} | 📍 {res.location}")
        print(f"   📜 {res.contract_type} | ⏳ {res.required_experience}")
        print(f"   🔗 Lien : {res.url} | ID: {res.id}")
        print("-" * 30)

    # 5. Interaction avec l'utilisateur pour le conseil LLM
    choice = input("\n👉 Saisissez le numéro de l'offre pour obtenir des conseils d'optimisation (ou 'q' pour quitter) : ")
    
    if choice.lower() == 'q':
        print("Fin du programme.")
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            selected_offer = results[idx]
            
            print(f"\n🚀 Analyse sémantique en cours pour l'offre : {selected_offer.title}...")
            
            # Appel du service LLM via l'API Hugging Face
            advice = advisor.get_advice(cv_text, selected_offer.id)
            
            print("\n" + " ✨ RECOMMANDATIONS DU LLM ".center(60, "="))
            print(advice)
            print("=" * 60 + "\n")
        else:
            print("Numéro invalide.")
    except ValueError:
        print("Entrée invalide. Veuillez saisir un nombre.")

if __name__ == "__main__":  
    orchestrate_matching("data/CVs/Exemple de CV Data engineer.pdf")