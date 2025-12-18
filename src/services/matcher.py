from sqlalchemy import text
from src.database.database import SessionLocal
from src.services.embedder import Embedder
from loguru import logger
from datetime import datetime, timedelta

class JobMatcher:
    def __init__(self):
        self.embedder = Embedder()
        self.db = SessionLocal()

    def find_matches(self, profile_text: str, days_limit: int = 30, top_n: int = 5, location: str = None, contract_type: str = None, experience: str = None):
        """
        Prend un texte (CV/Profil) et retourne les N offres les plus pertinentes
        en appliquant des filtres stricts si fournis.
        """
        logger.info("Génération du vecteur pour le profil utilisateur...")
        profile_vector = self.embedder.get_embedding(profile_text)
        
        if not profile_vector:
            return []

        # 1. Construction dynamique de la clause WHERE
        filters = []
        params = {
            "vector": str(profile_vector),
            "limit": top_n
        }

        # Calcul de la date limite pour ne pas avoir des offres trop vieilles
        limit_date = datetime.now() - timedelta(days=days_limit)
        filters.append("date_actualisation >= :limit_date")
        params["limit_date"] = limit_date

        if location:
            filters.append("location ILIKE :location")
            params["location"] = f"%{location}%"
        
        if contract_type:
            filters.append("type_contrat = :contract_type")
            params["contract_type"] = contract_type

        if experience:
            filters.append("experience_exigee ILIKE :experience")
            params["experience"] = f"%{experience}%"

        # Assemblage de la clause WHERE
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        # 2. Requête SQL Hybride (Vecteur + Filtres Stricts)
        query_str = f"""
            SELECT id, title, company, location, type_contrat, experience_exigee, url, id,
                (1 - (embedding <=> :vector)) AS similarity_score
            FROM job_offers
            {where_clause}
            ORDER BY similarity_score DESC
            LIMIT :limit
        """
        
        query = text(query_str)

        logger.info(f"Recherche des {top_n} meilleures correspondances avec filtres...")
        results = self.db.execute(query, params).fetchall()

        return results

if __name__ == "__main__":
    matcher = JobMatcher()
    
    # --- SCÉNARIO DE TEST ---
    test_profile = """
    Je suis un jeune diplômé en Data Science, je maîtrise Python, 
    le machine learning avec scikit-learn et la manipulation de données avec Pandas.
    """
    
    # Exemple d'utilisation avec filtres
    city_filter = "Paris"
    contract_filter = "CDI" 
    experience_level = "D" 

    
    matches = matcher.find_matches(
        profile_text=test_profile, 
        top_n=5,
        location=city_filter,
        contract_type=contract_filter, 
        experience=experience_level
    )
    
    print(f"\n--- TOP MATCHES (Filtres: {city_filter}, {contract_filter}, {experience_level}) ---")
    if not matches:
        print("Aucune offre ne correspond à ces critères stricts.")
    else:
        for row in matches:
            score = round(row.similarity_score * 100, 2)
            print(f"[{score}%] {row.title}")
            print(f"      Entreprise: {row.company} | Ville: {row.location}")
            print(f"      Contrat: {row.type_contrat} | Exp: {row.experience_exigee}\n")
            print(f"      Lien: {row.url} | ID: {row.id}\n")